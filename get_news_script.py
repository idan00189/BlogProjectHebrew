import requests
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, sessionmaker
from flask_login import UserMixin
import os
from newsdataapi import NewsDataApiClient
from bs4 import BeautifulSoup
from pprint import pprint


FLASK_APP_SECRET_KEY = os.environ.get("FLASK_APP_SECRET_KEY")
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_APP_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Session = sessionmaker(app)


NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

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
    img_url = db.Column(db.String(250), nullable=True)
    category = db.Column(db.String(250), nullable=False)
    site_name = db.Column(db.String(250), nullable=True)

    comments = relationship("Comment", back_populates="parent_news_post")

# db.create_all()
def upload_to_database():
    api = NewsDataApiClient(apikey=NEWS_API_KEY)
    response = api.news_api(category="technology", language="he")
    results = response['results']
    pprint(response)
    for news in results:
        description = news['description']
        try:
            title = news['title']
            subtitle = news['description']
            date = news['pubDate'].split()[0]
            img_url = news['image_url']
            site_name = news['source_id']
            if img_url ==None:
                web_scraping =web_scraping_news_site(url=news['link'], site_name=site_name, get_img=True)
                body = web_scraping[0]
                img_url = web_scraping[1]
            else:
                body = web_scraping_news_site(url=news['link'], site_name=site_name, get_img=False)
            category = news['category'][0]



            if body == None:
                body="web scraping error:cant load the content for this post"
            new_news_post = NewsPost(
                title=title,
                subtitle=subtitle,
                date=date,
                body=body,
                img_url=img_url,
                category=category,
                site_name=site_name
            )

            db.session.add(new_news_post)
            db.session.commit()

        except Exception as e:
            print(e)
            db.session.close()

def web_scraping_news_site(url,site_name,get_img):
    my_header = {
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    print(url)
    if site_name == 'tgspot':
        page = requests.get(url, headers=my_header)
        soup = BeautifulSoup(page.text, "html.parser")
        articale = soup.find("div", {"id": "penci-post-entry-inner"})
        all_p = articale.find_all(name='p')

        return " ".join([str(x) for x in all_p])
    # else:
    #     return render_template('blog-post.html', id=id, data=DATA, all_p=None)
    # ArticleBodyComponent
    elif site_name == 'calcalist':
        page = requests.get(url, headers=my_header)
        soup = BeautifulSoup(page.text, "html.parser")
        articale = soup.find("div", {"id": "ArticleBodyComponent"}).find_all('div',
                                                                             {'class': 'text_editor_paragraph rtl'})
        if get_img:
            img = soup.find("div", {"class": "CalcalistArticleTopStoryLinkedImage"}).find('img').get('src')
            print(img)
            return " ".join([str(x) + "<br>" for x in articale]),img
        else:
            return " ".join([str(x) + "<br>" for x in articale])
    else:
        return None

upload_to_database()