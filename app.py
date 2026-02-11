from flask import Flask,render_template,redirect,request
from flask_login import LoginManager,login_user
from werkzeug.security import generate_password_hash
from models import db, User

app = Flask(__name__)

app.config['SECRET_KEY'] = 'placement-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#------------Authentication and home routes-------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email=request.form.get('email')
        password=request.form.get('password')
        if email and password:
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                # return redirect('/dashboard')
        return render_template('login.html',error='Invalid email or password')
    

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        email=request.form.get('email')
        password=request.form.get('password')
        role=request.form.get('role')
        if email and password and role:
            user = User(email=email,password=password,role=role)
            db.session.add(user)
            db.session.commit()
            return redirect('/login')
        return render_template('register.html',error='Invalid email or password')

# --------- DATABASE CREATION + ADMIN ----------
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin_user = User(
            email='admin@placement.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print(" Admin user created")
    else:
        print(" Admin already exists")


if __name__ == '__main__':
    app.run(debug=True)