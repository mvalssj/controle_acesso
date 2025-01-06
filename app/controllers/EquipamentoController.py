from flask import Blueprint, render_template, request, redirect, url_for
from app.models import Equipamento, EquipamentoTipo, Unidade, LocalAcesso, db
from app.extensions import csrf  # Agora importa do extensions.py

class EquipamentoController:
    
    # Pega o ip dos equipamentos
    def get_equipamento_id(self, id_entidade_proprietaria):
        # Consulta os equipamentos, separando por direção
        equipamentos = Equipamento.query.all()
        ips_entrada = []
        ips_saida = []
        for equipamento in equipamentos:
            if equipamento.direcao == 'IN':
                ips_entrada.append(equipamento.ip)
            elif equipamento.direcao == 'OUT':
                ips_saida.append(equipamento.ip)

        return ips_entrada, ips_saida # Retorna duas listas
    
    def __init__(self):
        self.blueprint = Blueprint('equipamento', __name__)

        # Rota para listar todos os equipamentos
        @self.blueprint.route('/equipamentos')
        def equipamentos():
            # Obtém todos os equipamentos do banco de dados
            equipamentos = Equipamento.query.all()
            equipamentos_tipo = EquipamentoTipo.query.all()
            unidades = Unidade.query.all()
            local_acesso = LocalAcesso.query.all()
            # exit(equipamentos)
            # Renderiza a página de equipamentos, passando a lista de equipamentos como contexto
            return render_template('equipamentos.html', equipamentos=equipamentos, equipamentos_tipo=equipamentos_tipo, unidades=unidades, local_acesso=local_acesso)

        # Rota para inserir um novo equipamento
        @self.blueprint.route('/equipamentos/novo', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def novo_equipamento():
            # Obtém os dados do formulário
            nome = request.form.get('nome')
            id_local_acesso = request.form.get('local')    
            tipo = request.form.get('tipo')
            direcao = request.form.get('direcao')
            ip = request.form.get('ip')

            # Cria um novo objeto Equipamento
            novo_equipamento = Equipamento(nome=nome, id_equipamento_tipo=tipo, id_local_acesso=id_local_acesso, direcao=direcao, ip=ip)

            # Busca o tipo de equipamento no banco de dados
            tipo_equipamento = EquipamentoTipo.query.filter_by(nome=tipo).first()

            # Se o tipo de equipamento for encontrado, associa ao novo equipamento
            if tipo_equipamento:
                novo_equipamento.id_equipamento_tipo = tipo_equipamento.id

            # Adiciona o novo equipamento ao banco de dados
            db.session.add(novo_equipamento)
            db.session.commit()

            # Redireciona para a página de equipamentos
            return redirect(url_for('equipamento.equipamentos'))

        # Rota para atualizar um equipamento
        @self.blueprint.route('/equipamentos/<int:id>/editar', methods=['GET', 'POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def editar_equipamento(id):
            # Obtém o equipamento a ser editado
            equipamento = Equipamento.query.get_or_404(id)

            # Se o método for POST, atualiza o equipamento
            if request.method == 'POST':
                # Obtém os dados do formulário
                nome = request.form.get('nome')
                id_local_acesso = request.form.get('local')
                direcao = request.form.get('direcao')
                tipo = request.form.get('tipo')
                ip = request.form.get('ip')

                # Atualiza os dados do equipamento
                equipamento.nome = nome
                equipamento.id_local_acesso = id_local_acesso
                equipamento.direcao = direcao
                equipamento.ip = ip
                equipamento.id_equipamento_tipo = tipo

                # Salva as alterações no banco de dados
                db.session.commit()

                # Redireciona para a página de equipamentos
                return redirect(url_for('equipamento.equipamentos'))

            # Se o método for GET, renderiza a página de edição
            return render_template('editar_equipamento.html', equipamento=equipamento)

        # Rota para apagar um equipamento
        @self.blueprint.route('/equipamentos/<int:id>/apagar', methods=['POST'])
        @csrf.exempt  # Usa a instância csrf para desabilitar CSRF nessa rota
        def apagar_equipamento(id):
            # Obtém o equipamento a ser apagado
            equipamento = Equipamento.query.get_or_404(id)

            # Remove o equipamento do banco de dados
            db.session.delete(equipamento)
            db.session.commit()

            # Redireciona para a página de equipamentos após a exclusão
            return redirect(url_for('equipamento.equipamentos'))
