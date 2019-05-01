from st_webservice import app, db, lm
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users';
    id = db.Column(db.Integer, primary_key=True)           
    email = db.Column(db.String(120), index=True, unique=True)
    username = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserAuth(UserMixin, db.Model):      # for third-party oauth services
    __tablename__ = 'auth_users';
    id = db.Column(db.Integer, primary_key=True)           
    social_id = db.Column(db.String(64), nullable=True, unique=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True)

    def __repr__(self):
        return '<Authenticated User {}>'.format(self.username)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@lm.user_loader
def load_auth_user(id):
    return UserAuth.query.get(int(id))