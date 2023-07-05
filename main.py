import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email
from flask_bootstrap import Bootstrap
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import smtplib
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
Bootstrap(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vege_price.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
sender_email=os.getenv("SENDER_EMAIL")
email_password=os.getenv("EMAIL_PASSWORD")




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
    search = SubmitField('Search')

class EnterWeight(FlaskForm):

    produce_weight = StringField("Please enter weight(kg) of item(s)")
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    name = StringField('Name', validators =[DataRequired(), Length(min=4, max=25)])
    email = StringField(label='Email', validators=[Email()])
    password = PasswordField(label='Password', validators=[DataRequired(),Length(min=8)])
    submit = SubmitField(label='Log In')

class ContactUs(FlaskForm):
    name = StringField('Name', validators =[DataRequired(), Length(min=4, max=25)])
    email = StringField(label='Email', validators=[Email()])
    message = StringField(label='Comment/Feedback', validators=[DataRequired(),Length(min=8)])
    submit = SubmitField(label='Submit')

class ResetPassword(FlaskForm):
    email = StringField(label='Email', validators=[Email()])
    submit = SubmitField(label='Submit')

class NewPassword(FlaskForm):
    email = StringField(label='Email', validators=[Email()])
    emailed_token = PasswordField(label='Email Code', validators=[DataRequired(),Length(min=8)])
    password = PasswordField(label=' New Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label='Log In')


def send_notification_email(name, email, message):
    receiver_email = 'nzbeancounter@gmail.com'
    subject = 'Bean Counter Message'
    body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

    # Compose the email message
    email_message = f"Subject: {subject}\n\n{body}"

    try:
        # Connect to the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Replace with your email server address and port
            server.starttls()

            # Log in to your email account
            server.login('nzbeancounter@gmail.com', 'objldpmwioadasia')  # Replace with your email account login credentials

            # Send the email
            server.sendmail(sender_email, receiver_email, email_message)

        print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred while sending the email: {str(e)}")


def generate_token():
    token_length = 16  # Length of the token
    characters = string.ascii_letters + string.digits

    # Generate the token
    token = ''.join(random.choice(characters) for _ in range(token_length))

    return token


def send_password_reset_email(email, token):
    receiver_email = f"{email}"
    print(receiver_email)
    subject = 'Bean Counter Password Reset'
    reset_url = url_for('reset_password', token=token, _external=True)  # URL for the reset password page

    # Compose the email message
    message = f"Code: {token} \n Click the link below to reset your password:\n<{reset_url}>"
    body = f"Email: {email}\n\nMessage:\n{message}"

    # Compose the email message
    email_message = f"Subject: {subject}\n\n{body}"

    try:
        # Connect to the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()

            # Log in to your email account
            server.login('nzbeancounter@gmail.com',
                         'objldpmwioadasia')  # Replace with your email account login credentials

            # Send the email
            server.sendmail(sender_email, receiver_email, email_message)

        print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred while sending the email: {str(e)}")



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

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
        if user:
            print ("user true")
            if check_password_hash(user.password, password):
                print ("check password true")
                session['logged_in'] = True
                session['user_id'] = user.id
                return redirect('/userpage')
            else:
                error_message = 'Invalid email or password. Please try again.'
                return render_template('login.html', form=form, error=error_message)

        else:
            error_message = 'Invalid email or password. Please try again.'
            return render_template('login.html', form=form, error=error_message)
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
            print('user added')
            # Perform authentication after successful registration
            session['logged_in'] = True
            session['user_id'] = new_user.id

            return redirect('/userpage')
    else:
        return render_template('register.html', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ResetPassword()
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_token()
            #store the token where the password was in the database
            user.password = token
            db.session.commit()

            # Send password reset email
            send_password_reset_email(email, token)

            flash('An email has been sent with instructions to reset your password')

            return redirect('/login')


        else:
            return render_template('register.html', error='Could not find email in database. Please register.')

    return render_template('forgot_password.html',form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = NewPassword()
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user.password == request.form['emailed_token']:
            new_password = request.form['password']
            user.password = generate_password_hash(new_password)
            db.session.commit()

        flash('Your password has been successfully reset. You can now log in with your new password.')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token, form=form)


@app.route('/userpage', methods=['GET','POST'])
def userinfo():
    user_id = session.get('user_id')
    if not session.get('logged_in') :
        return redirect('/login')

    # This will access the users history in the database to be displayed

    data = History.query.filter_by(user_id=user_id).all()

    # this section is for updating databases once the user has entered new data
    form = EnterProduce()
    saved_result = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one()

    if form.validate_on_submit():
        if form.search.data:
            print("if statement through ")
            produce_harvested = form.produce_name.data
            items = CountdownPrice.query.filter(CountdownPrice.produce_formatted.like(f'%{produce_harvested}%')).all()
            if not items:
                error_message = "Sorry, that item is not in our database. Please contact us to add it."
                return render_template("user_page.html", form=form, user_id=user_id, error=error_message)
            for item in items:
                print(item.produce_formatted)

            return render_template('selection_page.html', produce_list=items)

    else:
        return render_template("user_page.html", form=form, history=data, user_id=user_id, total=str(round(saved_result.total_saved, 2)))



@app.route('/dataintake/<int:item_id>', methods=['GET', 'POST'])
def data_intake(item_id):
    item = CountdownPrice.query.get(item_id)
    if item == None:
        message = "Hmmm we can't find this item in our database. Please check your spelling and try again, or, if you would like us to add this item, we would love to hear from you."
        render_template('userinfo', note=message)
    form = EnterWeight()

    user_id = session.get('user_id')
    if not session.get('logged_in'):
        return redirect('/login')


    if form.submit.data:
        print("if through ")
        produce_harvested = item.produce_formatted
        harvest_weight = form.produce_weight.data
        try:
            weight_value = float(harvest_weight.split('kg')[0])
        except ValueError:
            error_message = "Please enter a valid weight in kilograms."
            return render_template('dataintake.html', form=form, item=item, error=error_message)

        with app.app_context():
            # get current price information from database and update total saved
            result = db.session.execute(
                db.select(CountdownPrice).filter_by(id=item_id)).scalar_one()
            if not result:
                error_message = "Sorry, that item is not in our database. Please contact us to add it."
                return redirect(url_for('userpage', error=error_message))

            amount_saved = float(result.per_kg_price) * float(weight_value)
            saved_result = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one()
            new_amount = saved_result.total_saved + amount_saved
            saved_result.total_saved = new_amount
                # save items to users database
            today_date=datetime.strptime(datetime.today().strftime("%d-%m-%Y"), "%d-%m-%Y")
            new_data = History(date=today_date, produce=produce_harvested, weight=harvest_weight, price=round(amount_saved,2),
                            user_id=user_id)
            db.session.add(new_data)
            db.session.commit()
            return render_template("savings_page.html", savings=round(amount_saved,2), total_saved=round(new_amount,2))
    return render_template('dataintake.html', form=form, item=item)


@app.route('/delete_history', methods=['POST'])
def delete_history():
    user_id= session.get('user_id')
    histories = History.query.filter_by(user_id=user_id).all()
    if histories:
        for history in histories:
            db.session.delete(history)
        db.session.commit()
        flash('History deleted successfully.', 'success')
    else:
        flash('No history found for the user.', 'error')
    return redirect(url_for('userinfo'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactUs()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Send email notification
        send_notification_email(name, email, message)

        # Return a response or redirect to a thank you page
        return render_template('contact.html', form=form, message="Thank you for your request! We will get back to you soon.")

    return render_template('contact.html', form=form)



if __name__ == '__main__':
    app.run(debug=True)




