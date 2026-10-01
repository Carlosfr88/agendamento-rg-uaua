# Agendamento Eletrônico de RG — SEDES Uauá

Sistema web responsivo para agendamento eletrônico do setor de RG da Secretaria de Desenvolvimento Social e Combate à Pobreza — Prefeitura Municipal de Uauá.

## Etapa 1

Nesta etapa foi criada a fundação do projeto:

- Flask com padrão Application Factory;
- banco inicial SQLite para desenvolvimento;
- SQLAlchemy;
- Flask-Login;
- estrutura modular;
- tela pública inicial;
- tela de login dos servidores;
- identidade visual inicial;
- preparação para PostgreSQL e hospedagem online;
- estrutura separada para administração, agendamento e atendimento.

## Instalação no Windows

```cmd
cd /d E:\agendamento-rg-uaua
py -3.13 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Acesse:

http://127.0.0.1:5000

## Próxima etapa

A Etapa 2 deverá criar o modelo completo de banco de dados, usuários/perfis e regras de agenda.
