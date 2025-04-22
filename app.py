# app.py – Hauptlogik für DIANAi
# Enthält: Login, Registrierung, Sessionverwaltung, Fragebogenpflicht, GPT-Anbindung, Audiofunktionen
from dotenv import load_dotenv
import os

load_dotenv()

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session as flask_session, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import openai
import os
import re
import json


# Eigene Module
from config import Config
from forms import LoginForm, RegistrationForm, SessionForm, QuestionnaireForm
from models import db, User, SessionLog, QuestionnaireResponse

# --------------------------------------------------
# 🧱 App-Konfiguration
# --------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
openai.api_key = os.getenv("OPENAI_API_KEY")


# Login-Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # lädt Nutzer anhand seiner ID

# --------------------------------------------------
# 🔐 Benutzerverwaltung
# --------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=form.password.data
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registrierung erfolgreich.")
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash("Benutzername oder E-Mail existiert bereits.")
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password_hash == form.password.data:
            login_user(user)
            # Weiterleitung zu Fragebogen, wenn noch kein Eintrag existiert
            if not QuestionnaireResponse.query.filter_by(user_id=user.id).first():
                return redirect(url_for('questionnaire'))
            return redirect(url_for('prompt_session'))
        flash("Ungültiger Login.")
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash("Du wurdest ausgeloggt.")
    return redirect(url_for('login'))

# --------------------------------------------------
# ❓ Nach Login: Session starten?
# --------------------------------------------------

@app.route('/prompt-session')
@login_required
def prompt_session():
    return render_template('prompt_session.html')

# --------------------------------------------------
# 📋 Fragebogen
# --------------------------------------------------

@app.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire():
    form = QuestionnaireForm()
    if form.validate_on_submit():
        # Antworten als Dictionary sammeln
        answers = {
            field.name: str(field.data) for field in form if field.name != 'csrf_token' and field.name != 'submit'
        }

        # Speichern in Datenbank als JSON-Text
        response = QuestionnaireResponse(
            user_id=current_user.id,
            responses=json.dumps(answers),
            created_at=datetime.utcnow()
        )
        db.session.add(response)
        db.session.commit()
        flash("Fragebogen gespeichert.")
        return redirect(url_for('session_control'))

    return render_template('questionnaire.html', form=form)

# --------------------------------------------------
# 💬 Session mit GPT-Modell- & Stimmwahl
# --------------------------------------------------

#fragebogenintegration
@app.route('/session', methods=['GET', 'POST'])
@login_required
def session_control():
    form = SessionForm()

    # Aktuellste Fragebogen-Antwort abrufen
    latest = QuestionnaireResponse.query.filter_by(user_id=current_user.id).order_by(QuestionnaireResponse.created_at.desc()).first()

    # Session-Anzahl zählen
    session_count = SessionLog.query.filter_by(user_id=current_user.id).count()

    # Fragebogenpflicht prüfen
    if not latest or (session_count > 0 and session_count % 5 == 0):
        return redirect(url_for('questionnaire'))

    # Formularverarbeitung
    if form.validate_on_submit():
        if form.start.data:
            new_session = SessionLog(
                user_id=current_user.id,
                model=form.model.data,
                voice=form.voice.data,
                started_at=datetime.utcnow()
            )
            db.session.add(new_session)
            db.session.commit()
            flask_session['session_id'] = new_session.id
            flash("Session gestartet.")
            return redirect(url_for('index'))

        elif form.end.data:
            session_id = flask_session.get('session_id')
            if session_id:
                session_log = SessionLog.query.get(session_id)
                if session_log:
                    session_log.ended = True
                    session_log.ended_at = datetime.utcnow()
                    db.session.commit()
                flask_session.pop('session_id', None)
                flash("Session beendet.")
                return redirect(url_for('prompt_session'))

    return render_template('session.html', form=form)




# --------------------------------------------------
# 🏠 Startseite nach Sessionstart
# --------------------------------------------------

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# --------------------------------------------------
# 🔊 Transkription via Whisper
# --------------------------------------------------

@app.route('/transcribe', methods=['POST'])
@login_required
def transcribe_audio():
    model = request.args.get("model", "gpt-4-turbo")
    if 'audio' not in request.files:
        return jsonify({'error': 'Keine Audiodatei gefunden'}), 400

    audio_file = request.files['audio']
    audio_path = "audio.wav"
    audio_file.save(audio_path)

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(audio_path, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )
        return jsonify({'transcript': transcript})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(audio_path)

# --------------------------------------------------
# 🤖 GPT-Antwort generieren
# --------------------------------------------------
@app.route('/chat-response', methods=['POST'])
@login_required
def chat_response():
    model = request.args.get("model", "gpt-4-turbo")
    data = request.get_json()
    user_input = data.get('user_input')
    current_step = data.get('current_step', '1')

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 🔧 Parameter dynamisch je nach Modell vorbereiten
    params = {
        "model": model,
        "messages": [
            {"role": "system", "content": app.config["GPT_SYSTEM_PROMPT"]},
            {"role": "system", "content": f"Aktuelle Phase: {current_step}"},
            {"role": "user", "content": user_input}
        ]
    }

    # OpenAI-Modelle nutzen "max_tokens", andere wie DeepSeek evtl. "max_completion_tokens"
    if model.startswith("gpt-") or model.startswith("o4-"):
        params["max_tokens"] = 200
    else:
        params["max_completion_tokens"] = 200

    # Anfrage ausführen
    gpt_response = client.chat.completions.create(**params)

    response_text = gpt_response.choices[0].message.content
    match = re.search(r"\[Phase:\s*(\d+)\]", response_text)
    next_step = match.group(1) if match else current_step

    return jsonify({
        'gpt_response': response_text,
        'next_step': next_step
    })


# --------------------------------------------------
# 🎧 Text-to-Speech mit Stimme streamen
# --------------------------------------------------

@app.route('/tts-stream', methods=['POST'])
@login_required
def tts_stream():
    data = request.get_json()
    text = data.get('text')
    voice = data.get('voice', 'nova')

    def generate():
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format='mp3'
        )
        for chunk in audio_response.iter_bytes(chunk_size=4096):
            yield chunk

    return Response(stream_with_context(generate()), mimetype='audio/mpeg')

# ----- Session beenden + Zusammenfassung anzeigen -----
@app.route('/end-session', methods=['GET'])
@login_required
def end_session():
    session_id = flask_session.get('session_id')
    if session_id:
        session_log = SessionLog.query.get(session_id)
        if session_log and not session_log.ended:
            session_log.ended = True
            session_log.ended_at = datetime.utcnow()

            # GPT-Zusammenfassung
            try:
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                prompt = "Fasse die wichtigsten Themen dieser Session in 3–10 Sätzen zusammen."
                gpt_response = client.chat.completions.create(
                    model=session_log.model or "gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": app.config["GPT_SYSTEM_PROMPT"]},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300
                )
                summary_text = gpt_response.choices[0].message.content
                session_log.summary = summary_text

                # Optional: Dummy-Transkript (hier kannst du den echten Verlauf speichern)
                session_log.transcript = "Dies ist ein Platzhalter für das tatsächliche Transkript."

            except Exception as e:
                session_log.summary = f"Zusammenfassung nicht verfügbar: {e}"

            db.session.commit()
            flask_session.pop('session_id', None)

            return render_template('session_summary.html', summary=session_log.summary)

    flash("Keine aktive Session gefunden.")
    return redirect(url_for('prompt_session'))


# ----- Übersicht: Alle Fragebögen & Sessions anzeigen -----
@app.route('/meine-daten')
@login_required
def user_data_overview():
    sessions = SessionLog.query.filter_by(user_id=current_user.id).order_by(SessionLog.started_at.desc()).all()
    questionnaires = QuestionnaireResponse.query.filter_by(user_id=current_user.id).order_by(QuestionnaireResponse.created_at.desc()).all()
    return render_template('user_data.html', sessions=sessions, questionnaires=questionnaires)

# ----- Admin-Übersicht: Alle Nutzerdaten -----
@app.route('/admin-overview')
@login_required
def admin_overview():
    # Sicherheits-Check: Nur du als Admin darfst diese Seite sehen
    if current_user.email != "martina.schaffer@gmail.com":  # <-- hier deine E-Mail einsetzen
        flash("Du hast keinen Zugriff auf diese Seite.")
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('admin_overview.html', users=users)



# --------------------------------------------------
# 🚀 App starten
# --------------------------------------------------
# 🟣 Für Render: Datenbank beim Start erstellen
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("Fehler beim Erstellen der DB:", e)


# 🟢 Für lokalen Start mit Flask (z. B. python app.py)
if __name__ == '__main__':
    app.run(debug=True)
