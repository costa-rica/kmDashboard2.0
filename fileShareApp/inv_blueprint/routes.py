from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory, jsonify
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
from fileShareApp.inv_blueprint.utils import investigations_query_util, queryToDict, \
    create_categories_xlsx, existing_report, column_names_inv_util, \
    column_names_dict_inv_util, update_investigation
import openpyxl
from werkzeug.utils import secure_filename
import json
import glob
import shutil
from fileShareApp.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, \
    RequestResetForm, ResetPasswordForm
import re
import logging
from fileShareApp.inv_blueprint.utils_general import category_list_dict_util, search_criteria_dictionary_util, \
    record_remover_util, track_util, update_files_util
from fileShareApp.inv_blueprint.forms import InvForm


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('fileShareApp_inv_blueprint_log.txt')
logger.addHandler(file_handler)
# logger = logging.getLogger(__name__)

# this_app = create_app()
# this_app.logger.addHandler(file_handler)

inv_blueprint = Blueprint('inv_blueprint', __name__)


@inv_blueprint.route("/search_investigations", methods=["GET","POST"])
@login_required
def search_investigations():
    print('*TOP OF def search_investigations()*')
    logger.info('in search_investigations page')
    category_list = [y for x in category_list_dict_util().values() for y in x]
    column_names=column_names_inv_util()
    column_names_dict=column_names_dict_inv_util()
    
    if request.args.get('category_dict'):
        category_dict=request.args.get('category_dict')
    else:
        category_dict={'cateogry1':''}
        
    
    #user_list for searching userlist
    user_list=db.session.query(Tracking_inv.updated_to).filter(Tracking_inv.field_updated=='verified_by_user').distinct().all()
    user_list=[i[0] for i in user_list]
    print('query_File_naem:::', request.args.get('query_file_name'))
    #Get/identify query to run for table
    if request.args.get('query_file_name'):
        print('does this fire???')
        query_file_name=request.args.get('query_file_name')
        investigations_query, search_criteria_dictionary, category_dict = investigations_query_util(query_file_name)
        no_hits_flag = False
        if len(investigations_query) ==0:
            no_hits_flag = True
    elif request.args.get('no_hits_flag')==True:
        investigations_query, search_criteria_dictionary = ([],{})
    else:
        query_file_name= 'default_query_inv.txt'
        investigations_query, search_criteria_dictionary, category_dict = investigations_query_util(query_file_name)
        print('does thre default_query_inv.txt:::')
        print('length of investigations_query::::',len(investigations_query))
        no_hits_flag = False
        if len(investigations_query) ==0:
            no_hits_flag = True        

    
    #Make investigations to dictionary for bit table bottom of home screen
    investigations_data = queryToDict(investigations_query, column_names)#List of dicts each dict is row
    
    #break data into smaller lists to paginate if number of returns greatere than inv_count_limit
    investigation_count=len(investigations_data)
    if request.args.get('search_limit'):
        search_limit=int(request.args.get('search_limit'))
    else:
        search_limit=investigation_count+1#login default record loading <<<This will change limit
    investigation_data_list=[]
    i=0
    loaded_dict = {}

    while i*search_limit <investigation_count:
        investigation_data_list.append(
            investigations_data[i * search_limit: (i +1) * search_limit])
        if (i +1)* search_limit<=investigation_count:
            loaded_dict[i]=f'[Loaded {i * search_limit} through {(i +1)* search_limit}]'
        else:
            loaded_dict[i]=f'[Loaded {i * search_limit} through {investigation_count}]'
        i+=1
    if investigation_count==0:
        investigation_data_list=[['No data']]
        loaded_dict[i]='search returns no records'
    

    
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
    with open(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'make_list_investigations.txt')) as json_file:
        make_list=json.load(json_file)
        json_file.close()

    if request.method == 'POST':
        print('!!!!in POST method no_hits_flag:::', no_hits_flag)
        formDict = request.form.to_dict()
        print('formDict:::',formDict)
        search_limit=formDict.get('search_limit')
        if formDict.get('refine_search_button'):
            print('@@@@@@ refine_search_button')
            query_file_name = search_criteria_dictionary_util(formDict, 'current_query_inv.txt')
            
            return redirect(url_for('inv_blueprint.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                investigation_data_list_page=0,search_limit=search_limit))
        # elif formDict.get('load_previous'):
            # investigation_data_list_page=investigation_data_list_page-1
            
            # return redirect(url_for('inv_blueprint.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                # investigation_data_list_page=investigation_data_list_page,
                # search_limit=search_limit))
        # elif formDict.get('load_next'):
            # investigation_data_list_page=investigation_data_list_page+1
            
            # return redirect(url_for('inv_blueprint.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                # investigation_data_list_page=investigation_data_list_page,
                # search_limit=search_limit))            
        elif formDict.get('view'):
            inv_id_for_dash=formDict.get('view')
            return redirect(url_for('inv_blueprint.investigations_dashboard',inv_id_for_dash=inv_id_for_dash))
        
        
        
        
        elif formDict.get('add_category'):
            new_category='sc_category' + str(len(category_dict)+1)
            formDict[new_category]=''
            # del formDict['add_category']
            # formDict['add_category']=''
            query_file_name = search_criteria_dictionary_util(formDict, 'current_query_inv.txt')
            return redirect(url_for('inv_blueprint.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                investigation_data_list_page=0,search_limit=search_limit))
        elif formDict.get('remove_category'):
            
            category_for_remove = 'sc_'+formDict['remove_category']
            # del category_dict[formDict['remove_category']]
            form_dict_cat_element = 'sc_' + formDict['remove_category']
            print('form_dict_cat_element:::',form_dict_cat_element)
            
            del formDict[form_dict_cat_element]
            print('formDict:::',formDict)
            
            query_file_name = search_criteria_dictionary_util(formDict, 'current_query_inv.txt')
            return redirect(url_for('inv_blueprint.search_investigations', query_file_name=query_file_name, no_hits_flag=no_hits_flag,
                investigation_data_list_page=0,search_limit=search_limit))
    
    print('column_names:::', column_names)
    # print('3investigation_data_list:::', len(investigation_data_list), 'page::',investigation_data_list_page)
    print('search_criteria_dictionary loaded to page:', search_criteria_dictionary)
    return render_template('search_investigations.html',table_data = investigation_data_list[int(investigation_data_list_page)], 
        column_names_dict=column_names_dict, column_names=column_names,
        len=len, make_list = make_list, query_file_name=query_file_name,
        search_criteria_dictionary=search_criteria_dictionary,str=str,search_limit=search_limit,
        investigation_count=f'{investigation_count:,}', loaded_dict=loaded_dict,
        investigation_data_list_page=investigation_data_list_page, disable_load_previous=disable_load_previous,
        disable_load_next=disable_load_next, category_list=category_list,category_dict=category_dict,
        user_list=user_list)






@inv_blueprint.route("/investigations_dashboard", methods=["GET","POST"])
@login_required
def investigations_dashboard():
    print('*TOP OF def dashboard()*')
    inv_form=InvForm()
    
    if request.args.get('current_inv_files_dir_name'):
        current_inv_files_dir_name=request.args.get('current_inv_files_dir_name')
    else:
        current_inv_files_dir_name='No file passed'
    
    #view, update
    if request.args.get('inv_id_for_dash'):
        # print('request.args.get(inv_id_for_dash, should build verified_by_list')
        inv_id_for_dash = int(request.args.get('inv_id_for_dash'))
        dash_inv= db.session.query(Investigations).get(inv_id_for_dash)
        verified_by_list =db.session.query(Tracking_inv.updated_to, Tracking_inv.time_stamp).filter_by(
            investigations_table_id=inv_id_for_dash,field_updated='verified_by_user').all()
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
    if dash_inv.files=='' or dash_inv.files==None:
        dash_inv_files=''
    else:
        # if ',' in dash_inv.files:
        dash_inv_files=dash_inv.files.split(',')
    
    #Categories
    if dash_inv.categories=='' or dash_inv.categories==None:
        dash_inv_categories=''
        has_category_flag=False
    else:
        dash_inv_categories=dash_inv.categories.split(',')
        dash_inv_categories=[i.strip() for i in dash_inv_categories]
        has_category_flag=True
        # print('dash_inv_categories:::',dash_inv_categories)
    
    
    #------start get linked reocrds----
    current_record_type='investigations'
    linked_record_type='investigations'
    id_for_dash=inv_id_for_dash
    records_util=record_remover_util(current_record_type,linked_record_type,id_for_dash)
    
    records_array=records_util[0]#list for dropdown
    # insert list of choices for linked records -- entering dashbaord from search:
    inv_form.records_list.choices = [(r.get('id'),r.get('shows_up')) for r in records_array]
    
    dash_inv_linked_records=records_util[1] #list of linked records for dashboard
    #------End of linked reocrds----


    dash_inv_ODATE=None if dash_inv.ODATE ==None else dash_inv.ODATE.strftime("%Y-%m-%d")
    dash_inv_CDATE=None if dash_inv.CDATE ==None else dash_inv.CDATE.strftime("%Y-%m-%d")
    
    
    dash_inv_list = [dash_inv.NHTSA_ACTION_NUMBER,dash_inv.MAKE,dash_inv.MODEL,dash_inv.YEAR,
        dash_inv_ODATE,dash_inv_CDATE,dash_inv.CAMPNO,
        dash_inv.COMPNAME, dash_inv.MFR_NAME, dash_inv.SUBJECT, dash_inv.SUMMARY,
        dash_inv.km_notes, dash_inv.date_updated.strftime('%Y/%m/%d %I:%M%p'), dash_inv_files,
        dash_inv_categories, dash_inv_linked_records]
    
    #Make lists for investigation_entry_top
    inv_entry_top_names_list=['NHTSA Action Number','Make','Model','Year','Open Date','Close Date',
        'Recall Campaign Number','Component Description','Manufacturer Name']
    inv_entry_top_list=zip(inv_entry_top_names_list,dash_inv_list[:9])
    
    #make dictionary of category lists from excel file
    category_list_dict=category_list_dict_util()
    
    category_group_dict_no_space={i:re.sub(r"\s+","",i) for i in list(category_list_dict)}
    
    
    if request.method == 'POST':
        print('!!!!in POST method')
        formDict = request.form.to_dict()
        argsDict = request.args.to_dict()
        filesDict = request.files.to_dict()
        # del formDict['inv_summary_textarea']
        # del formDict['csrf_token']
        record_type=formDict['record_type']
        verified_by_list_util=[i[0] for i in verified_by_list]
        
        if formDict.get('update_inv'):
            print('formDict:::',formDict)
            # print('argsDict:::',argsDict)
            print('filesDict::::',filesDict)
            print('formsDict.Keys():::',formDict.keys())

            if request.files.get('investigation_file'):
                print('!!!!request.files.get(investigation_file:::::')
                
                #new process:
                update_from=dash_inv.files 
                uploaded_file = request.files['investigation_file']
                file_added_flag=update_files_util(filesDict, id_for_dash,'investigation')
                
                if file_added_flag == 'file_added':
                    track_util('investigations', 'files',update_from, dash_inv.files,inv_id_for_dash)
                
            #Update triggered if 1) notes or verified user in formDict
            #2)'cat_' in formDict.keys()
            #3) if has_category_flag but no 'cat_' in formDict.keys()
            update_data_list=['re_km_notes','verified_by_user'] 
            if any(key in update_data_list for key in formDict.keys()) or any(
                'cat_' in key[:4] for key in formDict.keys()) or (
                has_category_flag and not any('cat_' in key[:4] for key in formDict.keys())):
                print('*****item in update_data_list and formDict.keys')
                update_investigation(formDict, inv_id_for_dash, verified_by_list_util)

            #This can only be case if update + user verified previously but no unchecked
            if (current_user.email in verified_by_list_util) and (
                formDict.get('verified_by_user')==None):
                db.session.query(Tracking_inv).filter_by(investigations_table_id=int(inv_id_for_dash),
                    field_updated='verified_by_user',updated_to=current_user.email).delete()
                db.session.commit()
            
            
            return redirect(url_for('inv_blueprint.investigations_dashboard', inv_id_for_dash=inv_id_for_dash,
                current_inv_files_dir_name=current_inv_files_dir_name, record_type=record_type))
                
        elif formDict.get('link_record'):
            # print('!!!!LINKED RECORD formDict:::::', formDict)
            
            #make list in current record to specified record ['type', 'id']
            current_to_specified={
                'record_type':formDict.get('record_type'),
                'record_id':formDict.get('records_list')
                }
            specified_to_current={
                'record_type':'investigations',
                'record_id':str(inv_id_for_dash)
                }
                
            #if existing record has something in linked_records then convert to dict
            if dash_inv.linked_records!= None and dash_inv.linked_records!= '':
                linked_records_dict_current=json.loads(dash_inv.linked_records)
                linked_records_dict_current[formDict.get('record_type')+formDict.get('records_list')]=current_to_specified
            else:
                linked_records_dict_current={formDict.get('record_type')+formDict.get('records_list'):current_to_specified}
              

            
            #check if linked record has
            if formDict.get('record_type')=='investigations':
                #get query of linked record:
                dash_inv_linked= db.session.query(Investigations).get(int(formDict.get('records_list')))
                if dash_inv_linked.linked_records!= None and dash_inv_linked.linked_records!= '':
                    linked_records_dict_for_linked=json.loads(dash_inv_linked.linked_records)
                    linked_records_dict_for_linked['investigations'+str(inv_id_for_dash)]=specified_to_current
                else:
                    linked_records_dict_for_linked={'investigations'+str(inv_id_for_dash):specified_to_current}
            elif formDict.get('record_type')=='recalls':
                #get query of linked record:
                dash_inv_linked= db.session.query(Recalls).get(int(formDict.get('records_list')))
                if dash_inv_linked.linked_records!= None and dash_inv_linked.linked_records!= '':
                    linked_records_dict_for_linked=json.loads(dash_inv_linked.linked_records)
                    linked_records_dict_for_linked['investigations'+str(inv_id_for_dash)]=specified_to_current
                else:
                    linked_records_dict_for_linked={'investigations'+str(inv_id_for_dash):specified_to_current}
                    
            #add list to current record db linked_record
            dash_inv.linked_records=json.dumps(linked_records_dict_current)
            dash_inv_linked.linked_records=json.dumps(linked_records_dict_for_linked)
            db.session.commit()
            
            
            return redirect(url_for('inv_blueprint.investigations_dashboard', record_type=record_type, 
                inv_id_for_dash=inv_id_for_dash,current_inv_files_dir_name=current_inv_files_dir_name))
                
    return render_template('dashboard_inv.html',inv_entry_top_list=inv_entry_top_list,
        dash_inv_list=dash_inv_list, str=str, len=len, inv_id_for_dash=inv_id_for_dash,
        verified_by_list=verified_by_list,checkbox_verified=checkbox_verified, int=int, 
        category_list_dict=category_list_dict, list=list,current_inv_files_dir_name=current_inv_files_dir_name,
        category_group_dict_no_space=category_group_dict_no_space, inv_form=inv_form)



@inv_blueprint.route("/delete_file_inv/<inv_id_for_dash>/<filename>", methods=["GET","POST"])
# @posts.route('/post/<post_id>/update', methods = ["GET", "POST"])
@login_required
def delete_file_inv(inv_id_for_dash,filename):
    #update Investigations table files column
    dash_inv =db.session.query(Investigations).get(inv_id_for_dash)
    update_from=dash_inv.files
    print('delete_file route - dash_inv::::',dash_inv.files)
    file_list=''
    print('filename:::',type(filename),filename)
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
    
    #update tracking
    track_util('investigations', 'files',update_from, dash_inv.files,inv_id_for_dash)
    # newTrack=Tracking_inv(field_updated='files',
        # updated_to=dash_inv.files, updated_by=current_user.id,
        # investigations_table_id=inv_id_for_dash)
    # db.session.add(newTrack)
    # db.session.commit()
    
    
    #Remove files from files dir
    current_inv_files_dir_name = 'Investigation_'+str(inv_id_for_dash)
    current_inv_files_dir=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'], current_inv_files_dir_name)
    files_dir_and_filename=os.path.join(current_app.config['UPLOADED_FILES_FOLDER'],
        current_inv_files_dir_name, filename)
    
    if os.path.exists(files_dir_and_filename):
        os.remove(files_dir_and_filename)
    
    if len(os.listdir(current_inv_files_dir))==0:
        os.rmdir(current_inv_files_dir)
    
    flash('file has been deleted!', 'success')
    return redirect(url_for('inv_blueprint.investigations_dashboard', inv_id_for_dash=inv_id_for_dash))



@inv_blueprint.route("/reports", methods=["GET","POST"])
@login_required
def reports():
    excel_file_name_inv='investigation_report.xlsx'
    excel_file_name_re='recalls_report.xlsx'
    
    #get columns from each reports
    column_names_inv=Investigations.__table__.columns.keys()
    column_names_re=Recalls.__table__.columns.keys()
    categories_dict_inv={}
    categories_dict_re={}
    if os.path.exists(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],excel_file_name_inv)):
        categories_dict_inv,time_stamp_inv=existing_report(excel_file_name_inv, 'investigations')
        print('categories_dict_inv:::', type(categories_dict_inv), categories_dict_inv)
    else:
        time_stamp_inv='no current file'
    if os.path.exists(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],excel_file_name_re)):
        categories_dict_re,time_stamp_re=existing_report(excel_file_name_re,'recalls')
    else:
        time_stamp_re='no current file'


    # print('time_stamp_inv_df:::', time_stamp_inv, type(time_stamp_inv))
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('reports - formDict::::',formDict)
        if formDict.get('build_excel_report_inv'):
            
            column_names_for_df=[i for i in column_names_inv if i in list(formDict.keys())]

            create_categories_xlsx(excel_file_name_inv, column_names_for_df, formDict, 'investigations')
        elif formDict.get('build_excel_report_re'):
            column_names_for_df=[i for i in column_names_re if i in list(formDict.keys())]

            create_categories_xlsx(excel_file_name_re, column_names_for_df, formDict, 'recalls')
        logger.info('in search page')
        return redirect(url_for('inv_blueprint.reports'))
    return render_template('reports.html', excel_file_name_inv=excel_file_name_inv, time_stamp_inv=time_stamp_inv,
        column_names_inv=column_names_inv,column_names_re=column_names_re, categories_dict_inv=categories_dict_inv,
        categories_dict_re=categories_dict_re,time_stamp_re=time_stamp_re, excel_file_name_re=excel_file_name_re)



@inv_blueprint.route("/files_zip", methods=["GET","POST"])
@login_required
def files_zip():
    if os.path.exists(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files')):
        os.remove(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files'))
    shutil.make_archive(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],'Investigation_files'), "zip", os.path.join(
        current_app.config['UPLOADED_FILES_FOLDER']))

    return send_from_directory(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER']),'Investigation_files.zip', as_attachment=True)


@inv_blueprint.route("/categories_report_download", methods=["GET","POST"])
@login_required
def categories_report_download():
    excel_file_name=request.args.get('excel_file_name')

    return send_from_directory(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER']),excel_file_name, as_attachment=True)



@inv_blueprint.route('/get_record/<record_type>/<inv_id_for_dash>')
@login_required
def get_record(record_type,inv_id_for_dash):
    current_record_type='investigations'
    linked_record_type=record_type
    id_for_dash=inv_id_for_dash
    records_array=record_remover_util(current_record_type,linked_record_type,id_for_dash)[0]
        
    return jsonify({'records':records_array})
    


@inv_blueprint.route('/delete_linked_record_investigations/<inv_id_for_dash>/<linked_record>', methods=["GET","POST"])
@login_required
def delete_linked_record_investigations(inv_id_for_dash,linked_record):
    print('ENTER -delete_linked_record')
    print('inv_id_for_dash::::', inv_id_for_dash)
    print('linked_record::::',linked_record)
    #get current record sqlalchemy
    current_record=db.session.query(Investigations).get(int(inv_id_for_dash))
    
    #get linked_record_type
    #get linked_record id
    if linked_record[0:3]=="Inv":
        linked_record_type=linked_record[:14]
        linked_record_id=linked_record[15:15+linked_record[15:].find('|')]
    elif linked_record[0:3]=="Rec":
        linked_record_type=linked_record[:7].lower()
        linked_record_id=linked_record[8:8+linked_record[8:].find('|')]
    
    #make linked_record_key= linked_record_type + id
    linked_record_key=linked_record_type.lower()+linked_record_id
    
    #delete linked_record from current.linked_record using linked_record_key
    cur_records_dict=json.loads(current_record.linked_records)
    print('cur_records_dict::::',cur_records_dict)
    del cur_records_dict[linked_record_key]
    
    current_record.linked_records=json.dumps(cur_records_dict)
    print('cur_records_dict after deleted and should be in 317s linked_records::::',cur_records_dict)
    #Edit LINKED_RECORD's linked record
    #get linked reocrd sqlalchemy
    if linked_record[0:3]=="Inv":
        linked_record_sql=db.session.query(Investigations).get(int(linked_record_id))
    elif linked_record[0:3]=="Rec":
        linked_record_sql=db.session.query(Recalls).get(int(linked_record_id))
        
    #make current_record_key= 'investigations' + id
    current_record_key='investigations' + inv_id_for_dash
    #delete linked_record from linked_record.linked_record using current_record_key
    linked_records_dict=json.loads(linked_record_sql.linked_records)
    print('linked_records_dict::::',linked_records_dict)
    del linked_records_dict[current_record_key]
    linked_record_sql.linked_records=json.dumps(linked_records_dict)
    db.session.commit()
    print('linked_records_dict after deleted and should be in selected linked_records::::',linked_records_dict)
    return redirect(url_for('inv_blueprint.investigations_dashboard', inv_id_for_dash=inv_id_for_dash))

















