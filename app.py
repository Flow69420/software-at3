from flask import Flask
from flask import render_template, redirect, url_for, flash

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db, User

from flask_migrate import Migrate

db.init_app(app)

migrate = Migrate(app, db)

from forms import RegistrationForm, LoginForm

# with app.app_context():
#     db.create_all()

@app.route('/')
def home():
    return 'Welcome to FitQuest!'

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)