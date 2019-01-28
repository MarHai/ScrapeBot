from flask import Blueprint


bp = Blueprint('main', __name__)
from web.main import routes
