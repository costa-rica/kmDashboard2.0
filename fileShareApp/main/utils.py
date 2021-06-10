from fileShareApp import db
from fileShareApp.models import Post, User, Investigations, Kmtracking,Km_saved_queries
import os
from flask import current_app
import json
from datetime import date, datetime
from flask_login import current_user
import pandas as pd


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
                investigations = investigations.filter(getattr(Investigations,i)==int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                investigations = investigations.filter(getattr(Investigations,i)==j[0])
            elif j[0]!='':
                investigations = investigations.filter(getattr(Investigations,i)==j[0])
        elif j[1]== "less_than":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                investigations = investigations.filter(getattr(Investigations,i)<int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                investigations = investigations.filter(getattr(Investigations,i)<j[0])
        elif j[1]== "greater_than":
            if i in ['id','YEAR'] and j[0]!='':
                # j[0]=int(j[0])
                investigations = investigations.filter(getattr(Investigations,i)>int(j[0]))
            elif i in ['ODATE','CDATE'] and j[0]!='':
                j[0]=datetime.strptime(j[0].strip(),'%Y-%m-%d')
                investigations = investigations.filter(getattr(Investigations,i)>j[0])
        elif j[1] =="string_contains" and j[0]!='':
            investigations = investigations.filter(getattr(Investigations,i).contains(j[0]))
    # investigations=investigations.filter(getattr(Investigations,'YEAR')>2015).all()
    investigations=investigations.all()
    msg="""END investigations_query_util(query_file_name), returns investigations,
search_criteria_dict. len(investigations) is 
    """
    print(msg, len(investigations), 'search_criteria_dict: ',search_criteria_dict)
    return (investigations,search_criteria_dict)


def search_criteria_dictionary_util(formDict):   
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

    query_file_name='current_query.txt'
    with open(os.path.join(current_app.config['QUERIES_FOLDER'],query_file_name),'w') as dict_file:
        json.dump(search_query_dict,dict_file)
    print('END search_criteria_dictionary_util(formDict), returns query_file_name')
    return query_file_name

def updateInvestigation(dict, **kwargs):
    date_flag=False
    print('in updateInvestigation - dict:::',dict,'kwargs:::',kwargs)
    formToDbCrosswalkDict = {'inv_number':'NHTSA_ACTION_NUMBER','inv_make':'MAKE',
        'inv_model':'MODEL','inv_year':'YEAR','inv_compname':'COMPNAME',
        'inv_mfr_name': 'MFR_NAME', 'inv_odate': 'ODATE', 'inv_cdate': 'CDATE',
        'inv_campno':'CAMPNO','inv_subject': 'SUBJECT', 'inv_summary_textarea': 'SUMMARY',
        'inv_km_notes_textarea': 'km_notes', 'investigation_file)': 'files',
        'checkbox_0':'checkbox_0','checkbox_1':'checkbox_1','checkbox_2':'checkbox_2',
        'checkbox_3':'checkbox_3','checkbox_4':'checkbox_4'}

    update_data = {formToDbCrosswalkDict.get(i): j for i,j in dict.items()}
    existing_data = db.session.query(Investigations).get(kwargs.get('inv_id_for_dash'))
    Investigations_attr=['SUBJECT','SUMMARY','km_notes','date_updated','files',
        'checkbox_0', 'checkbox_1','checkbox_2','checkbox_3','checkbox_4']
    at_least_one_field_changed = False
    #loop over existing data attributes
    print('update_data:::', update_data)
    
    for i in Investigations_attr:
        if update_data.get(i):

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