from flask_sqlalchemy import SQLAlchemy
import time

db = SQLAlchemy()

class Location(db.Model):

    _tablename_ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    machines = db.relationship('Machine', cascade='delete')

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'unnamed-location')


    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Machine(db.Model):

    _tablename_ = 'machine'
    id = db.Column(db.Integer, primary_key=True)
    washer = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    last_session_start = db.Column(db.Integer, nullable=True)
    last_session_duration = db.Column(db.Integer, nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)

    def __init__(self, **kwargs):
        self.washer = kwargs.get('washer', True)
        self.location_id = kwargs.get('location_id', 1)
        self.status = kwargs.get('status', 0)
        self.last_session_start = None
        self.last_session_duration = None


    def initiate_session(self, duration):
        self.last_session_start = round(time.time())
        self.last_session_duration = duration


    def get_status(self):
        if self.status != 2:
            return 1 if self.get_time_remaining() > 0 else 0
        return self.status


    def get_time_remaining(self):
        if self.last_session_start is None or self.last_session_duration is None:
            return 0
        session_time_left = (self.last_session_start + self.last_session_duration) - round(time.time())
        return max(session_time_left, 0)


    def serialize(self):
        return {
            'id': self.id,
            'location': self.location_id,
            'washer': self.washer,
            'status': self.get_status(),
            'time_remaining': self.get_time_remaining()
        }
