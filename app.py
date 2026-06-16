import os 
from werkzeug.utils import secure_filename
from flask import Flask,render_template,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import (generate_password_hash,check_password_hash)
from flask_migrate import Migrate


app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
db = SQLAlchemy(app)
migrate = Migrate(app,db)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_no = db.Column(db.String(20), nullable = False,unique=True)
    first_name = db.Column(db.String(100), nullable = False)
    last_name = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(100), nullable = False)
    department = db.Column(db.String(100), nullable = False)
    position = db.Column(db.String(100), nullable = False)
    status = db.Column(db.String(20), nullable = False)
    photo = db.Column(db.String(255), nullable=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False,unique=True)
    password =db.Column(db.String(255),nullable=False)


@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')

    search = request.args.get('search','')
    if search:
        employees = Employee.query.filter(
        or_(
            Employee.employee_no.contains(search),
            Employee.first_name.contains(search),
            Employee.last_name.contains(search),
            Employee.email.contains(search),
            Employee.department.contains(search),
            Employee.position.contains(search),
            Employee.status.contains(search)
            )
    ).all()
    else:
        employees = Employee.query.all()
        total_employees = Employee.query.count()
        active_employees = Employee.query.filter_by(status='Active').count()
        inactive_employees = Employee.query.filter_by(status='Inactive').count()

    return render_template(
        'index.html',
        employees=employees,
        search=search,
        username=session['username'],
        total_employees = total_employees,
        active_employees = active_employees,
        inactive_employees = inactive_employees
    )

@app.route('/add', methods=['POST'])

def add_employee():

    if 'username' not in session:
        return redirect('/login')
    


    employee_no = request.form['employee_no']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    department = request.form['department']
    position = request.form['position']
    status = request.form['status']
    photo = request.files['photo']

    filename = None

    if photo and photo.filename:
        filename = secure_filename(
            photo.filename
        )
        photo.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

    existing_employee = Employee.query.filter_by(employee_no=employee_no).first()
    if existing_employee:
        return """ 
            <script>
                alert('Employee Number already exists');
                window.location.href='/';
            </script>
            """

    new_employee = Employee(
        employee_no = employee_no,
        first_name = first_name,
        last_name = last_name,
        email = email,
        department = department,
        position = position,
        status = status,
        photo=filename
    )
    db.session.add(new_employee)
    db.session.commit()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete_employee(id):
    if 'username' not in session:
        return redirect('/login')

    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()

    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])

def edit_employee(id):
    if 'username' not in session:
        return redirect('/login')
    
    employee= Employee.query.get_or_404(id)
    if request.method == 'POST':

        employee.employee_no = request.form['employee_no']
        employee.first_name = request.form['first_name']
        employee.last_name = request.form['last_name']
        employee.email = request.form['email']
        employee.department = request.form['department']
        employee.position = request.form['position']
        employee.status = request.form['status']

        db.session.commit()
        print('saved')

        return redirect('/')
    
    return render_template(
        'edit.html',
        employee=employee
    )

@app.route('/create-admin')
def create_admin():

    return 'Disabled'

    hashed_password = generate_password_hash('admin123')

    admin = User(
        username='admin',
        password=hashed_password
    )
    db.session.add(admin)
    db.session.commit()

    return 'Admin Created'

@app.route('/login', methods=['GET','POST'])
def login():
    if 'username' in session:
        return redirect('/')

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):
            session['username'] = user.username
            return redirect('/')
        return 'Invalid Username or Password'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username',None)
    return redirect('/login')

if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(debug=True)