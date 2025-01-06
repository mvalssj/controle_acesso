from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import Unidade, LocalAcesso, db
from app.extensions import csrf  # Agora importa do extensions.py

class LocalAcessoController:
    def __init__(self):
        self.blueprint = Blueprint('local_acesso', __name__)

        # Rota para listar todos os locais de acesso
        @self.blueprint.route('/locais_acesso')
        def locais_acesso():
            # Obtém todos os locais de acesso do banco de dados
            locais_acesso = LocalAcesso.query.all()
            # Obtém todas as unidades do banco de dados
            unidades = Unidade.query.all()
            # Renderiza a página de locais de acesso, passando a lista de locais de acesso como contexto
            return render_template('locais_acesso.html', locais_acesso=locais_acesso, unidades=unidades)

        # Rota para inserir um novo local de acesso
        @self.blueprint.route('/locais_acesso/novo', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def novo_local_acesso():
            # Obtém os dados do formulário
            nome = request.form.get('nome')
            id_unidade = request.form.get('unidade')
            descricao = request.form.get('descricao')    

            # Cria um novo objeto LocalAcesso
            novo_local_acesso = LocalAcesso(nome=nome, id_unidade=id_unidade, descricao=descricao)

            # Adiciona o novo local de acesso ao banco de dados
            db.session.add(novo_local_acesso)
            db.session.flush() # Necessário para obter o ID antes do commit
            new_id = novo_local_acesso.id
            db.session.commit()

            return jsonify({"id": new_id}) # Retorna o ID como JSON

        # Rota para atualizar um local de acesso
        @self.blueprint.route('/locais_acesso/<int:id>/editar', methods=['GET', 'POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def editar_local_acesso(id):
            # Obtém o local de acesso a ser editado
            local_acesso = LocalAcesso.query.get_or_404(id)

            # Se o método for POST, atualiza o local de acesso
            if request.method == 'POST':
                # Obtém os dados do formulário
                nome = request.form.get('nome')
                unidade = request.form.get('unidade')
                descricao = request.form.get('descricao')

                # Atualiza os dados do local de acesso
                local_acesso.nome = nome
                local_acesso.id_unidade = unidade
                local_acesso.descricao = descricao

                # Salva as alterações no banco de dados
                db.session.commit()

                # Redireciona para a página de locais de acesso
                return redirect(url_for('local_acesso.locais_acesso'))

            # Se o método for GET, renderiza a página de edição
            return render_template('locais_acesso.html', local_acesso=local_acesso, unidades=Unidade.query.all())

        # Rota para apagar um local de acesso
        @self.blueprint.route('/locais_acesso/<int:id>/apagar', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def apagar_local_acesso(id):
            # Obtém o local de acesso a ser apagado
            local_acesso = LocalAcesso.query.get_or_404(id)

            # Remove o local de acesso do banco de dados
            db.session.delete(local_acesso)
            db.session.commit()

            # Redireciona para a página de locais de acesso após a exclusão
            return redirect(url_for('local_acesso.locais_acesso'))

        # Rota para obter os locais de acesso relacionados a uma unidade
        @self.blueprint.route('/locais_acesso/unidade/<int:id_unidade>')
        def locais_acesso_unidade(id_unidade):
            # Obtém os locais de acesso relacionados à unidade
            locais_acesso = LocalAcesso.query.filter_by(id_unidade=id_unidade).all()

            # Retorna os locais de acesso em formato JSON
            return jsonify([{'id': local_acesso.id, 'nome': local_acesso.nome, 'descricao': local_acesso.descricao} for local_acesso in locais_acesso])