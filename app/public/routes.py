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
    AgendaDiaria,
    Agendamento,
    Informacao,
    DiaAtendimento,
    BloqueioData
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
# FUNÇÃO AUXILIAR - VAGAS DA AGENDA DIÁRIA
# ============================================================

def calcular_vagas_agenda(agenda):
    """
    Calcula as vagas restantes de uma agenda diária.

    Todos os agendamentos ocupam uma vaga,
    exceto os cancelados.
    """

    ocupadas = (
        Agendamento.query
        .filter(
            Agendamento.servico_id == agenda.servico_id,
            Agendamento.data == agenda.data,
            Agendamento.status != "cancelado"
        )
        .count()
    )

    vagas = agenda.capacidade - ocupadas

    return max(vagas, 0)

def data_bloqueada(servico_id, data):
    return (
        BloqueioData.query
        .filter_by(
            servico_id=servico_id,
            data=data,
            ativo=True
        )
        .first()
        is not None
    )    

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

        dia_atendimento = (
            DiaAtendimento.query
            .filter_by(
                servico_id=servico.id,
                dia_semana=data_atual.weekday(),
                ativo=True
            )
            .first()
        )

        fim_de_semana = (
            data_atual.weekday() >= 5
        )

        passado = (
            data_atual < hoje
        )

        agenda = (
            AgendaDiaria.query
            .filter_by(
                servico_id=servico.id,
                data=data_atual,
                ativo=True
            )
            .first()
        )

        vagas_disponiveis = 0

        if agenda:

            vagas_disponiveis = (
                calcular_vagas_agenda(
                    agenda
                )
            )

        bloqueada = data_bloqueada(
            servico.id,
            data_atual
        )    

        disponivel = (
            dia_atendimento is not None
            and not fim_de_semana
            and not passado
            and not bloqueada
            and agenda is not None
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
# AGENDAMENTO - AGENDA DO DIA
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

        if data_bloqueada(
            servico.id,
            data_agendamento
        ):
            flash(
                "Esta data está bloqueada para este serviço.",
                "warning"
            )
            return redirect(
                url_for(
                    "public.agendamento_data",
                    servico_id=servico.id
                )
            )

        dia_atendimento = (
            DiaAtendimento.query
            .filter_by(
                servico_id=servico.id,
                dia_semana=data_agendamento.weekday(),
                ativo=True
            )
            .first()
        )

        if dia_atendimento is None:
            flash(
                "Não há atendimento disponível para este serviço nesta data.",
                "warning"
            )
            return redirect(
                url_for(
                    "public.agendamento_data",
                    servico_id=servico.id
                )
            )   

    except ValueError:

        return "Data inválida", 400

        # ========================================================
    # BLOQUEIA FINAIS DE SEMANA
    # ========================================================

    if data_agendamento.weekday() >= 5:

        flash(
            "Não há atendimento aos sábados e domingos.",
            "warning"
        )

        return redirect(
            url_for(
                "public.agendamento_data",
                servico_id=servico.id
            )
        )    

    # ========================================================
    # LOCALIZA A AGENDA DO DIA
    # ========================================================

    agenda = (
        AgendaDiaria.query
        .filter_by(
            servico_id=servico.id,
            data=data_agendamento,
            ativo=True
        )
        .first()
    )

    if not agenda:

        return render_template(
            "public/agendamento_horarios.html",
            servico=servico,
            data=data_agendamento,
            agenda=None,
            vagas=0
        )

    # ========================================================
    # CALCULA VAGAS
    # ========================================================

    vagas = calcular_vagas_agenda(
        agenda
    )

    ocupadas = (
        agenda.capacidade
        - vagas
    )

    disponivel = (
        vagas > 0
    )

    # ========================================================
    # EXIBE AGENDA DO DIA
    # ========================================================

    return render_template(
        "public/agendamento_horarios.html",
        servico=servico,
        data=data_agendamento,
        agenda=agenda,
        vagas=vagas,
        ocupadas=ocupadas,
        disponivel=disponivel
    )

# ============================================================
# AGENDAMENTO - FORMULÁRIO
# ============================================================

@public_bp.route(
    "/agendamento/<int:servico_id>/data/<string:data>/agenda/<int:agenda_id>",
    methods=["GET", "POST"]
)
def agendamento_formulario(
    servico_id,
    data,
    agenda_id
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

        if data_bloqueada(
            servico.id,
            data_agendamento
        ):
            flash(
                "Esta data está bloqueada para este serviço.",
                "warning"
            )
            return redirect(
                url_for(
                    "public.agendamento_data",
                    servico_id=servico.id
                )
            )

        dia_atendimento = (
            DiaAtendimento.query
            .filter_by(
                servico_id=servico.id,
                dia_semana=data_agendamento.weekday(),
                ativo=True
            )
            .first()
        )

        if dia_atendimento is None:
            flash(
                "Não há atendimento disponível para este serviço nesta data.",
                "warning"
            )
            return redirect(
                url_for(
                    "public.agendamento_data",
                    servico_id=servico.id
                )
            )

    except ValueError:

        return "Data inválida", 400

        # ========================================================
    # BLOQUEIA FINAIS DE SEMANA
    # ========================================================

    if data_agendamento.weekday() >= 5:

        flash(
            "Não há atendimento aos sábados e domingos.",
            "warning"
        )

        return redirect(
            url_for(
                "public.agendamento_data",
                servico_id=servico.id
            )
        )    

    # ========================================================
    # LOCALIZA A AGENDA
    # ========================================================

    agenda = (
        AgendaDiaria.query
        .filter_by(
            id=agenda_id,
            servico_id=servico.id,
            data=data_agendamento,
            ativo=True
        )
        .first_or_404()
    )

    # ========================================================
    # FUNÇÃO AUXILIAR PARA RENDERIZAR O FORMULÁRIO
    # ========================================================

    def exibir_formulario(
        nome="",
        cpf="",
        telefone="",
        endereco="",
        classificacao="normal"
    ):

        vagas_restantes = calcular_vagas_agenda(
            agenda
        )

        return render_template(
            "public/agendamento_formulario.html",
            servico=servico,
            data=data_agendamento,
            agenda=agenda,
            nome=nome,
            cpf=cpf,
            telefone=telefone,
            endereco=endereco,
            classificacao=classificacao,
            vagas_restantes=vagas_restantes
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

        endereco = request.form.get(
            "endereco",
            ""
        ).strip()

        classificacao = request.form.get(
            "classificacao",
            "normal"
        ).strip().lower()

        sem_telefone = (
            request.form.get(
                "sem_telefone"
            ) == "1"
        )

        if sem_telefone:

            telefone = ""

        classificacoes_validas = {
            "normal",
            "idoso",
            "pcd",
            "gestante"
        }

        if classificacao not in classificacoes_validas:

            classificacao = "normal"

        # ----------------------------------------------------
        # VALIDA NOME
        # ----------------------------------------------------

        if not nome:

            flash(
                "Informe o nome completo.",
                "danger"
            )

            return exibir_formulario(
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                endereco=endereco,
                classificacao=classificacao
            )

        # ----------------------------------------------------
        # VALIDA CPF OBRIGATÓRIO
        # ----------------------------------------------------

        if not cpf:

            flash(
                "Informe o CPF.",
                "danger"
            )

            return exibir_formulario(
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                endereco=endereco,
                classificacao=classificacao
            )

        # ----------------------------------------------------
        # VALIDA CPF
        # ----------------------------------------------------

        if not validar_cpf(cpf):

            flash(
                "CPF inválido. Verifique os números informados.",
                "danger"
            )

            return exibir_formulario(
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                endereco=endereco,
                classificacao=classificacao
            )

        # ----------------------------------------------------
        # VALIDA TELEFONE
        # ----------------------------------------------------

        if telefone and not validar_telefone(telefone):

            flash(
                "Telefone inválido. Informe um telefone válido.",
                "danger"
            )

            return exibir_formulario(
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                endereco=endereco,
                classificacao=classificacao
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
                Agendamento.status.in_([
                    "agendado",
                    "nao_compareceu"
                ])
            )
            .first()
        )

        if agendamento_existente:

            flash(
                "Já existe um agendamento ativo para este CPF. "
                "Não é possível realizar outro agendamento "
                "enquanto o atendimento anterior estiver ativo.",
                "warning"
            )

            return exibir_formulario(
                nome=nome,
                cpf=cpf,
                telefone=telefone or "",
                endereco=endereco,
                classificacao=classificacao
            )

        # ----------------------------------------------------
        # VERIFICA CAPACIDADE
        # ----------------------------------------------------

        vagas_restantes = calcular_vagas_agenda(
            agenda
        )

        if vagas_restantes <= 0:

            flash(
                "Este dia acabou de ficar sem vagas. "
                "Escolha outra data.",
                "warning"
            )

            return redirect(
                url_for(
                    "public.agendamento_horarios",
                    servico_id=servico.id,
                    data=data_agendamento.strftime(
                        "%Y-%m-%d"
                    )
                )
            )

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
        # IMEDIATAMENTE ANTES DE CRIAR
        # ----------------------------------------------------

        vagas_disponiveis = calcular_vagas_agenda(
            agenda
        )

        if vagas_disponiveis <= 0:

            flash(
                "Este dia acabou de ficar sem vagas. "
                "Escolha outra data.",
                "warning"
            )

            return redirect(
                url_for(
                    "public.agendamento_horarios",
                    servico_id=servico.id,
                    data=data_agendamento.strftime(
                        "%Y-%m-%d"
                    )
                )
            )

        # ----------------------------------------------------
        # CRIA AGENDAMENTO
        # ----------------------------------------------------

        novo_agendamento = Agendamento(
            protocolo=protocolo,
            servico_id=servico.id,
            data=data_agendamento,

            # Mantemos o horário de início da agenda
            # para compatibilidade com o banco existente.
            horario=agenda.hora_inicio,

            nome=nome,
            cpf=cpf,
            telefone=telefone,
            endereco=endereco or None,
            classificacao=classificacao,
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

    vagas_restantes = calcular_vagas_agenda(
        agenda
    )

    if vagas_restantes <= 0:

        return (
            "Este dia não possui mais vagas."
        ), 409

    return exibir_formulario()

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