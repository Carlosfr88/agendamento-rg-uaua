from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db
from app.models import Servico, DiaAtendimento


app = create_app()


with app.app_context():

    print("=" * 60)
    print("MIGRAÇÃO DO BANCO - AGENDA DIÁRIA")
    print("=" * 60)

    inspector = inspect(db.engine)

    # ==========================================================
    # GARANTE TABELAS DOS MODELOS
    # ==========================================================

    db.create_all()

    print("Tabelas dos modelos verificadas.")

        # ======================================================
    # TABELA DE BLOQUEIOS DE DATAS
    # ======================================================

    if not inspector.has_table("bloqueios_datas"):
        print("Criando tabela bloqueios_datas...")

        db.session.execute(text("""
            CREATE TABLE bloqueios_datas (
                id INTEGER PRIMARY KEY,
                servico_id INTEGER NOT NULL,
                data DATE NOT NULL,
                motivo VARCHAR(255),
                ativo BOOLEAN NOT NULL DEFAULT 1,
                CONSTRAINT uq_servico_data_bloqueio
                    UNIQUE (servico_id, data),
                FOREIGN KEY (servico_id)
                    REFERENCES servicos (id)
            )
        """))

        db.session.commit()

        print("Tabela bloqueios_datas criada.")
    else:
        print("Tabela bloqueios_datas já existe.")

    # ==========================================================
    # VERIFICA COLUNAS DE AGENDAMENTOS
    # ==========================================================

    colunas = {
        coluna["name"]
        for coluna in inspector.get_columns("agendamentos")
    }

    # ----------------------------------------------------------
    # ENDEREÇO
    # ----------------------------------------------------------

    if "endereco" not in colunas:

        print("Adicionando coluna: endereco")

        with db.engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE agendamentos "
                    "ADD COLUMN endereco VARCHAR(255)"
                )
            )

    else:

        print("Coluna endereco já existe.")

    # ----------------------------------------------------------
    # CLASSIFICAÇÃO
    # ----------------------------------------------------------

    if "classificacao" not in colunas:

        print("Adicionando coluna: classificacao")

        with db.engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE agendamentos "
                    "ADD COLUMN classificacao "
                    "VARCHAR(30) NOT NULL DEFAULT 'normal'"
                )
            )

    else:

        print("Coluna classificacao já existe.")

    # ==========================================================
    # VERIFICA AGENDA DIÁRIA
    # ==========================================================

    inspector = inspect(db.engine)

    tabelas = inspector.get_table_names()

    if "agendas_diarias" in tabelas:

        print("Tabela agendas_diarias já existe.")

    else:

        print("Criando tabela agendas_diarias...")

        db.create_all()

        print("Tabela agendas_diarias criada.")

    # ==========================================================
    # VERIFICA DIAS DE ATENDIMENTO
    # ==========================================================

    inspector = inspect(db.engine)

    tabelas = inspector.get_table_names()

    if "dias_atendimento" in tabelas:

        print("Tabela dias_atendimento já existe.")

    else:

        print("Criando tabela dias_atendimento...")

        db.create_all()

        print("Tabela dias_atendimento criada.")

    # ==========================================================
    # FINAL
    # ==========================================================

    # ==========================================================
    # CONFIGURA DIAS DE ATENDIMENTO
    # ==========================================================

    print()
    print("Configurando dias de atendimento...")

    servicos = Servico.query.all()

    for servico in servicos:

        for dia_semana in range(7):

            existente = DiaAtendimento.query.filter_by(
                servico_id=servico.id,
                dia_semana=dia_semana
            ).first()

            if existente is None:

                dia = DiaAtendimento(
                    servico_id=servico.id,
                    dia_semana=dia_semana,
                    ativo=(dia_semana < 5)
                )

                db.session.add(dia)

                nomes_dias = [
                    "segunda-feira",
                    "terça-feira",
                    "quarta-feira",
                    "quinta-feira",
                    "sexta-feira",
                    "sábado",
                    "domingo"
                ]

                print(
                    f"  {servico.nome}: "
                    f"{nomes_dias[dia_semana]} "
                    f"-> {'ATIVO' if dia.ativo else 'INATIVO'}"
                )

    db.session.commit()

    print("Dias de atendimento configurados.")

    print()
    print("=" * 60)
    print("MIGRAÇÃO CONCLUÍDA COM SUCESSO")
    print("=" * 60)