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
from fileShareApp.re_blueprint.utils import recalls_query_util, queryToDict, search_criteria_dictionary_util, \
    updateInvestigation, create_categories_xlsx
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

file_handler = logging.FileHandler('fileShareApp_re_blueprint_log.txt')
logger.addHandler(file_handler)
# logger = logging.getLogger(__name__)

# this_app = create_app()
# this_app.logger.addHandler(file_handler)

re_blueprint = Blueprint('re_blueprint', __name__)


@re_blueprint.route("/search_recalls", methods=["GET","POST"])
@login_required
def search_recalls():
    print('*TOP OF def search_investigations()*')
    logger.info('in search_investigations page')


    # column_names=['id','NHTSA_ACTION_NUMBER', 'MAKE','MODEL','YEAR','COMPNAME','MFR_NAME',
        # 'ODATE','CDATE','CAMPNO','SUBJECT']
    # column_names_dict={'id':'Dash ID','NHTSA_ACTION_NUMBER':'NHTSA Number', 'MAKE':'Make','MODEL':'Model',
        # 'YEAR':'Year','COMPNAME':'Component Name','MFR_NAME':'Manufacturer Name','ODATE':'Open Date',
        # 'CDATE':'Close Date','CAMPNO':'Recall Campaign Number','SUBJECT':'Subject'}
    
    
    column_names=['RECORD_ID', 'CAMPNO', 'MAKETXT', 'MODELTXT', 'YEAR', 'MFGCAMPNO',
       'COMPNAME', 'MFGNAME', 'BGMAN', 'ENDMAN', 'RCLTYPECD', 'POTAFF',
       'ODATE', 'INFLUENCED_BY', 'MFGTXT', 'RCDATE', 'DATEA', 'RPNO', 'FMVSS',
       'DESC_DEFECT', 'CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION','RCL_CMPT_ID']
    column_names_dict={'RECORD_ID':'Record ID','CAMPNO':'Recall Campaign Number','MAKETXT':'Make',
        'MODELTXT':'Model','YEAR':'Year', 'COMPNAME':'Component Name',
        'MFGNAME':'Manufacturer Name',
        # 'BGMAN':'BGMAN',
        # 'MFGCAMPNO':'MFGCAMPNO',
        # 'ENDMAN':'ENDMAN',
        # 'RCLTYPECD':'RCLTYPECD',
        # 'POTAFF':'POTAFF',
        # 'ODATE':'ODATE',
        # 'INFLUENCED_BY':'INFLUENCED_BY',
        # 'MFGTXT':'MFGTXT',
        # 'RCDATE':'RCDATE',
        # 'DATEA':'DATEA','RPNO':'RPNO', 'FMVSS':'FMVSS','DESC_DEFECT':'DESC_DEFECT',
        'CONSEQUENCE_DEFCT':'CONSEQUENCE_DEFCT','CORRECTIVE_ACTION':'CORRECTIVE_ACTION','RCL_CMPT_ID':'RCL_CMPT_ID'}
    
    
    
    #Get/identify query to run for table
    if request.args.get('query_file_name'):
        query_file_name=request.args.get('query_file_name')
        recalls_query, search_criteria_dictionary = recalls_query_util(query_file_name)
        no_hits_flag = False
        if len(recalls_query) ==0:
            no_hits_flag = True
    elif request.args.get('no_hits_flag')==True:
        recalls_query, search_criteria_dictionary = ([],{})
    else:
        query_file_name= 'default_query_re.txt'
        recalls_query, search_criteria_dictionary = recalls_query_util(query_file_name)
        no_hits_flag = False
        if len(recalls_query) ==0:
            no_hits_flag = True        

    
    #Make investigations to dictionary for bit table bottom of home screen
    recalls_data = queryToDict(recalls_query, column_names)#List of dicts each dict is row
    
    #break data into smaller lists to paginate if number of returns greatere than inv_count_limit
    investigation_count=len(recalls_data)
    if request.args.get('search_limit'):
        search_limit=int(request.args.get('search_limit'))
    else:
        search_limit=100 #login default record loading
    investigation_data_list=[]
    i=0
    loaded_dict = {}
    print('1investigation_data_list:::', len(investigation_data_list))
    while i*search_limit <investigation_count:
        investigation_data_list.append(
            recalls_data[i * search_limit: (i +1) * search_limit])
        if (i +1)* search_limit<=investigation_count:
            loaded_dict[i]=f'[Loaded {i * search_limit} through {(i +1)* search_limit}]'
        else:
            loaded_dict[i]=f'[Loaded {i * search_limit} through {investigation_count}]'
        i+=1
    if investigation_count==0:
        investigation_data_list=[['No data']]
        loaded_dict[i]='search returns no records'
    

    
    print('2investigation_data_list:::', len(investigation_data_list))
    
    #Keep track of what page user was on
    if request.args.get('investigation_data_list_page'):
        investigation_data_list_page=int(request.args.get('investigation_data_list_page'))
    else:
        investigation_data_list_page=0

    #make a flag to disable load previous
    if investigation_data_list_page == 0:
        disable_load_previous=True
        print('if investigation_data_list_page == 0:')
        if len(investigation_data_list)==1:
            disable_load_next = True
        else:
            disable_load_next = False
            print(' else disable_load_next = False')
    else:
        disable_load_previous=False
        if len(investigation_data_list)>investigation_data_list_page+1:
            disable_load_next = False
            print('if len(investigation_data_list)>investigation_data_list_page+1:')
        else:
            disable_load_next = True
        
    
    
    #make a flag to disable load next

    #make make_list drop down options
    with open(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'make_list_recalls.txt')) as json_file:
        make_list=json.load(json_file)
        json_file.close()

    if request.method == 'POST':
        print('!!!!in POST method no_hits_flag:::', no_hits_flag)
        formDict = request.form.to_dict()
        print('formDict:::',formDict)
        search_limit=formDict.get('search_limit')
        if formDict.get('refine_search_button'):
            print('@@@@@@ refine_search_button')
            query_file_name = search_criteria_dictionary_util(formDict)
            
            return redirect(url_for('re_blueprint.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                investigation_data_list_page=0,search_limit=search_limit))
        elif formDict.get('load_previous'):
            investigation_data_list_page=investigation_data_list_page-1
            
            return redirect(url_for('re_blueprint.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                investigation_data_list_page=investigation_data_list_page,
                search_limit=search_limit))
        elif formDict.get('load_next'):
            investigation_data_list_page=investigation_data_list_page+1
            
            return redirect(url_for('re_blueprint.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                investigation_data_list_page=investigation_data_list_page,
                search_limit=search_limit))            
        elif formDict.get('view'):
            inv_id_for_dash=formDict.get('view')
            return redirect(url_for('re_blueprint.investigations_dashboard',inv_id_for_dash=inv_id_for_dash))
            
    # print('3investigation_data_list:::', len(investigation_data_list), 'page::',investigation_data_list_page)
    print('search_criteria_dictionary loaded to page:', search_criteria_dictionary)
    return render_template('search_recalls.html',table_data = investigation_data_list[int(investigation_data_list_page)], 
        column_names_dict=column_names_dict, column_names=column_names[:11],
        len=len, make_list = make_list, query_file_name=query_file_name,
        search_criteria_dictionary=search_criteria_dictionary,str=str,search_limit=search_limit,
        investigation_count=f'{investigation_count:,}', loaded_dict=loaded_dict,
        investigation_data_list_page=investigation_data_list_page, disable_load_previous=disable_load_previous,
        disable_load_next=disable_load_next)






@re_blueprint.route("/investigations_dashboard", methods=["GET","POST"])
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
            return redirect(url_for('re_blueprint.investigations_dashboard', inv_id_for_dash=inv_id_for_dash))
        
    return render_template('dashboard_inv.html',inv_entry_top_list=inv_entry_top_list,
        dash_inv_list=dash_inv_list, str=str, len=len, inv_id_for_dash=inv_id_for_dash,
        verified_by_list=verified_by_list,checkbox_verified=checkbox_verified, int=int, 
        category_list_dict=category_list_dict, list=list,
        category_group_dict_no_space=category_group_dict_no_space)



@re_blueprint.route("/delete_file/<inv_id_for_dash>/<filename>", methods=["GET","POST"])
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
    return redirect(url_for('re_blueprint.investigations_dashboard', inv_id_for_dash=inv_id_for_dash))



@re_blueprint.route("/reports", methods=["GET","POST"])
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
        return redirect(url_for('re_blueprint.reports'))
    return render_template('reports.html', excel_file_name=excel_file_name, time_stamp=time_stamp)



@re_blueprint.route("/files_zip", methods=["GET","POST"])
@login_required
def files_zip():
    if os.path.exists(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files')):
        os.remove(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files'))
    shutil.make_archive(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files'), "zip", os.path.join(
        current_app.config['UPLOADED_FILES_FOLDER']))

    return send_from_directory(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER']),'Investigation_files.zip', as_attachment=True)


@re_blueprint.route("/investigation_categories", methods=["GET","POST"])
@login_required
def investigation_categories():
    excel_file_name=request.args.get('excel_file_name')

    return send_from_directory(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER']),excel_file_name, as_attachment=True)




































# @main.route("/search_recalls", methods=["GET","POST"])
# @login_required
# def search_recalls_2():
    # print('*TOP OF def search_recalls()*')
    # logger.info('in search_recalls page')



    # column_names=['RECORD_ID', 'CAMPNO', 'MAKETXT', 'MODELTXT', 'YEAR', 'MFGCAMPNO',
       # 'COMPNAME', 'MFGNAME', 'BGMAN', 'ENDMAN', 'RCLTYPECD', 'POTAFF',
       # 'ODATE', 'INFLUENCED_BY', 'MFGTXT', 'RCDATE', 'DATEA', 'RPNO', 'FMVSS',
       # 'DESC_DEFECT', 'CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION','RCL_CMPT_ID']
    # column_names_dict={'RECORD_ID':'Record ID','CAMPNO':'Recall Campaign Number','MAKETXT':'Make',
        # 'MODELTXT':'Model','YEAR':'Year', 'COMPNAME':'Component Name',
        # 'MFGNAME':'Manufacturer Name',
        # 'BGMAN':'BGMAN',
        # 'MFGCAMPNO':'MFGCAMPNO',
        # 'ENDMAN':'ENDMAN',
        # 'RCLTYPECD':'RCLTYPECD',
        # 'POTAFF':'POTAFF',
        # 'ODATE':'ODATE',
        # 'INFLUENCED_BY':'INFLUENCED_BY',
        # 'MFGTXT':'MFGTXT',
        # 'RCDATE':'RCDATE',
        # 'DATEA':'DATEA','RPNO':'RPNO', 'FMVSS':'FMVSS','DESC_DEFECT':'DESC_DEFECT',
        # 'CONSEQUENCE_DEFCT':'CONSEQUENCE_DEFCT','CORRECTIVE_ACTION':'CORRECTIVE_ACTION','RCL_CMPT_ID':'RCL_CMPT_ID'}
    
    #make make_list drop down options
    # with open(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'make_list_recalls.txt')) as json_file:
        # make_list=json.load(json_file)
        # json_file.close()
    
        #Get/identify query to run for table
    # if request.args.get('query_file_name'):
        # query_file_name=request.args.get('query_file_name')
        # recalls_query, search_criteria_dictionary = recalls_query_util(query_file_name)
        # no_hits_flag = False
        # if len(recalls_query) ==0:
            # no_hits_flag = True
    # elif request.args.get('no_hits_flag')==True:
        # recalls_query, search_criteria_dictionary = ([],{})
    # else:
        # query_file_name= 'default_query_inv.txt'
        # recalls_query, search_criteria_dictionary = recalls_query_util(query_file_name)
        # no_hits_flag = False
        # if len(recalls_query) ==0:
            # no_hits_flag = True      
    

    
    #Make investigations to dictionary for bit table bottom of home screen
    # recalls_data = queryToDict(recalls_query, column_names)#List of dicts each dict is row
    
    #break data into smaller lists to paginate if number of returns greatere than inv_count_limit
    # investigation_count=len(recalls_data)
    # if request.args.get('search_limit'):
        # search_limit=int(request.args.get('search_limit'))
    # else:
        # search_limit=100 #login default record loading
    # investigation_data_list=[]
    # i=0
    # loaded_dict = {}
    # print('1investigation_data_list:::', len(investigation_data_list))
    # while i*search_limit <investigation_count:
        # investigation_data_list.append(
            # recalls_data[i * search_limit: (i +1) * search_limit])
        # if (i +1)* search_limit<=investigation_count:
            # loaded_dict[i]=f'[Loaded {i * search_limit} through {(i +1)* search_limit}]'
        # else:
            # loaded_dict[i]=f'[Loaded {i * search_limit} through {investigation_count}]'
        # i+=1
    # if investigation_count==0:
        # investigation_data_list=[['No data']]
        # loaded_dict[i]='search returns no records'
        
        
            
    # print('2investigation_data_list:::', len(investigation_data_list))
    
    # Keep track of what page user was on
    # if request.args.get('investigation_data_list_page'):
        # investigation_data_list_page=int(request.args.get('investigation_data_list_page'))
    # else:
        # investigation_data_list_page=0

    # make a flag to disable load previous
    # if investigation_data_list_page == 0:
        # disable_load_previous=True
        # print('if investigation_data_list_page == 0:')
        # if len(investigation_data_list)==1:
            # disable_load_next = True
        # else:
            # disable_load_next = False
            # print(' else disable_load_next = False')
    # else:
        # disable_load_previous=False
        # if len(investigation_data_list)>investigation_data_list_page+1:
            # disable_load_next = False
            # print('if len(investigation_data_list)>investigation_data_list_page+1:')
        # else:
            # disable_load_next = True
        
    
    # if request.method == 'POST':
        # print('!!!!in POST method no_hits_flag:::', no_hits_flag)
        # formDict = request.form.to_dict()
        # print('formDict:::',formDict)
        # search_limit=formDict.get('search_limit')
        # if formDict.get('refine_search_button'):
            # print('@@@@@@ refine_search_button')
            # query_file_name = search_criteria_dictionary_util(formDict)
            
            # return redirect(url_for('main.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                # investigation_data_list_page=0,search_limit=search_limit))
        # elif formDict.get('load_previous'):
            # investigation_data_list_page=investigation_data_list_page-1
            
            # return redirect(url_for('main.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                # investigation_data_list_page=investigation_data_list_page,
                # search_limit=search_limit))
        # elif formDict.get('load_next'):
            # investigation_data_list_page=investigation_data_list_page+1
            
            # return redirect(url_for('main.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                # investigation_data_list_page=investigation_data_list_page,
                # search_limit=search_limit))            
        # elif formDict.get('view'):
            # inv_id_for_dash=formDict.get('view')
            # return redirect(url_for('re_blueprint.investigations_dashboard',inv_id_for_dash=inv_id_for_dash))
            
    # print('3investigation_data_list:::', len(investigation_data_list), 'page::',investigation_data_list_page)
    # print('search_criteria_dictionary loaded to page:', search_criteria_dictionary)

    
    # return render_template('search_recalls.html', table_data=investigation_data_list[int(investigation_data_list_page)], 
        # column_names_dict=column_names_dict, column_names=column_names,
        # len=len, make_list = make_list, query_file_name=query_file_name,
        # search_criteria_dictionary=search_criteria_dictionary,str=str,search_limit=search_limit,
        # investigation_count=f'{investigation_count:,}', loaded_dict=loaded_dict,
        # investigation_data_list_page=investigation_data_list_page, disable_load_previous=disable_load_previous,
        # disable_load_next=disable_load_next)
