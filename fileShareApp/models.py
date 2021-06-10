from fileShareApp import db, login_manager
from datetime import datetime, date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin

from flask_script import Manager
# from flask_migrate import Migrate, MigrateCommand

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    # username=db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    image_file = db.Column(db.String(100),nullable=False, default='default.jpg')
    password = db.Column(db.String(100), nullable=False)
    timeStamp = db.Column(db.DateTime, default=datetime.now)
    permission = db.Column(db.Text)
    theme = db.Column(db.Text)
    posts = db.relationship('Post', backref='author', lazy=True)
    km_tracking = db.relationship('Kmtracking', backref='updator', lazy=True)
    query_string = db.relationship('Km_saved_queries', backref='query_creator', lazy=True)
    # sharedfile = db.relationship('Sharedfile', backref='fileauthor', lazy=True)
    # dmrsEntry = db.relationship('Dmrs', backref='dmrUser', lazy=True)
    # shiftsEntry = db.relationship('Shifts', backref='dmrShiftUser', lazy=True)
    # employeeId = db.relationship('Employees', backref='employeeUser', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s=Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.id}','{self.email}','{self.permission}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content = db.Column(db.Text)
    screenshot = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}','{self.date_posted}')"


class Investigations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    NHTSA_ACTION_NUMBER=db.Column(db.String(10))
    MAKE=db.Column(db.String(25))
    MODEL=db.Column(db.String(256))
    YEAR=db.Column(db.Integer)
    COMPNAME=db.Column(db.Text)
    MFR_NAME=db.Column(db.Text)
    ODATE=db.Column(db.Date, nullable=True)
    CDATE=db.Column(db.Date, nullable=True)
    CAMPNO=db.Column(db.String(9))
    SUBJECT=db.Column(db.Text)
    SUMMARY=db.Column(db.Text)
    km_notes=db.Column(db.Text)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.now)
    files = db.Column(db.Text)
    km_tracking_id = db.relationship('Kmtracking', backref='update_record', lazy=True)
    checkbox_0=db.Column(db.String(10))
    checkbox_1=db.Column(db.String(10))
    checkbox_2=db.Column(db.String(10))
    checkbox_3=db.Column(db.String(10))
    checkbox_4=db.Column(db.String(10))
    textbox_1=db.Column(db.String(100))
    textbox_2=db.Column(db.String(100))
    textbox_3=db.Column(db.String(100))
    textbox_4=db.Column(db.String(100))

    def __repr__(self):
        return f"Sharedfile('{self.id}',NHTSA_ACTION_NUMBER:'{self.NHTSA_ACTION_NUMBER}'," \
        f"'SUBJECT: {self.SUBJECT}', ODATE: '{self.ODATE}', CDATE: '{self.CDATE}')"
    

class Kmtracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_updated = db.Column(db.Text)
    updated_from = db.Column(db.Text)
    updated_to = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    investigations_table_id=db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    
    def __repr__(self):
        return f"Kmtracking(investigations_table_id: '{self.investigations_table_id}'," \
        f"field_updated: '{self.field_updated}', updated_by: '{self.updated_by}')"

class Km_saved_queries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_name = db.Column(db.Text)
    query = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    used_count =db.Column(db.Integer)
    
    def __repr__(self):
        return f"Km_saved_queries(id: '{self.id}', 'query_name: '{self.query_name}'," \
        f"query_creator_id: '{self.created_by}')"