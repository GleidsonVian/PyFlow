"""
Estilos e constantes para conexões premium do PyFlow.
Centraliza cores, dimensões e lógicas de visualização do Canvas.
"""

# Configurações de snapping (imã)
SNAP_DISTANCE = 30  # Em pixels. Aumentado ligeiramente para facilitar o snap.

# Configurações da Porta
PORT_RADIUS_IDLE = 7
PORT_RADIUS_HOVER = 11

# Largura das conexões
CONN_WIDTH_MAIN = 2.5
CONN_WIDTH_GLOW = 10.0
CONN_WIDTH_HOVER = 3.5

# Cores Base
COLORS = {
    "success": "#a6e3a1",
    "error":   "#f38ba8",
    "input":   "#8b8fa8",
    "default": "#cba6f7",
    "invalid": "#f38ba8",
    "glow_success": "#33a6e3a1",  # Verde com ~20% alpha
    "glow_error":   "#33f38ba8",  # Vermelho com ~20% alpha
    "glow_default": "#33cba6f7",  # Roxo com ~20% alpha
}
