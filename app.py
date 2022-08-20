from flask import Flask, render_template, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from wtforms.widgets import TextArea
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_ckeditor import CKEditor
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
import uuid as uuid
import os


# Create a Flask Instance
app = Flask(__name__)
# Add CKEditor
ckeditor = CKEditor(app)
# Old SQLite DB
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# New MySQL DB
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Thetruth11@localhost/users'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://zmkhmhnimlqdnf:dbda68cc197c48447202705e9c4268aab6d998e37e97e2b8f60ce465c46719a4@ec2-34-203-182-65.compute-1.amazonaws.com:5432/d4taestphojlpt'
# Secret Key!
app.config['SECRET_KEY'] = "my super secret ket that no one is supposed to know"
# Initialize The Database

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Pass Stuff To Navbar
@app.context_processor
def base():
	form = SearchForm()
	return dict(form=form)

# Create Search Function
@app.route('/search', methods=["POST"])
def search():
	form = SearchForm()
	posts = Posts.query
	if form.validate_on_submit():
		# Get data from submitted form
		post.searched = form.searched.data
		# Query the Database
		posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
		posts = posts.order_by(Posts.title).all()


		return render_template("search.html", 
			form=form,
			searched = post.searched,
			posts=posts)

# Create A Search Form
class SearchForm(FlaskForm):
	searched = StringField("Searched", validators=[DataRequired()])
	submit = SubmitField("Submit")


# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))


# Create Login Form
class LoginForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")


# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(username=form.username.data).first()
		if user:
			# Check the hash
			if check_password_hash(user.password_hash, form.password.data):
				login_user(user)
				flash("Login successful!")
				return redirect(url_for('dashboard'))
			else:
				flash("Wrong password! Try again!")
		else:
			flash("That user doesn't exist! Try again!")

	return render_template('login.html', form=form)

# Create Logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	flash("You have been logged out!")
	return redirect(url_for('login'))


# Create Dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
	form = UserForm()
	id = current_user.id
	return render_template('dashboard.html')

# Create a Blog Post model
class Posts(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(255))
	content = db.Column(db.Text)
	#author = db.Column(db.String(255))
	date_posted = db.Column(db.DateTime, default=datetime.utcnow)
	slug = db.Column(db.String(255))
	# Foreign Key To Link Users (refer to primary key of the user)
	poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))

# Create a Posts Form
class PostForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired()])
	#content = StringField("Content", validators=[DataRequired()], widget=TextArea())
	content = CKEditorField('Content', validators=[DataRequired()])

	#author = StringField("Author")
	slug = StringField("Slug", validators=[DataRequired()])
	submit = SubmitField("Submit")

@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
	post_to_delete = Posts.query.get_or_404(id)
	id = current_user.id
	if id == post_to_delete.poster.id:
		try:
			db.session.delete(post_to_delete)
			db.session.commit()

			# Return a message
			flash("Post was deleted!")

			# Grab all the posts from the database
			posts = Posts.query.order_by(Posts.date_posted)
			return render_template("posts.html", posts=posts)


		except:
			# Return an error message
			flash("There was a problem, deleting your post! Try again!")


			# Grab all the posts from the database
			posts = Posts.query.order_by(Posts.date_posted)
			return render_template("posts.html", posts=posts)
	else:
		# Return a message
			flash("You aren't allowed to delete this post.")
			
			# Grab all the posts from the database
			posts = Posts.query.order_by(Posts.date_posted)
			return render_template("posts.html", posts=posts)

@app.route('/posts')
def posts():
	# Grab all the posts from the database
	posts = Posts.query.order_by(Posts.date_posted)
	return render_template("posts.html", posts=posts)

@app.route('/posts/<int:id>')
def post(id):
	post = Posts.query.get_or_404(id)
	return render_template("post.html", post=post)


@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
	post = Posts.query.get_or_404(id)
	form = PostForm()
	if form.validate_on_submit():
		post.title = form.title.data	
		#post.author = form.author.data
		post.slug = form.slug.data
		post.content = form.content.data
		# Update Database
		db.session.add(post)
		db.session.commit()
		flash("Post has been updated!")
		return redirect(url_for('post', id=post.id))

	if current_user.id == post.poster_id:
		form.title.data = post.title
		#form.author.data = post.author
		form.slug.data = post.slug
		form.content.data = post.content
		return render_template('edit_post.html', form=form)
	else:
		flash("You aren't allowed to edit this post.")
		post = Posts.query.get_or_404(id)
		return render_template("post.html", post=post)

# Add Post Page
@app.route('/add-post', methods=['GET', 'POST'])
#@login_required
def add_post():
	form = PostForm()

	if form.validate_on_submit():
		poster = current_user.id
		post = Posts(title=form.title.data, content=form.content.data, poster_id=poster, slug=form.slug.data)
		# Clear The Form
		form.title.data = ''
		form.content.data = ''
		#form.author.data = ''
		form.slug.data = ''

		# Add post data to database
		db.session.add(post)
		db.session.commit()

		# Return a Message
		flash("Blog Post Submitted Successfully!")

	# Redirect to the webpage
	return render_template("add_post.html", form=form)

# Create Admin Page
@app.route('/admin')
@login_required
def admin():
	id = current_user.id
	if id == 8:
		return render_template("admin.html")
	else:
		flash("Sorry you are not allowed to access this page!")
		return redirect(url_for('dashboard'))

# Json Thing
@app.route('/date')
def get_current_date():
	favorite_pizza = {
		"John"

	}
	return {"Date": date.today()}


# Create Model
class Users(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), nullable=False, unique=True)
	name = db.Column(db.String(200), nullable=False)
	email = db.Column(db.String(120), nullable=False, unique=True)
	date_added = db.Column(db.DateTime, default=datetime.utcnow)
	favorite_color = db.Column(db.String(120))
	about_author = db.Column(db.Text(), nullable=True)
	profile_pic = db.Column(db.String(200), nullable=True)

	# Do some password stuff!
	password_hash = db.Column(db.String(128))
	# User Can Have Many Posts
	posts = db.relationship('Posts', backref='poster')


	@property
	def password(self):
		raise AttributeError('password is not a readable attribute!')
		
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)
	

	# Create A String
	def __repr__(self):
		return '<Name%r>' % self.name

@app.route('/delete/<int:id>')
def delete(id):
	user_to_delete = Users.query.get_or_404(id)
	name = None
	form = UserForm()

	try:
		db.session.delete(user_to_delete)
		db.session.commit()
		flash("User Deleted Successfully!")

		our_users = Users.query.order_by(Users.date_added)
		return render_template("add_user.html",
		form=form,
		name=name,
		our_users=our_users)

	except:
		flash("Whoops! There was a problem deleting your user! Try Again!")
		return render_template("add_user.html",
		form=form, name=name, our_users=our_users)
# Create a Form Class
class UserForm(FlaskForm):
	name = StringField("Name", validators=[DataRequired()])
	username = StringField("UserName", validators=[DataRequired()])
	email = StringField("Email", validators=[DataRequired()])
	submit = SubmitField("Submit")
	favorite_color = StringField("Favorite Color")
	about_author = TextAreaField("About Author")
	password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message='Passwords Must Match')])
	password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
	profile_pic = FileField("Profile Pic")

# Update Database Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
	form = UserForm()
	name_to_update =  Users.query.get_or_404(id)
	if request.method == "POST":
		name_to_update.name = request.form['name']
		name_to_update.email = request.form['email']
		name_to_update.username = request.form['username']
		name_to_update.favorite_color = request.form['favorite_color']
		name_to_update.about_author = request.form['about_author']
		name_to_update.profile_pic = request.files['profile_pic']


		# Grab Image Name
		pic_filename = secure_filename(name_to_update.profile_pic.filename)
		# Set UUID
		pic_name = str(uuid.uuid1()) + "_" + pic_filename
		# Save That Image
		name_to_update.profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))

		# Change it to a string to save to db
		name_to_update.profile_pic = pic_name

		try:
			db.session.commit()
			flash("User Updated Successfully!")
			return render_template("update.html",
				form=form,
				name_to_update = name_to_update)
		except:
			flash("Error! Looks like there was a problem! Please Try again")
			return render_template("update.html",
				form=form,
				name_to_update = name_to_update)
	else:
		return render_template("update.html",
				form=form,
				name_to_update = name_to_update,
				id = id)

class PasswordForm(FlaskForm):
	email = StringField("What's Your Email", validators=[DataRequired()])
	password_hash = PasswordField("What's Your Password", validators=[DataRequired()])
	submit = SubmitField("Submit")


# Create a Form Class
class NamerForm(FlaskForm):
	name = StringField("What's Your Name", validators=[DataRequired()])
	submit = SubmitField("Submit")

	# BooleanField
	# DateField
	# DateTimeField
	# DecimalField
	# FileField
	# HiddenField
	# MultipleField
	# FieldList
	# FloatField
	# FormField
	# IntegerField
	# PasswordField
	# RadioField
	# SelectField
	# SelectMultipleField
	# SubmitField
	# StringField
	# TextAreaField

	## Validators
	# DataRequired
	# Email
	# EqualTo
	# InputRequired
	# IPAddress
	# Length
	# MacAddress
	# NumberRange
	# Optional
	# Regexp
	# URL
	# UUID
	# AnyOf
	# NoneOf


#def index():
#	return "<h1>Hello World!</h1>"

# FILTERS!!!
#safe
#capitalize
#lower
#upper
#title
#trim
#striptags

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
	name = None
	form = UserForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(email=form.email.data).first()
		if user is None:
			# Hash the password!!!
			hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
			user = Users(username=form.username.data, name=form.name.data, email=form.email.data, favorite_color=form.favorite_color.data, password_hash=hashed_pw)
			db.session.add(user)
			db.session.commit()
		name = form.name.data
		form.name.data = ''
		form.username.data = ''
		form.email.data = ''
		form.favorite_color.data = ''
		form.password_hash = ''

		flash("User Added Successfully!")
	our_users = Users.query.order_by(Users.date_added)
	return render_template("add_user.html",
		form=form,
		name=name,
		our_users=our_users)

# Create a route decorator
@app.route('/')
def index():
	first_name = "camile"
	stuff = "This is bold Text"

	favorite_pizza = ["Pepperoni", "Cheese", "Mushrooms", 41]
	return render_template("index.html", 
		first_name=first_name,
		stuff=stuff,
		favorite_pizza = favorite_pizza)

# localhost:5000/user/John
@app.route('/user/<name>')

def user(name):
	return render_template("user.html", user_name=name)

# Create Custom Error Pages

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
	return render_template("500.html"), 500

# Create Name Page
@app.route('/name', methods=['GET', 'POST'])
def name():
	name = None
	form = NamerForm()
	# Validate Form
	if form.validate_on_submit():
		name = form.name.data
		form.name.data= ''
		flash("Form Submitted Successfully!")

	return render_template("name.html",
		name = name,
		form = form)



# Create Password Test Page
@app.route('/test_pwd', methods=['GET', 'POST'])
def test_pwd():
	email = None
	password = None
	pw_to_check = None
	passed = None
	form = PasswordForm()


	# Validate Form
	if form.validate_on_submit():
		email = form.email.data
		password = form.password_hash.data
		# Clear the form
		form.email.data = ''
		form.password_hash.data = ''

		# Lookup User By Email Address
		pw_to_check = Users.query.filter_by(email=email).first()
		
		# Check Hashed Password
		check_password_hash(pw_to_check.password_hash, password)

	return render_template("test_pwd.html",
		email = email,
		password = password,
		pw_to_check = pw_to_check,
		form = form)

