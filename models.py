# models.py – Datenbankmodelle für DIANAi

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# SQLAlchemy-Datenbankinstanz
db = SQLAlchemy()

# ----- Nutzer-Modell -----
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # Primärschlüssel
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    sessions = db.relationship('SessionLog', backref='user', lazy=True)
    questionnaires = db.relationship('QuestionnaireResponse', backref='user', lazy=True)

# ----- Session-Protokoll für IMTT-Gespräche -----
class SessionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model = db.Column(db.String(50))
    voice = db.Column(db.String(50))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)


# ----- Fragebogenantworten zur Bestandsaufnahme -----
class QuestionnaireResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responses = db.Column(db.Text, nullable=False)  # JSON-String mit allen Antworten
