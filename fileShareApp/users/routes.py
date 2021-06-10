from flask import Blueprint

from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response
from fileShareApp import db, bcrypt, mail
from fileShareApp.models import Post, User, Investigations
from fileShareApp.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, \
    RequestResetForm, ResetPasswordForm
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from datetime import datetime, date, time
from sqlalchemy import func
import pandas as pd
import io
from wsgiref.util import FileWrapper
import xlsxwriter
from flask_mail import Message
from fileShareApp.users.utils import save_picture, send_reset_email, userPermission

users = Blueprint('users', __name__)

@users.route("/register", methods=["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form= RegistrationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            userPermission1=userPermission(form.email.data)
            if userPermission1[0]:
                user=User(email=form.email.data, password=hashed_password, permission=userPermission1[1])
            else:
                user=User(email=form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash(f'You are now registered! You can login.', 'success')
            return redirect(url_for('users.login'))
        else:
            flash(f'Did you mis type something? Check: 1) email is actually an email 2) password and confirm password match.', 'warning')
            return redirect(url_for('users.register'))
    return render_template('register.html', title='Register',form=form)

@users.route("/", methods=["GET","POST"])
@users.route("/login", methods=["GET","POST"])
def login():
    # print('***in login form****')
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        print('login - form.validate_on_submit worked')
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
            #^^^ another good thing turnary condition ^^^
        else:
            flash('Login unsuccessful', 'danger')
    return render_template('login.html', title='Login', form=form)

    

@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('users.login'))



@users.route('/account', methods=["GET","POST"])
@login_required
def account():
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        currentUser=User.query.get(current_user.id)
        currentUser.theme=request.form.get('darkTheme')
        db.session.commit()
        flash(f'Your account has been updated {current_user.email}!', 'success')
        return redirect(url_for('main.home')) #CS says want a new redirect due to "post-get-redirect pattern"
    #     post-get-redirect pattern is when browser asks are you sure you want to reload data.
    # It seems this is because the user will be running POst request on top of an existing post request
    elif request.method =='GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    #     This elif part is what i should do for preloading the DMR form with data when some already exists
    
    # if request.form.get('darkTheme'):
        # currentUser=User.query.get(current_user.id)
        # currentUser.theme='dark'
        # db.session.commit()
        
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='account', image_file=image_file, form=form)


@users.route('/reset_password', methods = ["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('email has been sent with instructions to reset your password','info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', legend='Reset Password', form=form)

@users.route('/reset_password/<token>', methods = ["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated! You are now able to login', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', legend='Reset Password', form=form)
