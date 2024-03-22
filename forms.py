from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()], render_kw={"placeholder": "email@.com"})
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


# Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()], render_kw={"placeholder": "email@.com"})
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


# Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    text = CKEditorField("Leave Your Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


# Create a ContactForm so users can leave message to blog owner
class ContactForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    phone_number = StringField("Phone Number", validators=[DataRequired()])
    message = CKEditorField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")

