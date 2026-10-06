import sys
sys.path.insert(0,'/mnt/gai/agent/gui')
from toy_app import Toy
from PySide6.QtWidgets import QApplication
app=QApplication(sys.argv); w=Toy('thought'); w.show(); sys.exit(app.exec())
