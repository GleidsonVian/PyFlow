"""
Agendador de fluxos do PyFlow RPA.
Coloque em: ui/scheduler_dialog.py
"""
import threading
import schedule
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QWidget, QListWidget,
    QListWidgetItem, QTimeEdit, QSpinBox, QCheckBox,
    QMessageBox, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTime, QTimer, QObject
from PySide6.QtGui import QColor, QFont


# ── Signal bridge para thread segura ──────────────────────────────────
class SchedulerSignals(QObject):
    trigger_run = Signal(str)   # emite o filepath do fluxo a executar
    log_message = Signal(str)   # emite mensagem para o log interno


_signals = SchedulerSignals()


class ScheduledJob:
    """Representa um agendamento configurado."""

    TYPES = {
        "once":    "Uma vez",
        "repeat":  "Repetir",
        "weekday": "Dias da semana",
    }

    WEEKDAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    WEEKDAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    def __init__(self, job_type: str, flow_name: str, flow_path: str,
                 time_str: str = "", interval: int = 0, interval_unit: str = "minutes",
                 weekdays: list = None):
        self.id          = id(self)
        self.job_type    = job_type
        self.flow_name   = flow_name
        self.flow_path   = flow_path
        self.time_str    = time_str      # "HH:MM" para once e weekday
        self.interval    = interval      # para repeat
        self.interval_unit = interval_unit  # minutes ou hours
        self.weekdays    = weekdays or []
        self.active      = True
        self.runs        = 0
        self.last_run    = ""
        self._schedule_jobs = []

    def describe(self) -> str:
        t = self.TYPES.get(self.job_type, "?")
        if self.job_type == "once":
            return f"{t} às {self.time_str}"
        elif self.job_type == "repeat":
            unit = "min" if self.interval_unit == "minutes" else "h"
            return f"A cada {self.interval} {unit}"
        elif self.job_type == "weekday":
            days = ", ".join(self.WEEKDAYS[i] for i in self.weekdays)
            return f"{days} às {self.time_str}"
        return t


class SchedulerEngine:
    """Motor de agendamento rodando em thread separada."""

    def __init__(self):
        self._jobs: list[ScheduledJob] = []
        self._running = False
        self._thread = None

    def add_job(self, job: ScheduledJob):
        self._jobs.append(job)
        self._register(job)

    def remove_job(self, job: ScheduledJob):
        for j in job._schedule_jobs:
            try:
                schedule.cancel_job(j)
            except Exception:
                pass
        job._schedule_jobs.clear()
        if job in self._jobs:
            self._jobs.remove(job)

    def _register(self, job: ScheduledJob):
        def run_job():
            if not job.active:
                return
            job.runs += 1
            job.last_run = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            msg = f"[{job.last_run}] Executando: {job.flow_name}"
            _signals.log_message.emit(msg)
            _signals.trigger_run.emit(job.flow_path)
            # once: cancela após primeira execução
            if job.job_type == "once":
                job.active = False

        if job.job_type == "once":
            j = schedule.every().day.at(job.time_str).do(run_job)
            job._schedule_jobs.append(j)

        elif job.job_type == "repeat":
            if job.interval_unit == "minutes":
                j = schedule.every(job.interval).minutes.do(run_job)
            else:
                j = schedule.every(job.interval).hours.do(run_job)
            job._schedule_jobs.append(j)

        elif job.job_type == "weekday":
            day_map = {
                0: schedule.every().monday,
                1: schedule.every().tuesday,
                2: schedule.every().wednesday,
                3: schedule.every().thursday,
                4: schedule.every().friday,
                5: schedule.every().saturday,
                6: schedule.every().sunday,
            }
            for day_idx in job.weekdays:
                j = day_map[day_idx].at(job.time_str).do(run_job)
                job._schedule_jobs.append(j)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            schedule.run_pending()
            time.sleep(1)

    @property
    def jobs(self) -> list:
        return self._jobs


# Instância global do engine
_engine = SchedulerEngine()


def get_engine() -> SchedulerEngine:
    return _engine


def get_signals() -> SchedulerSignals:
    return _signals


# ══════════════════════════════════════════════════════════════════════
# DIALOG
# ══════════════════════════════════════════════════════════════════════

class SchedulerDialog(QDialog):
    def __init__(self, flow_manager, parent=None):
        super().__init__(parent)
        self.flow_manager = flow_manager
        self.setWindowTitle("⏰  Agendador de Fluxos")
        self.setMinimumSize(640, 520)
        self.setModal(False)  # não bloqueia o PyFlow
        self._build_ui()
        self._apply_styles()
        self._load_flows()
        self._refresh_list()

        # Atualiza o log interno a cada segundo
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_list)
        self._timer.start(3000)

        # Conecta signal do engine
        _signals.log_message.connect(self._on_log)

        # Inicia o engine se ainda não rodando
        _engine.start()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("sched_header")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 14, 16, 14)

        title = QLabel("⏰  Agendador de Fluxos")
        title.setObjectName("sched_title")

        self.lbl_status = QLabel("▶ Engine ativo")
        self.lbl_status.setObjectName("sched_status_on")

        h.addWidget(title)
        h.addStretch()
        h.addWidget(self.lbl_status)
        root.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("sched_sep")
        root.addWidget(sep)

        # ── Conteúdo ──────────────────────────────────────────────────
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Painel esquerdo — lista de agendamentos
        left = QWidget()
        left.setObjectName("sched_left")
        left.setFixedWidth(260)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        lbl_jobs = QLabel("Agendamentos ativos")
        lbl_jobs.setObjectName("sched_section")
        left_layout.addWidget(lbl_jobs)

        self.jobs_list = QListWidget()
        self.jobs_list.setObjectName("sched_list")
        self.jobs_list.currentItemChanged.connect(self._on_job_selected)
        left_layout.addWidget(self.jobs_list, 1)

        self.btn_remove = QPushButton("🗑  Remover")
        self.btn_remove.setObjectName("btn_remove_job")
        self.btn_remove.setEnabled(False)
        self.btn_remove.clicked.connect(self._on_remove)
        left_layout.addWidget(self.btn_remove)

        # Log interno
        lbl_log = QLabel("Log")
        lbl_log.setObjectName("sched_section")
        left_layout.addWidget(lbl_log)

        self.log_list = QListWidget()
        self.log_list.setObjectName("sched_log")
        self.log_list.setFixedHeight(100)
        left_layout.addWidget(self.log_list)

        content_layout.addWidget(left)

        # Divisor
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setObjectName("sched_sep")
        content_layout.addWidget(div)

        # Painel direito — formulário novo agendamento
        right = QWidget()
        right.setObjectName("sched_right")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 12, 16, 12)
        right_layout.setSpacing(12)

        lbl_new = QLabel("Novo agendamento")
        lbl_new.setObjectName("sched_section")
        right_layout.addWidget(lbl_new)

        # Fluxo
        right_layout.addWidget(self._label("Fluxo"))
        self.combo_flow = QComboBox()
        self.combo_flow.setObjectName("sched_combo")
        right_layout.addWidget(self.combo_flow)

        # Tipo
        right_layout.addWidget(self._label("Tipo de agendamento"))
        self.combo_type = QComboBox()
        self.combo_type.setObjectName("sched_combo")
        self.combo_type.addItems(["Uma vez", "Repetir", "Dias da semana"])
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        right_layout.addWidget(self.combo_type)

        # Stack com formulários diferentes por tipo
        self.stack = QStackedWidget()
        self.stack.setObjectName("sched_stack")

        # ── Página 0: Uma vez ──────────────────────────────────────
        page_once = QWidget()
        p0 = QVBoxLayout(page_once)
        p0.setContentsMargins(0, 0, 0, 0)
        p0.setSpacing(8)
        p0.addWidget(self._label("Horário (HH:MM)"))
        self.time_once = QTimeEdit()
        self.time_once.setObjectName("sched_input")
        self.time_once.setDisplayFormat("HH:mm")
        self.time_once.setTime(QTime.currentTime().addSecs(300))
        p0.addWidget(self.time_once)
        p0.addStretch()
        self.stack.addWidget(page_once)

        # ── Página 1: Repetir ──────────────────────────────────────
        page_repeat = QWidget()
        p1 = QVBoxLayout(page_repeat)
        p1.setContentsMargins(0, 0, 0, 0)
        p1.setSpacing(8)
        p1.addWidget(self._label("Intervalo"))
        row_interval = QHBoxLayout()
        self.spin_interval = QSpinBox()
        self.spin_interval.setObjectName("sched_input")
        self.spin_interval.setRange(1, 9999)
        self.spin_interval.setValue(30)
        self.combo_unit = QComboBox()
        self.combo_unit.setObjectName("sched_combo")
        self.combo_unit.addItems(["minutos", "horas"])
        row_interval.addWidget(self.spin_interval)
        row_interval.addWidget(self.combo_unit)
        p1.addLayout(row_interval)
        p1.addStretch()
        self.stack.addWidget(page_repeat)

        # ── Página 2: Dias da semana ───────────────────────────────
        page_week = QWidget()
        p2 = QVBoxLayout(page_week)
        p2.setContentsMargins(0, 0, 0, 0)
        p2.setSpacing(8)
        p2.addWidget(self._label("Dias da semana"))
        self.day_checks = []
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        days_grid = QHBoxLayout()
        for day in days:
            cb = QCheckBox(day[:3])
            cb.setObjectName("sched_check")
            self.day_checks.append(cb)
            days_grid.addWidget(cb)
        p2.addLayout(days_grid)
        p2.addWidget(self._label("Horário (HH:MM)"))
        self.time_week = QTimeEdit()
        self.time_week.setObjectName("sched_input")
        self.time_week.setDisplayFormat("HH:mm")
        self.time_week.setTime(QTime(8, 0))
        p2.addWidget(self.time_week)
        p2.addStretch()
        self.stack.addWidget(page_week)

        right_layout.addWidget(self.stack, 1)

        # Botão adicionar
        self.btn_add = QPushButton("➕  Adicionar agendamento")
        self.btn_add.setObjectName("btn_add_job")
        self.btn_add.clicked.connect(self._on_add)
        right_layout.addWidget(self.btn_add)

        content_layout.addWidget(right, 1)
        root.addWidget(content, 1)

        # ── Footer ────────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("sched_sep")
        root.addWidget(sep2)

        footer = QWidget()
        footer.setObjectName("sched_footer")
        f = QHBoxLayout(footer)
        f.setContentsMargins(16, 10, 16, 10)

        self.lbl_next = QLabel("Nenhum agendamento ativo.")
        self.lbl_next.setObjectName("sched_next")

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_sched_close")
        btn_close.clicked.connect(self.close)

        f.addWidget(self.lbl_next, 1)
        f.addWidget(btn_close)
        root.addWidget(footer)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sched_label")
        return lbl

    def _load_flows(self):
        self.combo_flow.clear()
        flows = self.flow_manager.list_flows()
        if not flows:
            self.combo_flow.addItem("Nenhum fluxo salvo", "")
            return
        import os, json
        for path in sorted(flows):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("flow_name", os.path.basename(path))
            except Exception:
                name = os.path.basename(path)
            self.combo_flow.addItem(name, path)

    def _on_type_changed(self, index):
        self.stack.setCurrentIndex(index)

    def _on_add(self):
        flow_name = self.combo_flow.currentText()
        flow_path = self.combo_flow.currentData()

        if not flow_path:
            QMessageBox.warning(self, "Aviso", "Nenhum fluxo selecionado.")
            return

        type_idx = self.combo_type.currentIndex()
        types = ["once", "repeat", "weekday"]
        job_type = types[type_idx]

        if job_type == "once":
            t = self.time_once.time()
            time_str = t.toString("HH:mm")
            job = ScheduledJob(job_type, flow_name, flow_path, time_str=time_str)

        elif job_type == "repeat":
            interval = self.spin_interval.value()
            unit = "minutes" if self.combo_unit.currentIndex() == 0 else "hours"
            job = ScheduledJob(job_type, flow_name, flow_path,
                               interval=interval, interval_unit=unit)

        elif job_type == "weekday":
            selected = [i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
            if not selected:
                QMessageBox.warning(self, "Aviso", "Selecione pelo menos um dia da semana.")
                return
            t = self.time_week.time()
            time_str = t.toString("HH:mm")
            job = ScheduledJob(job_type, flow_name, flow_path,
                               time_str=time_str, weekdays=selected)

        _engine.add_job(job)
        self._refresh_list()
        self._on_log(f"Agendamento criado: {flow_name} — {job.describe()}")

    def _on_remove(self):
        item = self.jobs_list.currentItem()
        if not item:
            return
        job = item.data(Qt.UserRole)
        if job:
            reply = QMessageBox.question(self, "Remover agendamento",
                f"Remover '{job.flow_name}'?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                _engine.remove_job(job)
                self._refresh_list()

    def _on_job_selected(self, current, previous):
        self.btn_remove.setEnabled(current is not None)

    def _refresh_list(self):
        self.jobs_list.clear()
        for job in _engine.jobs:
            text = f"{'✅' if job.active else '⏸'} {job.flow_name}\n    {job.describe()}"
            if job.last_run:
                text += f"\n    Última: {job.last_run}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, job)
            item.setSizeHint(item.sizeHint().__class__(0, 64))
            if not job.active:
                item.setForeground(QColor("#45475a"))
            self.jobs_list.addItem(item)

        count = len(_engine.jobs)
        self.lbl_next.setText(
            f"{count} agendamento(s) ativo(s). Engine rodando em background."
            if count else "Nenhum agendamento configurado."
        )

    def _on_log(self, msg: str):
        self.log_list.addItem(msg)
        self.log_list.scrollToBottom()
        if self.log_list.count() > 50:
            self.log_list.takeItem(0)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }

            #sched_header { background-color: #181825; }
            #sched_title { font-size: 15px; font-weight: 700; color: #cba6f7; }
            #sched_status_on { font-size: 12px; color: #a6e3a1; font-weight: 600; }
            #sched_sep { color: #313244; }
            #sched_footer { background-color: #181825; }
            #sched_next { font-size: 11px; color: #6c7086; }

            #sched_left { background-color: #181825; }
            #sched_right { background-color: #1e1e2e; }
            #sched_section { font-size: 12px; font-weight: 700; color: #89b4fa; }
            #sched_label { font-size: 12px; font-weight: 600; color: #a6adc8; }

            #sched_list {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-radius: 6px; font-size: 11px; color: #cdd6f4;
            }
            #sched_list::item { padding: 4px 8px; border-bottom: 1px solid #313244; }
            #sched_list::item:selected { background-color: #313244; color: #cba6f7; }

            #sched_log {
                background-color: #11111b; border: 1px solid #313244;
                border-radius: 6px; font-size: 10px; color: #6c7086;
            }

            #sched_combo {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px 10px;
                color: #cdd6f4; font-size: 12px;
            }
            #sched_combo:focus { border-color: #cba6f7; }

            #sched_input {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px 10px;
                color: #cdd6f4; font-size: 13px;
            }
            #sched_input:focus { border-color: #cba6f7; }

            QSpinBox { background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px; color: #cdd6f4; font-size: 13px; }
            QTimeEdit { background-color: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 5px; color: #cdd6f4; font-size: 13px; }

            #sched_check { color: #cdd6f4; font-size: 11px; }
            QCheckBox::indicator {
                width: 14px; height: 14px; border-radius: 3px;
                border: 1px solid #45475a; background: #313244;
            }
            QCheckBox::indicator:checked { background-color: #cba6f7; border-color: #cba6f7; }

            #btn_add_job {
                background-color: #a6e3a1; color: #1e1e2e; border: none;
                border-radius: 6px; padding: 8px 16px;
                font-weight: 700; font-size: 13px;
            }
            #btn_add_job:hover { background-color: #b9f0b3; }

            #btn_remove_job {
                background-color: #3a1c1c; color: #f38ba8;
                border: 1px solid #f38ba8; border-radius: 6px;
                padding: 6px 12px; font-size: 12px;
            }
            #btn_remove_job:hover { background-color: #4a2020; }
            #btn_remove_job:disabled { background-color: #313244; color: #45475a; border-color: #45475a; }

            #btn_sched_close {
                background-color: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 6px 16px; font-size: 12px;
            }
            #btn_sched_close:hover { background-color: #45475a; }
        """)
