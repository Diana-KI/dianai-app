from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, SelectField, RadioField,
    IntegerField, TextAreaField, DateField
)
from wtforms.validators import DataRequired, Email, EqualTo, Optional


# ----- Login-Formular -----
class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Login')


# ----- Registrierungs-Formular -----
class RegistrationForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    password2 = PasswordField('Passwort wiederholen', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')


# ----- Session-Formular -----
class SessionForm(FlaskForm):
    model = SelectField('GPT-Modell', choices=[
        ('gpt-4.1-mini', 'gpt-4.1-mini'),
        ('gpt-4-turbo', 'gpt-4-turbo'),
        ('o4-mini', 'o4-mini'),
        ('deepseek-chat', 'DeepSeek')
    ])
    voice = SelectField('Stimme', choices=[
        ('nova', 'Nova'),
        ('shimmer', 'Shimmer'),
        ('echo', 'Echo')
    ])
    start = SubmitField('Session starten')
    end = SubmitField('Session beenden')


# ----- Fragebogen (Bestandsaufnahme) -----
class QuestionnaireForm(FlaskForm):
    # Soziodemografisch
    birthdate = DateField('Geburtsdatum', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Geschlecht', choices=[
        ('weiblich', 'Weiblich'),
        ('maennlich', 'Männlich'),
        ('divers', 'Divers'),
        ('keine_angabe', 'Keine Angabe')
    ])
    country_origin = StringField('Land, in dem du aufgewachsen bist', validators=[DataRequired()])
    country_current = StringField('Land, in dem du derzeit lebst', validators=[DataRequired()])

    # Schmerzen
    pain = RadioField('Hast du regelmäßig Schmerzen?', choices=[('ja', 'Ja'), ('nein', 'Nein')])
    pain_kopf = IntegerField('Kopfschmerzen (0–10)', validators=[Optional()])
    pain_ruecken = IntegerField('Rückenschmerzen (0–10)', validators=[Optional()])
    pain_bauch = IntegerField('Bauchschmerzen (0–10)', validators=[Optional()])
    pain_gelenke = IntegerField('Gelenkschmerzen (0–10)', validators=[Optional()])
    pain_muskeln = IntegerField('Muskelschmerzen (0–10)', validators=[Optional()])
    pain_nerven = IntegerField('Nervenschmerzen (0–10)', validators=[Optional()])
    pain_andere = StringField('Andere Schmerzen', validators=[Optional()])

    # Psychisch
    depression = IntegerField('Niedergeschlagenheit / Hoffnungslosigkeit (0–10)', validators=[Optional()])
    emotionale_taubheit = IntegerField('Emotionale Taubheit (0–10)', validators=[Optional()])
    anhedonie = IntegerField('Antriebslosigkeit (0–10)', validators=[Optional()])
    zufriedenheit = IntegerField('Zufriedenheit im Alltag (0–10)', validators=[Optional()])
    schlaf = IntegerField('Schlafprobleme (0–10)', validators=[Optional()])
    unruhe = IntegerField('Innere Unruhe (0–10)', validators=[Optional()])
    ueberforderung = IntegerField('Überforderung (0–10)', validators=[Optional()])

    trauma_erlebt = RadioField('Trauma erlebt?', choices=[('ja', 'Ja'), ('nein', 'Nein'), ('unsicher', 'Unsicher')])
    trauma_art = SelectField('Art des Traumas', choices=[
        ('einmalig', 'Einmalig'),
        ('wiederholt', 'Wiederholt'),
        ('langfristig', 'Langfristig'),
        ('', 'Nicht anwendbar')
    ], validators=[Optional()])
    trauma_folgen = IntegerField('Beeinträchtigung durch Erinnerungen (0–10)', validators=[Optional()])

    essverhalten = IntegerField('Problematisches Essverhalten (0–10)', validators=[Optional()])
    energiephasen = IntegerField('Übermäßige Energiephasen (0–10)', validators=[Optional()])
    substanznutzung = IntegerField('Substanzgebrauch zur Regulation (0–10)', validators=[Optional()])
    substanz_kontrollverlust = RadioField('Kontrollverlust bei Substanznutzung?', choices=[
        ('ja', 'Ja'), ('nein', 'Nein'), ('', 'Nicht anwendbar')
    ], validators=[Optional()])

    impulsverhalten = IntegerField('Impulsives/Zwanghaftes Verhalten (0–10)', validators=[Optional()])
    wutkontrolle = IntegerField('Kontrollverlust bei Wut (0–10)', validators=[Optional()])
    wut_folgen = RadioField('Führt das zu Problemen?', choices=[
        ('ja', 'Ja'), ('nein', 'Nein'), ('', 'Nicht anwendbar')
    ], validators=[Optional()])

    konzentration = IntegerField('Konzentrationsprobleme (0–10)', validators=[Optional()])
    neurodivergenz = RadioField('Neurodivergenz diagnostiziert?', choices=[
        ('ja', 'Ja'), ('nein', 'Nein'), ('unsicher', 'Unsicher')
    ])
    trauer = IntegerField('Trauer oder Verlustschmerz (0–10)', validators=[Optional()])
    stress = IntegerField('Stress durch Alltag (0–10)', validators=[Optional()])

    selbstbewertung = SelectField('Psychischer Zustand', choices=[
        ('stabil', 'Stabil'),
        ('belastet', 'Belastet, aber funktionstüchtig'),
        ('beeinträchtigt', 'Stark beeinträchtigt'),
        ('krise', 'In akuter Krise'),
        ('selbstmord', 'Selbstmordgefahr')
    ])
    hilfe = RadioField('Aktuelle therapeutische Unterstützung?', choices=[
        ('ja', 'Ja'),
        ('nein', 'Nein'),
        ('wuensche', 'Nein, aber gewünscht')
    ])
    gespraech = RadioField('Gespräch gewünscht?', choices=[('ja', 'Ja'), ('nein', 'Nein')])
    freitext = TextAreaField('Was brauchst du oder möchtest du mitteilen?', validators=[Optional()])
    submit = SubmitField('Fragebogen abschließen')
