from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed #used for image uploading
from wtforms import StringField, PasswordField, SubmitField, BooleanField\
    , TextAreaField, DateTimeField, FloatField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from fileShareApp.models import User, Post, Investigations
from flask_login import current_user
from datetime import datetime
from fileShareApp import db



class RegistrationForm(FlaskForm):
    # username = StringField('Username',
                           # validators=[DataRequired(),Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign up')

    # def validate_username(self, username):
        # user=User.query.filter_by(username=username.data).first()
        # if user:
            # raise ValidationError('That username already taken.')

    def validate_email(self, email):
        user=User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email already taken.')

    # def validate_field(self, field):
    #     if True:
    #         raise ValidationError('Validation Message')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    # username = StringField('Username',
                           # validators=[DataRequired(),Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(),Email()])
    picture = FileField('Update Profile Picture', validators = [FileAllowed(['jpg','png'])])
    submit = SubmitField('Update')

    # def validate_username(self, username):
        # if username.data != current_user.username:
            # user=User.query.filter_by(username=username.data).first()
            # if user:
                # raise ValidationError('That username already taken.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user=User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email already taken.')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(),Email()])
    submit = SubmitField('Request password reset')


    def validate_email(self, email):
        user=User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')