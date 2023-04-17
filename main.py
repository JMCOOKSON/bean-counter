from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
import time
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email
from flask_bootstrap import Bootstrap
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vege_price.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# driver set up
# CHROME_DRIVER_LOCATION = "C:/Users/cooks/Documents/chromedriver.exe"
# service = Service(CHROME_DRIVER_LOCATION)
# driver = webdriver.Chrome(service=service)


total_amount_saved_to_date = 0
price_per_kg = 0
value_of_product = 0

class CountdownPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produce = db.Column(db.String(250), nullable=False)
    produce_formatted = db.Column(db.String(250), nullable=True)
    single_price = db.Column(db.Integer, nullable=True)
    per_kg_price = db.Column(db.Integer, nullable= True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    total_saved = db.Column(db.Integer, nullable=False)
    history = db.relationship('History', backref='author', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.email

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    produce = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"History('{self.date}', '{self.price}')"

with app.app_context():
    db.create_all()
    db.session.commit()

class EnterProduce(FlaskForm):
    # search = StringField('Search', validators=[DataRequired()], render_kw={"id": "search"})
    produce_name = StringField("Please enter the name of the item harvested.", validators=[DataRequired()], render_kw={"id": "search"})
    produce_weight = StringField("Please enter weight(kg) or number of item(s)", validators=[DataRequired()])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    name = StringField('Name', validators =[DataRequired(), Length(min=4, max=25)])
    email = StringField(label='Email', validators=[Email()])
    password = PasswordField(label='Password', validators=[DataRequired(),Length(min=8)])
    submit = SubmitField(label='Log In')

class ContactUs(FlaskForm):
    name = StringField('Name', validators =[DataRequired(), Length(min=4, max=25)])
    email = StringField(label='Email', validators=[Email()])
    comment = StringField(label='Comment/Feedback', validators=[DataRequired(),Length(min=8)])
    submit = SubmitField(label='Log In')


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['user_id'] = user.id
            return redirect('/userpage')
        else:
            return render_template('login.html', form=form, error='Invalid email or password')
    else:
        return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session['logged_in'] = False
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        saved = 0;
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('register.html', error='Email address already exists')
        else:
            new_user = User(email=email, password=generate_password_hash(password), name=name, total_saved=saved)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/userpage')
    else:
        return render_template('register.html', form=form)

@app.route('/userpage', methods=['GET','POST'])
def userinfo():
    user_id = session.get('user_id')
    print(user_id)
    if not session.get('logged_in') :
        return redirect('/login')

    # This will access the users history in the database to be displayed

    data = History.query.filter_by(user_id=user_id).all()

    # this section is for updating databases once the user has entered new data
    form = EnterProduce()
    saved_result = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one()
    if form.validate_on_submit():
        produce_harvested = form.produce_name.data
        harvest_weight = form.produce_weight.data
        with app.app_context():
            # get current price information from database and update total saved
            result = db.session.execute(db.select(CountdownPrice).filter_by(produce_formatted=produce_harvested)).scalar_one()
            amount_saved = float(result.per_kg_price) * float(harvest_weight)
            saved_result = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one()
            new_amount = saved_result.total_saved + amount_saved
            saved_result.total_saved = new_amount
            # save items to users database
            new_data = History(date=datetime.today(), produce=produce_harvested, weight=harvest_weight, price=amount_saved, user_id=user_id)
            db.session.add(new_data)
            db.session.commit()
        return render_template("savings_page.html", savings=amount_saved, total_saved=new_amount)
    return render_template("user_page.html", form=form, history=data, total=saved_result.total_saved)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactUs()
    return render_template('register.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)




