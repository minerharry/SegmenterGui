import sys
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import QObject, Qt


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.box = QtWidgets.QWidget();
        self.bg = QtWidgets.QLabel(self.box);
        canvas = QtGui.QPixmap("./image3.png")
        self.bg.setPixmap(canvas)
        
        self.label = QtWidgets.QLabel(self.box)
        canvas2 = QtGui.QPixmap(canvas.size());
        #canvas2.fill(QtGui.QColorConstants.Blue);
        self.label.setPixmap(canvas2);

        self.opacity = QtWidgets.QGraphicsOpacityEffect();
        self.opacity.setOpacity(0.2);
        self.label.setGraphicsEffect(self.opacity)

        # self.stack = QtWidgets.QStackedWidget();
        # self.stack.addWidget(self.label);
        # self.stack.addWidget(self.bg);
        
        

        self.setCentralWidget(self.box)

        self.last_x, self.last_y = None, None

    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return # Ignore the first time.

        painter = QtGui.QPainter(self.label.pixmap())
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.update()

        # Update the origin for next time.
        self.last_x = e.x()
        self.last_y = e.y()

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec();