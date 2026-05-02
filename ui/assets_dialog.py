from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QPushButton, QHeaderView, 
                               QLineEdit, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from engine.asset_manager import AssetManager

class AssetsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciador de Assets e Credenciais")
        self.setMinimumSize(500, 400)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.label_info = QLabel("Use esses assets nos blocos como: {{ASSET:NOME_DO_ASSET}}")
        self.label_info.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.label_info)

        # Tabela
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Nome (Chave)", "Valor (Conteúdo)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Formuário para adicionar
        form_layout = QHBoxLayout()
        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("Ex: URL_SISTEMA")
        self.input_val = QLineEdit()
        self.input_val.setPlaceholderText("Ex: https://google.com")
        
        btn_add = QPushButton("Adicionar / Atualizar")
        btn_add.clicked.connect(self.add_asset)
        btn_add.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")

        form_layout.addWidget(self.input_key)
        form_layout.addWidget(self.input_val)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout)

        # Botões de ação
        actions_layout = QHBoxLayout()
        btn_delete = QPushButton("Excluir Selecionado")
        btn_delete.clicked.connect(self.delete_asset)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)

        actions_layout.addWidget(btn_delete)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_close)
        layout.addLayout(actions_layout)

    def load_data(self):
        """Carrega os assets do JSON para a tabela."""
        self.table.setRowCount(0)
        assets = AssetManager.list_assets()
        for key, value in assets.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(key))
            # Mostramos o valor, mas em uma aplicação real você poderia mascarar se fosse senha
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))

    def add_asset(self):
        key = self.input_key.text().strip().upper() # Padroniza para maiúsculo
        val = self.input_val.text().strip()

        if not key or not val:
            QMessageBox.warning(self, "Erro", "Preencha Chave e Valor.")
            return

        assets = AssetManager.list_assets()
        assets[key] = val
        AssetManager.save_assets(assets)
        
        self.input_key.clear()
        self.input_val.clear()
        self.load_data()

    def delete_asset(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        key = self.table.item(current_row, 0).text()
        
        reply = QMessageBox.question(self, "Confirmar", f"Excluir o asset '{key}'?", 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            assets = AssetManager.list_assets()
            if key in assets:
                del assets[key]
                AssetManager.save_assets(assets)
                self.load_data()