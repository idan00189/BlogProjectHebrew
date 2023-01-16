from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Length,Email
from flask_ckeditor import CKEditorField
from flask_wtf import Form, RecaptchaField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("כותרת הפוסט", validators=[DataRequired()])
    subtitle = StringField("כותרת משנה", validators=[DataRequired()])
    img_url = StringField("קישור לתמונה", validators=[DataRequired(), URL()])
    body = CKEditorField("תוכן הפוסט", validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField("הוספה")

class RegisterForm(FlaskForm):
    email = StringField("אמייל", validators=[DataRequired(),Email()])
    password = PasswordField("סיסמא", validators=[DataRequired(),Length(min=8,max=64)])
    name = StringField("שם מלא", validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField("הרשמה")

class LogInForm(FlaskForm):
    email = StringField("אמייל", validators=[DataRequired(), Email()])
    password = PasswordField("סיסמא", validators=[DataRequired(), Length(min=8, max=64)])
    submit = SubmitField("התחברות")

class CommentForm(FlaskForm):
    body = CKEditorField("תגובה", validators=[DataRequired()])
    submit = SubmitField("שלח")