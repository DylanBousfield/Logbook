from __future__ import annotations
import os
from datetime import datetime, date
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import pandas as pd

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
        db.session.add(Employee(name="Dylan"))
    if Workplace.query.count() == 0:
        db.session.add(Workplace(name="Admin"))

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
# Add new employee
@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        name = request.form["name"]
        if name:
            new_emp = Employee(name=name)
            db.session.add(new_emp)
            db.session.commit()
            return redirect(url_for("admin"))
    return render_template("add_employee.html")

# Add new workplace
@app.route("/add_workplace", methods=["GET", "POST"])
def add_workplace():
    if request.method == "POST":
        name = request.form["name"]
        if name:
            new_wp = Workplace(name=name)
            db.session.add(new_wp)
            db.session.commit()
            return redirect(url_for("admin"))
    return render_template("add_workplace.html")

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
# RUN LOCAL
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
app = create_app()