from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import Entidade, EntidadePessoaFisica, SystemUsuario, db
from app.extensions import csrf

class AuthController:
    def __init__(self):
        self.blueprint = Blueprint('auth', __name__)

        @self.blueprint.route('/usuarios')
        def usuarios():
            entidades = Entidade.query.all()
            return render_template('usuarios/index.html', entidades=entidades)

        # Rota para inserir uma nova entidade no banco de dados
        @self.blueprint.route('/usuarios', methods=['POST'])
        @csrf.exempt
        def criar_usuario():
            nome = request.form.get('nome')
            natureza = request.form.get('natureza')
            estrutura_societaria = request.form.get('estrutura_societaria')
            unidade_negocio = request.form.get('unidade_negocio')
            ativo = request.form.get('ativo')
            sigla = request.form.get('sigla')
            fornecedor = request.form.get('fornecedor')
            cliente = request.form.get('cliente')
            colaborador = request.form.get('colaborador')
            terceiro = request.form.get('terceiro')
            motorista = request.form.get('motorista')
            transportador = request.form.get('transportador')
            salina = request.form.get('salina')
            agencia_maritima = request.form.get('agencia_maritima')
            operador = request.form.get('operador')
            armador = request.form.get('armador')
            representante = request.form.get('representante')
            id_entidade_matriz = request.form.get('id_entidade_matriz')
            id_entidade_representada = request.form.get('id_entidade_representada')

            nova_entidade = Entidade(
                nome=nome,
                natureza=natureza,
                estrutura_societaria=estrutura_societaria,
                unidade_negocio=unidade_negocio,
                ativo=ativo,
                sigla=sigla,
                fornecedor=fornecedor,
                cliente=cliente,
                colaborador=colaborador,
                terceiro=terceiro,
                motorista=motorista,
                transportador=transportador,
                salina=salina,
                agencia_maritima=agencia_maritima,
                operador=operador,
                armador=armador,
                representante=representante,
                id_entidade_matriz=id_entidade_matriz,
                id_entidade_representada=id_entidade_representada
            )
            db.session.add(nova_entidade)
            db.session.commit()

            novo_usuario = SystemUsuario(
                id_entidade=nova_entidade.id,
                nome=nome,
                email=f'{nome}@email.com',
                password='123456'
            )
            db.session.add(novo_usuario)
            db.session.commit()

            return jsonify({'message': 'Entidade criada com sucesso!'}), 201

        # Rota para exibir o formulário de edição de uma entidade
        @self.blueprint.route('/usuarios/<int:id>/editar')
        def editar_usuario(id):
            entidade = Entidade.query.get_or_404(id)
            return render_template('usuarios/editar.html', entidade=entidade)

        # Rota para atualizar uma entidade no banco de dados
        @self.blueprint.route('/usuarios/<int:id>', methods=['POST'])
        @csrf.exempt
        def atualizar_usuario(id):
            entidade = Entidade.query.get_or_404(id)
            entidade.nome = request.form.get('nome')
            entidade.natureza = request.form.get('natureza')
            entidade.estrutura_societaria = request.form.get('estrutura_societaria')
            entidade.unidade_negocio = request.form.get('unidade_negocio')
            entidade.ativo = request.form.get('ativo')
            entidade.sigla = request.form.get('sigla')
            entidade.fornecedor = request.form.get('fornecedor')
            entidade.cliente = request.form.get('cliente')
            entidade.colaborador = request.form.get('colaborador')
            entidade.terceiro = request.form.get('terceiro')
            entidade.motorista = request.form.get('motorista')
            entidade.transportador = request.form.get('transportador')
            entidade.salina = request.form.get('salina')
            entidade.agencia_maritima = request.form.get('agencia_maritima')
            entidade.operador = request.form.get('operador')
            entidade.armador = request.form.get('armador')
            entidade.representante = request.form.get('representante')
            entidade.id_entidade_matriz = request.form.get('id_entidade_matriz')
            entidade.id_entidade_representada = request.form.get('id_entidade_representada')

            db.session.commit()

            return redirect(url_for('entidade.entidades'))

        # Rota para excluir uma entidade do banco de dados
        @self.blueprint.route('/usuarios/<int:id>/excluir', methods=['POST'])
        @csrf.exempt
        def excluir_usuario(id):
            entidade = Entidade.query.get_or_404(id)
            db.session.delete(entidade)
            db.session.commit()

            return redirect(url_for('entidade.entidades'))
        