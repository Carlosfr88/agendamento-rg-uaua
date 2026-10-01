from datetime import date, time, timedelta

from app import create_app
from app.extensions import db
from app.models import Servico, HorarioDisponivel


app = create_app()


with app.app_context():

    servicos = Servico.query.filter_by(
        ativo=True
    ).all()

    if not servicos:
        print("Nenhum serviço encontrado.")
        exit()

    hoje = date.today()

    horarios = [
        time(8, 0),
        time(8, 30),
        time(9, 0),
        time(9, 30),
        time(10, 0),
        time(10, 30),
        time(11, 0),
        time(11, 30),
        time(13, 0),
        time(13, 30),
        time(14, 0),
        time(14, 30),
        time(15, 0),
        time(15, 30),
        time(16, 0),
    ]

    for servico in servicos:

        for dias_a_frente in range(1, 31):

            data_agenda = hoje + timedelta(
                days=dias_a_frente
            )

            # Segunda a sexta
            if data_agenda.weekday() >= 5:
                continue

            for horario in horarios:

                existente = HorarioDisponivel.query.filter_by(
                    servico_id=servico.id,
                    data=data_agenda,
                    hora=horario
                ).first()

                if not existente:

                    novo_horario = HorarioDisponivel(
                        servico_id=servico.id,
                        data=data_agenda,
                        hora=horario,
                        capacidade=1,
                        ativo=True
                    )

                    db.session.add(novo_horario)

    db.session.commit()

    print("Horários cadastrados com sucesso!")