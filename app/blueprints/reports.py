import io
import csv
import datetime

from flask import Blueprint, request, redirect, url_for, session, make_response, Response

from app.extensions import db
from app.models import Patient
from app.helpers import login_required, filter_seizures, tr_chars

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

reports_bp = Blueprint('reports', __name__)


if FPDF:
    class PDFReport(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, tr_chars('EpiTrack - Nöbet Raporu'), 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')


def _render_report_table_header(pdf):
    pdf.set_font('Arial', 'B', 10)
    w_date, w_type, w_dur, w_post, w_trig = 30, 40, 20, 40, 50
    pdf.cell(w_date, 10, tr_chars('Tarih/Saat'), 1)
    pdf.cell(w_type, 10, tr_chars('Nobet Tipi'), 1)
    pdf.cell(w_dur, 10, tr_chars('Sure'), 1)
    pdf.cell(w_post, 10, tr_chars('Sonrasi'), 1)
    pdf.cell(w_trig, 10, tr_chars('Tetikleyici'), 1)
    pdf.ln()
    return w_date, w_type, w_dur, w_post, w_trig


def _authorize_patient_access(patient):
    if 'user_id' not in session:
        return redirect(url_for('auth.index'))
    if session['role'] == 'patient' and session['user_id'] != patient.id:
        return "Unauthorized", 403
    if session['role'] == 'doctor' and patient.doctorid != session['user_id']:
        return "Unauthorized", 403
    return None


@reports_bp.route('/download_report/<int:patient_id>')
def download_report(patient_id):
    if not FPDF:
        return "FPDF library is not installed.", 500

    patient = db.get_or_404(Patient, patient_id)
    denied = _authorize_patient_access(patient)
    if denied is not None:
        return denied

    history = filter_seizures(patient.id, request.args)

    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    pdf.cell(0, 10, f"Hasta TC: {patient.tcno}", 0, 1)
    pdf.cell(0, 10, tr_chars(f"Ad Soyad: {patient.fullname}"), 0, 1)

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    pdf.cell(0, 10, f"Rapor Tarihi: {now_str}", 0, 1)
    pdf.ln(10)

    w_date, w_type, w_dur, w_post, w_trig = _render_report_table_header(pdf)

    pdf.set_font('Arial', '', 10)
    for row in history:
        if pdf.get_y() > 265:
            pdf.add_page()
            w_date, w_type, w_dur, w_post, w_trig = _render_report_table_header(pdf)
        pdf.cell(w_date, 10, row.seizuretime.strftime('%Y-%m-%d %H:%M'), 1)
        pdf.cell(w_type, 10, tr_chars(row.type), 1)
        pdf.cell(w_dur, 10, tr_chars(row.duration), 1)
        pdf.cell(w_post, 10, tr_chars(row.postictal), 1)
        pdf.cell(w_trig, 10, tr_chars(row.trigger), 1)
        pdf.ln()

    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        pdf_bytes = pdf_output.encode('latin-1', 'replace')
    else:
        pdf_bytes = bytes(pdf_output)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=rapor_{patient.tcno}.pdf'
    return response


@reports_bp.route('/export_csv/<int:patient_id>')
@login_required
def export_csv(patient_id):
    patient = db.get_or_404(Patient, patient_id)
    denied = _authorize_patient_access(patient)
    if denied is not None:
        return denied

    history = filter_seizures(patient.id, request.args)

    buffer = io.StringIO()
    buffer.write('﻿')
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Tarih', 'Saat', 'Nobet Tipi', 'Sure (dk)', 'Nobet Sonrasi', 'Tetikleyici'])
    for s in history:
        writer.writerow([
            s.seizuretime.strftime('%Y-%m-%d'),
            s.seizuretime.strftime('%H:%M'),
            s.type or '',
            s.duration if s.duration is not None else '',
            s.postictal or '',
            s.trigger or '',
        ])

    return Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=nobetler_{patient.tcno}.csv'},
    )
