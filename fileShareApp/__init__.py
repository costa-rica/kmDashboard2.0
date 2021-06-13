from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from fileShareApp.config import Config
from flask_migrate import Migrate

import logging
import sys

db = SQLAlchemy()

bcrypt = Bcrypt()
login_manager= LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()

#application factory
def create_app(config_class=Config):
    app = Flask(__name__)
    
    logger = logging.getLogger(__name__)
    stderr_handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(stderr_handler)
    file_handler = logging.FileHandler('fileShareApp_log.txt')
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    # app.logger.addHandler(file_handler)
    
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)


    from fileShareApp.inv_blueprint.routes import inv_blueprint
    from fileShareApp.re_blueprint.routes import re_blueprint
    from fileShareApp.users.routes import users
    from fileShareApp.errors.handlers import errors
    app.register_blueprint(inv_blueprint)
    app.register_blueprint(re_blueprint)
    app.register_blueprint(users)
    app.register_blueprint(errors)

    return app