"""
Documentação inline de cada bloco do PyFlow RPA.
Cada entrada contém: descrição, parâmetros e exemplo de uso.
"""

BLOCK_DOCS = {

    "OpenBrowserBlock": {
        "title": "Abrir Navegador",
        "description": "Abre o Google Chrome em uma URL especificada. Deve ser o primeiro bloco em fluxos de automação web. O driver fica ativo para todos os blocos seguintes.",
        "params": [
            ("url", "Texto", "Sim", "URL completa. Ex: https://google.com"),
            ("maximized", "Booleano", "Não", "Abre o navegador maximizado na tela"),
        ],
        "example": "url: https://www.google.com\nmaximized: True",
        "tip": "Se a URL não começar com http, o prefixo https:// é adicionado automaticamente."
    },

    "ClickElementBlock": {
        "title": "Clicar em Elemento",
        "description": "Localiza um elemento na página pelo seletor CSS e clica nele. Aguarda o elemento estar clicável antes de agir.",
        "params": [
            ("selector", "Texto", "Sim", "Seletor CSS. Ex: #btn-login, .btn-submit"),
            ("timeout", "Número", "Não", "Segundos para aguardar o elemento (padrão: 10)"),
        ],
        "example": "selector: #btn-entrar\ntimeout: 10",
        "tip": "No DevTools (F12): botão direito no elemento → Copiar → Copiar selector."
    },

    "FillFieldBlock": {
        "title": "Preencher Campo",
        "description": "Localiza um campo de texto e digita o valor informado. Suporta variáveis dinâmicas.",
        "params": [
            ("selector", "Texto", "Sim", "Seletor CSS do campo. Ex: input[name='email']"),
            ("value", "Texto", "Sim", "Texto a digitar. Aceita {{variavel}}"),
            ("clear_before", "Booleano", "Não", "Limpa o campo antes de digitar (padrão: True)"),
            ("timeout", "Número", "Não", "Segundos para aguardar o campo (padrão: 10)"),
        ],
        "example": "selector: #campo-busca\nvalue: {{termo_busca}}\nclear_before: True",
        "tip": "Use {{nome_variavel}} para inserir valores dinâmicos extraídos por outros blocos."
    },

    "ExtractTextBlock": {
        "title": "Extrair Texto",
        "description": "Extrai o texto visível de um elemento e salva como variável. Tenta text, innerText e textContent automaticamente.",
        "params": [
            ("selector", "Texto", "Sim", "Seletor CSS. Ex: h1, .titulo-produto, #preco"),
            ("variable_name", "Texto", "Não", "Nome da variável onde salvar (padrão: texto_extraido)"),
            ("timeout", "Número", "Não", "Segundos para aguardar o elemento (padrão: 10)"),
        ],
        "example": "selector: h1\nvariable_name: titulo_pagina\ntimeout: 10",
        "tip": "O valor fica disponível como {{titulo_pagina}} em todos os blocos seguintes."
    },

    "ExtractListBlock": {
        "title": "Extrair Lista",
        "description": "Extrai o texto (ou atributo) de todos os elementos que correspondem ao seletor e salva como lista. Ideal para usar com o bloco Para Cada.",
        "params": [
            ("selector", "Texto", "Sim", "Seletor CSS. Ex: .product-title, ul li"),
            ("attribute", "Texto", "Não", "Atributo a extrair. Ex: href, src. Vazio = texto"),
            ("variable_name", "Texto", "Não", "Nome da variável lista (padrão: lista_extraida)"),
            ("limit", "Número", "Não", "Máximo de itens. 0 = sem limite"),
            ("filter_empty", "Booleano", "Não", "Ignora itens vazios (padrão: True)"),
            ("timeout", "Número", "Não", "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "selector: .product_pod h3 a\nvariable_name: titulos\nlimit: 10",
        "tip": "Gera também {{titulos_total}} e {{titulos_primeiro}} automaticamente."
    },

    "PressKeyBlock": {
        "title": "Pressionar Tecla",
        "description": "Pressiona uma tecla especial em um elemento ou na página inteira do navegador.",
        "params": [
            ("key", "Texto", "Sim", "Tecla: Enter, Tab, Escape, Backspace, Delete, Space, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Home, End, F5"),
            ("selector", "Texto", "Não", "Seletor CSS do elemento. Vazio = pressiona no body"),
            ("timeout", "Número", "Não", "Segundos para aguardar o elemento (padrão: 10)"),
        ],
        "example": "key: Enter\nselector: #campo-busca",
        "tip": "Para submeter um formulário, use o seletor do campo + tecla Enter."
    },

    "ScrollPageBlock": {
        "title": "Scroll na Página",
        "description": "Rola a página para uma direção ou até um elemento específico.",
        "params": [
            ("direction", "Texto", "Sim", "top = topo | bottom = final | element = até elemento | outro = usa pixels"),
            ("selector", "Texto", "Cond.", "Seletor CSS (somente para direction=element)"),
            ("pixels", "Número", "Cond.", "Pixels para rolar (quando direction não é top/bottom/element)"),
        ],
        "example": "direction: bottom\n\n# Ou até um elemento:\ndirection: element\nselector: #rodape",
        "tip": "Use direction=bottom para carregar conteúdo lazy-loaded antes de extrair."
    },

    "ScreenshotBlock": {
        "title": "Tirar Screenshot",
        "description": "Salva uma captura de tela completa da página atual em arquivo PNG.",
        "params": [
            ("filename", "Texto", "Não", "Nome do arquivo sem extensão. Vazio = usa data/hora"),
            ("folder", "Texto", "Não", "Pasta de destino (padrão: screenshots). Criada automaticamente"),
        ],
        "example": "filename: resultado_login\nfolder: screenshots",
        "tip": "Ideal para usar após ações importantes para registrar o estado da página."
    },

    "GetCurrentUrlBlock": {
        "title": "Obter URL Atual",
        "description": "Captura a URL atual do navegador e salva como variável.",
        "params": [
            ("variable_name", "Texto", "Não", "Nome da variável (padrão: url_atual)"),
        ],
        "example": "variable_name: url_pagina_produto",
        "tip": "Útil para salvar URLs de produtos encontrados durante scraping."
    },

    "MouseActionBlock": {
        "title": "Ação de Mouse",
        "description": "Executa ações avançadas de mouse usando ActionChains do Selenium.",
        "params": [
            ("action", "Texto", "Sim", "double_click | right_click | hover | drag_and_drop | click_offset | move_to"),
            ("selector", "Texto", "Cond.", "Seletor CSS do elemento alvo"),
            ("target_selector", "Texto", "Cond.", "Seletor do destino (somente drag_and_drop)"),
            ("offset_x", "Número", "Não", "Offset X em pixels (click_offset e move_to)"),
            ("offset_y", "Número", "Não", "Offset Y em pixels (click_offset e move_to)"),
            ("timeout", "Número", "Não", "Segundos para aguardar (padrão: 10)"),
        ],
        "example": "action: hover\nselector: .menu-dropdown\n\n# Duplo clique:\naction: double_click\nselector: .item-editavel",
        "tip": "Use hover para ativar menus dropdown antes de clicar em submenus."
    },

    "NavigateToUrlBlock": {
        "title": "Navegar para URL",
        "description": "Navega para uma URL no navegador já aberto, sem abrir nova janela.",
        "params": [
            ("url", "Texto", "Sim", "URL de destino. Aceita {{variavel}}"),
        ],
        "example": "url: https://exemplo.com/produto/{{id_produto}}",
        "tip": "Diferente do Abrir Navegador, este bloco reutiliza a janela já aberta."
    },

    "GoBackBlock": {
        "title": "Voltar Página",
        "description": "Equivalente ao botão Voltar do navegador. Vai para a página anterior no histórico.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Útil após acessar um produto para voltar à listagem."
    },

    "GoForwardBlock": {
        "title": "Avançar Página",
        "description": "Equivalente ao botão Avançar do navegador.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Só funciona se você voltou antes — equivale ao botão → do browser."
    },

    "RefreshPageBlock": {
        "title": "Atualizar Página",
        "description": "Recarrega a página atual. Equivalente ao F5.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Use após ações que podem levar tempo para refletir na página."
    },

    "OpenNewTabBlock": {
        "title": "Abrir Nova Aba",
        "description": "Abre uma nova aba no navegador e opcionalmente navega para uma URL.",
        "params": [
            ("url", "Texto", "Não", "URL a abrir na nova aba. Vazio = aba em branco"),
        ],
        "example": "url: https://github.com",
        "tip": "Após abrir a nova aba, o foco muda automaticamente para ela."
    },

    "CloseTabBlock": {
        "title": "Fechar Aba",
        "description": "Fecha a aba atual e retorna para a aba anterior automaticamente.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Não funciona se houver apenas uma aba — use Fechar Navegador nesses casos."
    },

    "SwitchTabBlock": {
        "title": "Trocar de Aba",
        "description": "Muda o foco para uma aba específica pelo índice numérico.",
        "params": [
            ("tab_index", "Número", "Sim", "Índice da aba: 0 = primeira, 1 = segunda..."),
        ],
        "example": "tab_index: 0",
        "tip": "Use após Abrir Nova Aba para voltar para a aba original com tab_index: 0."
    },

    "CloseBrowserBlock": {
        "title": "Fechar Navegador",
        "description": "Fecha todas as abas e encerra completamente o processo do Chrome.",
        "params": [],
        "example": "Sem parâmetros.",
        "tip": "Recomendado como último bloco em fluxos web para liberar memória."
    },

    "WaitBlock": {
        "title": "Aguardar",
        "description": "Pausa a execução por um número determinado de segundos.",
        "params": [
            ("seconds", "Número", "Sim", "Tempo de pausa. Aceita decimais: 1.5 = 1,5 segundos"),
        ],
        "example": "seconds: 3",
        "tip": "Use após ações que precisam de tempo para carregar (login, navegação, etc)."
    },

    "IfBlock": {
        "title": "Condição (If)",
        "description": "Verifica uma condição e pula os próximos N blocos se for falsa.",
        "params": [
            ("condition_type", "Texto", "Sim", "element_exists | element_not_exists | variable_contains | variable_equals"),
            ("selector", "Texto", "Cond.", "Seletor CSS (para condições de elemento)"),
            ("variable_name", "Texto", "Cond.", "Nome da variável (para condições de variável)"),
            ("expected_value", "Texto", "Cond.", "Valor esperado (para contains/equals)"),
            ("skip_on_false", "Número", "Não", "Blocos a pular se falso (padrão: 1)"),
        ],
        "example": "condition_type: variable_contains\nvariable_name: titulo\nexpected_value: Python\nskip_on_false: 2",
        "tip": "skip_on_false=2 pula os próximos 2 blocos. A condição verdadeira continua normalmente."
    },

    "LoopBlock": {
        "title": "Loop (Repetir)",
        "description": "Repete um grupo de blocos N vezes.",
        "params": [
            ("times", "Número", "Sim", "Número de repetições"),
            ("blocks_count", "Número", "Sim", "Quantos blocos seguintes fazem parte do loop"),
            ("delay_between", "Número", "Não", "Pausa em segundos entre repetições (padrão: 0)"),
        ],
        "example": "times: 5\nblocks_count: 2\ndelay_between: 1",
        "tip": "Loop com blocks_count=2 inclui os 2 blocos imediatamente abaixo dele."
    },

    "ForEachBlock": {
        "title": "Para Cada (For Each)",
        "description": "Itera sobre uma lista executando blocos para cada item.",
        "params": [
            ("items", "Texto", "Sim", "Lista separada por vírgula OU nome de variável de lista"),
            ("variable_name", "Texto", "Não", "Variável de iteração (padrão: item_atual)"),
            ("blocks_count", "Número", "Sim", "Quantos blocos seguintes fazem parte do loop"),
            ("delay_between", "Número", "Não", "Pausa entre iterações em segundos (padrão: 0)"),
        ],
        "example": "# Lista literal:\nitems: google.com, github.com\nvariable_name: url\nblocks_count: 2\n\n# Lista de variável (do Ler CSV):\nitems: csv_linhas\nvariable_name: email",
        "tip": "Em cada iteração, {{item_atual}} recebe o valor do item corrente da lista."
    },

    "ShowMessageBlock": {
        "title": "Exibir Mensagem",
        "description": "Abre uma caixa de diálogo modal. O fluxo pausa até o usuário clicar OK.",
        "params": [
            ("title", "Texto", "Não", "Título da janela (padrão: PyFlow RPA)"),
            ("message", "Texto", "Sim", "Mensagem exibida. Aceita {{variavel}} e \\n para quebra de linha"),
            ("kind", "Texto", "Não", "info | warning | error (padrão: info)"),
        ],
        "example": "title: Resultado\nmessage: Extração concluída!\nTítulo: {{titulo}}\nkind: info",
        "tip": "Ideal para debug: exibe valores de variáveis durante a execução."
    },

    "DesktopNotificationBlock": {
        "title": "Notificação Desktop",
        "description": "Exibe uma notificação sem interromper a execução do fluxo.",
        "params": [
            ("title", "Texto", "Sim", "Título da notificação"),
            ("message", "Texto", "Sim", "Mensagem. Aceita {{variavel}}"),
            ("duration", "Número", "Não", "Duração em milissegundos (padrão: 5000)"),
        ],
        "example": "title: ✅ Concluído\nmessage: Fluxo finalizado! {{total}} itens.\nduration: 7000",
        "tip": "Diferente do Exibir Mensagem, não pausa o fluxo."
    },

    "TextManipulationBlock": {
        "title": "Manipular Texto",
        "description": "Aplica transformações em uma variável de texto. 14 operações disponíveis.",
        "params": [
            ("input_variable", "Texto", "Sim", "Nome da variável de entrada"),
            ("operation", "Texto", "Sim", "upper | lower | trim | replace | regex_extract | regex_replace | split | join | count | contains | starts_with | ends_with | substring | length"),
            ("param1", "Texto", "Cond.", "Parâmetro 1 (depende da operação)"),
            ("param2", "Texto", "Cond.", "Parâmetro 2 (depende da operação)"),
            ("output_variable", "Texto", "Não", "Variável de saída. Vazio = sobrescreve a entrada"),
        ],
        "example": "# Extrair domínio do email:\ninput_variable: email\noperation: regex_extract\nparam1: @(.+)\noutput_variable: dominio\n\n# Substituir texto:\noperation: replace\nparam1: R$\nparam2: BRL",
        "tip": "upper/lower/trim não precisam de parâmetros. replace precisa de param1 e param2."
    },

    "KeyboardActionBlock": {
        "title": "Teclado do Sistema",
        "description": "Interage com o teclado do sistema operacional via PyAutoGUI. Funciona fora do navegador — digita texto, pressiona teclas e executa atalhos em qualquer janela ativa (Bloco de Notas, Excel, etc).",
        "params": [
            ("action", "Texto", "Sim", "type = digitar texto | press = pressionar tecla | hotkey = atalho de teclado"),
            ("value", "Texto", "Sim", "Texto a digitar, tecla ou atalho. Ex: ctrl+c, alt+tab, enter"),
            ("interval", "Número", "Não", "Intervalo em segundos entre cada tecla ao digitar (padrão: 0.05)"),
            ("delay_before", "Número", "Não", "Aguarda N segundos antes de executar — útil para focar a janela (padrão: 0)"),
        ],
        "example": "# Digitar texto:\naction: type\nvalue: Olá, mundo!\n\n# Pressionar tecla:\naction: press\nvalue: enter\n\n# Atalho Ctrl+C:\naction: hotkey\nvalue: ctrl+c\n\n# Abrir Executar do Windows:\naction: hotkey\nvalue: win+r\ndelay_before: 0.5",
        "tip": "Use delay_before para dar tempo de clicar na janela alvo antes de digitar. Failsafe: mover o mouse ao canto superior esquerdo cancela a execução do PyAutoGUI."
    },

    "ReadCsvBlock": {
        "title": "Ler CSV",
        "description": "Lê uma coluna de um arquivo CSV e salva como lista. Use com Para Cada para iterar.",
        "params": [
            ("filepath", "Texto", "Sim", "Caminho do arquivo. Ex: dados/lista.csv"),
            ("column", "Texto", "Não", "Nome da coluna ou índice numérico (padrão: 0)"),
            ("variable_name", "Texto", "Não", "Nome da variável lista (padrão: csv_linhas)"),
            ("skip_header", "Booleano", "Não", "Pula a primeira linha cabeçalho (padrão: True)"),
            ("delimiter", "Texto", "Não", "Separador do CSV: , ou ; ou | (padrão: ,)"),
        ],
        "example": "filepath: dados/emails.csv\ncolumn: email\nvariable_name: lista_emails\nskip_header: True",
        "tip": "Gera {{csv_linhas_total}} com a contagem e {{csv_linhas_primeiro}} com o primeiro item."
    },

    "SaveTextBlock": {
        "title": "Salvar em TXT",
        "description": "Salva texto em arquivo .txt. Pode sobrescrever ou adicionar ao final.",
        "params": [
            ("content", "Texto", "Sim", "Conteúdo a salvar. Aceita {{variavel}}"),
            ("filepath", "Texto", "Não", "Caminho do arquivo (padrão: saida/resultado.txt)"),
            ("mode", "Texto", "Não", "append = adiciona ao final | overwrite = substitui (padrão: append)"),
            ("add_timestamp", "Booleano", "Não", "Adiciona [data hora] em cada linha (padrão: False)"),
        ],
        "example": "content: {{url}} — {{titulo}}\nfilepath: saida/resultado.txt\nmode: append\nadd_timestamp: True",
        "tip": "A pasta de destino é criada automaticamente se não existir."
    },

    "SaveCsvBlock": {
        "title": "Salvar em CSV",
        "description": "Adiciona uma linha de dados em CSV. Cria o arquivo e cabeçalho automaticamente.",
        "params": [
            ("filepath", "Texto", "Não", "Caminho do arquivo CSV (padrão: saida/dados.csv)"),
            ("values", "Texto", "Sim", "Valores separados por pipe |. Ex: {{titulo}}|{{preco}}|{{url}}"),
            ("headers", "Texto", "Não", "Cabeçalhos separados por pipe |. Escritos apenas na criação"),
            ("delimiter", "Texto", "Não", "Separador do CSV (padrão: ,)"),
            ("add_timestamp", "Booleano", "Não", "Adiciona coluna de timestamp (padrão: False)"),
        ],
        "example": "filepath: saida/produtos.csv\nvalues: {{nome}}|{{preco}}|{{url_atual}}\nheaders: Nome|Preco|URL",
        "tip": "Use | para separar colunas no campo values, independente do delimiter do CSV."
    },

    "HttpRequestBlock": {
        "title": "HTTP Request",
        "description": "Realiza requisições HTTP para APIs REST. Suporta GET, POST, PUT, PATCH e DELETE.",
        "params": [
            ("method", "Texto", "Sim", "GET | POST | PUT | PATCH | DELETE"),
            ("url", "Texto", "Sim", "URL da API. Aceita {{variavel}}"),
            ("headers", "JSON", "Não", 'Headers como JSON. Ex: {"Authorization": "Bearer {{token}}"}'),
            ("body", "JSON", "Não", 'Body para POST/PUT/PATCH. Ex: {"nome": "{{nome}}"}'),
            ("json_field", "Texto", "Não", "Campo do JSON via dot notation. Ex: data.user.email"),
            ("variable_name", "Texto", "Não", "Variável para salvar a resposta (padrão: http_resposta)"),
            ("timeout", "Número", "Não", "Timeout em segundos (padrão: 15)"),
        ],
        "example": "method: GET\nurl: https://api.exemplo.com/users/{{id}}\njson_field: name\nvariable_name: nome_usuario",
        "tip": "Dot notation: data.user.email acessa response['data']['user']['email']. Use números para arrays: results.0.name"
    },

    "SendEmailBlock": {
        "title": "Enviar E-mail",
        "description": "Envia e-mail via SMTP. Suporta Gmail, Outlook, Yahoo e SMTP customizado.",
        "params": [
            ("provider", "Texto", "Não", "gmail | outlook | yahoo | custom (padrão: gmail)"),
            ("smtp_host", "Texto", "Cond.", "Servidor SMTP (somente para custom)"),
            ("smtp_port", "Número", "Cond.", "Porta SMTP (somente para custom). 587=TLS, 465=SSL"),
            ("sender_email", "Texto", "Sim", "E-mail do remetente"),
            ("sender_password", "Texto", "Sim", "Senha ou App Password do Gmail"),
            ("recipient", "Texto", "Sim", "Destinatário(s). Múltiplos separados por vírgula"),
            ("subject", "Texto", "Sim", "Assunto. Aceita {{variavel}}"),
            ("body_text", "Texto", "Não", "Corpo em texto simples. Aceita {{variavel}}"),
            ("body_html", "Texto", "Não", "Corpo em HTML. Aceita {{variavel}}"),
        ],
        "example": "provider: gmail\nsender_email: meu@gmail.com\nsender_password: abcd efgh ijkl mnop\nrecipient: destino@email.com\nsubject: Relatório {{data}}\nbody_text: Segue o relatório de {{data}}.",
        "tip": "Para Gmail: gere uma App Password em myaccount.google.com/apppasswords (requer 2FA ativo)."
    },
}