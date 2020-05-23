from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

# Register Form Decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session ##giriş yapıldıysa dashboard gidiyor
            return f(*args, **kwargs)
        else: 
            flash ("Bu sayfayı görüntülemek için lütfen giriş yapın","danger")
            return redirect(url_for"/login")
    return decorated_function

# Register form
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=24)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min=6,max=20)])
    email = StringField("Email Adresi",validators=[validators.Email(message= "Lütfen Geçerli Bir Adres Giriniz...")])  
    password=PasswordField("Parola: ",validators=[
        validators.DataRequired(message="Lütfen Parola Belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor...")])
    confirm = PasswordField("Parola Doğrula")

##Login Form
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


app = Flask(__name__)
app.secret_key="bblog" ##for flash messages to be seen 

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "bblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


mysql = MySQL(app)


@app.route("/")
def index():
    return render_template("index.html",articles=articles)

@app.route("/about")
def about():
    return render_template("about.html")

##Articles Page
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()

    sorgu="Select * from articles"

    result = cursor.execute(sorgu)
    if result > 0:              ################if we have articles
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else: 
        return render_template("articles.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s"
    result=cursor.execute(sorgu,(session["username"],))

    if result >0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:

    return render_template("dashboard.html")

#Register
@app.route("/register",methods = ["GET","POST"])
def register():
    form=RegisterForm(request.form) ##gelen get/post isteklerine göre
    if request.method == "POST" and form.validate():
        
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor() ##mysql bağlantısı

        sorgu = "Insert into users (name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit 

        cursor.close()
        flash("Başarıyla Kayıt Oldunuz","success") ##flash process connected with layout
        return redirect(url_for("login")) ##ilgili url git (kök dizine)
    else:
        return render_template("register.html",form=form)

##Login process
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor=mysql.connection.cursor()

        sorgu = "Select * from users where username=%s"

        result = cursor.execute(sorgu,(username,))

        if result > 0: ## there is user
            data = cursor.fetchone() ##sql connection for pass
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password): ##password check
                flash("Başarıyla Giriş Yapıldı...","success")

                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash ("Parolanızı Yanlış Girdiniz","danger")
                return redirect(url_for("login"))
        else: ## if there is not any user
            flash("Böyle bir kullanıcı bulunmuyor...","danger") ##flash message denger
            return redirect(url_for("login"))
    return render_template("login.html", form = form)



@app.route("/article/<string:id>") ##flask dynamic url
def detail(id):
    return "Article Id:" + id
## Details Page

@app.route("/article/<string:id>")  ##checking according to id from db
def article(id):
   
    cursor = mysql.connection.cursor
    sorgu = "Select * from articles where id= %s"
    result = cursor.execute(sorgu,(id,))
    
    if result>0:
        article = cursor.fetchone()
        return render_template("article.html", article= article)
    else: 
        return render_template("article.html")
##Logout process
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("/index"))

##Article Adding
@app.route("/addarticle",methods= ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close

        flash("Makale Başarıyla Eklendi","success")
        
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form=form) 

##Article Deleting 
@app.route("/delete/<string:id>") ###dynamic url
@login_required
def delete (id):
    cursor=mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result= cursor.execute (sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Bu makaleyi silemezsiniz...")
        return redirect(url_for("index"))
##  Article Update
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu="Select * from articles where id= %s and author= %s"
        result= cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash ("Böyle bir makale mevcut değil ya da yetkiniz yok...","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm
            form.title.data = article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
    else:
        ##POST REQUEST  
        form= ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.title.data

        sorgu2= "Update articles set title=%s,content=%s,where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale Başarıyla Güncellendi","success")

        return redirect(url_for("dashboard"))
        pass
## Article Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validator=[validators.Lenght(min=5,max=100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])

## Search URL
@app.route("/search", methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword") ##connected wirh articles keyword name 
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword + "%'"
        result= cursor.execute(sorgu)

        if result ==0:
            flash ("Makale bulunamadı...","warning")
            return redirect(url_for("articles"))
        else: 
            articles = cursor.fetchall()
            return render_template("articles.html",articles=articles)
        

if __name__ == "__main__":  ##terminalden çalıştırıldığında
    app.run(debug=True)


