from setup import get_config
from scrapebot.database import User
from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail


config = get_config(False)
db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()
mail = Mail()


def create_web():
    web = Flask(__name__)
    web.config['SQLALCHEMY_DATABASE_URI'] = config.get_db_engine_string()
    web.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    web.config['SECRET_KEY'] = 'yn+T[bf037&3k$7ypK4"6LMjDkymbA~gv`#qN0N*7e{i+m4%,G+/.R<qh4y7!&O'
    web.config['MAIL_SERVER'] = config.get('Email', 'host')
    web.config['MAIL_PORT'] = int(config.get('Email', 'port'))
    web.config['MAIL_USE_TLS'] = config.get('Email', 'tls') is True
    web.config['MAIL_USERNAME'] = config.get('Email', 'user')
    web.config['MAIL_PASSWORD'] = config.get('Email', 'password')
    # web.debug = True

    db.init_app(web)
    login.init_app(web)
    bootstrap.init_app(web)
    mail.init_app(web)

    from web.auth import bp as bp_auth
    web.register_blueprint(bp_auth)

    from web.json import bp as bp_json
    web.register_blueprint(bp_json)

    from web.download import bp as bp_download
    web.register_blueprint(bp_download)

    from web.main import bp as bp_main
    web.register_blueprint(bp_main)

    return web


@login.user_loader
def load_user(uid):
    return db.session.query(User).filter(User.uid == int(uid)).first()
