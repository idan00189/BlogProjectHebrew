from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import CreatePostForm,RegisterForm,LogInForm,CommentForm
from flask_gravatar import Gravatar
from functools import wraps
from flask import abort,request
from sqlalchemy import desc
import os
global DATA

MY_EMAIL = os.environ.get("MY_EMAIL")
MY_EMAIL_PASSWORD = os.environ.get("MY_EMAIL_PASSWORD")
FLASK_APP_SECRET_KEY = os.environ.get("FLASK_APP_SECRET_KEY")

login_manager = LoginManager()
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_APP_SECRET_KEY
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager.init_app(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",'sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="parent_blog_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    blog_post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_blog_post = relationship("BlogPost", back_populates="comments")

    news_post_id = db.Column(db.Integer, db.ForeignKey("news_posts.id"))
    parent_news_post = relationship("NewsPost", back_populates="comments")

class NewsPost(db.Model):
    __tablename__ = "news_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, unique=True, nullable=False)
    subtitle = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    category = db.Column(db.String(250), nullable=False)
    site_name = db.Column(db.String(250), nullable=False)

    comments = relationship("Comment", back_populates="parent_news_post")

# db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.is_authenticated is False:
            return abort(403)
        if current_user.id != 1 :
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function



@app.route('/')
def get_all_posts():
    blog_posts = BlogPost.query.all()
    return render_template("index.html", all_posts=blog_posts,error=None)


@app.route('/register',methods=["GET","POST"])
def register():
    error = None
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password_hash = generate_password_hash(password=form.password.data,method="pbkdf2:sha256",salt_length=8)
        name = form.name.data
        if User.query.filter_by(email=email).first() is None:
            new_user = User(email=email,password= password_hash,name=name)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            error = "האימייל הזה קיים במערכת, התחבר במקום."
            return render_template("register.html",form=form,error = error)

    return render_template("register.html",form=form)


@app.route('/login',methods=["GET","POST"])
def login():
    if request.args.get("error"):
        error = request.args.get("error")
    else:
        error = None
    form = LogInForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user is None:
            error = 'האימייל לא קיים, בבקשה תנסה שוב.'
            return render_template("login.html", form=form,error=error)
        else:
            if check_password_hash(pwhash=user.password,password=password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                error = 'סיסמא לא נכונה, בבקשה תנסה שוב.'
                return render_template("login.html", form=form,error=error)

    return render_template("login.html",form=form,error=error)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=["GET","POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text=form.body.data,
                comment_author=current_user,
                parent_blog_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            return render_template("blog-post.html", post=requested_post, form=form)
        else:
            error = "please log in to add comment"
            return redirect(url_for("login", error=error))

    return render_template("blog-post.html", post=requested_post, form=form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact",methods=["GET","POST"])
def contact():
    return render_template("contact.html")


@app.route("/new-post",methods=["GET","POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>",methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/news")
def show_latest_news():
    news_posts = NewsPost.query.order_by(desc(NewsPost.id))
    return render_template("news-latest.html", all_posts=news_posts, error=None)


@app.route("/news/<int:post_id>",methods=["GET","POST"])
def show_news_post(post_id):
    form = CommentForm()
    requested_post = NewsPost.query.get(post_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text = form.body.data,
                comment_author=current_user,
                parent_news_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            return render_template("news-post.html", post=requested_post, form=form)
        else:
            error = "please log in to add comment"
            return redirect(url_for("login",error=error))

    return render_template("news-post.html", post=requested_post,form=form)



if __name__ == "__main__":
    app.run(debug=True,port=5005)
