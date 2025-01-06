from flask import Blueprint, render_template, request, redirect, url_for
from app.models import Unidade, db
from app.extensions import csrf  # Agora importa do extensions.py

class UnidadeController:
    def __init__(self):
        self.blueprint = Blueprint('unidade', __name__)

        # Rota para listar todos os unidades
        @self.blueprint.route('/unidades')
        def unidades():
            # Obtém todos os unidades do banco de dados
            unidades = Unidade.query.all()
            # Renderiza a página de unidades, passando a lista de unidades como contexto
            return render_template('unidades.html', unidades=unidades)
        
        # Rota para inserir um novo unidades
        @self.blueprint.route('/unidades/novo', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def nova_unidade():
            # Obtém os dados do formulário
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')    

            # Cria um novo objeto Unidade
            nova_unidade = Unidade(nome=nome, descricao=descricao)

            # Adiciona o novo equipamento ao banco de dados
            db.session.add(nova_unidade)
            db.session.commit()

            # Redireciona para a página de unidades
            return redirect(url_for('unidade.unidades'))

        # Rota para atualizar um unidade
        @self.blueprint.route('/unidades/<int:id>/editar', methods=['GET', 'POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def editar_unidade(id):
            # Obtém o unidade a ser editado
            unidade = Unidade.query.get_or_404(id)

            # Se o método for POST, atualiza o unidade
            if request.method == 'POST':
                # Obtém os dados do formulário
                nome = request.form.get('nome')
                descricao = request.form.get('descricao')

                # Atualiza os dados do unidade
                unidade.nome = nome
                unidade.descricao = descricao

                # Salva as alterações no banco de dados
                db.session.commit()

                # Redireciona para a página de unidades
                return redirect(url_for('unidade.unidades'))

            # Se o método for GET, renderiza a página de edição
            return render_template('editar_unidade.html', unidade=unidade)

        # Rota para apagar um unidade
        @self.blueprint.route('/unidades/<int:id>/apagar', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def apagar_unidade(id):
            # Obtém o unidade a ser apagado
            unidade = Unidade.query.get_or_404(id)

            # Remove o unidade do banco de dados
            db.session.delete(unidade)
            db.session.commit()

            # Redireciona para a página de unidades após a exclusão
            return redirect(url_for('unidade.unidades'))