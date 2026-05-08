import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt

class DaemonDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Serviço PyFlow (Daemon)")
        self.setFixedSize(500, 320)
        self._build_ui()
        self._apply_styles()
        self._update_status()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(15)
        root.setContentsMargins(20, 20, 20, 20)

        # Header
        lbl_title = QLabel("⚙️ PyFlow Daemon")
        lbl_title.setObjectName("daemon_title")
        root.addWidget(lbl_title)

        desc = QLabel(
            "O modo Serviço (Daemon) permite que o PyFlow continue rodando "
            "de forma invisível em background (segundo plano).\n\n"
            "Isso significa que Webhooks continuarão escutando e Agendamentos "
            "continuarão disparando automações, mesmo se você fechar esta janela."
        )
        desc.setWordWrap(True)
        desc.setObjectName("daemon_desc")
        root.addWidget(desc)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("sep")
        root.addWidget(sep)

        # Status
        self.lbl_status = QLabel("Status: Desconhecido")
        self.lbl_status.setObjectName("status_text")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_status)

        # Actions
        btn_layout = QHBoxLayout()
        self.btn_install = QPushButton("✅ Instalar (Iniciar com o Windows)")
        self.btn_install.setObjectName("btn_install")
        self.btn_install.clicked.connect(self._install_daemon)
        
        self.btn_remove = QPushButton("🗑️ Remover Serviço")
        self.btn_remove.setObjectName("btn_remove")
        self.btn_remove.clicked.connect(self._remove_daemon)

        btn_layout.addWidget(self.btn_install)
        btn_layout.addWidget(self.btn_remove)
        root.addLayout(btn_layout)

        root.addStretch()

        btn_close = QPushButton("Fechar")
        btn_close.setObjectName("btn_close")
        btn_close.clicked.connect(self.accept)
        root.addWidget(btn_close, alignment=Qt.AlignRight)

    def _get_startup_path(self) -> Path:
        startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        return Path(startup_dir) / "pyflow_daemon.vbs"

    def _update_status(self):
        vbs_path = self._get_startup_path()
        if vbs_path.exists():
            self.lbl_status.setText("🟢 Status: Serviço Instalado (Rodando na inicialização)")
            self.lbl_status.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14px;")
            self.btn_install.setEnabled(False)
            self.btn_remove.setEnabled(True)
        else:
            self.lbl_status.setText("🔴 Status: Serviço NÃO Instalado")
            self.lbl_status.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 14px;")
            self.btn_install.setEnabled(True)
            self.btn_remove.setEnabled(False)

    def _install_daemon(self):
        vbs_path = self._get_startup_path()
        main_py = Path(sys.argv[0]).resolve()
        
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        
        # Cria um VBScript que roda o pythonw (invisível) sem abrir tela de console
        vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{python_exe}"" ""{main_py}"" --daemon", 0, False
'''
        try:
            vbs_path.write_text(vbs_content, encoding="utf-8")
            
            # Já roda ele agora para o usuário não precisar reiniciar o PC!
            os.startfile(str(vbs_path))
            
            QMessageBox.information(self, "Sucesso", "Serviço PyFlow instalado com sucesso!\nEle começará a rodar automaticamente sempre que o Windows iniciar e já está rodando agora no fundo.")
            self._update_status()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao instalar o serviço:\n{e}")

    def _remove_daemon(self):
        vbs_path = self._get_startup_path()
        try:
            if vbs_path.exists():
                vbs_path.unlink()
            
            # Tenta matar o processo daemon
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], capture_output=True)
            
            QMessageBox.information(self, "Removido", "Serviço removido da inicialização do Windows.\nOs webhooks em background foram interrompidos.")
            self._update_status()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao remover o serviço:\n{e}")

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; }
            #daemon_title { font-size: 20px; font-weight: 700; color: #cba6f7; }
            #daemon_desc { font-size: 13px; color: #a6adc8; line-height: 1.4; }
            #sep { color: #313244; }
            QPushButton { border: none; border-radius: 6px; padding: 8px 14px; font-weight: 600; font-size: 13px; }
            #btn_install { background-color: #a6e3a1; color: #1e1e2e; }
            #btn_install:hover { background-color: #94cca0; }
            #btn_install:disabled { background-color: #45475a; color: #6c7086; }
            #btn_remove { background-color: #f38ba8; color: #1e1e2e; }
            #btn_remove:hover { background-color: #d97d97; }
            #btn_remove:disabled { background-color: #45475a; color: #6c7086; }
            #btn_close { background-color: #313244; color: #cdd6f4; }
            #btn_close:hover { background-color: #45475a; }
        """)
