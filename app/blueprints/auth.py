import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.extensions import db, limiter
from app.models import Doctor, Patient
from app.helpers import hash_password, verify_password, is_valid_tckn, log_audit, login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'patient':
            return redirect(url_for('patient.dashboard'))
        elif session.get('role') == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    doctors = Doctor.query.filter_by(is_approved=True).all()
    if request.method == 'POST':
        role = request.form.get('role')
        fullname = request.form.get('fullname')
        tcno = request.form.get('tcno')
        password = request.form.get('password')
        hashed_pw = hash_password(password)

        if not is_valid_tckn(tcno):
            flash('Geçersiz T.C. Kimlik Numarası. 11 haneli ve doğru olmalıdır.', 'danger')
            return redirect(url_for('auth.register'))

        if role == 'doctor':
            if Doctor.query.filter_by(tcno=tcno).first():
                flash('Bu TC No ile kayıtlı doktor zaten var.', 'danger')
                return redirect(url_for('auth.register'))

            new_doc = Doctor(fullname=fullname, tcno=tcno, password=hashed_pw, is_approved=False)
            db.session.add(new_doc)
            db.session.commit()
            log_audit('create', 'doctor', new_doc.id, f'Kayıt (onay bekliyor): {fullname}')
            flash('Doktor kaydınız alındı. Hesabınız yönetici onayından sonra aktifleşecektir.', 'info')
            return redirect(url_for('auth.index'))

        elif role == 'patient':
            doctorid = request.form.get('doctorid')
            bloodtype = request.form.get('bloodtype')
            birthdate_str = request.form.get('birthdate')

            if Patient.query.filter_by(tcno=tcno).first():
                flash('Bu TC No ile kayıtlı hasta zaten var.', 'danger')
                return redirect(url_for('auth.register'))

            try:
                birthdate = datetime.datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Geçersiz doğum tarihi formatı.', 'danger')
                return redirect(url_for('auth.register'))

            new_pat = Patient(
                fullname=fullname, tcno=tcno, password=hashed_pw,
                doctorid=doctorid, bloodtype=bloodtype, birthdate=birthdate,
            )
            db.session.add(new_pat)
            db.session.commit()
            log_audit('create', 'patient', new_pat.id, f'Kayıt: {fullname}')
            flash('Hasta kaydı başarılı.', 'success')
            return redirect(url_for('auth.index'))

    return render_template('register.html', doctors=doctors)


@auth_bp.route('/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    role = request.form.get('role')
    tcno = request.form.get('tcno')
    password = request.form.get('password')

    if role == 'patient':
        user = Patient.query.filter_by(tcno=tcno).first()
        if user and verify_password(user, password):
            session['user_id'] = user.id
            session['role'] = 'patient'
            session['name'] = user.fullname
            return redirect(url_for('patient.dashboard'))
    elif role == 'doctor':
        user = Doctor.query.filter_by(tcno=tcno).first()
        if user and verify_password(user, password):
            if not user.is_approved:
                flash('Hesabınız henüz yönetici tarafından onaylanmadı.', 'warning')
                return redirect(url_for('auth.index'))
            session['user_id'] = user.id
            session['role'] = 'doctor'
            session['name'] = user.fullname
            return redirect(url_for('doctor.dashboard'))

    flash('Giriş başarısız. Bilgilerinizi kontrol edin.', 'danger')
    return redirect(url_for('auth.index'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    role = session['role']
    user_id = session['user_id']

    if role == 'doctor':
        user = db.session.get(Doctor, user_id)
    else:
        user = db.session.get(Patient, user_id)

    if request.method == 'POST':
        fullname = request.form.get('fullname')
        if fullname:
            user.fullname = fullname

        tcno = request.form.get('tcno')
        if tcno and tcno != user.tcno:
            if not is_valid_tckn(tcno):
                flash('Geçersiz T.C. Kimlik Numarası.', 'danger')
                return redirect(url_for('auth.profile'))
            user.tcno = tcno

        new_pass = request.form.get('password')
        if new_pass:
            user.password = hash_password(new_pass)

        if role == 'patient':
            bloodtype = request.form.get('bloodtype')
            if bloodtype:
                user.bloodtype = bloodtype

            birthdate_str = request.form.get('birthdate')
            if birthdate_str:
                try:
                    user.birthdate = datetime.datetime.strptime(birthdate_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            doctorid = request.form.get('doctorid')
            if doctorid:
                user.doctorid = doctorid

        db.session.commit()
        session['name'] = user.fullname
        log_audit('update', role, user.id, 'Profil güncellendi')
        flash('Profil bilgileriniz güncellendi.', 'success')
        return redirect(url_for('auth.index'))

    doctors = Doctor.query.filter_by(is_approved=True).all() if role == 'patient' else []
    return render_template('edit_profile.html', user=user, role=role, doctors=doctors)


@auth_bp.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        role = session['role']
        user_id = session['user_id']

        if role == 'doctor':
            user = db.session.get(Doctor, user_id)
            if user and user.patients:
                flash('Size atanmış hastalar varken hesabınızı silemezsiniz. '
                      'Lütfen yönetici ile iletişime geçin.', 'danger')
                return redirect(url_for('auth.profile'))
        else:
            user = db.session.get(Patient, user_id)

        if user:
            name = user.fullname
            db.session.delete(user)
            db.session.commit()
            log_audit('delete', role, user_id, f'Hesap silindi: {name}')
            session.clear()
            flash('Hesabınız başarıyla silindi.', 'success')
            return redirect(url_for('auth.index'))

    return redirect(url_for('auth.index'))
