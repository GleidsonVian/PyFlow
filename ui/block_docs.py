"""
Documentação inline de cada bloco do PyFlow RPA.
"""

BLOCK_DOCS = {

    "OpenBrowserBlock": {
        "title": "Abrir Navegador",
        "description": "Abre o Google Chrome em uma URL. Deve ser o primeiro bloco em fluxos de automação web.",
        "params": [
            ("url",       "Texto",    "Sim", "URL completa. Ex: https://google.com"),
            ("maximized", "Booleano", "Não", "Abre o navegador maximizado"),
        ],
        "example": "url: https://www.google.com\nmaximized: True",
        "tip": "Se a URL não começar com http, o prefixo https:// é adicionado automaticamente."
    },

    "ClickElementBlock": {
        "title": "Clicar em Elemento",
        "description": "Localiza um elemento pelo seletor CSS e clica nele.",
        "params": [
            ("selector", "Texto",  "Sim", "Seletor CSS. Ex: #btn-login, .btn-submit"),
            ("timeout",  "Número", "Não", "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "selector: #btn-entrar\ntimeout: 10",
        "tip": "DevTools (F12): botão direito → Copiar → Copiar selector."
    },

    "FillFieldBlock": {
        "title": "Preencher Campo",
        "description": "Localiza um campo de texto e digita o valor informado.",
        "params": [
            ("selector",      "Texto",    "Sim", "Seletor CSS do campo"),
            ("value",         "Texto",    "Sim", "Texto a digitar. Aceita {{variavel}}"),
            ("clear_before",  "Booleano", "Não", "Limpa o campo antes de digitar (padrão: True)"),
            ("timeout",       "Número",   "Não", "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "selector: #campo-busca\nvalue: {{termo_busca}}",
        "tip": "Use {{nome_variavel}} para inserir valores dinâmicos."
    },

    "ExtractTextBlock": {
        "title": "Extrair Texto",
        "description": "Extrai o texto visível de um elemento e salva como variável.",
        "params": [
            ("selector",       "Texto",  "Sim", "Seletor CSS. Ex: h1, .titulo, #preco"),
            ("variable_name",  "Texto",  "Não", "Nome da variável (padrão: texto_extraido)"),
            ("timeout",        "Número", "Não", "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "selector: h1\nvariable_name: titulo_pagina",
        "tip": "O valor fica disponível como {{titulo_pagina}} nos blocos seguintes."
    },

    "ExtractListBlock": {
        "title": "Extrair Lista",
        "description": "Extrai o texto de todos os elementos que correspondem ao seletor e salva como lista.",
        "params": [
            ("selector",      "Texto",    "Sim", "Seletor CSS. Ex: .product-title, ul li"),
            ("attribute",     "Texto",    "Não", "Atributo a extrair. Ex: href, src. Vazio = texto"),
            ("variable_name", "Texto",    "Não", "Nome da variável lista (padrão: lista_extraida)"),
            ("limit",         "Número",   "Não", "Máximo de itens. 0 = sem limite"),
            ("filter_empty",  "Booleano", "Não", "Ignora itens vazios (padrão: True)"),
            ("timeout",       "Número",   "Não", "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "selector: .product_pod h3 a\nvariable_name: titulos\nlimit: 10",
        "tip": "Gera também {{titulos_total}} e {{titulos_primeiro}} automaticamente."
    },

    "SmartWaitBlock": {
        "title": "Espera Inteligente",
        "description": "Aguarda uma condição específica antes de prosseguir.",
        "params": [
            ("condition",     "Texto",  "Sim",  "element_visible | element_clickable | element_hidden | element_exists | url_contains | url_equals | text_in_element | text_in_page | page_loaded | element_count"),
            ("selector",      "Texto",  "Cond.", "Seletor CSS (para condições de elemento)"),
            ("value",         "Texto",  "Cond.", "Valor esperado (para url_contains, text_in_*, element_count)"),
            ("timeout",       "Número", "Não",  "Tempo máximo em segundos (padrão: 15)"),
            ("poll_interval", "Número", "Não",  "Intervalo de verificação em segundos (padrão: 0.5)"),
            ("variable_name", "Texto",  "Não",  "Salva True/False do resultado como variável"),
        ],
        "example": "condition: element_visible\nselector: .btn-submit\n\ncondition: url_contains\nvalue: /dashboard",
        "tip": "Use após cliques e navegações. Muito mais confiável que um Aguardar fixo."
    },

    "PressKeyBlock": {
        "title": "Pressionar Tecla",
        "description": "Pressiona uma tecla especial em um elemento ou na página.",
        "params": [
            ("key",      "Texto",  "Sim", "Enter, Tab, Escape, Backspace, Delete, Space, ArrowUp/Down, F5..."),
            ("selector", "Texto",  "Não", "Seletor CSS. Vazio = pressiona no body"),
            ("timeout",  "Número", "Não", "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "key: Enter\nselector: #campo-busca",
        "tip": "Para submeter formulário: use seletor do campo + tecla Enter."
    },

    "ScrollPageBlock": {
        "title": "Scroll na Página",
        "description": "Rola a página para uma direção ou até um elemento.",
        "params": [
            ("direction", "Texto",  "Sim",  "top | bottom | element | (pixels)"),
            ("selector",  "Texto",  "Cond.", "Seletor CSS (somente direction=element)"),
            ("pixels",    "Número", "Cond.", "Pixels para rolar"),
        ],
        "example": "direction: bottom",
        "tip": "Use direction=bottom para carregar conteúdo lazy-loaded."
    },

    "ScreenshotBlock": {
        "title": "Tirar Screenshot",
        "description": "Salva captura de tela completa da página em PNG.",
        "params": [
            ("filename", "Texto", "Não", "Nome sem extensão. Vazio = usa data/hora"),
            ("folder",   "Texto", "Não", "Pasta de destino (padrão: screenshots)"),
        ],
        "example": "filename: resultado_login\nfolder: screenshots",
        "tip": "Ideal para registrar o estado da página após ações importantes."
    },

    "GetCurrentUrlBlock": {
        "title": "Obter URL Atual",
        "description": "Captura a URL atual do navegador e salva como variável.",
        "params": [
            ("variable_name", "Texto", "Não", "Nome da variável (padrão: url_atual)"),
        ],
        "example": "variable_name: url_produto",
        "tip": "Útil para salvar URLs de produtos durante scraping."
    },

    "MouseActionBlock": {
        "title": "Ação de Mouse",
        "description": "Executa ações avançadas: hover, duplo clique, drag & drop.",
        "params": [
            ("action",          "Texto",  "Sim",  "double_click | right_click | hover | drag_and_drop | click_offset | move_to"),
            ("selector",        "Texto",  "Cond.", "Seletor CSS do elemento"),
            ("target_selector", "Texto",  "Cond.", "Destino (somente drag_and_drop)"),
            ("offset_x",        "Número", "Não",  "Offset X em pixels"),
            ("offset_y",        "Número", "Não",  "Offset Y em pixels"),
            ("timeout",         "Número", "Não",  "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "action: hover\nselector: .menu-dropdown",
        "tip": "Use hover para ativar menus dropdown antes de clicar."
    },

    "NavigateToUrlBlock": {
        "title": "Navegar para URL",
        "description": "Navega para uma URL no navegador já aberto.",
        "params": [
            ("url", "Texto", "Sim", "URL de destino. Aceita {{variavel}}"),
        ],
        "example": "url: https://exemplo.com/{{id}}",
        "tip": "Reutiliza a janela já aberta, diferente do Abrir Navegador."
    },

    "GoBackBlock": {
        "title": "Voltar Página",
        "description": "Equivalente ao botão Voltar do navegador.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Útil após acessar um produto para voltar à listagem."
    },

    "GoForwardBlock": {
        "title": "Avançar Página",
        "description": "Equivalente ao botão Avançar do navegador.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Só funciona se você voltou antes."
    },

    "RefreshPageBlock": {
        "title": "Atualizar Página",
        "description": "Recarrega a página atual (F5).",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Use após ações que demoram para refletir na página."
    },

    "OpenNewTabBlock": {
        "title": "Abrir Nova Aba",
        "description": "Abre uma nova aba e opcionalmente navega para uma URL.",
        "params": [
            ("url", "Texto", "Não", "URL a abrir. Vazio = aba em branco"),
        ],
        "example": "url: https://github.com",
        "tip": "O foco muda automaticamente para a nova aba."
    },

    "CloseTabBlock": {
        "title": "Fechar Aba",
        "description": "Fecha a aba atual e volta para a anterior.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Não funciona com apenas uma aba — use Fechar Navegador."
    },

    "SwitchTabBlock": {
        "title": "Trocar de Aba",
        "description": "Muda o foco para uma aba pelo índice.",
        "params": [
            ("tab_index", "Número", "Sim", "0 = primeira, 1 = segunda..."),
        ],
        "example": "tab_index: 0",
        "tip": "Use para voltar para a aba original após Abrir Nova Aba."
    },

    "CloseBrowserBlock": {
        "title": "Fechar Navegador",
        "description": "Fecha todas as abas e encerra o Chrome.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Recomendado como último bloco em fluxos web."
    },

    "WaitBlock": {
        "title": "Aguardar",
        "description": "Pausa a execução por N segundos.",
        "params": [
            ("seconds", "Número", "Sim", "Tempo de pausa. Aceita decimais: 1.5s"),
        ],
        "example": "seconds: 3",
        "tip": "Para condições dinâmicas, prefira o bloco Espera Inteligente."
    },

    "IfBlock": {
        "title": "Condição (If)",
        "description": "Verifica uma condição e pula os próximos N blocos se for falsa.",
        "params": [
            ("condition_type", "Texto",  "Sim",  "element_exists | element_not_exists | variable_contains | variable_equals"),
            ("selector",       "Texto",  "Cond.", "Seletor CSS"),
            ("variable_name",  "Texto",  "Cond.", "Nome da variável"),
            ("expected_value", "Texto",  "Cond.", "Valor esperado"),
            ("skip_on_false",  "Número", "Não",  "Blocos a pular se falso (padrão: 1)"),
        ],
        "example": "condition_type: variable_contains\nvariable_name: titulo\nexpected_value: Python\nskip_on_false: 2",
        "tip": "skip_on_false=2 pula os 2 blocos seguintes se a condição for falsa."
    },

    "LoopBlock": {
        "title": "Loop (Repetir)",
        "description": "Repete um grupo de blocos N vezes.",
        "params": [
            ("times",         "Número", "Sim", "Número de repetições"),
            ("blocks_count",  "Número", "Sim", "Quantos blocos seguintes fazem parte do loop"),
            ("delay_between", "Número", "Não", "Pausa em segundos entre repetições"),
        ],
        "example": "times: 5\nblocks_count: 2\ndelay_between: 1",
        "tip": "blocks_count=2 inclui os 2 blocos imediatamente abaixo."
    },

    "ForEachBlock": {
        "title": "Para Cada (For Each)",
        "description": "Itera sobre uma lista executando blocos para cada item.",
        "params": [
            ("items",         "Texto",  "Sim", "Lista separada por vírgula OU nome de variável de lista"),
            ("variable_name", "Texto",  "Não", "Variável de iteração (padrão: item_atual)"),
            ("blocks_count",  "Número", "Sim", "Quantos blocos seguintes fazem parte do loop"),
            ("delay_between", "Número", "Não", "Pausa entre iterações"),
        ],
        "example": "items: titulos\nvariable_name: titulo\nblocks_count: 2",
        "tip": "Em cada iteração {{item_atual}} recebe o valor corrente."
    },

    "SetVariableBlock": {
        "title": "Definir Variável",
        "description": "Cria ou modifica variáveis sem precisar de scraping.",
        "params": [
            ("variable_name", "Texto", "Sim",  "Nome da variável a criar/modificar"),
            ("operation",     "Texto", "Sim",  "set | increment | decrement | append | prepend | multiply | divide | now | clear"),
            ("value",         "Texto", "Cond.", "Valor a usar. Aceita {{variavel}}"),
            ("format",        "Texto", "Não",  "Formato para operation=now (padrão: %d/%m/%Y %H:%M:%S)"),
        ],
        "example": "variable_name: contador\noperation: set\nvalue: 0\n\noperation: increment\nvalue: 1\n\noperation: now\nformat: %d/%m/%Y",
        "tip": "Use increment em loops para contar. Use now para timestamps."
    },

    "SequenceStartBlock": {
        "title": "Início da Sequência",
        "description": "Marca o início de um grupo de blocos que pode ser recolhido para organizar visualmente o fluxo. Funciona em par com o bloco 'Fim da Sequência'.",
        "params": [
            ("sequence_name", "Texto", "Sim", "Nome descritivo para o grupo. Ex: Login, Processar Itens."),
        ],
        "example": "sequence_name: Login no Sistema",
        "tip": "Clique no ícone ▼ ao lado do número do bloco para recolher ou expandir a sequência."
    },

    "SequenceEndBlock": {
        "title": "Fim da Sequência",
        "description": "Marca o final de um grupo de blocos iniciado com 'Início da Sequência'.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Este bloco serve apenas como delimitador. Será ocultado junto com o grupo ao recolher."
    },

    "ShowMessageBlock": {
        "title": "Exibir Mensagem",
        "description": "Abre uma caixa de diálogo modal. O fluxo pausa até clicar OK.",
        "params": [
            ("title",   "Texto", "Não", "Título da janela"),
            ("message", "Texto", "Sim", "Mensagem. Aceita {{variavel}} e \\n para quebra de linha"),
            ("kind",    "Texto", "Não", "info | warning | error"),
        ],
        "example": "title: Resultado\nmessage: Contador: {{contador}}\nkind: info",
        "tip": "Ideal para debug: exibe valores de variáveis durante a execução."
    },

    "DesktopNotificationBlock": {
        "title": "Notificação Desktop",
        "description": "Exibe uma notificação sem interromper a execução.",
        "params": [
            ("title",    "Texto",  "Sim", "Título da notificação"),
            ("message",  "Texto",  "Sim", "Mensagem. Aceita {{variavel}}"),
            ("duration", "Número", "Não", "Duração em ms (padrão: 5000)"),
        ],
        "example": "title: ✅ Concluído\nmessage: {{total}} itens processados.",
        "tip": "Diferente do Exibir Mensagem, não pausa o fluxo."
    },

    "TextManipulationBlock": {
        "title": "Manipular Texto",
        "description": "Aplica transformações em uma variável. 14 operações disponíveis.",
        "params": [
            ("input_variable",  "Texto", "Sim",  "Nome da variável de entrada"),
            ("operation",       "Texto", "Sim",  "upper | lower | trim | replace | regex_extract | regex_replace | split | join | count | contains | starts_with | ends_with | substring | length"),
            ("param1",          "Texto", "Cond.", "Parâmetro 1 (depende da operação)"),
            ("param2",          "Texto", "Cond.", "Parâmetro 2 (depende da operação)"),
            ("output_variable", "Texto", "Não",  "Variável de saída. Vazio = sobrescreve a entrada"),
        ],
        "example": "input_variable: email\noperation: regex_extract\nparam1: @(.+)\noutput_variable: dominio",
        "tip": "upper/lower/trim não precisam de parâmetros. replace precisa de param1 e param2."
    },

    "KeyboardActionBlock": {
        "title": "Teclado do Sistema",
        "description": "Interage com o teclado via PyAutoGUI. Funciona fora do navegador.",
        "params": [
            ("action",       "Texto",  "Sim", "type | press | hotkey"),
            ("value",        "Texto",  "Sim", "Texto, tecla ou atalho. Ex: ctrl+c, enter"),
            ("interval",     "Número", "Não", "Intervalo entre teclas (padrão: 0.05)"),
            ("delay_before", "Número", "Não", "Aguarda N segundos antes (padrão: 0)"),
        ],
        "example": "action: hotkey\nvalue: ctrl+c\n\naction: type\nvalue: Olá!\ndelay_before: 0.5",
        "tip": "Use delay_before para focar a janela alvo antes de digitar."
    },

    "ClipboardBlock": {
        "title": "Clipboard",
        "description": "Lê ou escreve no clipboard do sistema operacional.",
        "params": [
            ("action",        "Texto", "Sim",  "copy = copiar para clipboard | paste = ler do clipboard | clear = limpar"),
            ("value",         "Texto", "Cond.", "Texto a copiar (somente action=copy). Aceita {{variavel}}"),
            ("variable_name", "Texto", "Não",  "Variável onde salvar o texto lido (somente action=paste, padrão: clipboard_texto)"),
        ],
        "example": "# Copiar:\naction: copy\nvalue: {{titulo_extraido}}\n\n# Ler:\naction: paste\nvariable_name: texto_copiado",
        "tip": "Combine com Teclado do Sistema (Ctrl+C / Ctrl+V) para copiar conteúdo de janelas externas."
    },

    "ReadCsvBlock": {
        "title": "Ler CSV",
        "description": "Lê uma coluna de um CSV e salva como lista.",
        "params": [
            ("filepath",      "Texto",    "Sim", "Caminho do arquivo. Ex: dados/lista.csv"),
            ("column",        "Texto",    "Não", "Nome da coluna ou índice (padrão: 0)"),
            ("variable_name", "Texto",    "Não", "Nome da variável lista (padrão: csv_linhas)"),
            ("skip_header",   "Booleano", "Não", "Pula a primeira linha (padrão: True)"),
            ("delimiter",     "Texto",    "Não", "Separador: , ou ; ou | (padrão: ,)"),
        ],
        "example": "filepath: dados/emails.csv\ncolumn: email\nvariable_name: lista_emails",
        "tip": "Gera {{csv_linhas_total}} e {{csv_linhas_primeiro}} automaticamente."
    },

    "SaveTextBlock": {
        "title": "Salvar em TXT",
        "description": "Salva texto em arquivo .txt.",
        "params": [
            ("content",        "Texto",    "Sim", "Conteúdo a salvar. Aceita {{variavel}}"),
            ("filepath",       "Texto",    "Não", "Caminho do arquivo (padrão: saida/resultado.txt)"),
            ("mode",           "Texto",    "Não", "append = adiciona | overwrite = substitui"),
            ("add_timestamp",  "Booleano", "Não", "Adiciona [data hora] em cada linha"),
        ],
        "example": "content: {{url}} — {{titulo}}\nfilepath: saida/resultado.txt\nmode: append",
        "tip": "A pasta de destino é criada automaticamente se não existir."
    },

    "SaveCsvBlock": {
        "title": "Salvar em CSV",
        "description": "Adiciona uma linha de dados em CSV.",
        "params": [
            ("filepath",       "Texto",    "Não", "Caminho do arquivo CSV (padrão: saida/dados.csv)"),
            ("values",         "Texto",    "Sim", "Valores separados por pipe |. Ex: {{titulo}}|{{preco}}"),
            ("headers",        "Texto",    "Não", "Cabeçalhos separados por pipe |"),
            ("delimiter",      "Texto",    "Não", "Separador do CSV (padrão: ,)"),
            ("add_timestamp",  "Booleano", "Não", "Adiciona coluna de timestamp"),
        ],
        "example": "filepath: saida/produtos.csv\nvalues: {{nome}}|{{preco}}\nheaders: Nome|Preco",
        "tip": "Use | para separar colunas no campo values."
    },

    "SQLiteBlock": {
        "title": "Banco de Dados (SQLite)",
        "description": "Executa queries SQL em um banco SQLite local.",
        "params": [
            ("database",      "Texto", "Sim",  "Caminho do arquivo .db. Ex: dados/banco.db"),
            ("query",         "Texto", "Sim",  "Query SQL. Use ? para parâmetros posicionais"),
            ("params",        "Texto", "Não",  "Parâmetros separados por | para os ? na query"),
            ("variable_name", "Texto", "Não",  "Variável onde salvar resultado do SELECT"),
            ("row_variable",  "Texto", "Não",  "Variável para a primeira linha — expande cada coluna como {{row_var_coluna}}"),
        ],
        "example": "query: SELECT * FROM itens\nvariable_name: lista\nrow_variable: item",
        "tip": "Use row_variable para acessar colunas: {{item_nome}}, {{item_id}}, etc."
    },

    "HttpRequestBlock": {
        "title": "HTTP Request",
        "description": "Realiza requisições HTTP para APIs REST.",
        "params": [
            ("method",        "Texto",  "Sim", "GET | POST | PUT | PATCH | DELETE"),
            ("url",           "Texto",  "Sim", "URL da API. Aceita {{variavel}}"),
            ("headers",       "JSON",   "Não", 'Ex: {"Authorization": "Bearer {{token}}"}'),
            ("body",          "JSON",   "Não", 'Ex: {"nome": "{{nome}}"}'),
            ("json_field",    "Texto",  "Não", "Campo via dot notation. Ex: data.user.email"),
            ("variable_name", "Texto",  "Não", "Variável para salvar a resposta"),
            ("timeout",       "Número", "Não", "Timeout em segundos (padrão: 15)"),
        ],
        "example": "method: GET\nurl: https://api.exemplo.com/users/{{id}}\njson_field: name\nvariable_name: nome",
        "tip": "Dot notation: data.user.email acessa response['data']['user']['email']."
    },

    "SendEmailBlock": {
        "title": "Enviar E-mail",
        "description": "Envia e-mail via SMTP. Suporta Gmail, Outlook, Yahoo e custom.",
        "params": [
            ("provider",         "Texto",  "Não",  "gmail | outlook | yahoo | custom"),
            ("smtp_host",        "Texto",  "Cond.", "Servidor SMTP (somente custom)"),
            ("smtp_port",        "Número", "Cond.", "Porta SMTP (somente custom)"),
            ("sender_email",     "Texto",  "Sim",  "E-mail do remetente"),
            ("sender_password",  "Texto",  "Sim",  "Senha ou App Password"),
            ("recipient",        "Texto",  "Sim",  "Destinatário(s). Múltiplos por vírgula"),
            ("subject",          "Texto",  "Sim",  "Assunto. Aceita {{variavel}}"),
            ("body_text",        "Texto",  "Não",  "Corpo em texto simples"),
            ("body_html",        "Texto",  "Não",  "Corpo em HTML"),
        ],
        "example": "provider: gmail\nsender_email: meu@gmail.com\nsender_password: abcd efgh\nrecipient: dest@email.com\nsubject: Relatório {{data_atual}}",
        "tip": "Para Gmail: gere App Password em myaccount.google.com/apppasswords."
    },

    "FtpBlock": {
        "title": "FTP / SFTP",
        "description": "Transfere arquivos via FTP (nativo) ou SFTP (paramiko). Suporta upload, download, listar arquivos remotos e deletar arquivo remoto.",
        "params": [
            ("protocol",      "Texto",  "Sim",  "ftp | sftp"),
            ("action",        "Texto",  "Sim",  "upload | download | list | delete"),
            ("host",          "Texto",  "Sim",  "Host ou IP do servidor. Ex: ftp.meusite.com | 192.168.1.100"),
            ("port",          "Número", "Não",  "Porta (vazio = padrão: FTP=21, SFTP=22)"),
            ("username",      "Texto",  "Sim",  "Usuário FTP/SFTP"),
            ("password",      "Texto",  "Não",  "Senha do usuário"),
            ("local_path",    "Texto",  "Cond.", "Caminho local do arquivo. Ex: saida/relatorio.csv"),
            ("remote_path",   "Texto",  "Cond.", "Caminho remoto no servidor. Ex: /public/relatorio.csv"),
            ("variable_name", "Texto",  "Não",  "Variável onde salvar lista de arquivos (action=list, padrão: ftp_lista)"),
            ("timeout",       "Número", "Não",  "Timeout em segundos (padrão: 30)"),
        ],
        "example": "# Upload FTP:\nprotocol: ftp\naction: upload\nhost: ftp.meusite.com\nusername: admin\npassword: senha123\nlocal_path: saida/relatorio.csv\nremote_path: /public/relatorio.csv\n\n# Download SFTP:\nprotocol: sftp\naction: download\nhost: 192.168.1.100\nport: 22\nusername: deploy\npassword: {{ftp_senha}}\nremote_path: /var/data/arquivo.xlsx\nlocal_path: downloads/arquivo.xlsx\n\n# Listar arquivos:\naction: list\nremote_path: /public\nvariable_name: arquivos_remotos",
        "tip": "FTP usa ftplib nativo do Python — sem instalar nada. SFTP requer 'pip install paramiko'. list salva a lista como variável e gera {{ftp_lista_total}} com a contagem. Use {{variavel}} nos campos para senhas e caminhos dinâmicos."
    },

    "SmartClickBlock": {
        "title": "Smart Click",
        "description": "Clica em um elemento com redundância. Se o primeiro seletor falhar, tenta os próximos automaticamente.",
        "params": [
            ("selector_1",       "Texto",  "Sim", "Seletor CSS ou XPath principal"),
            ("selector_2",       "Texto",  "Não", "Segundo seletor caso o primeiro falhe"),
            ("selector_3",       "Texto",  "Não", "Terceiro seletor de emergência"),
            ("timeout_per_try",  "Número", "Sim", "Segundos de espera para cada tentativa"),
        ],
        "example": "selector_1: //button[@id='login']\nselector_2: .btn-submit\nselector_3: #main-action\ntimeout_per_try: 5",
        "tip": "Use seletores de tipos diferentes (ID, classe, XPath) para aumentar a resiliência."
    },

    "SubfluxoBlock": {
        "title": "Subfluxo",
        "description": (
            "Executa outro fluxo JSON dentro do fluxo atual, permitindo reutilizar "
            "sequências de automação em múltiplos fluxos sem duplicar blocos. "
            "Ideal para ações repetidas como login, logout, setup inicial, etc."
        ),
        "params": [
            ("flow_name",        "Texto",    "Sim", "Nome do fluxo a executar (sem .json). Ex: login_sistema"),
            ("share_variables",  "Booleano", "Não", "Se ativo, o subfluxo enxerga as variáveis do fluxo pai durante execução."),
            ("export_variables", "Booleano", "Não", "Se ativo, as variáveis criadas no subfluxo ficam disponíveis no fluxo pai após execução."),
            ("stop_on_failure",  "Booleano", "Não", "Se ativo, o fluxo pai para quando o subfluxo falhar."),
            ("flows_dir",        "Texto",    "Não", "Pasta onde os fluxos estão salvos. Padrão: flows/"),
        ],
        "example": (
            "# Subfluxo simples — chama login antes de scraping\n"
            "flow_name: login_sistema\n"
            "share_variables: true\n"
            "export_variables: true\n"
            "stop_on_failure: true\n\n"
            "# Após o subfluxo, use as variáveis exportadas:\n"
            "# {{login_sistema_status}} → 'sucesso' ou 'falhou'\n"
            "# {{login_sistema_ok}}     → número de passos OK\n"
            "# {{login_sistema_total}}  → total de passos"
        ),
        "tip": (
            "Crie um fluxo 'login_sistema.json' com os passos de autenticação "
            "e chame-o via Subfluxo em todos os fluxos que precisam de login. "
            "Quando o processo mudar, edita só esse arquivo."
        ),
    },

}