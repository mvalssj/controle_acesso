from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import db, Dashboard, Unidade, Evento  # Importe o modelo Dashboard
from sqlalchemy import func, distinct
from app.extensions import csrf  # Importe csrf
from datetime import date, datetime, timedelta

class DashboardController:
    def __init__(self):
        self.blueprint = Blueprint('dashboard', __name__)

        @self.blueprint.route('/home', methods=['GET'])
        def visualizar_dashboard():
            # Consulta para obter o primeiro dashboard (ou None se não existir)
            dashboard = Dashboard.query.first()
            unidades = Unidade.query.all()
                # Consulta para obter o último evento por data de criação
            ultimo_evento = Evento.query.order_by(Evento.id.desc()).first()             
            # Renderiza o template, passando o dashboard ou um dicionário vazio
            return render_template('home.html', dashboard=dashboard, unidades=unidades, evento=ultimo_evento)

        # Rota para listar todos os dashboards
        @self.blueprint.route('/dashboards', methods=['GET'])
        def listar_dashboards():
            dashboards = Dashboard.query.all()
            return render_template('listar_dashboards.html', dashboards=dashboards)
               
        # Rota para criar um novo dashboard
        @self.blueprint.route('/dashboards/criar', methods=['GET', 'POST'])
        @csrf.exempt  # Desabilita CSRF para esta rota (apenas para demonstração)
        def criar_dashboard():
            if request.method == 'POST':
                # Obtém os dados do formulário
                id_entidade_pessoa_juridica = request.form.get('id_entidade_pessoa_juridica')
                pessoas_terminal = request.form.get('pessoas_terminal')
                veiculos_terminal = request.form.get('veiculos_terminal')
                pessoas_liberadas = request.form.get('pessoas_liberadas')
                total_acessos = request.form.get('total_acessos')

                # Cria um novo objeto Dashboard
                novo_dashboard = Dashboard(
                    id_entidade_pessoa_juridica=id_entidade_pessoa_juridica,
                    pessoas_terminal=pessoas_terminal,
                    veiculos_terminal=veiculos_terminal,
                    pessoas_liberadas=pessoas_liberadas,
                    total_acessos=total_acessos
                )

                # Adiciona o novo dashboard ao banco de dados
                db.session.add(novo_dashboard)
                db.session.commit()

                return redirect(url_for('dashboard.listar_dashboards'))  # Redireciona para a lista de dashboards

            return render_template('criar_dashboard.html')
        
        # Rota para editar um dashboard
        @self.blueprint.route('/dashboards/<int:id>/editar', methods=['GET', 'POST'])
        @csrf.exempt  # Desabilita CSRF para esta rota (apenas para demonstração)
        def editar_dashboard(id):
            dashboard = Dashboard.query.get_or_404(id)

            if request.method == 'POST':
                # Atualiza os campos do dashboard com os dados do formulário
                dashboard.id_entidade_pessoa_juridica = request.form.get('id_entidade_pessoa_juridica')
                dashboard.pessoas_terminal = request.form.get('pessoas_terminal')
                dashboard.veiculos_terminal = request.form.get('veiculos_terminal')
                dashboard.pessoas_liberadas = request.form.get('pessoas_liberadas')
                dashboard.total_acessos = request.form.get('total_acessos')

                db.session.commit()
                return redirect(url_for('dashboard.listar_dashboards'))

            return render_template('editar_dashboard.html', dashboard=dashboard)
        
        # Rota para excluir um dashboard
        @self.blueprint.route('/dashboards/<int:id>/excluir', methods=['POST'])
        @csrf.exempt  # Desabilita CSRF para esta rota (apenas para demonstração)
        def excluir_dashboard(id):
            dashboard = Dashboard.query.get_or_404(id)
            db.session.delete(dashboard)
            db.session.commit()
            return redirect(url_for('dashboard.listar_dashboards'))
        
        # Rota para pegar o numero de eventos de antipassback e o total de acessos únicos hoje
        @self.blueprint.route('/dashboard', methods=['POST'])
        @csrf.exempt  # Desabilita CSRF para esta rota (apenas para demonstração)
        def dashboard():
            get_dashboard = Dashboard.query.first()  # Assumindo que você quer o primeiro dashboard
            hoje = date.today()
            # Consulta para obter a quantidade de eventos com código de erro 20
            eventos_antipassback = Evento.query.filter(Evento.codigo_erro == '20', func.date(Evento.created_at) == hoje).count()
            print(f"Quantidade de eventos com código de erro 20: {eventos_antipassback}")

            # Consulta para obter a quantidade de acessos únicos hoje
            acessos_unicos = db.session.query(func.count(distinct(Evento.cpf))).filter(func.date(Evento.created_at) == hoje, Evento.direcao == 'IN').scalar()
            print(f"Quantidade de acessos únicos hoje: {acessos_unicos}")

            # Subconsulta para pegar o maior ID de eventos com direção 'OUT' para cada CPF
            subquery_last_out = (
                Evento.query
                .filter(Evento.direcao == 'OUT')
                .with_entities(Evento.cpf, func.max(Evento.id).label('last_out_id'))
                .group_by(Evento.cpf)
                .subquery()
            )
            
            # Calcula a data de dois dias atrás
            dois_dias_atras = datetime.now() - timedelta(days=2)

                # Subconsulta para pegar o último evento de IN para cada CPF, excluindo CPFs com OUT posterior,
            # eventos que tenham o código_erro = '16', eventos com CPF vazio e eventos com mais de dois dias.
            subquery_last_in = (
                Evento.query
                .outerjoin(subquery_last_out, Evento.cpf == subquery_last_out.c.cpf)
                .filter(
                    Evento.direcao == 'IN',  # Apenas eventos de IN
                    (subquery_last_out.c.last_out_id == None) | (Evento.id > subquery_last_out.c.last_out_id),  # Excluir CPFs com OUT posterior
                    Evento.codigo_erro != '16',  # Ignorar eventos com código_erro '16'
                    Evento.cpf != '',  # Ignorar eventos com CPF vazio
                    Evento.created_at >= dois_dias_atras # Considera apenas eventos dos últimos dois dias
                )
                .with_entities(Evento.cpf, func.max(Evento.id).label('last_in_id'))
                .group_by(Evento.cpf)
                .subquery()
            )
            
            # Consulta principal para pegar os eventos correspondentes ao último 'IN' de cada CPF
            pessoas_terminal = (
                Evento.query
                .join(subquery_last_in, Evento.id == subquery_last_in.c.last_in_id)
                .distinct(Evento.cpf)  # Garantir que cada CPF seja listado apenas uma vez
                .filter(Evento.codigo_erro != '16')  # Garantir que a consulta final também ignora '16'
                .all()
            )

            ultimo_evento = Evento.query.order_by(Evento.id.desc()).first() 

            # --- ATUALIZAÇÃO DO DASHBOARD ---
            try:
                # Obtém o dashboard com ID 1
                dashboard = Dashboard.query.get(1) 

                # Verifica se o dashboard existe
                if dashboard:
                    # Atualiza a coluna 'pessoas_terminal'
                    dashboard.eventos_antipassback = eventos_antipassback
                    # Atualiza a coluna 'total_acessos'
                    dashboard.total_acessos = acessos_unicos

                    qty_pessoas_terminal = len(pessoas_terminal)
                    dashboard.pessoas_terminal = qty_pessoas_terminal
                    db.session.commit()
                    print(f"### Dados atualizados do Antipassback hoje: {eventos_antipassback}")
                    print(f"### Total de acessos únicos hoje: {acessos_unicos}")
                    print(f"### Pessoas no terminal Agora: {qty_pessoas_terminal}")
                else:
                    print("Dashboard com ID 1 não encontrado.")
            except Exception as e:
                print(f"Erro ao atualizar o dashboard")            
            # --- ATUALIZAÇÃO DO DASHBOARD ---

            # Retorna a quantidade de eventos de antipassback e o total de acessos únicos hoje
            return {
                'pessoas_liberadas': get_dashboard.pessoas_liberadas,
                'eventos_antipassback': eventos_antipassback,
                'acessos_unicos': acessos_unicos,
                'veiculos_terminal': get_dashboard.veiculos_terminal,
                'pessoas_terminal': qty_pessoas_terminal,
                'ultimo_acesso_pessoa': ultimo_evento.pessoa,
                'ultimo_acesso_data': ultimo_evento.updated_at
                
            }
