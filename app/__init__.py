import os
from flask import Flask
from werkzeug.security import generate_password_hash
from app.models import db, Admin, specialization

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
    app.config['SECRET_KEY'] = 'secret_key81708730'

    db.init_app(app)

    with app.app_context():
        db.create_all()
        hardcoded_username = "admin"
        hardcoded_password = "admin123"

        admin = Admin.query.filter_by(username=hardcoded_username).first()

        if not admin:
            admin = Admin(username=hardcoded_username,password=generate_password_hash(hardcoded_password))
            db.session.add(admin)
            db.session.commit()
        
        default_specializations = [
            ("Cardiology", "Heart and blood vessel related treatments."),
            ("Neurology", "Brain, spinal cord, and nervous system disorders."),
            ("Orthopedics", "Bones, joints, muscles, and skeletal issues."),
            ("Dermatology", "Skin, hair, and nail conditions."),
            ("Pediatrics", "Healthcare for infants, children, and teenagers."),
            ("Gynecology", "Women's reproductive health and pregnancy."),
            ("Ophthalmology", "Eye and vision-related care."),
            ("Psychiatry", "Mental health, emotional, and behavioral disorders."),
            ("ENT", "Ear, nose, and throat related conditions."),
            ("General Medicine", "Primary medical care for adults.")
        ]

        for name, about in default_specializations:
            exists = specialization.query.filter_by(name=name).first()
            if not exists:
                spec = specialization(name=name, about=about)
                db.session.add(spec)

        db.session.commit()


    return app
