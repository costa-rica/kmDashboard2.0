from fileShareApp import db, bcrypt, mail
from fileShareApp.models import Post, User, Investigations, Kmtracking,Km_saved_queries
from sqlalchemy import func, desc
import pandas as pd
from flask_login import current_user
import ast
import json
from fileShareApp.custom_dict import doubleQuoteDict
import os
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from os import listdir
from datetime import date, datetime

def queryToDict(query_data, column_names):
    db_row_list =[]
    for i in query_data:
        row = {key: value for key, value in i.__dict__.items() if key not in ['_sa_instance_state']}
        db_row_list.append(row)
    return db_row_list

def updateInvestigation(dict, **kwargs):
    date_flag=False
    print('in updateInvestigation - dict:::',dict,'kwargs:::',kwargs)
    formToDbCrosswalkDict = {'inv_number':'NHTSA_ACTION_NUMBER','inv_make':'MAKE',
        'inv_model':'MODEL','inv_year':'YEAR','inv_compname':'COMPNAME',
        'inv_mfr_name': 'MFR_NAME', 'inv_odate': 'ODATE', 'inv_cdate': 'CDATE',
        'inv_campno':'CAMPNO','inv_subject': 'SUBJECT', 'inv_summary_textarea': 'SUMMARY',
        'inv_km_notes_textarea': 'km_notes', 'investigation_file)': 'files'}
    # if dict.get('investigation_file'):
        # print('dict.get(investigation_file)::::',type(dict.get('investigation_file')),
            # dict.get('investigation_file'))
        # uploaded_file_list = [ i.filename for i in dict.get('investigation_file')]
        # update_data = {'files': uploaded_file_list}
        # print('update_data:::', update_data)
    # else:
    update_data = {formToDbCrosswalkDict.get(i): j for i,j in dict.items()}
    existing_data = db.session.query(Investigations).get(kwargs.get('inv_id_for_dash'))
    # Investigations_attr=['id','NHTSA_ACTION_NUMBER', 'MAKE', 'MODEL', 'YEAR', 'COMPNAME', 'MFR_NAME',
        # 'ODATE','CDATE','CAMPNO','SUBJECT','SUMMARY','km_notes','date_updated','files','km_tracking_id']
    Investigations_attr=['SUBJECT','SUMMARY','km_notes','date_updated','files']
    at_least_one_field_changed = False
    #loop over existing data attributes
    print('update_data:::', update_data)
    
    for i in Investigations_attr:
        # if i== 'SUMMARY':
            # print('Investigations_attr --- SUMMARY,,, existing dagta is:',getattr(existing_data, i))
            # print('Investigations_attr --- SUMMARY,,, update data is:', update_data.get(i))
        if update_data.get(i):
            # if i in ['ODATE','CDATE']:
                # if str(getattr(existing_data, i).date()) != update_data.get(i):
                    # at_least_one_field_changed = True
                    # print('existing_data for ',i,':::',type(getattr(existing_data, i)), getattr(existing_data, i))
                    # print('update_data for ',i,':::', type(update_data.get(i)), update_data.get(i))
                    # try:
                        # datetime_obj=datetime. strptime(update_data.get(i), '%Y-%m-%d')
                        # setattr(existing_data, i ,datetime_obj)
                    # except:
                        # date_flag = 'Date entered incorrectly. Not updated. Use YYYY-MM-DD format.'
                        # continue
                # else:
                    # print(i, ' has no change')
            # elif i=='YEAR':
                # if str(getattr(existing_data, i)) != update_data.get(i):
                    # print('existing_data for ',i,':::',type(getattr(existing_data, i)), getattr(existing_data, i))
                    # print('update_data for ',i,':::', type(update_data.get(i)), update_data.get(i))
                    # at_least_one_field_changed = True
                    # setattr(existing_data, i ,int(update_data.get(i)))
                    # newTrack= Kmtracking(field_updated=i,updated_from=getattr(existing_data, i),
                        # updated_to=update_data.get(i), updated_by=current_user.id,
                        # investigations_table_id=kwargs.get('inv_id_for_dash'))
                    # db.session.add(newTrack)
                    # db.session.commit()
                # else:
                    # print(i, ' has no change')
            if str(getattr(existing_data, i)) != update_data.get(i):
                
                print('This should get triggered when updateing summary')
                at_least_one_field_changed = True
                newTrack= Kmtracking(field_updated=i,updated_from=getattr(existing_data, i),
                    updated_to=update_data.get(i), updated_by=current_user.id,
                    investigations_table_id=kwargs.get('inv_id_for_dash'))
                db.session.add(newTrack)
                # print('added ',i,'==', update_data.get(i),' to KmTracker')
                #Actually change database data here:
                setattr(existing_data, i ,update_data.get(i))

                # print('updated investigations table with ',i,'==', update_data.get(i))
                db.session.commit()
            else:
                print(i, ' has no change')

    if dict.get('verified_by_user'):
        if any(current_user.email in s for s in kwargs.get('verified_by_list')):
            print('do nothing')
        # elif kwargs.get('verified_by_list') ==[] or any(current_user.email not in s for s in kwargs.get('verified_by_list')):
        else:
            print('user verified adding to Kmtracking table')
            at_least_one_field_changed = True
            newTrack=Kmtracking(field_updated='verified_by_user',
                updated_to=current_user.email, updated_by=current_user.id,
                investigations_table_id=kwargs.get('inv_id_for_dash'))
            db.session.add(newTrack)
            db.session.commit()
    else:
        print('no verified user added')
        if any(current_user.email in s for s in kwargs.get('verified_by_list')):
            db.session.query(Kmtracking).filter_by(investigations_table_id=kwargs.get('inv_id_for_dash'),
                field_updated='verified_by_user',updated_to=current_user.email).delete()
            db.session.commit()
            
    if at_least_one_field_changed:
        print('at_least_one_field_changed::::',at_least_one_field_changed)
        setattr(existing_data, 'date_updated' ,datetime.now())
        db.session.commit()
    if date_flag:
        flash(date_flag, 'warning')
    
    print('end updateInvestigation util')
        #if there is a corresponding update different from existing_data:
        #1.add row to kmtracking datatable
        #2.update existing_data with change        
    

def search_criteria_dictionary_util(formDict):   
    print('formDict in search_criteria_dictionary_util:::',formDict)
    #remove prefix 'sc_'
    formDict = {(i[3:] if "sc_" in i else i) :j for i,j in formDict.items()}
    #make dict of any exact items
    exactDict = {i[6:]:j for i,j in formDict.items() if "exact_" in i} 
    #make search dict w/out exact keys
    search_query_dict = {i:[j,"string_contains"] for i,j in formDict.items() if "exact_" not in i}
    print('exactDict', exactDict)
    #if exact change 'exact'
    for i,j in exactDict.items():
        search_query_dict[i]=[list(search_query_dict[i])[0],"exact"]
    print('search_query_dict::::',search_query_dict)
    # file_number_list= [int(i[5:10]) for i in listdir(current_app.config['QUERIES_FOLDER'])]
    # query_file_name = 'query'+str(max(file_number_list)+1).zfill(5) +'.txt'
    query_file_name='current_query.txt'
    with open(os.path.join(current_app.config['QUERIES_FOLDER'],query_file_name),'w') as dict_file:
        json.dump(search_query_dict,dict_file)
    return query_file_name

def investigations_query_util(query_file_name):
    investigations = db.session.query(Investigations)
    with open(os.path.join(current_app.config['QUERIES_FOLDER'],query_file_name)) as json_file:
        search_criteria_dict=json.load(json_file)
        json_file.close()

    if search_criteria_dict.get("refine_search_button"):
        del search_criteria_dict["refine_search_button"]
    if search_criteria_dict.get("save_search_name"):
        del search_criteria_dict["save_search_name"]
    if search_criteria_dict.get('save_query_button'):
        del search_criteria_dict['save_query_button']

    loop_count=0
    for i,j in search_criteria_dict.items():
        if j[1]== "exact":
            if i=='YEAR' and j[0]!='':
                print('excat - YEAR is investigations_query_util:::',type(j[0]),j[0])
                j[0]=int(j[0])
                print('YEAR afer conversion is investigations_query_util:::',type(j[0]),j[0])
            elif i in ['ODATE','CDATE'] and j[0]!='':
                print('exact ODATE and CDATE fire***')
                print(i,j[0])
                j[0]=datetime.strptime(j[0],'%Y-%m-%d')
                print('i and j[0] after convertsion of j[0].....',i,j, type(j[0]))
                loop_count+=1
                investigations = investigations.filter(getattr(Investigations,i)==j[0])
            else:
                investigations = investigations.filter(getattr(Investigations,i)==j[0])
        elif j[1] =="string_contains":
            # if i=='YEAR' and j[0]!='':
                # print('string contains - YEAR is investigations_query_util:::',type(j[0]),j[0])
                # j[0]=int(j[0])
                # print('YEAR afer conversion is investigations_query_util:::',type(j[0]),j[0])
            # elif i in ['ODATE','CDATE'] and j[0]!='':
                # print('string contains ODATE or CDATE fires***')
                # print(i,j[0])
                # j[0]=datetime.strptime(j[0],'%Y-%m-%d')
                # loop_count+=1
            investigations = investigations.filter(getattr(Investigations,i).contains(j[0]))
    investigations=investigations.filter(getattr(Investigations,'YEAR')>2015).all()
    print('loop_count:::',loop_count)
    return (investigations,search_criteria_dict)


def save_query_util(dict):
    query_file_name = search_criteria_dictionary_util(dict)
    # query_name = dict.get('save_search_name')
    query_to_save = Km_saved_queries(query_name=dict.get('save_search_name'),
        query=query_file_name,created_by=current_user.id)
    db.session.add(query_to_save)
    db.session.commit()
    print('Added ',query_file_name, ' to saved queries table')
    return query_file_name


