from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Creating default Admin if not exists
        if not User.query.filter_by(role='Admin').first():
            admin = User(
                username='admin', 
                email='mswati9472@gmail.com', 
                password=generate_password_hash('admin123'), 
                role='Admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin User Created: admin / admin123")
    app.run(debug=True, port=5000)