import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.extensions import db
from app.models import Patient, Seizure, Message
from app.constants import SEIZURE_TYPES, SEIZURE_TRIGGERS
from app.helpers import (
    login_required, parse_duration_input, filter_seizures, compute_stats,
    paginate, get_page_arg, clean_filters, log_audit,
)

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')


@patient_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if session['role'] != 'patient':
        return redirect(url_for('auth.index'))

    patient = db.session.get(Patient, session['user_id'])

    if request.method == 'POST':
        try:
            dt_str = f"{request.form.get('date')} {request.form.get('time')}"
            seizuretime = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
            new_seizure = Seizure(
                patientid=patient.id,
                seizuretime=seizuretime,
                type=request.form.get('type'),
                trigger=request.form.get('trigger'),
                postictal=request.form.get('post_seizure'),
                duration=parse_duration_input(request.form.get('duration')),
            )
            db.session.add(new_seizure)
            db.session.commit()
            log_audit('create', 'seizure', new_seizure.id, f'Nöbet eklendi ({seizuretime:%Y-%m-%d %H:%M})')
            flash('Nöbet kaydı eklendi.', 'success')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')

    history = filter_seizures(patient.id, request.args)
    stats = compute_stats(history)
    page_items, page_meta = paginate(history, get_page_arg())
    unread = Message.query.filter_by(patient_id=patient.id, sender_role='doctor', is_read=False).count()

    return render_template(
        'patient_dashboard.html',
        patient=patient,
        history=page_items,
        page_meta=page_meta,
        stats=stats,
        seizure_types=SEIZURE_TYPES,
        seizure_triggers=SEIZURE_TRIGGERS,
        filters=clean_filters(request.args),
        unread=unread,
    )


@patient_bp.route('/delete_seizure/<int:id>', methods=['POST'])
@login_required
def delete_seizure(id):
    if session['role'] != 'patient':
        return redirect(url_for('auth.index'))
    seizure = db.get_or_404(Seizure, id)
    if seizure.patientid != session['user_id']:
        return "Unauthorized", 403
    db.session.delete(seizure)
    db.session.commit()
    log_audit('delete', 'seizure', id, 'Nöbet silindi')
    flash('Nöbet silindi.', 'success')
    return redirect(url_for('patient.dashboard'))


@patient_bp.route('/edit_seizure/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_seizure(id):
    if session['role'] != 'patient':
        return redirect(url_for('auth.index'))
    seizure = db.get_or_404(Seizure, id)
    if seizure.patientid != session['user_id']:
        return "Unauthorized", 403

    if request.method == 'POST':
        try:
            dt_str = f"{request.form.get('date')} {request.form.get('time')}"
            seizure.seizuretime = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
            seizure.type = request.form.get('type')
            seizure.trigger = request.form.get('trigger')
            seizure.postictal = request.form.get('post_seizure')
            seizure.duration = parse_duration_input(request.form.get('duration'))
            db.session.commit()
            log_audit('update', 'seizure', seizure.id, 'Nöbet güncellendi')
            flash('Nöbet kaydı güncellendi.', 'success')
            return redirect(url_for('patient.dashboard'))
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')

    return render_template(
        'edit_seizure.html',
        seizure=seizure,
        seizure_types=SEIZURE_TYPES,
        seizure_triggers=SEIZURE_TRIGGERS,
    )


@patient_bp.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    if session['role'] != 'patient':
        return redirect(url_for('auth.index'))
    patient = db.session.get(Patient, session['user_id'])

    if request.method == 'POST':
        body = (request.form.get('body') or '').strip()
        if body:
            msg = Message(doctor_id=patient.doctorid, patient_id=patient.id,
                          sender_role='patient', body=body)
            db.session.add(msg)
            db.session.commit()
            log_audit('create', 'message', msg.id, 'Hasta mesaj gönderdi')
            flash('Mesajınız gönderildi.', 'success')
        return redirect(url_for('patient.messages'))

    Message.query.filter_by(patient_id=patient.id, sender_role='doctor', is_read=False)\
        .update({'is_read': True})
    db.session.commit()

    conversation = Message.query.filter_by(patient_id=patient.id)\
        .order_by(Message.created_at.asc()).all()
    return render_template('messages.html', messages=conversation, patient=patient,
                           doctor=patient.doctor, role='patient')
