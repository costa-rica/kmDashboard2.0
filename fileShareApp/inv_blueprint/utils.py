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

def column_names_inv_util():
    column_names=['id','NHTSA_ACTION_NUMBER', 'MAKE','MODEL','YEAR','COMPNAME','MFR_NAME',
        'ODATE','CDATE','CAMPNO','SUBJECT','km_notes','categories']
    return column_names


def column_names_dict_inv_util():
    column_names_dict={'id':'Dash ID','NHTSA_ACTION_NUMBER':'NHTSA Number', 'MAKE':'Make','MODEL':'Model',
        'YEAR':'Year','COMPNAME':'Component Name','MFR_NAME':'Manufacturer Name','ODATE':'Open Date',
        'CDATE':'Close Date','CAMPNO':'Recall Campaign Number','SUBJECT':'Subject'}
    return column_names_dict

def queryToDict(query_data, column_names):
    db_row_list =[]
    for i in query_data:
        row = {key: value for key, value in i.__dict__.items() if key not in ['_sa_instance_state']}
        db_row_list.append(row)
    return db_row_list


def investigations_query_util(query_file_name):
    investigations = db.session.query(Investigations)
    with open(os.path.join(current_app.config['QUERIES_FOLDER'],query_file_name)) as json_file:
        search_criteria_dict=json.load(json_file)
        json_file.close()

    print('1investigations lentght::::',len(investigations.all()))
    if search_criteria_dict.get('user'):
        if search_criteria_dict.get('user')[0]!='':
            # print('this should not fire if no user')
        #search_criteria_dict.get('user') comes in as a list of [string containing all users or single user, 'string contains']
            #get users verified
            user_criteria = [a for a in re.split(r'(\s|\,)',  search_criteria_dict.get('user')[0].strip()) if len(a)>1]
            table_ids_dict={}
            for j in user_criteria:
                investigations_table_ids=db.session.query(Tracking_inv.investigations_table_id).filter(Tracking_inv.updated_to.contains(j)).distinct().all()
                investigations_table_ids=[i[0] for i in investigations_table_ids]
                # print('recalls_table_ids:::',investigations_table_ids)
                table_ids_dict[j]=investigations_table_ids
            
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
                investigations = investigations.filter(getattr(Investigations,'id').in_(table_ids_list))

    print('2investigations lentght::::',len(investigations.all()))
    #put all 'category' elements in another dictionary
    category_dict={}
    for i,j in search_criteria_dict.items():
        if 'category' in i:
            category_dict[i]=j
    print('category_dict::::', category_dict)
    #take out all keys that contain "cateogry"
    for i,j in category_dict.items():
        del search_criteria_dict[i]


    #filter recalls query by anything that contains
    for i,j in category_dict.items():
        if j[0]!='':
            investigations = investigations.filter(getattr(Investigations,'categories').contains(j[0]))

    print('3investigations lentght::::',len(investigations.all()))
    for i,j in search_criteria_dict.items():
        if j[1]== "exact":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                investigations = investigations.filter(getattr(Investigations,i)==int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                investigations = investigations.filter(getattr(Investigations,i)==j[0])
            elif j[0]!='':
                investigations = investigations.filter(getattr(Investigations,i)==j[0])
        elif j[1]== "less_than":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                investigations = investigations.filter(getattr(Investigations,i)<int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                investigations = investigations.filter(getattr(Investigations,i)<j[0])
        elif j[1]== "greater_than":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                investigations = investigations.filter(getattr(Investigations,i)>int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                # j[0]=datetime.strptime(j[0].strip(),'%m/%d/%Y')
                investigations = investigations.filter(getattr(Investigations,i)>j[0])
        elif j[1] =="string_contains" and j[0]!='':
            if i not in ['user']:
                investigations = investigations.filter(getattr(Investigations,i).contains(j[0]))
    # print('filtered all investigations except Odate restriction ::', len(investigations.all()))
    investigations=investigations.filter(getattr(Investigations,'ODATE')>="2011-01-01")
    print('4investigations lentght::::',len(investigations.all()))
    # print('filtered all investigations::', len(investigations.all()))
    investigations=investigations.all()
    print('filtered complte')
    
    msg="""END investigations_query_util(query_file_name), returns investigations,
search_criteria_dict. len(investigations) is 
    """
    search_criteria_dict.update(category_dict)
    # print(msg, len(investigations), 'search_criteria_dict: ',search_criteria_dict)
    return (investigations,search_criteria_dict, category_dict)


    
def update_investigation(formDict, inv_id_for_dash, verified_by_list):
    # date_flag=False
    # print('START investigation UPdate')
    # print('updateInv - formDict::',formDict)
    formToDbCrosswalkDict = {'inv_number':'NHTSA_ACTION_NUMBER','inv_make':'MAKE',
        'inv_model':'MODEL','inv_year':'YEAR','inv_compname':'COMPNAME',
        'inv_mfr_name': 'MFR_NAME', 'inv_odate': 'ODATE', 'inv_cdate': 'CDATE',
        'inv_campno':'CAMPNO','inv_subject': 'SUBJECT', 'inv_summary_textarea': 'SUMMARY',
        'inv_km_notes': 'km_notes','investigation_file': 'files'}

    update_data = {formToDbCrosswalkDict.get(i): j for i,j in formDict.items()}
    # del update_data['SUMMARY']
    # print('update_data::::',update_data)
    
    
    # no_update_list=['inv_NHTSA Action Number','inv_Make', 'inv_Model','inv_Year','inv_Open Date',
                   # 'inv_Close Date','inv_Recall Campaign Number', 'inv_Component Description',
                   # 'inv_Manufacturer Name', 'inv_subject','inv_summary_textarea','inv_km_notes',
                   # 'update_inv','verified_by_user','investigation_file','csrf_token',
                   # 'inv_or_re','record_type','records_list']
    
    
    #get categories from formDict --was formDict
    assigned_categories=''
    for i in formDict:
        if i[:4]=='cat_':
        # if i not in no_update_list:
            # print('formDict value in assigned category:::',i)
            if assigned_categories=='':
                assigned_categories=i[4:]
            else:
                assigned_categories=assigned_categories +', '+ i[4:]
    update_data['categories']=assigned_categories
    
    existing_data = db.session.query(Investigations).get(int(inv_id_for_dash))
    #database columns to potentially update
    # Investigations_attr=['km_notes','files', 'categories']
    Investigations_attr=['km_notes', 'categories']
    # at_least_one_field_changed = False
    # print('update data:::', update_data)
    # print('Does existing_data have any files?:::',existing_data.files)
    
    for i in Investigations_attr:
        # print('**Attribute to update:::',str(i))
        # print('Begininng of loop, files status:::',existing_data.files)
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
            track_util('investigations', i,update_from, update_data.get(i),inv_id_for_dash)
        # else:
            # print(i, ' has no change')
        # print('End of loop, files status:::',existing_data.files)
    # print('After loop throug attributes---Does existing_data have any files?:::',existing_data.files)
    
    if formDict.get('verified_by_user'):
    
        if current_user.email not in verified_by_list:
            track_util('investigations', 'verified_by_user','',current_user.email,inv_id_for_dash)
    
    
        # if any(current_user.email in s for s in kwargs.get('verified_by_list')):
            # print('do nothing')
        # else:
            # print('user verified adding to Tracking_inv table')
            # at_least_one_field_changed = True
            # newTrack=Tracking_inv(field_updated='verified_by_user',
                # updated_to=current_user.email, updated_by=current_user.id,
                # investigations_table_id=kwargs.get('inv_id_for_dash'))
            # db.session.add(newTrack)
            # db.session.commit()
    # else:
        # print('no verified user added')
        # if any(current_user.email in s for s in kwargs.get('verified_by_list')):
            # db.session.query(Tracking_inv).filter_by(investigations_table_id=kwargs.get('inv_id_for_dash'),
                # field_updated='verified_by_user',updated_to=current_user.email).delete()
            # db.session.commit()
            
    # if at_least_one_field_changed:
        # print('at_least_one_field_changed::::',at_least_one_field_changed)
        # setattr(existing_data, 'date_updated' ,datetime.now())
        # db.session.commit()
    # if date_flag:
        # flash(date_flag, 'warning')
    
    # print('end updateInvestigation util')
        #if there is a corresponding update different from existing_data:
        #1.add row to Tracking_inv datatable
        #2.update existing_data with change       


# def update_files(filesDict, **kwargs):
    # date_flag=False
    ## print('in update_files - filesDict:::',filesDict,'kwargs:::',kwargs)
    # formToDbCrosswalkDict = {'investigation_file': 'files'}

    # update_data = {formToDbCrosswalkDict.get(i): j for i,j in filesDict.items()}
    # existing_data = db.session.query(Investigations).get(kwargs.get('inv_id_for_dash'))
    # for i in Investigations_attr:
    # at_least_one_field_changed = False
    ## if update_data.get('files') not in [existing_data.files,'']:
    ## if different an not null then add
        ## print('files update --- values not the same')
        # at_least_one_field_changed = True
    
    # if at_least_one_field_changed:
        # print('at_least_one_field_changed::::',at_least_one_field_changed)
        # setattr(existing_data, 'date_updated' ,datetime.now())
        # db.session.commit()
    # if date_flag:
        # flash(date_flag, 'warning')



def create_categories_xlsx(excel_file_name, column_names_for_df, formDict, db_table):
    excelObj=pd.ExcelWriter(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],excel_file_name))

    # columnNames=Investigations.__table__.columns.keys()
    colNamesDf=pd.DataFrame([column_names_for_df],columns=column_names_for_df)
    colNamesDf.to_excel(excelObj,sheet_name=db_table.capitalize() + ' Data', header=False, index=False)

    queryDf = pd.read_sql_table(db_table, db.engine)
    queryDf=queryDf[column_names_for_df].copy()
    queryDf=queryDf[(queryDf['ODATE']>datetime(2011,1,1,0,0,0))]

    
    queryDf.to_excel(excelObj,sheet_name=db_table.capitalize() + ' Data', header=False, index=False,startrow=1)
    inv_data_workbook=excelObj.book
    notes_worksheet = inv_data_workbook.add_worksheet('Notes')
    notes_worksheet.write('A1','Created:')
    notes_worksheet.set_column(1,1,len(str(datetime.now())))
    time_stamp_format = inv_data_workbook.add_format({'num_format': 'mmm d yyyy hh:mm:ss AM/PM'})
    notes_worksheet.write('B1',datetime.now(), time_stamp_format)
    excelObj.close()


def existing_report(excel_file_name, db_table):
    # Read Excel and turn entire sheet to a df
    time_stamp_df = pd.read_excel(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],excel_file_name),
        'Notes',header=None)
    categories_df =pd.read_excel(os.path.join(
        current_app.config['UTILITY_FILES_FOLDER'],excel_file_name),
        db_table.capitalize() + ' Data')
    categories_dict={i:'checked' for i in list(categories_df.columns)}
    # print('categories_dict:::', categories_dict)
    time_stamp = time_stamp_df.loc[0,1].to_pydatetime().strftime("%Y-%m-%d %I:%M:%S %p")
    return (categories_dict,time_stamp)
