
from flask import Flask
app = None
from application.database import db

def create_app():
    app = Flask(__name__)
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking_app.sqlite3'
    db.init_app(app)
    app.app_context().push()
    return app

app = create_app()
from application.controllers import *
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        Admin = User.query.filter_by(email = 'admin@user.com').first()
        if Admin is None:
            Admin = User(name='Admin',email='admin@user.com',phone = '1234567890',status = 'approved', password ='1234')
            db.session.add(Admin)
            db.session.commit()
    app.run()