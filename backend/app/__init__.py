from flask import Flask
from flask_cors import CORS
from celery import Celery
from flask_mail import Mail
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from .models import db
from celery.schedules import crontab
from datetime import timedelta
import os 

mail = Mail()
cache = Cache()
jwt = JWTManager()

# ─── DYNAMIC PRODUCTION REDIS FETCH ───
# Falls back to local localhost if REDIS_URL environment variable isn't configured on Render
redis_provider_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Initialize Celery with dynamic broker string
celery = Celery(__name__,
                broker=redis_provider_url,
                result_backend=redis_provider_url)

# BEAT SCHEDULE
celery.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'app.tasks.send_daily_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    'send-monthly-report': {
        'task': 'app.tasks.send_monthly_report',
        'schedule': crontab(hour=9, minute=0, day_of_month='1'),
    },
}
celery.conf.timezone = 'Asia/Kolkata'


def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ppa_v2.db') 
    app.config['SECRET_KEY'] = '756d6a85b79fd9faad3a2958f87191993c9fd181f0bcf04b'

    # JWT CONFIG
    app.config['JWT_SECRET_KEY'] = 'ppa-jwt-super-secret-key-2026'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)

    # Celery Config Linked to Dynamic Target
    app.config['broker_url'] = redis_provider_url
    app.config['result_backend'] = redis_provider_url

    # Mail Config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'mswati9472@gmail.com'
    app.config['MAIL_PASSWORD'] = 'qzeo wtsi qubn oyli'

    # ─── DYNAMIC CACHING STRATEGY FOR PRODUCTION ───
    # If REDIS_URL exists on Render, use RedisCache. Otherwise fallback safely to SimpleCache.
    if os.environ.get('REDIS_URL'):
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = redis_provider_url
    else:
        app.config['CACHE_TYPE'] = 'SimpleCache'
        
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300

    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    jwt.init_app(app)          

    # Tie the Flask config to Celery
    celery.conf.update(app.config)

    # Context wrapper so tasks can access the Database
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    from app.routes import main
    app.register_blueprint(main)

    return app