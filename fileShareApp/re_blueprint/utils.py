from fileShareApp import db
from fileShareApp.models import User, Post, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
import os
from flask import current_app
import json
from datetime import date, datetime
from flask_login import current_user
import pandas as pd
import re
from fileShareApp.inv_blueprint.utils_general import track_util

def column_names_dict_re_util():
    column_names_dict={'RECORD_ID':'Record ID','CAMPNO':'Recall Campaign Number','MAKETXT':'Make',
    'MODELTXT':'Model','YEAR':'Year', 'COMPNAME':'Component Name',
    'MFGNAME':'Manufacturer Name',
    'BGMAN':'BGMAN',
    'MFGCAMPNO':'MFGCAMPNO',
    'ENDMAN':'ENDMAN',
    'RCLTYPECD':'RCLTYPECD',
    'POTAFF':'POTAFF',
    'ODATE':'ODATE',
    'INFLUENCED_BY':'INFLUENCED_BY',
    'MFGTXT':'MFGTXT',
    'RCDATE':'RCDATE',
    'DATEA':'DATEA','RPNO':'RPNO', 'FMVSS':'FMVSS','DESC_DEFECT':'DESC_DEFECT',
    'CONSEQUENCE_DEFCT':'CONSEQUENCE_DEFCT','CORRECTIVE_ACTION':'CORRECTIVE_ACTION','RCL_CMPT_ID':'RCL_CMPT_ID'}
    return column_names_dict

def column_names_re_util():
    column_names=['RECORD_ID', 'CAMPNO', 'MAKETXT', 'MODELTXT', 'YEAR', 'MFGCAMPNO',
       'COMPNAME', 'MFGNAME', 'BGMAN', 'ENDMAN', 'RCLTYPECD', 'POTAFF',
       'ODATE', 'INFLUENCED_BY', 'MFGTXT', 'RCDATE', 'DATEA', 'RPNO', 'FMVSS',
       'DESC_DEFECT', 'CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION','RCL_CMPT_ID','categories']
    return column_names


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

    if search_criteria_dict.get('user'):
        if search_criteria_dict.get('user')[0]!='':
            # print('this should not fire if no user')
        #search_criteria_dict.get('user') comes in as a list of [string containing all users or single user, 'string contains']
            #get users verified
            user_criteria = [a for a in re.split(r'(\s|\,)',  search_criteria_dict.get('user')[0].strip()) if len(a)>1]
            table_ids_dict={}
            for j in user_criteria:
                recalls_table_ids=db.session.query(Tracking_re.recalls_table_id).filter(Tracking_re.updated_to.contains(j)).distinct().all()
                recalls_table_ids=[i[0] for i in recalls_table_ids]
                print('recalls_table_ids:::',recalls_table_ids)
                table_ids_dict[j]=recalls_table_ids
            
            # print('table_ids_dict::',table_ids_dict)
            #get list of records users 
            n=0
            for i,j in table_ids_dict.items():
                if n==0:
                    table_ids_list=j
                else:
                    for k in j:
                        if k not in table_ids_list:
                            del[k]
            
            #filter recalls query by anything that contains
            if len(table_ids_list)>0:
                recalls = recalls.filter(getattr(Recalls,'RECORD_ID').in_(table_ids_list))


    #put all 'category' elements in another dictionary
    category_dict={}
    for i,j in search_criteria_dict.items():
        if 'category' in i:
            category_dict[i]=j

    #filter recalls query by anything that contains
    flag = [key for key, value in search_criteria_dict.items() if 'category' in key]
    if len(flag)>0:
        for i,j in category_dict.items():
            if j[0]!='':
                recalls = recalls.filter(getattr(Recalls,'categories').contains(j[0]))

    #take out all keys that contain "cateogry"
    for i,j in category_dict.items():
        del search_criteria_dict[i]
            

    


    for i,j in search_criteria_dict.items():
        if j[1]== "exact":
            if i in ['RECORD_ID','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                recalls = recalls.filter(getattr(Recalls,i)==int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                recalls = recalls.filter(getattr(Recalls,i)==j[0])
            elif j[0]!='':
                recalls = recalls.filter(getattr(Recalls,i)==j[0])
        elif j[1]== "less_than":
            if i in ['RECORD_ID','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                recalls = recalls.filter(getattr(Recalls,i)<int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                recalls = recalls.filter(getattr(Recalls,i)<j[0])
        elif j[1]== "greater_than":
            if i in ['RECORD_ID','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                recalls = recalls.filter(getattr(Recalls,i)>int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                recalls = recalls.filter(getattr(Recalls,i)>j[0])
        elif j[1] =="string_contains" and j[0]!='':
            if i not in ['user']:
                recalls = recalls.filter(getattr(Recalls,i).contains(j[0]))
    recalls=recalls.filter(getattr(Recalls,'ODATE')>="2011-01-01")
    
    recalls=recalls.all()
    msg="""END recalls_query_util(query_file_name), returns recalls,
search_criteria_dict. len(recalls) is 
    """
    
    search_criteria_dict.update(category_dict)
    # print(msg, len(recalls), 'search_criteria_dict: ',search_criteria_dict)
    return (recalls,search_criteria_dict, category_dict)



    
def update_recall(formDict, re_id_for_dash, verified_by_list):
    print('START update_recall')
    # date_flag=False

    #convert formDict keys to Recalls table column names
    formToDbCrosswalkDict ={'re_Record ID':'RECORD_ID','re_CAMPNO':'CAMPNO',
        're_MFGCAMPNO':'MFGCAMPNO','re_COMPNAME':'COMPNAME','re_BGMAN':'BGMAN',
        're_ENDMAN':'ENDMAN','re_RCLTYPECD':'RCLTYPECD','re_POTAFF':'POTAFF',
        're_INFLUENCED_BY':'INFLUENCED_BY', 're_MFGTXT':'MFGTXT', 're_RCDATE':'RCDATE',
        're_DATEA':'DATEA','re_RPNO':'RPNO','re_FMVSS':'FMVSS', 're_DESC_DEFECT':'DESC_DEFECT',
        're_CONSEQUENCE_DEFCT':'CONSEQUENCE_DEFCT','re_CORRECTIVE_ACTION':'CORRECTIVE_ACTION',
        're_NOTES':'NOTES', 're_RCL_CMPT_ID':'RCL_CMPT_ID','re_km_notes': 'km_notes',
        'recall_file': 'files'}
    update_data = {formToDbCrosswalkDict.get(i): j for i,j in formDict.items()}
    # print('update_data::::',update_data)
    
    #important for category list
    # no_update_list=['re_Record ID', 're_CAMPNO', 're_MFGCAMPNO', 're_COMPNAME', 're_BGMAN',
        # 're_ENDMAN', 're_RCLTYPECD', 're_POTAFF', 're_INFLUENCED_BY', 're_MFGTXT', 're_RCDATE',
        # 're_DATEA', 're_RPNO', 're_FMVSS', 're_DESC_DEFECT', 're_CONSEQUENCE_DEFCT',
        # 're_CORRECTIVE_ACTION', 're_NOTES', 're_RCL_CMPT_ID', 're_Make', 're_Model', 're_Year',
        # 're_Manufacturer Name', 're_Open Date','update_re','verified_by_user','recall_file',
        # 'record_type','records_list','re_km_notes']
    #removed from no_update_list: 're_km_notes_textarea',
    assigned_categories=''
    for i in formDict:
        # if i not in no_update_list:
        if i[:4]=='cat_':
            print('formDict value in assigned category:::',i)
            if assigned_categories=='':
                assigned_categories=i[4:]
            else:
                assigned_categories=assigned_categories +', '+ i[4:]
    update_data['categories']=assigned_categories
    #END important for category list
    
    existing_data = db.session.query(Recalls).get(int(re_id_for_dash))
    Recalls_attr=['km_notes', 'categories']
    # at_least_one_field_changed = False
    #loop over existing data attributes
    print('update_data:::', update_data)
    
    for i in Recalls_attr:
        if str(getattr(existing_data, i)) != update_data.get(i):
            
            update_from=str(getattr(existing_data, i))
            
            if update_data.get(i)==None:
                update_value=''
            else:
                update_value=update_data.get(i)                
            
            #Actually change database data here:
            setattr(existing_data, i ,update_data.get(i))
            
            #Change timestamp of record last update
            setattr(existing_data, 'date_updated' ,datetime.now())
            
            db.session.commit()
            
            #Track change in Track_inv table here
            track_util('recalls', i,update_from, update_data.get(i),re_id_for_dash)
            # newTrack= Tracking_re(field_updated=i,updated_from=getattr(existing_data, i),
                # updated_to=update_data.get(i), updated_by=current_user.id,
                # recalls_table_id=kwargs.get('re_id_for_dash'))
            # db.session.add(newTrack)
        # else:
            # print(i, ' has no change')

    if formDict.get('verified_by_user'):
        # if current_user.email not in verified_by_list:
            # pass
            # print('do nothing')
        # elif kwargs.get('verified_by_list') ==[] or any(current_user.email not in s for s in kwargs.get('verified_by_list')):
        # else:

        
        
        if current_user.email not in verified_by_list:
            track_util('recalls', 'verified_by_user','',current_user.email,re_id_for_dash)
            # print('user verified adding to Tracking_re table')
            # at_least_one_field_changed = True
            # newTrack=Tracking_re(field_updated='verified_by_user',
                # updated_to=current_user.email, updated_by=current_user.id,
                # recalls_table_id=kwargs.get('re_id_for_dash'))
            # db.session.add(newTrack)
            # db.session.commit()
    # else:
        # print('*****IN Else***')
        # print('current_user.email:::',type(current_user.email),current_user.email)
        # print('verified_by_list::::',type(verified_by_list),verified_by_list)
        # print('no verified user added')
        # if any(current_user.email in s for s in kwargs.get('verified_by_list')):
        # if current_user.email in verified_by_list:
            # print('current user in verified_by_list')
            # db.session.query(Tracking_re).filter_by(recalls_table_id=int(re_id_for_dash),
                # field_updated='verified_by_user',updated_to=current_user.email).delete()
            # db.session.commit()
            
    # if at_least_one_field_changed:
        # print('at_least_one_field_changed::::',at_least_one_field_changed)
        # setattr(existing_data, 'date_updated' ,datetime.now())
        # db.session.commit()
    # if date_flag:
        # flash(date_flag, 'warning')
    print('END update_recall')
    # print('end updateInvestigation util')
        #if there is a corresponding update different from existing_data:
        #1.add row to Tracking_re datatable
        #2.update existing_data with change       


# def update_files_re(filesDict, **kwargs):
    # print('START update_files_re')
    # date_flag=False
    # print('in update_files - filesDict:::',filesDict,'kwargs:::',kwargs)
    # formToDbCrosswalkDict = {'recall_file': 'files'}

    # update_data = {formToDbCrosswalkDict.get(i): j for i,j in filesDict.items()}
    # existing_data = db.session.query(Recalls).get(kwargs.get('re_id_for_dash'))
    
    # at_least_one_field_changed = False
    # if update_data.get('files') not in [existing_data.files,'']:
    ##if different an not null then add
        # print('files update --- values not the same')
        # at_least_one_field_changed = True
        ##newTrack=Tracking_re(field_updated='verified_by_user',
            ##updated_to=current_user.email, updated_by=current_user.id,
           ## recalls_table_id=kwargs.get('re_id_for_dash'))
        ##db.session.add(newTrack)
        ##db.session.commit()
    # if at_least_one_field_changed:
        # print('at_least_one_field_changed::::',at_least_one_field_changed)
        # setattr(existing_data, 'date_updated' ,datetime.now())
        # db.session.commit()
    # if date_flag:
        # flash(date_flag, 'warning')
    # print('END update_files_re')

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

