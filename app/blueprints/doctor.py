from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.extensions import db
from app.models import Doctor, Patient, Message
from app.helpers import (
    login_required, filter_seizures, compute_stats, paginate, get_page_arg,
    clean_filters, log_audit,
)

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')


@doctor_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if session['role'] != 'doctor':
        return redirect(url_for('auth.index'))

    doctor = db.session.get(Doctor, session['user_id'])
    patients = Patient.query.filter_by(doctorid=doctor.id).all()

    selected_patient = None
    history = None
    stats = None
    page_meta = None

    patient_id = request.args.get('patient_id')
    if patient_id:
        selected_patient = db.session.get(Patient, int(patient_id)) if patient_id.isdigit() else None
        if selected_patient and selected_patient.doctorid == doctor.id:
            full_history = filter_seizures(selected_patient.id, request.args)
            stats = compute_stats(full_history)
            history, page_meta = paginate(full_history, get_page_arg())
        else:
            if selected_patient:
                flash('Bu hastayı görüntüleme yetkiniz yok.', 'danger')
            selected_patient = None

    unread = Message.query.filter_by(doctor_id=doctor.id, sender_role='patient', is_read=False).count()

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        patients=patients,
        selected_patient=selected_patient,
        history=history,
        page_meta=page_meta,
        stats=stats,
        filters=clean_filters(request.args),
        unread=unread,
    )


@doctor_bp.route('/messages/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def messages(patient_id):
    if session['role'] != 'doctor':
        return redirect(url_for('auth.index'))
    doctor = db.session.get(Doctor, session['user_id'])
    patient = db.get_or_404(Patient, patient_id)
    if patient.doctorid != doctor.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        body = (request.form.get('body') or '').strip()
        if body:
            msg = Message(doctor_id=doctor.id, patient_id=patient.id,
                          sender_role='doctor', body=body)
            db.session.add(msg)
            db.session.commit()
            log_audit('create', 'message', msg.id, f'Doktor mesaj gönderdi -> {patient.fullname}')
            flash('Mesajınız gönderildi.', 'success')
        return redirect(url_for('doctor.messages', patient_id=patient.id))

    Message.query.filter_by(patient_id=patient.id, sender_role='patient', is_read=False)\
        .update({'is_read': True})
    db.session.commit()

    conversation = Message.query.filter_by(patient_id=patient.id)\
        .order_by(Message.created_at.asc()).all()
    return render_template('messages.html', messages=conversation, patient=patient,
                           doctor=doctor, role='doctor')
