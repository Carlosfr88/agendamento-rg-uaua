from datetime import time

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

    endereco = db.Column(
    db.String(255),
    nullable=True

    )

    classificacao = db.Column(
        db.String(30),
        nullable=False,
        default="normal",
        server_default="normal"
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

# ==========================================================
# AGENDA DIÁRIA
# ==========================================================

class AgendaDiaria(db.Model):
    __tablename__ = "agendas_diarias"

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

    hora_inicio = db.Column(
        db.Time,
        nullable=False,
        default=time(8, 0)
    )

    hora_fim = db.Column(
        db.Time,
        nullable=False,
        default=time(14, 0)
    )

    capacidade = db.Column(
        db.Integer,
        nullable=False,
        default=30
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    servico = db.relationship(
        "Servico",
        backref=db.backref(
            "agendas_diarias",
            lazy=True
        )
    )

# ==========================================================
# INFORMAÇÕES PÚBLICAS
# ==========================================================

class Informacao(db.Model):
    __tablename__ = "informacoes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    titulo = db.Column(
        db.String(150),
        nullable=False
    )

    conteudo = db.Column(
        db.Text,
        nullable=False
    )

    ordem = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    ) 

# ==========================================================
# DIAS DE ATENDIMENTO
# ==========================================================

class DiaAtendimento(db.Model):
    __tablename__ = "dias_atendimento"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    servico_id = db.Column(
        db.Integer,
        db.ForeignKey("servicos.id"),
        nullable=False
    )

    dia_semana = db.Column(
        db.Integer,
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
            "dias_atendimento",
            lazy=True
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "servico_id",
            "dia_semana",
            name="uq_servico_dia_semana"
        ),
    )

# ==========================================================
# BLOQUEIOS DE DATAS
# ==========================================================

class BloqueioData(db.Model):
    __tablename__ = "bloqueios_datas"

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

    motivo = db.Column(
        db.String(255),
        nullable=True
    )

    ativo = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    servico = db.relationship(
        "Servico",
        backref=db.backref(
            "bloqueios_datas",
            lazy=True
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "servico_id",
            "data",
            name="uq_servico_data_bloqueio"
        ),
    )           