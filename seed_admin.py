from app import create_app
from app.extensions import db
from app.models import User


app = create_app()


with app.app_context():

    username = "admin"
    senha = "Admin@123"
    nome = "Administrador"

    usuario = User.query.filter_by(
        username=username
    ).first()

    if usuario:

        usuario.nome = nome
        usuario.ativo = True
        usuario.set_password(senha)

        print("Administrador atualizado com sucesso!")

    else:

        usuario = User(
            nome=nome,
            username=username,
            ativo=True
        )

        usuario.set_password(senha)

        db.session.add(usuario)

        print("Administrador criado com sucesso!")

    db.session.commit()

    print()
    print("======================================")
    print("ACESSO ADMINISTRATIVO")
    print("======================================")
    print(f"Usuário: {username}")
    print(f"Senha:   {senha}")
    print("======================================")