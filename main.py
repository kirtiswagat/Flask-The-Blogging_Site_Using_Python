from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import os
import math

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



with open('config.json', 'r') as c:
    params = json.load(c)["params"]
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)

local_server = True
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/blog_from_engineers'
db = SQLAlchemy(app)

class Contact_details(db.Model):
    ''' contact_details_id_pk, contact_details_name,
        contact_details_email, contact_details_phone_no,
        contact_details_msg, contact_details_date'''
    contact_details_id_pk = db.Column(db.Integer, primary_key=True)
    contact_details_name = db.Column(db.String(30), nullable=False)
    contact_details_email = db.Column(db.String(20), nullable=False)
    contact_details_phone_no = db.Column(db.String(13), nullable=False)
    contact_details_msg = db.Column(db.Text, nullable=False)
    contact_details_date = db.Column(db.DateTime, nullable=True, default=datetime.now())

class Posts(db.Model):
    posts_id_pk = db.Column(db.Integer, primary_key=True)
    posts_title = db.Column(db.String(80), nullable=False)
    posts_slug = db.Column(db.String(21), nullable=False)
    posts_content = db.Column(db.String(250), nullable=False)
    posts_date = db.Column(db.String(12), nullable=True)
    posts_img_file = db.Column(db.String(12), nullable=True)
    posts_by= db.Column(db.String(50), nullable=False)



@app.route("/")
def home():
    #posts= Posts.query.filter_by().all()[0:params['no_of_posts']]
    
    posts = Posts.query.filter_by().all()#[0:params['no_of_posts']]

    last= math.ceil(len(posts)/int(params['no_of_posts']))
    page= request.args.get('page')
    if(not str(page).isnumeric()):
        page=1

    page= int(page)
    posts= posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if (page==1):
        prevp= "#"
        nextp= "/?page="+ str(page+1)
    elif(page==last):
        nextp= "#"
        prevp= "/?page="+ str(page-1)
    else:
        prevp= "/?page="+ str(page-1)
        nextp= "/?page="+ str(page+1)
   

    return render_template('index.html',params=params, posts= posts, prev= prevp, next=nextp )


@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/dashboard", methods= ['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user']== params['admin_user']):
        posts= Posts.query.all()
        return render_template('dashboard.html', params=params, posts= posts)


    if (request.method== 'POST'):
        username= request.form.get('uname')
        userpass= request.form.get('pass')
        if (username == params['admin_user'] and userpass== params['admin_password']):
            session['user']= username
            posts= Posts.query.all()
            return render_template('dashboard.html', params=params, posts= posts)
            #pass
        
    return render_template('login.html', params=params)



@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(posts_slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name= request.form.get('name')
        email= request.form.get('email')
        phone= request.form.get('phone_no')
        message= request.form.get('msg')
        entry= Contact_details(contact_details_name= name,contact_details_email= email,
                               contact_details_phone_no= phone, contact_details_msg= message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + "Contact No:" +phone + "\n" + "Email_Id:" + email
                          )
    return render_template('contact.html',params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    #return redirect('/dashboard')
    return render_template('login.html',params=params)


@app.route("/chart")
def chart():
    if ('user' in session and session['user']== params['admin_user']):
        return render_template('charts.html',params=params)

@app.route("/table")
def table():
    posts= Posts.query.all()
    return render_template('tables.html', params= params, posts= posts)

@app.route("/edit/<string:posts_id_pk>", methods=['GET', 'POST'])
def edit(posts_id_pk):
    #if ('user' in session and session['user']== params['admin_user']):
    if (request.method=='POST'):
        box_title= request.form.get('title')
        slug= request.form.get('slug')
        content= request.form.get('content')
        post_by= request.form.get('post_by')
        img_file= request.form.get('img_file')
        date= datetime.now()


        if (posts_id_pk== '0'):
            post= Posts(posts_title= box_title, posts_slug=slug, posts_content=content,posts_date= date,
                                posts_img_file=img_file, posts_by= post_by)
            db.session.add(post)
            db.session.commit()

        else:
            post= Posts.query.filter_by(posts_id_pk= posts_id_pk).first()
            post.posts_title= box_title
            post.posts_slug= slug
            post.posts_content= content
            post.posts_date= date
            post.posts_img_file= img_file
            post.posts_by= post_by
            db.session.commit()
            return redirect('/edit/'+posts_id_pk)

    post= Posts.query.filter_by(posts_id_pk= posts_id_pk).first()

    return render_template('edit.html', params=params, posts= post, posts_id_pk= posts_id_pk)

@app.route("/new_blog", methods=['GET', 'POST'])
def new_blog():
    
    if (request.method== 'POST'):
        box_title= request.form.get('title')
        slug= request.form.get('slug')
        content= request.form.get('content')
        post_by= request.form.get('post_by')
        img_file= request.form.get('img_file')
        date= datetime.now()
        posts= Posts(posts_title= box_title, posts_slug=slug, posts_content=content,posts_date= date,
                                posts_img_file=img_file, posts_by= post_by)
        db.session.add(posts)
        db.session.commit()
    return render_template('new_blog.html', params=params)

 
@app.route("/delete/<string:posts_id_pk>", methods=['GET'])
def delete(posts_id_pk):
    #1if ('user' in session and session['user']== params['admin_user']):
    if request.method== 'GET':
        post= Posts.query.filter_by(posts_id_pk= posts_id_pk).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/table')
    #return render_template('tables.html', params=params)



app.secret_key= os.urandom(24)
app.run(debug=True)