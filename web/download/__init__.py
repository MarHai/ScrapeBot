from flask import Blueprint


bp = Blueprint('download', __name__)
from web.download import routes
