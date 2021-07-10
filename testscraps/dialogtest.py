from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,QMainWindow,QApplication, QPushButton, QWidget
from PyQt6.QtGui import QDoubleValidator, QPixmap,QBitmap,QImage
import sys
from PyQt6 import QtQuickWidgets

class TestDialog(QDialog):
    def __init__(self):
        super().__init__();
        self.createObjects();

    def createObjects(self):
        self.layout = QGridLayout(self);
        self.range = EditableRange();
        self.confirmButton = QPushButton("Confirm");
        self.previewButton = QPushButton("Preview");
        self.cancelButton = QPushButton("Cancel");
        
        self.confirmButton.setDefault(True);

        self.confirmButton.clicked.connect(self.accept);
        self.cancelButton.clicked.connect(self.reject);

        self.layout.addWidget(self.range,0,0,1,3);
        self.layout.addWidget(self.confirmButton,1,0,);
        self.layout.addWidget(self.previewButton,1,1);
        self.layout.addWidget(self.cancelButton,1,2);
        self.setLayout(self.layout);
        
class EditableRange(QWidget):#TODO: Fix rangeslider implementation, add an EditableRangeSlider class
    rangeChanged = pyqtSignal(float,float);

    def __init__(self, names=["min pix value","max pix value"],values=[0,100]):
        super().__init__();
        self.createObjects(names,values);

    def createObjects(self,names,values):
        self.layout = QGridLayout(self);
        
        self.minWidget = QWidget();
        self.minWidget.setLayout(QHBoxLayout());
        self.minLabel = QLabel(names[0]);
        self.minBox = QLineEdit(str(values[0]))
        self.minBox.setValidator(QDoubleValidator());
        self.minWidget.layout().addWidget(self.minLabel);
        self.minWidget.layout().addWidget(self.minBox);
        
        self.maxWidget = QWidget();
        self.maxWidget.setLayout(QHBoxLayout());
        self.maxLabel = QLabel(names[1]);
        self.maxBox = QLineEdit(str(values[1]))
        self.maxBox.setValidator(QDoubleValidator());
        self.maxWidget.layout().addWidget(self.maxLabel);
        self.maxWidget.layout().addWidget(self.maxBox);
        
        self.layout.addWidget(self.minWidget,0,0);
        self.layout.addWidget(self.maxWidget,0,1);
        self.setLayout(self.layout);





        



if __name__ == "__main__":
    app = QApplication(sys.argv);
    window = QMainWindow();
    dialogButton = QPushButton("Open Dialog");
    dialog = TestDialog();
    window.setCentralWidget(dialogButton);
    def do_dialog():
        dialog.exec();
        print("executed");
    dialogButton.clicked.connect(do_dialog);
    window.show();
    app.exec();
    sys.exit();
