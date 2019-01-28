from flask import Blueprint

bp = Blueprint('auth', __name__)

from web.auth import routes