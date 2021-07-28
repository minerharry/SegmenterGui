from PyQt6 import QtGui
from PyQt6.QtWidgets import QAbstractItemView, QAbstractSlider, QApplication, QCheckBox, QDialog, QFileDialog, QGraphicsScene, QGraphicsView, QGridLayout, QHBoxLayout, QLabel, QLayout, QLineEdit, QListView, QMainWindow, QMenu, QMessageBox, QPushButton, QSizePolicy, QSlider, QSplitter, QStyle, QStyleOptionFrame, QToolButton, QVBoxLayout, QWidget
from PyQt6 import QtCore
from PyQt6.QtCore import QFile, QPoint, QSignalMapper, QSize, QStringListModel, QTimer, Qt, pyqtSignal, pyqtSlot, QObject, QEvent
from PyQt6.QtGui import QAction, QBitmap, QBrush, QCloseEvent, QColor, QDoubleValidator, QFontMetrics, QIcon, QImage, QIntValidator, QMouseEvent, QPainter, QPen, QPixmap, QShortcut, QKeySequence, QTextDocument, QTransform, QUndoCommand, QUndoStack
import numpy as np

import sys
import os
import shutil
import json
import inspect


class LoadMode:
    biof = 0;
    skimage = 1;

class Defaults:
    bioLogging = False;
    loadMode = LoadMode.skimage;
    blankSize = QSize(300,300);
    blankColor = QColor(0,0,0,0);
    opacity = 0.5;
    defaultFG = QColor(0,0,0,0);
    defaultBG = QColor(0,0,0,80);
    defaultBrushSize = 10;
    maxBrushSize = 80;
    filePathMaxLength = 200; #characters
    drawButtonNames = ("Include", "Exclude");
    drawButtonsLabel = "Draw Mode";
    workingDirectory = "working_masks/";
    sessionFileName = "session_dat.json";
    supportedImageExts = [".sld",".tif",".aim",".al3d",".gel",".am",".amiramesh",".grey",".hx",".labels",".cif",".img",".hdr",".sif",".png",".afi",".svs",".htd",".pnl",".avi",".arf",".exp",".sdt",".1sc",".pic",".raw",".xml",".scn",".ims",".cr2",".crw",".ch5",".c01",".dib",".dv",".r3d",".dcm",".dicom",".v",".eps",".epsi",".ps",".flex",".mea",".res",".tiff",".fits",".dm3",".dm4",".dm2",".gif",".naf",".his",".vms",".txt",".bmp",".jpg",".i2i",".ics",".ids",".seq",".ipw",".hed",".mod",".leff",".obf",".msr",".xdce",".frm",".inr",".ipl",".ipm",".dat",".par",".jp2",".jpk",".jpx",".xv",".bip",".fli",".lei",".lif",".scn",".sxm",".l2d",".lim",".stk"]; 
    supportedMaskExts = supportedImageExts; #TODO: filter list by image formats and not just supported formats
    autosaveTime = 5*1000; #milliseconds
    exportedFlagFile = "export.flag";

if Defaults.loadMode == LoadMode.biof:
    import bioformats as bf
    import javabridge
    if not(Defaults.bioLogging):
        def init_logger(self):
            pass
        bf.init_logger = init_logger
else:
    from skimage.io import imread
    from skimage.exposure import rescale_intensity

class DataObject: #basic implementation of object data loading/saving
    def loadState(self,data):
        if data == {}:
            return;
        for name,datum in data['children'].items():
            if (hasattr(self,name)):
                child = getattr(self,name)
                if isinstance(child,DataObject):
                    child.loadState(datum);
                else:
                    print(f"Data state load error: named child {name} not an instance of DataObject")
            else:
                print(f"Data state load error: named child {name} not part of class {self}");
        self.loadData(data['self']);

    def loadData(self,data): #loads data for self; can be left blank if no data for that class
        pass;

    def getStateData(self):
        children = {};
        for child,chObj in inspect.getmembers(self,lambda x: isinstance(x,DataObject)):
            children[child] = DataObject.getStateData(chObj);
        return {'self':self.getSaveData(),'children':children};

    def getSaveData(self): #returns state data for self; can be left blank if no data for that class
        return {};


class MaskSegmenter(QSplitter,DataObject):
    def __init__(self,window,parent=None):
        super().__init__(parent);
        self.createObjects(window);
    
    def createObjects(self,window):
        self.setFocus();
        self.editor = EditorPane();
        self.data = DataPane();

        # self.layout = QHBoxLayout();
        # self.layout.addWidget(self.data);
        # self.layout.addWidget(self.editor);
        # self.layout.setStretch(1, 2)
        # self.setLayout(self.layout);
        self.addWidget(self.data);
        self.addWidget(self.editor);
        self.setHandleWidth(20);
        self.setStyleSheet("QSplitterHandle {background-image: black;}")
        

        self.ctrl = False;
        self.shift = False;

        self.editor.toolbar.iButtons.increment.connect(self.data.selector.incrementImage);
        self.data.selector.imageChanged.connect(self.editor.maskView.maskContainer.switchImage);
        self.data.selector.imageChanged.connect(self.editor.toolbar.adjustDialog.imageChanged);
        self.editor.toolbar.maskRevert.connect(self.data.selector.revertMask);

        self.exitConfirm = MaskUnexportedDialog(
            "Warning: You have unexported masks. \nYour changes and session will be saved.",
            buttonNames=["Exit","Export and Exit"]);
        self.exitConfirm.exportClicked.connect(self.data.selector.export);

        window.installEventFilter(self);

        ### SESSION SAVING STUFF
        self.autosaveTimer = QTimer(self);
        self.sessionManager = SessionManager(Defaults.sessionFileName,self);
        self.sessionManager.loadData();
        self.autosaveTimer.timeout.connect(self.sessionManager.saveData)
        self.data.selector.directoryChanged.connect(self.sessionManager.saveData)
        #print(self.getStateData());
        self.sessionManager.saveData();

        self.data.selector.workingDirCleared.connect(self.sessionManager.saveData);

    def closeEvent(self, a0: QCloseEvent) -> None:
        if (self.exitConfirm.exec()):
            self.sessionManager.saveData();
            return super().closeEvent(a0);
        a0.ignore();

    def event(self,ev):
        if ev.type() == QEvent.Type.KeyPress:
            print("key event - segmenter");
        return super().event(ev);
        

    def eventFilter(self,obj,ev):
        if ev.type() == QEvent.Type.KeyPress:
            print("key event - filter");
            if (Qt.KeyboardModifier.ControlModifier in ev.modifiers()):
                self.editor.toolbar.drawButtons.setValue(1,store=True);
                self.ctrl = True;
                print("control pressed");
                return True;
            if (Qt.KeyboardModifier.ShiftModifier in ev.modifiers()):
                self.editor.toolbar.drawButtons.setValue(0,store=True);
                self.shift = True;
                print("shift pressed");
                return True;
            if (ev.key() == Qt.Key.Key_Space):# and not ev.isAutoRepeat()):
                self.editor.toolbar.maskCheck.setChecked(True);
                print("space pressed");
                return True;
        if ev.type() == QEvent.Type.KeyRelease:
            if (Qt.KeyboardModifier.ControlModifier not in ev.modifiers() and self.ctrl): 
                self.editor.toolbar.drawButtons.restoreValue();
                print("ctrl released")
                self.ctrl = False;
                return True;
            if (Qt.KeyboardModifier.ShiftModifier not in ev.modifiers() and self.shift):
                self.editor.toolbar.drawButtons.restoreValue();
                print("shift released")
                self.shift = False;
                return True;
            if (ev.key() == Qt.Key.Key_Space and not ev.isAutoRepeat()):
                self.editor.toolbar.maskCheck.setChecked(False);
                print("space released");
                return True;
        return False;

class WorkingDirManager:
    def __init__(self,dir=Defaults.workingDir):
        self.workingDir = dir;
        


class SessionManager:
    def __init__(self,path,dataSource:DataObject):
        self.dataSource = dataSource;
        self.path = path;
        print(f"attempting to load session; checking existence of path: {self.path}")
        if os.path.exists(self.path):
            try: 
                with open(self.path,'r') as f:
                    self.data = json.load(f);
            except:
                print("there was an error");
                self.data = {};
        else:
            print("path does not exist");
            self.data = {};
        print(self.data);

    def loadData(self):
        self.dataSource.loadState(self.data);

    def saveData(self):
        print('saving...');
        self.data = self.dataSource.getStateData();
        with open(self.path,'w') as f:
            json.dump(self.data,f);
        

            
        
class EditorPane(QWidget,DataObject):
    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();
    
    def createObjects(self):
        self.setLayout(QVBoxLayout());
        self.maskView = MaskedImageView();
        self.toolbar = MaskToolbar();
        self.layout().addWidget(self.maskView);
        self.layout().addWidget(self.toolbar);
        self.layout().setStretch(0,2);
        self.toolbar.slider.valueChanged.connect(self.maskView.maskContainer.mask.setBrushSize);
        self.toolbar.drawButtons.valueChanged.connect(self.maskView.maskContainer.mask.setDrawMode);
        self.toolbar.maskCheck.toggled.connect(lambda x: self.maskView.maskContainer.mask.setVisible(not(x)));
        self.toolbar.zButtons.zoomed.connect(self.maskView.zoom);
        self.toolbar.adjustDialog.pixelRangeChanged.connect(self.maskView.maskContainer.setOverrideRescale);
        self.toolbar.adjustDialog.rangeReset.connect(self.maskView.maskContainer.resetOverride);
        self.maskView.maskContainer.imageRanged.connect(self.toolbar.adjustDialog.setPixelRange);

class MaskedImageView(QGraphicsView,DataObject):
    wheel_factor = 0.1;
    zoomChanged = pyqtSignal(float);

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();
        self.scaleFactor = 1;

    def createObjects(self):
        self.scene = QGraphicsScene();
        
        self.maskContainer = MaskContainer();
        self.proxy = self.scene.addWidget(self.maskContainer);
        self.setScene(self.scene);
        #self.maskContainer.sizeChanged.connect(self.updateProxy);

    #def updateProxy(self):
        #print(f"Proxy Update called, Container size: {self.maskContainer.size()}");
        #print(f"Proxy Update called, proxy size: {self.proxy.size()}");

    def wheelEvent(self,event):
        #print(f"Wheel Event, Container Size: {self.maskContainer.size()}");
        #print(f"Wheel Event, Proxy Size: {self.proxy.size()}");
        if (Qt.KeyboardModifier.ControlModifier in event.modifiers()):
            angle = event.angleDelta().y();
            factor = 1 + (1 if angle > 0 else -1)*self.wheel_factor;
            self.zoom(factor, anchor=QGraphicsView.ViewportAnchor.AnchorUnderMouse);
        else:
            super().wheelEvent(event);

    @pyqtSlot(float)
    def zoom(self,factor,anchor=None):
        self.scaleFactor*=factor;
        if (anchor):
            anch = self.transformationAnchor();
            self.setTransformationAnchor(anchor);
            self.scale(factor,factor);
            self.setTransformationAnchor(anch);
        else:
            self.scale(factor,factor);
        self.zoomChanged.emit(self.scaleFactor);

    @pyqtSlot(float)
    def setZoom(self,newScale):
        self.setTransform(QTransform.fromScale(newScale/self.scaleFactor,newScale/self.scaleFactor),combine=True)
        self.scaleFactor = newScale;
        self.zoomChanged.emit(self.scaleFactor);

class DrawMode:
    INCLUDE = 0;
    EXCLUDE = 1;

class MaskContainer(QWidget,DataObject):
    sizeChanged = pyqtSignal(QSize);
    imageRanged = pyqtSignal(float,float);
    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.overrideRescale = None;
        self.imName = None;
        self.imData = None;
        self.imRange = None;
        self.image = QLabel(self);
        pixmap = QPixmap(Defaults.blankSize);
        pixmap.fill(Defaults.blankColor);
        self.image.setPixmap(pixmap)
        self.mask = ImageMask(self);
        self.iFileName = None;
        self.mFileName = None;
        #print(self.sizeHint())
        

    def sizeHint(self) -> QSize:
        return self.mask.sizeHint();

    #switches to a specific image, and loads mask if provided
    #both image and mask are filenames
    @pyqtSlot(str,str)
    def switchImage(self,image=None,mask=None):
        if image == "":
            image = None;
        if mask == "":
            mask = None;
        print(f"switching image to Image: {image} and Mask: {mask}")
        if image == self.imName:
            print("image already loaded, reusing image data");
        else:
            if image is not None:
                pmap = self.readPixmap(image);
                print(pmap);
                print(pmap.size());
                self.image.setPixmap(pmap);
            else:
                self.imData = None;
                self.image.setPixmap(QPixmap(Defaults.blankSize));
                self.image.pixmap().fill(Defaults.blankColor);
        self.imName = image;
        
        self.image.setFixedSize(self.image.pixmap().size());
        self.setFixedSize(self.image.size());
        #print(f"Image Switched, Container Size: {self.size()}");
        #print(f"Image Switched, pixmap Size: {self.image.pixmap().size()}")
        if mask and os.path.exists(mask):
            bmap = QBitmap(mask);
            print("creating mask from file")
        else:
            print(f"no file, creating empty mask of size {self.image.pixmap().size()}")
            bmap = QBitmap(self.image.pixmap().size());
            bmap.clear();
        if bmap.size() != self.image.pixmap().size(): #provided mask and image are of different sizes; create new mask
            print(print(f"ERROR: Provided mask file incorrect size, creating empty mask of size {self.image.pixmap().size()}"))
            bmap = QBitmap(self.image.pixmap().size());
            bmap.clear();
        self.mask.loadBitmap(bmap,mask);
        self.sizeChanged.emit(self.size());

    def readPixmap(self,image): #TODO: Finish bf->qImage testing
        ext = os.path.splitext(image)[1];
        self.imData = None;
        if Defaults.loadMode == LoadMode.biof:
            print("BEEP BOP BOOP BF LOADING A FILE BEEP BOP BOOP")
            self.imData = bf.load_image(image);
        elif Defaults.loadMode == LoadMode.skimage:
            print("BEEP BOP BOOP SKIMAGE LOADING A FILE BEEP BOP BOOP")
            self.imData = imread(image);
        self.imRange = (np.min(self.imData),np.max(self.imData));
        self.imageRanged.emit(*self.imRange);
        return self.rescaleAndPixmapData();

    def rescaleAndPixmapData(self):
        shape = self.imData.shape;
        print(f"shape: {shape}");
        bytesPerLine = 2*shape[1]
        type = np.uint16;
        format = QImage.Format.Format_Grayscale16
        data = None;
        if len(shape) > 2:
            print("rgb image");
            bytesPerLine = shape[1]*shape[2];
            print(bytesPerLine);
            format = QImage.Format.Format_RGB888;
            type = np.uint8;
        if True:
            if self.overrideRescale:
                data = rescale_intensity(self.imData,self.overrideRescale,type);
            else:
                data = rescale_intensity(self.imData,self.imRange,type);
        else:
            data = np.uint8(self.imData);
        return QPixmap(QImage(data.data, shape[1], shape[0], bytesPerLine, format));

    
    @pyqtSlot(float,float)
    def setOverrideRescale(self,min,max):
        self.overrideRescale = (min,max);
        if self.imData is not None:
            self.image.setPixmap(self.rescaleAndPixmapData());
        
    @pyqtSlot()
    def resetOverride(self):
        self.overrideRescale = None;
        self.imageRanged.emit(*self.imRange);

    def readBitmap(self,map):
        if (False):
            pass;
        else:
            return QBitmap(map);

    def resizeEvent(self, ev):
        print(f"ResizeEvent, Container size: {self.size()}")
        self.sizeChanged.emit(self.size());

class ImageMask(QLabel,DataObject):
    maskUpdate = pyqtSignal(); #whenever mask is changed or a stroke is completed; saves to working directory

    def __init__(self,parent):
        super().__init__(parent);
        self.createObjects();
        self.lastPos = None;

    def update(self):
        self.setPixmap(self.pixlayer);
        super().update();

    def createObjects(self,initSize=Defaults.blankSize):
        self.fileName = None;
        self.fgColor = Defaults.defaultFG;
        self.bgColor = Defaults.defaultBG;
        self.pen = QPen(Defaults.defaultFG,Defaults.defaultBrushSize,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin);
        self.brush = QBrush(Defaults.defaultFG);
        self.drawMode = DrawMode.INCLUDE;
        self.bitcolors = [Qt.GlobalColor.color1,Qt.GlobalColor.color0];
        self.bitlayer = QBitmap(initSize);
        self.bitlayer.clear();
        self.pixlayer = QPixmap(initSize);
        self.setFixedSize(initSize)
        self.reloadPixLayer();
        self.setPixmap(self.pixlayer);
        self.maskUpdate.connect(self.save);

        self.resetUndoStack();#new states added to the end; lower number is more recent

    def resetUndoStack(self):
        #print("undo reset");
        self.undoStates = [self.bitlayer.copy()];
        self.lastBitId = 0;
        #print(f"last bit id: {self.lastBitId}")
        self.undoIds = [self.lastBitId];
        self.undoIndex = 0;
        #print(f"undo stack updated, size: {len(self.undoStates)}, index: {self.undoIndex}, with ids: {self.undoIds}");

    def pushUndoStack(self):
        #print("undo pushed");
        self.undoStates = [self.bitlayer.copy()] + self.undoStates[self.undoIndex:];
        self.lastBitId += 1;
        # print(f"last bit id: {self.lastBitId}")
        self.undoIds = [self.lastBitId] + self.undoIds[self.undoIndex:];
        self.undoIndex = 0;
        #self.setBitmap(self.undoStates[self.undoIndex].copy());
        # print(f"undo stack updated, size: {len(self.undoStates)}, index: {self.undoIndex}, with ids: {self.undoIds}");
        #print(self.bitlayer.toImage().pixel(self.pressPos.toPoint()));

    @pyqtSlot()
    def undo(self):
        print("undo triggered")
        if (self.undoIndex<len(self.undoStates)-1):
            self.undoIndex += 1;
            self.setBitmap(self.undoStates[self.undoIndex].copy());
            print("undone")
        # print(f"undo stack updated, size: {len(self.undoStates)}, index: {self.undoIndex}, with ids: {self.undoIds}");
        #print(self.bitlayer.toImage().pixel(self.pressPos.toPoint()));

    @pyqtSlot()
    def redo(self):
        print("redo triggered")
        if (self.undoIndex > 0):
            self.undoIndex -= 1;
            self.setBitmap(self.undoStates[self.undoIndex].copy());
            print("redone")
        # print(f"undo stack updated, size: {len(self.undoStates)}, index: {self.undoIndex}, with ids: {self.undoIds}");
        #print(self.bitlayer.toImage().pixel(self.pressPos.toPoint()));

    def mouseMoveEvent(self, e, dot=False):
        #print(e.position())
        if not(dot) and self.lastPos is None: # First event.
            self.lastPos = e.position();
            return # Ignore the first time.

        colors = [self.fgColor,self.bgColor];

        #print("painting bit");
        #print(self.bitlayer.paintEngine())
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
        
        #print("painting pix");
        #self.reloadPixLayer();
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
        #print("moved");


    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.pressPos = ev.position();
        #print(self.bitlayer.toImage().pixel(self.pressPos.toPoint()));
        self.mouseMoveEvent(ev,dot=True);
        #print(self.bitlayer.toImage().pixel(self.pressPos.toPoint()));

    def mouseReleaseEvent(self, e): #guaranteed called whenever mouse released after clicking on pane
        self.lastPos = None;
        print("mouse released")
        self.maskUpdate.emit();
        self.pushUndoStack();
        #print("released");

    def reloadPixLayer(self): 
        self.pixlayer = QPixmap(self.bitlayer.size());
        self.pixlayer.fill(self.fgColor)
        pixptr = QPainter(self.pixlayer);
        pixptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source);
        pixptr.setBackgroundMode(Qt.BGMode.OpaqueMode);
        pixptr.setBackground(self.bgColor);
        pixptr.setPen(self.fgColor);
        pixptr.drawPixmap(0,0,self.bitlayer);
        pixptr.end();
        self.update();

    #specifically loads a bitmap from memory and processes an image change, very different from setBitmap()
    def loadBitmap(self,bmap,fName):
        print("Loading mask with filename: " + str(self.fileName));
        self.fileName = os.path.basename(fName) if fName else None;
        self.setBitmap(bmap,update=False);
        self.resetUndoStack();

    #low-level command, changes loaded bitmap without doing any other intelligence
    def setBitmap(self,map,update=True):
        self.bitlayer = map;
        self.setFixedSize(self.bitlayer.size());
        self.reloadPixLayer();
        if update:
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
    
    @pyqtSlot()
    def save(self):
        if (self.fileName is not None):
            print(f"attempting save to {self.fileName}");
            self.bitlayer.save(Defaults.workingDirectory+self.fileName);
            if (os.path.exists(Defaults.exportedFlagFile)):
                os.remove(Defaults.exportedFlagFile)
        else:
            print("not saving, no filename")


class MaskToolbar(QWidget,DataObject):
    maskRevert = pyqtSignal();

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();
    
    def createObjects(self):
        self.layout = QHBoxLayout()
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum);
        self.layout.setContentsMargins(0,0,0,0);
        self.slider = EditableSlider(label="Brush Size");
        self.slider.editor.setFixedWidth(20);
        self.drawButtons = DualToggleButtons();
        self.maskCheck = QCheckBox("Hide Mask");
        self.iButtons = NextPrevButtons();
        self.zButtons = ZoomButtons()
        self.adjustButton = QPushButton("Adjust\nBrightness")
        self.adjustDialog = AdjustmentDialog();
        self.adjustButton.clicked.connect(self.adjustDialog.exec);
        self.revertButton = QPushButton("Revert to Original")
        self.revertButton.clicked.connect(self.revert);
        self.maskRevert.connect(self.adjustDialog.reset);
        self.layout.addWidget(self.slider);
        self.layout.addWidget(self.drawButtons);
        self.layout.addWidget(self.maskCheck);
        self.layout.addWidget(self.iButtons);
        self.layout.addWidget(self.zButtons);
        self.layout.addWidget(self.adjustButton);
        self.layout.addWidget(self.revertButton);
        self.layout.insertStretch(-1,1);

        self.setLayout(self.layout);

    def revert(self): #TODO: Potentially move into image selector pane, check if there are changes on current image
        confirmBox = QMessageBox(QMessageBox.Icon.Warning,"Revert Mask","Clear changes and revert to the original mask?");
        confirmBox.setInformativeText("This action cannot be undone.");
        clearbtn = confirmBox.addButton("Revert",QMessageBox.ButtonRole.AcceptRole);
        confirmBox.addButton(QMessageBox.StandardButton.Cancel);
        
        confirmBox.exec();
        if (confirmBox.clickedButton() == clearbtn):
            self.maskRevert.emit()


class EditableSlider(QWidget,DataObject):
    
    valueChanged = pyqtSignal(int); #whenever the value is changed internally

    def __init__(self,label="Slider",bounds=(1,Defaults.maxBrushSize),defaultValue=Defaults.defaultBrushSize,parent=None):
        super().__init__(parent);
        self.createObjects(bounds,defaultValue,label);

    def createObjects(self,bounds,default,label):        
        self.setLayout(QGridLayout());
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        
        self.label = QLabel(label);
        self.layout().addWidget(self.label,0,0,1,2);

        self.slider = QSlider(Qt.Orientation.Horizontal);
        self.slider.setValue(default);
        self.slider.setTickPosition(QSlider.TickPosition.TicksBothSides);
        self.slider.setMinimum(bounds[0]);
        self.slider.setMaximum(bounds[1]);
        self.layout().addWidget(self.slider,1,0);

        self.editor = QLineEdit(str(default));
        self.editor.setValidator(QIntValidator(*bounds));
        self.layout().addWidget(self.editor,1,1);

        self.slider.actionTriggered.connect(lambda action: self.setValue(self.slider.sliderPosition())); #action unused atm
        self.editor.editingFinished.connect(lambda: self.setValue(int(self.editor.text())));

    @pyqtSlot(int) #assumes a validated value; sets both components
    def setValue(self,value):
        self.slider.setValue(value);
        self.editor.setText(str(value));
        self.valueChanged.emit(value);

    def triggerAction(self,action):
        self.slider.triggerAction(action);

    def getSaveData(self):
        return self.slider.value();

    def loadData(self,data):
        self.setValue(data);

class DualToggleButtons(QWidget,DataObject):

    valueChanged = pyqtSignal(int);

    def __init__(self,label=Defaults.drawButtonsLabel,names=Defaults.drawButtonNames,parent=None):
        super().__init__(parent);
        self.createObjects(label,names);
    
    def createObjects(self,label,buttonNames):
        self.value = 0;
        self.storedValue = -1; #-1 indicates no value stored
        self.setLayout(QVBoxLayout());
        self.label = QLabel();
        self.layout().addWidget(self.label);
        self.label.setText(label);
        self.layout().setContentsMargins(0,0,0,0);

        self.buttonWidget = QWidget();
        self.layout().addWidget(self.buttonWidget);
        self.buttonWidget.setLayout(QHBoxLayout());
        self.buttonWidget.layout().setSpacing(0);
        self.buttonWidget.layout().setContentsMargins(0,0,0,0)
        #print(self.buttonWidget.layout().itemAt(0))

        self.buttons = [QToolButton() for _ in buttonNames];
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
        self.setValue(buttonId,overrideStore=True,updateButtons=False);
        

    @pyqtSlot(int) #from elsewhere; use temp=True to store the current value to be recalled later
    def setValue(self,value,store=False,overrideStore=False,updateButtons=True):
        if store and self.storedValue == -1:
            self.storedValue = self.value
        self.value = value;
        if overrideStore:
            self.storedValue = -1;
        self.valueChanged.emit(self.value);
        if updateButtons:
            [button.setChecked(False) for button in self.buttons];
            self.buttons[self.value].setChecked(True);

    @pyqtSlot()
    def restoreValue(self):
        if self.storedValue != -1:
            self.setValue(self.storedValue,overrideStore=True,updateButtons=True);

class NextPrevButtons(QWidget,DataObject):
    increment = pyqtSignal(int);
    
    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();
    
    def createObjects(self):
        self.layout = QHBoxLayout();
        self.bButton = QPushButton("Previous");
        self.nButton = QPushButton("Next");
        self.layout.addWidget(self.bButton);
        self.layout.addWidget(self.nButton);
        self.bButton.clicked.connect(self.handleBButton);
        self.nButton.clicked.connect(self.handleNButton);
        self.setLayout(self.layout);

    @pyqtSlot()
    def handleBButton(self):
        self.increment.emit(-1);

    @pyqtSlot()
    def handleNButton(self):
        self.increment.emit(1);

class ZoomButtons(QWidget,DataObject):
    zInIconPath = "./zoom-in.png";
    zOutIconPath = "./zoom-out.png";
    zoomFactor = 0.2;
    zoomed = pyqtSignal(float);

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.zInButton = QToolButton();
        self.zInButton.setIcon(QIcon(self.zInIconPath));
        self.zOutButton = QToolButton();
        self.zOutButton.setIcon(QIcon(self.zOutIconPath));
        self.zoomDisplay = QLabel("100%");
        self.zInButton.clicked.connect(lambda: self.handleClick(1))
        self.zOutButton.clicked.connect(lambda: self.handleClick(-1))

        self.layout = QHBoxLayout();
        self.layout.addWidget(self.zInButton);
        self.layout.addWidget(self.zOutButton);
        #self.layout.addWidget(self.zoomDisplay);
        self.setLayout(self.layout);

    def handleClick(self,direction):
        self.zoomed.emit(1+direction*self.zoomFactor);

    @pyqtSlot(float)
    def displayZoom(self,zoom):
        self.zoomDisplay.setText(f"{round(zoom,2)*100}%")

        

class DataPane(QWidget,DataObject):

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.selector = ImageSelectorPane();
        self.exportPane = ExportPanel();

        self.layout = QVBoxLayout();
        self.layout.addWidget(self.selector);
        self.layout.addWidget(self.exportPane);

        self.setLayout(self.layout);

        self.exportPane.clearDir.connect(self.selector.clearWorkingDir);
        self.exportPane.clearDir.connect(self.selector.changeImage);
        self.exportPane.exportActivated.connect(self.selector.export);

class ImageSelectorPane(QWidget,DataObject):
    directoryChanged = pyqtSignal(str,str); #image directory, mask directory
    imageChanged = pyqtSignal(str,str); #image file, mask file
    workingDirCleared = pyqtSignal();

    def __init__(self,directory=None,parent=None):
        super().__init__(parent);
        self.createObjects(directory);

    def createObjects(self,dire):
        self.importConfirm = MaskUnexportedDialog(
            "Warning: You have unsaved masks. \nImporting new masks will overwrite the current changes. \nContinue?",
            buttonNames=["Overwrite Masks","Export Unsaved Masks"]);
        self.imageDirChooser = DirectorySelector("Select Image Directory:");
        self.maskDirChooser = DirectorySelector(title="Import Masks",dialog=self.importConfirm);
        self.importConfirm.exportClicked.connect(self.export)
        
        self.list = QListView();
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);
        self.list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.model = QStringListModel(self.list);
        self.list.setModel(self.model);
        
        
        self.layout = QVBoxLayout();
        self.layout.addWidget(self.imageDirChooser);
        self.layout.addWidget(self.list);
        self.layout.addWidget(self.maskDirChooser);

        self.setLayout(self.layout);
        self.imageDirChooser.directoryChanged.connect(self.selectImageDir);
        self.maskDirChooser.directoryChanged.connect(self.selectMaskDir);
        self.list.selectionModel().currentChanged.connect(self.changeImage);

        self.exportDialog = QExportDialog(self);
        self.exportDialog.setFileMode(QFileDialog.FileMode.Directory);
        self.exportDialog.setOption(QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.ReadOnly);

    @pyqtSlot()
    def export(self):
        if not(self.imageDirChooser.dire and self.maskDirChooser.dire):
            QMessageBox.information(self,"Unable to export","No mask files to export",QMessageBox.StandardButton.Ok,defaultButton=QMessageBox.StandardButton.Ok);
            return;
        print("gonna grab some file paths");
        filesToExport = self.getAllMaskFilePaths();
        print("paths retrieved");
        output = self.exportDialog.exec([os.path.basename(file) for file in filesToExport]);
        print(output);
        if (output):
            exportDir = self.exportDialog.selectedFiles()[0];
            print(f"window accepted, exporting to: {exportDir}");
            for path in filesToExport:
                if (exportDir != os.path.dirname(path)):
                    shutil.copy(path,exportDir);
            print("Export successful");
            with open(Defaults.exportedFlagFile,'w') as f:
                pass;
            print("flag file created");
        else:
            print("window rejected");

    @pyqtSlot()
    def revertMask(self):
        print("Reverting mask");
        if self.imageDirChooser.dire and self.maskDirChooser.dire:
            imName = self.getSelectedImageName()
            baseName = os.path.splitext(imName)[0];
            workingFiles = os.listdir(Defaults.workingDirectory);
            #print(f"Working files: {workingFiles}");
            workingMasks = list(filter(lambda x: x.startswith(baseName+".") and x.endswith(tuple(Defaults.supportedMaskExts)),workingFiles));
            #print(f"Working Masks: {workingMasks}")
            maskName = (Defaults.workingDirectory + workingMasks[0]) if len(workingMasks) > 0 else None;
            print(f"mask name: {maskName}")
            if os.path.exists(maskName):
                os.remove(maskName);
                if (os.path.exists(Defaults.exportedFlagFile)):
                    os.remove(Defaults.exportedFlagFile);
                self.changeImage();
                



    def getAllMaskFilePaths(self): #should only be called if both mask and image directory selected
        if not(self.imageDirChooser.dire and self.maskDirChooser.dire):
            print("Warning: attempting to get file paths without without proper directories");
            return [];
        imagenames = self.model.stringList();
        workingMasks = list(filter(lambda x: x.endswith(tuple(Defaults.supportedMaskExts)),os.listdir(Defaults.workingDirectory)));
        originalMasks = list(filter(lambda x: x.endswith(tuple(Defaults.supportedMaskExts)),os.listdir(self.maskDirChooser.dire)));

        result = [];
        for im in imagenames:
            base = os.path.splitext(im)[0];
            working = list(filter(lambda x: x.startswith(base+"."),workingMasks));
            if len(working) > 0:
                result.append(Defaults.workingDirectory + working[0]);
            else:
                original = list(filter(lambda x:x.startswith(base+"."),originalMasks));
                if len(original) > 0:
                    result.append(self.maskDirChooser.dire + "\\" + original[0]);
        return result;

    def selectImageDir(self,dire,clear=True): 
        if dire and not(os.path.exists(dire)):
            print(f"Error: somehow attempting to select invalid image directory {dire}; setting to None")
            dire=None;
        print(f"image dir selected: {dire}");
        if dire and dire != '':
            filtered = list(filter(lambda x: x.lower().endswith(tuple(Defaults.supportedImageExts)),os.listdir(dire)));
            filtered.sort(key = lambda e: (len(e),e));
            self.model.setStringList(filtered);
        else:
            self.model.setStringList([]);
        self.list.setCurrentIndex(self.model.index(0));
        print(self.list.currentIndex().row());
        if clear:
            self.maskDirChooser.setDirectory(None);
        self.changeImage();
        self.directoryChanged.emit(dire,None);

    def selectMaskDir(self,dire,clear=True): 
        if dire and not(os.path.exists(dire)):
            print(f"Error: somehow attempting to select invalid mask directory {dire}; setting to None")
            dire=None;
        print(f"mask dir selected: {dire}")
        if clear:
            self.clearWorkingDir();
        self.changeImage();
        self.directoryChanged.emit(self.imageDirChooser.dire,dire);

    def clearWorkingDir(self): #TODO: Make separate object for working dir management, make this a signal instead
        print("Beep boop files should be removed");
        for file in os.scandir(Defaults.workingDirectory):
            os.remove(file.path);
        self.workingDirCleared.emit();

    def changeImage(self,row=None): 
        print("changeimage method called")
        #method is called with the assumption that the masks in Defaults.workingDirectory are the priority;
        #if the mask dir has been changed / selected, the import of those masks should happen *first*
        if (type(row) == QtCore.QModelIndex):
            row = row.row();
        if self.imageDirChooser.dire and self.imageDirChooser.dire != '':
            imName = self.getSelectedImageName(row)
            imagePath = self.imageDirChooser.dire+"/"+imName;
            maskPath = None;
            if self.maskDirChooser.dire:
                baseName = os.path.splitext(imName)[0];
                workingFiles = os.listdir(Defaults.workingDirectory);
                #print(f"Working files: {workingFiles}");
                workingMasks = list(filter(lambda x: x.startswith(baseName+".") and x.endswith(tuple(Defaults.supportedMaskExts)),workingFiles));
                #print(f"Working Masks: {workingMasks}")
                maskName = workingMasks[0] if len(workingMasks) > 0 else None;
                if not(maskName):
                    maskfiles = os.listdir(self.maskDirChooser.dire);
                    goodMasks = list(filter(lambda x: x.startswith(baseName+".") and x.endswith(tuple(Defaults.supportedMaskExts)),maskfiles));
                    if len(goodMasks) > 0:
                        maskName = goodMasks[0]
                        if (len(goodMasks) > 1):
                            print(f"warning: more than one mask file with the same name, unsupported behavior. Using {maskName}");
                        maskPath = (self.maskDirChooser.dire+"/"+maskName);
                else:
                    maskPath = (Defaults.workingDirectory+maskName);
                
            self.imageChanged.emit(imagePath,maskPath);

    def getSelectedImageName(self,row=None):
        return self.model.stringList()[row if row else self.list.currentIndex().row()];

    def selectImage(self,index):
        print("image selected")
        self.list.setCurrentIndex(self.model.index(index));
        self.changeImage(index);

    @pyqtSlot(int)
    def incrementImage(self,inc):
        if len(self.model.stringList()) > 0:
            self.selectImage(max(0,min(self.list.currentIndex().row()+inc,len(self.model.stringList())-1)));

    def getSaveData(self):
        return {"row":self.list.currentIndex().row(),"image_dir":self.imageDirChooser.dire,"mask_dir":self.maskDirChooser.dire};

    def loadData(self, data):
        try:
            self.list.setCurrentIndex(self.model.index(data['row']));
            self.maskDirChooser.setDirectory(data['mask_dir'],emit=False);
            self.selectMaskDir(data['mask_dir'],clear=False);
            self.imageDirChooser.setDirectory(data['image_dir'],emit=False);
            self.selectImageDir(data['image_dir'],clear=False)
        except:
            pass;
        

class DirectorySelector(QWidget):
    directoryChanged = pyqtSignal(str);
    
    def __init__(self,title="Select Directory:",startingDirectory=None,parent=None,buttonText="Browse...",dialog=None):
        super().__init__(parent=parent);
        self.createObjects(title,startingDirectory,dialog,buttonText);
    
    def createObjects(self,title,dire,dialog,buttonText):
        self.dire = dire;
        self.dialog = dialog;
        if self.dialog:
            self.dialog.accepted.connect(self.selectDirectory);
        self.title = QLabel(title);
        self.browseButton = QPushButton(buttonText);
        self.browseButton.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed))
        self.pathLabel = ElideLabel();
        self.layout = QGridLayout();
        self.layout.addWidget(self.title,0,0);
        self.layout.addWidget(self.browseButton,0,1);
        self.layout.addWidget(self.pathLabel,1,0,1,2);

        self.fileDialog = QFileDialog(self);
        self.fileDialog.setFileMode(QFileDialog.FileMode.Directory);
        self.fileDialog.setOption(QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.ReadOnly);

        self.setLayout(self.layout)
        self.directoryChanged.connect(self.pathLabel.setText);
        self.directoryChanged.connect(self.pathLabel.setToolTip);
        self.browseButton.clicked.connect(self.checkDialog);



    @pyqtSlot()
    def checkDialog(self):
        print("dialog checked");
        if self.dialog:
            print("dialog opened");
            self.dialog.open();
        else:
            print("no dialog, selecting directory");
            self.selectDirectory();

    @pyqtSlot()
    def selectDirectory(self):
        print("select directory activated")
        if not(self.fileDialog.exec()):
            return;
        self.setDirectory(self.fileDialog.selectedFiles()[0]);
        
    
    def setDirectory(self,dire,emit=True):
        if dire and not(os.path.exists(dire)):
            print(f"Error: attempting to set invalid directory {dire}; setting to none");
            dire=None;
        print(dire);
        self.dire = dire;
        self.fileDialog.setDirectory(self.dire if self.dire else "");
        if emit:
            self.directoryChanged.emit(self.dire);


class MaskUnexportedDialog(QDialog):
    exportClicked = pyqtSignal()
    
    def __init__(self,desc,buttonNames=["Exit, don't export","Export and exit"]):
        super().__init__();
        self.createObjects(desc,buttonNames);

    def createObjects(self,desc,bNames):
        self.setWindowTitle("Warning: Unexported Masks");
        self.layout = QGridLayout();

        self.descLabel = QLabel(desc);
        self.noExportButton = QPushButton(bNames[0]);
        self.exportButton = QPushButton(bNames[1]);
        self.cancelButton = QPushButton("Cancel");

        self.layout.addWidget(self.descLabel,0,0,1,3);
        self.layout.addWidget(self.noExportButton,1,0)
        self.layout.addWidget(self.exportButton,1,1)
        self.layout.addWidget(self.cancelButton,1,2);
        self.setLayout(self.layout);

        self.noExportButton.clicked.connect(self.accept);
        self.exportButton.clicked.connect(self.exportAndAccept);
        self.cancelButton.clicked.connect(self.reject);

    def open(self):
        if (self.unexportedMasks()):
            print("before open");
            super().open();
            print("after open");
        else:
            self.accept();

    def exec(self):
        if (self.unexportedMasks()):
            print("before exec");
            return super().exec();
        else:
            self.accept();
            return True;

    def unexportedMasks(self):
        workingDirNonempty = any(os.scandir(Defaults.workingDirectory));
        noFlag = not(os.path.exists(Defaults.exportedFlagFile));
        print(f"Checking if unexported masks... {workingDirNonempty}, {noFlag}");
        return workingDirNonempty and noFlag;
        

    def exportAndAccept(self):
        self.exportClicked.emit();
        self.accept();




class ElideLabel(QLabel):
    _elideMode = QtCore.Qt.TextElideMode.ElideMiddle

    def elideMode(self):
        return self._elideMode

    def setElideMode(self, mode):
        if self._elideMode != mode and mode != QtCore.Qt.TextElideMode.ElideNone:
            self._elideMode = mode
            self.updateGeometry()

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        hint = self.fontMetrics().boundingRect(self.text()).size()
        margins = self.contentsMargins()
        margin = self.margin() * 2
        return QtCore.QSize(
            min(100, hint.width()) + margins.left() + margins.right() + margin, 
            min(self.fontMetrics().height(), hint.height()) + margins.top() + margins.bottom() + margin
        )

    def paintEvent(self, event):
        qp = QPainter(self)
        opt = QStyleOptionFrame()
        self.initStyleOption(opt)
        self.style().drawControl(
            QStyle.ControlElement.CE_ShapedFrame, opt, qp, self)
        margin = self.margin()
        try:
            # since Qt >= 5.11
            m = self.fontMetrics().horizontalAdvance('x') / 2 - margin
        except:
            m = self.fontMetrics().width('x') / 2 - margin
        r = self.contentsRect().adjusted(
            margin + m,  margin, -(margin + m), -margin)
        qp.drawText(r, self.alignment(), 
            self.fontMetrics().elidedText(
                self.text(), self.elideMode(), r.width()))


class AdjustmentDialog(QDialog,DataObject):
    pixelRangeChanged = pyqtSignal(float,float)
    persistentChanged = pyqtSignal(bool);
    rangeReset = pyqtSignal();


    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.setWindowTitle("Adjust Image Brightness / Contrast");
        self.tempState = None;
        self.layout = QGridLayout(self);
        self.range = EditableRange();
        self.persistenceCheck = QCheckBox("Use for all images");
        self.resetButton = QPushButton("Reset to default");
        self.confirmButton = QPushButton("Confirm");
        self.previewButton = QPushButton("Preview");
        self.cancelButton = QPushButton("Cancel");
    
        self.layout.addWidget(self.range,0,0,1,6);
        self.layout.addWidget(self.persistenceCheck,1,0,1,3);
        self.layout.addWidget(self.resetButton,1,3,1,3);
        self.layout.addWidget(self.confirmButton,2,0,1,2);
        self.layout.addWidget(self.previewButton,2,2,1,2);
        self.layout.addWidget(self.cancelButton,2,4,1,2);
        self.setLayout(self.layout)

        self.confirmButton.setDefault(True);
        self.resetButton.clicked.connect(self.reset);
        self.confirmButton.clicked.connect(self.accept);
        self.cancelButton.clicked.connect(self.reject);
        self.previewButton.clicked.connect(self.apply)
        # self.range.rangeChanged.connect(self.pixelRangeChanged.emit); #done through apply
        # self.persistenceCheck.toggled.connect(self.persistentChanged.emit);
        
    def accept(self):
        self.apply();
        return super().accept();

    def reject(self):
        self.revertState();
        return super().reject();

    def exec(self):
        self.saveState();
        return super().exec();

    @pyqtSlot()
    def reset(self):
        self.setPersistent(False);
        self.rangeReset.emit();
        self.apply();
        self.saveState();

    def apply(self): #Emit signals to update image
        pers = self.persistent();
        self.persistentChanged.emit(pers);
        self.pixelRangeChanged.emit(*self.pixelRange());

    def saveState(self):
        self.tempState = self.getStateData();

    def revertState(self):
        self.loadState(self.tempState);
        self.apply();

    def persistent(self):
        return self.persistenceCheck.isChecked();

    @pyqtSlot(bool)
    def setPersistent(self,pers):
        self.persistenceCheck.setChecked(pers);

    def pixelRange(self):
        return self.range.range();
    
    @pyqtSlot(float,float)
    def setPixelRange(self,min,max):
        if (not(self.persistent())):
            self.range.setRange(min,max);

    @pyqtSlot()
    def imageChanged(self):
        if (not(self.persistent())):
            self.apply(); #

    def loadData(self, data):
        if data:
            self.setPersistent(data);
        self.apply();

    def getSaveData(self):
        return self.persistent();

        
class EditableRange(QWidget,DataObject):#TODO: Fix rangeslider implementation, add an EditableRangeSlider class
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

    def range(self):
        return (float(self.minBox.text()),float(self.maxBox.text()));

    @pyqtSlot(float,float)
    def setRange(self,min,max):
        self.minBox.setText(str(min));
        self.maxBox.setText(str(max));

    def getSaveData(self):
        return self.range();

    def loadData(self, data):
        if data:
            self.setRange(*data);

class QExportDialog(QFileDialog):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);
        self.setOptions(QFileDialog.Option.DontUseNativeDialog);
        self.names = [];
        self.dialog = QDialog();
        layout = QGridLayout();
        self.text = QLabel("Warning: no files will be overwritten. Proceed?");
        yesbtn = QPushButton("Yes, overwrite");
        nobtn = QPushButton("Cancel");
        layout.addWidget(self.text,0,0,1,2);
        layout.addWidget(yesbtn,1,0);
        layout.addWidget(nobtn,1,1);
        self.dialog.setLayout(layout);
        yesbtn.clicked.connect(self.dialog.accept);
        nobtn.clicked.connect(self.dialog.reject);

    def exec(self,names=None):
        self.names = names;
        return super().exec();

    def accept(self):
        print("accept method called");
        overlaps = len(set(self.names) & set(os.listdir(self.selectedFiles()[0])));
        if (overlaps > 0):
            print("there be overlaps")
            self.text.setText(f"Warning: {overlaps} files will be overwritten. Proceed?")
            if (self.dialog.exec()):
                return super().accept();
        else:
            return super().accept();
            

class ExportPanel(QWidget):
    exportActivated = pyqtSignal(); #export handled by imageselectorpane, not the export panel itself
    clearDir = pyqtSignal();

    def __init__(self):
        super().__init__();
        self.createObjects();

    def createObjects(self):
        self.layout = QGridLayout(self);
        self.exportButton = QPushButton("Export Changes");
        self.clearButton = QPushButton("Clear All Changes");

        self.exportButton.clicked.connect(self.exportActivated.emit);
        self.clearButton.clicked.connect(self.clearChanges);

        self.layout.addWidget(self.exportButton,0,0);
        self.layout.addWidget(self.clearButton,0,1);
        self.setLayout(self.layout);



    def clearChanges(self):
        confirmBox = QMessageBox(QMessageBox.Icon.Warning,"Clear Changes?","Clear all changes and revert to original masks?");
        confirmBox.setInformativeText("This action cannot be undone.");
        clearbtn = confirmBox.addButton("Clear Changes",QMessageBox.ButtonRole.AcceptRole);
        confirmBox.addButton(QMessageBox.StandardButton.Cancel);

        confirmBox.exec();
        if (confirmBox.clickedButton() == clearbtn):
            self.clearDir.emit()


class QDumbWindow(QMainWindow,DataObject):
    def __init__(self):
        super().__init__();
        self.segmenter = MaskSegmenter(self,parent=self);
        self.setCentralWidget(self.segmenter);
        self.createActions();

    def createActions(self):
        self.prevAction = QAction("Previous Image");
        self.nextAction = QAction("Next Image");
        self.increaseAction = QAction("Increase Brush Size");
        self.decreaseAction = QAction("Decrease Brush Size");
        self.undoAction = QAction("Undo Brush Stroke");
        self.redoAction = QAction("Redo Brush Stroke");
        self.imageDirAction = QAction("Open Image Directory");
        self.maskDirAction = QAction("Open Mask Directory");
        self.exitAction = QAction("Exit");
        self.aboutAction = QAction("About");
        self.shortcutsAction = QAction("Keyboard Shortcuts");
        self.exportAction = QAction("Export Masks");
        self.actions = [self.prevAction,
            self.nextAction,
            self.increaseAction,
            self.decreaseAction,
            self.undoAction,
            self.redoAction,
            self.imageDirAction,
            self.maskDirAction,
            self.exitAction,
            self.aboutAction,
            self.shortcutsAction,
            self.exportAction];
        
        self.prevAction.setShortcut(QKeySequence("left"));
        self.nextAction.setShortcut(QKeySequence("right"));
        self.increaseAction.setShortcut(QKeySequence("up"));
        self.decreaseAction.setShortcut(QKeySequence("down"));
        self.undoAction.setShortcut(QKeySequence.StandardKey.Undo);
        self.redoAction.setShortcut(QKeySequence.StandardKey.Redo);

        self.prevAction.triggered.connect(lambda: self.segmenter.data.selector.incrementImage(-1));
        self.nextAction.triggered.connect(lambda: self.segmenter.data.selector.incrementImage(1));
        self.increaseAction.triggered.connect(lambda: self.segmenter.editor.toolbar.slider.triggerAction(QAbstractSlider.SliderAction.SliderSingleStepAdd));
        self.decreaseAction.triggered.connect(lambda: self.segmenter.editor.toolbar.slider.triggerAction(QAbstractSlider.SliderAction.SliderSingleStepSub));
        self.undoAction.triggered.connect(self.segmenter.editor.maskView.maskContainer.mask.undo);
        self.redoAction.triggered.connect(self.segmenter.editor.maskView.maskContainer.mask.redo);
        self.exportAction.triggered.connect(self.segmenter.data.selector.export);
        self.imageDirAction.triggered.connect(self.segmenter.data.selector.imageDirChooser.checkDialog);
        self.maskDirAction.triggered.connect(self.segmenter.data.selector.maskDirChooser.checkDialog);
        self.exitAction.triggered.connect(self.close);
        self.aboutAction.triggered.connect(self.about);
        self.shortcutsAction.triggered.connect(self.shortcuts);

        menubar = self.menuBar();
        fileMenu = menubar.addMenu("&File");
        editMenu = menubar.addMenu("&Edit");
        helpMenu = menubar.addMenu("&Help");

        fileMenu.addActions([self.imageDirAction,self.maskDirAction,self.exportAction,self.exitAction]);
        editMenu.addActions([self.nextAction,self.prevAction,self.increaseAction,self.decreaseAction,self.undoAction,self.redoAction]);
        helpMenu.addActions([self.aboutAction,self.shortcutsAction]);

    def about(self):
        #TODO: edit about text
        mbox = QMessageBox(QMessageBox.Icon.NoIcon,"About Mask Segmenter","Mask Segmenter is a program designed by Harrison Truscott for Jim Bear and Tim Elston's labs at UNC, for use in combination with Sam Ramirez's AI Segmenter. For more information, please visit <a href='https://github.com/minerharry/SegmenterGui'>the GitHub homepage</a>.",QMessageBox.StandardButton.Ok,parent=self);
        mbox.setDefaultButton(QMessageBox.StandardButton.Ok);
        mbox.setTextFormat(Qt.TextFormat.RichText);
        mbox.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction);
        #mbox.setOpenExternalLinks(True);
        mbox.exec();

    def shortcuts(self):
        shortcutList = [(action.text(),action.shortcut().toString()) for action in self.actions if action.shortcut()]
        shortcutList += [("Toggle Draw Mode","Hold Ctrl/Shift"),("Hide Mask","Hold Space"),("Zoom In/Out","Ctrl+Scroll Up/Scroll Down")];
        QMessageBox.information(self,"Keyboard Shortcuts","\n".join(["{0}: {1}".format(name,key) for (name,key) in shortcutList]),QMessageBox.StandardButton.Ok,defaultButton=QMessageBox.StandardButton.Ok);
            
    def closeEvent(self, a0: QCloseEvent) -> None:
        return self.segmenter.closeEvent(a0);
        
def init_logger():
    """This is so that Javabridge doesn't spill out a lot of DEBUG messages
    during runtime.
    From CellProfiler/python-bioformats.
    """
    rootLoggerName = javabridge.get_static_field("org/slf4j/Logger",
                                         "ROOT_LOGGER_NAME",
                                         "Ljava/lang/String;")

    rootLogger = javabridge.static_call("org/slf4j/LoggerFactory",
                                "getLogger",
                                "(Ljava/lang/String;)Lorg/slf4j/Logger;",
                                rootLoggerName)

    logLevel = javabridge.get_static_field("ch/qos/logback/classic/Level",
                                   "WARN",
                                   "Lch/qos/logback/classic/Level;")

    javabridge.call(rootLogger,
            "setLevel",
            "(Lch/qos/logback/classic/Level;)V",
            logLevel)



if __name__ == '__main__':
    if Defaults.loadMode == LoadMode.biof:
        javabridge.start_vm(class_path=bf.JARS);
        init_logger();
    app = QApplication(sys.argv)
    window = QDumbWindow();
    window.show();
    app.exec();
    if Defaults.loadMode == LoadMode.biof:
        javabridge.kill_vm();
    sys.exit();
