from .database import db
from datetime import date

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    name = db.Column(db.String(),  nullable = False)
    email = db.Column(db.String(), unique = True, nullable = False)
    phone = db.Column(db.String(10), unique = True, nullable = False)
    password = db.Column(db.String(), nullable = False)
    status = db.Column(db.String(),  nullable = False, default= "Approved")
    bookings = db.relationship("Booking", backref = "user")
    
class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    name = db.Column(db.String(),  nullable = False)
    email = db.Column(db.String(), unique = True, nullable = False)
    phone = db.Column(db.String(10), unique = True, nullable = False)
    password = db.Column(db.String(), nullable = False)
    status = db.Column(db.String(),  nullable = False, default= "Pending")
    treks = db.relationship("Trek", backref = "staff")
    
class Trek(db.Model):
    __tablename__ = 'trek'
    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    trek_name = db.Column(db.String(),  nullable = False)
    location = db.Column(db.String(),  nullable = False)
    difficulty = db.Column(db.String(),  nullable = False)
    duration = db.Column(db.String(),  nullable = False)
    available_slots = db.Column(db.Integer(),  nullable = False)
    assigned_staff_id = db.Column(db.Integer(), db.ForeignKey('staff.id'),  nullable = False)
    start_date = db.Column(db.Date(),  nullable = False)
    end_date = db.Column(db.Date(),  nullable = False)
    status = db.Column(db.String(),  nullable = False)
    description = db.Column(db.String(),  nullable = False)
    bookings = db.relationship("Booking", backref = "trek")
    
class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'),  nullable = False)
    trek_id = db.Column(db.Integer(), db.ForeignKey('trek.id'),  nullable = False)
    booking_date = db.Column(db.Date(),  nullable = False, default=date.today)
    status = db.Column(db.String(),  nullable = False, default= "Booked")