from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
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


@app.route('/')

def home():
    search = request.args.get('search','')
    if search:
        employees = Employee.query.filter(
            Employee.fullname.contains(search)
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

        employee_no = request.form['employee_no']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        department = request.form['department']
        position = request.form['position']
        status = request.form['status']

        db.session.commit()
        print('saved')

        return redirect('/')
    
    return render_template(
        'edit.html',
        employee=employee
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        app.run(debug=True)