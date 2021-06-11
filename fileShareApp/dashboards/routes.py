from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from fileShareApp import db, bcrypt, mail
from fileShareApp.models import User, Post, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from datetime import datetime, date, time
import datetime
from sqlalchemy import func, desc
import pandas as pd
import io
from wsgiref.util import FileWrapper
import xlsxwriter
from flask_mail import Message
from fileShareApp.dashboards.utils import updateInvestigation, create_categories_xlsx
import openpyxl
from werkzeug.utils import secure_filename
import json
import glob
import shutil
from fileShareApp.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, \
    RequestResetForm, ResetPasswordForm
import re
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('fileShareApp_dashboards_log.txt')
logger.addHandler(file_handler)
# logger = logging.getLogger(__name__)

# this_app = create_app()
# this_app.logger.addHandler(file_handler)

dashboards = Blueprint('dashboards', __name__)



@dashboards.route("/investigations_dashboard", methods=["GET","POST"])
@login_required
def investigations_dashboard():
    print('*TOP OF def dashboard()*')
    
    #view, update
    if request.args.get('inv_id_for_dash'):
        print('request.args.get(inv_id_for_dash, should build verified_by_list')
        inv_id_for_dash = int(request.args.get('inv_id_for_dash'))
        dash_inv= db.session.query(Investigations).get(inv_id_for_dash)
        verified_by_list =db.session.query(Tracking_inv.updated_to, Tracking_inv.time_stamp).filter_by(
            investigations_table_id=inv_id_for_dash,field_updated='verified_by_user').all()
        verified_by_list=[[i[0],i[1].strftime('%Y/%m/%d %#I:%M%p')] for i in verified_by_list]
        print('verified_by_list:::',verified_by_list)
    else:
        verified_by_list=[]

    #pass check or no check for current_user
    if any(current_user.email in s for s in verified_by_list):
        checkbox_verified = 'checked'
    else:
        checkbox_verified = ''
    
    #FILES This turns the string in files column to a list if something exists
    if dash_inv.files=='':
        dash_inv_files=''
    else:
        dash_inv_files=dash_inv.files.split(',')
    
    #Categories
    if dash_inv.categories=='':
        dash_inv_categories=''
    else:
        dash_inv_categories=dash_inv.categories.split(',')
        dash_inv_categories=[i.strip() for i in dash_inv_categories]
        print('dash_inv_categories:::',dash_inv_categories)
    
    dash_inv_list = [dash_inv.NHTSA_ACTION_NUMBER,dash_inv.MAKE,dash_inv.MODEL,dash_inv.YEAR,
        dash_inv.ODATE.strftime("%Y-%m-%d"),dash_inv.CDATE.strftime("%Y-%m-%d"),dash_inv.CAMPNO,
        dash_inv.COMPNAME, dash_inv.MFR_NAME, dash_inv.SUBJECT, dash_inv.SUMMARY,
        dash_inv.km_notes, dash_inv.date_updated.strftime('%Y/%m/%d %I:%M%p'), dash_inv_files,
        dash_inv_categories]
    
    #Make lists for investigation_entry_top
    inv_entry_top_names_list=['NHTSA Action Number','Make','Model','Year','Open Date','Close Date',
        'Recall Campaign Number','Component Description','Manufacturer Name']
    inv_entry_top_list=zip(inv_entry_top_names_list,dash_inv_list[:9])
    
    #make dictionary of category lists from excel file
    categories_excel=os.path.join(current_app.config['UTILITY_FILES_FOLDER'], 'categories.xlsx')
    df=pd.read_excel(categories_excel)
    category_list_dict={}
    for i in range(0,len(df.columns)):
        category_list_dict[df.columns[i]] =df.iloc[:,i:i+1][df.columns[i]].dropna().tolist()

    
    category_group_dict_no_space={i:re.sub(r"\s+","",i) for i in list(category_list_dict)}

    
    
    if request.method == 'POST':
        print('!!!!in POST method')
        formDict = request.form.to_dict()
        argsDict = request.args.to_dict()
        filesDict = request.files.to_dict()
        
        if formDict.get('update_inv'):
            print('formDict:::',formDict)
            # print('argsDict:::',argsDict)
            # print('filesDict::::',filesDict)
            updateInvestigation(formDict, inv_id_for_dash=inv_id_for_dash, verified_by_list=verified_by_list)

            if request.files.get('investigation_file'):
                #updates file name in database
                updateInvestigation(filesDict, inv_id_for_dash=inv_id_for_dash, verified_by_list=verified_by_list)
                
                #SAVE file in dir named after NHTSA action num _ dash_id
                uploaded_file = request.files['investigation_file']
                current_inv_files_dir_name = dash_inv.NHTSA_ACTION_NUMBER + '_'+str(inv_id_for_dash)
                current_inv_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'], current_inv_files_dir_name)
                
                if not os.path.exists(current_inv_files_dir):
                    os.makedirs(current_inv_files_dir)
                uploaded_file.save(os.path.join(current_inv_files_dir,uploaded_file.filename))
                
                #Investigations database files column - set value as string comma delimeted
                if dash_inv.files =='':
                    dash_inv.files =uploaded_file.filename
                else:
                    dash_inv.files =dash_inv.files +','+ uploaded_file.filename
                db.session.commit()                
            return redirect(url_for('dashboards.investigations_dashboard', inv_id_for_dash=inv_id_for_dash))
        
    return render_template('dashboard_inv.html',inv_entry_top_list=inv_entry_top_list,
        dash_inv_list=dash_inv_list, str=str, len=len, inv_id_for_dash=inv_id_for_dash,
        verified_by_list=verified_by_list,checkbox_verified=checkbox_verified, int=int, 
        category_list_dict=category_list_dict, list=list,
        category_group_dict_no_space=category_group_dict_no_space)



@dashboards.route("/delete_file/<inv_id_for_dash>/<filename>", methods=["GET","POST"])
# @posts.route('/post/<post_id>/update', methods = ["GET", "POST"])
@login_required
def delete_file(inv_id_for_dash,filename):
    #update Investigations table files column
    dash_inv =db.session.query(Investigations).get(inv_id_for_dash)
    print('delete_file route - dash_inv::::',dash_inv.files)
    file_list=''
    if (",") in dash_inv.files and len(dash_inv.files)>1:
        file_list=dash_inv.files.split(",")
        file_list.remove(filename)
    dash_inv.files=''
    db.session.commit()
    if len(file_list)>0:
        for i in range(0,len(file_list)):
            if i==0:
                dash_inv.files = file_list[i]
            else:
                dash_inv.files = dash_inv.files +',' + file_list[i]
    db.session.commit()
    
    
    #Remove files from files dir
    current_inv_files_dir_name = dash_inv.NHTSA_ACTION_NUMBER + '_'+str(inv_id_for_dash)
    current_inv_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'], current_inv_files_dir_name)
    files_dir_and_filename=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'],
        current_inv_files_dir_name, filename)
    
    if os.path.exists(files_dir_and_filename):
        os.remove(files_dir_and_filename)
    
    if len(os.listdir(current_inv_files_dir))==0:
        os.rmdir(current_inv_files_dir)
    
    flash('file has been deleted!', 'success')
    return redirect(url_for('dashboards.investigations_dashboard', inv_id_for_dash=inv_id_for_dash))



@dashboards.route("/reports", methods=["GET","POST"])
@login_required
def reports():
    excel_file_name='investigation_categories_report.xlsx'
    if os.path.exists(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],excel_file_name)):
        # Read Excel and turn entire sheet to a df
        time_stamp_df = pd.read_excel(os.path.join(
            current_app.config['UTILITY_FILES_FOLDER'],excel_file_name),
            'Notes',header=None)
        time_stamp = time_stamp_df.loc[0,1].to_pydatetime().strftime("%Y-%m-%d %I:%M:%S %p")
    else:
        time_stamp='no current file'

    print('time_stamp_df:::', time_stamp, type(time_stamp))
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDict::::',formDict)
        if formDict.get('build_excel_report'):

            create_categories_xlsx('investigation_categories_report.xlsx')
            logger.info('in search page')
        return redirect(url_for('dashboards.reports'))
    return render_template('reports.html', excel_file_name=excel_file_name, time_stamp=time_stamp)



@dashboards.route("/files_zip", methods=["GET","POST"])
@login_required
def files_zip():
    if os.path.exists(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files')):
        os.remove(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files'))
    shutil.make_archive(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files'), "zip", os.path.join(
        current_app.config['UPLOADED_FILES_FOLDER']))

    return send_from_directory(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER']),'Investigation_files.zip', as_attachment=True)


@dashboards.route("/investigation_categories", methods=["GET","POST"])
@login_required
def investigation_categories():
    excel_file_name=request.args.get('excel_file_name')

    return send_from_directory(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER']),excel_file_name, as_attachment=True)



