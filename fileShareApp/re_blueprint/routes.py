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
    update_recall, create_categories_xlsx, update_files_re, column_names_dict_re_util, \
    column_names_re_util
import openpyxl
from werkzeug.utils import secure_filename
import json
import glob
import shutil
from fileShareApp.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, \
    RequestResetForm, ResetPasswordForm
import re
import logging
from fileShareApp.inv_blueprint.utils_general import category_list_dict_util, remove_category_util
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
    print('*TOP OF def search_recalls()*')
    logger.info('in search_recalls page')
    category_list =[y for x in category_list_dict_util().values() for y in x]
    column_names=column_names_re_util()
    column_names_dict=column_names_dict_re_util()
    
    if request.args.get('category_dict'):
        category_dict=request.args.get('category_dict')
    else:
        category_dict={'category1':''}
    
    
    #Get/identify query to run for table
    if request.args.get('query_file_name'):
        query_file_name=request.args.get('query_file_name')
        print('query_file_name:::', query_file_name)
        recalls_query, search_criteria_dictionary, category_dict = recalls_query_util(query_file_name)
        no_hits_flag = False
        if len(recalls_query) ==0:
            no_hits_flag = True
    elif request.args.get('no_hits_flag')==True:
        recalls_query, search_criteria_dictionary = ([],{})
    else:
        query_file_name= 'default_query_re.txt'
        recalls_query, search_criteria_dictionary, category_dict = recalls_query_util(query_file_name)
        no_hits_flag = False
        if len(recalls_query) ==0:
            no_hits_flag = True        

    
    #Make recalls to dictionary for bit table bottom of home screen
    recalls_data = queryToDict(recalls_query, column_names)#List of dicts each dict is row
    
    #break data into smaller lists to paginate if number of returns greatere than inv_count_limit
    recall_count=len(recalls_data)
    if request.args.get('search_limit'):
        search_limit=int(request.args.get('search_limit'))
    else:
        search_limit=recall_count+1#login default record loading <<<This will change limit
    recall_data_list=[]
    i=0
    loaded_dict = {}

    while i*search_limit <recall_count:
        recall_data_list.append(
            recalls_data[i * search_limit: (i +1) * search_limit])
        if (i +1)* search_limit<=recall_count:
            loaded_dict[i]=f'[Loaded {i * search_limit} through {(i +1)* search_limit}]'
        else:
            loaded_dict[i]=f'[Loaded {i * search_limit} through {recall_count}]'
        i+=1
    if recall_count==0:
        recall_data_list=[['No data']]
        loaded_dict[i]='search returns no records'
    

    #Keep track of what page user was on
    if request.args.get('recall_data_list_page'):
        recall_data_list_page=int(request.args.get('recall_data_list_page'))
    else:
        recall_data_list_page=0

    #make a flag to disable load previous
    if recall_data_list_page == 0:
        disable_load_previous=True
        print('if recall_data_list_page == 0:')
        if len(recall_data_list)==1:
            disable_load_next = True
        else:
            disable_load_next = False
            print(' else disable_load_next = False')
    else:
        disable_load_previous=False
        if len(recall_data_list)>recall_data_list_page+1:
            disable_load_next = False
            print('if len(recall_data_list)>recall_data_list_page+1:')
        else:
            disable_load_next = True
        
    

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
                recall_data_list_page=0,search_limit=search_limit))
        elif formDict.get('load_previous'):
            recall_data_list_page=recall_data_list_page-1
            
            return redirect(url_for('re_blueprint.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                recall_data_list_page=recall_data_list_page,
                search_limit=search_limit))
        elif formDict.get('load_next'):
            recall_data_list_page=recall_data_list_page+1
            
            return redirect(url_for('re_blueprint.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                recall_data_list_page=recall_data_list_page,
                search_limit=search_limit))            
        elif formDict.get('view'):
            re_id_for_dash=formDict.get('view')
            return redirect(url_for('re_blueprint.recalls_dashboard',re_id_for_dash=re_id_for_dash))
        elif formDict.get('add_category'):
            new_category='category' + str(len(category_dict)+1)
            formDict[new_category]=''
            del formDict['add_category']
            # formDict['add_category']=''
            query_file_name = search_criteria_dictionary_util(formDict)
            return redirect(url_for('re_blueprint.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                recall_data_list_page=0,search_limit=search_limit))
        elif formDict.get('remove_category'):
            
            category_for_remove = 'sc_'+formDict['remove_category']
            # del category_dict[formDict['remove_category']]
            form_dict_cat_element = 'sc_' + formDict['remove_category']
            print('form_dict_cat_element:::',form_dict_cat_element)
            
            del formDict[form_dict_cat_element]
            print('formDict:::',formDict)
            
            query_file_name = search_criteria_dictionary_util(formDict)
            return redirect(url_for('re_blueprint.search_recalls', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                recall_data_list_page=0,search_limit=search_limit))
            
    return render_template('search_recalls.html',table_data = recall_data_list[int(recall_data_list_page)], 
        column_names_dict=column_names_dict, column_names=column_names,
        len=len, make_list = make_list, query_file_name=query_file_name,
        search_criteria_dictionary=search_criteria_dictionary,str=str,search_limit=search_limit,
        recall_count=f'{recall_count:,}', loaded_dict=loaded_dict,
        recall_data_list_page=recall_data_list_page, disable_load_previous=disable_load_previous,
        disable_load_next=disable_load_next, category_list=category_list,category_dict=category_dict)






@re_blueprint.route("/recalls_dashboard", methods=["GET","POST"])
@login_required
def recalls_dashboard():
    print('*TOP OF def dashboard()*')
    
    #for deleting files only
    if request.args.get('current_re_files_dir_name'):
        current_re_files_dir_name=request.args.get('current_re_files_dir_name')
    else:
        current_re_files_dir_name='No file passed'
        
    #view, update
    if request.args.get('re_id_for_dash'):
        # print('request.args.get(re_id_for_dash, should build verified_by_list')
        re_id_for_dash = int(request.args.get('re_id_for_dash'))
        dash_re= db.session.query(Recalls).get(re_id_for_dash)
        verified_by_list =db.session.query(Tracking_re.updated_to, Tracking_re.time_stamp).filter_by(
            recalls_table_id=re_id_for_dash,field_updated='verified_by_user').all()
        verified_by_list=[[i[0],i[1].strftime('%Y/%m/%d %#I:%M%p')] for i in verified_by_list]
        # print('verified_by_list:::',verified_by_list)
    else:
        verified_by_list=[]

    #pass check or no check for current_user
    if any(current_user.email in s for s in verified_by_list):
        checkbox_verified = 'checked'
    else:
        checkbox_verified = ''
    
    #FILES This turns the string in files column to a list if something exists
    if dash_re.files=='':
        dash_re_files=''
    else:
        dash_re_files=dash_re.files.split(',')
    
    #Categories
    if dash_re.categories=='':
        dash_re_categories=''
    else:
        dash_re_categories=dash_re.categories.split(',')
        dash_re_categories=[i.strip() for i in dash_re_categories]
        print('dash_re_categories:::',dash_re_categories)
    
    dash_re_BGMAN=None if dash_re.BGMAN==None else dash_re.BGMAN.strftime("%Y-%m-%d")
    dash_re_ODATE= None if dash_re.ODATE == None else dash_re.ODATE.strftime("%Y-%m-%d")
    dash_re_RCDATE=None if dash_re.RCDATE==None else dash_re.RCDATE.strftime("%Y-%m-%d")
    dash_re_DATEA=None if dash_re.DATEA==None else dash_re.DATEA.strftime("%Y-%m-%d")
    
    
    dash_re_list = [dash_re.RECORD_ID, dash_re.CAMPNO, dash_re.MAKETXT, dash_re.MODELTXT, dash_re.YEAR,
        dash_re.MFGCAMPNO, dash_re.COMPNAME, dash_re.MFGNAME, dash_re_BGMAN,
        dash_re.ENDMAN, dash_re.RCLTYPECD, dash_re.POTAFF, dash_re_ODATE,
        dash_re.INFLUENCED_BY, dash_re.MFGTXT, dash_re_RCDATE, 
        dash_re_DATEA, dash_re.RPNO, dash_re.FMVSS, dash_re.DESC_DEFECT, dash_re.CONSEQUENCE_DEFCT,
        dash_re.CORRECTIVE_ACTION,dash_re.NOTES, dash_re.RCL_CMPT_ID,dash_re.km_notes,
        dash_re.date_updated.strftime('%Y/%m/%d %I:%M%p'), dash_re_files, dash_re_categories]

#files 24

    #Make lists for investigation_entry_top
    re_entry_top_names_list=['Record ID', 'CAMPNO', 'Make', 'Model', 'Year', 'MFGCAMPNO',
       'COMPNAME', 'Manufacturer Name', 'BGMAN', 'ENDMAN', 'RCLTYPECD', 'POTAFF',
       'Open Date', 'INFLUENCED_BY', 'MFGTXT', 'RCDATE', 'DATEA', 'RPNO', 'FMVSS',
       'DESC_DEFECT', 'CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION', 'NOTES','RCL_CMPT_ID']
    

    re_entry_top_list=zip(re_entry_top_names_list[:19],dash_re_list[:19])
    re_entry_top2_list=zip(re_entry_top_names_list[19:],dash_re_list[19:])
    
    #make dictionary of category lists from excel file
    # categories_excel=os.path.join(current_app.config['UTILITY_FILES_FOLDER'], 'categories.xlsx')
    # df=pd.read_excel(categories_excel)
    # category_list_dict={}
    # for i in range(0,len(df.columns)):
        # category_list_dict[df.columns[i]] =df.iloc[:,i:i+1][df.columns[i]].dropna().tolist()
    category_list_dict=category_list_dict_util()
    
    category_group_dict_no_space={i:re.sub(r"\s+","",i) for i in list(category_list_dict)}

    
    
    if request.method == 'POST':
        print('!!!!in POST method')
        formDict = request.form.to_dict()
        argsDict = request.args.to_dict()
        filesDict = request.files.to_dict()
        
        if formDict.get('update_re'):
            # print('formDict:::',formDict)
            # print('argsDict:::',argsDict)
            # print('filesDict::::',filesDict)
            update_recall(formDict, re_id_for_dash=re_id_for_dash, verified_by_list=verified_by_list)

            if request.files.get('recall_file'):
                #updates file name in database
                update_files_re(filesDict, re_id_for_dash=re_id_for_dash, verified_by_list=verified_by_list)
                
                #SAVE file in dir named after NHTSA action num _ dash_id
                uploaded_file = request.files['recall_file']
                current_re_files_dir_name = 'Recall_'+str(re_id_for_dash)
                current_re_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'], current_re_files_dir_name)
                
                if not os.path.exists(current_re_files_dir):
                    os.makedirs(current_re_files_dir)
                uploaded_file.save(os.path.join(current_re_files_dir,uploaded_file.filename))
                
                #recalls database files column - set value as string comma delimeted
                if dash_re.files =='':
                    dash_re.files =uploaded_file.filename
                else:
                    dash_re.files =dash_re.files +','+ uploaded_file.filename
                db.session.commit()                
            return redirect(url_for('re_blueprint.recalls_dashboard', re_id_for_dash=re_id_for_dash,
                current_re_files_dir_name=current_re_files_dir_name))
        
    return render_template('dashboard_re.html',re_entry_top_list=re_entry_top_list,
        dash_re_list=dash_re_list, str=str, len=len, re_id_for_dash=re_id_for_dash,
        verified_by_list=verified_by_list,checkbox_verified=checkbox_verified, int=int, 
        category_list_dict=category_list_dict, list=list,
        category_group_dict_no_space=category_group_dict_no_space, re_entry_top2_list=re_entry_top2_list,
        current_re_files_dir_name=current_re_files_dir_name)



@re_blueprint.route("/delete_file_re/<re_id_for_dash>/<filename>", methods=["GET","POST"])
# @posts.route('/post/<post_id>/update', methods = ["GET", "POST"])
@login_required
def delete_file_re(re_id_for_dash,filename):
    #update Investigations table files column
    dash_re =db.session.query(Recalls).get(re_id_for_dash)
    print('delete_file route - dash_re::::',dash_re.files)
    file_list=''
    if (",") in dash_re.files and len(dash_re.files)>1:
        file_list=dash_re.files.split(",")
        file_list.remove(filename)
    dash_re.files=''
    db.session.commit()
    if len(file_list)>0:
        for i in range(0,len(file_list)):
            if i==0:
                dash_re.files = file_list[i]
            else:
                dash_re.files = dash_re.files +',' + file_list[i]
    db.session.commit()
    
    
    #Remove files from files dir
    current_re_files_dir_name = str(dash_re.RECORD_ID) + '_'+str(re_id_for_dash)
    current_re_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'], current_re_files_dir_name)
    files_dir_and_filename=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'],
        current_re_files_dir_name, filename)
    
    if os.path.exists(files_dir_and_filename):
        os.remove(files_dir_and_filename)
    
    if len(os.listdir(current_re_files_dir))==0:
        os.rmdir(current_re_files_dir)
    
    flash('file has been deleted!', 'success')
    return redirect(url_for('re_blueprint.recalls_dashboard', re_id_for_dash=re_id_for_dash))





















