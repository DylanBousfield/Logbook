from __future__ import annotations
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from io import BytesIO
import pandas as pd

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///worklogs.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# MODELS
# -----------------------------
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Workplace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class WorkLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"))
    workplace_id = db.Column(db.Integer, db.ForeignKey("workplace.id"))
    employee = db.relationship("Employee", backref="logs")
    workplace = db.relationship("Workplace", backref="logs")

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
@app.before_first_request
def initialize_database():
    db.create_all()
    if Employee.query.count() == 0:
        db.session.add(Employee(name="John Doe"))
    if Workplace.query.count() == 0:
        db.session.add(Workplace(name="Office"))
    db.session.commit()

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    employees = Employee.query.all()
    workplaces = Workplace.query.all()
    return render_template("index.html", employees=employees, workplaces=workplaces)

@app.route("/log", methods=["POST"])
def log():
    employee_id = request.form["employee_id"]
    workplace_id = request.form["workplace_id"]
    date = request.form["date"]
    hours = float(request.form["hours"])
    description = request.form["description"]

    new_log = WorkLog(
        employee_id=employee_id,
        workplace_id=workplace_id,
        date=date,
        hours=hours,
        description=description
    )
    db.session.add(new_log)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/admin")
def admin():
    logs = WorkLog.query.all()
    employees = Employee.query.all()
    workplaces = Workplace.query.all()
    return render_template("admin.html", logs=logs, employees=employees, workplaces=workplaces)

# -----------------------------
# FILTER + EXPORT
# -----------------------------
@app.route("/filter_logs")
def filter_logs():
    employee_id = request.args.get('employee_id', type=int)
    workplace_id = request.args.get('workplace_id', type=int)
    query = WorkLog.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if workplace_id:
        query = query.filter_by(workplace_id=workplace_id)
    logs = query.all()
    return jsonify(logs=[{
        'id': log.id,
        'employee': log.employee.name,
        'workplace': log.workplace.name,
        'date': log.date,
        'hours': log.hours,
        'description': log.description
    } for log in logs])

@app.route('/export')
def export_excel():
    employee_id = request.args.get('employee_id', type=int)
    workplace_id = request.args.get('workplace_id', type=int)
    query = WorkLog.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if workplace_id:
        query = query.filter_by(workplace_id=workplace_id)
    logs = query.all()
    data = [{
        'Employee': log.employee.name,
        'Workplace': log.workplace.name,
        'Date': log.date,
        'Hours': log.hours,
        'Description': log.description
    } for log in logs]
    df = pd.DataFrame(data)
    total_hours = df['Hours'].sum() if not df.empty else 0
    df = pd.concat([df, pd.DataFrame([{'Employee':'','Workplace':'','Date':'','Hours':total_hours,'Description':'Total Hours'}])], ignore_index=True)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='Work Logs')
    output.seek(0)
    return send_file(output, download_name="work_logs.xlsx", as_attachment=True)

# -----------------------------
# AJAX CRUD ROUTES
# -----------------------------
@app.route("/add_employee", methods=["POST"])
def add_employee():
    name = request.form.get("name")
    if not name:
        return jsonify(success=False, error="No name provided")
    if Employee.query.filter_by(name=name).first():
        return jsonify(success=False, error="Employee already exists")
    emp = Employee(name=name)
    db.session.add(emp)
    db.session.commit()
    return jsonify(success=True, id=emp.id, name=emp.name)

@app.route("/add_workplace", methods=["POST"])
def add_workplace():
    name = request.form.get("name")
    if not name:
        return jsonify(success=False, error="No name provided")
    if Workplace.query.filter_by(name=name).first():
        return jsonify(success=False, error="Workplace already exists")
    wp = Workplace(name=name)
    db.session.add(wp)
    db.session.commit()
    return jsonify(success=True, id=wp.id, name=wp.name)

@app.route("/delete_employee/<int:id>", methods=["POST"])
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    return jsonify(success=True)

@app.route("/delete_workplace/<int:id>", methods=["POST"])
def delete_workplace(id):
    wp = Workplace.query.get_or_404(id)
    db.session.delete(wp)
    db.session.commit()
    return jsonify(success=True)

@app.route("/delete_log/<int:id>", methods=["POST"])
def delete_log(id):
    log = WorkLog.query.get_or_404(id)
    db.session.delete(log)
    db.session.commit()
    return jsonify(success=True)

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
