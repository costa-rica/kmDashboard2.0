from fileShareApp import db
from fileShareApp.models import User, Post, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
import os
from flask import current_app
import json
from datetime import date, datetime
from flask_login import current_user
import pandas as pd

def updateInvestigation(dict, **kwargs):
    date_flag=False
    print('in updateInvestigation - dict:::',dict,'kwargs:::',kwargs)
    formToDbCrosswalkDict = {'inv_number':'NHTSA_ACTION_NUMBER','inv_make':'MAKE',
        'inv_model':'MODEL','inv_year':'YEAR','inv_compname':'COMPNAME',
        'inv_mfr_name': 'MFR_NAME', 'inv_odate': 'ODATE', 'inv_cdate': 'CDATE',
        'inv_campno':'CAMPNO','inv_subject': 'SUBJECT', 'inv_summary_textarea': 'SUMMARY',
        'inv_km_notes_textarea': 'km_notes', 'investigation_file)': 'files'}

    update_data = {formToDbCrosswalkDict.get(i): j for i,j in dict.items()}
    print('update_data::::',update_data)
    
    #create list of categories selected
    no_update_list=['inv_NHTSA Action Number','inv_Make', 'inv_Model','inv_Year','inv_Open Date',
                   'inv_Close Date','inv_Recall Campaign Number', 'inv_Component Description',
                   'inv_Manufacturer Name', 'inv_subject','inv_summary_textarea']
    not_category_list=['inv_km_notes_textarea','update_inv','verified_by_user']
    assigned_categories=''
    for i in dict:
        if i not in no_update_list + not_category_list:
            if assigned_categories=='':
                assigned_categories=i
            else:
                assigned_categories=assigned_categories +', '+ i
    
    update_data['categories']=assigned_categories
    
    
    existing_data = db.session.query(Investigations).get(kwargs.get('inv_id_for_dash'))
    Investigations_attr=['SUBJECT','SUMMARY','km_notes','date_updated','files', 'categories']
    at_least_one_field_changed = False
    #loop over existing data attributes
    print('update_data:::', update_data)
    
    for i in Investigations_attr:
        if update_data.get(i):

            if str(getattr(existing_data, i)) != update_data.get(i):
                
                print('This should get triggered when updateing summary')
                at_least_one_field_changed = True
                newTrack= Tracking_inv(field_updated=i,updated_from=getattr(existing_data, i),
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
            print('user verified adding to Tracking_inv table')
            at_least_one_field_changed = True
            newTrack=Tracking_inv(field_updated='verified_by_user',
                updated_to=current_user.email, updated_by=current_user.id,
                investigations_table_id=kwargs.get('inv_id_for_dash'))
            db.session.add(newTrack)
            db.session.commit()
    else:
        print('no verified user added')
        if any(current_user.email in s for s in kwargs.get('verified_by_list')):
            db.session.query(Tracking_inv).filter_by(investigations_table_id=kwargs.get('inv_id_for_dash'),
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
        #1.add row to Tracking_inv datatable
        #2.update existing_data with change       



def create_categories_xlsx(excel_file_name):

    excelObj=pd.ExcelWriter(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],excel_file_name))

    columnNames=Investigations.__table__.columns.keys()
    colNamesDf=pd.DataFrame([columnNames],columns=columnNames)
    colNamesDf.to_excel(excelObj,sheet_name='Investigation Data', header=False, index=False)

    queryDf = pd.read_sql_table('investigations', db.engine)
    queryDf.to_excel(excelObj,sheet_name='Investigation Data', header=False, index=False,startrow=1)
    inv_data_workbook=excelObj.book
    notes_worksheet = inv_data_workbook.add_worksheet('Notes')
    notes_worksheet.write('A1','Created:')
    notes_worksheet.set_column(1,1,len(str(datetime.now())))
    time_stamp_format = inv_data_workbook.add_format({'num_format': 'mmm d yyyy hh:mm:ss AM/PM'})
    notes_worksheet.write('B1',datetime.now(), time_stamp_format)
    excelObj.close()