from urllib.parse import urlencode

from flask import Flask, request, flash, redirect, url_for

from config import Config
from app.extensions import db, migrate, csrf, limiter


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.errorhandler(429)
    def too_many_requests(e):
        flash('Çok fazla deneme yapıldı. Lütfen bir dakika sonra tekrar deneyin.', 'danger')
        if request.path.startswith('/admin'):
            return redirect(url_for('admin.login'))
        return redirect(url_for('auth.index'))

    from app import models

    from app.blueprints.auth import auth_bp
    from app.blueprints.patient import patient_bp
    from app.blueprints.doctor import doctor_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    def merge_query(**overrides):
        args = request.args.to_dict()
        args.update(overrides)
        args = {k: v for k, v in args.items() if v not in (None, '')}
        return urlencode(args)

    # Registered as a Jinja global (not a context processor) so it is also
    # accessible inside imported macros such as _macros.html's pager().
    app.jinja_env.globals['merge_query'] = merge_query

    from app.cli import register_cli
    register_cli(app)

    return app
