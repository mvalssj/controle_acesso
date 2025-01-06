$(document).ready(function () {
    
    // Entidades
    $(document).ready(function() {

        // Preenche a coluna "Tipo" na tabela - código modificado
        $('#entidadesTable tbody tr').each(function() {
            var colaborador = parseInt($(this).data('tipo-colaborador')); // Certifique-se de que é um inteiro
            var terceiro = parseInt($(this).data('tipo-terceiro'));    // Certifique-se de que é um inteiro
            var id = $(this).data('id');
            var tipo = "";

            if (colaborador === 1 && terceiro === 1) {
                tipo = "colaborador e terceiro";
            } else if (colaborador === 1) {
                tipo = "colaborador";
            } else if (terceiro === 1) {
                tipo = "terceiro";
            } else {
                tipo = "Nenhum";
            }

            $('#tipo-' + id).text(tipo);
        });
    
        // Abre o modal de edição e preenche os campos
        $('#entidadeModal').on('show.bs.modal', function(event) {
            var button = $(event.relatedTarget);
            var id = button.data('id');
            var nome = button.data('nome');
            var natureza = button.data('natureza');
            var colaborador = button.data('tipo-colaborador');
            var terceiro = button.data('tipo-terceiro');
            var ativo = button.data('ativo');
    
            var modal = $(this);
            modal.find('.modal-body #id').val(id);
            modal.find('.modal-body #nome').val(nome);
            modal.find('.modal-body #natureza').val(natureza);
    
            // Define os valores dos checkboxes (adapte se usar selects ou outro elemento)
            modal.find('.modal-body #colaborador').prop('checked', colaborador == 1);
            modal.find('.modal-body #terceiro').prop('checked', terceiro == 1);
    
            modal.find('.modal-body #ativo').val(ativo);
        });
    
        // Limpa os campos do modal de nova entidade ao abrir
        $('#novaEntidadeModal').on('show.bs.modal', function(event) {
            $(this).find('input[type="text"], input[type="checkbox"], select').val('');
            $(this).find('input[type="checkbox"]').prop('checked', false);
        });
    
        // Salva a entidade editada
        $('#editarEntidadeBtn').click(function() {
            var id = $('#entidadeModal #id').val();
            var entidade = {
                nome: $('#entidadeModal #nome').val(),
                natureza: $('#entidadeModal #natureza').val(),
                colaborador: $('#entidadeModal #colaborador').prop('checked') ? 1 : 0,
                terceiro: $('#entidadeModal #terceiro').prop('checked') ? 1 : 0,
                ativo: $('#entidadeModal #ativo').val()
            };
    
            editarEntidade(id, entidade);
        });
    
        // Salva uma nova entidade
        $('#salvarNovaEntidadeBtn').click(function() {
            var entidade = {
                nome: $('#novaEntidadeModal #nome').val(),
                natureza: $('#novaEntidadeModal #natureza').val(),
                colaborador: $('#novaEntidadeModal #colaborador').prop('checked') ? 1 : 0,
                terceiro: $('#novaEntidadeModal #terceiro').prop('checked') ? 1 : 0,
                ativo: $('#novaEntidadeModal #ativo').val()
            };
    
            novaEntidade(entidade);
        });
    
        function editarEntidade(id, entidade) {
            let dados = {
                nome: entidade.nome,
                natureza: entidade.natureza,
                ativo: entidade.ativo,
                colaborador: entidade.colaborador,
                terceiro: entidade.terceiro
            };
    
            $.ajax({
                url: `/entidades/${id}/editar`,
                type: 'POST',
                data: dados,
                success: function(response) {
                    alert('Entidade atualizada com sucesso!');
                    location.reload();
                },
                error: function(error) {
                    alert('Erro ao atualizar entidade.');
                    console.error(error);
                }
            });
        }
    
        function novaEntidade(entidade) {
            let dados = {
                nome: entidade.nome,
                natureza: entidade.natureza,
                ativo: entidade.ativo,
                colaborador: entidade.colaborador,
                terceiro: entidade.terceiro
            };
    
            $.ajax({
                url: '/entidades/novo',
                type: 'POST',
                data: dados,
                success: function(response) {
                    alert('Entidade criada com sucesso!');
                    location.reload();
                },
                error: function(error) {
                    alert('Erro ao criar entidade.');
                    console.error(error);
                }
            });
        }
    
        // Evento de clique para apagar a entidade
        $('.apagar-entidade').click(function() {
            var id = $(this).data('id');
            if (confirm("Tem certeza que deseja apagar esta entidade?")) {
                apagarEntidade(id);
            }
        });
    
        function apagarEntidade(id) {
            $.ajax({
                url: `/entidades/${id}/apagar`,
                type: 'POST',
                success: function(response) {
                    alert('Entidade apagada com sucesso!');
                    location.reload();
                },
                error: function(error) {
                    alert('Erro ao apagar entidade.');
                    console.error(error);
                }
            });
        }
    });
            
    // Equipamentos
    $(document).ready(function () {
        $('#equipamentosTable').DataTable({
            "pageLength": 5, // Define o número de linhas por página
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json"
            }
        });

        // Ação ao clicar na linha da tabela
        $('#equipamentosTable tbody').on('click', 'tr', function () {
            var nome = $(this).data('nome');
            var local = $(this).data('local');
            var tipo_id = $(this).data('tipo_id');
            var tipo = $(this).data('tipo');
            var direcao = $(this).data('direcao');
            var ip = $(this).data('ip');
            var data_cadastro = $(this).data('data_cadastro');
            var data_modificacao = $(this).data('data_modificacao');
            var id = $(this).data('id');

            // Preenche os campos do modal com os dados da linha clicada
            $('#equipamentoModal #nome').val(nome);
            $('#equipamentoModal #local').val(local);
            $('#equipamentoModal #tipo').val(tipo);
            $('#equipamentoModal #tipo').val(tipo_id);
            $('#equipamentoModal #direcao').val(direcao);
            $('#equipamentoModal #ip').val(ip);
            $('#equipamentoModal #data_cadastro').val(data_cadastro);
            $('#equipamentoModal #data_modificacao').val(data_modificacao);
            $('#equipamentoModal #id').val(id);

            // Exibe o modal
            $('#equipamentoModal').modal('show');
        });

        // Envia os dados do formulário do modal "novoEquipamentoModal"
        $('#salvarEquipamentoBtn').click(function () {
            // Obtém os dados do formulário
            var nome = $('#novoEquipamentoModal #nome').val();
            var local = $('#novoEquipamentoModal #local').val();
            var tipo = $('#novoEquipamentoModal #tipo').val();
            var direcao = $('#novoEquipamentoModal #direcao').val();
            var ip = $('#novoEquipamentoModal #ip').val();

            // Verifica se os campos estão preenchidos
            if (!nome || !local || !tipo || !ip || !direcao) {
                alert('Por favor, preencha todos os campos!');
                return;
            }

            // Envia os dados para o servidor via AJAX
            $.ajax({
                url: '/equipamentos/novo',
                type: 'POST',
                data: {
                    nome: nome,
                    local: local,
                    tipo: tipo,
                    direcao: direcao,
                    ip: ip
                },
                success: function (response) {
                    // Recarrega a página após o sucesso do envio
                    location.reload();
                },
                error: function (error) {
                    // Exibe uma mensagem de erro caso ocorra algum problema
                    alert('Erro ao salvar o equipamento!');
                }
            });
        });

        // Editar o local de acesso sem recarregar a página
        $('#editarEquipamentoBtn').click(function () {
            var id = $('#equipamentoModal #id').val();
            var nome = $('#equipamentoModal #nome').val();
            var local = $('#equipamentoModal #local').val();
            var tipo = $('#equipamentoModal #tipo').val();
            var direcao = $('#equipamentoModal #direcao').val();
            var ip = $('#equipamentoModal #ip').val();

            if (!nome || !local || !tipo || !ip || !direcao) {
                alert('Por favor, preencha todos os campos!');
                return;
            }

            $.ajax({
                url: '/equipamentos/' + id + '/editar',
                type: 'POST',
                data: {
                    nome: nome,
                    local: local,
                    tipo: tipo,
                    direcao: direcao,
                    ip: ip
                },
                success: function (response) {
                    // Atualize os valores diretamente na interface
                    $('#equipamentoModal #nome').val(response.nome);
                    $('#equipamentoModal #local').val(response.local);
                    $('#equipamentoModal #tipo').val(response.tipo);
                    $('#equipamentoModal #direcao').val(response.direcao);
                    $('#equipamentoModal #ip').val(response.ip);

                    location.reload(); // Atualiza a página
                
                    // Fecha o modal após a edição
                    $('#equipamentoModal').modal('hide');

                    alert('Equipamento editado com sucesso!');
                },
                error: function (error) {
                    alert('Erro ao editar o equipamento!');
                }
            });
        });

        // Função para apagar o equipamento
        $('#apagarEquipamentoBtn').click(function () {
            var id = $('#equipamentoModal #id').val();

            if (confirm('Tem certeza que deseja apagar este equipamento?')) {
                // Envia a requisição de exclusão via AJAX
                $.ajax({
                    url: '/equipamentos/' + id + '/apagar',
                    type: 'POST',
                    success: function (response) {
                        // Recarrega a página após o sucesso da exclusão
                        location.reload();
                    },
                    error: function (error) {
                        alert('Erro ao apagar o equipamento!');
                    }
                });
            }
        });
    });

    // Eventos
    $(document).ready(function () {
        var tableNoTerminal = $('#eventosTableNoTerminal').DataTable({
            "pageLength": 5, // Define o número de linhas por página
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json"
            },
            "order": [[0, "desc"]], // Ordena a coluna 0 (primeira coluna) de forma decrescente
            "columns": [
                { "data": "id", "type": "num" }, // Mapeia a coluna ID como numérico
                { "data": "pessoa" }, // Mapeia a coluna Pessoa como texto
                { "data": "cpf" }, // Mapeia a coluna CPF como texto
                { "data": "created_at", "type": "date" }, // Mapeia a coluna Início Programação como data
            ]
        });

        function fetchAndUpdateTableNoTerminal() {
            $.ajax({
                url: '/no_terminal',
                method: 'POST', // Usa o método POST para obter JSON
                success: function (data) {
                    console.log("Dados recebidos para eventosTableNoTerminal:", data);
                    tableNoTerminal.clear().rows.add(data).draw();
                },
                error: function (xhr, status, error) {
                    console.error("Erro ao buscar dados para eventosTableNoTerminal: " + error);
                }
            });
        }

        // Chama a função para buscar e atualizar a tabela a cada 5 segundos
        setInterval(fetchAndUpdateTableNoTerminal, 5000);

        function fetchAndUpdateDashboard() {
            $.ajax({
                url: '/dashboard',
                method: 'POST', // Usa o método POST para obter JSON
                success: function (data) {
                    console.log("Dados recebidos para Dashboard:", data);
                    // Atualiza os elementos HTML com os novos dados
                    document.getElementById('pessoas-liberadas').textContent = '0';
                    document.getElementById('total-acessos').textContent = data.acessos_unicos;
                    document.getElementById('antipassback-count').textContent = data.eventos_antipassback;
                    document.getElementById('pessoas-terminal').textContent = data.pessoas_terminal;
                    document.getElementById('veiculos-terminal').textContent = '0';
                    // Adicione as linhas abaixo para atualizar os dados do último acesso
                    document.getElementById('ultimo-acesso-pessoa').textContent = data.ultimo_acesso_pessoa;
                    // Formata a data e hora para o padrão brasileiro com dia da semana
                    var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric' };
                    var formattedDateTime = new Date(data.ultimo_acesso_data).toLocaleDateString('pt-BR', options);
                    document.getElementById('ultimo-acesso-data').textContent = formattedDateTime;
                },
                error: function (xhr, status, error) {
                    console.error("Erro ao buscar dados para Dashboard: " + error);
                }
            });
        }

        // Chama a função para buscar e atualizar a Dashboard a cada 5 segundos
        setInterval(fetchAndUpdateDashboard, 5000);
        

        var tableEventos = $('#eventosTable').DataTable({
            "pageLength": 5,
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json"
            },
            "order": [[0, "desc"]],
            "columns": [
                {
                    "data": "id",
                    "type": "num",
                    "render": function (data, type, row) {
                        return data.toString().toUpperCase();
                    }
                },
                {
                    "data": "pessoa",
                    "render": function (data, type, row) {
                        return data.toString().toUpperCase();
                    }
                },
                {
                    "data": "cpf",
                    "render": function (data, type, row) {
                        return data.toString().toUpperCase();
                    }
                },
                {
                    "data": "direcao",
                    "type": "text",
                    "render": function (data, type, row) {
                        if (data === 'IN') {
                            return "ENTROU";
                        } else if (data === 'OUT') {
                            return "SAIU";
                        } else {
                            return "ANTIPASSBACK";
                        }
                    }
                },
                {
                    "data": "retificacao",
                    "type": "date",
                    "render": function (data, type, row) {
                        if (data === 'Y') {
                            return "SIM";
                        } else if (data === 'N') {
                            return "NÃO";
                        }
                    }
                },
                {
                    "data": "created_at",
                    "type": "date",
                    "render": function (data, type, row) {
                        return data.toString().toUpperCase();
                    }
                }
            ]
        });

        function fetchAndUpdateEventosTable() {
            $.ajax({
                url: '/eventos',
                method: 'POST', // Usa o método POST para obter JSON
                success: function (data) {
                    console.log("Dados recebidos para eventosTable:", data);
                    tableEventos.clear().rows.add(data).draw();
                },
                error: function (xhr, status, error) {
                    console.error("Erro ao buscar dados para eventosTable: " + error);
                }
            });
        }
        
        // Chama a função para buscar e atualizar a tabela a cada 5 segundos
        setInterval(fetchAndUpdateEventosTable, 5000);

        // Adicione um ouvinte de eventos para lidar com cliques nas linhas da tabela 'eventosTable'
        $('#eventosTable tbody').on('click', 'tr', function () {
            // Obtenha os dados da linha clicada
            var data = tableEventos.row(this).data();

            // Verifique se os dados foram obtidos corretamente
            if (data) {
                // Exiba um alerta com o ID do evento
                if (confirm(`Deseja retificar o evento com ID ${data.id}?`)) {
                    // Se o usuário confirmar, faça uma requisição AJAX para excluir o evento
                    var json_data = {
                        "direcao": data.direcao,
                        "CardName": data.pessoa,
                        "CardNo": data.cpf,
                        "IdEvento": data.id
                    };

                    $.ajax({
                        url: '/adequar_evento', 
                        type: 'POST', // Ou o método HTTP que seu backend espera para adequação
                        data: JSON.stringify(json_data),
                        contentType: 'application/json',
                        success: function (response) {
                            // Manipule a resposta do servidor após a adequação (se necessário)
                            console.log('Evento adequado com sucesso:', response);

                            // Atualize a tabela para refletir a adequação
                            tableEventos.row(this).remove().draw();
                        },
                        error: function (error) {
                            console.error('Erro ao adequado evento:', error);
                            // Manipule erros durante a adequação, como exibir uma mensagem de erro ao usuário
                        }
                    });
                }
            } else {
                console.error('Dados da linha não encontrados.');
            }
        });

        // Adicione o evento 'draw.dt' para aplicar a cor laranja após o carregamento dos dados
        $('#eventosTable').on('draw.dt', function () {
            // Selecione as linhas da tabela que devem ter a cor laranja
            $('#eventosTable tbody tr').each(function () {
                var retificacao = $(this).find('td:eq(4)').text(); // Obtém o valor da coluna "retificacao"
                if (retificacao === 'SIM') {
                    $(this).addClass('table-warning'); // Adiciona a classe 'table-warning' se a retificacao for 'SIM'
                }
            });
        });

    });

    // Unidades
    $(document).ready(function () {
        // Inicializa a tabela de unidades com DataTables
        $('#unidadesTable').DataTable({
            "pageLength": 5, // Define o número de linhas por página
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json"
            }
        });

        // Ação ao clicar na linha da tabela
        $('#unidadesTable tbody').on('click', 'tr', function () {
            var nome = $(this).data('nome');
            var descricao = $(this).data('descricao');
            var data_cadastro = $(this).data('data_cadastro');
            var data_modificacao = $(this).data('data_modificacao');
            var id = $(this).data('id');

            // Preenche os campos do modal com os dados da linha clicada
            $('#unidadeModal #nome').val(nome);
            $('#unidadeModal #descricao').val(descricao);
            $('#unidadeModal #data_cadastro').val(data_cadastro);
            $('#unidadeModal #data_modificacao').val(data_modificacao);
            $('#unidadeModal #id').val(id);

            // Limpa o container de locais de acesso
            $('#locais_acesso_container').empty();

            // Exibe o modal
            $('#unidadeModal').modal('show');

            // Carrega os locais de acesso da unidade
            $.ajax({
                url: '/locais_acesso/unidade/' + id,
                type: 'GET',
                success: function (response) {
                    // Adiciona cada local de acesso ao container
                    response.forEach(function (localAcesso) {
                        // Adiciona um atributo data-id ao botão para armazenar o ID do local
                        var localAcessoItem = $(`
                            <div class="row mb-3 align-items-center">
                                <div class="col-md-5" hidden>
                                    <label class="form-label">ID:</label>
                                    <input type="text" class="form-control" id="id" value="${localAcesso.id}" readonly>
                                </div>
                                <div class="col-md-5">
                                    <label class="form-label">Local:</label>
                                    <input type="text" class="form-control" value="${localAcesso.nome}" readonly>
                                </div>
                                <div class="col-md-5">
                                    <label class="form-label">Descrição:</label>
                                    <input type="text" class="form-control" value="${localAcesso.descricao}" readonly>
                                </div>
                                <div class="col-md-2 text-end">
                                    <label class="form-label d-block">&nbsp;</label>
                                    <button type="button" class="btn btn-danger apagarLocalAcessoBtnUnidade" data-id="${localAcesso.id}">Apagar Local</button>
                                </div>
                            </div>
                        `);
                        $('#locais_acesso_container').append(localAcessoItem);
                    });

                    // Evento de clique para apagar o local de acesso
                    $('#locais_acesso_container').on('click', '.apagarLocalAcessoBtnUnidade', function() {
                        var id = $(this).data('id'); // Obtém o ID do botão clicado

                        if (confirm('Tem certeza que deseja apagar este local de acesso?')) {
                            $.ajax({
                                url: '/locais_acesso/' + id + '/apagar',
                                type: 'POST',
                                success: function (response) {
                                    location.reload();
                                },
                                error: function (error) {
                                    alert('Erro ao apagar o local de acesso!');
                                }
                            });
                        }
                    });

                    // Evento de clique para apagar o local de acesso
                    $('#locais_acesso_container').on('click', '.apagarLocalAcessoBtnUnidadeNovo', function() {
                        var id = $(this).data('id'); // Obtém o ID do botão clicado

                        if (confirm('Tem certeza que deseja apagar este local de acesso?')) {
                            $.ajax({
                                url: '/locais_acesso/' + id + '/apagar',
                                type: 'POST',
                                success: function (response) {
                                    location.reload();
                                },
                                error: function (error) {
                                    alert('Erro ao apagar o local de acesso!');
                                }
                            });
                        }
                    });
                },
                error: function (error) {
                    console.error('Erro ao carregar locais de acesso:', error);
                }
            });
        });

        // Função para adicionar um novo local de acesso
        $('#addLocalAcessoBtn').click(function () {
            // Obtém o ID da unidade do modal
            var id_unidade = $('#unidadeModal #id').val();
            // Obtém os valores dos campos de nome e descrição
            var nome = $('#local_acesso_nome').val();
            var descricao = $('#local_acesso_descricao').val();

            // Verifica se os campos estão preenchidos
            if (!nome || !descricao) {
                alert('Por favor, preencha todos os campos!');
                return;
            }

            // Adiciona diretamente ao frontend antes de enviar para o backend
            var localAcessoItem = $(`
                <div class="row mb-3 align-items-center">
                    <div class="col-md-5" hidden>
                        <label class="form-label">ID:</label>
                        <input type="text" class="form-control" id="id" value="" readonly> 
                    </div>
                    <div class="col-md-5">
                        <label class="form-label">Local:</label>
                        <input type="text" class="form-control" value="${nome}" readonly>
                    </div>
                    <div class="col-md-5">
                        <label class="form-label">Descrição:</label>
                        <input type="text" class="form-control" value="${descricao}" readonly>
                    </div>
                    <div class="col-md-2 text-end">
                        <label class="form-label d-block">&nbsp;</label>
                        <button type="button" class="btn btn-danger apagarLocalAcessoBtnUnidadeNovo" data-id="">Apagar Local</button>
                    </div>
                </div>
            `);
            $('#locais_acesso_container').append(localAcessoItem);

            // Limpa os campos de entrada após adicionar ao frontend
            $('#local_acesso_nome').val('');
            $('#local_acesso_descricao').val('');

            // Faz a requisição AJAX para enviar ao backend
            $.ajax({
                url: '/locais_acesso/novo',
                type: 'POST',
                data: {
                    nome: nome,
                    unidade: id_unidade,
                    descricao: descricao
                },
                success: function (response) {
                    // Aqui response deve conter o ID do novo local de acesso criado
                    console.log("Local de acesso adicionado:", response);

                    // Assumindo que a resposta contém um objeto com o ID: { id: 123 }
                    const newId = response.id;

                    // Encontra o último local de acesso adicionado (que ainda não tem o ID)
                    const lastLocalAcessoItem = $('#locais_acesso_container').children().last();

                    // Define o ID nos elementos corretos dentro do último item adicionado
                    lastLocalAcessoItem.find('input#id').val(newId);
                    lastLocalAcessoItem.find('button.apagarLocalAcessoBtnUnidadeNovo').attr('data-id', newId);


                },
                error: function (error) {
                    console.error('Erro ao adicionar local de acesso ao banco de dados:', error);
                    // Se houver erro, você pode optar por remover o item do frontend ou alertar o usuário
                    alert('Erro ao adicionar local de acesso ao banco de dados.');

                    // Remove o item adicionado do frontend se houve erro na requisição
                    localAcessoItem.remove();
                }
            });
        });

        // Envia os dados do formulário do modal "novaUnidadeModal"
        $('#salvarUnidadeBtn').click(function () {
            // Obtém os dados do formulário
            var nome = $('#novaUnidadeModal #nome').val();
            var descricao = $('#novaUnidadeModal #descricao').val();

            // Verifica se os campos estão preenchidos
            if (!nome || !descricao) {
                alert('Por favor, preencha todos os campos!');
                return;
            }

            // Envia os dados para o servidor via AJAX
            $.ajax({
                url: '/unidades/novo',
                type: 'POST',
                data: {
                    nome: nome,
                    descricao: descricao
                },
                success: function (response) {
                    // Recarrega a página após o sucesso do envio
                    location.reload();
                },
                error: function (error) {
                    alert('Erro ao salvar a unidade!');
                }
            });
        });

        // Função para apagar a Unidade
        $('#apagarUnidadeBtn').click(function () {
            var id = $('#unidadeModal #id').val();

            if (confirm('Tem certeza que deseja apagar esta unidade?')) {
                // Envia a requisição de exclusão via AJAX
                $.ajax({
                    url: '/unidades/' + id + '/apagar',
                    type: 'POST',
                    success: function (response) {
                        // Recarrega a página após o sucesso da exclusão
                        location.reload();
                    },
                    error: function (error) {
                        alert('Erro ao apagar a unidade! Primeiro apague os locais Relacionados.');
                    }
                });
            }
        });       

    });

    // Programacoes
    $(document).ready(function () {

        // Configuração inicial dos elementos da câmera para o modal de nova programação
        const video = document.getElementById('camera');
        const canvas = document.getElementById('fotoCanvas');
        const captureButton = document.getElementById('captureButton');
        const fotoInput = document.getElementById('foto');
        const cameraLoading = document.getElementById('cameraLoading');

        // Configuração inicial dos elementos da câmera para o modal de edição
        const editarVideo = document.getElementById('editarCamera');
        const editarCanvas = document.getElementById('editarFotoCanvas');
        const editarCaptureButton = document.getElementById('editarCaptureButton');
        const editarFotoInput = document.getElementById('editarFoto');
        const editarCameraLoading = document.getElementById('editarCameraLoading');

        // Evento ao clicar em uma linha da tabela para abrir o modal de edição
        $('#programacoesTable tbody').on('click', 'tr', function () {
            // Obtém os dados da programação da linha clicada
            const programacaoId = $(this).data('id');
            const cpf = $(this).data('cpf').toString().replace(/[^\d]/g, '');
            const pessoa = $(this).data('pessoa');
            const datahora_inicio = $(this).data('datahora_inicio');
            const datahora_fim = $(this).data('datahora_fim');
            const cavalo = $(this).data('cavalo');
            const carreta = $(this).data('carreta');
            const tipo = $(this).data('tipo');

            // Preenche os campos do modal de edição com os dados da programação

            // Define o ID no modal de edição
            $('#editarProgramacaoModal').data('id', programacaoId);
            $('#editarPessoa').val(pessoa);
            $('#editarCpf').val(cpf);
            $('#editarCpfAtual').val(cpf);
            $('#editarDatahoraInicio').val(datahora_inicio);
            $('#editarDatahoraFim').val(datahora_fim);
            $('#editarCavalo').val(cavalo);
            $('#editarCarreta').val(carreta);
            $('#editarTipo').val(tipo);

            // Aplica a máscara ao CPF antes de definir o valor
            $('#editarCpf').mask('000.000.000-00'); // <--- Adicione esta linha aqui
            $('#editarCpf').val(cpf); // Define o valor do CPF

            // Define o título do modal com o ID da programação
            $('#editarProgramacaoModalLabel').text(`Editar Programação - ${programacaoId}`);
            $('#id_programacao').text(`Editar Programação - ${programacaoId}`);

            // Abre o modal de edição
            $('#editarProgramacaoModal').modal('show');

            // Faz uma requisição POST para a rota /buscar/equipamento ao abrir o modal
            $.ajax({
                url: '/buscar/equipamento',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ cpf: cpf }),
                success: function (response) {
                    // Extrai o valor de UserID do retorno
                    const userIdMatch = response.data.match(/UserID=(\d+)/);

                    // Verifica se o valor de UserID foi encontrado
                    if (userIdMatch && userIdMatch[1]) {
                        // Define o valor de UserID no campo #id_equipamento
                        $('#id_equipamento').val(userIdMatch[1]);

                        // Se a resposta contém a foto, desenha-a no canvas
                        if (response.foto) {
                            const context = editarCanvas.getContext('2d');
                            const image = new Image();
                            image.onload = function () {
                                // Limpa o canvas e desenha a imagem do equipamento
                                context.clearRect(0, 0, editarCanvas.width, editarCanvas.height);
                                context.drawImage(image, 0, 0, editarCanvas.width, editarCanvas.height);
                                editarCanvas.style.display = 'block'; // Certifique-se de exibir o canvas
                            };
                            image.src = 'data:image/jpeg;base64,' + response.foto;
                        }
                    } else {
                        // Exibe um alerta se o UserID não for encontrado
                        alert('Erro ao buscar dados do equipamento: ' + response.message);
                    }
                },
                error: function (xhr, status, error) {
                    // Exibe um alerta em caso de erro na requisição
                    console.error('Erro ao buscar o equipamento:', error);
                    alert('Erro ao buscar o equipamento.');
                }
            });
        });

        // Inicializa a câmera ao abrir o modal de nova programação
        $('#novoProgramacaoModal').on('shown.bs.modal', function () {
            // Exibe a mensagem de carregamento
            cameraLoading.style.display = 'block';
            // Verifica se o navegador suporta a API de mídia
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then(function (stream) {
                        // Exibe o vídeo da câmera
                        video.style.display = 'block';
                        // Oculta a mensagem de carregamento
                        cameraLoading.style.display = 'none';
                        // Exibe o botão de captura
                        captureButton.style.display = 'block';
                        // Define o stream de vídeo para o elemento de vídeo
                        video.srcObject = stream;
                    })
                    .catch(function (err) {
                        // Exibe um erro no console e um alerta se houver um erro ao acessar a câmera
                        console.error('Erro ao acessar a câmera:', err);
                        cameraLoading.style.display = 'none';
                    });
            } else {
                // Exibe um erro no console e um alerta se o navegador não suportar a API de mídia
                console.error('O navegador não suporta a API de mídia.');
                cameraLoading.style.display = 'none';
            }
        });

        // Limpa a câmera ao fechar o modal de nova programação
        $('#novoProgramacaoModal').on('hidden.bs.modal', function () {
            // Obtém o stream de vídeo
            const stream = video.srcObject;
            // Obtém as faixas de mídia do stream
            const tracks = stream.getTracks();

            // Para cada faixa de mídia, chama a função stop() para parar a faixa
            tracks.forEach(track => track.stop());
            // Define o srcObject do vídeo como nulo para parar o stream
            video.srcObject = null;
            // Oculta o vídeo, o canvas e o botão de captura
            video.style.display = 'none';
            canvas.style.display = 'none';
            captureButton.style.display = 'none';
            // Oculta a mensagem de carregamento
            cameraLoading.style.display = 'none';
        });

        // Captura a imagem ao clicar no botão de captura no modal de nova programação
        captureButton.addEventListener('click', function () {
            // Exibe o canvas
            canvas.style.display = 'block';
            // Obtém o contexto 2D do canvas
            const context = canvas.getContext('2d');
            // Desenha a imagem do vídeo no canvas
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Converte a imagem para base64 e armazena no input hidden
            const dataURL = canvas.toDataURL('image/jpeg');
            fotoInput.value = dataURL;
        });

        // Inicializa a câmera ao abrir o modal de edição de programação
        $('#editarProgramacaoModal').on('shown.bs.modal', function () {
            // Exibe a mensagem de carregamento
            editarCameraLoading.style.display = 'block';
            // Verifica se o navegador suporta a API de mídia
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then(function (stream) {
                        // Exibe o vídeo da câmera
                        editarVideo.style.display = 'block';
                        // Oculta a mensagem de carregamento
                        editarCameraLoading.style.display = 'none';
                        // Exibe o botão de captura
                        editarCaptureButton.style.display = 'block';
                        // Define o stream de vídeo para o elemento de vídeo
                        editarVideo.srcObject = stream;
                    })
                    .catch(function (err) {
                        // Exibe um erro no console e um alerta se houver um erro ao acessar a câmera
                        console.error('Erro ao acessar a câmera:', err);
                        editarCameraLoading.style.display = 'none';
                    });
            } else {
                // Exibe um erro no console e um alerta se o navegador não suportar a API de mídia
                console.error('O navegador não suporta a API de mídia.');
                editarCameraLoading.style.display = 'none';
            }
        });

        // Limpa a câmera ao fechar o modal de edição
        $('#editarProgramacaoModal').on('hidden.bs.modal', function () {
            // Obtém o stream de vídeo
            const stream = editarVideo.srcObject;
            // Obtém as faixas de mídia do stream
            const tracks = stream.getTracks();

            // Para cada faixa de mídia, chama a função stop() para parar a faixa
            tracks.forEach(track => track.stop());
            // Define o srcObject do vídeo como nulo para parar o stream
            editarVideo.srcObject = null;
            // Oculta o vídeo, o canvas e o botão de captura
            editarVideo.style.display = 'none';
            editarCanvas.style.display = 'none';
            editarCaptureButton.style.display = 'none';
            // Oculta a mensagem de carregamento
            editarCameraLoading.style.display = 'none';
        });

        // Captura a imagem ao clicar no botão de captura no modal de edição
        editarCaptureButton.addEventListener('click', function () {
            // Obtém o contexto 2D do canvas
            const context = editarCanvas.getContext('2d');

            // Desenha a imagem do vídeo no canvas
            context.drawImage(editarVideo, 0, 0, editarCanvas.width, editarCanvas.height);

            // Converte a imagem para base64 e armazena no input hidden
            const dataURL = editarCanvas.toDataURL('image/jpeg');
            editarFotoInput.value = dataURL;

            // Exibe o canvas
            editarCanvas.style.display = 'block';
        });

        // Aplica a máscara ao campo CPF nos dois modais
        $('#cpf').mask('000.000.000-00');
        $('#editarCpf').mask('000.000.000-00');

        // Valida o CPF ao salvar a nova programação
        $('#salvarProgramacaoBtn').click(function () {
            let cpf = $('#cpf').val();

            // Remove pontos e hífen
            cpf = cpf.replace(/[.\-]/g, '');

            if (!validarCPF(cpf)) {
                alert('CPF inválido. Por favor, insira um CPF válido.');
                return false; // Impede o envio do formulário
            }

            // Atualiza o campo com CPF limpo para envio
            $('#cpf').val(cpf);
        });

        // Valida o CPF ao salvar a edição da programação
        $('#salvarEdicaoBtn').click(function () {
            let cpf = $('#editarCpf').val();

            // Remove pontos e hífen
            cpf = cpf.replace(/[.\-]/g, '');

            if (!validarCPF(cpf)) {
                alert('CPF inválido. Por favor, insira um CPF válido.');
                return false; // Impede o envio do formulário
            }

            // Atualiza o campo com CPF limpo para envio
            $('#editarCpf').val(cpf);
        });

        $('#programacoesTable').DataTable({
            "pageLength": 5, // Define o número de linhas por página
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json"
            },
            "order": [[0, "desc"]], // Ordena a coluna 0 (primeira coluna) de forma decrescente
            "columns": [
                { "data": "id", "type": "num" }, // Mapeia a coluna ID como numérico
                { "data": "pessoa" }, // Mapeia a coluna Pessoa como texto
                { "data": "cpf" }, // Mapeia a coluna CPF como texto
                { "data": "cavalo" }, // Mapeia a coluna Cavalo como texto
                { "data": "carreta" }, // Mapeia a coluna Carreta como texto
                { "data": "id_tipo" },
                { "data": "datahora_inicio", "type": "date" }, // Mapeia a coluna Início Programação como data
                { "data": "datahora_fim", "type": "date" }, // Mapeia a coluna Final Programação como data
            ]
        });

        // Envia os dados do formulário do modal "novoProgramacaoModal"
        $('#salvarProgramacaoBtn').click(function () {
            // Obtém os dados do formulário
            var datahora_inicio = $('#novoProgramacaoModal #datahora_inicio').val();
            var datahora_fim = $('#novoProgramacaoModal #datahora_fim').val();
            var cavalo = $('#novoProgramacaoModal #cavalo').val();
            var carreta = $('#novoProgramacaoModal #carreta').val();
            var pessoa = $('#novoProgramacaoModal #pessoa').val();
            var cpf = $('#novoProgramacaoModal #cpf').val().replace(/[^0-9]/g, ''); // Remove caracteres especiais do CPF
            var id_tipo = $('#novoProgramacaoModal #id_tipo').val();
            var foto = $('#novoProgramacaoModal #foto').val();

            // Valida o CPF
            if (!validarCPF(cpf)) {
                alert('CPF inválido. Por favor, insira um CPF válido.');
                return false; // Impede o envio do formulário
            }

            // Verifica se os campos estão preenchidos
            if (!datahora_inicio || !datahora_fim || !pessoa || !cpf || !foto) {
                alert('Por favor, preencha todos os campos!');
                return false; // Interrompe a execução da função se algum campo estiver vazio
            } else {
                // Envia os dados para o servidor via AJAX
                $.ajax({
                    url: '/programacoes/novo',
                    type: 'POST',
                    data: {
                        datahora_inicio: datahora_inicio,
                        datahora_fim: datahora_fim,
                        cavalo: cavalo,
                        carreta: carreta,
                        pessoa: pessoa,
                        cpf: cpf,
                        id_tipo: id_tipo,
                        foto: foto
                    },
                    success: function (response) {
                        // Recarrega a página após o sucesso do envio
                        location.reload();
                    },
                    error: function (error) {
                        // Exibe uma mensagem de erro caso ocorra algum problema
                        alert('Erro ao salvar a programação!');
                    }
                });
            }
        });

        // Envia os dados do formulário do modal de edição "editarProgramacaoModal"
        $('#salvarEdicaoBtn').click(function () {
            // Obtém o ID da programação do modal
            var id = $('#editarProgramacaoModal').data('id');

            // Certifica-se de que o ID está definido corretamente
            if (!id) {
                alert('Erro: ID da programação não encontrado.');
                return false;
            }

            // Obtém os dados do formulário de edição
            var datahora_inicio = $('#editarDatahoraInicio').val();
            var datahora_fim = $('#editarDatahoraFim').val();
            var cavalo = $('#editarCavalo').val();
            var carreta = $('#editarCarreta').val();
            var pessoa = $('#editarPessoa').val();
            var cpf = $('#editarCpf').val().replace(/[^0-9]/g, ''); // Remove caracteres especiais do CPF
            var cpf_atual = $('#editarCpfAtual').val().replace(/[^0-9]/g, ''); // Remove caracteres especiais do CPF
            var id_tipo = $('#editarTipo').val();
            var id_equipamento = $('#id_equipamento').val();
            var foto = $('#editarFoto').val();

            // Verifica se os campos estão preenchidos
            if (!datahora_inicio || !datahora_fim || !pessoa || !cpf || !id_tipo) {
                alert('Por favor, preencha todos os campos!');
                return false;
            }

            // Envia os dados para o servidor via AJAX para editar
            $.ajax({
                url: '/programacoes/' + id + '/editar',
                type: 'POST',
                data: {
                    datahora_inicio: datahora_inicio,
                    datahora_fim: datahora_fim,
                    cavalo: cavalo,
                    carreta: carreta,
                    pessoa: pessoa,
                    cpf: cpf,
                    cpf_atual: cpf_atual,
                    id_tipo: id_tipo,
                    foto: foto,
                    id_equipamento: id_equipamento
                },
                success: function (response) {
                    // Recarrega a página após o sucesso do envio
                    location.reload();
                },
                error: function (error) {
                    // Exibe uma mensagem de erro caso ocorra algum problema
                    alert('Erro ao editar a programação!');
                }
            });
        });

        // Função para apagar a programação
        $('#apagarProgramacaoBtn').click(function () {
            var id = $('#programacaoModal #id').val();

            if (confirm('Tem certeza que deseja apagar esta programação?')) {
                // Envia a requisição de exclusão via AJAX
                $.ajax({
                    url: '/programacoes/' + id + '/apagar',
                    type: 'POST',
                    success: function (response) {
                        // Recarrega a página após o sucesso da exclusão
                        location.reload();
                    },
                    error: function (error) {
                        alert('Erro ao apagar a programação!');
                    }
                });
            }
        });

        // Função de validação de CPF (reutilizada para ambos os modais)
        function validarCPF(cpf) {
            // Remove qualquer caractere que não seja número
            cpf = cpf.replace(/[^\d]+/g, '');
            // Verifica se o CPF tem 11 dígitos ou se todos são iguais
            if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {
                return false;
            }

            let soma = 0;
            let resto;

            // Verifica o primeiro dígito
            for (let i = 1; i <= 9; i++) {
                soma += parseInt(cpf.substring(i - 1, i)) * (11 - i);
            }

            resto = (soma * 10) % 11;
            if ((resto === 10) || (resto === 11)) resto = 0;
            if (resto !== parseInt(cpf.substring(9, 10))) return false;

            // Verifica o segundo dígito
            soma = 0;
            for (let i = 1; i <= 10; i++) {
                soma += parseInt(cpf.substring(i - 1, i)) * (12 - i);
            }

            resto = (soma * 10) % 11;
            if ((resto === 10) || (resto === 11)) resto = 0;
            if (resto !== parseInt(cpf.substring(10, 11))) return false;

            return true;
        }

    });

    // Locais de Acesso
    $(document).ready(function () {
        $('#locaisAcessoTable').DataTable({
            "pageLength": 5, // Define o número de linhas por página
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json"
            }
        });

        // Ação ao clicar na linha da tabela
        $('#locaisAcessoTable tbody').on('click', 'tr', function () {
            var nome = $(this).data('nome');
            var unidade_id = $(this).data('unidade_id');
            var descricao = $(this).data('descricao');
            var data_cadastro = $(this).data('data_cadastro');
            var data_modificacao = $(this).data('data_modificacao');
            var id = $(this).data('id');

            // Preenche os campos do modal com os dados da linha clicada
            $('#localAcessoModal #nome').val(nome);
            $('#localAcessoModal #unidade').val(unidade_id);
            $('#localAcessoModal #descricao').val(descricao);
            $('#localAcessoModal #data_cadastro').val(data_cadastro);
            $('#localAcessoModal #data_modificacao').val(data_modificacao);
            $('#localAcessoModal #id').val(id);

            // Exibe o modal
            $('#localAcessoModal').modal('show');
        });

        // Envia os dados do formulário do modal "novoLocalAcessoModal"
        $('#salvarLocalAcessoBtn').click(function () {
            // Obtém os dados do formulário
            var nome = $('#novoLocalAcessoModal #nome').val();
            var unidade = $('#novoLocalAcessoModal #unidade').val();
            var descricao = $('#novoLocalAcessoModal #descricao').val();

            // Verifica se os campos estão preenchidos
            if (!nome || !unidade || !descricao) {
                alert('Por favor, preencha todos os campos!');
                return;
            }

            // Envia os dados para o servidor via AJAX
            $.ajax({
                url: '/locais_acesso/novo',
                type: 'POST',
                data: {
                    nome: nome,
                    unidade: unidade,
                    descricao: descricao
                },
                success: function (response) {
                    // Recarrega a página após o sucesso do envio
                    location.reload();
                },
                error: function (error) {
                    // Exibe uma mensagem de erro caso ocorra algum problema
                    alert('Erro ao salvar o local de acesso!');
                }
            });
        });

        // Envia os dados do formulário do modal "localAcessoModal" para editar
        $('#editarLocalAcessoBtn').click(function () {
            // Obtém os dados do formulário
            var id = $('#localAcessoModal #id').val();
            var nome = $('#localAcessoModal #nome').val();
            var unidade = $('#localAcessoModal #unidade').val();
            var descricao = $('#localAcessoModal #descricao').val();

            // Verifica se os campos estão preenchidos
            if (!nome || !unidade || !descricao) {
                alert('Por favor, preencha todos os campos!');
                return;
            }

            console.log(id)
            console.log(nome)
            console.log(unidade)
            console.log(descricao)
            // Envia os dados para o servidor via AJAX
            $.ajax({
                url: '/locais_acesso/' + id + '/editar',
                type: 'POST',
                data: {
                    nome: nome,
                    unidade: unidade,
                    descricao: descricao
                },
                success: function (response) {
                    // Recarrega a página após o sucesso do envio
                    location.reload();
                },
                error: function (error) {
                    // Exibe uma mensagem de erro caso ocorra algum problema
                    alert('Erro ao editar o local de acesso!');
                }
            });
        });

        // Função para apagar o local de acesso
        $('#apagarLocalAcessoBtn').click(function () {
            var id = $('#localAcessoModal #id').val();

            if (confirm('Tem certeza que deseja apagar este local de acesso?')) {
                // Envia a requisição de exclusão via AJAX
                $.ajax({
                    url: '/locais_acesso/' + id + '/apagar',
                    type: 'POST',
                    success: function (response) {
                        // Recarrega a página após o sucesso da exclusão
                        location.reload();
                    },
                    error: function (error) {
                        alert('Erro ao apagar o local de acesso!');
                    }
                });
            }
        });
    });

});