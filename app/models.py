from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db
from .extensions import login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(120), nullable=False)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================================
# SERVIÇOS
# ==========================================================

class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    descricao = db.Column(
        db.Text,
        nullable=True
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    agendamentos = db.relationship(
        "Agendamento",
        back_populates="servico",
        lazy=True
    )


# ==========================================================
# AGENDAMENTOS
# ==========================================================

class Agendamento(db.Model):
    __tablename__ = "agendamentos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    protocolo = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    servico_id = db.Column(
        db.Integer,
        db.ForeignKey("servicos.id"),
        nullable=False
    )

    data = db.Column(
        db.Date,
        nullable=False
    )

    horario = db.Column(
        db.Time,
        nullable=False
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    cpf = db.Column(
        db.String(14),
        nullable=False
    )

    telefone = db.Column(
        db.String(20),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="agendado",
        nullable=False
    )

    criado_em = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    servico = db.relationship(
        "Servico",
        back_populates="agendamentos"
    )

# ==========================================================
# HORÁRIOS DISPONÍVEIS
# ==========================================================

class HorarioDisponivel(db.Model):
    __tablename__ = "horarios_disponiveis"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    servico_id = db.Column(
        db.Integer,
        db.ForeignKey("servicos.id"),
        nullable=False
    )

    data = db.Column(
        db.Date,
        nullable=False
    )

    hora = db.Column(
        db.Time,
        nullable=False
    )

    capacidade = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    servico = db.relationship(
        "Servico",
        backref=db.backref(
            "horarios_disponiveis",
            lazy=True
        )
    )    