from __future__ import annotations
import os
from datetime import datetime, date
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import pandas as pd


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Secret key for session/flash
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'dev-secret-change-me')

    # SQLite DB lives in instance folder (not tracked by git by default)
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'worklogs.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(app)

    class WorkLog(db.Model):
        __tablename__ = 'worklogs'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False, index=True)
        work_date = db.Column(db.Date, nullable=False, index=True)
        hours = db.Column(db.Float, nullable=False)
        description = db.Column(db.Text, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

        def __repr__(self):
            return f'<WorkLog {self.id} {self.name} {self.work_date}>'

    with app.app_context():
        db.create_all()

    # -------- Routes --------
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            name = (request.form.get('name') or '').strip()
            work_date_str = request.form.get('work_date') or ''
            hours_str = (request.form.get('hours') or '').strip()
            description = (request.form.get('description') or '').strip()

            # Basic validation
            errors = []
            if not name:
                errors.append('Name is required.')
            if not work_date_str:
                errors.append('Date is required.')
            else:
                try:
                    work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
                except ValueError:
                    errors.append('Date must be in YYYY-MM-DD format.')
                    work_date = None
            try:
                hours = float(hours_str)
                if hours < 0:
                    errors.append('Hours cannot be negative.')
            except ValueError:
                errors.append('Hours must be a number (e.g., 7.5).')
                hours = None
            if not description:
                errors.append('Description is required.')

            if errors:
                for e in errors:
                    flash(e, 'error')
                return render_template('index.html')

            entry = WorkLog(name=name, work_date=work_date, hours=hours, description=description)
            db.session.add(entry)
            db.session.commit()
            flash('Log saved. Thank you!', 'success')
            return redirect(url_for('index'))

        return render_template('index.html')

    @app.route('/admin')
    def admin():
        # Filters
        name = (request.args.get('name') or '').strip()
        start = request.args.get('start')
        end = request.args.get('end')

        q = WorkLog.query
        if name:
            q = q.filter(WorkLog.name.ilike(f'%{name}%'))
        if start:
            try:
                start_d = datetime.strptime(start, '%Y-%m-%d').date()
                q = q.filter(WorkLog.work_date >= start_d)
            except ValueError:
                flash('Start date invalid. Use YYYY-MM-DD.', 'error')
        if end:
            try:
                end_d = datetime.strptime(end, '%Y-%m-%d').date()
                q = q.filter(WorkLog.work_date <= end_d)
            except ValueError:
                flash('End date invalid. Use YYYY-MM-DD.', 'error')

        logs = q.order_by(WorkLog.work_date.desc(), WorkLog.created_at.desc()).all()

        # Totals (matching filters)
        total_hours = db.session.query(func.sum(WorkLog.hours))
        if name:
            total_hours = total_hours.filter(WorkLog.name.ilike(f'%{name}%'))
        if start:
            try:
                start_d = datetime.strptime(start, '%Y-%m-%d').date()
                total_hours = total_hours.filter(WorkLog.work_date >= start_d)
            except ValueError:
                pass
        if end:
            try:
                end_d = datetime.strptime(end, '%Y-%m-%d').date()
                total_hours = total_hours.filter(WorkLog.work_date <= end_d)
            except ValueError:
                pass
        total_hours = total_hours.scalar() or 0.0

        # Distinct names for quick filter chips
        names = [n for (n,) in db.session.query(WorkLog.name.distinct()).order_by(WorkLog.name.asc()).all()]

        return render_template('admin.html', logs=logs, total_hours=total_hours, names=names)

    @app.route('/export')
    def export():
        # same filters as admin
        name = (request.args.get('name') or '').strip()
        start = request.args.get('start')
        end = request.args.get('end')

        q = WorkLog.query
        if name:
            q = q.filter(WorkLog.name.ilike(f'%{name}%'))
        if start:
            try:
                start_d = datetime.strptime(start, '%Y-%m-%d').date()
                q = q.filter(WorkLog.work_date >= start_d)
            except ValueError:
                pass
        if end:
            try:
                end_d = datetime.strptime(end, '%Y-%m-%d').date()
                q = q.filter(WorkLog.work_date <= end_d)
            except ValueError:
                pass

        logs = q.order_by(WorkLog.work_date.asc(), WorkLog.created_at.asc()).all()

        # create DataFrame
        data = [
            {
                'Name': l.name,
                'Date': l.work_date.isoformat(),
                'Hours': l.hours,
                'Description': l.description,
                'Submitted At (UTC)': l.created_at.replace(tzinfo=None).isoformat(sep=' ', timespec='seconds'),
            }
            for l in logs
        ]
        df = pd.DataFrame(data)

        bio = BytesIO()
        with pd.ExcelWriter(bio, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Work Logs', index=False)
        bio.seek(0)

        filename = 'work_logs.xlsx'
        return send_file(
            bio,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    return app


app = create_app()
