import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from sqlalchemy import or_, func

from app.extensions import db, limiter
from app.models import Doctor, Patient, Seizure, Message, Admin, AuditLog
from app.constants import SEIZURE_TYPES, SEIZURE_TRIGGERS
from app.helpers import (
    admin_required, hash_password, is_valid_tckn, parse_duration_input,
    paginate, get_page_arg, log_audit,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session.clear()
            session['user_id'] = admin.id
            session['role'] = 'admin'
            session['name'] = admin.fullname
            log_audit('login', 'admin', admin.id, 'Yönetici girişi')
            return redirect(url_for('admin.dashboard'))
        flash('Yönetici girişi başarısız.', 'danger')
        return redirect(url_for('admin.login'))
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))


@admin_bp.route('/profile', methods=['GET', 'POST'])
@admin_required
def profile():
    admin = db.get_or_404(Admin, session['user_id'])
    if request.method == 'POST':
        fullname = (request.form.get('fullname') or '').strip()
        username = (request.form.get('username') or '').strip()
        current = request.form.get('current_password') or ''
        new_pass = request.form.get('new_password') or ''
        confirm = request.form.get('confirm_password') or ''

        if not fullname or not username:
            flash('Ad soyad ve kullanıcı adı boş bırakılamaz.', 'danger')
            return redirect(url_for('admin.profile'))

        existing = Admin.query.filter_by(username=username).first()
        if existing and existing.id != admin.id:
            flash('Bu kullanıcı adı zaten kullanılıyor.', 'danger')
            return redirect(url_for('admin.profile'))

        if new_pass:
            if not check_password_hash(admin.password, current):
                flash('Mevcut parola hatalı.', 'danger')
                return redirect(url_for('admin.profile'))
            if new_pass != confirm:
                flash('Yeni parolalar eşleşmiyor.', 'danger')
                return redirect(url_for('admin.profile'))
            admin.password = hash_password(new_pass)

        admin.fullname = fullname
        admin.username = username
        db.session.commit()
        session['name'] = admin.fullname
        log_audit('update', 'admin', admin.id, 'Profil güncellendi')
        flash('Profil bilgileriniz güncellendi.', 'success')
        return redirect(url_for('admin.profile'))

    return render_template('admin/profile.html', admin=admin)


@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'doctors': db.session.scalar(db.select(func.count(Doctor.id))),
        'patients': db.session.scalar(db.select(func.count(Patient.id))),
        'seizures': db.session.scalar(db.select(func.count(Seizure.id))),
        'messages': db.session.scalar(db.select(func.count(Message.id))),
    }
    recent_audit_items = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    recent_audit, recent_audit_meta = paginate(recent_audit_items, get_page_arg(), per_page=10)
    recent_seizures = Seizure.query.order_by(Seizure.id.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_audit=recent_audit, recent_audit_meta=recent_audit_meta,
                           recent_seizures=recent_seizures)


def _admin_search(model, fields, args):
    query = model.query
    q = (args.get('q') or '').strip()
    if q:
        like = f'%{q}%'
        query = query.filter(or_(*[getattr(model, f).ilike(like) for f in fields]))
    items = query.order_by(model.id.desc()).all()
    page_items, meta = paginate(items, get_page_arg())
    return page_items, meta, q


@admin_bp.route('/doctors')
@admin_required
def doctors():
    items, meta, q = _admin_search(Doctor, ['fullname', 'tcno'], request.args)
    return render_template('admin/doctors.html', doctors=items, page_meta=meta, q=q)


@admin_bp.route('/doctors/new', methods=['GET', 'POST'])
@admin_required
def doctor_new():
    if request.method == 'POST':
        tcno = request.form.get('tcno')
        if not is_valid_tckn(tcno):
            flash('Geçersiz T.C. Kimlik Numarası.', 'danger')
            return redirect(url_for('admin.doctor_new'))
        if Doctor.query.filter_by(tcno=tcno).first():
            flash('Bu TC No ile kayıtlı doktor zaten var.', 'danger')
            return redirect(url_for('admin.doctor_new'))
        password = (request.form.get('password') or '').strip()
        if not password:
            flash('Parola boş bırakılamaz.', 'danger')
            return redirect(url_for('admin.doctor_new'))
        doc = Doctor(fullname=request.form.get('fullname'), tcno=tcno,
                     password=hash_password(password), is_approved=True)
        db.session.add(doc)
        db.session.commit()
        log_audit('create', 'doctor', doc.id, f'Admin doktor ekledi: {doc.fullname}')
        flash('Doktor eklendi.', 'success')
        return redirect(url_for('admin.doctors'))
    return render_template('admin/doctor_form.html', doctor=None)


@admin_bp.route('/doctors/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def doctor_edit(id):
    doctor = db.get_or_404(Doctor, id)
    if request.method == 'POST':
        tcno = request.form.get('tcno')
        if tcno and tcno != doctor.tcno and not is_valid_tckn(tcno):
            flash('Geçersiz T.C. Kimlik Numarası.', 'danger')
            return redirect(url_for('admin.doctor_edit', id=id))
        doctor.fullname = request.form.get('fullname') or doctor.fullname
        if tcno:
            doctor.tcno = tcno
        new_pass = request.form.get('password')
        if new_pass:
            doctor.password = hash_password(new_pass)
        db.session.commit()
        log_audit('update', 'doctor', doctor.id, f'Admin doktor güncelledi: {doctor.fullname}')
        flash('Doktor güncellendi.', 'success')
        return redirect(url_for('admin.doctors'))
    return render_template('admin/doctor_form.html', doctor=doctor)


@admin_bp.route('/doctors/<int:id>/approve', methods=['POST'])
@admin_required
def doctor_approve(id):
    doctor = db.get_or_404(Doctor, id)
    doctor.is_approved = True
    db.session.commit()
    log_audit('update', 'doctor', doctor.id, f'Doktor onaylandı: {doctor.fullname}')
    flash('Doktor onaylandı.', 'success')
    return redirect(url_for('admin.doctors'))


@admin_bp.route('/doctors/<int:id>/delete', methods=['POST'])
@admin_required
def doctor_delete(id):
    doctor = db.get_or_404(Doctor, id)
    if doctor.patients:
        flash('Bu doktora atanmış hastalar var. Silmeden önce hastaları başka bir doktora aktarın.', 'danger')
        return redirect(url_for('admin.doctors'))
    name = doctor.fullname
    db.session.delete(doctor)
    db.session.commit()
    log_audit('delete', 'doctor', id, f'Admin doktor sildi: {name}')
    flash('Doktor silindi.', 'success')
    return redirect(url_for('admin.doctors'))


@admin_bp.route('/patients')
@admin_required
def patients():
    items, meta, q = _admin_search(Patient, ['fullname', 'tcno'], request.args)
    return render_template('admin/patients.html', patients=items, page_meta=meta, q=q)


@admin_bp.route('/patients/new', methods=['GET', 'POST'])
@admin_required
def patient_new():
    doctors = Doctor.query.filter_by(is_approved=True).all()
    if request.method == 'POST':
        tcno = request.form.get('tcno')
        if not is_valid_tckn(tcno):
            flash('Geçersiz T.C. Kimlik Numarası.', 'danger')
            return redirect(url_for('admin.patient_new'))
        if Patient.query.filter_by(tcno=tcno).first():
            flash('Bu TC No ile kayıtlı hasta zaten var.', 'danger')
            return redirect(url_for('admin.patient_new'))
        password = (request.form.get('password') or '').strip()
        if not password:
            flash('Parola boş bırakılamaz.', 'danger')
            return redirect(url_for('admin.patient_new'))
        birthdate = None
        if request.form.get('birthdate'):
            try:
                birthdate = datetime.datetime.strptime(request.form['birthdate'], '%Y-%m-%d').date()
            except ValueError:
                pass
        pat = Patient(fullname=request.form.get('fullname'), tcno=tcno,
                      password=hash_password(password),
                      bloodtype=request.form.get('bloodtype'), birthdate=birthdate,
                      doctorid=request.form.get('doctorid'))
        db.session.add(pat)
        db.session.commit()
        log_audit('create', 'patient', pat.id, f'Admin hasta ekledi: {pat.fullname}')
        flash('Hasta eklendi.', 'success')
        return redirect(url_for('admin.patients'))
    return render_template('admin/patient_form.html', patient=None, doctors=doctors)


@admin_bp.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def patient_edit(id):
    patient = db.get_or_404(Patient, id)
    doctors = Doctor.query.filter_by(is_approved=True).all()
    if request.method == 'POST':
        tcno = request.form.get('tcno')
        if tcno and tcno != patient.tcno and not is_valid_tckn(tcno):
            flash('Geçersiz T.C. Kimlik Numarası.', 'danger')
            return redirect(url_for('admin.patient_edit', id=id))
        patient.fullname = request.form.get('fullname') or patient.fullname
        if tcno:
            patient.tcno = tcno
        patient.bloodtype = request.form.get('bloodtype')
        if request.form.get('doctorid'):
            patient.doctorid = request.form.get('doctorid')
        if request.form.get('birthdate'):
            try:
                patient.birthdate = datetime.datetime.strptime(request.form['birthdate'], '%Y-%m-%d').date()
            except ValueError:
                pass
        new_pass = request.form.get('password')
        if new_pass:
            patient.password = hash_password(new_pass)
        db.session.commit()
        log_audit('update', 'patient', patient.id, f'Admin hasta güncelledi: {patient.fullname}')
        flash('Hasta güncellendi.', 'success')
        return redirect(url_for('admin.patients'))
    return render_template('admin/patient_form.html', patient=patient, doctors=doctors)


@admin_bp.route('/patients/<int:id>/delete', methods=['POST'])
@admin_required
def patient_delete(id):
    patient = db.get_or_404(Patient, id)
    name = patient.fullname
    db.session.delete(patient)
    db.session.commit()
    log_audit('delete', 'patient', id, f'Admin hasta sildi: {name}')
    flash('Hasta silindi.', 'success')
    return redirect(url_for('admin.patients'))


@admin_bp.route('/seizures')
@admin_required
def seizures():
    items = Seizure.query.order_by(Seizure.seizuretime.desc()).all()
    page_items, meta = paginate(items, get_page_arg())
    return render_template('admin/seizures.html', seizures=page_items, page_meta=meta)


@admin_bp.route('/seizures/new', methods=['GET', 'POST'])
@admin_required
def seizure_new():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        try:
            dt = datetime.datetime.strptime(
                f"{request.form.get('date')} {request.form.get('time')}", '%Y-%m-%d %H:%M')
            s = Seizure(patientid=request.form.get('patientid'), seizuretime=dt,
                        type=request.form.get('type'), trigger=request.form.get('trigger'),
                        postictal=request.form.get('post_seizure'),
                        duration=parse_duration_input(request.form.get('duration')))
            db.session.add(s)
            db.session.commit()
            log_audit('create', 'seizure', s.id, 'Admin nöbet ekledi')
            flash('Nöbet eklendi.', 'success')
            return redirect(url_for('admin.seizures'))
        except Exception as e:
            flash(f'Hata: {e}', 'danger')
    return render_template('admin/seizure_form.html', seizure=None, patients=patients_list,
                           seizure_types=SEIZURE_TYPES, seizure_triggers=SEIZURE_TRIGGERS)


@admin_bp.route('/seizures/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def seizure_edit(id):
    seizure = db.get_or_404(Seizure, id)
    patients_list = Patient.query.all()
    if request.method == 'POST':
        try:
            seizure.seizuretime = datetime.datetime.strptime(
                f"{request.form.get('date')} {request.form.get('time')}", '%Y-%m-%d %H:%M')
            seizure.patientid = request.form.get('patientid')
            seizure.type = request.form.get('type')
            seizure.trigger = request.form.get('trigger')
            seizure.postictal = request.form.get('post_seizure')
            seizure.duration = parse_duration_input(request.form.get('duration'))
            db.session.commit()
            log_audit('update', 'seizure', seizure.id, 'Admin nöbet güncelledi')
            flash('Nöbet güncellendi.', 'success')
            return redirect(url_for('admin.seizures'))
        except Exception as e:
            flash(f'Hata: {e}', 'danger')
    return render_template('admin/seizure_form.html', seizure=seizure, patients=patients_list,
                           seizure_types=SEIZURE_TYPES, seizure_triggers=SEIZURE_TRIGGERS)


@admin_bp.route('/seizures/<int:id>/delete', methods=['POST'])
@admin_required
def seizure_delete(id):
    seizure = db.get_or_404(Seizure, id)
    db.session.delete(seizure)
    db.session.commit()
    log_audit('delete', 'seizure', id, 'Admin nöbet sildi')
    flash('Nöbet silindi.', 'success')
    return redirect(url_for('admin.seizures'))


@admin_bp.route('/audit')
@admin_required
def audit():
    items = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    page_items, meta = paginate(items, get_page_arg(), per_page=25)
    return render_template('admin/audit.html', logs=page_items, page_meta=meta)
