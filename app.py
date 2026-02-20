from flask import Flask,render_template,redirect,request,url_for,flash,abort
from flask_login import LoginManager,login_user,current_user
from werkzeug.security import generate_password_hash
from models import *
from flask_login import logout_user, login_required
def admin_required():
    if current_user.role != 'admin':
        abort(403)

def company_required():
    if current_user.role != 'company':
        abort(403)

def student_required():
    if current_user.role != 'student':
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

#----------------------------------------------------Authentication and home routes--------------------------------------
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
                elif user.role == 'student':
                    return redirect('/student_dashboard')
                elif user.role == 'company':
                    return redirect('/company_dashboard')
        return render_template('login.html',error='Invalid email or password')
    

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if not email or not password or not role:
        return render_template('register.html', error='Invalid details')

    user = User(
        email=email,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()   

    if role == 'student':
        student = Student(user_id=user.id)
        db.session.add(student)

    elif role == 'company':
        company = Company(
            user_id=user.id,
            approval_status='Approved'  
        )
        db.session.add(company)

    db.session.commit()

    return redirect('/login')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ----------------------------------------------------------ADMIN PAGE ROUTES------------------------------------------------------------------

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

    for drive in company.drives:
        drive.status = 'Cancelled'

    db.session.commit()

    flash(f"{company.company_name} has been blacklisted. All drives cancelled.", "danger")
    return redirect(url_for('admin_company'))

@app.route('/admin_company/approve/<int:company_id>')
@login_required
def admin_approve_company(company_id):
    admin_required()
    company = Company.query.get_or_404(company_id)

    company.approval_status = 'Approved'
    company.is_blacklisted = False

    for drive in company.drives:
        drive.status = 'Approved'

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

@app.route('/admin/student/blacklist/<int:student_id>', methods=['POST'])
@login_required
def student_blacklist(student_id):
    admin_required()
    student = Student.query.get_or_404(student_id)

    student.is_blacklisted = True
    student.approval_status = 'Blacklisted'

    db.session.commit()

    flash(f"{student.name} has been blacklisted.", "danger")
    return redirect(url_for('admin_student'))



@app.route('/admin_company_applications')
@login_required
def admin_company_applications():
    admin_required()
    applications=PlacementDrive.query.all()
    return render_template('admin_company_applications.html',applications=applications)


@app.route('/admin_student_applications')
@login_required
def admin_student_applications():
    admin_required()
    applications=Application.query.all()
    return render_template('admin_student_applications.html',applications=applications)

@app.route('/admin_ongoing_drives')
@login_required
def admin_ongoing_drives():
    admin_required()

    from datetime import date
    drives = PlacementDrive.query.filter(
        PlacementDrive.status == 'Approved',
        PlacementDrive.deadline >= date.today()
    ).all()

    return render_template('admin_ongoing_drives.html', drives=drives)

@app.route('/admin_ongoing_details/<int:drive_id>')
@login_required
def admin_ongoing_details(drive_id):
    admin_required()
    drive = PlacementDrive.query.get_or_404(drive_id)
    return render_template('admin_ongoing_details.html', drive=drive)


@app.route('/admin_student_details/<int:student_id>')
@login_required
def admin_student_details(student_id):
    admin_required()
    student = Student.query.get_or_404(student_id)
    return render_template('admin_student_details.html', student=student)

@app.route('/admin_drive/complete/<int:drive_id>', methods=['POST'])
@login_required
def admin_mark_drive_complete(drive_id):
    admin_required()

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Completed'

    db.session.commit()
    flash("Drive marked as completed.", "success")
    return redirect(url_for('admin_ongoing_drives'))


# ----------------------------------------------------------------------Company Routes------------------------------------------------------------

@app.route('/company_dashboard')
@login_required
def company_dashboard():
    company_required()

    from datetime import date

    company = current_user.company
    if not company:
        abort(403)

    drives = PlacementDrive.query.filter(
        PlacementDrive.company_id == company.id,  
        PlacementDrive.deadline >= date.today()
    ).all()

    return render_template('company_dashboard.html', drives=drives)


@app.route('/company_drives')
@login_required
def company_drives():
    company_required()

    company = Company.query.filter_by(user_id=current_user.id).first()
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()

    return render_template('company_drives.html', drives=drives)


@app.route('/company_drives/create_drive', methods=['GET','POST'])
@login_required
def company_create_drive():
    company_required()

    if request.method == 'GET':
        return render_template('company_create_drive.html')

    job_title = request.form.get('job_title')
    description = request.form.get('description')
    deadline = request.form.get('deadline')
    eligibility = request.form.get('eligibility')

    if not (job_title and description and deadline):
        return render_template('company_create_drive.html', error='Invalid details')

    deadline = datetime.strptime(deadline, "%Y-%m-%d").date()

    company = Company.query.filter_by(user_id=current_user.id).first()

    if not company:
        abort(403)

    drive = PlacementDrive(
        job_title=job_title,
        job_description=description,
        eligibility=eligibility,
        deadline=deadline,
        company_id=company.id,  
        status='Approved'
    )

    db.session.add(drive)
    db.session.commit()

    return redirect('/company_drives')


@app.route('/company/student')
@login_required
def company_student():
    company_required()  

    company = current_user.company

    drive_ids = [drive.id for drive in company.drives]
    applications = Application.query.filter(Application.drive_id.in_(drive_ids)).all()

    return render_template('company_student.html', applications=applications)


@app.route('/company/drive/details/<int:drive_id>')
@login_required
def company_drive_details(drive_id):
    company_required()
    company = current_user.company
    drive_ids = [drive.id for drive in company.drives]
    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = Application.query.filter(Application.drive_id.in_(drive_ids), Application.drive_id == drive_id).all()
    return render_template('company_drive_details.html', drive=drive, applications=applications)


@app.route('/company_student_details/<int:student_id>')
@login_required
def company_student_details(student_id):
    company_required()

    student = Student.query.get_or_404(student_id)

    application = Application.query.filter_by(
        student_id=student.id
    ).first_or_404()

    return render_template(
        'company_student_details.html',
        student=student,
        application=application  
    )


@app.route('/company/application/update/<int:application_id>', methods=['POST'])
@login_required
def company_update_application_status(application_id):
    company_required()

    application = Application.query.get_or_404(application_id)

    new_status = request.form.get('status')

    application.status = new_status
    db.session.commit()

    flash(f"Application marked as {new_status}.", "success")
    return redirect(request.referrer)

# ---------------------------------------------------------------Student Routes----------------------------------------------------------------


@app.route('/student_dashboard')
@login_required
def student_dashboard():
    student_required()
    student=current_user.student
    companies = Company.query.filter(
    Company.approval_status == 'Approved',
    Company.is_blacklisted == False
).all()

    applications=Application.query.filter_by(student_id=student.id).all()
    return render_template('student_dashboard.html',applications=applications,companies=companies)

@app.route('/student_drives')
@login_required
def student_drives():
    student_required()
    student=current_user.student
    applications=Application.query.filter_by(student_id=student.id).all()
    return render_template('student_drives.html',applications=applications)


@app.route('/student_company')
@login_required
def student_company():
    student_required()
    companies=Company.query.all()
    return render_template('student_company.html',companies=companies)


@app.route('/student_company/details/<int:company_id>')
@login_required
def student_company_details(company_id):    
    student_required()
    company=Company.query.get_or_404(company_id)
    drives=PlacementDrive.query.filter_by(company_id=company.id).all()
    return render_template('student_company_details.html',company=company,drives=drives)



@app.route('/student_apply/<int:drive_id>', methods=['POST'])
@login_required
def student_apply(drive_id):
    student_required()

    student = current_user.student
    drive = PlacementDrive.query.get_or_404(drive_id)

    #  Prevent duplicate applications
    existing_application = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive.id
    ).first()

    if existing_application:
        flash("You have already applied to this drive.", "warning")
        return redirect(url_for('student_drives'))

    application = Application(
        student_id=student.id,
        drive_id=drive.id,
        status='Waiting'
    )

    db.session.add(application)
    db.session.commit()

    flash("Application submitted successfully!", "success")
    return redirect(url_for('student_drives'))


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