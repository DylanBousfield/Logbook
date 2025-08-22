from __future__ import annotations
import os
from datetime import datetime, date
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./worklogs.db"
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
@app.before_request
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
    hours = request.form["hours"]
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

@app.route("/export")
def export():
    employee_id = request.args.get("employee_id")
    workplace_id = request.args.get("workplace_id")

    query = WorkLog.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if workplace_id:
        query = query.filter_by(workplace_id=workplace_id)

    logs = query.all()

    data = []
    for log in logs:
        data.append({
            "Employee": log.employee.name,
            "Workplace": log.workplace.name,
            "Date": log.date,
            "Hours": log.hours,
            "Description": log.description
        })

    df = pd.DataFrame(data)
    filename = "worklogs.xlsx"
    df.to_excel(filename, index=False)
    return send_file(filename, as_attachment=True)

# -----------------------------
# NEW CRUD ROUTES
# -----------------------------
@app.route("/add_employee", methods=["POST"])
def add_employee():
    name = request.form["name"]
    if not Employee.query.filter_by(name=name).first():
        db.session.add(Employee(name=name))
        db.session.commit()
    return redirect(url_for("admin"))

@app.route("/delete_employee/<int:id>", methods=["POST"])
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    db.session.delete(emp)
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/add_workplace", methods=["POST"])
def add_workplace():
    name = request.form["name"]
    if not Workplace.query.filter_by(name=name).first():
        db.session.add(Workplace(name=name))
        db.session.commit()
    return redirect(url_for("admin"))

@app.route("/delete_workplace/<int:id>", methods=["POST"])
def delete_workplace(id):
    wp = Workplace.query.get_or_404(id)
    db.session.delete(wp)
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/delete_log/<int:id>", methods=["POST"])
def delete_log(id):
    log = WorkLog.query.get_or_404(id)
    db.session.delete(log)
    db.session.commit()
    return redirect(url_for("admin"))

# -----------------------------
# RUN LOCAL
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
