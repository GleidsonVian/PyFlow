import sys
import io
import traceback
from blocks.base_block import BaseBlock
import engine.execution_context as ctx

class PythonScriptBlock(BaseBlock):
    name = "Script Python"
    description = "Executa um script Python customizado. Use a variável 'var' para acessar e modificar as variáveis do PyFlow."
    category = "Sistema"

    params_schema = [
        {
            "name": "code",
            "label": "Código Python",
            "type": "text",
            "required": True,
            "default": "# Escreva seu código aqui\n# Exemplo: var['nome'] = var['nome'].upper()\n",
            "placeholder": "Ex: var['total'] = var['a'] + var['b']"
        }
    ]

    def execute(self, params: dict) -> dict:
        code = params.get("code", "").strip()
        if not code:
            return {"success": False, "message": "Nenhum código fornecido."}

        # Contexto de execução
        variables = ctx.get()
        
        # Redireciona stdout para capturar prints
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_capture

        try:
            # Prepara o ambiente de execução
            exec_globals = {
                "var": variables,
                "variables": variables,
                "ctx": variables,
                "print": print,
                "__builtins__": __builtins__
            }
            
            # Executa o código
            exec(code, exec_globals)
            
            # Restaura stdout
            sys.stdout = old_stdout
            output = stdout_capture.getvalue().strip()
            
            msg = "Script executado com sucesso."
            if output:
                msg += f"\nOutput:\n{output}"
            
            return {
                "success": True,
                "message": msg,
                "data": {"output": output}
            }

        except Exception:
            sys.stdout = old_stdout
            err = traceback.format_exc()
            # Limpa o traceback para mostrar apenas a parte relevante do erro do usuário
            lines = err.splitlines()
            relevant_err = "\n".join(lines[3:]) if len(lines) > 3 else err
            
            return {
                "success": False,
                "message": f"Erro no script:\n{relevant_err}"
            }
