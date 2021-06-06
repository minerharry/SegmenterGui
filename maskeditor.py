import sys
import os
from PyQt6 import QtWidgets
from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6.QtCore import QPoint, QSignalMapper, QSize, QStringListModel, Qt, pyqtSignal, pyqtSlot;
from PyQt6.QtGui import QBitmap, QBrush, QColor, QIntValidator, QMouseEvent, QPainter, QPen, QPixmap




class Defaults:
    blankSize = QSize(300,300);
    opacity = 0.5;
    defaultFG = QColor(0,0,0,0);
    defaultBG = QColor(0,0,0,80);
    defaultBrushSize = 10;
    maxBrushSize = 80;
    drawButtonNames = ("Include", "Exclude");
    drawButtonsLabel = "Draw Mode";
    

class EditorPane(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();
    
    def createObjects(self):
        self.setLayout(QtWidgets.QVBoxLayout());
        self.mask = MaskContainer();
        self.toolbar = MaskToolbar();
        self.layout().addWidget(self.mask);
        self.layout().addWidget(self.toolbar);
        self.toolbar.slider.valueChanged.connect(self.mask.mask.setBrushSize);
        self.toolbar.drawButtons.valueChanged.connect(self.mask.mask.setDrawMode);
        self.toolbar.maskCheck.toggled.connect(lambda x: self.mask.mask.setVisible(not(x)));

class DrawMode:
    INCLUDE = 0;
    EXCLUDE = 1;

class MaskContainer(QtWidgets.QWidget):
    
    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.image = QtWidgets.QLabel(self);
        pixmap = QPixmap(Defaults.blankSize);
        pixmap.fill(QColor(255,0,0));
        self.image.setPixmap(pixmap)
        self.mask = ImageMask(self);
        #print(self.sizeHint())
        

    def sizeHint(self) -> QSize:
        return self.mask.sizeHint();

    #switches to a specific image, and loads mask if provided
    #both image and mask are filenames
    @pyqtSlot(str,str)
    def switchImage(self,image,mask=None):
        self.pixmap = QPixmap(image);
        self.image.setPixmap(self.pixmap);
        bmap = QBitmap(mask if mask else self.pixmap.size());
        if bmap.size() != self.pixmap.size(): #provided mask and image are of different sizes; create new mask
            bmap = QBitmap(self.pixmap.size());
        self.mask.loadBitmap(bmap);

class ImageMask(QtWidgets.QLabel):
    maskUpdate = pyqtSignal(); #whenever mask is changed or a stroke is completed

    def __init__(self,parent):
        super().__init__(parent);
        self.createObjects();
        self.lastPos = None;

    def update(self):
        super().update();
        self.setPixmap(self.pixlayer);

    def createObjects(self,initSize=Defaults.blankSize):
        self.fgColor = Defaults.defaultFG;
        self.bgColor = Defaults.defaultBG;
        self.pen = QPen(Defaults.defaultFG,Defaults.defaultBrushSize,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin);
        self.brush = QBrush(Defaults.defaultFG);
        self.drawMode = DrawMode.INCLUDE;
        self.bitcolors = [Qt.GlobalColor.color1,Qt.GlobalColor.color0];
        self.bitlayer = QBitmap("./image3.png");
        self.pixlayer = QPixmap(initSize);
        self.setFixedSize(initSize)
        self.reloadPixLayer();
        self.setPixmap(self.pixlayer);

    def keyPressEvent(self, ev) -> None:
        print('saving...')
        self.bitlayer.save('bitmap.bmp')
        return super().keyPressEvent(ev)

    def mouseMoveEvent(self, e, dot=False):
        #print(e.position())
        if not(dot) and self.lastPos is None: # First event.
            self.lastPos = e.position();
            return # Ignore the first time.

        colors = [self.fgColor,self.bgColor];

        bitpainter = QPainter(self.bitlayer)
        bitpainter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source);
        
        if dot:
            self.brush.setColor(self.bitcolors[self.drawMode]);
            bitpainter.setPen(Qt.PenStyle.NoPen)
            bitpainter.setBrush(self.brush)
            bitpainter.drawEllipse(e.position(),self.pen.widthF()/2,self.pen.widthF()/2);
            #print(f"circle drawn, at position {e.position()} of radii {self.pen.widthF()}");
        else:
            self.pen.setColor(self.bitcolors[self.drawMode]);
            bitpainter.setPen(self.pen);
            bitpainter.drawLine(self.lastPos, e.position())
        bitpainter.end()
        
        # self.reloadPixLayer();
        pixpainter = QPainter(self.pixlayer)
        pixpainter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source);

        if dot:
            self.brush.setColor(colors[self.drawMode]);
            pixpainter.setPen(Qt.PenStyle.NoPen)
            pixpainter.setBrush(self.brush)
            pixpainter.drawEllipse(e.position(),self.pen.widthF()/2,self.pen.widthF()/2);
            #print(f"circle drawn, at position {e.position()} of radii {self.pen.widthF()}");
        else:
            self.pen.setColor(colors[self.drawMode]);
            pixpainter.setPen(self.pen);
            pixpainter.drawLine(self.lastPos, e.position())
        pixpainter.end();

        # Update the origin for next time.
        self.lastPos = e.position();
        self.update();

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.mouseMoveEvent(ev,dot=True);

    def mouseReleaseEvent(self, e): #guaranteed called whenever mouse released after clicking on pane
        self.lastPos = None;
        self.maskUpdate.emit();

    def reloadPixLayer(self): #TODO: possibly further optimize by saving the pen each time?
        self.pixlayer.fill(self.fgColor)
        pixptr = QPainter(self.pixlayer);
        pixptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source);
        pixptr.setBackgroundMode(Qt.BGMode.OpaqueMode);
        pixptr.setBackground(self.bgColor);
        pixptr.setPen(self.fgColor);
        pixptr.drawPixmap(0,0,self.bitlayer);
        pixptr.end();
        self.update();

    def loadBitmap(self,bmap):
        self.bitlayer = bmap;
        self.reloadPixLayer();
        self.maskUpdate.emit();

    def setFGColor(self,colour):
        self.fgColor = colour;
    
    def setBGColor(self,colour):
        self.bgColor = colour;

    @pyqtSlot(int)
    def setDrawMode(self,mode):
        self.drawMode = mode;
        #print(f"draw mode set: {mode}")

    @pyqtSlot(int)
    def setBrushSize(self,size):
        self.pen.setWidth(size);

class MaskToolbar(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();
    
    def createObjects(self):
        self.setLayout(QtWidgets.QHBoxLayout());
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum);
        self.slider = EditableSlider();
        self.slider.editor.setFixedWidth(20);
        self.drawButtons = DualToggleButtons();
        self.maskCheck = QtWidgets.QCheckBox("Hide Mask");
        self.layout().addWidget(self.slider);
        self.layout().addWidget(self.drawButtons);
        self.layout().addWidget(self.maskCheck)

class EditableSlider(QtWidgets.QWidget):
    
    valueChanged = pyqtSignal(int); #whenever the value is changed internally

    def __init__(self,bounds=(0,Defaults.maxBrushSize),defaultValue=Defaults.defaultBrushSize,parent=None):
        super().__init__(parent);
        self.createObjects(bounds,defaultValue);

    def createObjects(self,bounds,default):
        self.setLayout(QtWidgets.QHBoxLayout());
        self.layout().setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)
        
        self.slider = QtWidgets.QSlider(Qt.Orientation.Horizontal);
        self.slider.setValue(default);
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBothSides);
        self.slider.setMinimum(bounds[0]);
        self.slider.setMaximum(bounds[1]);
        self.layout().addWidget(self.slider);

        self.editor = QtWidgets.QLineEdit(str(default));
        self.editor.setValidator(QIntValidator(*bounds));
        self.layout().addWidget(self.editor);

        self.slider.actionTriggered.connect(lambda action: self.setValue(self.slider.sliderPosition())); #action unused atm
        self.editor.editingFinished.connect(lambda: self.setValue(int(self.editor.text())));

    @pyqtSlot(int) #assumes a validated value; sets both components
    def setValue(self,value):
        self.slider.setValue(value);
        self.editor.setText(str(value));
        self.valueChanged.emit(value);

    def triggerAction(self,action):
        self.slider.triggerAction(action);

class DualToggleButtons(QtWidgets.QWidget):

    valueChanged = pyqtSignal(int);

    def __init__(self,label=Defaults.drawButtonsLabel,names=Defaults.drawButtonNames,parent=None):
        super().__init__(parent);
        self.createObjects(label,names);
    
    def createObjects(self,label,buttonNames):
        self.value = 0;
        self.storedValue = 0;
        self.setLayout(QtWidgets.QVBoxLayout());
        self.label = QtWidgets.QLabel();
        self.layout().addWidget(self.label);
        self.label.setText(label);

        self.buttonWidget = QtWidgets.QWidget();
        self.layout().addWidget(self.buttonWidget);
        self.buttonWidget.setLayout(QtWidgets.QHBoxLayout());
        self.buttonWidget.layout().setSpacing(0);
        self.buttonWidget.layout().setContentsMargins(0,0,0,0)
        #print(self.buttonWidget.layout().itemAt(0))

        self.buttons = [QtWidgets.QToolButton() for _ in buttonNames];
        [self.buttonWidget.layout().addWidget(button) for button in self.buttons];
        [button.setText(name) for button,name in zip(self.buttons,buttonNames)];
        [button.setCheckable(True) for button in self.buttons];
        [self.buttons[i].clicked.connect(lambda state,i=i: self.handleClick(state,i)) for i in range(len(self.buttons))]
        self.buttons[0].setChecked(True);
        self.buttonWidget.layout().insertStretch(0,1);
        self.buttonWidget.layout().insertStretch(-1,1);
    
    @pyqtSlot(bool) #from buttons
    def handleClick(self,checked,buttonId):
        if not(checked):
            print(f"button {buttonId} clicked while checked; rechecking")
            self.buttons[buttonId].setChecked(True);
            return;
        print(f"button {buttonId} clicked while unchecked; unchecking {self.value}")
        self.buttons[self.value].setChecked(False);
        self.setValue(buttonId,overrideStore=True);
        

    @pyqtSlot(int) #from elsewhere; use temp=True to store the current value to be recalled later
    def setValue(self,value,store=False,overrideStore=False):
        if store:
            self.storedValue = self.value
        self.value = value;
        if overrideStore:
            self.storedValue = self.value;
        self.valueChanged.emit(self.value);

    @pyqtSlot()
    def restoreValue(self):
        self.setValue(self.storedValue,overrideStore=True);
        
class DataPane(QtWidgets.QWidget):

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.selector = ImageSelectorPane();

        self.layout = QtWidgets.QVBoxLayout();
        self.layout.addWidget(self.selector);

        self.setLayout(self.layout);

class ImageSelectorPane(QtWidgets.QWidget):
    imageDirectoryChanged = pyqtSignal(str);
    imageChanged = pyqtSignal(str,str);

    def __init__(self,directory=None,parent=None):
        super().__init__(parent);
        self.createObjects(directory);

    def createObjects(self,dire):
        self.imageDirChooser = DirectorySelector("Select Image Directory:");
        self.maskDirChooser = DirectorySelector("Select Mask Directory");
        
        self.list = QtWidgets.QListView();
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection);
        self.model = QStringListModel(self.list);
        self.list.setModel(self.model);
        
        self.layout = QtWidgets.QVBoxLayout();
        self.layout.addWidget(self.imageDirChooser);
        self.layout.addWidget(self.list);
        self.layout.addWidget(self.maskDirChooser);

        self.setLayout(self.layout);
        self.imageDirChooser.directoryChanged.connect(self.selectImageDir);

    def selectImageDir(self):
        self.model.setStringList(os.listdir(self.imageDirChooser.dire));
        self.list.setCurrentIndex(0);
        self.imageChanged.emit(self.imageDirChooser.dire+self.getSelectedImageName());

    def selectMaskDir(self):
        self.imageChanged.emit(self.imageDirChooser.dire+self.getSelectedImageName(),)

    def getSelectedImageName(self):
        return self.model.stringList()[self.list.currentIndex()];

    def selectImage(self,index):
        self.list.selectionModel().setCurrentIndex(index);
        #self.imageChanged.emit();

    @pyqtSlot()
    def nextImage(self):
        pass;

class DirectorySelector(QtWidgets.QWidget):
    directoryChanged = pyqtSignal(str)
    
    def __init__(self,title="Select Directory:",startingDirectory=None,parent=None):
        super().__init__(parent=parent);
        self.createObjects(title,startingDirectory);
    
    def createObjects(self,title,dire):
        self.dire = dire;
        self.title = QtWidgets.QLabel(title);
        self.browseButton = QtWidgets.QPushButton("Browse...");
        self.browseButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed,QtWidgets.QSizePolicy.Policy.Fixed))
        self.pathLabel = QtWidgets.QLabel();
        self.fileDialog = QtWidgets.QFileDialog(self);
        self.fileDialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory);
        self.fileDialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly | QtWidgets.QFileDialog.Option.ReadOnly);
        self.layout = QtWidgets.QGridLayout();
        self.layout.addWidget(self.title,0,0,1,2);
        self.layout.addWidget(self.browseButton,1,0);
        self.layout.addWidget(self.pathLabel,1,1);

        self.directoryChanged.connect(self.pathLabel.setText);
        self.browseButton.clicked.connect(self.selectDirectory);

    @pyqtSlot()
    def selectDirectory(self):
        if (not(self.ifileDialog.exec())):
            return;
        self.dire = self.fileDialog.selectedFiles()[0];
        self.fileDialog.setDirectory(self.dire)
        self.directoryChanged.emit(self.dire);
        


        

    



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow();
    ex = DataPane(parent=window);
    window.setCentralWidget(ex);
    window.show();
    app.exec()
