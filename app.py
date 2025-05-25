from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db, User

from flask_migrate import Migrate

db.init_app(app)

migrate = Migrate(app, db)

# with app.app_context():
#     db.create_all()

@app.route('/')
def home():
    return 'Welcome to FitQuest!'