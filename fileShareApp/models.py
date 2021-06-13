from fileShareApp import db, login_manager
from datetime import datetime, date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin

from flask_script import Manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    image_file = db.Column(db.String(100),nullable=False, default='default.jpg')
    password = db.Column(db.String(100), nullable=False)
    timeStamp = db.Column(db.DateTime, default=datetime.now)
    permission = db.Column(db.Text)
    theme = db.Column(db.Text)
    posts = db.relationship('Post', backref='author', lazy=True)
    track_inv = db.relationship('Tracking_inv', backref='updator_inv', lazy=True)
    track_re = db.relationship('Tracking_re', backref='updator_re', lazy=True)
    query_string_inv = db.relationship('Saved_queries_inv', backref='query_creator_inv', lazy=True)
    query_string_re = db.relationship('Saved_queries_re', backref='query_creator_re', lazy=True)

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
    categories=db.Column(db.Text)
    km_tracking_id = db.relationship('Tracking_inv', backref='update_inv_record', lazy=True)
    

    def __repr__(self):
        return f"Investigations('{self.id}',NHTSA_ACTION_NUMBER:'{self.NHTSA_ACTION_NUMBER}'," \
        f"'SUBJECT: {self.SUBJECT}', ODATE: '{self.ODATE}', CDATE: '{self.CDATE}')"
    

class Tracking_inv(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_updated = db.Column(db.Text)
    updated_from = db.Column(db.Text)
    updated_to = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    investigations_table_id=db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    
    def __repr__(self):
        return f"Tracking_inv(investigations_table_id: '{self.investigations_table_id}'," \
        f"field_updated: '{self.field_updated}', updated_by: '{self.updated_by}')"

class Saved_queries_inv(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_name = db.Column(db.Text)
    query = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    used_count =db.Column(db.Integer)
    
    def __repr__(self):
        return f"Km_saved_queries(id: '{self.id}', 'query_name: '{self.query_name}'," \
        f"query_creator_id: '{self.created_by}')"


class Recalls(db.Model):
    RECORD_ID = db.Column(db.Integer, primary_key=True)
    CAMPNO=db.Column(db.Text)
    MAKETXT=db.Column(db.Text)
    MODELTXT=db.Column(db.Text)
    YEAR=db.Column(db.Integer)
    MFGCAMPNO=db.Column(db.Text)
    COMPNAME=db.Column(db.Text)
    MFGNAME=db.Column(db.Text)
    BGMAN =db.Column(db.Date, nullable=True)
    ENDMAN =db.Column(db.Date, nullable=True)
    RCLTYPECD=db.Column(db.Text)
    POTAFF=db.Column(db.Float)
    ODATE=db.Column(db.Date, nullable=True)
    INFLUENCED_BY=db.Column(db.Text)
    MFGTXT=db.Column(db.Text)
    RCDATE=db.Column(db.Date, nullable=True)
    DATEA=db.Column(db.Date,nullable=True)
    RPNO=db.Column(db.Text)
    FMVSS=db.Column(db.Text)
    DESC_DEFECT=db.Column(db.Text)
    CONSEQUENCE_DEFCT=db.Column(db.Text)
    CORRECTIVE_ACTION=db.Column(db.Text)
    NOTES=db.Column(db.Text)
    RCL_CMPT_ID=db.Column(db.Text)
    km_notes=db.Column(db.Text)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.now)
    files = db.Column(db.Text)
    categories=db.Column(db.Text)
    km_tracking_id = db.relationship('Tracking_re', backref='update_re_record', lazy=True)
    

    def __repr__(self):
        return f"Recalls('{self.RECORD_ID}',MAKE:'{self.MAKETXT}'," \
        f"'Component Name: {self.COMPNAME}', Manuf Name: '{self.MFGNAME}', Recall Date: '{self.RCDATE}')"

    

class Tracking_re(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_updated = db.Column(db.Text)
    updated_from = db.Column(db.Text)
    updated_to = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    recalls_table_id=db.Column(db.Integer, db.ForeignKey('recalls.RECORD_ID'), nullable=False)
    
    def __repr__(self):
        return f"Tracking_re(id: '{self.id}'," \
        f"field_updated: '{self.field_updated}', updated_by: '{self.updated_by}')"

class Saved_queries_re(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_name = db.Column(db.Text)
    query = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    used_count =db.Column(db.Integer)
    
    def __repr__(self):
        return f"Km_saved_queries(id: '{self.id}', 'query_name: '{self.query_name}'," \
        f"query_creator_id: '{self.created_by}')"

