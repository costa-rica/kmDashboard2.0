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



def remove_category_util(formDict):
    for i,j in formDict.items():
        if 'remove' in i:
            print('remove_category_util(formDict):::', i)
            remove_name = 'sc' + i[6:]
    return remove_name