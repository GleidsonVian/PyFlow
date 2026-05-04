"""
Motor de execução em modo debug step-by-step.
Executa um bloco por vez, aguardando sinal para avançar.
"""
import threading
from blocks.base_block import BaseBlock
import engine.execution_context as ctx
from engine.execution_context import resolve_params


class DebugRunner:
    """
    Executa blocos um por vez.
    Aguarda chamada de .step() para avançar para o próximo bloco.
    """

    def __init__(self,
                 on_step_ready=None,    # (index, block, params) — bloco pronto para executar
                 on_step_done=None,     # (index, block, result) — bloco executado
                 on_step_error=None,    # (index, block, result) — bloco falhou
                 on_finished=None,      # (ok, total) — execução encerrada
                 on_paused=None):       # (index, block) — aguardando ação do usuário
        self.on_step_ready  = on_step_ready
        self.on_step_done   = on_step_done
        self.on_step_error  = on_step_error
        self.on_finished    = on_finished
        self.on_paused      = on_paused

        self._steps         = []
        self._index         = 0
        self._results       = []
        self._running       = False
        self._paused        = True
        self._advance_event = threading.Event()
        self._stop_flag     = False
        self._thread        = None

    def load(self, steps: list):
        ctx.clear()
        self._steps   = steps
        self._index   = 0
        self._results = []
        self._paused  = True
        self._stop_flag = False

    def start(self):
        """Inicia a thread de execução e aguarda no primeiro bloco."""
        self._running = True
        self._advance_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def step(self):
        """Avança um bloco (modo passo a passo)."""
        self._paused = False
        self._advance_event.set()

    def resume(self):
        """Executa todos os blocos restantes sem pausar."""
        self._paused = False
        self._advance_event.set()

    def stop(self):
        """Para a execução."""
        self._stop_flag = True
        self._paused = False
        self._advance_event.set()

    @property
    def current_index(self) -> int:
        return self._index

    @property
    def total(self) -> int:
        return len(self._steps)

    @property
    def is_running(self) -> bool:
        return self._running

    def _loop(self):
        total = len(self._steps)
        ok    = 0

        while self._index < total and not self._stop_flag:
            step   = self._steps[self._index]
            block  = step["block_instance"]
            params = resolve_params(step.get("params", {}))

            # Notifica que o bloco está pronto e aguarda sinal
            if self.on_step_ready:
                self.on_step_ready(self._index, block, params)

            # Aguarda o usuário avançar
            self._advance_event.clear()
            self._advance_event.wait()

            if self._stop_flag:
                break

            # Executa o bloco
            result = block.execute(params)
            result["step_index"] = self._index
            result["block_name"] = block.name
            self._results.append(result)

            if result.get("success"):
                ok += 1
                if self.on_step_done:
                    self.on_step_done(self._index, block, result)
            else:
                if self.on_step_error:
                    self.on_step_error(self._index, block, result)
                # Para no erro em modo debug
                break

            self._index += 1

            # Se ainda em modo passo a passo, pausa antes do próximo
            if self._paused and self._index < total:
                self._advance_event.clear()

        self._running = False
        if self.on_finished:
            self.on_finished(ok, len(self._results))
