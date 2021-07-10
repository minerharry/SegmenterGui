import sys
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import QObject, Qt


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.label = QtWidgets.QLabel();
        self.pmap = QtGui.QPixmap(500,500);
        self.pmap.fill(QtGui.QColor(200,0,0));
        self.label.setPixmap(self.pmap);
        self.setCentralWidget(self.label);

        self.action_list = [self.draw_rect,self.copy_image,self.draw_circle,self.swap_loaded_image];
        self.action_index = 0;

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.next_action();

    def next_action(self):
        self.action_list[min(self.action_index,len(self.action_list)-1)]();
        self.action_index += 1;

    def draw_rect(self):
        ptr = QtGui.QPainter(self.pmap);
        ptr.fillRect(200,200,300,300,QtGui.QColor(0,255,0));
        ptr.end();
        self.label.setPixmap(self.pmap);

    def copy_image(self):
        self.copy = self.pmap.copy();

    def draw_circle(self):
        ptr = QtGui.QPainter(self.pmap);
        ptr.setPen(10);
        ptr.drawEllipse(100,200,300,200);
        ptr.end();
        self.label.setPixmap(self.pmap);

    def swap_loaded_image(self):
        temp = self.pmap;
        self.pmap = self.copy;
        self.copy = temp;
        self.label.setPixmap(self.pmap);


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec();