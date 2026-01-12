import click

from app.extensions import db
from app.models import Admin
from app.helpers import hash_password


def register_cli(app):
    @app.cli.command('create-admin')
    @click.option('--username', prompt=True, help='Yönetici kullanıcı adı')
    @click.option('--fullname', prompt=True, help='Ad Soyad')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, fullname, password):
        if Admin.query.filter_by(username=username).first():
            click.echo(f"'{username}' kullanıcı adı zaten mevcut.")
            return
        admin = Admin(username=username, fullname=fullname, password=hash_password(password))
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Yönetici oluşturuldu: {username}")
