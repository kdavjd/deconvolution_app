from PyQt5.QtWidgets import QApplication, QSplitter, QTextEdit, QVBoxLayout, QWidget
import sys

class SimpleExample(QWidget):
    def __init__(self):
        super().__init__()

        splitter = QSplitter()
        
        left_widget = QTextEdit()
        right_widget = QTextEdit()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        layout = QVBoxLayout()
        layout.addWidget(splitter)

        self.setLayout(layout)

app = QApplication(sys.argv)

window = SimpleExample()
window.show()

sys.exit(app.exec_())
