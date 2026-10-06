from PySide6.QtGui import QFont
THEME_CSS="""
QWidget { background:#080807; color:#e7c98c; }
QLabel { color:#e7c98c; }
QTextEdit { background:#090909; color:#e7c98c; border:1px solid #705b36; padding:10px; selection-background-color:#40341f; }
QComboBox { background:#090909; color:#e7c98c; border:1px solid #705b36; padding:5px 9px; }
QComboBox QAbstractItemView { background:#090909; color:#e7c98c; selection-background-color:#40341f; }
"""
MONO="DejaVu Sans Mono"
SANS="DejaVu Sans"
def apply(app):
    app.setStyleSheet(THEME_CSS)
    app.setFont(QFont(MONO,9))
