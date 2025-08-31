from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from typing import  List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import PostForm, RegisterForm, LoginForm, CommentForm
from functools import wraps
import  os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap5(app)
# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("db_url")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    posts: Mapped[List["BlogPost"]] = relationship("BlogPost", back_populates="author"  )
    comments: Mapped[List["Comments"]] = relationship("Comments", back_populates="commentor")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments: Mapped[List["Comments"]] = relationship("Comments", back_populates="post_comments")
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts" )# Matches User.posts )
class Comments(db.Model):
    __tablename__="Comments"
    id: Mapped[int]=mapped_column(Integer, primary_key=True)
    #----------- commentor_id is the foreign key that links to the User table---#
    #comments relations-----#
    commentor_id:Mapped[int]=mapped_column(Integer, ForeignKey("users.id"))
    commentor=relationship("User", back_populates="comments")

    #----------- post_id is the foreign key that links to the BlogPost table---#
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_posts.id"))
    post_comments = relationship("BlogPost", back_populates="comments")
    text: Mapped[str] = mapped_column(Text, nullable=False)
with app.app_context():
    db.create_all()
def admin_only(function):
    @wraps(function)
    def decorator(*args, **kwargs):
        #check if user is logged in and if user id is 1 (admin)
        if not current_user.is_authenticated or current_user.id != 1:
            abort(403, description="You are not authorized to access this page.")
        return function(*args, **kwargs)
    return decorator
def commentors_only(function):
    @wraps(function)
    def decorator(*args, **kwargs):
        #since the Comments table has a commentor_id foreign key, we can use it to check if the current user is the commentor
        comments=db.session.execute(db.select(Comments).where(Comments.commentor_id==current_user.id)).scalar()
        #check if user is logged in and if user id matches the commentor_id
        if not current_user.is_authenticated or current_user.id != comments.commentor_id:
            abort(403)
        return function(*args, **kwargs)
    return decorator
# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        try:
            hash_pass=generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=8)
            new_user= User(email=form.email.data, password=hash_pass, name=form.name.data)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already exists. Please use a different email.")
    return render_template("register.html",form=form)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login',methods=["GET", "POST"])
def login():
    form=LoginForm()
    is_login = False
    if form.validate_on_submit():

        user=db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()

        if user:
            user_id = user.id
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                is_login=True
                return redirect(url_for("get_all_posts", user_id=user_id))
            else:
                flash("Incorrect password, please try again.")
        else:
            flash("Email not found, please register first.")
    return render_template("login.html",form=form,is_login=is_login)


@app.route('/logout')
@login_required
def logout():
    return redirect(url_for("login"))


@app.route('/')
@login_required
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts, is_login=True,user=int(current_user.id))

# TODO: Add a route so that you can click on individual posts.
@app.route("/blogs_info",methods=["GET", "POST"])
def show_post():
    gravatar = Gravatar(app, size=100,
                        rating='g',
                        default='retro',
                        force_default=False,
                        force_lower=False,
                        use_ssl=False,
                        base_url=None)
    post_id = request.args.get('post_id')
    requested_post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    form=CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comments(
                text=form.comment.data,
                commentor=current_user,  # Pass the User object, not a string
                post_comments=requested_post  # Pass the BlogPost object, not a string
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("show_post", post_id=post_id))
        else:
            flash("You need to be logged in to comment.")
            return redirect(url_for("login"))
    return render_template("post.html", post=requested_post, is_login=True,form=form,gravatar=gravatar,commentor=int(current_user.id))


# TODO: add_new_post() to create a new blog post
@app.route("/new_post", methods=["GET", "POST"])
@admin_only
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        blog_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            author=current_user,  # Pass the User object, not a string
            img_url=form.url.data,
            body=form.body.data,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(blog_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, post_status="Add new post",is_login=True)

# TODO: edit_post() to change an existing blog post
@app.route("/edit",methods=["GET", "POST"])
@login_required
@admin_only
def edit_post():
    form = PostForm()
    post_id = request.args.get('id')

    if form.validate_on_submit():
        post_to_update = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
        if post_to_update:
            post_to_update.title = form.title.data
            post_to_update.subtitle = form.subtitle.data
            post_to_update.author = form.author.data
            post_to_update.img_url = form.url.data
            post_to_update.body = form.body.data
            db.session.commit()
            return redirect(url_for("show_post", id=post_id))

    return render_template("make-post.html", form=form,post_status="Edit post", post_id=post_id,is_login=True,user=int(current_user.id))

# TODO: delete_post() to remove a blog post from the database
@app.route("/delete", methods=["GET", "POST"])
@login_required
@admin_only
def delete_post():
    post_id = request.args.get('id')
    post_to_delete = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    if post_to_delete:
        db.session.delete(post_to_delete)
        db.session.commit()
    return redirect(url_for("get_all_posts"))
@app.route("/delete_comment", methods=["GET", "POST"])
@commentors_only
def delete_comment():
    #get post_id so it can be returned to the same post after deleting the comment
    post_id= request.args.get('post_id')
    #get comment_id to identify which comment to delete
    comment_id = request.args.get('comment_id')
    comment_to_delete = db.session.execute(db.select(Comments).where(Comments.id == comment_id)).scalar()
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for("show_post", post_id=post_id))
# Below is the code from previous lessons. No changes needed.
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
