import os
import json

if os.environ.get('COMPUTERNAME')=='CAPTAIN2020':
    with open(r'D:\OneDrive\Documents\professional\config_files\config_km_dashboard.json') as config_file:
        config = json.load(config_file)
elif os.environ.get('USER')=='sanjose':
    with open('/home/sanjose/Documents/environments/config.json') as config_file:
        config = json.load(config_file)
else:
    print('Error with ',os.path.abspath(os.getcwd()),'/config.py')


class Config:
    SECRET_KEY = config.get('SECRET_KEY_DMR')
    SQLALCHEMY_DATABASE_URI = config.get('SQL_URI_FILESHAREAPP')
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = config.get('MAIL_PASSWORD_CBC')
    MAIL_USERNAME = config.get('MAIL_USERNAME_CBC')
    DEBUG = True
    UPLOADED_FILES_FOLDER = os.path.join(os.path.dirname(__file__), 'static/files')
    UTILITY_FILES_FOLDER = os.path.join(os.path.dirname(__file__), 'static/utility_files')
    QUERIES_FOLDER = os.path.join(os.path.dirname(__file__), 'static/queries')
    