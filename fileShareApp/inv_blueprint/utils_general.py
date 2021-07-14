from fileShareApp import db
from fileShareApp.models import User, Post, Investigations, Tracking_inv, \
    Saved_queries_inv, Recalls, Tracking_re, Saved_queries_re
import os
from flask import current_app
import json
from datetime import date, datetime
from flask_login import current_user
import pandas as pd


def category_list_dict_util():
    categories_excel=os.path.join(current_app.config['UTILITY_FILES_FOLDER'], 'categories.xlsx')
    df=pd.read_excel(categories_excel)
    category_list_dict={}
    for i in range(0,len(df.columns)):
        category_list_dict[df.columns[i]] =df.iloc[:,i:i+1][df.columns[i]].dropna().tolist()
    return category_list_dict



def remove_category_util(formDict, query_file_name):
    for i,j in formDict.items():
        if 'remove' in i:
            print('remove_category_util(formDict):::', i)
            remove_name = 'sc' + i[6:]
    return remove_name
    

def search_criteria_dictionary_util(formDict, query_file_name):   
    print('START search_criteria_dictionary_util')

    
    #make search dict with only 'sc_' items but take out 'sc_' :["", "string_contains"]
    search_query_dict={i[3:] :[j,"string_contains"] for i,j in formDict.items() if "sc_" in i}
    
    #make match_type dict, remove 'match_type' from key and keep value
    match_type_dict={i[11:]: j for i,j in formDict.items() if "match_type_" in i}
    
    #Loop over match_type dict, for key in in match_type dict, replace value in search_dict with [search_dict[key][0],value]
    search_query_dict = {i:([j[0],match_type_dict[i]] if i in match_type_dict.keys() else j) for i,j in search_query_dict.items() }
    


    # query_file_name='current_query_re.txt'
    with open(os.path.join(current_app.config['QUERIES_FOLDER'],query_file_name),'w') as dict_file:
        json.dump(search_query_dict,dict_file)
    print('END search_criteria_dictionary_util(formDict), returns query_file_name')
    return query_file_name