import datetime
import hashlib
from collections import Counter, OrderedDict
from functools import wraps

from flask import session, flash, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

from app.extensions import db
from app.models import Seizure, AuditLog

PER_PAGE = 10


def hash_password(password):
    return generate_password_hash(password)


def _is_legacy_sha256(stored):
    return len(stored) == 64 and all(c in '0123456789abcdef' for c in stored.lower())


def verify_password(user, password):
    stored = user.password
    if _is_legacy_sha256(stored):
        if hashlib.sha256(password.encode()).hexdigest() == stored:
            user.password = generate_password_hash(password)
            db.session.commit()
            return True
        return False
    return check_password_hash(stored, password)


def tr_chars(text):
    if text is None:
        return ""
    text = str(text)
    replacements = {
        'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def is_valid_tckn(value):
    if not value or not value.isdigit() or len(value) != 11:
        return False
    d = [int(c) for c in value]
    if d[0] == 0:
        return False
    if (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 != d[9]:
        return False
    if sum(d[0:10]) % 10 != d[10]:
        return False
    return True


def parse_duration_input(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        n = int(float(value.replace(',', '.')))
        return n if n >= 0 else None
    except ValueError:
        return None


def clean_filters(args):
    return {k: args.get(k) for k in ('start', 'end', 'q') if args.get(k)}


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def filter_seizures(patient_id, args):
    query = Seizure.query.filter_by(patientid=patient_id)

    start = _parse_date(args.get('start'))
    end = _parse_date(args.get('end'))
    search = (args.get('q') or '').strip()

    if start:
        query = query.filter(Seizure.seizuretime >= datetime.datetime.combine(start, datetime.time.min))
    if end:
        query = query.filter(Seizure.seizuretime <= datetime.datetime.combine(end, datetime.time.max))
    if search:
        like = f'%{search}%'
        query = query.filter(or_(
            Seizure.type.ilike(like),
            Seizure.trigger.ilike(like),
            Seizure.postictal.ilike(like),
        ))

    return query.order_by(Seizure.seizuretime.desc()).all()


def compute_stats(history):
    total = len(history)
    by_type = Counter((s.type or 'Belirtilmemiş') for s in history)
    by_trigger = Counter((s.trigger or 'Belirtilmemiş') for s in history)

    months = OrderedDict()
    today = datetime.date.today().replace(day=1)
    for i in range(11, -1, -1):
        year = today.year + (today.month - 1 - i) // 12
        month = (today.month - 1 - i) % 12 + 1
        months[f'{year:04d}-{month:02d}'] = 0
    for s in history:
        key = s.seizuretime.strftime('%Y-%m')
        if key in months:
            months[key] += 1

    durations = [s.duration for s in history if s.duration is not None]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else None

    return {
        'total': total,
        'by_type': dict(by_type),
        'by_trigger': dict(by_trigger.most_common(8)),
        'months': months,
        'avg_duration': avg_duration,
    }


def paginate(items, page, per_page=PER_PAGE):
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    meta = {
        'page': page,
        'total_pages': total_pages,
        'total': total,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }
    return items[start:start + per_page], meta


def get_page_arg():
    try:
        return max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        return 1


def log_audit(action, entity, entity_id=None, details=''):
    entry = AuditLog(
        actor_role=session.get('role', 'system'),
        actor_id=session.get('user_id'),
        actor_name=session.get('name', 'Sistem'),
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=str(details)[:255],
    )
    db.session.add(entry)
    db.session.commit()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Lütfen önce giriş yapın.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Bu alana erişim için yönetici girişi gerekli.', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function
