from flask import Blueprint


bp = Blueprint('json', __name__)
from web.json import routes
