from flask import Flask,render_template,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import (generate_password_hash,check_password_hash)

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_no = db.Column(db.String(20), nullable = False)
    first_name = db.Column(db.String(100), nullable = False)
    last_name = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(100), nullable = False)
    department = db.Column(db.String(100), nullable = False)
    position = db.Column(db.String(100), nullable = False)
    status = db.Column(db.String(20), nullable = False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False,unique=True)
    password =db.Column(db.String(255),nullable=False)


@app.route('/')
def home():
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

    return render_template(
        'index.html',
        employees=employees
    )

@app.route('/add', methods=['POST'])

def add_employee():

    employee_no = request.form['employee_no']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    department = request.form['department']
    position = request.form['position']
    status = request.form['status']


    new_employee = Employee(
        employee_no = employee_no,
        first_name = first_name,
        last_name = last_name,
        email = email,
        department = department,
        position = position,
        status = status
    )
    db.session.add(new_employee)
    db.session.commit()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()

    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])

def edit_employee(id):

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        app.run(debug=True)