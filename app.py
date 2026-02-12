from flask import Flask,render_template,redirect,request,url_for,flash,abort
from flask_login import LoginManager,login_user,current_user
from werkzeug.security import generate_password_hash
from models import *
from flask_login import logout_user, login_required
def admin_required():
    if current_user.role != 'admin':
        abort(403)



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
                if user.role == 'admin':
                    return redirect('/admin_dashboard')
                # elif user.role == 'student':
                #     return redirect('/student_dashboard')
                # elif user.role == 'company':
                #     return redirect('/company_dashboard')
        return render_template('login.html',error='Invalid email or password')
    

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if email and password and role:
            user = User(
                email=email,
                password=generate_password_hash(password),
                role=role
            )
            db.session.add(user)
            db.session.commit()
            return redirect('/login')

        return render_template('register.html', error='Invalid details')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------ADMIN PAGE ROUTES------------

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    admin_required()
    companies=Company.query.all()
    students=Student.query.all()
    applications=Application.query.all()
    return render_template('admin_dashboard.html',companies=companies ,students=students,applications=applications)

@app.route('/admin_company')
@login_required
def admin_company():
    admin_required()
    companies=Company.query.all()
    return render_template('admin_company.html',companies=companies)

@app.route('/admin_company/blacklist/<int:company_id>', methods=['POST'])
@login_required
def company_blacklist(company_id):
    admin_required()
    company = Company.query.get_or_404(company_id)

    company.is_blacklisted = True
    company.approval_status = 'Blacklisted'

    db.session.commit()

    flash(f"{company.company_name} has been blacklisted.", "danger")
    return redirect(url_for('admin_company'))
@app.route('/admin_company/approve/<int:company_id>')
@login_required
def admin_approve_company(company_id):
    admin_required()
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'Approved'
    db.session.commit()
    return redirect(url_for('admin_company'))


@app.route('/admin_company/reject/<int:company_id>')
@login_required
def admin_reject_company(company_id):
    admin_required()
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'Rejected'
    db.session.commit()
    return redirect(url_for('admin_company'))

@app.route('/admin_student')
@login_required
def admin_student():
    admin_required()
    students=Student.query.all()
    return render_template('admin_student.html',students=students)



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