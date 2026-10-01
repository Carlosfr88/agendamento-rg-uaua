from datetime import datetime, date, time
import json

from sqlalchemy import text

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from ..extensions import db
from ..models import (
    User,
    Servico,
    HorarioDisponivel,
    Agendamento
)


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ============================================================
# DASHBOARD
# ============================================================

@admin_bp.route("/")
@login_required
def dashboard():

    # --------------------------------------------------------
    # SERVIÇOS PARA O FILTRO
    # --------------------------------------------------------

    servicos = (
        Servico.query
        .order_by(
            Servico.nome.asc()
        )
        .all()
    )

    # --------------------------------------------------------
    # FILTROS
    # --------------------------------------------------------

    protocolo = request.args.get(
        "protocolo",
        ""
    ).strip()

    cpf = request.args.get(
        "cpf",
        ""
    ).strip()

    servico_id = request.args.get(
        "servico_id",
        "",
        type=int
    )

    status = request.args.get(
        "status",
        ""
    ).strip()

    data_inicio = request.args.get(
        "data_inicio",
        ""
    ).strip()

    data_fim = request.args.get(
        "data_fim",
        ""
    ).strip()

    # --------------------------------------------------------
    # CONSULTA PRINCIPAL
    # --------------------------------------------------------

    query = Agendamento.query

    if protocolo:

        query = query.filter(
            Agendamento.protocolo.ilike(
                f"%{protocolo}%"
            )
        )

    if cpf:

        query = query.filter(
            Agendamento.cpf.ilike(
                f"%{cpf}%"
            )
        )

    if servico_id:

        query = query.filter(
            Agendamento.servico_id == servico_id
        )

    if status:

        query = query.filter(
            Agendamento.status == status
        )

    # --------------------------------------------------------
    # FILTRO DE DATA INICIAL
    # --------------------------------------------------------

    if data_inicio:

        try:

            data_inicio_obj = datetime.strptime(
                data_inicio,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                Agendamento.data >= data_inicio_obj
            )

        except ValueError:

            flash(
                "A data inicial informada é inválida.",
                "danger"
            )

            data_inicio = ""

    # --------------------------------------------------------
    # FILTRO DE DATA FINAL
    # --------------------------------------------------------

    if data_fim:

        try:

            data_fim_obj = datetime.strptime(
                data_fim,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                Agendamento.data <= data_fim_obj
            )

        except ValueError:

            flash(
                "A data final informada é inválida.",
                "danger"
            )

            data_fim = ""

    # --------------------------------------------------------
    # ORDENAÇÃO
    # --------------------------------------------------------

    agendamentos = (
        query
        .order_by(
            Agendamento.data.desc(),
            Agendamento.horario.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # TOTAL FILTRADO
    # --------------------------------------------------------

    total_filtrado = len(
        agendamentos
    )

    # --------------------------------------------------------
    # INDICADORES GERAIS
    # --------------------------------------------------------

    total = Agendamento.query.count()

    agendados = (
        Agendamento.query
        .filter_by(
            status="agendado"
        )
        .count()
    )

    atendidos = (
        Agendamento.query
        .filter_by(
            status="atendido"
        )
        .count()
    )

    cancelados = (
        Agendamento.query
        .filter_by(
            status="cancelado"
        )
        .count()
    )

    nao_compareceu = (
        Agendamento.query
        .filter_by(
            status="nao_compareceu"
        )
        .count()
    )

    # --------------------------------------------------------
    # INDICADORES DO DIA
    # --------------------------------------------------------

    hoje = date.today()

    hoje_total = (
        Agendamento.query
        .filter(
            Agendamento.data == hoje
        )
        .count()
    )

    hoje_atendidos = (
        Agendamento.query
        .filter(
            Agendamento.data == hoje,
            Agendamento.status == "atendido"
        )
        .count()
    )

    return render_template(
        "admin/dashboard.html",
        agendamentos=agendamentos,
        total=total,
        agendados=agendados,
        atendidos=atendidos,
        cancelados=cancelados,
        nao_compareceu=nao_compareceu,
        hoje_total=hoje_total,
        hoje_atendidos=hoje_atendidos,
        servicos=servicos,
        total_filtrado=total_filtrado,
        protocolo=protocolo,
        cpf=cpf,
        servico_id=servico_id,
        status=status,
        data_inicio=data_inicio,
        data_fim=data_fim
    )


# ============================================================
# ALTERAR STATUS DO AGENDAMENTO
# ============================================================

@admin_bp.route(
    "/agendamento/<int:agendamento_id>/status",
    methods=["POST"]
)
@login_required
def alterar_status(agendamento_id):

    agendamento = (
        Agendamento.query.get_or_404(
            agendamento_id
        )
    )

    novo_status = request.form.get(
        "status",
        ""
    ).strip()

    status_validos = [
        "agendado",
        "atendido",
        "cancelado",
        "nao_compareceu"
    ]

    if novo_status not in status_validos:

        flash(
            "Status inválido.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    status_atual = agendamento.status

    # --------------------------------------------------------
    # CANCELADO NÃO PODE SER REATIVADO
    # --------------------------------------------------------

    if (
        status_atual == "cancelado"
        and novo_status != "cancelado"
    ):

        flash(
            "Um agendamento cancelado não pode ser reativado.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # MESMO STATUS
    # --------------------------------------------------------

    if status_atual == novo_status:

        flash(
            "O agendamento já possui este status.",
            "warning"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # ATUALIZA STATUS
    # --------------------------------------------------------

    agendamento.status = novo_status

    db.session.commit()

    mensagens = {
        "agendado": (
            "Agendamento marcado como agendado."
        ),
        "atendido": (
            "Agendamento marcado como atendido."
        ),
        "cancelado": (
            "Agendamento cancelado com sucesso."
        ),
        "nao_compareceu": (
            "Agendamento marcado como não compareceu."
        )
    }

    flash(
        mensagens.get(
            novo_status,
            "Status atualizado com sucesso."
        ),
        "success"
    )

    return redirect(
        url_for(
            "admin.dashboard"
        )
    )


# ============================================================
# SERVIÇOS
# ============================================================

@admin_bp.route("/servicos")
@login_required
def servicos():

    servicos = (
        Servico.query
        .order_by(
            Servico.nome.asc()
        )
        .all()
    )

    return render_template(
        "admin/servicos.html",
        servicos=servicos
    )


# ============================================================
# NOVO SERVIÇO
# ============================================================

@admin_bp.route(
    "/servicos/novo",
    methods=["GET", "POST"]
)
@login_required
def novo_servico():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        if not nome:

            flash(
                "Informe o nome do serviço.",
                "danger"
            )

            return render_template(
                "admin/novo_servico.html"
            )

        existente = Servico.query.filter(
            db.func.lower(
                Servico.nome
            ) == nome.lower()
        ).first()

        if existente:

            flash(
                "Já existe um serviço com este nome.",
                "danger"
            )

            return render_template(
                "admin/novo_servico.html"
            )

        servico = Servico(
            nome=nome,
            descricao=descricao or None,
            ativo=True
        )

        db.session.add(
            servico
        )

        db.session.commit()

        flash(
            "Serviço criado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "admin.servicos"
            )
        )

    return render_template(
        "admin/novo_servico.html"
    )


# ============================================================
# EDITAR SERVIÇO
# ============================================================

@admin_bp.route(
    "/servicos/<int:servico_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar_servico(servico_id):

    servico = (
        Servico.query.get_or_404(
            servico_id
        )
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        if not nome:

            flash(
                "Informe o nome do serviço.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.editar_servico",
                    servico_id=servico.id
                )
            )

        existente = Servico.query.filter(
            db.func.lower(
                Servico.nome
            ) == nome.lower(),
            Servico.id != servico.id
        ).first()

        if existente:

            flash(
                "Já existe outro serviço com este nome.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.editar_servico",
                    servico_id=servico.id
                )
            )

        servico.nome = nome
        servico.descricao = (
            descricao or None
        )

        db.session.commit()

        flash(
            "Serviço atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "admin.servicos"
            )
        )

    return render_template(
        "admin/editar_servico.html",
        servico=servico
    )

# ============================================================
# ATIVAR / DESATIVAR SERVIÇO
# ============================================================

@admin_bp.route(
    "/servicos/<int:servico_id>/status",
    methods=["POST"]
)
@login_required
def alterar_status_servico(servico_id):

    servico = (
        Servico.query.get_or_404(
            servico_id
        )
    )

    servico.ativo = not servico.ativo

    db.session.commit()

    if servico.ativo:

        flash(
            "Serviço ativado com sucesso.",
            "success"
        )

    else:

        flash(
            "Serviço desativado com sucesso.",
            "success"
        )

    return redirect(
        url_for(
            "admin.servicos"
        )
    )    


# ============================================================
# ATIVAR / DESATIVAR ADMINISTRADOR
# ============================================================

@admin_bp.route(
    "/administradores/<int:usuario_id>/status",
    methods=["POST"]
)
@login_required
def alterar_status_administrador(usuario_id):

    usuario = User.query.get_or_404(
        usuario_id
    )

    # --------------------------------------------------------
    # IMPEDE O ADMINISTRADOR DE DESATIVAR A PRÓPRIA CONTA
    # --------------------------------------------------------

    if usuario.id == current_user.id:

        flash(
            "Você não pode desativar sua própria conta.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.administradores"
            )
        )

    usuario.ativo = not usuario.ativo

    db.session.commit()

    if usuario.ativo:

        flash(
            "Administrador ativado com sucesso.",
            "success"
        )

    else:

        flash(
            "Administrador desativado com sucesso.",
            "success"
        )

    return redirect(
        url_for(
            "admin.administradores"
        )
    )

# ============================================================
# HORÁRIOS DISPONÍVEIS
# ============================================================

@admin_bp.route("/horarios")
@login_required
def horarios():

    servico_id = request.args.get("servico_id", type=int)
    data_inicial = request.args.get("data_inicial", "").strip()
    data_final = request.args.get("data_final", "").strip()
    status = request.args.get("status", "").strip()

    query = HorarioDisponivel.query

    # Filtro por serviço
    if servico_id:
        query = query.filter(
            HorarioDisponivel.servico_id == servico_id
        )

    # Filtro por data inicial
    data_inicial_obj = None

    if data_inicial:
        try:
            data_inicial_obj = datetime.strptime(
                data_inicial,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                HorarioDisponivel.data >= data_inicial_obj
            )

        except ValueError:
            flash(
                "A data inicial informada é inválida.",
                "danger"
            )

    # Filtro por data final
    data_final_obj = None

    if data_final:
        try:
            data_final_obj = datetime.strptime(
                data_final,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                HorarioDisponivel.data <= data_final_obj
            )

        except ValueError:
            flash(
                "A data final informada é inválida.",
                "danger"
            )

    # Filtro por status
    if status == "ativo":
        query = query.filter(
            HorarioDisponivel.ativo.is_(True)
        )

    elif status == "inativo":
        query = query.filter(
            HorarioDisponivel.ativo.is_(False)
        )

    horarios = (
        query
        .order_by(
            HorarioDisponivel.data.asc(),
            HorarioDisponivel.hora.asc()
        )
        .all()
    )

    for horario in horarios:

        horario.ocupadas = Agendamento.query.filter(
            Agendamento.servico_id == horario.servico_id,
            Agendamento.data == horario.data,
            Agendamento.horario == horario.hora,
            Agendamento.status != "cancelado"
        ).count()

        horario.disponiveis = max(
            horario.capacidade - horario.ocupadas,
            0
        )

    servicos = (
        Servico.query
        .order_by(Servico.nome.asc())
        .all()
    )

    return render_template(
        "admin/horarios.html",
        horarios=horarios,
        servicos=servicos,
        filtro_servico_id=servico_id,
        filtro_data_inicial=data_inicial,
        filtro_data_final=data_final,
        filtro_status=status
    )

# ============================================================
# NOVO HORÁRIO
# ============================================================

@admin_bp.route(
    "/horarios/novo",
    methods=["GET", "POST"]
)
@login_required
def novo_horario():

    servicos = (
        Servico.query
        .order_by(
            Servico.nome.asc()
        )
        .all()
    )

    if request.method == "POST":

        servico_id = request.form.get(
            "servico_id",
            type=int
        )

        data = request.form.get(
            "data",
            ""
        ).strip()

        hora = request.form.get(
            "hora",
            ""
        ).strip()

        capacidade = request.form.get(
            "capacidade",
            type=int
        )

        if not servico_id:

            flash(
                "Selecione um serviço.",
                "danger"
            )

            return render_template(
                "admin/novo_horario.html",
                servicos=servicos
            )

        if not data:

            flash(
                "Informe a data.",
                "danger"
            )

            return render_template(
                "admin/novo_horario.html",
                servicos=servicos
            )

        if not hora:

            flash(
                "Informe o horário.",
                "danger"
            )

            return render_template(
                "admin/novo_horario.html",
                servicos=servicos
            )

        if not capacidade or capacidade < 1:

            flash(
                "A capacidade deve ser maior que zero.",
                "danger"
            )

            return render_template(
                "admin/novo_horario.html",
                servicos=servicos
            )

        try:

            data_obj = datetime.strptime(
                data,
                "%Y-%m-%d"
            ).date()

            hora_obj = datetime.strptime(
                hora,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Data ou horário inválido.",
                "danger"
            )

            return render_template(
                "admin/novo_horario.html",
                servicos=servicos
            )

        servico = Servico.query.get(
            servico_id
        )

        if not servico:

            flash(
                "Serviço não encontrado.",
                "danger"
            )

            return render_template(
                "admin/novo_horario.html",
                servicos=servicos
            )

        existente = (
            HorarioDisponivel.query
            .filter_by(
                servico_id=servico_id,
                data=data_obj,
                hora=hora_obj
            )
            .first()
        )

        if existente:

            flash(
                "Este horário já está cadastrado para este serviço.",
                "danger"
            )

            return render_template(
                "admin/novo_horario.html",
                servicos=servicos
            )

        horario = HorarioDisponivel(
            servico_id=servico_id,
            data=data_obj,
            hora=hora_obj,
            capacidade=capacidade,
            ativo=True
        )

        db.session.add(
            horario
        )

        db.session.commit()

        flash(
            "Horário cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "admin.horarios"
            )
        )

    return render_template(
        "admin/novo_horario.html",
        servicos=servicos
    )


# ============================================================
# EDITAR HORÁRIO
# ============================================================

@admin_bp.route(
    "/horarios/<int:horario_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar_horario(horario_id):

    horario = (
        HorarioDisponivel.query.get_or_404(
            horario_id
        )
    )

    servicos = (
        Servico.query
        .order_by(
            Servico.nome.asc()
        )
        .all()
    )

    if request.method == "POST":

        servico_id = request.form.get(
            "servico_id",
            type=int
        )

        data = request.form.get(
            "data",
            ""
        ).strip()

        hora = request.form.get(
            "hora",
            ""
        ).strip()

        capacidade = request.form.get(
            "capacidade",
            type=int
        )

        if not servico_id:

            flash(
                "Selecione um serviço.",
                "danger"
            )

            return render_template(
                "admin/editar_horario.html",
                horario=horario,
                servicos=servicos
            )

        if not data:

            flash(
                "Informe a data.",
                "danger"
            )

            return render_template(
                "admin/editar_horario.html",
                horario=horario,
                servicos=servicos
            )

        if not hora:

            flash(
                "Informe o horário.",
                "danger"
            )

            return render_template(
                "admin/editar_horario.html",
                horario=horario,
                servicos=servicos
            )

        if not capacidade or capacidade < 1:

            flash(
                "A capacidade deve ser maior que zero.",
                "danger"
            )

            return render_template(
                "admin/editar_horario.html",
                horario=horario,
                servicos=servicos
            )

        try:

            data_obj = datetime.strptime(
                data,
                "%Y-%m-%d"
            ).date()

            hora_obj = datetime.strptime(
                hora,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Data ou horário inválido.",
                "danger"
            )

            return render_template(
                "admin/editar_horario.html",
                horario=horario,
                servicos=servicos
            )

        servico = Servico.query.get(
            servico_id
        )

        if not servico:

            flash(
                "Serviço não encontrado.",
                "danger"
            )

            return render_template(
                "admin/editar_horario.html",
                horario=horario,
                servicos=servicos
            )

        existente = (
            HorarioDisponivel.query
            .filter(
                HorarioDisponivel.servico_id == servico_id,
                HorarioDisponivel.data == data_obj,
                HorarioDisponivel.hora == hora_obj,
                HorarioDisponivel.id != horario.id
            )
            .first()
        )

        if existente:

            flash(
                "Já existe outro horário com estes mesmos dados.",
                "danger"
            )

            return render_template(
                "admin/editar_horario.html",
                horario=horario,
                servicos=servicos
            )

        horario.servico_id = servico_id
        horario.data = data_obj
        horario.hora = hora_obj
        horario.capacidade = capacidade

        db.session.commit()

        flash(
            "Horário atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "admin.horarios"
            )
        )

    return render_template(
        "admin/editar_horario.html",
        horario=horario,
        servicos=servicos
    )


# ============================================================
# ATIVAR / DESATIVAR HORÁRIO
# ============================================================

@admin_bp.route(
    "/horarios/<int:horario_id>/status",
    methods=["POST"]
)
@login_required
def alterar_status_horario(horario_id):

    horario = (
        HorarioDisponivel.query.get_or_404(
            horario_id
        )
    )

    horario.ativo = not horario.ativo

    db.session.commit()

    if horario.ativo:

        flash(
            "Horário ativado com sucesso.",
            "success"
        )

    else:

        flash(
            "Horário desativado com sucesso.",
            "success"
        )

    return redirect(
        url_for(
            "admin.horarios"
        )
    )


# ============================================================
# ADMINISTRADORES
# ============================================================

@admin_bp.route("/administradores")
@login_required
def administradores():

    administradores = (
        User.query
        .order_by(
            User.nome.asc()
        )
        .all()
    )

    return render_template(
        "admin/administradores.html",
        administradores=administradores
    )

 
# ============================================================
# NOVO ADMINISTRADOR
# ============================================================

# ============================================================
# EDITAR ADMINISTRADOR
# ============================================================

@admin_bp.route(
    "/administradores/<int:usuario_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar_administrador(usuario_id):

    usuario = User.query.get_or_404(
        usuario_id
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        if not nome:

            flash(
                "Informe o nome.",
                "danger"
            )

            return render_template(
                "admin/editar_administrador.html",
                usuario=usuario
            )

        if not username:

            flash(
                "Informe o usuário.",
                "danger"
            )

            return render_template(
                "admin/editar_administrador.html",
                usuario=usuario
            )

        outro_usuario = (
            User.query
            .filter(
                User.username == username,
                User.id != usuario.id
            )
            .first()
        )

        if outro_usuario:

            flash(
                "Este usuário já está sendo utilizado.",
                "danger"
            )

            return render_template(
                "admin/editar_administrador.html",
                usuario=usuario
            )

        if password:

            if password != confirmar_senha:

                flash(
                    "As senhas não coincidem.",
                    "danger"
                )

                return render_template(
                    "admin/editar_administrador.html",
                    usuario=usuario
                )

            usuario.set_password(
                password
            )

        usuario.nome = nome
        usuario.username = username

        db.session.commit()

        flash(
            "Administrador atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "admin.administradores"
            )
        )

    return render_template(
        "admin/editar_administrador.html",
        usuario=usuario
    )


# ============================================================
# NOVO ADMINISTRADOR
# ============================================================

@admin_bp.route(
    "/administradores/novo",
    methods=["GET", "POST"]
)
@login_required
def novo_administrador():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        if not nome:
            flash(
                "Informe o nome.",
                "danger"
            )
            return render_template(
                "admin/novo_administrador.html"
            )

        if not username:
            flash(
                "Informe o usuário.",
                "danger"
            )
            return render_template(
                "admin/novo_administrador.html"
            )

        if not password:
            flash(
                "Informe a senha.",
                "danger"
            )
            return render_template(
                "admin/novo_administrador.html"
            )

        if password != confirmar_senha:
            flash(
                "As senhas não coincidem.",
                "danger"
            )
            return render_template(
                "admin/novo_administrador.html"
            )

        existente = User.query.filter_by(
            username=username
        ).first()

        if existente:
            flash(
                "Este usuário já existe.",
                "danger"
            )
            return render_template(
                "admin/novo_administrador.html"
            )

        administrador = User(
            nome=nome,
            username=username,
            ativo=True
        )

        administrador.set_password(password)

        db.session.add(administrador)
        db.session.commit()

        flash(
            "Administrador criado com sucesso.",
            "success"
        )

        return redirect(
            url_for(
                "admin.administradores"
            )
        )

    return render_template(
        "admin/novo_administrador.html"
    )
# ============================================================
# IMPORTAÇÃO TEMPORÁRIA DOS DADOS
# ============================================================

@admin_bp.route(
    "/importar-dados",
    methods=["GET", "POST"]
)
@login_required
def importar_dados():

    if request.method == "GET":

        return render_template(
            "admin/importar_dados.html"
        )

    arquivo = request.files.get("arquivo")

    if not arquivo:

        flash(
            "Selecione o arquivo de migração.",
            "danger"
        )

        return redirect(
            url_for("admin.importar_dados")
        )

    if not arquivo.filename.lower().endswith(".json"):

        flash(
            "O arquivo deve estar no formato JSON.",
            "danger"
        )

        return redirect(
            url_for("admin.importar_dados")
        )

    try:

        conteudo = arquivo.read().decode("utf-8")
        dados = json.loads(conteudo)

    except Exception:

        flash(
            "Não foi possível ler o arquivo JSON.",
            "danger"
        )

        return redirect(
            url_for("admin.importar_dados")
        )

    chaves_obrigatorias = {
        "usuarios",
        "servicos",
        "horarios",
        "agendamentos"
    }

    if not chaves_obrigatorias.issubset(dados.keys()):

        flash(
            "O arquivo não possui a estrutura esperada.",
            "danger"
        )

        return redirect(
            url_for("admin.importar_dados")
        )

    try:

        usuarios = dados["usuarios"]
        servicos = dados["servicos"]
        horarios = dados["horarios"]
        agendamentos = dados["agendamentos"]

        # ====================================================
        # SERVIÇOS
        # ====================================================

        servicos_importados = 0

        for item in servicos:

            existente = Servico.query.filter(
                db.func.lower(Servico.nome)
                == item["nome"].lower()
            ).first()

            if existente:
                continue

            servico = Servico(
                id=item["id"],
                nome=item["nome"],
                descricao=item.get("descricao"),
                ativo=item.get("ativo", True)
            )

            db.session.add(servico)
            servicos_importados += 1

        db.session.flush()

        # ====================================================
        # USUÁRIOS
        # ====================================================

        usuarios_importados = 0

        for item in usuarios:

            existente = User.query.filter_by(
                username=item["username"]
            ).first()

            if existente:
                continue

            usuario = User(
                nome=item["nome"],
                username=item["username"],
                password_hash=item["password_hash"],
                ativo=item.get("ativo", True)
            )

            db.session.add(usuario)
            usuarios_importados += 1

        db.session.flush()

        # ====================================================
        # HORÁRIOS
        # ====================================================

        horarios_importados = 0

        for item in horarios:

            existente = (
                HorarioDisponivel.query
                .filter_by(
                    servico_id=item["servico_id"],
                    data=date.fromisoformat(item["data"]),
                    hora=time.fromisoformat(item["hora"])
                )
                .first()
            )

            if existente:
                continue

            horario = HorarioDisponivel(
                id=item["id"],
                servico_id=item["servico_id"],
                data=date.fromisoformat(item["data"]),
                hora=time.fromisoformat(item["hora"]),
                capacidade=item["capacidade"],
                ativo=item.get("ativo", True)
            )

            db.session.add(horario)
            horarios_importados += 1

        db.session.flush()

        # ====================================================
        # AGENDAMENTOS
        # ====================================================

        agendamentos_importados = 0

        for item in agendamentos:

            existente = Agendamento.query.filter_by(
                protocolo=item["protocolo"]
            ).first()

            if existente:
                continue

            criado_em = item.get("criado_em")

            if criado_em:
                criado_em = datetime.fromisoformat(
                    criado_em
                )

            dados_agendamento = {
                "id": item["id"],
                "protocolo": item["protocolo"],
                "servico_id": item["servico_id"],
                "data": date.fromisoformat(
                    item["data"]
                ),
                "horario": time.fromisoformat(
                    item["horario"]
                ),
                "nome": item["nome"],
                "cpf": item["cpf"],
                "telefone": item.get("telefone"),
                "status": item.get(
                    "status",
                    "agendado"
                )
            }

            if criado_em:
                dados_agendamento["criado_em"] = criado_em

            agendamento = Agendamento(
                **dados_agendamento
            )

            db.session.add(agendamento)
            agendamentos_importados += 1

        db.session.flush()

        # ====================================================
        # CORRIGE SEQUÊNCIAS DO POSTGRESQL
        # ====================================================

        if db.engine.dialect.name == "postgresql":

            tabelas = [
                "users",
                "servicos",
                "horarios_disponiveis",
                "agendamentos"
            ]

            for tabela in tabelas:

                db.session.execute(
                    text(
                        f"""
                        SELECT setval(
                            pg_get_serial_sequence(
                                '{tabela}',
                                'id'
                            ),
                            COALESCE(
                                (
                                    SELECT MAX(id)
                                    FROM {tabela}
                                ),
                                1
                            ),
                            (
                                SELECT COUNT(*) > 0
                                FROM {tabela}
                            )
                        )
                        """
                    )
                )

        # ====================================================
        # CONFIRMA TUDO
        # ====================================================

        db.session.commit()

        flash(
            "Migração concluída com sucesso.",
            "success"
        )

        return render_template(
            "admin/importar_dados.html",
            concluido=True,
            total_usuarios=usuarios_importados,
            total_servicos=servicos_importados,
            total_horarios=horarios_importados,
            total_agendamentos=agendamentos_importados
        )

    except Exception as erro:

        db.session.rollback()

        print(
            "ERRO NA IMPORTAÇÃO:",
            erro
        )

        flash(
            "A importação falhou. Nenhum dado da operação foi gravado.",
            "danger"
        )

        return redirect(
            url_for("admin.importar_dados")
        )

@admin_bp.route("/diagnostico-banco")
@login_required
def diagnostico_banco():

    return {
        "usuarios": User.query.count(),
        "servicos": Servico.query.count(),
        "horarios": HorarioDisponivel.query.count(),
        "agendamentos": Agendamento.query.count()
    }            