from fileShareApp import db
from fileShareApp.models import User, Post, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
import os
from flask import current_app
import json
from datetime import date, datetime
from flask_login import current_user
import pandas as pd


def queryToDict(query_data, column_names):
    # not_include_list=['INFLUENCED_BY', 'MFGTXT', 'RCDATE', 'DATEA', 'RPNO', 'FMVSS',
        # 'DESC_DEFECT', 'CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION','RCL_CMPT_ID']
    # not_include_list=['CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION','RCL_CMPT_ID']
    db_row_list =[]
    for i in query_data:
        row = {key: value for key, value in i.__dict__.items() if key not in ['_sa_instance_state']}
        db_row_list.append(row)
    return db_row_list


def recalls_query_util(query_file_name):
    recalls = db.session.query(Recalls)
    with open(os.path.join(current_app.config['QUERIES_FOLDER'],query_file_name)) as json_file:
        search_criteria_dict=json.load(json_file)
        json_file.close()

    if search_criteria_dict.get("refine_search_button"):
        del search_criteria_dict["refine_search_button"]
    if search_criteria_dict.get("save_search_name"):
        del search_criteria_dict["save_search_name"]
    if search_criteria_dict.get('save_query_button'):
        del search_criteria_dict['save_query_button']
    if search_criteria_dict.get('search_limit'):
        del search_criteria_dict['search_limit']

    for i,j in search_criteria_dict.items():
        if j[1]== "exact":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                recalls = recalls.filter(getattr(Recalls,i)==int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                recalls = recalls.filter(getattr(Recalls,i)==j[0])
            elif j[0]!='':
                recalls = recalls.filter(getattr(Recalls,i)==j[0])
        elif j[1]== "less_than":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                recalls = recalls.filter(getattr(Recalls,i)<int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                recalls = recalls.filter(getattr(Recalls,i)<j[0])
        elif j[1]== "greater_than":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                recalls = recalls.filter(getattr(Recalls,i)>int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                recalls = recalls.filter(getattr(Recalls,i)>j[0])
        elif j[1] =="string_contains" and j[0]!='':
            recalls = recalls.filter(getattr(Recalls,i).contains(j[0]))
    # recalls=recalls.filter(getattr(recalls,'YEAR')>2015).all()
    recalls=recalls.all()
    msg="""END recalls_query_util(query_file_name), returns recalls,
search_criteria_dict. len(recalls) is 
    """
    print(msg, len(recalls), 'search_criteria_dict: ',search_criteria_dict)
    return (recalls,search_criteria_dict)


def search_criteria_dictionary_util(formDict):   
    print('START search_criteria_dictionary_util')
    print('formDict in search_criteria_dictionary_util:::',formDict)
    #remove prefix 'sc_'
    formDict = {(i[3:] if "sc_" in i else i) :j for i,j in formDict.items()}
    
    #make dict of any exact items
    match_type_dict={}
    for i,j in formDict.items():
        if "match_type_" in i:
            match_type_dict[i[11:]]=j

    #make search dict w/out exact keys
    search_query_dict = {i:[j,"string_contains"] for i,j in formDict.items() if "match_type_" not in i}
    
    #if match_type
    for i,j in match_type_dict.items():
        search_query_dict[i]=[list(search_query_dict[i])[0],j]

    query_file_name='current_query_inv.txt'
    with open(os.path.join(current_app.config['QUERIES_FOLDER'],query_file_name),'w') as dict_file:
        json.dump(search_query_dict,dict_file)
    print('END search_criteria_dictionary_util(formDict), returns query_file_name')
    return query_file_name
    
def update_recall(dict, **kwargs):
    print('START update_recall')
    date_flag=False
    # print('in updateInvestigation - dict:::',dict,'kwargs:::',kwargs)
    # formToDbCrosswalkDict = {'inv_number':'NHTSA_ACTION_NUMBER','inv_make':'MAKE',
        # 'inv_model':'MODEL','inv_year':'YEAR','inv_compname':'COMPNAME',
        # 'inv_mfr_name': 'MFR_NAME', 'inv_odate': 'ODATE', 'inv_cdate': 'CDATE',
        # 'inv_campno':'CAMPNO','inv_subject': 'SUBJECT', 'inv_summary_textarea': 'SUMMARY',
        # 'inv_km_notes_textarea': 'km_notes', 'investigation_file': 'files'}

    formToDbCrosswalkDict ={'re_Record ID':'RECORD_ID','re_CAMPNO':'CAMPNO',
        're_MFGCAMPNO':'MFGCAMPNO','re_COMPNAME':'COMPNAME','re_BGMAN':'BGMAN',
        're_ENDMAN':'ENDMAN','re_RCLTYPECD':'RCLTYPECD','re_POTAFF':'POTAFF',
        're_INFLUENCED_BY':'INFLUENCED_BY', 're_MFGTXT':'MFGTXT', 're_RCDATE':'RCDATE',
        're_DATEA':'DATEA','re_RPNO':'RPNO','re_FMVSS':'FMVSS', 're_DESC_DEFECT':'DESC_DEFECT',
        're_CONSEQUENCE_DEFCT':'CONSEQUENCE_DEFCT','re_CORRECTIVE_ACTION':'CORRECTIVE_ACTION',
        're_NOTES':'NOTES', 're_RCL_CMPT_ID':'RCL_CMPT_ID','re_km_notes_textarea': 'km_notes',
        'investigation_file': 'files'}


    update_data = {formToDbCrosswalkDict.get(i): j for i,j in dict.items()}
    # print('update_data::::',update_data)
    
    #create list of categories selected
    no_update_list=['re_Record ID', 're_CAMPNO', 're_MFGCAMPNO', 're_COMPNAME', 're_BGMAN',
        're_ENDMAN', 're_RCLTYPECD', 're_POTAFF', 're_INFLUENCED_BY', 're_MFGTXT', 're_RCDATE',
        're_DATEA', 're_RPNO', 're_FMVSS', 're_DESC_DEFECT', 're_CONSEQUENCE_DEFCT',
        're_CORRECTIVE_ACTION', 're_NOTES', 're_RCL_CMPT_ID', 're_Make', 're_Model', 're_Year',
        're_Manufacturer Name', 're_Open Date']
    not_category_list=['re_km_notes_textarea','update_re','verified_by_user']
    assigned_categories=''
    for i in dict:
        if i not in no_update_list + not_category_list:
            if assigned_categories=='':
                assigned_categories=i
            else:
                assigned_categories=assigned_categories +', '+ i
    
    update_data['categories']=assigned_categories
    
    
    existing_data = db.session.query(Recalls).get(kwargs.get('re_id_for_dash'))
    Recalls_attr=['km_notes', 'categories']
    at_least_one_field_changed = False
    #loop over existing data attributes
    print('update_data:::', update_data)
    
    for i in Recalls_attr:
        if update_data.get(i):
            print('for i in Recalls_attr - loop::',i)
            if str(getattr(existing_data, i)) != update_data.get(i):
                
                print('This should get triggered when updateing summary')
                at_least_one_field_changed = True
                newTrack= Tracking_re(field_updated=i,updated_from=getattr(existing_data, i),
                    updated_to=update_data.get(i), updated_by=current_user.id,
                    recalls_table_id=kwargs.get('re_id_for_dash'))
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
            pass
            # print('do nothing')
        # elif kwargs.get('verified_by_list') ==[] or any(current_user.email not in s for s in kwargs.get('verified_by_list')):
        else:
            print('user verified adding to Tracking_re table')
            at_least_one_field_changed = True
            newTrack=Tracking_re(field_updated='verified_by_user',
                updated_to=current_user.email, updated_by=current_user.id,
                recalls_table_id=kwargs.get('re_id_for_dash'))
            db.session.add(newTrack)
            db.session.commit()
    else:
        # print('no verified user added')
        if any(current_user.email in s for s in kwargs.get('verified_by_list')):
            db.session.query(Tracking_re).filter_by(recalls_table_id=kwargs.get('re_id_for_dash'),
                field_updated='verified_by_user',updated_to=current_user.email).delete()
            db.session.commit()
            
    if at_least_one_field_changed:
        print('at_least_one_field_changed::::',at_least_one_field_changed)
        setattr(existing_data, 'date_updated' ,datetime.now())
        db.session.commit()
    if date_flag:
        flash(date_flag, 'warning')
    print('END update_recall')
    # print('end updateInvestigation util')
        #if there is a corresponding update different from existing_data:
        #1.add row to Tracking_re datatable
        #2.update existing_data with change       


def update_files_re(filesDict, **kwargs):
    print('START update_files_re')
    date_flag=False
    # print('in update_files - filesDict:::',filesDict,'kwargs:::',kwargs)
    formToDbCrosswalkDict = {'investigation_file': 'files'}

    update_data = {formToDbCrosswalkDict.get(i): j for i,j in filesDict.items()}
    existing_data = db.session.query(Investigations).get(kwargs.get('re_id_for_dash'))
    # for i in Investigations_attr:
    at_least_one_field_changed = False
    if update_data.get('files') not in [existing_data.files,'']:
    #if different an not null then add
        print('files update --- values not the same')
        at_least_one_field_changed = True
        newTrack=Tracking_re(field_updated='verified_by_user',
            updated_to=current_user.email, updated_by=current_user.id,
            recalls_table_id=kwargs.get('re_id_for_dash'))
        db.session.add(newTrack)
        db.session.commit()
    if at_least_one_field_changed:
        print('at_least_one_field_changed::::',at_least_one_field_changed)
        setattr(existing_data, 'date_updated' ,datetime.now())
        db.session.commit()
    if date_flag:
        flash(date_flag, 'warning')
    print('END update_files_re')

def create_categories_xlsx(excel_file_name):
    print('START create_categories_xlsx')
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
    print('END create_categories_xlsx')
