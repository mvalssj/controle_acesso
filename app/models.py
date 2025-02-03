from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Classe base para herdar comportamentos comuns (Soft Delete, Timestamps, Entidade)
class BaseModel(db.Model):
    __abstract__ = True
    
    deleted = db.Column(db.SmallInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

# Tabela de tipos de equipamento
class EquipamentoTipo(BaseModel):
    __tablename__ = 'equipamento_tipo'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=True)
    ativo = db.Column(db.SmallInteger, default=1)

    # Relacionamento com Equipamentos, definindo apenas um backref aqui
    equipamentos = db.relationship('Equipamento', backref='tipo_equipamento')

# Tabela de equipamentos
class Equipamento(BaseModel):
    __tablename__ = 'equipamento'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_equipamento_tipo = db.Column(db.BigInteger, db.ForeignKey('equipamento_tipo.id'), nullable=False)
    id_local_acesso = db.Column(db.BigInteger, db.ForeignKey('local_acesso.id'), nullable=False) # Correção: Adicionando a ForeignKey
    nome = db.Column(db.String(150), nullable=True)
    ip = db.Column(db.String(150), nullable=True)
    ativo = db.Column(db.SmallInteger, default=1)
    sigla = db.Column(db.String(10), nullable=True, comment='A sigla que será usada na numeração das viagens.')
    direcao = db.Column(db.String(10), nullable=True)
    id_entidade_proprietaria = db.Column(db.BigInteger, db.ForeignKey('unidade.id'), nullable=False)

    local_acesso = db.relationship('LocalAcesso', backref='equipamentos') # Adicionando o relacionamento
    entidade_proprietaria = db.relationship('Unidade', backref='equipamentos') # Adicionando o relacionamento

# Tabela de configuração dos equipamentos
class EquipamentoConfiguracao(BaseModel):
    __tablename__ = 'equipamento_configuracao'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_equipamento = db.Column(db.BigInteger, db.ForeignKey('equipamento.id'), nullable=False)
    configuracao = db.Column(db.JSON, nullable=True)
    ativo = db.Column(db.SmallInteger, default=1)

# Tabela de eventos relacionados ao equipamento
class Evento(BaseModel):
    __tablename__ = 'evento'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_equipamento = db.Column(db.BigInteger, db.ForeignKey('equipamento.id'), nullable=False)
    id_evento = db.Column(db.BigInteger, nullable=False)
    pessoa = db.Column(db.String(150), nullable=True)
    cpf = db.Column(db.String(11), nullable=True)
    pos_fila = db.Column(db.Integer, nullable=True)
    placa_1 = db.Column(db.String(7), nullable=True)
    placa_2 = db.Column(db.String(7), nullable=True)
    direcao = db.Column(db.String(3), nullable=True)
    retificacao = db.Column(db.String(3), nullable=True, default='N')
    lpr = db.Column(db.String(3), nullable=True, default='N')
    gravacao_equipamento = db.Column(db.String(3), nullable=True, default='N')
    pesar = db.Column(db.String(3), nullable=True, default='N')
    codigo_erro = db.Column(db.String(10), nullable=True)
    imagem_path = db.Column(db.String(255), nullable=True)
    json = db.Column(db.JSON, nullable=True)
    protocolo = db.Column(db.String(2000), nullable=True)

# Tabela de eventos biométricos
class EventoBiometria(BaseModel):
    __tablename__ = 'evento_biometria'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_equipamento = db.Column(db.BigInteger, db.ForeignKey('equipamento.id'), nullable=False)

# Tabela de Unidades
class Unidade(BaseModel):
    __tablename__ = 'unidade'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    ativo = db.Column(db.SmallInteger, default=1)
    # locais_acesso = db.relationship('LocalAcesso', backref='unidade', lazy=True)

# Tabela de Locais de Acesso
class LocalAcesso(BaseModel):
    __tablename__ = 'local_acesso'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    id_unidade = db.Column(db.BigInteger, db.ForeignKey('unidade.id'), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    unidade = db.relationship('Unidade', backref='locais_acesso', lazy=True)

    # equipamentos = db.relationship('Equipamento', backref='local_acesso', lazy=True)

# Tabela de Programação
class Programacao(BaseModel):
    __tablename__ = 'programacao'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    datahora_inicio = db.Column(db.DateTime, nullable=False)
    datahora_fim = db.Column(db.DateTime, nullable=False)
    cavalo = db.Column(db.String(50), nullable=False, default='')
    carreta = db.Column(db.String(50), nullable=False, default='')
    pessoa = db.Column(db.String(150), nullable=False, default='')
    cpf = db.Column(db.String(11), nullable=False, default='')
    id_tipo = db.Column(db.Integer, nullable=False, default=0)

# Tabela de Tipo de Programação
class ProgramacaoTipo(BaseModel):
    __tablename__ = 'programacao_tipo'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(50), nullable=False)

# Tabela de Dashboard
class Dashboard(BaseModel):
    __tablename__ = 'dashboard'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_entidade_pessoa_juridica = db.Column(db.Integer, nullable=False, default=0)
    pessoas_terminal = db.Column(db.Integer, nullable=True)    
    eventos_antipassback = db.Column(db.Integer, nullable=True)
    veiculos_terminal = db.Column(db.Integer, nullable=True)
    pessoas_liberadas = db.Column(db.Integer, nullable=True)
    total_acessos = db.Column(db.Integer, nullable=True)

# Tabela de Entidade
class Entidade(BaseModel):
    __tablename__ = 'entidade'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False)
    natureza = db.Column(db.Enum('pessoa_fisica', 'pessoa_juridica'), nullable=False)
    estrutura_societaria = db.Column(db.Enum('individual', 'filial', 'matriz'), nullable=True)
    unidade_negocio = db.Column(db.SmallInteger, nullable=False, default=0)
    ativo = db.Column(db.SmallInteger, nullable=True, default=1)
    sigla = db.Column(db.String(10), nullable=True, comment='A sigla que será usada na numeração das viagens.')
    fornecedor = db.Column(db.Boolean, nullable=True)
    cliente = db.Column(db.Boolean, nullable=True, default=False)
    colaborador = db.Column(db.Boolean, nullable=True)
    terceiro = db.Column(db.Boolean, nullable=True)
    motorista = db.Column(db.Boolean, nullable=True)
    transportador = db.Column(db.Boolean, nullable=True)
    salina = db.Column(db.Boolean, nullable=True)
    agencia_maritima = db.Column(db.Boolean, nullable=True)
    operador = db.Column(db.Boolean, nullable=True)
    armador = db.Column(db.Boolean, nullable=True)
    representante = db.Column(db.Boolean, nullable=True)
    id_entidade_matriz = db.Column(db.BigInteger, nullable=True, default=0)
    id_entidade_representada = db.Column(db.BigInteger, nullable=True, comment='Quando a entidade é um representante, deve-se informar a entidade representada')

# Tabela de Entidade Pessoa Física
class EntidadePessoaFisica(BaseModel):
    __tablename__ = 'entidade_pessoa_fisica'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_entidade = db.Column(db.BigInteger, db.ForeignKey('entidade.id'), nullable=False)
    id_pais = db.Column(db.BigInteger, nullable=False, default=93)
    nome = db.Column(db.String(150), nullable=False)
    cpf_passaporte = db.Column(db.String(11), unique=True, nullable=True)
    cnh = db.Column(db.String(11), nullable=True)
    rg = db.Column(db.String(12), nullable=True)

# Tabela de Configurações do Sistema
class SystemConfig(BaseModel):
    __tablename__ = 'system_config'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_entidade_created = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_updated = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_deleted = db.Column(db.BigInteger, nullable=False, default=0)

# Tabela de Perfis do Sistema
class SystemPerfil(BaseModel):
    __tablename__ = 'system_perfil'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_system_rota = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_unidade_negocio = db.Column(db.BigInteger, nullable=False)
    descricao = db.Column(db.String(150), nullable=True)
    id_entidade_created = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_updated = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_deleted = db.Column(db.BigInteger, nullable=False, default=0)
    id_usuario_created = db.Column(db.BigInteger, nullable=True)
    id_usuario_updated = db.Column(db.BigInteger, nullable=True)
    id_usuario_deleted = db.Column(db.BigInteger, nullable=True)

# Tabela de Perfis de Usuários e Rotas
class SystemPerfilRota(BaseModel):
    __tablename__ = 'system_perfil_rota'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_system_perfil = db.Column(db.BigInteger, nullable=False, default=0)
    id_system_rota = db.Column(db.BigInteger, nullable=True)
    ver = db.Column(db.Boolean, nullable=False, default=False)
    criar = db.Column(db.Boolean, nullable=False, default=False)
    atualizar = db.Column(db.Boolean, nullable=False, default=False)
    apagar = db.Column(db.Boolean, nullable=False, default=False)
    id_entidade_created = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_updated = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_deleted = db.Column(db.BigInteger, nullable=False, default=0)
    id_usuario_created = db.Column(db.BigInteger, nullable=True)
    id_usuario_updated = db.Column(db.BigInteger, nullable=True)
    id_usuario_deleted = db.Column(db.BigInteger, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('id_system_perfil', 'id_system_rota', name='id_system_perfil_id_system_rota'),
    )

# Tabela de Perfis de Usuários
class SystemPerfilUsuario(BaseModel):
    __tablename__ = 'system_perfil_usuario'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_system_usuario = db.Column(db.BigInteger, nullable=False, default=0)
    id_system_perfil = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_created = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_updated = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_deleted = db.Column(db.BigInteger, nullable=False, default=0)
    id_usuario_created = db.Column(db.BigInteger, nullable=True)
    id_usuario_updated = db.Column(db.BigInteger, nullable=True)
    id_usuario_deleted = db.Column(db.BigInteger, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('id_system_usuario', 'id_system_perfil', name='id_entidade_id_system_perfil'),
    )

# Tabela de Rotas do Sistema
class SystemRota(BaseModel):
    __tablename__ = 'system_rota'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    descricao = db.Column(db.String(100), nullable=False, default='0')
    rota = db.Column(db.String(250), nullable=False, default='0')
    deleted = db.Column(db.SmallInteger, nullable=False, default=0)
    ativo = db.Column(db.SmallInteger, nullable=False, default=0)
    id_entidade_created = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_updated = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_deleted = db.Column(db.BigInteger, nullable=False, default=0)
    id_usuario_created = db.Column(db.BigInteger, nullable=True)
    id_usuario_updated = db.Column(db.BigInteger, nullable=True)
    id_usuario_deleted = db.Column(db.BigInteger, nullable=True)

# Tabela de Usuários do Sistema
class SystemUsuario(BaseModel):
    __tablename__ = 'system_usuario'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_entidade = db.Column(db.BigInteger, nullable=False)
    id_entidade_unidade_negocio_ativo = db.Column(db.BigInteger, nullable=False, default=1)
    nome = db.Column(db.String(50), nullable=True)
    imagem_perfil = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    remember_token = db.Column(db.String(100), nullable=True)
    id_entidade_created = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_updated = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_deleted = db.Column(db.BigInteger, nullable=False, default=0)
    id_usuario_created = db.Column(db.BigInteger, nullable=True)
    id_usuario_updated = db.Column(db.BigInteger, nullable=True)
    id_usuario_deleted = db.Column(db.BigInteger, nullable=True)

# Tabela de Logs de Usuários do Sistema
class SystemUsuarioLog(BaseModel):
    __tablename__ = 'system_usuario_log'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_entidade = db.Column(db.BigInteger, nullable=False)
    id_usuario = db.Column(db.BigInteger, nullable=False)
    acao = db.Column(db.Enum('login', 'logout'), nullable=False)
    id_entidade_created = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_updated = db.Column(db.BigInteger, nullable=False, default=0)
    id_entidade_deleted = db.Column(db.BigInteger, nullable=False, default=0)
    id_usuario_created = db.Column(db.BigInteger, nullable=True)
    id_usuario_updated = db.Column(db.BigInteger, nullable=True)
    id_usuario_deleted = db.Column(db.BigInteger, nullable=True)

class ProgramacaoCheck(BaseModel):
    __tablename__ = 'programacao_check'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    evento_id = db.Column(db.BigInteger, nullable=False)
    traseira_progrmacao = db.Column(db.String(10), nullable=True)
    frontal_programacao = db.Column(db.String(10), nullable=True)
    pessoa_programacao = db.Column(db.String(100), nullable=True)
    cpf_programacao = db.Column(db.String(11), nullable=True)
    frontal_detectada = db.Column(db.String(10), nullable=True)
    traseira_detectada = db.Column(db.String(10), nullable=True)
    pessoa_detectada = db.Column(db.String(100), nullable=True)
    cpf_detectado = db.Column(db.String(10), nullable=True)
    frontal_corrigida = db.Column(db.String(10), nullable=True)
    traseira_corrigida = db.Column(db.String(10), nullable=True)
    pessoa_corrigida = db.Column(db.String(100), nullable=True)
    cpf_corrigido = db.Column(db.String(11), nullable=True)
    frontal_status = db.Column(db.Enum('OK', 'NOK'), nullable=True)
    traseira_status = db.Column(db.Enum('OK', 'NOK'), nullable=True)
    pessoa_status = db.Column(db.Enum('OK', 'NOK'), nullable=True)
    cpf_status = db.Column(db.Enum('OK', 'NOK'), nullable=True)
    geral_status = db.Column(db.Enum('OK', 'NOK'), nullable=True)