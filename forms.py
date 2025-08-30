from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class PostForm(FlaskForm):
    title = StringField("The blog post title :", validators=[DataRequired()])
    subtitle = StringField("The subtitle:", validators=[DataRequired()])
    url= StringField("The image url:", validators=[DataRequired(), URL()])
    body = CKEditorField("The blog post body:", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")

# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment = CKEditorField("Your comment:", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")