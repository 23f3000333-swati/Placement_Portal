from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from app.models import db, User, CompanyDetails, PlacementDrive, Application
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from app import mail, cache
from flask_mail import Message
from flask_jwt_extended import create_access_token, jwt_required

main = Blueprint('main', __name__)
CORS(main)

# AUTH ROUTES----------------------------------

@main.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        if not user.is_active:
            return jsonify({"error": "Your account has been deactivated/blacklisted by Admin."}), 403

        if user.role == 'Company':
            company = CompanyDetails.query.filter_by(user_id=user.id).first()
            if not company or not company.is_approved:
                return jsonify({"error": "Your registration is pending Admin approval."}), 403

        additional_claims = {"role": user.role, "user_id": user.id, "username": user.username}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)

        return jsonify({
            "access_token": access_token,
            "role": user.role,
            "user_id": user.id,
            "username": user.username
        }), 200

    return jsonify({"error": "Invalid credentials"}), 401


@main.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])

    if data['role'] == 'Student':
        user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password,
            role='Student',
            cgpa=float(data['cgpa']) if data.get('cgpa') else None   # ← Save CGPA on register
        )
        db.session.add(user)

    elif data['role'] == 'Company':
        user = User(username=data['username'], email=data['email'], password=hashed_password, role='Company')
        db.session.add(user)
        db.session.flush()
        company = CompanyDetails(
            name=data['company_name'],
            description=data.get('description'),
            hr_contact=data.get('hr_contact'),
            website=data.get('website'),
            user_id=user.id
        )
        db.session.add(company)
    else:
        return jsonify({"error": "Invalid role"}), 400

    db.session.commit()
    cache.delete('admin_dashboard')
    return jsonify({"message": "User registered successfully"}), 201

# ADMIN ROUTES----------------------------------

@main.route('/api/admin/dashboard_data', methods=['GET'])
@jwt_required()
@cache.cached(timeout=300, key_prefix='admin_dashboard')
def get_admin_dashboard():
    stats = {
        "total_students": User.query.filter_by(role='Student').count(),
        "total_companies": User.query.filter_by(role='Company').count(),
        "total_drives": PlacementDrive.query.count()
    }
    students = User.query.filter_by(role='Student').all()
    companies = CompanyDetails.query.all()
    drives = PlacementDrive.query.all()

    return jsonify({
        "stats": stats,
        "students": [{"id": s.id, "username": s.username, "email": s.email, "is_active": s.is_active} for s in students],
        "companies": [
            {
                "id": c.id, "name": c.name, "is_approved": c.is_approved, "user_id": c.user_id,
                "is_active": User.query.get(c.user_id).is_active if User.query.get(c.user_id) else True
            } for c in companies
        ],
        "drives": [{"id": d.id, "title": d.title, "status": d.status, "is_approved": d.status == 'Approved'} for d in drives]
    })


@main.route('/api/admin/search', methods=['GET'])
@jwt_required()
def admin_search():
    q = request.args.get('q', '')
    role = request.args.get('role', 'Student')
    if not q:
        return jsonify([])

    if role == 'Drive':
        drives = PlacementDrive.query.filter(PlacementDrive.title.contains(q)).all()
        results = []
        for d in drives:
            company = CompanyDetails.query.get(d.company_id)
            results.append({
                "id": d.id, "title": d.title, "status": d.status,
                "is_approved": d.status == 'Approved',
                "company_name": company.name if company else "Unknown"
            })
        return jsonify(results)

    users = User.query.filter(
        or_(User.username.contains(q), User.email.contains(q))
    ).filter(User.role == role).all()

    results = []
    for u in users:
        data = {"id": u.id, "username": u.username, "role": u.role, "email": u.email, "is_active": u.is_active}
        if u.role == 'Company':
            company = CompanyDetails.query.filter_by(user_id=u.id).first()
            if company:
                data["company_id"] = company.id
                data["company_name"] = company.name
                data["is_approved"] = company.is_approved
        results.append(data)
    return jsonify(results)


@main.route('/api/admin/toggle_user_status/<int:user_id>', methods=['POST'])
@jwt_required()
def toggle_user_status(user_id):
    user = User.query.get(user_id)
    if user and user.role != 'Admin':
        user.is_active = not user.is_active
        db.session.commit()
        cache.delete('admin_dashboard')
        return jsonify({"message": "User status updated"})
    return jsonify({"error": "Action denied"}), 400


@main.route('/api/admin/approve_company/<int:comp_id>', methods=['POST'])
@jwt_required()
def approve_company(comp_id):
    company = CompanyDetails.query.get(comp_id)
    if company:
        company.is_approved = True
        db.session.commit()
        cache.delete('admin_dashboard')
        return jsonify({"message": "Company Registration Approved"})
    return jsonify({"error": "Company not found"}), 404


@main.route('/api/admin/reject_company/<int:comp_id>', methods=['POST'])
@jwt_required()
def reject_company(comp_id):
    company = CompanyDetails.query.get(comp_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    user = User.query.get(company.user_id)
    db.session.delete(company)
    if user:
        db.session.delete(user)
    db.session.commit()
    cache.delete('admin_dashboard')
    return jsonify({"message": "Company rejected and removed"})


@main.route('/api/admin/approve_drive/<int:drive_id>', methods=['POST'])
@jwt_required()
def approve_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found"}), 404
    drive.status = 'Approved'
    db.session.commit()
    cache.delete('admin_dashboard')
    cache.delete_many(*[f'student_drives_{u.id}' for u in User.query.filter_by(role='Student').all()])
    return jsonify({"message": "Drive approved successfully"}), 200


@main.route('/api/admin/reject_drive/<int:drive_id>', methods=['POST'])
@jwt_required()
def reject_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found"}), 404
    drive.status = 'Rejected'
    db.session.commit()
    cache.delete('admin_dashboard')
    cache.delete_many(*[f'student_drives_{u.id}' for u in User.query.filter_by(role='Student').all()])
    return jsonify({"message": "Drive rejected successfully"})


@main.route('/api/admin/all_applications', methods=['GET'])
@jwt_required()
def get_all_applications():
    apps = Application.query.all()
    output = []
    for a in apps:
        student = User.query.get(a.student_id)
        drive = PlacementDrive.query.get(a.placement_drive_id)
        company = CompanyDetails.query.get(drive.company_id) if drive else None
        output.append({
            "id": a.id,
            "student_name": student.username if student else "Unknown",
            "drive_title": drive.title if drive else "Unknown",
            "company_name": company.name if company else "Unknown",
            "status": a.status
        })
    return jsonify(output)

# COMPANY ROUTES----------------------------------

@main.route('/api/company/dashboard/<int:user_id>', methods=['GET'])
@jwt_required()
def get_company_dashboard(user_id):
    cache_key = f'company_dashboard_{user_id}'
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)

    company = CompanyDetails.query.filter_by(user_id=user_id).first()
    if not company:
        return jsonify({"error": "Company not found"}), 404

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    drive_list = []
    for d in drives:
        drive_list.append({
            "id": d.id,
            "title": d.title,
            "date": str(d.date),
            "deadline": str(d.deadline) if d.deadline else None,
            "eligibility": d.eligibility_criteria,   # float or None
            "status": d.status,
            "is_approved": d.status == 'Approved',
            "applicant_count": len(d.applications)
        })

    result = {"details": {"name": company.name, "description": company.description}, "drives": drive_list}
    cache.set(cache_key, result, timeout=120)
    return jsonify(result)


@main.route('/api/company/create_drive', methods=['POST'])
@jwt_required()
def create_placement_drive():
    data = request.get_json()
    user_id = data.get('user_id')

    company = CompanyDetails.query.filter_by(user_id=user_id).first()
    if not company:
        return jsonify({"error": "Company profile not found for this user"}), 404
    if not company.is_approved:
        return jsonify({"error": "Your company is not yet approved by Admin. You cannot post drives."}), 403

    try:
        # eligibility is stored as a float (min CGPA) or None if left blank
        raw_eligibility = data.get('eligibility')
        min_cgpa = float(raw_eligibility) if raw_eligibility else None

        new_drive = PlacementDrive(
            company_id=company.id,
            title=data.get('title'),
            description=data.get('description'),
            eligibility_criteria=min_cgpa,            
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            deadline=datetime.strptime(data.get('deadline'), '%Y-%m-%d').date(),
            status='Pending'
        )
        db.session.add(new_drive)
        db.session.commit()
        cache.delete(f'company_dashboard_{user_id}')
        cache.delete('admin_dashboard')
        return jsonify({"message": "Drive created successfully!"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route('/api/company/applications/<int:drive_id>', methods=['GET'])
@jwt_required()
def get_drive_applications(drive_id):
    apps = Application.query.filter_by(placement_drive_id=drive_id).all()
    results = []
    for a in apps:
        student = User.query.get(a.student_id)
        results.append({
            "app_id": a.id,
            "student_name": student.username if student else "Unknown",
            "student_email": student.email if student else "Unknown",
            "status": a.status,
            "interview_date": str(a.interview_date) if a.interview_date else None,
            "interview_notes": a.interview_notes or "",
            "cgpa": student.cgpa if student else None,
            "resume": student.resume if student else None

        })
    return jsonify(results)


@main.route('/api/company/update_status', methods=['POST'])
@jwt_required()
def update_app_status():
    data = request.get_json()
    app = Application.query.get(data['app_id'])
    if not app:
        return jsonify({"error": "Application not found"}), 404
    app.status = data['status']
    db.session.commit()
    return jsonify({"message": f"Status updated to {data['status']}"})


@main.route('/api/company/schedule_interview', methods=['POST'])
@jwt_required()
def schedule_interview():
    data = request.get_json()
    app = Application.query.get(data['app_id'])
    if not app:
        return jsonify({"error": "Application not found"}), 404
    try:
        app.interview_date = datetime.strptime(data['interview_date'], '%Y-%m-%d').date() if data.get('interview_date') else None
        app.interview_notes = data.get('interview_notes', '')
        db.session.commit()
        return jsonify({"message": "Interview scheduled successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# STUDENT ROUTES ----------------------------------

@main.route('/api/student/dashboard/<int:user_id>', methods=['GET'])
@jwt_required()
def get_student_dashboard(user_id):
    cache_key = f'student_drives_{user_id}'
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)

    student = User.query.get(user_id)
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    applied_drive_ids = [a.placement_drive_id for a in Application.query.filter_by(student_id=user_id).all()]

    drive_list = []
    for d in drives:
        # SKIP DRIVES FROM BLACKLISTED COMPANIES
        company = d.company
        if not company:
            continue
        company_user = User.query.get(company.user_id)
        if not company_user or not company_user.is_active:
            continue

        # CGPA ELIGIBILITY CHECK 
        min_cgpa = d.eligibility_criteria   
        student_cgpa = student.cgpa        

        if min_cgpa is None:
            # No requirement — open to all
            is_eligible = True
            ineligibility_reason = None
        elif student_cgpa is None:
            # Student hasn't set CGPA yet
            is_eligible = False
            ineligibility_reason = f"This drive requires CGPA >= {min_cgpa}. Please update your CGPA in profile."
        elif student_cgpa >= min_cgpa:
            is_eligible = True
            ineligibility_reason = None
        else:
            is_eligible = False
            ineligibility_reason = f"Requires CGPA >= {min_cgpa}. Your CGPA is {student_cgpa}."

        drive_list.append({
            "id": d.id,
            "title": d.title,
            "company_name": d.company.name if d.company else "Unknown Company",
            "date": str(d.date),
            "deadline": str(d.deadline) if d.deadline else None,
            "eligibility": min_cgpa,             
            "status": d.status,
            "has_applied": d.id in applied_drive_ids,
            "is_eligible": is_eligible,           
            "ineligibility_reason": ineligibility_reason  
        })

    cache.set(cache_key, drive_list, timeout=120)
    return jsonify(drive_list)


@main.route('/api/student/profile/<int:user_id>', methods=['GET'])
@jwt_required()
def get_student_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "email": user.email,
        "resume": user.resume,
        "username": user.username,
        "cgpa": user.cgpa   
    })


@main.route('/api/student/history/<int:user_id>', methods=['GET'])
@jwt_required()
def get_student_history(user_id):
    apps = Application.query.filter_by(student_id=user_id).all()
    history = []
    for a in apps:
        drive = PlacementDrive.query.get(a.placement_drive_id)
        company = CompanyDetails.query.get(drive.company_id) if drive else None
        history.append({
            "drive_title": drive.title if drive else "Unknown",
            "company_name": company.name if company else "Unknown",
            "application_date": str(a.application_date),
            "status": a.status,
            "interview_date": str(a.interview_date) if a.interview_date else None,
            "interview_notes": a.interview_notes or ""
        })
    return jsonify(history)


@main.route('/api/student/apply', methods=['POST'])
@jwt_required()
def apply_for_drive():
    data = request.get_json()

    student = User.query.get(data['user_id'])
    drive = PlacementDrive.query.get(data['drive_id'])

    if not student or not drive:
        return jsonify({"error": "Invalid student or drive"}), 404

    # CGPA ELIGIBILITY CHECK ON BACKEND
    min_cgpa = drive.eligibility_criteria
    if min_cgpa is not None:
        student_cgpa = student.cgpa if student.cgpa is not None else 0.0
        if student_cgpa < min_cgpa:
            return jsonify({
                "error": f"Not eligible. This drive requires CGPA >= {min_cgpa}. Your CGPA is {student_cgpa}."
            }), 403

    # Duplicate check
    exists = Application.query.filter_by(
        student_id=data['user_id'],
        placement_drive_id=data['drive_id']
    ).first()
    if exists:
        return jsonify({"error": "Already applied!"}), 400

    new_app = Application(student_id=data['user_id'], placement_drive_id=data['drive_id'])
    db.session.add(new_app)
    db.session.commit()
    cache.delete(f'student_drives_{data["user_id"]}')
    return jsonify({"message": "Application successful!"})


@main.route('/api/student/update_profile', methods=['POST'])
@jwt_required()
def update_profile():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if 'resume' in request.files:
        file = request.files['resume']
        filename = secure_filename(f"user_{user_id}_{file.filename}")
        upload_path = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file.save(os.path.join(upload_path, filename))
        user.resume = filename

    user.email = request.form.get('email', user.email)

    # Update CGPA from profile form if provided
    new_cgpa = request.form.get('cgpa')
    if new_cgpa:
        user.cgpa = float(new_cgpa)

    db.session.commit()
    # Clear student drives cache so eligibility re-evaluates immediately
    cache.delete(f'student_drives_{user_id}')
    return jsonify({"message": "Profile Updated!"})


# ASYNC / BATCH JOB ROUTES ------------------------------

@main.route('/api/student/export-history', methods=['POST'])
@jwt_required()
def trigger_export():
    from .tasks import export_applications_csv
    data = request.get_json(silent=True) or {}
    email = data.get('email')

    if not email:
        return jsonify({"message": "Email is required"}), 400

    student = User.query.filter_by(email=email).first()
    if not student:
        return jsonify({"message": "User not found for this email"}), 404

    export_applications_csv.delay(student.email)
    return jsonify({"message": "Batch job started! You will receive an email once done."}), 202

@main.route('/init-db', methods=['GET'])
def init_db():
    try:
        from app.models import db, User
        from werkzeug.security import generate_password_hash
        
        db.create_all()
        
        if not User.query.filter_by(role='Admin').first():
            admin = User(
                username='admin',
                email='mswati9472@gmail.com',
                password=generate_password_hash('admin123'),
                role='Admin'
            )
            db.session.add(admin)
            db.session.commit()
        return {"status": "success", "message": "Tables initialized successfully!"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500