from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from fileShareApp import db, bcrypt, mail
from fileShareApp.models import Post, User, Investigations, Kmtracking
# from fileShareApp.main.forms import EmployeeForm, AddRestaurantForm, DatabaseForm, AddRoleForm
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
# from fileShareApp.main.utils 
from fileShareApp.buckets.utils import queryToDict, updateInvestigation, \
    search_criteria_dictionary_util, investigations_query_util, save_query_util
import openpyxl
from werkzeug.utils import secure_filename
import json
import glob
import ast
from fileShareApp.custom_dict import doubleQuoteDict
# from flask_login import login_user, current_user, logout_user, login_required

buckets = Blueprint('buckets', __name__)



@buckets.route("/home_dashboard", methods=["GET","POST"])
@login_required
def home_dashboard():
    print('*TOP OF def home()*')
    print('top of home - request.args:::',type(request.args),request.args)
    # print('request.args dictionary:::',request.args.to_dict())
    formDict = request.form.to_dict()
    print('top of home - reqeust.form:::',formDict)
    #all
    column_names=['id','NHTSA_ACTION_NUMBER', 'MAKE','MODEL','YEAR','COMPNAME','MFR_NAME',
        'ODATE','CDATE','CAMPNO','SUBJECT']

    #login takes else
    if request.args.get('query_file_name'):
        query_file_name=request.args.get('query_file_name')
        print('request.args exists::::',request.args.get('query_file_name'))
        print('***NOT login path***')
        investigations_query, search_criteria_dictionary = investigations_query_util(query_file_name)
        # investigations_query=investigations_query.filter(getattr(Investigations,'YEAR')>2015).all()
        print('investigations_query results:::', len(investigations_query))
        print('search_criteria_dictionary results:::',  search_criteria_dictionary)
        no_hits_flag = False
        if len(investigations_query) ==0:
            no_hits_flag = True
    elif request.args.get('no_hits_flag')==True:
        investigations_query, search_criteria_dictionary = ([],{})
    else:
        query_file_name= 'default_query.txt'
        investigations_query, search_criteria_dictionary = investigations_query_util(query_file_name)
        # investigations_query=investigations_query.filter(getattr(Investigations,'YEAR')>2015).all()
        print('investigations_query results:::', len(investigations_query))
        no_hits_flag = False
        if len(investigations_query) ==0:
            no_hits_flag = True
        
    #view, update
    if request.args.get('inv_id_for_dash'):
        inv_id_for_dash = request.args.get('inv_id_for_dash')
        dash_inv= db.session.query(Investigations).get(inv_id_for_dash)
        verified_by_list =db.session.query(Kmtracking.updated_to, Kmtracking.time_stamp).filter_by(
            investigations_table_id=inv_id_for_dash,field_updated='verified_by_user').all()
        verified_by_list=[[i[0],i[1].strftime('%Y/%m/%d %#I:%M%p')] for i in verified_by_list]
    #login, search
    elif len(investigations_query)>0:
        dash_inv=investigations_query[0]
        inv_id_for_dash=dash_inv.id
        verified_by_list =db.session.query(Kmtracking.updated_to, Kmtracking.time_stamp).filter_by(
            investigations_table_id=inv_id_for_dash,field_updated='verified_by_user').all()
        verified_by_list=[[i[0],i[1].strftime('%Y/%m/%d %#I:%M%p')] for i in verified_by_list]
    else:
        verified_by_list=[]

    #pass check or no check for current_user
    if any(current_user.email in s for s in verified_by_list):
        checkbox_verified = 'checked'
    else:
        checkbox_verified = ''
        
    if request.method == 'POST':
        print('!!!!in POST method no_hits_flag:::', no_hits_flag)
        # formDict = doubleQuoteDict(request.form)
        formDict = request.form.to_dict()
        argsDict = request.args.to_dict()
        filesDict = request.files.to_dict()
        print('requst.method=== -POST')
        print('argsDict:::',len(argsDict),argsDict)
        print('formDict::::', len(formDict),formDict)
        print('filesDict:::', len(filesDict), filesDict)
        print('filesDict.get(investigation_file)::::',type(filesDict.get('investigation_file')),
            filesDict.get('investigation_file'))
        
        # if no_hits_flag == True:
            # print('@@@@@@@no_hits_fla')
            # flash('Your query returned no new results. Below is default query.', 'warning')
            # return redirect(url_for('buckets.home', query_file_name=query_file_name))
        if formDict.get('view'):
            print('@@@@@2VIEW')
            print('clicked view - formDict::', formDict)
            return redirect(url_for('buckets.home', inv_id_for_dash=formDict.get('view'),
                query_file_name=query_file_name))

        elif formDict.get('refine_search_button'):
            print('@@@@@@ refine_search_button')
            query_file_name = search_criteria_dictionary_util(formDict)
            return redirect(url_for('buckets.home', query_file_name=query_file_name, no_hits_flag=no_hits_flag))
        elif formDict.get('update_inv'):
            print('@@@@@@route - updateInvestigation')
            if len(formDict)>0:#I think this is the only case. I.E if you click update the form has something in it. Nothing else can happen????
                updateInvestigation(formDict, inv_id_for_dash=inv_id_for_dash, verified_by_list=verified_by_list)
                print('!!!!!update_inv args.get(inv_id_for_dash) and formDict')
            else:
                print('*****unexpected case of argsDict and formDict lengths both greater than zero or equal to zero***')
                print('lengths arre, args: ',len(argsDict),'form: ',len(formDict))
            if request.files.get('investigation_file'):
                # print('filesDict.get(investigation_file).filename::::',len(filesDict.get('investigation_file')),
                # type(filesDict.get('investigation_file')),
                # filesDict.get('investigation_file').filename)
                
                # uploaded_file_list = [ i.filename for i in filesDict.get('investigation_file')]
                new_filesDict = {'investigation_file)': filesDict.get('investigation_file').filename}
                
                updateInvestigation(filesDict, inv_id_for_dash=inv_id_for_dash, verified_by_list=verified_by_list)
                
                uploaded_file = request.files['investigation_file']
                uploaded_file.save(os.path.join(current_app.config['UPLOADED_FILES_FOLDER'],uploaded_file.filename))
                # existing_data = db.session.query(Investigations).get(argsDict['inv_id_for_dash'])
                print('What is dash_inv.files before adding:::',type(dash_inv.files),dash_inv.files)
                if dash_inv.files =='':
                    file_list = uploaded_file.filename
                    dash_inv.files=str(file_list.split(','))
                else:
                    file_list=dash_inv.files.split(',')
                    file_list.append(uploaded_file.filename)
                    dash_inv.files=str(file_list)
                
                db.session.commit()
            return redirect(url_for('buckets.home', inv_id_for_dash=inv_id_for_dash,
                query_file_name=query_file_name))
        elif formDict.get('save_query_button'):
            query_file_name=save_query_util(formDict)
            return redirect(url_for('buckets.home', inv_id_for_dash=inv_id_for_dash,
                query_file_name=query_file_name, _anchor='search'))
            #save query to file -- same as search_criteria_dictionary_util
            
            #add recrod to km_save_queries table

#***Moved from top***

    #all
    #make search_criteria_dict complete with empty values for keys not searched
    for i in column_names:
        if i not in search_criteria_dictionary:
            search_criteria_dictionary[i]=""

    #all - get Files linked to investigation record
    if no_hits_flag == True:
        dash_inv_list=['','','','','','','','','','','','','','','','','','','']
        inv_id_for_dash='no investigations found'
    # elif dash_inv.files != '':
        # if (",") in dash_inv.files:
            # file_list=dash_inv.files.split(",")
        # elif ("[") in dash_inv.files:
            # dash_inv_files = ast.literal_eval(dash_inv.files)
            # file_list=dash_inv_files
        # else:
            # file_list=[]
            # file_list.append(dash_inv.files)
            
        # dash_inv_list = [dash_inv.NHTSA_ACTION_NUMBER,dash_inv.MAKE,dash_inv.MODEL,dash_inv.YEAR,
            # dash_inv.ODATE.strftime("%Y-%m-%d"),dash_inv.CDATE.strftime("%Y-%m-%d"), dash_inv.CAMPNO,
            # dash_inv.COMPNAME, dash_inv.MFR_NAME, dash_inv.SUBJECT, dash_inv.SUMMARY,
            # dash_inv.km_notes, dash_inv.date_updated.strftime('%Y/%m/%d %I:%M%p'), file_list]
        # print('dash_inv_list (no dash_inv.files):::',dash_inv_list)
    else:
        dash_inv_list = [dash_inv.NHTSA_ACTION_NUMBER,dash_inv.MAKE,dash_inv.MODEL,dash_inv.YEAR,
            dash_inv.ODATE.strftime("%Y-%m-%d"),dash_inv.CDATE.strftime("%Y-%m-%d"),dash_inv.CAMPNO,
            dash_inv.COMPNAME, dash_inv.MFR_NAME, dash_inv.SUBJECT, dash_inv.SUMMARY,
            dash_inv.km_notes, dash_inv.date_updated.strftime('%Y/%m/%d %I:%M%p'), dash_inv.files.split(',')]
        print('dash_inv_list (YES dash_inv.files):::',dash_inv_list)
        print('dash_inv.files::::',type(dash_inv.files), dash_inv.files)
        # dash_inv.files=dash_inv.files.split(',')
        # print('dash_inv.files::::',type(dash_inv.files), dash_inv.files)
    #all
    #Make investigations to dictionary for bit table bottom of home screen
    investigations_data = queryToDict(investigations_query, column_names)#List of dicts each dict is row

    #all
    #make make_list drop down options
    with open(os.path.join(current_app.config['UTILITY_FILES_FOLDER'],'make_list.txt')) as json_file:
        make_list=json.load(json_file)
        json_file.close()
#***end move***
#Make lists for investigation_entry_top
    inv_entry_top_names_list=['NHTSA Action Number','Make','Model','Year','Open Date','Close Date',
        'Recall Campaign Number','Component Description','Manufacturer Name']
    inv_entry_top_list=zip(inv_entry_top_names_list,dash_inv_list[:9])


    return render_template('home_dashboard.html', table_data = investigations_data, column_names=column_names,
        len=len, dash_inv_list=dash_inv_list, inv_id_for_dash=inv_id_for_dash, make_list = make_list,
        query_file_name=query_file_name, search_criteria_dictionary=search_criteria_dictionary,
        verified_by_list=verified_by_list,checkbox_verified=checkbox_verified, str=str,
        inv_entry_top_list=inv_entry_top_list)




        