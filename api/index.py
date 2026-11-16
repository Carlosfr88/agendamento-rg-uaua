
from flask import Flask
from app import create_app

app = Flask(__name__)

flask_app = create_app()

app.wsgi_app = flask_app.wsgi_app
