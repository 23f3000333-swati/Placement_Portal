import csv
import os
from datetime import date, timedelta
from app import celery, mail
from flask_mail import Message

# JOB 1: CSV Export (User Triggered Async) --------------------------

@celery.task
def export_applications_csv(student_email):
    from app import create_app, db
    from app.models import User, Application, PlacementDrive, CompanyDetails

    app = create_app()
    with app.app_context():
        # 1. Find the Student
        user = User.query.filter_by(email=student_email).first()
        if not user:
            return "Error: Student not found"

        # 2. Get all applications for this student
        apps = Application.query.filter_by(student_id=user.id).all()

        # 3. Setup File Path
        filename = f"history_{user.id}.csv"
        export_path = os.path.join(app.root_path, 'static', 'exports')
        os.makedirs(export_path, exist_ok=True)
        file_full_path = os.path.join(export_path, filename)

        # 4. Write CSV
        with open(file_full_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Student ID', 'Company Name', 'Drive Title', 'Application Status', 'Applied On'])

            for a in apps:
                drive = PlacementDrive.query.get(a.placement_drive_id)
                company = CompanyDetails.query.get(drive.company_id) if drive else None

                writer.writerow([
                    user.id,
                    company.name if company else "N/A",
                    drive.title if drive else "N/A",
                    a.status,
                    str(a.application_date)
                ])

        # 5. Send Email Alert
        download_url = f"http://127.0.0.1:5000/static/exports/{filename}"
        msg = Message(
            subject="Your Application Export is Ready",
            sender=app.config.get('MAIL_USERNAME'),
            recipients=[user.email]
        )
        msg.body = f"Hi {user.username},\n\nYour placement application history export is ready!\n\nDownload it here: {download_url}\n\nRegards,\nPlacement Portal"

        try:
            mail.send(msg)
            return f"Success: Exported {len(apps)} applications"
        except Exception as e:
            return f"File created but mail failed: {str(e)}"


# JOB 2A: Daily Deadline Reminder (Scheduled) | Runs every day at 8:00 AM ---------------------------------------

@celery.task
def send_daily_reminders():
    from app import create_app, db
    from app.models import User, PlacementDrive, CompanyDetails

    app = create_app()
    with app.app_context():
        today = date.today()
        upcoming_deadline = today + timedelta(days=3)

        # Get all approved drives with deadline within next 3 days
        drives = PlacementDrive.query.filter(
            PlacementDrive.status == 'Approved',
            PlacementDrive.deadline >= today,
            PlacementDrive.deadline <= upcoming_deadline
        ).all()

        if not drives:
            return "No upcoming deadlines found today"

        # Get ALL active students only (never Admin or Company)
        students = User.query.filter_by(role='Student', is_active=True).all()

        if not students:
            return "No active students found"

        # drive lines for email body
        drive_lines = ""
        for d in drives:
            company = CompanyDetails.query.get(d.company_id)
            company_name = company.name if company else "Unknown Company"
            drive_lines += f"\n  - {d.title} at {company_name} | Deadline: {d.deadline}"

        # For reminder to EVERY active student
        emails_sent = 0
        for student in students:
            msg = Message(
                subject="⏰ Placement Drive Deadline Reminder",
                sender=app.config.get('MAIL_USERNAME'),
                recipients=[student.email]  
            )
            msg.body = f"""Hi {student.username},

This is a reminder that the following placement drives have deadlines coming up in the next 3 days:
{drive_lines}

Please log in to the Placement Portal and apply before the deadline!

Portal: http://localhost:5173/student-dash

Regards,
Placement Cell"""

            try:
                mail.send(msg)
                emails_sent += 1
            except Exception as e:
                print(f"Failed to send reminder to {student.email}: {str(e)}")
                continue

        return f"Daily reminders sent to {emails_sent} students"


# JOB 2B: Monthly Activity Report (Scheduled) | Runs on 1st of every month at 9:00 AM

@celery.task
def send_monthly_report():
    from app import create_app, db
    from app.models import User, PlacementDrive, Application, CompanyDetails
    from datetime import datetime

    app = create_app()
    with app.app_context():
        # Find Admin user only
        admin = User.query.filter_by(role='Admin').first()
        if not admin:
            return "Error: No admin found"

        # Get stats for the CURRENT month
        today = date.today()
        first_day_this_month = today.replace(day=1)
        last_day_this_month = today  # up to today

        month_name = today.strftime("%B %Y")

        # Count drives conducted this month
        drives_this_month = PlacementDrive.query.filter(
            PlacementDrive.date >= first_day_this_month,
            PlacementDrive.date <= last_day_this_month
        ).all()

        total_drives = len(drives_this_month)
        total_applied = 0
        total_selected = 0
        drive_rows = ""

        for drive in drives_this_month:
            company = CompanyDetails.query.get(drive.company_id)
            company_name = company.name if company else "Unknown"
            apps = Application.query.filter_by(placement_drive_id=drive.id).all()
            applied_count = len(apps)
            selected_count = len([a for a in apps if a.status == 'Selected'])
            total_applied += applied_count
            total_selected += selected_count

            drive_rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{drive.title}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{company_name}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{str(drive.date)}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align:center;">{applied_count}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align:center;">{selected_count}</td>
            </tr>"""

        total_students = User.query.filter_by(role='Student').count()
        total_companies = User.query.filter_by(role='Company').count()

        # Build HTML Report
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; padding: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #3498db; }}
                .stats-box {{
                    display: inline-block;
                    background: #f0f4f8;
                    border-left: 4px solid #3498db;
                    padding: 15px 25px;
                    margin: 10px;
                    border-radius: 4px;
                    min-width: 150px;
                }}
                .stats-box h3 {{ margin: 0; font-size: 32px; color: #2c3e50; }}
                .stats-box p {{ margin: 5px 0 0; font-size: 13px; color: #7f8c8d; text-transform: uppercase; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                thead {{ background-color: #3498db; color: white; }}
                thead th {{ padding: 12px; text-align: left; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #aaa; border-top: 1px solid #eee; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>📊 Monthly Placement Activity Report</h1>
            <p>Report for: <strong>{month_name}</strong></p>
            <p>Generated on: <strong>{today.strftime("%d %B %Y")}</strong></p>

            <h2>Overview</h2>
            <div>
                <div class="stats-box">
                    <h3>{total_drives}</h3>
                    <p>Drives Conducted</p>
                </div>
                <div class="stats-box">
                    <h3>{total_applied}</h3>
                    <p>Students Applied</p>
                </div>
                <div class="stats-box">
                    <h3>{total_selected}</h3>
                    <p>Students Selected</p>
                </div>
                <div class="stats-box">
                    <h3>{total_students}</h3>
                    <p>Total Students</p>
                </div>
                <div class="stats-box">
                    <h3>{total_companies}</h3>
                    <p>Total Companies</p>
                </div>
            </div>

            <h2>Drive-wise Breakdown</h2>
            {"<p>No drives were conducted this month.</p>" if total_drives == 0 else f'''
            <table>
                <thead>
                    <tr>
                        <th>Drive Title</th>
                        <th>Company</th>
                        <th>Date</th>
                        <th>Applied</th>
                        <th>Selected</th>
                    </tr>
                </thead>
                <tbody>
                    {drive_rows}
                </tbody>
            </table>'''}

            <div class="footer">
                <p>This report was automatically generated by the Placement Portal System.</p>
                <p>Do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        # Send to Admin ONLY
        msg = Message(
            subject=f"📊 Monthly Placement Report — {month_name}",
            sender=app.config.get('MAIL_USERNAME'),
            recipients=[admin.email] 
        )
        msg.html = html_report

        try:
            mail.send(msg)
            return f"Monthly report for {month_name} sent to {admin.email}"
        except Exception as e:
            return f"Report generation failed: {str(e)}"