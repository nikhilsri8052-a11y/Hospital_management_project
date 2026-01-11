from flask import render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time, timedelta
from sqlalchemy import or_
from app.models import db, Enquiry, Admin, specialization, Doctor, blacklist, Patient, PatientHistory, DoctorSlot, Appointment, BlacklistedPatient

def init_routes(app):
    @app.route('/')
    @app.route('/home')
    def home():
        return render_template('home.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/privacy')
    def privacy_policy():
        return render_template('privacy_policy.html')

    @app.route('/terms')
    def terms_conditions():
        return render_template('terms_of_services.html')

    @app.route('/enquiry')
    def enquiry():
        return render_template('Enquiry.html')

    @app.route('/submit_contact', methods=['POST'])
    def submit_contact():
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        new_enquiry = Enquiry(name=name, email=email, message=message)
        db.session.add(new_enquiry)
        db.session.commit()
        return redirect(url_for('enquiry'))

    @app.route('/delete_enquiry/<int:enquiry_id>', methods=['POST'])
    def delete_enquiry(enquiry_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        enquiry = Enquiry.query.get_or_404(enquiry_id)
        db.session.delete(enquiry)
        db.session.commit()
        return redirect(url_for('view_enquiries'))

    @app.route('/view_enquiries')
    def view_enquiries():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        enquiries = Enquiry.query.all()
        return render_template('view_enquiries.html', enquiries=enquiries)

    @app.route('/admin_login')
    def admin_login():
        return render_template('admin_login.html')

    @app.route('/submit-admin-login', methods=['POST', 'GET'])
    def submit_admin_login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            admin = Admin.query.filter_by(username=username).first()
            if admin and check_password_hash(admin.password, password):
                session['admin_id'] = admin.id
                session['admin_username'] = admin.username
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('admin_login.html', error="Invalid credentials")
        else:
            return redirect(url_for('admin_login'))

    @app.route('/logout')
    def logout():
        if 'admin_id' in session:
            session.pop('admin_id', None)
            session.pop('admin_username', None)
            return redirect(url_for('home'))
        elif 'doctor_id' in session:
            session.pop('doctor_id', None)
            session.pop('doctor_username', None)
            return redirect(url_for('home'))
        elif 'patient_id' in session:
            session.pop('patient_id', None)
            session.pop('patient_name', None)
            return redirect(url_for('home'))
        return redirect(url_for('home'))

    @app.route('/admin_dashboard')
    def admin_dashboard():
        if 'admin_id' in session:
            return render_template('admin.html')
        else:
            return redirect(url_for('admin_login'))

    @app.route('/manage_doctors')
    def manage_doctors():
        if 'admin_id' in session:
            doctors = Doctor.query.all()
            specializations = specialization.query.all()
            return render_template('manage_doctors.html', doctors=doctors, spec_list=specializations)
        else:
            return redirect(url_for('admin_login'))

    @app.route('/add_doctor', methods=['GET', 'POST'])
    def add_doctor():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        specializations = specialization.query.all()
        if request.method == 'POST':
            name = request.form['name']
            specialization_id = request.form['specialization_id']
            email = request.form['email']
            username = request.form['username']
            password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
            experience = request.form['experience']
            education = request.form['education']
            blacklisted = blacklist.query.filter_by(email=email).first()
            if blacklisted:
                error = "This doctor is blacklisted. Reason: " + blacklisted.reason
                return render_template('new_doc.html', specializations=specializations, error=error)
            email_taken = Doctor.query.filter_by(email=email).first()
            if email_taken:
                error = "A doctor with this email already exists."
                return render_template('new_doc.html', specializations=specializations, error=error)
            username_taken = Doctor.query.filter_by(username=username).first()
            if username_taken:
                error = "Username already exists. Choose a different username."
                return render_template('new_doc.html', specializations=specializations, error=error)
            new_doctor = Doctor(name=name, specialization_id=specialization_id, email=email, username=username, password=password, experience=experience, education=education)
            db.session.add(new_doctor)
            db.session.commit()
            return redirect(url_for('manage_doctors'))
        return render_template('new_doc.html', specializations=specializations)

    @app.route('/edit_doctor/<int:doctor_id>', methods=['GET'])
    def edit_doctor(doctor_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        doctor = Doctor.query.get_or_404(doctor_id)
        specializations = specialization.query.all()
        return render_template('edit_doc.html', doctor=doctor, specializations=specializations)

    @app.route('/edit_doctor/<int:doctor_id>', methods=['POST'])
    def update_doctor(doctor_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        doctor = Doctor.query.get_or_404(doctor_id)
        doctor.name = request.form['name']
        doctor.specialization_id = request.form['specialization_id']
        doctor.email = request.form['email']
        doctor.experience = request.form['experience']
        doctor.education = request.form['education']
        db.session.commit()
        return redirect(url_for('manage_doctors'))

    @app.route('/remove_doctor/<int:doctor_id>', methods=['POST'])
    def remove_doctor(doctor_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        doctor = Doctor.query.get_or_404(doctor_id)
        db.session.delete(doctor)
        db.session.commit()
        return redirect(url_for('manage_doctors'))

    @app.route('/blacklist_doctor/<int:doctor_id>', methods=['POST'])
    def blacklist_doctor(doctor_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        doctor = Doctor.query.get_or_404(doctor_id)
        doctor.blacklisted = True
        existing_blacklist_entry = blacklist.query.filter_by(email=doctor.email).first()
        if not existing_blacklist_entry:
            entry = blacklist(email=doctor.email, reason="Admin blacklisted this doctor manually.")
            db.session.add(entry)
        db.session.commit()
        return redirect(url_for('manage_doctors'))

    @app.route('/blacklist_patient/<int:patient_id>', methods=['POST'])
    def blacklist_patient(patient_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        patient = Patient.query.get_or_404(patient_id)
        new_entry = BlacklistedPatient(name=patient.name, email=patient.email, phone=patient.phone, reason="Admin blacklisted this patient manually.")
        db.session.add(new_entry)
        db.session.delete(patient)
        db.session.commit()
        flash("Patient blacklisted successfully. All patient data including appointments and medical history has been deleted.", "success")
        return redirect(url_for('admin_patient'))

    @app.route('/revoke_patient_blacklist/<int:bid>', methods=['POST'])
    def revoke_patient_blacklist(bid):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        bl_patient = BlacklistedPatient.query.get_or_404(bid)
        db.session.delete(bl_patient)
        db.session.commit()
        flash("Blacklist revoked. Patient can register again with the same email.", "success")
        return redirect(url_for('blacklisted_doctors'))

    @app.route('/blacklisted_doctors')
    def blacklisted_doctors():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        search_patient = request.args.get('search_patient', '').strip()
        search_doctor = request.args.get('search_doctor', '').strip()
        if search_patient:
            bp = BlacklistedPatient.query.filter(BlacklistedPatient.name.ilike(f'%{search_patient}%')).all()
        else:
            bp = BlacklistedPatient.query.all()
        doctor_query = (db.session.query(Doctor, blacklist.reason.label("reason"), blacklist.date_blacklisted.label("date_blacklisted")).join(blacklist, Doctor.email == blacklist.email).filter(Doctor.blacklisted == True))
        if search_doctor:
            doctor_query = doctor_query.filter(Doctor.name.ilike(f'%{search_doctor}%'))
        blacklisted_info = doctor_query.all()
        return render_template('blacklist.html', blacklisted_info=blacklisted_info, bp=bp)

    @app.route('/revoke_blacklist/<int:doctor_id>', methods=['POST'])
    def revoke_blacklist(doctor_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        doctor = Doctor.query.get_or_404(doctor_id)
        doctor.blacklisted = False
        blacklist_entry = blacklist.query.filter_by(email=doctor.email).first()
        if blacklist_entry:
            db.session.delete(blacklist_entry)
        db.session.commit()
        return redirect(url_for('blacklisted_doctors'))

    @app.route('/Services')
    def services():
        all_specializations = specialization.query.all()
        return render_template('services.html', specializations=all_specializations)

    @app.route('/OurDoctor', methods=['GET'])
    def our_doctors():
        query = request.args.get('search')
        selected_spec = request.args.get('specialization_id')
        doctors_query = Doctor.query.filter(Doctor.blacklisted == False)
        if query:
            query_like = f"%{query.lower()}%"
            doctors_query = doctors_query.join(specialization, Doctor.specialization_id == specialization.id).filter(or_(db.func.lower(Doctor.name).like(query_like), db.func.lower(specialization.name).like(query_like)))
        if selected_spec and selected_spec.isdigit():
            doctors_query = doctors_query.filter(Doctor.specialization_id == int(selected_spec))
        doctors = doctors_query.all()
        specializations = specialization.query.all()
        return render_template('doctor.html', doctors=doctors, specializations=specializations, search_query=query, selected_spec=selected_spec)

    @app.route('/department/<int:specialization_id>')
    def department(specialization_id):
        spec = specialization.query.get_or_404(specialization_id)
        doctors = Doctor.query.filter_by(specialization_id=specialization_id, blacklisted=False).all()
        return render_template('department.html', spec=spec, doctors=doctors)

    @app.route('/manage_doctors_page', methods=['GET'])
    def manage_doctors_page():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        search_id = request.args.get('search_id', '').strip()
        search_name = request.args.get('search', '').strip()
        spec_id = request.args.get('specialization_id', '').strip()
        query = Doctor.query
        if search_id.isdigit():
            query = query.filter(Doctor.id == int(search_id))
        if search_name:
            query = query.filter(Doctor.name.ilike(f"%{search_name}%"))
        if spec_id and spec_id.isdigit():
            query = query.filter(Doctor.specialization_id == int(spec_id))
        doctors = query.all()
        specializations = specialization.query.all()
        return render_template('manage_doctors.html', doctors=doctors, spec_list=specializations, selected_spec=spec_id, search_name=search_name, search_id=search_id)

    @app.route('/doctor_login')
    def doctor_login():
        return render_template('doctor_login.html')

    @app.route('/submit-doctor-login', methods=['POST'])
    def submit_doctor_login():
        username = request.form['username']
        password = request.form['password']
        doctor = Doctor.query.filter_by(username=username).first()
        if doctor and check_password_hash(doctor.password, password):
            if doctor.blacklisted:
                return render_template('doctor_login.html', error='Your account has been suspended. Please contact Admin.')
            session['doctor_id'] = doctor.id
            session['doctor_username'] = doctor.username
            return redirect(url_for('doctor_dashboard'))
        else:
            return render_template('doctor_login.html', error='Invalid credentials')

    @app.route('/doctor_dashboard')
    def doctor_dashboard():
        if 'doctor_id' in session:
            doctor = Doctor.query.get(session['doctor_id'])
            return render_template('doctor_dashboard.html', doctor=doctor)
        else:
            return redirect(url_for('doctor_login'))

    @app.route('/register')
    def register():
        return render_template('register.html')

    @app.route('/submit-registration', methods=['POST'])
    def submit_registration():
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        age = request.form['age']
        gender = request.form['gender']
        dob = request.form.get('dob')
        address = request.form.get('address')
        blood_group = request.form.get('blood_group')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        password = request.form['password']
        existing_user = Patient.query.filter_by(email=email).first()
        bl = BlacklistedPatient.query.filter_by(email=email).first()
        if bl:
            flash("This email has been blacklisted. Registration denied.", "error")
            return redirect(url_for('register'))
        if existing_user:
            flash('Email already exists!', 'error')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        dob_date = None
        if dob:
            try:
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                pass
        new_patient = Patient(name=name, email=email, phone=phone, age=int(age), gender=gender, dob=dob_date, address=address, blood_group=blood_group, emergency_contact_name=emergency_contact_name, emergency_contact_phone=emergency_contact_phone, password=hashed_password)
        try:
            db.session.add(new_patient)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('patient_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('register'))

    @app.route('/patient_login')
    def patient_login():
        return render_template('login.html')

    @app.route('/submit-patient-login', methods=['POST'])
    def submit_patient_login():
        email = request.form['email']
        password = request.form['password']
        patient = Patient.query.filter_by(email=email).first()
        if patient and check_password_hash(patient.password, password):
            session['patient_id'] = patient.id
            session['patient_name'] = patient.name
            return redirect(url_for('patient_dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')

    @app.route('/patient_dashboard')
    def patient_dashboard():
        if 'patient_id' in session:
            patient = Patient.query.get(session['patient_id'])
            history = PatientHistory.query.filter_by(patient_id=patient.id).order_by(PatientHistory.date_recorded.desc()).all()
            return render_template('patient_dashboard.html', patient=patient, history=history)
        else:
            return redirect(url_for('patient_login'))

    @app.route('/login')
    def login():
        return render_template('login.html')

    @app.route('/book_appointment/<int:doctor_id>',methods=['GET','POST'])
    def show_book_appointment(doctor_id):
        if 'patient_id' not in session:
            flash('Please login to book an appointment','error');return redirect(url_for('register'))
        doctor=Doctor.query.get_or_404(doctor_id)
        today=date.today()
        available_dates=[today+timedelta(days=i) for i in range(7)]
        schedule=[]
        for d in available_dates:
            morning_slot=DoctorSlot.query.filter_by(doctor_id=doctor.id,date=d,slot_name='Morning').first()
            evening_slot=DoctorSlot.query.filter_by(doctor_id=doctor.id,date=d,slot_name='Evening').first()
            modified=False
            if not morning_slot:
                morning_slot=DoctorSlot(doctor_id=doctor.id,date=d,slot_name='Morning',start_time=time(8,0),end_time=time(12,0),max_patients=5,current_patients=0,status='Available');db.session.add(morning_slot);modified=True
            if not evening_slot:
                evening_slot=DoctorSlot(doctor_id=doctor.id,date=d,slot_name='Evening',start_time=time(18,0),end_time=time(21,0),max_patients=5,current_patients=0,status='Available');db.session.add(evening_slot);modified=True
            if modified:db.session.commit()
            morning_status='Full' if (morning_slot.status=='Available' and morning_slot.current_patients>=morning_slot.max_patients) else morning_slot.status
            evening_status='Full' if (evening_slot.status=='Available' and evening_slot.current_patients>=evening_slot.max_patients) else evening_slot.status
            if morning_slot.status!=morning_status:morning_slot.status=morning_status;db.session.commit()
            if evening_slot.status!=evening_status:evening_slot.status=evening_status;db.session.commit()
            schedule.append({'date':d,'Morning':{'status':morning_status,'start_time':morning_slot.start_time,'end_time':morning_slot.end_time,'slot_id':morning_slot.id},'Evening':{'status':evening_status,'start_time':evening_slot.start_time,'end_time':evening_slot.end_time,'slot_id':evening_slot.id}})
        if request.method=='POST':
            selected_slot_id=request.form['slot_id']
            slot=DoctorSlot.query.get_or_404(selected_slot_id)
            if slot.status!='Available':flash('This time slot is no longer available','error');return redirect(url_for('show_book_appointment',doctor_id=doctor_id))
            if slot.current_patients>=slot.max_patients:flash('This time slot is fully booked','error');return redirect(url_for('show_book_appointment',doctor_id=doctor_id))
            repeat=Appointment.query.filter_by(patient_id=session['patient_id'],doctor_id=doctor.id,appointment_date=slot.date,appointment_time=slot.start_time).first()
            if repeat:
                flash('You already booked this doctor at the same time!','error')
                return redirect(url_for('show_book_appointment',doctor_id=doctor_id))
            existing_appointment=Appointment.query.filter_by(patient_id=session['patient_id'],slot_id=selected_slot_id).first()
            if existing_appointment:
                flash('You already booked this exact slot!','error')
                return redirect(url_for('show_book_appointment',doctor_id=doctor_id))
            new_appointment=Appointment(patient_id=session['patient_id'],doctor_id=doctor.id,appointment_date=slot.date,appointment_time=slot.start_time,slot_id=selected_slot_id)
            slot.current_patients+=1
            if slot.current_patients>=slot.max_patients:slot.status='Full'
            db.session.add(new_appointment);db.session.commit()
            flash('Appointment booked successfully!','success');return redirect(url_for('patient_my_appointment'))
        return render_template('book_appointment.html',doctor=doctor,schedule=schedule)

    @app.route('/patient_my_appointment', methods=['GET'])
    def patient_my_appointment():
        if 'patient_id' not in session:
            return redirect(url_for('patient_login'))
        
        patient_id = session['patient_id']
        appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc()).all()
        
        available_slots = DoctorSlot.query.filter(
            DoctorSlot.date >= datetime.now().date(),
            DoctorSlot.status.in_(['Available', 'Full'])
        ).all()
        
        return render_template('patient_my_appointment.html', 
                            appointments=appointments, 
                            available_slots=available_slots)

    @app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
    def cancel_appointment(appointment_id):
        if 'patient_id' not in session:
            return redirect(url_for('patient_login'))
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.patient_id != session['patient_id']:
            flash('Unauthorized action', 'error')
            return redirect(url_for('patient_my_appointment'))
        slot = DoctorSlot.query.get(appointment.slot_id)
        if slot:
            slot.current_patients -= 1
            if slot.current_patients < slot.max_patients:
                slot.status = 'Available'
        db.session.delete(appointment)
        db.session.commit()
        flash('Appointment cancelled successfully', 'success')
        return redirect(url_for('patient_my_appointment'))

    @app.route('/doctor_appointments')
    def doctor_appointments():
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        doctor_id = session['doctor_id']
        today = date.today()
        search_date = request.args.get('search_date', '')
        search_name = request.args.get('search_name', '')
        search_slot = request.args.get('new_slot_id', '')
        pending_query = (Appointment.query.filter_by(doctor_id=doctor_id).filter(Appointment.status == 'Pending').join(Patient, Appointment.patient_id == Patient.id).join(DoctorSlot, Appointment.slot_id == DoctorSlot.id))
        upcoming_query = (Appointment.query.filter_by(doctor_id=doctor_id).filter(Appointment.appointment_date >= today).filter(Appointment.status == 'Confirmed').join(Patient, Appointment.patient_id == Patient.id).join(DoctorSlot, Appointment.slot_id == DoctorSlot.id))
        if search_name:
            pending_query = pending_query.filter(Patient.name.ilike(f'%{search_name}%'))
            upcoming_query = upcoming_query.filter(Patient.name.ilike(f'%{search_name}%'))
        if search_date:
            pending_query = pending_query.filter(Appointment.appointment_date == search_date)
            upcoming_query = upcoming_query.filter(Appointment.appointment_date == search_date)
        if search_slot:
            slot_date, slot_name = search_slot.split("|")
            pending_query = pending_query.filter(Appointment.appointment_date == slot_date, DoctorSlot.slot_name == slot_name)
            upcoming_query = upcoming_query.filter(Appointment.appointment_date == slot_date, DoctorSlot.slot_name == slot_name)
        pending_appointments = pending_query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()
        upcoming_appointments = upcoming_query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()
        available_slots = (DoctorSlot.query.filter_by(doctor_id=doctor_id).filter(DoctorSlot.date >= today).filter(DoctorSlot.current_patients < DoctorSlot.max_patients).order_by(DoctorSlot.date, DoctorSlot.start_time).all())
        return render_template('doctor_appointments.html', pending_appointments=pending_appointments, upcoming_appointments=upcoming_appointments, available_slots=available_slots, today=today)

    @app.route('/reschedule_appointment/<int:appointment_id>', methods=['POST'])
    def reschedule_appointment(appointment_id):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id != session['doctor_id']:
            flash('Unauthorized action', 'error')
            return redirect(url_for('doctor_appointments'))
        new_slot_id = request.form['new_slot_id']
        new_slot = DoctorSlot.query.get_or_404(new_slot_id)
        if new_slot.current_patients >= new_slot.max_patients:
            flash('The selected new slot is full.', 'error')
            return redirect(url_for('doctor_appointments'))
        existing_in_new_slot = Appointment.query.filter_by(patient_id=appointment.patient_id, slot_id=new_slot_id).first()
        if existing_in_new_slot and existing_in_new_slot.id != appointment.id:
            flash('Patient already has another appointment in the selected new slot.', 'error')
            return redirect(url_for('doctor_appointments'))
        old_slot = DoctorSlot.query.get(appointment.slot_id)
        if old_slot:
            old_slot.current_patients -= 1
            if old_slot.current_patients < old_slot.max_patients:
                old_slot.status = 'Available'
        appointment.slot_id = new_slot_id
        appointment.appointment_date = new_slot.date
        appointment.appointment_time = new_slot.start_time
        appointment.status = 'Confirmed'
        new_slot.current_patients += 1
        if new_slot.current_patients >= new_slot.max_patients:
            new_slot.status = 'Full'
        db.session.commit()
        flash('Appointment confirmed successfully', 'success')
        return redirect(url_for('doctor_appointments'))

    @app.route('/view_patient_history/<int:patient_id>')
    def view_patient_history(patient_id):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        patient = Patient.query.get_or_404(patient_id)
        history_records = PatientHistory.query.filter_by(patient_id=patient_id).order_by(PatientHistory.date_recorded.asc()).all()
        for index, record in enumerate(history_records, start=1):
            record.visit_no = index
        return render_template('patient_history.html', patient=patient, history=history_records)

    @app.route('/add_patient_record/<int:patient_id>', methods=['POST'])
    def add_patient_record(patient_id):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        Patient.query.get_or_404(patient_id)
        new_record = PatientHistory(patient_id=patient_id, medical_history=request.form.get('medical_history'), allergies=request.form.get('allergies'), current_medications=request.form.get('current_medications'), notes=request.form.get('notes'))
        db.session.add(new_record)
        db.session.commit()
        flash('Patient record added successfully', 'success')
        return redirect(url_for('view_patient_history', patient_id=patient_id))

    @app.route('/edit_patient_record/<int:record_id>', methods=['GET', 'POST'])
    def edit_patient_record(record_id):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        record = PatientHistory.query.get_or_404(record_id)
        if request.method == 'POST':
            record.medical_history = request.form.get('medical_history')
            record.allergies = request.form.get('allergies')
            record.current_medications = request.form.get('current_medications')
            record.notes = request.form.get('notes')
            db.session.commit()
            flash('Patient record updated successfully', 'success')
            return redirect(url_for('view_patient_history', patient_id=record.patient_id))
        return render_template('edit_patient_record.html', record=record)

    @app.route('/delete_patient_record/<int:record_id>', methods=['POST'])
    def delete_patient_record(record_id):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        record = PatientHistory.query.get_or_404(record_id)
        patient_id = record.patient_id
        db.session.delete(record)
        db.session.commit()
        flash('Patient record deleted successfully', 'success')
        return redirect(url_for('view_patient_history', patient_id=patient_id))

    @app.route('/update_appointment_status/<int:appointment_id>', methods=['POST'])
    def update_appointment_status(appointment_id):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id != session['doctor_id']:
            flash('Unauthorized action', 'error')
            return redirect(url_for('doctor_appointments'))
        new_status = request.form['status']
        appointment.status = new_status
        db.session.commit()
        flash(f'Appointment status updated to {new_status}', 'success')
        return redirect(url_for('doctor_appointments'))

    @app.route('/admin_view_appointments')
    def admin_view_appointments():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        search_id = request.args.get('search_id', '')
        search_patient = request.args.get('search_patient', '')
        search_doctor = request.args.get('search_doctor', '')
        status_filter = request.args.get('status_filter', '')
        appointments_query = Appointment.query.join(Patient).join(Doctor).join(DoctorSlot)
        if search_id:
            appointments_query = appointments_query.filter(Appointment.id == search_id)
        if search_patient:
            appointments_query = appointments_query.filter(Patient.name.ilike(f'%{search_patient}%'))
        if search_doctor:
            appointments_query = appointments_query.filter(Doctor.name.ilike(f'%{search_doctor}%'))
        if status_filter:
            appointments_query = appointments_query.filter(Appointment.status == status_filter)
        appointments = appointments_query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
        return render_template('admin_appointments.html', appointments=appointments, search_id=search_id, search_patient=search_patient, search_doctor=search_doctor, status_filter=status_filter)

    @app.route('/admin-cancel-appointment/<int:appointment_id>', methods=['POST'])
    def admin_cancel_appointment(appointment_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        appointment = Appointment.query.get_or_404(appointment_id)
        slot = DoctorSlot.query.get(appointment.slot_id)
        if slot:
            slot.current_patients -= 1
            if slot.current_patients < slot.max_patients:
                slot.status = 'Available'
        db.session.delete(appointment)
        db.session.commit()
        flash('Appointment cancelled successfully by admin', 'success')
        return redirect(url_for('admin_view_appointments'))

    @app.route('/admin-patient')
    def admin_patient():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        search_id = request.args.get('search_id', '')
        search_name = request.args.get('search_name', '')
        search_email = request.args.get('search_email', '')
        search_phone = request.args.get('search_phone', '')
        patients_query = Patient.query
        if search_id:
            patients_query = patients_query.filter(Patient.id == search_id)
        if search_name:
            patients_query = patients_query.filter(Patient.name.ilike(f'%{search_name}%'))
        if search_email:
            patients_query = patients_query.filter(Patient.email.ilike(f'%{search_email}%'))
        if search_phone:
            patients_query = patients_query.filter(Patient.phone.ilike(f'%{search_phone}%'))
        patients = patients_query.order_by(Patient.id).all()
        blacklist_emails = {b.email for b in blacklist.query.all()}
        return render_template('admin_patient.html', patients=patients, search_id=search_id, search_name=search_name, search_email=search_email, search_phone=search_phone, blacklist_emails=blacklist_emails)

    @app.route('/admin-view-patient/<int:patient_id>')
    def admin_view_patient(patient_id):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        patient = Patient.query.get_or_404(patient_id)
        history = PatientHistory.query.filter_by(patient_id=patient_id).order_by(PatientHistory.date_recorded.desc()).all()
        return render_template('patient_profile_admin.html', patient=patient, history=history)

    @app.route('/admin-myAcc')
    def admin_myAcc():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        admin = Admin.query.get(session['admin_id'])
        return render_template('admin_myAcc.html', admin=admin)

    @app.route('/admin-change-pass')
    def admin_change_pass():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        admin = Admin.query.get(session['admin_id'])
        return render_template('admin_change_pass.html', admin=admin)

    @app.route('/admin-update-pass', methods=['POST'])
    def admin_change_pw():
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        admin = Admin.query.get(session['admin_id'])
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('admin_change_pass'))
        if not check_password_hash(admin.password, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('admin_change_pass'))
        admin.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('admin_myAcc'))

    @app.route('/doctor_myAcc')
    def doctor_myAcc():
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        doctor = Doctor.query.get(session['doctor_id'])
        return render_template('doctor_myAcc.html', doctor=doctor)

    @app.route('/doctor-change-pass')
    def doctor_change_pass():
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        doctor = Doctor.query.get(session['doctor_id'])
        return render_template('doctor_change_pass.html', doctor=doctor)

    @app.route('/doctor-update-pw', methods=['POST'])
    def doctor_change_pw():
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        doctor = Doctor.query.get(session['doctor_id'])
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('doctor_change_pass'))
        if not check_password_hash(doctor.password, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('doctor_change_pass'))
        doctor.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('doctor_myAcc'))

    @app.route('/patient-myAcc')
    def patient_myAcc():
        if 'patient_id' not in session:
            return redirect(url_for('patient_login'))
        patient = Patient.query.get(session['patient_id'])
        return render_template('patient_myAcc.html', patient=patient)

    @app.route('/update-profile', methods=['GET', 'POST'])
    def update_profile():
        if 'patient_id' not in session:
            return redirect(url_for('patient_login'))
        patient = Patient.query.get(session['patient_id'])
        if request.method == 'POST':
            try:
                patient.name = request.form['name']
                patient.email = request.form['email']
                patient.phone = request.form['phone']
                patient.age = request.form['age'] if request.form['age'] else None
                patient.gender = request.form['gender']
                patient.blood_group = request.form['blood_group']
                patient.address = request.form['address']
                patient.emergency_contact_name = request.form['emergency_contact_name']
                patient.emergency_contact_phone = request.form['emergency_contact_phone']
                dob_str = request.form['dob']
                if dob_str:
                    patient.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('patient_myAcc'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating profile. Please try again.', 'error')
        return render_template('patient_edit_profile.html', patient=patient)

    @app.route('/patient-change-pass')
    def patient_change_pass():
        if 'patient_id' not in session:
            return redirect(url_for('patient_login'))
        patient = Patient.query.get(session['patient_id'])
        return render_template('patient_change_pass.html', patient=patient)

    @app.route('/patient-update-pw', methods=['POST'])
    def patient_change_pw():
        if 'patient_id' not in session:
            return redirect(url_for('patient_login'))
        patient = Patient.query.get(session['patient_id'])
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('patient_change_pass'))
        if not check_password_hash(patient.password, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('patient_change_pass'))
        if check_password_hash(patient.password, new_password):
            flash('New password cannot be the same as current password', 'error')
            return redirect(url_for('patient_change_pass'))
        patient.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('patient_myAcc'))

    @app.route('/patient-history-for-patient/<int:patient_id>')
    def patient_history_for_patient(patient_id):
        if 'patient_id' not in session or session['patient_id'] != patient_id:
            return redirect(url_for('patient_login'))
        patient = Patient.query.get_or_404(patient_id)
        history = PatientHistory.query.filter_by(patient_id=patient_id).order_by(PatientHistory.date_recorded.desc()).all()
        return render_template('patient_history_for_patient.html', patient=patient, history_records=history)

    @app.route('/doctor-patients')
    def doctor_patients():
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login'))
        doctor_id = session['doctor_id']
        search_id = request.args.get('search_id', '')
        search_name = request.args.get('search', '')
        patient_query = Patient.query.join(Appointment, Patient.id == Appointment.patient_id).filter(Appointment.doctor_id == doctor_id).distinct(Patient.id)
        if search_id:
            patient_query = patient_query.filter(Patient.id == search_id)
        if search_name:
            patient_query = patient_query.filter(Patient.name.ilike(f'%{search_name}%'))
        patients = patient_query.all()
        for patient in patients:
            last_appointment = Appointment.query.filter_by(patient_id=patient.id, doctor_id=doctor_id).order_by(Appointment.appointment_date.desc()).first()
            patient.last_appointment = last_appointment.appointment_date if last_appointment else None
        return render_template('doctor_patients.html', patients=patients, search_id=search_id, search_name=search_name)

    @app.route('/doc-ava/<int:doctor_id>', methods=['GET', 'POST'])
    def doctor_ava(doctor_id):
        if 'doctor_id' not in session:
            flash('Please login as doctor', 'error')
            return redirect(url_for('doctor_login'))
        if session['doctor_id'] != doctor_id:
            flash('Unauthorized access', 'error')
            return redirect(url_for('doctor_dashboard'))
        doctor = Doctor.query.get_or_404(doctor_id)
        today = date.today()
        available_dates = [today + timedelta(days=i) for i in range(7)]
        if request.method == 'POST':
            try:
                for d in available_dates:
                    date_str = d.strftime('%Y-%m-%d')
                    morning_status = request.form.get(f'morning_{date_str}')
                    morning_slot = DoctorSlot.query.filter_by(doctor_id=doctor_id, date=d, slot_name='Morning').first()
                    if morning_slot and morning_slot.current_patients == 0:
                        morning_slot.status = morning_status
                    evening_status = request.form.get(f'evening_{date_str}')
                    evening_slot = DoctorSlot.query.filter_by(doctor_id=doctor_id, date=d, slot_name='Evening').first()
                    if evening_slot and evening_slot.current_patients == 0:
                        evening_slot.status = evening_status
                db.session.commit()
                flash('Availability updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error updating availability', 'error')
                print(f"Error: {e}")
            return redirect(url_for('doctor_ava', doctor_id=doctor_id))
        schedule = []
        for d in available_dates:
            morning_slot = DoctorSlot.query.filter_by(doctor_id=doctor_id, date=d, slot_name='Morning').first()
            evening_slot = DoctorSlot.query.filter_by(doctor_id=doctor_id, date=d, slot_name='Evening').first()
            if not morning_slot:
                morning_slot = DoctorSlot(doctor_id=doctor_id, date=d, slot_name='Morning', start_time=time(8, 0), end_time=time(12, 0), max_patients=5, current_patients=0, status='Available')
                db.session.add(morning_slot)
            if not evening_slot:
                evening_slot = DoctorSlot(doctor_id=doctor_id, date=d, slot_name='Evening', start_time=time(18, 0), end_time=time(21, 0), max_patients=5, current_patients=0, status='Available')
                db.session.add(evening_slot)
            db.session.commit()
            date_slots = {'date': d, 'morning': {'status': morning_slot.status, 'start_time': morning_slot.start_time, 'end_time': morning_slot.end_time, 'slot_id': morning_slot.id, 'current_patients': morning_slot.current_patients, 'max_patients': morning_slot.max_patients}, 'evening': {'status': evening_slot.status, 'start_time': evening_slot.start_time, 'end_time': evening_slot.end_time, 'slot_id': evening_slot.id, 'current_patients': evening_slot.current_patients, 'max_patients': evening_slot.max_patients}}
            schedule.append(date_slots)
        return render_template('doctor_ava.html', doctor=doctor, slots=schedule)
    
    @app.route('/Preschedule_appointment/<int:appointment_id>', methods=['POST'])
    def Preschedule_appointment(appointment_id):
        if 'patient_id' not in session:
            return redirect(url_for('patient_login'))
        
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.patient_id != session['patient_id']:
            flash('Unauthorized action', 'error')
            return redirect(url_for('patient_my_appointment'))
        
        new_slot_id = request.form['new_slot_id']
        new_slot = DoctorSlot.query.get_or_404(new_slot_id)
        
        if new_slot.current_patients >= new_slot.max_patients:
            flash('The selected new slot is full.', 'error')
            return redirect(url_for('patient_my_appointment'))
        
        existing_in_new_slot = Appointment.query.filter_by(
            patient_id=appointment.patient_id, 
            slot_id=new_slot_id
        ).first()
        
        if existing_in_new_slot and existing_in_new_slot.id != appointment.id:
            flash('You already have another appointment in the selected new slot.', 'error')
            return redirect(url_for('patient_my_appointment'))
        
        old_slot = DoctorSlot.query.get(appointment.slot_id)
        if old_slot:
            old_slot.current_patients -= 1
            if old_slot.current_patients < old_slot.max_patients:
                old_slot.status = 'Available'
        appointment.slot_id = new_slot_id
        appointment.appointment_date = new_slot.date
        appointment.appointment_time = new_slot.start_time
        appointment.status = 'Pending'
        
        new_slot.current_patients += 1
        if new_slot.current_patients >= new_slot.max_patients:
            new_slot.status = 'Full'
        
        db.session.commit()
        flash('Appointment rescheduled successfully and is pending confirmation', 'success')
        return redirect(url_for('patient_my_appointment'))