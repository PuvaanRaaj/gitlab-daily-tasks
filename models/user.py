import enum

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UserStatus(enum.Enum):
    DELETED = 0
    ACTIVE = 1
    BLOCKED = 2


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(100))
    team_lead = db.Column(db.String(100))
    gitlab_username = db.Column(db.String(100))
    token = db.Column(db.String(200))
    job_title = db.Column(db.String(100))
    status = db.Column(db.Enum(UserStatus), default=UserStatus.ACTIVE)
