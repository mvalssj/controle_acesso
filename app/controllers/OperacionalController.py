from flask import Blueprint, render_template, request, redirect, url_for
from app.models import db, Evento, Programacao, Unidade

class OperacionalController:
    def __init__(self):
        self.blueprint = Blueprint('operacional', __name__)

        # Rota para listar todos os eventos e programações
        @self.blueprint.route('/operacional')
        def operacional():
            # Renderiza a página de operacional, passando a lista de eventos e programações como contexto
            # Obtenha a programação do banco de dados ou de outra fonte
            programacao = Programacao.query.all()
            unidades = Unidade.query.all()
            return render_template('operacional.html', programacao=programacao, unidades=unidades)
        
        # Rota para listar todos os eventos e programações
        @self.blueprint.route('/operacional_balanca')
        def operacional_balanca():
            # Renderiza a página de operacional, passando a lista de eventos e programações como contexto
            # Obtenha a programação do banco de dados ou de outra fonte
            programacao = Programacao.query.all()
            unidades = Unidade.query.all()
            return render_template('operacional_balanca.html', programacao=programacao, unidades=unidades)