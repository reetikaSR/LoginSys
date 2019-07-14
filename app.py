from flask import Flask, render_template, request, session, redirect, url_for, g
from flask_pymongo import PyMongo
import bcrypt


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
mongo = PyMongo(app)
users = mongo.db.users
companies = mongo.db.companies
app.secret_key = "my_key"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


@app.route('/', methods=['POST','GET'])
def login():
    if 'username' in session and session['username'] is not None:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        existing = users.find_one({'name': request.form['username']})
        if existing:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), existing['password']) == existing['password']:
                session['username'] = request.form['username']
                return redirect(url_for('profile'))
        return render_template('login.html', value="Invalid username or password")
    return render_template('login.html')


@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        existing = users.find_one({'name': request.form['username']})
        if existing is None:
            password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            file = request.files['file']
            if file and allowed_file(file.filename):
                mongo.save_file("user_" + request.form['username'], file)
            users.insert({'name': request.form['username'], 'password': password, 'role': request.form['role'],
                          'company': request.form['company']})
            session['username'] = request.form['username']
            return redirect(url_for('login'))
        return render_template('signup.html', value="UserName already exists")
    return render_template('signup.html')


@app.route('/profile', methods=['GET'])
def profile():
    if 'username' in session:
        existing = users.find_one({'name': session['username']})
        if existing:
            try:
                user_file = mongo.send_file("user_"+session['username'])
                return render_template('myprofile.html', user=existing, user_image=user_file)
            except:
                return render_template('myprofile.html', user=existing)
    return redirect(url_for('login'))


@app.route('/org/<org_name>', methods=['GET'])
def org(org_name):
    existing = companies.find_one({'name':org_name})
    print(request, session)
    if existing:
        total_users = existing['total']
        total_users[session['username']] = True
        companies.update_one({'_id': existing['_id']}, {'$set': {'total': total_users}}, upsert=False)
        count = len(total_users)
        try:
            org_file = mongo.send_file("org_" + org_name)
            return render_template('company.html', org=existing, org_image=org_file, total_count=count)
        except:
            return render_template('company.html', org=existing)
    return redirect(url_for('addOrg', org_name = org_name))


@app.route('/addOrg/<org_name>', methods=['GET','POST'])
def addOrg(org_name):
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            mongo.save_file("org_" + org_name, file)
        d = {}
        companies.insert({'name': org_name, 'address': request.form['address'], 'total': d, 'current': []})
        return redirect(url_for('org', org_name=org_name))
    return render_template('add.html', org_name=org_name)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS