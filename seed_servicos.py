from app import create_app
from app.extensions import db
from app.models import Servico


app = create_app()


with app.app_context():

    servicos = [
        {
            "nome": "Primeira via",
            "descricao": "Emissão da primeira via do documento de identificação."
        },
        {
            "nome": "Segunda via",
            "descricao": "Emissão da segunda via do documento de identificação."
        },
        {
            "nome": "Atualização",
            "descricao": "Atualização dos dados do documento de identificação."
        }
    ]

    for item in servicos:

        existente = Servico.query.filter_by(
            nome=item["nome"]
        ).first()

        if not existente:

            servico = Servico(
                nome=item["nome"],
                descricao=item["descricao"]
            )

            db.session.add(servico)

    db.session.commit()

    print("Serviços cadastrados com sucesso!")