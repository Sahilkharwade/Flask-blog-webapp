from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#it use to rander templete

app=Flask(__name__)

#config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'portfolio'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL

mysql=MySQL(app)




@app.route('/')
def index():
	return render_template("index.html")

@app.route('/about/')
def about():
	return render_template("about.html")



@app.route('/services/')
def services():
	return render_template("services.html")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first" , 'danger')
            return redirect(url_for('login'))

    return wrap




class RegisterForm(Form):
	name = StringField('Name',[validators.length(min=2,max=50)])
	username = StringField('Username', [validators.length(min=2, max=50)])
	email = StringField('Email', [validators.length(min=2, max=50)])
	password=PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm', message='password donot match')])
	confirm=PasswordField('Confirm password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_cadidate = request.form['password']

        #create cur

        cur = mysql.connection.cursor()

        #get user by username

        result =cur.execute("SELECT * FROM users WHERE username = %s",[username])
        if result > 0:
            data=cur.fetchone()
            password=data['password']

            #campare password
            if sha256_crypt.verify(password_cadidate,password):
                # app.logger.info('PASSWORD MATCHED')
                #passed
                session['logged_in']=True
                session['username']=username

                flash("You are now logged in",'success')
                return redirect(url_for('dashboard'))
            else:
                #app logger print this in terminal
                # app.logger.info('PASSWORD NOT MATCHED')
                error = 'WRONG PASSWORD ENTERED'
                return render_template('login.html', error=error)
            #close the connection
            cur.close()
        else:
            error='Username not found'
            return render_template('login.html',error=error)
    return render_template('login.html')


# @app.route('/test/')
# def test():
# 	return render_template("test.html")

@app.route('/articles')
def articles():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('article.html', articles=articles)
    else:
        msg = 'NO Article Found'
        return render_template('article.html', msg=msg)
    cur.close()




@app.route('/article/<string:id>/')
def ID(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    article= cur.fetchone()


    return render_template('test.html',article=article)


# logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("You are now logout", 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('dash.html', articles=articles)
    else:
        msg = 'NO Article Found'
        return render_template('dash.html', msg=msg)
    cur.close()


class ArticleForm(Form):
    title = StringField('Title', [validators.length(min=2, max=200)])
    body = TextAreaField('Body', [validators.length(min=30)])


@app.route('/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        # create a cur
        cur = mysql.connection.cursor()

        # execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s, %s ,%s)", (title, body, session['username']))

        # commit
        mysql.connection.commit()
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add.html', form=form)


@app.route('/edit_article/<string:id>/', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>')
@login_required
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    mysql.connection.commit()

    # Close connection
    cur.close()
    flash('article', 'success')

    return redirect(url_for('dashboard'))


if __name__=="__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)