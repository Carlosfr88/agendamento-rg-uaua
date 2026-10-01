import os
from ..extensions import db

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from flask_login import (
    login_user,
    logout_user
)

from ..models import User


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username,
            ativo=True
        ).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(
                url_for("admin.dashboard")
            )

        flash(
            "Usuário ou senha inválidos.",
            "danger"
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route("/logout")
def logout():

    logout_user()

    return redirect(
        url_for("public.index")
    )

# ============================================================
# RECUPERAÇÃO TEMPORÁRIA DO ADMINISTRADOR
# ============================================================

@auth_bp.route(
    "/recuperar-admin",
    methods=["GET", "POST"]
)
def recuperar_admin():

    recovery_key = os.getenv(
        "ADMIN_RECOVERY_KEY"
    )

    recovery_username = os.getenv(
        "RECOVERY_USERNAME"
    )

    recovery_password = os.getenv(
        "RECOVERY_PASSWORD"
    )

    if not recovery_key:
        return "Recuperação não configurada.", 503

    if not recovery_username:
        return "RECOVERY_USERNAME não configurado.", 503

    if not recovery_password:
        return "RECOVERY_PASSWORD não configurado.", 503

    if request.method == "POST":

        chave = request.form.get(
            "chave",
            ""
        )

        if chave != recovery_key:

            flash(
                "Chave de recuperação inválida.",
                "danger"
            )

            return render_template(
                "auth/recuperar_admin.html"
            )

        usuario = User.query.filter_by(
            username=recovery_username
        ).first()

        if usuario:

            usuario.nome = "Administrador"
            usuario.ativo = True

        else:

            usuario = User(
                nome="Administrador",
                username=recovery_username,
                ativo=True
            )

            db.session.add(
                usuario
            )

        usuario.set_password(
            recovery_password
        )

        db.session.commit()

        flash(
            "Administrador recuperado com sucesso.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/recuperar_admin.html"
    )    
