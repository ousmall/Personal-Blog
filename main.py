from datetime import date, datetime
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ContactForm
from hashlib import md5
from secret import SMTP_SERVER, SMTP_PORT, MY_EMAIL, MY_PASS
import smtplib


year = date.today().year


# CREATE GRAVATAR MANUALLY
def gravatar(email, size=100, default='identicon', rating='g'):
    email_hash = md5(email.lower().encode()).hexdigest()
    gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}&r={rating}"
    return gravatar_url


# SEND MESSAGE FUNCTION
def send_email(name, email, phone_num, message):
    try:
        email_message = (f"Subject: A message comes from your blog!\n\n"
                         f"You got a message:\n"
                         f"From {name}, Email:{email}, phone number:{phone_num} \n"
                         f"For details:\n"
                         f"{message}")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASS)
            connection.sendmail(from_addr=MY_EMAIL,
                                to_addrs=MY_EMAIL,
                                msg=email_message)
            print(f"The message was sent.")
    except smtplib.SMTPServerDisconnected:
        print("ERROR: Could not connect to the SMTP server. "
              "Make sure the SMTP_LOGIN and SMTP_PASS credentials have been set correctly.")


# TIME CALCULATION FUNCTION
def calculate_time_difference(posted_time):
    current_time = datetime.now()
    time_difference = current_time - posted_time
    # When we calculate the time difference between two datetime objects,
    # we typically get a timedelta object, which represents the difference in terms of days,
    # seconds, and microseconds.

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    # the divmod() function returns a tuple containing the quotient and the remainder
    # when dividing two numbers.

    # time_difference.seconds contains the number of seconds in the time difference.
    # Since one hour equals 3600 seconds, we divide the seconds by 3600 to get the quotient,
    # which represents the number of hours, and the remainder represents the remaining seconds
    # that are less than an hour.

    # the same way to get minutes but use _ to indicate that we don't care about
    # the second part of the remainder.

    if days > 0:
        return f"Posted {days} days ago"
    elif hours > 0:
        return f"Posted {hours} hours ago"
    elif minutes > 0:
        return f"Posted {minutes} minutes ago"
    else:
        return "Posted just now"


# CREATE A DECORATOR TO RESTRICT USAGE TO OTHER USERS
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


# CREATE A DECORATOR TO DEFINE ONLY COMMENTER CAN DELETE COMMENT
def only_commenter(function):
    @wraps(function)
    def check(*args, **kwargs):
        user = db.session.execute(db.select(Comment).where(Comment.author_id == current_user.id)).scalar()
        if not current_user.is_authenticated or current_user.id != user.author_id:
            return abort(403)
        return function(*args, **kwargs)

    return check


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    # relationship to table User(child)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    author: Mapped[str] = relationship("User", back_populates="posts")

    # one for table Comment(parent)
    comments = relationship("Comment", back_populates="comment_post")


# Create a User table for all your registered users.
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))

    # one for table BlogPost(parent)
    posts = relationship("BlogPost", back_populates="author")

    # one for table Comment(parent)
    comments = relationship("Comment", back_populates="comment_author")

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password


class Comment(db.Model):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    posted_time = db.Column(db.DateTime, nullable=False)

    # relationship to table User(child)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    comment_author: Mapped[str] = relationship("User", back_populates="comments")

    # relationship to table BlogPost(child)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_posts.id"))
    comment_post: Mapped[str] = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html",
                           all_posts=posts, logged_in=current_user.is_authenticated, current_year=year)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            flash('This email has already been registered, Login instead!')
            return redirect(url_for('login'))
        else:
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)

        return redirect(url_for('get_all_posts'))
    return render_template("register.html",
                           form=form, logged_in=current_user.is_authenticated, current_year=year)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Invalid Email, Please register first.')
            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash('Invalid Password, Please try again.')
            return redirect(url_for('login'))

        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form, current_year=year)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Only registered users can post comments')
            return redirect(url_for('login'))
        else:
            new_comment = Comment(
                text=comment_form.text.data,
                comment_author=current_user,
                comment_post=requested_post,
                posted_time=datetime.now()
            )
            db.session.add(new_comment)
            db.session.commit()

    # add gravatar:
    user = current_user
    gravatar_urls = {comment.comment_author.id: gravatar(comment.comment_author.email)
                     for comment in requested_post.comments}

    comments = Comment.query.filter_by(post_id=post_id).all()
    the_time = []
    for comments_time in comments:
        print(comments_time.posted_time)
        time = calculate_time_difference(comments_time.posted_time)
        the_time.append(time)
    print(the_time)

    return render_template("post.html", post=requested_post,
                           logged_in=current_user.is_authenticated, form=comment_form,
                           user=user, gravatar_urls=gravatar_urls, current_year=year, posted_time=the_time)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# only administer can post blog
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html",
                           form=form, logged_in=current_user.is_authenticated, current_year=year)


# only administer can modify
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html",
                           form=edit_form, is_edit=True,
                           logged_in=current_user.is_authenticated, current_year=year)


# only administer can delete
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# only commenter can delete
@app.route("/delete/comment/<int:comment_id>/<int:post_id>")
@only_commenter
def delete_comment(post_id, comment_id):
    post_to_delete = db.get_or_404(Comment, comment_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('show_post', post_id=post_id))


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated, current_year=year)


@app.route("/contact", methods=['POST', 'GET'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.username.data,
        email = form.email.data,
        phone_num = form.phone_number.data,
        message = form.message.data
        send_email(name, email, phone_num, message)
        if send_email:
            flash('Successfully sent your message!')
            return redirect(url_for('contact'))
        else:
            flash('Unable to send email, please try again later')
    return render_template("contact.html", form=form,
                           logged_in=current_user.is_authenticated,
                           current_year=year)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
