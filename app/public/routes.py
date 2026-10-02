from calendar import monthrange
from datetime import date
import secrets

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from ..extensions import db
from ..models import (
    Servico,
    HorarioDisponivel,
    Agendamento,
    Informacao
)


public_bp = Blueprint(
    "public",
    __name__
)


def limpar_documento(valor):
    """Remove caracteres não numéricos."""
    return "".join(
        caractere
        for caractere in valor
        if caractere.isdigit()
    )


def validar_cpf(cpf):
    """Valida CPF pelos dígitos verificadores."""
    cpf = limpar_documento(cpf)

    if len(cpf) != 11:
        return False

    # Rejeita CPFs com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False

    # Primeiro dígito verificador
    soma = sum(
        int(cpf[i]) * (10 - i)
        for i in range(9)
    )

    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        return False

    # Segundo dígito verificador
    soma = sum(
        int(cpf[i]) * (11 - i)
        for i in range(10)
    )

    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    if int(cpf[10]) != digito2:
        return False

    return True


def formatar_cpf(cpf):
    """Padroniza CPF para 000.000.000-00."""
    cpf = limpar_documento(cpf)

    if len(cpf) != 11:
        return cpf

    return (
        f"{cpf[:3]}."
        f"{cpf[3:6]}."
        f"{cpf[6:9]}-"
        f"{cpf[9:]}"
    )


def validar_telefone(telefone):
    """Valida telefone brasileiro com 10 ou 11 dígitos."""
    telefone = limpar_documento(telefone)

    if len(telefone) not in (10, 11):
        return False

    # Rejeita números formados por um único dígito repetido
    if telefone == telefone[0] * len(telefone):
        return False

    # DDD deve estar entre 11 e 99
    ddd = int(telefone[:2])

    if ddd < 11 or ddd > 99:
        return False

    return True


def formatar_telefone(telefone):
    """Padroniza telefone brasileiro."""
    telefone = limpar_documento(telefone)

    if len(telefone) == 11:
        return (
            f"({telefone[:2]}) "
            f"{telefone[2:7]}-"
            f"{telefone[7:]}"
        )

    if len(telefone) == 10:
        return (
            f"({telefone[:2]}) "
            f"{telefone[2:6]}-"
            f"{telefone[6:]}"
        )

    return telefone

# ============================================================
# FUNÇÃO AUXILIAR - VAGAS
# ============================================================

def calcular_vagas(horario):
    """
    Calcula a quantidade de vagas restantes.

    Todos os agendamentos ocupam vaga, exceto os cancelados.
    """

    ocupadas = Agendamento.query.filter(
        Agendamento.servico_id == horario.servico_id,
        Agendamento.data == horario.data,
        Agendamento.horario == horario.hora,
        Agendamento.status != "cancelado"
    ).count()

    vagas = horario.capacidade - ocupadas

    return max(vagas, 0)


# ============================================================
# PÁGINA INICIAL
# ============================================================

@public_bp.route("/")
def index():

    return render_template(
        "public/index.html"
    )


# ============================================================
# AGENDAMENTO - SERVIÇOS
# ============================================================

@public_bp.route("/agendamento")
def agendamento():

    servicos = (
        Servico.query
        .filter_by(ativo=True)
        .order_by(Servico.nome.asc())
        .all()
    )

    return render_template(
        "public/agendamento.html",
        servicos=servicos
    )


# ============================================================
# AGENDAMENTO - CALENDÁRIO
# ============================================================

@public_bp.route(
    "/agendamento/<int:servico_id>/data"
)
def agendamento_data(servico_id):

    # Somente serviços ativos podem receber novos agendamentos
    servico = (
        Servico.query
        .filter_by(
            id=servico_id,
            ativo=True
        )
        .first_or_404()
    )

    hoje = date.today()

    try:

        mes = int(
            request.args.get(
                "mes",
                hoje.month
            )
        )

        ano = int(
            request.args.get(
                "ano",
                hoje.year
            )
        )

    except (TypeError, ValueError):

        mes = hoje.month
        ano = hoje.year

    if mes < 1:

        mes = 12
        ano -= 1

    if mes > 12:

        mes = 1
        ano += 1

    primeiro_dia = date(
        ano,
        mes,
        1
    )

    total_dias = monthrange(
        ano,
        mes
    )[1]

    dias = []

    for numero in range(
        1,
        total_dias + 1
    ):

        data_atual = date(
            ano,
            mes,
            numero
        )

        fim_de_semana = (
            data_atual.weekday() >= 5
        )

        passado = (
            data_atual < hoje
        )

        horarios = (
            HorarioDisponivel.query
            .filter_by(
                servico_id=servico.id,
                data=data_atual,
                ativo=True
            )
            .order_by(
                HorarioDisponivel.hora.asc()
            )
            .all()
        )

        vagas_disponiveis = 0

        for horario in horarios:

            vagas = calcular_vagas(
                horario
            )

            vagas_disponiveis += vagas

        disponivel = (
            not fim_de_semana
            and not passado
            and vagas_disponiveis > 0
        )

        dias.append({
            "numero": numero,
            "data": data_atual,
            "disponivel": disponivel,
            "hoje": data_atual == hoje,
            "vagas": vagas_disponiveis
        })

    primeiro_weekday = (
        primeiro_dia.weekday()
    )

    return render_template(
        "public/agendamento_data.html",
        servico=servico,
        dias=dias,
        mes=mes,
        ano=ano,
        primeiro_weekday=primeiro_weekday
    )


# ============================================================
# AGENDAMENTO - HORÁRIOS
# ============================================================

@public_bp.route(
    "/agendamento/<int:servico_id>/data/<string:data>/horarios"
)
def agendamento_horarios(
    servico_id,
    data
):

    # Somente serviços ativos podem receber novos agendamentos
    servico = (
        Servico.query
        .filter_by(
            id=servico_id,
            ativo=True
        )
        .first_or_404()
    )

    try:

        data_agendamento = date.fromisoformat(
            data
        )

    except ValueError:

        return "Data inválida", 400

    horarios = (
        HorarioDisponivel.query
        .filter_by(
            servico_id=servico.id,
            data=data_agendamento,
            ativo=True
        )
        .order_by(
            HorarioDisponivel.hora.asc()
        )
        .all()
    )

    horarios_disponiveis = []

    for horario in horarios:

        vagas_restantes = calcular_vagas(
            horario
        )

        ocupadas = (
            horario.capacidade
            - vagas_restantes
        )

        horarios_disponiveis.append({
            "id": horario.id,
            "hora": horario.hora,
            "capacidade": horario.capacidade,
            "ocupadas": ocupadas,
            "vagas": vagas_restantes,
            "disponivel": vagas_restantes > 0
        })

    return render_template(
        "public/agendamento_horarios.html",
        servico=servico,
        data=data_agendamento,
        horarios=horarios_disponiveis
    )

# ============================================================
# AGENDAMENTO - FORMULÁRIO
# ============================================================

@public_bp.route(
    "/agendamento/<int:servico_id>/data/<string:data>/horario/<int:horario_id>",
    methods=["GET", "POST"]
)
def agendamento_formulario(
    servico_id,
    data,
    horario_id
):

    # Somente serviços ativos podem receber novos agendamentos
    servico = (
        Servico.query
        .filter_by(
            id=servico_id,
            ativo=True
        )
        .first_or_404()
    )

    try:

        data_agendamento = date.fromisoformat(
            data
        )

    except ValueError:

        return "Data inválida", 400

    horario = (
        HorarioDisponivel.query
        .filter_by(
            id=horario_id,
            servico_id=servico.id,
            data=data_agendamento,
            ativo=True
        )
        .first_or_404()
    )

    # ========================================================
    # PROCESSAMENTO DO AGENDAMENTO
    # ========================================================

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        cpf = request.form.get(
            "cpf",
            ""
        ).strip()

        telefone = request.form.get(
            "telefone",
            ""
        ).strip()

        # ----------------------------------------------------
        # VALIDA NOME
        # ----------------------------------------------------

        if not nome:

            flash(
                "Informe o nome completo.",
                "danger"
            )

            return render_template(
                "public/agendamento_formulario.html",
                servico=servico,
                data=data_agendamento,
                horario=horario,
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                vagas_restantes=calcular_vagas(horario)
            )

        # ----------------------------------------------------
        # VALIDA CPF OBRIGATÓRIO
        # ----------------------------------------------------

        if not cpf:

            flash(
                "Informe o CPF.",
                "danger"
            )

            return render_template(
                "public/agendamento_formulario.html",
                servico=servico,
                data=data_agendamento,
                horario=horario,
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                vagas_restantes=calcular_vagas(horario)
            )

        # ----------------------------------------------------
        # VALIDA CPF
        # ----------------------------------------------------

        if not validar_cpf(cpf):

            flash(
                "CPF inválido. Verifique os números informados.",
                "danger"
            )

            return render_template(
                "public/agendamento_formulario.html",
                servico=servico,
                data=data_agendamento,
                horario=horario,
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                vagas_restantes=calcular_vagas(horario)
            )

        # ----------------------------------------------------
        # VALIDA TELEFONE
        # ----------------------------------------------------

        if telefone and not validar_telefone(telefone):

            flash(
                "Telefone inválido. Informe um telefone válido.",
                "danger"
            )

            return render_template(
                "public/agendamento_formulario.html",
                servico=servico,
                data=data_agendamento,
                horario=horario,
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                vagas_restantes=calcular_vagas(horario)
            )

        # ----------------------------------------------------
        # FORMATA DADOS
        # ----------------------------------------------------

        cpf = formatar_cpf(cpf)

        if telefone:

            telefone = formatar_telefone(
                telefone
            )

        else:

            telefone = None

                # ----------------------------------------------------
        # VERIFICA AGENDAMENTO DUPLICADO
        # ----------------------------------------------------

        agendamento_existente = (
            Agendamento.query
            .filter(
                Agendamento.cpf == cpf,
                Agendamento.servico_id == servico.id,
                Agendamento.data == data_agendamento,
                Agendamento.status != "cancelado"
            )
            .first()
        )

        if agendamento_existente:

            flash(
                "Já existe um agendamento para este CPF "
                "neste serviço e nesta data.",
                "warning"
            )

            return render_template(
                "public/agendamento_formulario.html",
                servico=servico,
                data=data_agendamento,
                horario=horario,
                nome=nome,
                cpf=cpf,
                telefone=telefone or "",
                vagas_restantes=calcular_vagas(horario)
            )    

        # ----------------------------------------------------
        # VERIFICA NOVAMENTE A CAPACIDADE
        # ----------------------------------------------------

        vagas_restantes = calcular_vagas(
            horario
        )

        if vagas_restantes <= 0:

            return (
                "Este horário acabou de ficar sem vagas. "
                "Escolha outro horário."
            ), 409

        # ----------------------------------------------------
        # GERA PROTOCOLO ÚNICO
        # ----------------------------------------------------

        while True:

            protocolo = (
                "UAUA-"
                + date.today().strftime("%Y%m%d")
                + "-"
                + secrets.token_hex(3).upper()
            )

            existente = (
                Agendamento.query
                .filter_by(
                    protocolo=protocolo
                )
                .first()
            )

            if not existente:

                break

            # ----------------------------------------------------
        # VERIFICA NOVAMENTE A DISPONIBILIDADE
        # IMEDIATAMENTE ANTES DE CRIAR O AGENDAMENTO
        # ----------------------------------------------------

        vagas_disponiveis = calcular_vagas(
            horario
        )

        if vagas_disponiveis <= 0:

            flash(
                "Este horário acabou de ficar sem vagas. "
                "Escolha outro horário.",
                "warning"
            )

            return redirect(
                url_for(
                    "public.agendamento_formulario",
                    servico_id=servico.id,
                    data=data_agendamento.strftime("%Y-%m-%d"),
                    horario_id=horario.id
                )
            )

        # ----------------------------------------------------
        # CRIA AGENDAMENTO
        # ----------------------------------------------------

        novo_agendamento = Agendamento(
            protocolo=protocolo,
            servico_id=servico.id,
            data=data_agendamento,
            horario=horario.hora,
            nome=nome,
            cpf=cpf,
            telefone=telefone,
            status="agendado"
        )

        db.session.add(
            novo_agendamento
        )

        db.session.commit()

        return render_template(
            "public/agendamento_sucesso.html",
            agendamento=novo_agendamento
        )    

    # ========================================================
    # VERIFICA DISPONIBILIDADE PARA EXIBIÇÃO
    # ========================================================

    vagas_restantes = calcular_vagas(
        horario
    )

    if vagas_restantes <= 0:

        return (
            "Este horário não possui mais vagas."
        ), 409

    return render_template(
        "public/agendamento_formulario.html",
        servico=servico,
        data=data_agendamento,
        horario=horario,
        vagas_restantes=vagas_restantes
    )

@public_bp.route("/informacoes")
def informacoes():

    informacoes = (
        Informacao.query
        .filter_by(ativo=True)
        .order_by(
            Informacao.ordem.asc(),
            Informacao.id.asc()
        )
        .all()
    )

    return render_template(
        "public/informacoes.html",
        informacoes=informacoes
    )
    
# ============================================================
# CONSULTAR AGENDAMENTO
# ============================================================

@public_bp.route(
    "/consultar-agendamento",
    methods=["GET", "POST"]
)
def consultar_agendamento():

    agendamento = None
    erro = None

    if request.method == "POST":

        protocolo = request.form.get(
            "protocolo",
            ""
        ).strip().upper()

        cpf = request.form.get(
            "cpf",
            ""
        ).strip()

        cpf = formatar_cpf(cpf)

        if not protocolo or not cpf:

            erro = (
                "Informe o protocolo e o CPF."
            )

        else:

            agendamento = (
                Agendamento.query
                .filter_by(
                    protocolo=protocolo,
                    cpf=cpf
                )
                .first()
            )

            if not agendamento:

                erro = (
                    "Não encontramos um agendamento "
                    "com os dados informados."
                )

    return render_template(
        "public/consultar_agendamento.html",
        agendamento=agendamento,
        erro=erro
    )


# ============================================================
# CANCELAR AGENDAMENTO
# ============================================================

@public_bp.route(
    "/cancelar-agendamento/<int:agendamento_id>",
    methods=["POST"]
)
def cancelar_agendamento(agendamento_id):

    agendamento = Agendamento.query.get_or_404(
        agendamento_id
    )

    # ========================================================
    # CONFIRMAÇÃO DE SEGURANÇA
    # ========================================================

    protocolo = request.form.get(
        "protocolo",
        ""
    ).strip().upper()

    cpf = request.form.get(
        "cpf",
        ""
    ).strip()

    if (
        protocolo != agendamento.protocolo
        or cpf != agendamento.cpf
    ):

        return (
            "Não foi possível validar os dados "
            "do agendamento."
        ), 403

    # ========================================================
    # VERIFICA O STATUS ATUAL
    # ========================================================

    if agendamento.status == "cancelado":

        return redirect(
            url_for(
                "public.consultar_agendamento"
            )
        )

    if agendamento.status != "agendado":

        return (
            "Este agendamento não pode mais ser cancelado."
        ), 409

    # ========================================================
    # CANCELA SEM EXCLUIR O REGISTRO
    # ========================================================

    agendamento.status = "cancelado"

    db.session.commit()

    return render_template(
        "public/cancelamento_sucesso.html",
        agendamento=agendamento
    )