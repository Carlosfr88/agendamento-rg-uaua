import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import User, Servico, Agendamento, HorarioDisponivel


SQLITE_URL = os.getenv(
    "SQLITE_DATABASE_URL",
    "sqlite:///E:/agendamento-rg-uaua/instance/agendamento.db"
)

POSTGRES_URL = os.getenv(
    "POSTGRES_DATABASE_URL"
)


if not POSTGRES_URL:
    raise RuntimeError(
        "POSTGRES_DATABASE_URL não foi configurada."
    )


sqlite_engine = create_engine(
    SQLITE_URL
)

postgres_engine = create_engine(
    POSTGRES_URL
)


SQLiteSession = sessionmaker(
    bind=sqlite_engine
)

PostgresSession = sessionmaker(
    bind=postgres_engine
)


sqlite_session = SQLiteSession()
postgres_session = PostgresSession()


def migrar():

    print("=" * 70)
    print("MIGRAÇÃO SQLITE -> POSTGRESQL")
    print("=" * 70)

    print("\nLendo dados do SQLite...")

    usuarios = (
        sqlite_session
        .query(User)
        .order_by(User.id)
        .all()
    )

    servicos = (
        sqlite_session
        .query(Servico)
        .order_by(Servico.id)
        .all()
    )

    horarios = (
        sqlite_session
        .query(HorarioDisponivel)
        .order_by(HorarioDisponivel.id)
        .all()
    )

    agendamentos = (
        sqlite_session
        .query(Agendamento)
        .order_by(Agendamento.id)
        .all()
    )

    print(f"Usuários: {len(usuarios)}")
    print(f"Serviços: {len(servicos)}")
    print(f"Horários: {len(horarios)}")
    print(f"Agendamentos: {len(agendamentos)}")

    print("\nCriando estrutura no PostgreSQL...")

    from app.extensions import db

    db.metadata.create_all(
        postgres_engine
    )

    print("Estrutura criada.")

    print("\nMigrando usuários...")

    for item in usuarios:

        existente = (
            postgres_session
            .query(User)
            .filter_by(id=item.id)
            .first()
        )

        if existente:
            continue

        novo = User(
            id=item.id,
            nome=item.nome,
            username=item.username,
            password_hash=item.password_hash,
            ativo=item.ativo
        )

        postgres_session.add(novo)

    postgres_session.commit()

    print("Usuários migrados.")

    print("\nMigrando serviços...")

    for item in servicos:

        existente = (
            postgres_session
            .query(Servico)
            .filter_by(id=item.id)
            .first()
        )

        if existente:
            continue

        novo = Servico(
            id=item.id,
            nome=item.nome,
            descricao=item.descricao,
            ativo=item.ativo
        )

        postgres_session.add(novo)

    postgres_session.commit()

    print("Serviços migrados.")

    print("\nMigrando horários...")

    for item in horarios:

        existente = (
            postgres_session
            .query(HorarioDisponivel)
            .filter_by(id=item.id)
            .first()
        )

        if existente:
            continue

        novo = HorarioDisponivel(
            id=item.id,
            servico_id=item.servico_id,
            data=item.data,
            hora=item.hora,
            capacidade=item.capacidade,
            ativo=item.ativo
        )

        postgres_session.add(novo)

    postgres_session.commit()

    print("Horários migrados.")

    print("\nMigrando agendamentos...")

    for item in agendamentos:

        existente = (
            postgres_session
            .query(Agendamento)
            .filter_by(id=item.id)
            .first()
        )

        if existente:
            continue

        novo = Agendamento(
            id=item.id,
            protocolo=item.protocolo,
            servico_id=item.servico_id,
            data=item.data,
            horario=item.horario,
            nome=item.nome,
            cpf=item.cpf,
            telefone=item.telefone,
            status=item.status,
            criado_em=item.criado_em
        )

        postgres_session.add(novo)

    postgres_session.commit()

    print("Agendamentos migrados.")

    print("\n" + "=" * 70)
    print("MIGRAÇÃO CONCLUÍDA")
    print("=" * 70)


try:

    migrar()

except Exception:

    postgres_session.rollback()

    raise

finally:

    sqlite_session.close()
    postgres_session.close()