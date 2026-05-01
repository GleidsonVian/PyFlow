import os
import re
from datetime import datetime


def _scroll_code(p):
    direction = p.get("direction", "bottom")
    if direction == "top":
        scroll_line = "driver.execute_script('window.scrollTo(0, 0);')"
    elif direction == "bottom":
        scroll_line = "driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')"
    elif direction == "element":
        sel = repr(p.get("selector", ""))
        smooth = "{behavior: 'smooth', block: 'center'}"
        scroll_line = "driver.execute_script('arguments[0].scrollIntoView(" + smooth + ");', driver.find_element(By.CSS_SELECTOR, " + sel + "))"
    else:
        px = p.get("pixels", 500)
        scroll_line = "driver.execute_script('window.scrollBy(0, " + str(px) + ");')"
    return (
        "\n    # Scroll na Página\n"
        "    " + scroll_line + "\n"
        '    print("  ✓ Scroll executado")\n'
    )


def _press_key_code(p):
    key = p.get("key", "Enter")
    selector = p.get("selector", "")
    timeout = p.get("timeout", 10)
    if selector:
        action = f"WebDriverWait(driver, {timeout}).until(EC.presence_of_element_located((By.CSS_SELECTOR, {repr(selector)}))).send_keys(_key)"
    else:
        action = "driver.find_element(By.TAG_NAME, 'body').send_keys(_key)"
    return f"""
    # Pressionar Tecla
    _key_map = {{"Enter": Keys.ENTER, "Tab": Keys.TAB, "Escape": Keys.ESCAPE,
                 "Backspace": Keys.BACK_SPACE, "Delete": Keys.DELETE, "Space": Keys.SPACE,
                 "ArrowUp": Keys.ARROW_UP, "ArrowDown": Keys.ARROW_DOWN,
                 "ArrowLeft": Keys.ARROW_LEFT, "ArrowRight": Keys.ARROW_RIGHT, "F5": Keys.F5}}
    _key = _key_map.get({repr(key)})
    if _key:
        {action}
    print("  ✓ Tecla pressionada:", {repr(key)})
"""


def _http_code(p):
    method = p.get("method", "GET")
    url = p.get("url", "")
    body = p.get("body", "")
    timeout = p.get("timeout", 15)
    json_field = p.get("json_field", "")
    var_name = p.get("variable_name", "http_resposta")

    body_line = f"_body = {repr(body.encode('utf-8'))}" if body and method in ("POST", "PUT", "PATCH") else "_body = None"

    if json_field:
        extract = f"""
    _val = _parsed
    for _k in {repr(json_field.split('.'))}:
        if isinstance(_val, dict): _val = _val.get(_k)
        elif isinstance(_val, list):
            try: _val = _val[int(_k)]
            except: _val = None
        else: _val = None"""
    else:
        extract = "    _val = _parsed"

    return f"""
    # HTTP Request
    import urllib.request as _urllib, json as _json, ssl as _ssl
    _ctx2 = _ssl.create_default_context()
    {body_line}
    _req = _urllib.Request({repr(url)}, data=_body, headers={{"Content-Type": "application/json"}}, method={repr(method)})
    with _urllib.urlopen(_req, timeout={timeout}) as _r:
        _raw = _r.read().decode("utf-8")
    _parsed = _json.loads(_raw)
{extract}
    context[{repr(var_name)}] = str(_val) if _val is not None else ""
    print("  ✓ HTTP {method} →", {repr(var_name)}, ":", str(_val)[:60])
"""


BLOCK_CODEGEN = {

    "OpenBrowserBlock": lambda p: f"""
    # Abrir Navegador
    options = Options()
    {"options.add_argument('--start-maximized')" if p.get("maximized") else ""}
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get({repr(p.get("url", ""))})
    print("  ✓ Navegador aberto em:", {repr(p.get("url", ""))})
""",

    "ClickElementBlock": lambda p: f"""
    # Clicar em Elemento
    element = WebDriverWait(driver, {p.get("timeout", 10)}).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, {repr(p.get("selector", ""))}))
    )
    element.click()
    print("  ✓ Elemento clicado:", {repr(p.get("selector", ""))})
""",

    "FillFieldBlock": lambda p: f"""
    # Preencher Campo
    element = WebDriverWait(driver, {p.get("timeout", 10)}).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, {repr(p.get("selector", ""))}))
    )
    {"element.clear()" if p.get("clear_before", True) else ""}
    element.send_keys(resolve({repr(p.get("value", ""))}, context))
    print("  ✓ Campo preenchido:", {repr(p.get("selector", ""))})
""",

    "ExtractTextBlock": lambda p: f"""
    # Extrair Texto
    element = WebDriverWait(driver, {p.get("timeout", 10)}).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, {repr(p.get("selector", ""))}))
    )
    _text = element.text.strip()
    if not _text:
        _text = (driver.execute_script("return arguments[0].innerText;", element) or "").strip()
    context[{repr(p.get("variable_name", "texto_extraido"))}] = _text
    print("  ✓ Texto extraído →", {repr(p.get("variable_name", "texto_extraido"))}, ":", repr(_text[:60]))
""",

    "PressKeyBlock":  _press_key_code,
    "ScrollPageBlock": _scroll_code,

    "GetCurrentUrlBlock": lambda p: f"""
    # Obter URL Atual
    context[{repr(p.get("variable_name", "url_atual"))}] = driver.current_url
    print("  ✓ URL capturada →", {repr(p.get("variable_name", "url_atual"))}, ":", driver.current_url)
""",

    "ScreenshotBlock": lambda p: f"""
    # Tirar Screenshot
    _folder = {repr(p.get("folder", "screenshots"))}
    _filename = {repr(p.get("filename", "")) or 'f"screenshot_{{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}}.png"'}
    if not _filename.endswith(".png"): _filename += ".png"
    os.makedirs(_folder, exist_ok=True)
    driver.save_screenshot(os.path.join(_folder, _filename))
    print("  ✓ Screenshot salva em:", os.path.join(_folder, _filename))
""",

    "WaitBlock": lambda p: f"""
    # Aguardar
    time.sleep({p.get("seconds", 3)})
    print("  ✓ Aguardou {p.get('seconds', 3)} segundo(s)")
""",

    "ShowMessageBlock": lambda p: f"""
    # Exibir Mensagem
    _msg = resolve({repr(p.get("message", ""))}, context)
    print(f"  💬 {p.get('title','PyFlow RPA')}: {{_msg}}")
    input("  Pressione ENTER para continuar...")
""",

    "HttpRequestBlock": _http_code,

    "SaveTextBlock": lambda p: f"""
    # Salvar em TXT
    _folder = os.path.dirname({repr(p.get("filepath", "saida/resultado.txt"))})
    if _folder: os.makedirs(_folder, exist_ok=True)
    _line = resolve({repr(p.get("content", ""))}, context)
    {"_line = f'[{{datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}}] {{_line}}'" if p.get("add_timestamp") else ""}
    with open({repr(p.get("filepath", "saida/resultado.txt"))}, {"'w'" if p.get("mode") == "overwrite" else "'a'"}, encoding="utf-8") as _f:
        _f.write(_line + "\\n")
    print("  ✓ Texto salvo em:", {repr(p.get("filepath", "saida/resultado.txt"))})
""",

    "SaveCsvBlock": lambda p: f"""
    # Salvar em CSV
    import csv as _csv
    _folder = os.path.dirname({repr(p.get("filepath", "saida/dados.csv"))})
    if _folder: os.makedirs(_folder, exist_ok=True)
    _file_exists = os.path.exists({repr(p.get("filepath", "saida/dados.csv"))})
    _values = [resolve(v.strip(), context) for v in {repr(p.get("values", ""))}.split("|")]
    with open({repr(p.get("filepath", "saida/dados.csv"))}, "a", newline="", encoding="utf-8-sig") as _f:
        _w = _csv.writer(_f, delimiter={repr(p.get("delimiter", ","))})
        if not _file_exists and {repr(bool(p.get("headers", "")))}: _w.writerow([h.strip() for h in {repr(p.get("headers", ""))}.split("|")])
        _w.writerow(_values)
    print("  ✓ Linha salva em:", {repr(p.get("filepath", "saida/dados.csv"))})
""",

    "ReadCsvBlock": lambda p: f"""
    # Ler CSV
    import csv as _csv
    with open({repr(p.get("filepath", ""))}, "r", encoding="utf-8-sig") as _f:
        _rows = list(_csv.reader(_f, delimiter={repr(p.get("delimiter", ","))}))
    _data = _rows[{"1" if p.get("skip_header", True) else "0"}:]
    _col = {repr(p.get("column", "0"))}
    _col_idx = int(_col) if _col.isdigit() else 0
    _values = [r[_col_idx].strip() for r in _data if _col_idx < len(r)]
    context[{repr(p.get("variable_name", "csv_linhas"))}] = _values
    context[{repr(p.get("variable_name", "csv_linhas") + "_total")}] = str(len(_values))
    print("  ✓ CSV lido:", len(_values), "linha(s)")
""",

    "SendEmailBlock": lambda p: f"""
    # Enviar E-mail
    import smtplib as _smtp, ssl as _ssl2
    from email.mime.multipart import MIMEMultipart as _MMP
    from email.mime.text import MIMEText as _MMT
    _msg = _MMP("alternative")
    _msg["From"]    = {repr(p.get("sender_email", ""))}
    _msg["To"]      = {repr(p.get("recipient", ""))}
    _msg["Subject"] = resolve({repr(p.get("subject", ""))}, context)
    if {repr(p.get("body_text", ""))}: _msg.attach(_MMT(resolve({repr(p.get("body_text", ""))}, context), "plain", "utf-8"))
    if {repr(p.get("body_html", ""))}: _msg.attach(_MMT(resolve({repr(p.get("body_html", ""))}, context), "html", "utf-8"))
    _sctx = _ssl2.create_default_context()
    with _smtp.SMTP("smtp.gmail.com", 587) as _s:
        _s.starttls(context=_sctx)
        _s.login({repr(p.get("sender_email", ""))}, {repr(p.get("sender_password", ""))})
        _s.sendmail({repr(p.get("sender_email", ""))}, {repr(p.get("recipient", ""))}, _msg.as_string())
    print("  ✓ E-mail enviado para:", {repr(p.get("recipient", ""))})
""",
}


SCRIPT_HEADER = '''#!/usr/bin/env python3
"""
{flow_name}
Exportado pelo PyFlow RPA em {exported_at}
"""
import os
import re
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

context = {{}}
driver  = None


def resolve(text: str, ctx: dict) -> str:
    return re.sub(r"\\{{\\{{(.+?)\\}}\\}}", lambda m: str(ctx.get(m.group(1).strip(), m.group(0))), text)


def main():
    global driver
    print("\\n⚡ Iniciando: {flow_name}\\n")
'''

SCRIPT_FOOTER = '''
    print("\\n✅ Fluxo concluído!")
    if driver:
        input("\\nPressione ENTER para fechar o navegador...")
        driver.quit()


if __name__ == "__main__":
    main()
'''


class FlowExporter:
    def export(self, flow_name: str, steps: list, output_dir: str = "exports") -> str:
        os.makedirs(output_dir, exist_ok=True)
        safe_name = flow_name.strip().replace(" ", "_").lower()
        filepath = os.path.join(output_dir, f"{safe_name}.py")

        lines = [SCRIPT_HEADER.format(
            flow_name=flow_name,
            exported_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )]

        for i, step in enumerate(steps):
            block_name = step.get("block", "")
            params     = step.get("params", {})
            codegen    = BLOCK_CODEGEN.get(block_name)

            lines.append(f"\n    # ── Passo {i + 1}: {block_name} ──")
            lines.append(f'    print("\\n[{i+1}/{len(steps)}] {block_name}")')

            if codegen:
                try:
                    lines.append(codegen(params))
                except Exception as e:
                    lines.append(f"    # ⚠ Erro ao gerar código para {block_name}: {e}\n    pass")
            else:
                lines.append(f"    # Bloco '{block_name}' não suportado na exportação\n    pass")

        lines.append(SCRIPT_FOOTER)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath