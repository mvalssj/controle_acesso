from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import Entidade, db
from app.extensions import csrf

class EntidadeController:
    def __init__(self):
        self.blueprint = Blueprint('entidade', __name__)

        @self.blueprint.route('/entidades')
        def entidades():
            entidades = Entidade.query.all()
            return render_template('entidades.html', entidades=entidades)

        @self.blueprint.route('/entidades/novo', methods=['POST'])
        @csrf.exempt
        def nova_entidade():
            try:
                data = request.form.to_dict()
                # Conversão de tipos de dados
                for key in ['ativo', 'colaborador', 'terceiro']:
                    if data.get(key):  # Verifica se a chave existe e se o valor não é vazio
                        try:
                            data[key] = int(data[key])
                        except ValueError:
                            # Lida com o caso em que o valor não pode ser convertido para int (por exemplo, string vazia)
                            data[key] = None  # Ou outro valor padrão apropriado
                    else:
                        data[key] = None # Define como None se a chave não existir ou o valor for vazio
                
                nova_entidade = Entidade(**data)
                db.session.add(nova_entidade)
                db.session.commit()
                return jsonify({'message': 'Entidade criada com sucesso!'}), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500

        @self.blueprint.route('/entidades/<int:id>/editar', methods=['POST'])
        @csrf.exempt
        def editar_entidade(id):
            entidade = Entidade.query.get_or_404(id)
            if request.method == 'POST':
                try:
                    data = request.form.to_dict()
                    for key in ['ativo', 'colaborador', 'terceiro']:
                        if data.get(key):
                            try:
                                data[key] = int(data[key])
                            except ValueError:
                                data[key] = None
                        else:
                            data[key] = None

                    for key, value in data.items():
                        setattr(entidade, key, value)
                    db.session.commit()
                    return jsonify({'message': 'Entidade atualizada com sucesso!'}), 200
                except Exception as e:
                    db.session.rollback()
                    return jsonify({'error': str(e)}), 500
            return render_template('entidades.html', entidade=entidade) # permanece entidades.html

        @self.blueprint.route('/entidades/<int:id>/apagar', methods=['POST'])
        @csrf.exempt
        def apagar_entidade(id):
            entidade = Entidade.query.get_or_404(id)

            db.session.delete(entidade)
            db.session.commit()

            return redirect(url_for('entidade.entidades'))