from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
from fileShareApp import db, bcrypt, mail
from fileShareApp.models import Post, User, Investigations
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
    search_criteria_dictionary_util, investigations_query_util
import openpyxl
from werkzeug.utils import secure_filename
import json
import glob
import ast

#from login run default query

#if 