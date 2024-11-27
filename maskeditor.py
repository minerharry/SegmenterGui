from ColorButton import ColorButton
from enum import Enum
import parsend
from to_precision import std_notation
from rangesliderside import RangeSlider
from PyQt6 import QtGui
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtWidgets import QAbstractItemView, QAbstractSlider, QApplication, QCheckBox, QComboBox, QCompleter, QDialog, QFileDialog, QGraphicsPathItem, QGraphicsScene, QGraphicsView, QGridLayout, QHBoxLayout, QLabel, QLayout, QLineEdit, QListView, QMainWindow, QMenu, QMessageBox, QPushButton, QSizePolicy, QSlider, QSplitter, QStatusBar, QStyle, QStyleOptionFrame, QToolButton, QVBoxLayout, QWidget, QWhatsThis
from PyQt6 import QtCore
from PyQt6.QtCore import QFile, QLineF, QMargins, QMarginsF, QPoint, QPointF, QRect, QRectF, QSignalMapper, QSize, QStringListModel, QTimer, Qt, pyqtSignal, pyqtSlot, QObject, QEvent, QUrl, QCoreApplication, QByteArray, QIODevice, QBuffer
from PyQt6.QtGui import QAction, QBitmap, QBrush, QCloseEvent, QColor, QCursor, QDoubleValidator, QFontMetrics, QGuiApplication, QIcon, QImage, QImageWriter, QIntValidator, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap, QPolygon, QPolygonF, QShortcut, QKeySequence, QTextDocument, QTransform, QUndoCommand, QUndoStack, QValidator
import numpy as np
import math
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer
import sys
import os
import shutil
import json_tricks as json
import inspect
import circleutil
from typing import Any, Union,List,Tuple
from skimage.transform import resize
from skimage.exposure import rescale_intensity
from pathlib import Path
from tqdm import tqdm
import webbrowser
from natsort import natsorted, ns

class LoadMode:
    biof = 0;
    skimage = 1;
    imageio = 2;

class Defaults:
    bioLogging = False;
    loadMode = LoadMode.imageio; #TODO: image load error when switching between formats on first load, not reproducible
    blankSize = QSize(300,300);
    blankColor = QColor(0,0,0,0);
    defaultFG = QColor(255,255,255,10)#QColor(255,0,255,50)
    defaultBG = QColor(70,0,0,60)#QColor(0,255,255,50)
    bmapFG = Qt.GlobalColor.color0
    bmapBG = Qt.GlobalColor.color1;
    defaultBrushSize = 10;
    maxBrushSliderSize = 80;
    maxBrushInputSize = 999;
    filePathMaxLength = 200; #characters
    drawButtonNames = ("Include", "Exclude");
    drawButtonsLabel = "Draw Mode";
    workingDirectory = "working_masks/";
    sessionFileName = "session_dat.json";
    supportedImageExts = [".bmp",".png",".jpg",".pbm",".jpeg",".tif",".sld",".aim",".al3d",".gel",".am",".amiramesh",".grey",".hx",".labels",".cif",".img",".hdr",".sif",".afi",".svs",".htd",".pnl",".avi",".arf",".exp",".sdt",".1sc",".pic",".raw",".xml",".scn",".ims",".cr2",".crw",".ch5",".c01",".dib",".dv",".r3d",".dcm",".dicom",".v",".eps",".epsi",".ps",".flex",".mea",".res",".tiff",".fits",".dm3",".dm4",".dm2",".gif",".naf",".his",".vms",".i2i",".ics",".ids",".seq",".ipw",".hed",".mod",".leff",".obf",".msr",".xdce",".frm",".inr",".ipl",".ipm",".dat",".par",".jp2",".jpk",".jpx",".xv",".bip",".fli",".lei",".lif",".scn",".sxm",".l2d",".lim",".stk"]; 
    supportedMaskExts = supportedImageExts; #TODO: filter list by image formats and not just supported formats
    autosaveTime = 60*1000; #milliseconds
    exportedFlagFile = "export.flag";
    attemptMaskResize = False;
    penPreview = True;
    exactPreviewWidth = 0.6;
    circlePreviewWidth = exactPreviewWidth*5;
    allowMaskCreation = True;
    defaultMaskFormat = ".bmp";
    adjustSigFigs = 4;
    histSliderPrecision = 100000
    convertUnassignedMasks = True; #whether to convert masks with no equivalent in the mask source directory to some standard type, and prompt the user of that type
    createEmptyMasksForExport = False;
    adjustForcePreview = False;



def getTypes(dic:dict,types:set=set()):
    for k,v in dic.items():
        if isinstance(v,dict):
            types = types.union(getTypes(v,types));
        else:
            types.add(type(v));
        if isinstance(v,np.int64):
            print(f"Value {v} with key {k} has type int64")
    return types;
        
if Defaults.loadMode == LoadMode.biof:
    import bioformats as bf
    import javabridge
    if not(Defaults.bioLogging):
        def init_logger(self):
            pass
        bf.init_logger = init_logger
elif Defaults.loadMode == LoadMode.skimage:
    raise DeprecationWarning("skimage imread/imsave is deprecated! Please use imageio.")
    from skimage.io import imread,imsave
else:
    from imageio import imread,imsave


class DataObject: #basic implementation of object data loading/saving

    #loadstate is mostly internal, but can be overriden if need be
    def _loadState(self,data,stack="root",**kwargs):
        print("loading state for object",stack);
        errors = [];
        if data == {}:
            return errors;
        if 'children' in data:
            for name,datum in data['children'].items():
                if (hasattr(self,name)):
                    # print("loading child state:",name);
                    child = getattr(self,name)
                    if isinstance(child,DataObject):
                        errors.extend(child._loadState(datum,stack = stack+"."+name));
                    else:
                        print(f"Data state load error: named child {name} not an instance of DataObject");
                else:
                    print(f"Data state load error: named child {name} not part of class {self}");
        selfData = None;
        if 'self' in data:
            selfData = data['self'];
        try:
            self.loadData(selfData,**kwargs);
        except Exception as e:
            errors.append([stack,str(type(e)),repr(e),repr(e.with_traceback(None))]);
        return errors;
        

    def loadData(self,data): #loads data for self; can be left blank if no data for that class
        pass;

    #getstatedata is mostly internal, but can be overriden if need be
    def _getStateData(self,stack="root"): #error format: list of [obj_stack,type,error] errors;
        children = {};
        errors = [];
        for child,chObj in inspect.getmembers(self,lambda x: isinstance(x,DataObject)):
            children[child],ch_errors = DataObject._getStateData(chObj,stack=stack+"."+child);
            errors.extend(ch_errors);
        selfdata = None;
        error = None;
        try:
            selfdata = self.getSaveData();
        except Exception as e:
            error = [stack,str(type(e)),repr(e),repr(e.with_traceback(None))];
            errors.append(error);
        out_dict = {};
        if selfdata:
            out_dict['self'] = selfdata;
        if children:
            out_dict['children'] = children;
        if error:
            out_dict['save error'] = error[3];
        return [out_dict,errors];

    def getSaveData(self): #returns state data for self; can be left blank if no data for that class
        return {};

class CursorLoader:
    def __init__(self,delay,delegate:QWidget):
        self.timer = QTimer();
        self.timer.setInterval(delay);
        self.timer.setSingleShot(True);
        self.timer.timeout.connect(self._activate);
        self.activated = False;
        self.delegate = delegate;

    def start(self):
        # self.timer.start();
        self._activate();

    def stop(self):
        # self.timer.stop();
        self._deactivate()

    def _activate(self):
        if not self.activated:
            self.activated = True;
            QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor);
            self.delegate.update();

    def _deactivate(self):
        if self.activated:
            self.activated = False;
            QGuiApplication.restoreOverrideCursor();
            self.delegate.update();

class MaskSegmenter(QSplitter,DataObject):
    def __init__(self,window,status=None,parent=None):
        super().__init__(parent);
        self.createObjects(window,status);
    
    def createObjects(self,window,statusBar=None):
        self.setFocus();

        if not os.path.exists(Defaults.workingDirectory):
            os.mkdir(Defaults.workingDirectory);

        self.editor = EditorPane();
        self.data = DataPane();
        self.statusBar:SegmenterStatusBar = statusBar;

        # self.lay = QHBoxLayout();
        # self.lay.addWidget(self.data);
        # self.lay.addWidget(self.editor);
        # self.lay.setStretch(1, 2)
        # self.setLayout(self.lay);
        self.addWidget(self.data);
        self.addWidget(self.editor);
        self.setHandleWidth(20);
        self.setStyleSheet("QSplitterHandle {background-image: black;}")
        

        self.ctrl = False;
        self.shift = False;

        self.editor.toolbar.iButtons.increment.connect(self.data.selector.incrementImage);
        self.data.selector.prepImageChange.connect(self.editor.maskView.maskContainer.prepSwitchImage);
        self.data.selector.imageChanged.connect(self.editor.toolbar.adjustDialog.imageChanged);
        self.data.selector.imageChanged.connect(self.editor.maskView.maskContainer.switchImage);
        self.editor.toolbar.maskRevert.connect(self.data.selector.revertMask);
        self.data.selector.directoryChanged.connect(self.editor.toolbar.adjustDialog.reset);
        self.data.selector.directoryChanged.connect(self.editor.maskView.fitImageInView);

        self.exitConfirm = MaskUnexportedDialog(
            "Warning: You have unexported masks. \nYour changes and session will be saved.",
            buttonNames=["Exit","Export and Exit"]);
        self.exitConfirm.exportClicked.connect(self.data.selector.export);

        window.installEventFilter(self);
        self.data.selector.list.installEventFilter(self);
        self.editor.toolbar.maskCheck.installEventFilter(self);
        self.editor.toolbar.adjustButton.installEventFilter(self);
        self.editor.toolbar.exactCheck.installEventFilter(self);
        self.data.selector.maskDirChooser.browseButton.installEventFilter(self);
        self.data.selector.imageDirChooser.browseButton.installEventFilter(self);
        self.data.exportPane.exportButton.installEventFilter(self);
        self.data.exportPane.clearButton.installEventFilter(self);
        self.editor.toolbar.colorbuttons.installEventFilter(self)
        QCoreApplication.instance().installEventFilter(self);

        ### SESSION SAVING STUFF
        self.autosaveTimer = QTimer(self);
        self.sessionManager = SessionManager(Defaults.sessionFileName,self);
        self.sessionManager.loadData();
        self.autosaveTimer.timeout.connect(self.sessionManager.saveData)
        self.data.selector.directoryChanged.connect(self.sessionManager.saveData)
        self.sessionManager.saveData();
        self.autosaveTimer.setInterval(Defaults.autosaveTime);
        self.autosaveTimer.start();

        self.data.selector.workingDirCleared.connect(self.sessionManager.saveData);

        self.sessionManager.error.connect(self.receiveError);
        self.editor.maskView.maskContainer.mask.error.connect(self.receiveError);
        self.editor.maskView.maskContainer.error.connect(self.receiveError);
        self.data.selector.error.connect(self.receiveError);

        self.cursor = CursorLoader(1500,self);
        self.data.selector.exportStart.connect(self.cursor.start);
        self.data.selector.exportEnd.connect(self.cursor.stop);
        self.data.selector.exportCanceled.connect(self.cursor.stop);
        # self.data.selector.imLoadStart.connect(self.cursor.start); TODO: figure out cursor change only if taking a long time
        # self.data.selector.imLoadEnd.connect(self.cursor.stop);
        # self.data.selector.imLoadCanceled.connect(self.cursor.stop);
        # self.editor.maskView.maskContainer.rescaleStart.connect(self.cursor.start);
        # self.editor.maskView.maskContainer.rescaleEnd.connect(self.cursor.stop);
        # self.editor.maskView.maskContainer.rescaleCanceled.connect(self.cursor.stop);

        if self.statusBar:
            self.sessionManager.saved.connect(self.statusBar.saveMessage);
            if Defaults.penPreview:
                self.editor.maskView.cursorUpdate.connect(self.statusBar.showCursorPos);
            self.data.selector.exportTriggered.connect(lambda:self.statusBar.showMessage("Exporting..."));
            self.data.selector.exportCanceled.connect(lambda: self.statusBar.showMessage("Export Canceled",15000))
            self.data.selector.exportEnd.connect(lambda: self.statusBar.showMessage("Export Successful",10000))
            self.data.selector.imLoadTriggered.connect(lambda:self.statusBar.showMessage("Loading Image/Mask..."));
            self.data.selector.imLoadCanceled.connect(lambda: self.statusBar.showMessage("Image/Mask Loading Failed",15000))
            self.data.selector.imLoadEnd.connect(lambda: self.statusBar.showMessage("Image/Mask Successfully Loaded",10000))
            self.editor.maskView.maskContainer.rescaleTriggered.connect(lambda:self.statusBar.showMessage("Rescaling Image Intensity..."));
            self.editor.maskView.maskContainer.rescaleCanceled.connect(lambda: self.statusBar.showMessage("Image Intensity Rescale Failed",15000))
            self.editor.maskView.maskContainer.rescaleEnd.connect(lambda: self.statusBar.showMessage("Image Intensity Rescaled Successfully",15000))
        
        self.editor.maskView.fitImageInView();
            
        


    def receiveError(self,error_msg,timeout=None,label=None):
        if error_msg is not None and error_msg != '':
            print(f"ERROR: {error_msg}");
        if self.statusBar:
            self.statusBar.showErrorMessage(error_msg,timeout=timeout,label=label);

    def closeEvent(self, a0: QCloseEvent) -> None:
        if (self.exitConfirm.exec()):
            self.sessionManager.saveData();
            return super().closeEvent(a0);
        a0.ignore();

    def event(self,ev):
        # if ev.type() == QEvent.Type.KeyPress:
        #     print("key event - segmenter");
        return super().event(ev);
        

    def eventFilter(self,obj:QObject,ev:Union[QtGui.QInputEvent,Any]):
        if not isinstance(ev,QtGui.QInputEvent): return False
        tobj = obj
        while ( tobj is not  None ):
            if( tobj == self ):
                break;
            try:
                tobj = tobj.parent()
            except:
                from IPython import embed; embed()
        if tobj is None:
            return False

        out = False;
        if ev.type() in [QEvent.Type.KeyPress,QEvent.Type.ShortcutOverride]:
            # print("key event - filter");
            if (Qt.KeyboardModifier.ControlModifier in ev.modifiers()):
                self.editor.toolbar.drawButtons.setValue(1,store=True);
                self.ctrl = True;
                # print("control pressed");
                out = True;
            if (Qt.KeyboardModifier.ShiftModifier in ev.modifiers()):
                self.editor.toolbar.drawButtons.setValue(0,store=True);
                self.shift = True;
                # print("shift pressed");
                out = True;
            if (ev.key() == Qt.Key.Key_Tab):
                self.editor.toolbar.exactCheck.setChecked(True);
                # print("tab pressed");
                out = True
            if (ev.key() == Qt.Key.Key_Space):# and not ev.isAutoRepeat()):
                self.editor.toolbar.maskCheck.setChecked(True);
                # print("space pressed");
                out = True;
        if ev.type() == QEvent.Type.KeyRelease:
            if (Qt.KeyboardModifier.ControlModifier not in ev.modifiers() and self.ctrl): 
                self.editor.toolbar.drawButtons.restoreValue();
                # print("ctrl released")
                self.ctrl = False;
                out = True;
            if (Qt.KeyboardModifier.ShiftModifier not in ev.modifiers() and self.shift):
                self.editor.toolbar.drawButtons.restoreValue();
                # print("shift released")
                self.shift = False;
                out = True;
            if (ev.key() == Qt.Key.Key_Space and not ev.isAutoRepeat()):
                self.editor.toolbar.maskCheck.setChecked(False);
                # print("space released");
                out = True;
            if (ev.key() == Qt.Key.Key_Tab and not ev.isAutoRepeat()):
                self.editor.toolbar.exactCheck.setChecked(False);
                # print("tab released");
                out = True
        return out;       

class SegmenterStatusBar(QStatusBar): #TODO: add additional status & error messages as needed
    def __init__(self):
        super().__init__();
        self.createObjects();

    def createObjects(self):
        self.errorWidget = QLabel();
        self.errorWidget.setStyleSheet("QLabel {color : red;}");
        self.errorTimer = QTimer(self);
        self.errorTimer.setSingleShot(True);
        self.errorTimer.timeout.connect(self.clearError);
        self.errorLabel = '';

        self.cursorWidget = QLabel();

        self.addPermanentWidget(self.errorWidget);
        self.addPermanentWidget(self.cursorWidget);

        self.errorWidget.hide();
        self.cursorWidget.hide();

    def clearError(self):
        print("clearing error");
        self.errorWidget.hide();
        self.errorTimer.stop();
        self.errorLabel = None;

    def showMessage(self, message: str, msecs: int=0) -> None:
        return super().showMessage(message, msecs=msecs)

    def showCursorPos(self,pos:QPointF):
        if bool(pos) and not pos.isNull():
            self.cursorWidget.setText(f"({std_notation(pos.x(),4)},{std_notation(pos.y(),4)})");
            if not self.currentMessage():
                self.cursorWidget.show();
        else:
            self.cursorWidget.hide();

    def showErrorMessage(self,msg,timeout=None,label=None):
        print("Error Received:",msg,timeout,label);
        if (msg is None or msg == ""): #clear-error command, check if relevant
            if (not(label) or label == self.errorLabel):
                self.clearError();
            return;
        self.errorWidget.setText(f"Error: {msg}");
        self.errorWidget.show();
        self.errorLabel = label;
        if timeout:
            self.errorTimer.start(timeout);
        else:
            self.errorTimer.stop(); #ensure earlier timer doesn't override;

    def saveMessage(self):
        self.showMessage("Saving session...",3000)

class SessionManager(QObject):
    error = pyqtSignal(str,int,str);
    saved = pyqtSignal();

    def __init__(self,path:os.PathLike,dataSource:DataObject):
        super().__init__();
        self.dataSource = dataSource;
        self.path = path;
        print(f"attempting to load session; checking existence of path: {self.path}")
        if os.path.exists(self.path):
            try: 
                with open(self.path,'r') as f:
                    self.data = json.load(f);
                    if 'Session Data' in self.data:
                        self.data = self.data['Session Data']
            except:
                self.error.emit(f"Session data could not be read from {self.path}",10000,'session');
                self.data = {};
        else:
            self.error.emit(f"Session data location {self.path} does not exist",10000,'session');
            self.data = {};

    def loadData(self):
        errors = self.dataSource._loadState(self.data);
        if errors:
            for error in errors:
                print(f"Error in loading data to {error[0]}: {error[3]}");

    def saveData(self):
        self.saved.emit();
        print('saving...');
        self.data,errors = self.dataSource._getStateData();
        if errors:
            error_msg = ""
            if len(errors) == 1:
                error = errors[0]
                error_msg = f"Save error: {error[1]} when attempting to save {error[0]},";
            else:
                error_msg = f"Save error: {len(errors)} errors when attempting to save session data,";
            error_msg += " See " + Defaults.sessionFileName + " for more details";
            self.error.emit(error_msg,60000,'save');
        for error in errors:
            print(f"Error in getting save data from {error[0]}: {error[3]}");
        backup = {};
        if os.path.exists(self.path):
            with open(self.path,'r') as f:
                try:
                    backup = json.load(f);
                except:
                    pass;
        with open(self.path,'w') as f:
            savedata = {'Session Data': self.data}
            if errors:
                savedata['Errors'] = errors;
            try:
                json.dump(savedata,f);
            except Exception as e:
                json.dump(backup,f);
                self.error.emit("SESSION SAVE FAILED",30000,'session')
                print("JSON SAVE ERROR:",e.with_traceback(None))
                print(f"when attempting to load data of types {getTypes(savedata)}")
        
            
        
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
        if Defaults.penPreview:
            self.toolbar.slider.valueChanged.connect(self.maskView.setPreviewDiameter);
        self.toolbar.drawButtons.valueChanged.connect(self.maskView.maskContainer.mask.setDrawMode);
        self.toolbar.maskCheck.toggled.connect(lambda x: self.maskView.maskContainer.mask.setPixlayerVisibility(not(x)));
        self.toolbar.zButtons.zoomed.connect(self.maskView.zoom);
        self.toolbar.adjustDialog.pixelRangeChanged.connect(self.maskView.maskContainer.setOverrideRescale);
        self.toolbar.adjustDialog.rangeReset.connect(self.maskView.maskContainer.resetOverride);
        self.toolbar.zoomReset.clicked.connect(self.maskView.fitImageInView);
        if Defaults.penPreview:
            self.toolbar.previewCheck.clicked.connect(lambda x: self.maskView.setPreviewsVisible(not x));
            self.toolbar.exactCheck.toggled.connect(self.maskView.setExactCursorMode);
        self.maskView.maskContainer.imageRanged.connect(self.toolbar.adjustDialog.setPixelRange);
        self.maskView.maskContainer.imageDataRead.connect(self.toolbar.adjustDialog.loadImageData);
        self.toolbar.colorbuttons.fgColorChanged.connect(self.maskView.maskContainer.mask.setFGColor)
        self.toolbar.colorbuttons.bgColorChanged.connect(self.maskView.maskContainer.mask.setBGColor)

class MaskedImageView(QGraphicsView,DataObject):
    wheel_factor = 0.1;
    zoomChanged = pyqtSignal(float);
    cursorUpdate = pyqtSignal(QPointF);
    tabletErasing = pyqtSignal(bool);

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def fitImageInView(self):
        self.fitInView(self.proxy,Qt.AspectRatioMode.KeepAspectRatio);
        self.scaleFactor = 1;

    def createObjects(self):
        self.graphicsScene = QGraphicsScene();
        self.scaleFactor = 1;
        self.maskContainer = MaskContainer();
        self.proxy = self.graphicsScene.addWidget(self.maskContainer);
        self.maskContainer.sizeChanged.connect(self.proxyChanged);
        self.maskContainer.mask.cursorMove.connect(self.updatePreviews);
        self.maskContainer.mask.draggingStart.connect(self.previewSwitchDragging)
        self.maskContainer.mask.draggingEnd.connect(self.previewSwitchHovering)
        self.setScene(self.graphicsScene);
        self.tabletErasing.connect(self.maskContainer.mask.setTabletErasing)
        self.setMouseTracking(True);
        if Defaults.penPreview:
            self.diameter = Defaults.defaultBrushSize;
            self.exactPreviewThickness = Defaults.exactPreviewWidth;
            self.circlePreviewThickness = Defaults.circlePreviewWidth;
            self.backPath = None;
            self.forePath = None;
            self.pathsEnabled = True;
            
            backpen = QPen(QColor(255,255,255),self.circlePreviewThickness,Qt.PenStyle.SolidLine);
            backpen.setCosmetic(True);
            self.preview = self.graphicsScene.addEllipse(300,50,30,30,backpen);
            self.preview.setVisible(False);
            self.preview.setZValue(50);

            pen = QPen(QColor(0,0,0),self.circlePreviewThickness,Qt.PenStyle.DotLine);
            pen.setCosmetic(True);
            self.backPreview = self.graphicsScene.addEllipse(QRectF(),pen);
            self.backPreview.setZValue(50);
            self.backPreview.setParentItem(self.preview);
            self.backPreview.setRect(QRectF(0,0,1,1));
            self.circlePreviewEnabled = False

            self.previewsVisible = True;
            self.setExactCursorMode(False);
            

    def setExactCursorMode(self,mode:bool):
        if Defaults.penPreview:
            self.exactMode = mode;
            self.setExactPreviewVisible(mode);
            self.setCirclePreviewVisible(not mode);

    def previewSwitchDragging(self):
        # print("preview switched to dragging mode")
        if Defaults.penPreview:
            self.setExactPreviewVisible(False);
            self.setCirclePreviewVisible(True);
    
    def previewSwitchHovering(self):
        # print("preview switched to hovering mode")
        if Defaults.penPreview and self.exactMode:
            self.setExactPreviewVisible(True);
            self.setCirclePreviewVisible(False);

    def setPreviewsVisible(self,visible):
        self.previewsVisible = visible;
        self.updatePreviews(-1);

    def setExactPreviewVisible(self,visible):
        if Defaults.penPreview:
            self.pathsEnabled = visible;
            self.drawBetweenPixels(-1);

    def setCirclePreviewVisible(self,visible):
        if Defaults.penPreview:
            self.circlePreviewEnabled = visible;
            self.updateCirclePreview(-1);

    @pyqtSlot()
    def proxyChanged(self):
        self.graphicsScene.setSceneRect(self.proxy.rect());

    def updatePreviews(self,position):
        if Defaults.penPreview:
            self.drawBetweenPixels(position);
            self.updateCirclePreview(position);

    def drawBetweenPixels(self,position):
        if position == -1:
            position = self.mapToScene(self.mapFromGlobal(QCursor.pos()));
            # print(f"position1: {position}");
            
            
        if not position or not self.pathsEnabled or not self.previewsVisible:
            if self.backPath is not None and self.forePath is not None:
                self.backPath.setVisible(False);
                self.forePath.setVisible(False);
            #NOTE: leaving persistent variables (diameter, lastpos) because the paths still exists in their previous locations
            return

        # print("drawing betweel pixels")
        left = self.proxy.geometry().left()
        top = self.proxy.geometry().top()
        pixel_width = self.proxy.geometry().width()/self.maskContainer.mask.pixlayer.width();
        pixel_height = self.proxy.geometry().height()/self.maskContainer.mask.pixlayer.height();
        # print("units per pixel width:",pixel_width);
        # print("pixel bounds:",(self.proxy.geometry().width(),self.proxy.geometry().height()))
        # print("pixmap size:",(self.maskContainer.mask.pixlayer.width(),self.maskContainer.mask.pixlayer.height()));
        
        adjusted_position = QPoint(int((position.x()-left)/pixel_width),int((position.y()-top)/pixel_height));
        # print(f"position: {position}");
        # print(f"adjusted position: {adjusted_position}");

        self.maskContainer.mask.setAdjustedDrawPoint([adjusted_position.x()*pixel_width + left,adjusted_position.y()*pixel_height + top]);
        # print(self.diameter);

        if self.backPath is None:
            outline = [(p[0]*pixel_width+left, p[1]*pixel_width+top) for p in circleutil.getCircleOutline((adjusted_position.x(),adjusted_position.y()),self.diameter/2)];
            path = QPainterPath(QPointF(*outline[-1]));
            for point in outline:
                path.lineTo(*point);
            self.backPath:QGraphicsPathItem = self.graphicsScene.addPath(path,QPen(QColor(255,255,255),self.exactPreviewThickness/self.scaleFactor));
            self.forePath:QGraphicsPathItem = self.graphicsScene.addPath(path,QPen(QColor(0,0,0),self.exactPreviewThickness/self.scaleFactor,Qt.PenStyle.DotLine));
            self.maskContainer.update();
        else:
            if self.drawnPathDiameter != self.diameter:
                outline = [(p[0]*pixel_width+left, p[1]*pixel_width+top) for p in circleutil.getCircleOutline((adjusted_position.x(),adjusted_position.y()),self.diameter/2)];
                path = QPainterPath(QPointF(*outline[-1]));
                for point in outline:
                    path.lineTo(*point);
                self.backPath.setPath(path);
                self.forePath.setPath(path);
                self.maskContainer.update();
            elif adjusted_position != self.drawnPathPos:
                offset = QPointF(adjusted_position-self.drawnPathPos);
                # print(f"translation offset: {offset}")
                self.backPath.setPath(self.backPath.path().translated(offset))
                self.forePath.setPath(self.forePath.path().translated(offset))
                self.maskContainer.update();
                # print(self.backPath.path().pointAtPercent(0));

            width = self.exactPreviewThickness/math.sqrt(self.scaleFactor);
            pen = self.backPath.pen()
            pen.setWidthF(width);
            self.backPath.setPen(pen);
            pen = self.forePath.pen()
            pen.setWidthF(width);
            self.forePath.setPen(pen);

        self.drawnPathPos = adjusted_position;
        self.drawnPathDiameter = self.diameter;
        self.backPath.setVisible(True);
        self.forePath.setVisible(True);

        # if not self.backBetween:
        #     print(f"drawing line at {(adjusted_position.x()*pixel_width,adjusted_position.y()*pixel_height,10*pixel_width,2*pixel_height)}");
        #     self.backBetween = self.graphicsScene.addRect(adjusted_position.x(),adjusted_position.y(),10*pixel_width,10*pixel_height,QPen(QColor(255,255,255),0.2));
        #     self.foreBetween = self.graphicsScene.addRect(adjusted_position.x(),adjusted_position.y(),10*pixel_width,10*pixel_height,QPen(QColor(0,0,0),0.2,Qt.PenStyle.DashLine));
        # else:
        #     self.backBetween.setRect(adjusted_position.x(),pixel_height,10*pixel_width,10*pixel_height);
        #     self.foreBetween.setRect(adjusted_position.x(),adjusted_position.y(),10*pixel_width,10*pixel_height);
        
    def updateCirclePreview(self,position):
        if position == -1:
            position = self.mapToScene(self.mapFromGlobal(QCursor.pos()))

        if not position or not self.circlePreviewEnabled or not self.previewsVisible:
            self.backPreview.setVisible(False);
            self.preview.setVisible(False);
            return;
        else:
            self.backPreview.setVisible(True);
            self.preview.setVisible(True);

        margin = self.circlePreviewThickness + 20;
        origin = self.preview.rect().adjusted(-margin,-margin,margin,margin);
        self.preview.setVisible(True); 
        newRect = QRectF(position.x()-self.diameter/2*0.95,position.y()-self.diameter/2*0.95,self.diameter,self.diameter);
        self.preview.setRect(newRect)
        self.backPreview.setVisible(True);
        self.backPreview.setRect(newRect);
        self.repaint(origin.toRect());
        self.repaint(newRect.adjusted(-margin,-margin,margin,margin).toRect());            
        self.scene().update();
        self.update();

    def setPreviewDiameter(self,size):
        self.diameter=size;
        self.updatePreviews(-1);

    def wheelEvent(self,event):
        self.cursorUpdate.emit(self.mapToScene(event.position().toPoint()));
        if (Qt.KeyboardModifier.ControlModifier in event.modifiers()):
            angle = event.angleDelta().y();
            factor = 1 + (1 if angle > 0 else -1)*self.wheel_factor;
            self.zoom(factor, anchor=QGraphicsView.ViewportAnchor.AnchorUnderMouse);
        else:
            super().wheelEvent(event);
        if Defaults.penPreview:
            self.updatePreviews(-1);
            # print("wheely\n");
            # self.repaint() #since the start and end positions are farther away just repaint the whole thing lol

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if Defaults.penPreview:
            self.mousePos = None;
            self.updatePreviews(-1);
            self.cursorUpdate.emit(self.mapToScene(event.position().toPoint()));
        super().mouseMoveEvent(event);


    @pyqtSlot(float)
    def zoom(self,factor,anchor=None):
        newFactor = self.scaleFactor*factor;
        self.scaleFactor = newFactor
        if (anchor):
            anch = self.transformationAnchor();
            self.setTransformationAnchor(anchor);
            self.scale(factor,factor);
            self.setTransformationAnchor(anch);
        else:
            self.scale(factor,factor);
        self.zoomChanged.emit(self.scaleFactor);

class DrawMode:
    INCLUDE = 0;
    EXCLUDE = 1;

class MaskContainer(QWidget,DataObject):
    error = pyqtSignal(str,int,str)
    sizeChanged = pyqtSignal(QSize);
    imageRanged = pyqtSignal(float,float);
    imageDataRead = pyqtSignal(np.ndarray);

    rescaleTriggered = pyqtSignal();
    rescaleStart = pyqtSignal();
    rescaleCanceled = pyqtSignal();
    rescaleEnd = pyqtSignal();

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.overrideRescale = None;
        self.imName = None;
        self.imData = None;
        self.imRange = None;
        
        self.image = ImageDisplayer(self);
        self.mask:ImageMask = ImageMask(self);

        pixmap = QPixmap(Defaults.blankSize);
        pixmap.fill(Defaults.blankColor);
        self.image.setPixmap(pixmap)
        
        self.iFileName = None;
        self.mFileName = None;


    def sizeHint(self) -> QSize:
        return self.mask.sizeHint();

    def prepSwitchImage(self):
        self.imData = None;

    #switches to a specific image, and loads mask if provided
    #both image and mask are filenames
    @pyqtSlot(str,str)
    def switchImage(self,image=None,maskName=None):
        print(f"switching image, extant mask: {maskName}")
        errored = False;
        if image == "":
            image = None;
        if maskName == "":
            maskName = None;
        print(f"switching image to Image: {image} and Mask: {maskName}")
        if image == self.imName:
            print("image already loaded, reusing image data");
        else:
            if image is not None:
                pmap = self.readPixmap(image);
                self.image.setPixmap(pmap);
            else:
                self.imData = None;
                self.image.setPixmap(QPixmap(Defaults.blankSize));
                self.image.pixmap().fill(Defaults.blankColor);
        self.imName = image;
        # print("pixmap loaded")
        self.image.setFixedSize(self.image.pixmap().size());
        self.setFixedSize(self.image.size());
        # print("label pmap size:",self.image.pixmap().size())
        # print(self.image.geometry())
        # print(self.image.size());
        if maskName and os.path.exists(maskName):
            bmap = self.readBitmap(maskName,rsize=(self.image.size() if Defaults.attemptMaskResize else None));
            print("creating mask from file")
        else:
            errored = True;
            self.error.emit("No existing mask found; creating a blank one",20000,'mask');
            bmap = QBitmap(self.image.pixmap().size());
            print(self.image.pixmap().size(),bmap.size())
            bmap.fill(Defaults.bmapBG);
            if (Defaults.allowMaskCreation):
                maskName = image;
        if bmap.size() != self.image.pixmap().size(): #provided mask and image are of different sizes; create new mask
            errored = True;
            self.error.emit("Existing mask file is of a different size than corresponding image, creating a blank one; enable AttemptMaskResize to automatically resize input masks",20000,'mask') #TODO: Make this actually configurable
            bmap = QBitmap(self.image.pixmap().size());
            bmap.fill(Defaults.bmapBG);
        print("Bitmap created, loading...")
        self.mask.loadBitmap(bmap,maskName);
        print("Bitmap loaded")
        self.sizeChanged.emit(self.size());
        if not errored:
            self.error.emit("",0,'mask')

    def readPixmap(self,image,rintensity=True):
        self.imData = None;
        if Defaults.loadMode == LoadMode.biof:
            self.imData = bf.load_image(image);
        elif Defaults.loadMode in (LoadMode.skimage,LoadMode.imageio):
            self.imData = imread(image);
        self.imData = rescale_intensity(self.imData,in_range='dtype',out_range=(0.0,1.0));
        self.imageDataRead.emit(self.imData);
        if rintensity:
            self.imRange = (max(np.min(self.imData),0),np.max(self.imData));
            if self.imRange[0] == self.imRange[1]:
                self.error.emit("Image has only one value, setting to black",3000,"image");
                self.imRange = (self.imRange[0],self.imRange[0]+1)
            print("image ranged:",self.imRange);
            self.imageRanged.emit(*self.imRange);
        return self.rescaleAndPixmapData(external=False);

    def rescaleAndPixmapData(self,external=True):
        print("rescaling")
        if external:
            self.rescaleTriggered.emit();
        shape = self.imData.shape;
        bytesPerLine = 2*shape[1]
        type = np.uint16;
        format = QImage.Format.Format_Grayscale16
        if len(shape) > 2:
            bytesPerLine = shape[1]*shape[2];
            format = QImage.Format.Format_RGB888;
            type = np.uint8;
        if external:
            self.rescaleStart.emit();
        print("rescale:",self.overrideRescale)
        if self.overrideRescale:
            data = rescale_intensity(self.imData,self.overrideRescale,type);
        else:
            data = rescale_intensity(self.imData,self.imRange,type);
        im = QImage(data.data, shape[1], shape[0], bytesPerLine, format);
        # print("im size:",im.size());
        out_pix = QPixmap.fromImage(im);
        # print("pix size:",out_pix.size())
        if external:
            self.rescaleEnd.emit();
        return out_pix;

    def setOverrideRescale(self,min,max):
        if min is not None and max is not None:
            self.overrideRescale = (min,max);
        else:
            self.overrideRescale = None;
        if self.imData is not None:
            self.image.setPixmap(self.rescaleAndPixmapData());
        
    @pyqtSlot()
    def resetOverride(self):
        self.overrideRescale = None;
        if self.imRange:
            self.imageRanged.emit(*self.imRange);

    def readBitmap(self,map,rsize=None):
        if Defaults.loadMode == LoadMode.biof:
            bitData = bf.load_image(map);
        elif Defaults.loadMode in (LoadMode.skimage,LoadMode.imageio):
            bitData = imread(map).astype("uint16");
            bitData = rescale_intensity(bitData,'image',np.uint16);
        else:
            raise NotImplementedError(f"Load mode {Defaults.loadMode} not supported");


        if (rsize):
            print("resizing")
            if isinstance(rsize,QSize):
                rsize = [rsize.height(),rsize.width()];
            if (bitData.shape != rsize):
                bitData = resize(bitData,rsize,anti_aliasing=False);
        
        print(bitData)
        shape = bitData.shape;
        if len(bitData.shape) > 2:
            if len(bitData.shape) == 3:
                bitData = bitData[:,:,0].copy()
            else:
                raise Exception()

        result = QBitmap(QImage(bitData.data, shape[1], shape[0], 2*shape[1], QImage.Format.Format_Grayscale16));
        print(result)
        return result

    def resizeEvent(self, ev):
        self.sizeChanged.emit(self.size());

class ImageDisplayer(QWidget): #using this instead of QLabel prevents it from scaling up my pixmaps (!??!?) and stops anti-aliasing
    def __init__(self,parent=None):
        super().__init__(parent);
        self.image = None;

    def setPixmap(self,pmap):
        self.image = pmap;
        # print("pixmap set")
        super().update();

    def pixmap(self):
        return self.image

    def paintEvent(self,event):
        if self.image is not None:
            painter = QPainter(self);
            painter.drawPixmap(0,0,self.image);
            
class ImageMask(ImageDisplayer,DataObject):
    maskUpdate = pyqtSignal(); #whenever mask is changed or a stroke is completed; saves to working directory
    error = pyqtSignal(str,int,str);
    cursorMove = pyqtSignal(object); #[QPointF, None] are the options
    draggingStart = pyqtSignal();
    draggingEnd = pyqtSignal();

    def __init__(self,parent):
        super().__init__(parent);
        self.createObjects();
        self.lastPos = None;

    def update(self):
        if self.pixVisible:
            self.setPixmap(self.pixlayer);
        else:
            self.setPixmap(self.blankLayer)
        super().update();

    def createObjects(self,initSize=Defaults.blankSize):
        self.pixVisible = True;
        self.fileName = None;
        self.fgColor = Defaults.defaultFG;
        self.bgColor = Defaults.defaultBG;
        self.pen = QPen(self.fgColor,Defaults.defaultBrushSize,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin);
        self.brush = QBrush(self.fgColor);
        self.drawMode = DrawMode.INCLUDE;
        self.bitlayer = QBitmap(initSize);
        self.bitlayer.clear();
        self.pixlayer:QPixmap = QPixmap(initSize);
        self.setFixedSize(initSize)
        self.reloadPixLayer();
        self.setPixmap(self.pixlayer);
        self.maskUpdate.connect(self.save);
        self.blankLayer:QPixmap = QPixmap(self.pixlayer.size());
        self.blankLayer.fill(Defaults.blankColor);
        self.tabletErasing = False;

        self.resetUndoStack();#new states added to the end; lower number is more recent

    def setPixlayerVisibility(self,visible):
        self.pixVisible = visible;
        if visible:
            self.setPixmap(self.pixlayer);
        else:
            self.setPixmap(self.blankLayer);

    def resetUndoStack(self):
        self.undoStates = [self.bitlayer.copy()];
        self.lastBitId = 0;
        self.undoIds = [self.lastBitId];
        self.undoIndex = 0;

    def pushUndoStack(self):
        self.undoStates = [self.bitlayer.copy()] + self.undoStates[self.undoIndex:];
        self.lastBitId += 1;
        self.undoIds = [self.lastBitId] + self.undoIds[self.undoIndex:];
        self.undoIndex = 0;

    @pyqtSlot()
    def undo(self):
        print("undo triggered")
        if (self.undoIndex<len(self.undoStates)-1):
            self.undoIndex += 1;
            self.setBitmap(self.undoStates[self.undoIndex].copy());
            print("undone")

    @pyqtSlot()
    def redo(self):
        print("redo triggered")
        if (self.undoIndex > 0):
            self.undoIndex -= 1;
            self.setBitmap(self.undoStates[self.undoIndex].copy());
            print("redone")

    def setTabletErasing(self,erase):
        self.tabletErasing = erase;

    def setAdjustedDrawPoint(self,point):
        self.adjustDrawPoint=point;

    def mouseMoveEvent(self, e, dot=False):
        self.adjustDrawPoint = None
        self.cursorMove.emit(e.position());

        if not(Qt.MouseButton.LeftButton in e.buttons()): #TODO: Test compatibility tablet drawing
            self.lastPos = None;
            return;

        #print(e.position())
        if not(dot) and self.lastPos is None: # First event while moving
            self.lastPos = e.position();
            self.draggingStart.emit();
            # print("first mousemove event");
            return # Ignore the first time.

        colors = self.getPixColors(invert=self.tabletErasing);
        bitcolors = self.getBitColors(invert=self.tabletErasing);
        ##invert colors TODO: make sure this wild west inversion doesn't interfere with anything else lol

        bitpainter = QPainter(self.bitlayer)
        bitpainter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source);
        if dot:
            self.brush.setColor(bitcolors[self.drawMode]);
            bitpainter.setBrush(self.brush)
            if self.adjustDrawPoint:
                bitpainter.setPen(bitcolors[self.drawMode]);
                self.drawPoints = circleutil.getCircleFill(self.adjustDrawPoint,self.pen.widthF()/2);
                bitpainter.drawPoints(QPolygonF([QPointF(*p) for p in self.drawPoints]));
            else:
                bitpainter.setPen(Qt.PenStyle.NoPen)
                bitpainter.drawEllipse(e.position(),self.pen.widthF()/2,self.pen.widthF()/2);
        else:
            self.pen.setColor(bitcolors[self.drawMode]);
            bitpainter.setPen(self.pen);
            bitpainter.drawLine(self.lastPos, e.position())
        bitpainter.end()
        
        pixpainter = QPainter(self.pixlayer)
        pixpainter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source);

        if dot:
            self.brush.setColor(colors[self.drawMode]);
            pixpainter.setBrush(self.brush)
            if self.adjustDrawPoint:
                pixpainter.setPen(colors[self.drawMode]);
                pixpainter.drawPoints(QPolygonF([QPointF(*p) for p in self.drawPoints])); #draw points would have been generated in earlier block
            else:
                pixpainter.setPen(Qt.PenStyle.NoPen)
                pixpainter.drawEllipse(e.position(),self.pen.widthF()/2,self.pen.widthF()/2);
            #print(f"circle drawn, at position {e.position()} of radii {self.pen.widthF()}");
        else:
            self.pen.setColor(colors[self.drawMode]);
            pixpainter.setPen(self.pen);
            pixpainter.drawLine(self.lastPos, e.position())
        pixpainter.end();

        # Update the origin for next time.
        if not(dot):
            self.lastPos = e.position();
        self.update();


    def leaveEvent(self,ev: QEvent):
        self.cursorMove.emit(None)
        self.draggingEnd.emit();

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.pressPos = ev.position();
        self.mouseMoveEvent(ev,dot=True);

    def mouseReleaseEvent(self, e): #guaranteed called whenever mouse released after clicking on pane
        self.lastPos = None;
        self.maskUpdate.emit();
        self.draggingEnd.emit();
        self.pushUndoStack();

    def getPixColors(self,invert=False):
        return [self.fgColor,self.bgColor][::-1 if invert else 1];

    def getBitColors(self,invert=False):
        return [Defaults.bmapFG,Defaults.bmapBG][::-1 if invert else 1];

    def reloadPixLayer(self): 
        print("pix layer reloaded");
        self.pixlayer = QPixmap(self.bitlayer.size());
        self.blankLayer = QPixmap(self.pixlayer.size());
        self.blankLayer.fill(Defaults.blankColor);
        fg,bg = self.getPixColors();
        self.pixlayer.fill(fg)
        pixptr = QPainter(self.pixlayer);
        pixptr.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source);
        pixptr.setBackgroundMode(Qt.BGMode.OpaqueMode);
        pixptr.setBackground(fg);
        pixptr.setPen(bg);
        pixptr.drawPixmap(0,0,self.bitlayer);
        pixptr.end();
        self.update();

    #specifically loads a bitmap from memory and processes an image change, very different from setBitmap()
    def loadBitmap(self,bmap:QBitmap,fName):
        self.fileName = os.path.basename(fName) if fName else None;
        # print(Path(fName).parents)
        if Path(Defaults.workingDirectory) in Path(fName).parents:
            print(f"selected mask {fName} in working directory, splitting")
            self.fileName = os.path.splitext(self.fileName)[0] #working directory files have extra extension, ignore for saving purposes
        print("Loading mask with filename: " + str(self.fileName));
        self.setBitmap(bmap,update=False);
        self.resetUndoStack();

    #low-level command, changes loaded bitmap without doing any other intelligence
    def setBitmap(self,map:QBitmap,update=True):
        self.bitlayer = map;
        self.setFixedSize(self.bitlayer.size());
        self.reloadPixLayer();
        if update:
            self.maskUpdate.emit();

    def setFGColor(self,colour):
        self.fgColor = colour;
        print(f"Fg color set: {colour.name(QColor.NameFormat.HexArgb)}")
        self.reloadPixLayer()
    
    def setBGColor(self,colour):
        self.bgColor = colour;
        print(f"Bg color set: {colour.name(QColor.NameFormat.HexArgb)}")
        self.reloadPixLayer()

    @pyqtSlot(int)
    def setDrawMode(self,mode):
        self.drawMode = mode;

    @pyqtSlot(int)
    def setBrushSize(self,size):
        self.pen.setWidth(size);
    
    @pyqtSlot()
    def save(self):
        if (self.fileName is not None):
            
            savename = Defaults.workingDirectory+self.fileName+Defaults.defaultMaskFormat
            print(f"attempting save mask contents to {savename}");

            # saveName = self.fileName + Defaults.defaultMaskFormat;
            # names = os.path.splitext(self.fileName);
            # if (names[1][1:].lower() not in QImageWriter.supportedImageFormats()):
            #     saveName = names[0] + Defaults.defaultMaskFormat;

            data = QImageToArray(self.bitlayer,intermediate_format="bmp")
            print(data)
            print(data.max())
            np.save("test.png",data)

            self.bitlayer.save(savename); #NOTE: SAVES "inverted" according to windows preview - don't let it confuse you!
            ##NOTE: The numerical values saved by bitlayer.save change depending on the extension. for consistency, all should be saved with the same format.
            if (os.path.exists(Defaults.exportedFlagFile)):
                os.remove(Defaults.exportedFlagFile)
        else:
            self.error.emit("No mask source loaded, unable to save mask",20000,"mask");

def QImageToArray(incomingImage:Union[QImage,QPixmap],intermediate_format:str="PNG"):
    '''  Converts a QImage into an opencv/numpy MAT format  '''
    ba = QByteArray()
    buff = QBuffer(ba)
    # Essentially open up a "RAM" file
    buff.open(QIODevice.OpenModeFlag.ReadWrite)
    # Store a PNG formatted file into the "RAM" File
    incomingImage.save(buff, "PNG")
    import imageio
    image = imageio.imread(ba.data())
    return image

class MaskToolbar(QWidget,DataObject): #TODO: Fix second slider handle seeming to jump all the way left after mask revert
    maskRevert = pyqtSignal();

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();
    
    def createObjects(self):
        self.lay = QGridLayout()

        self.gridbutton_margins = QMargins(8,8,8,8);
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed);
        
        self.slider = EditableSlider(label="Brush Size");
        
        self.drawButtons = DualToggleButtons();
        
        self.maskCheck = QCheckBox("Hide Mask");
        
        if Defaults.penPreview:
            self.previewCheck = QCheckBox("Hide Cursor");
            self.exactCheck = QCheckBox("Exact Cursor");
        
        self.iButtons = NextPrevButtons();
        
        self.zButtons = ZoomButtons()
        
        zoomWidget = QWidget();
        zoomWidget.setLayout(QHBoxLayout());
        self.zoomReset = QPushButton("Reset Zoom");
        zoomWidget.layout().addWidget(self.zoomReset)
        
        adjustWidget = QWidget();
        adjustWidget.setLayout(QHBoxLayout());
        self.adjustButton = QPushButton("Adjust Brightness")
        adjustWidget.layout().addWidget(self.adjustButton);
        self.adjustDialog = AdjustmentDialog();
        self.adjustButton.clicked.connect(self.adjustDialog.exec);
        
        revertWidget = QWidget();
        revertWidget.setLayout(QHBoxLayout());
        self.revertButton = QPushButton("Revert to Original")
        revertWidget.layout().addWidget(self.revertButton);
        self.revertButton.clicked.connect(self.revert);
        self.maskRevert.connect(self.adjustDialog.reset);

        self.colorbuttons = ColorButtons()
        
        self.lay.addWidget(self.slider,0,0,-1,1);
        self.lay.addWidget(self.drawButtons,0,1,-1,1,Qt.AlignmentFlag.AlignCenter);
        
        if Defaults.penPreview:
            self.lay.addWidget(self.maskCheck,0,2,1,1,Qt.AlignmentFlag.AlignBottom);
            self.lay.addWidget(self.previewCheck,1,2,1,1,Qt.AlignmentFlag.AlignVCenter);
            self.lay.addWidget(self.exactCheck,2,2,1,1,Qt.AlignmentFlag.AlignTop);
        else:
            self.lay.addWidget(self.maskCheck,0,2,-1,1,Qt.AlignmentFlag.AlignCenter);
        self.lay.addWidget(self.iButtons,0,3,1,2,Qt.AlignmentFlag.AlignBottom);
        self.lay.addWidget(self.zButtons,1,3,-1,1,Qt.AlignmentFlag.AlignTop);
        self.lay.addWidget(revertWidget,1,5,-1,1,Qt.AlignmentFlag.AlignTop);
        self.lay.addWidget(zoomWidget,0,5,1,1,Qt.AlignmentFlag.AlignBottom);
        self.lay.addWidget(adjustWidget,1,4,-1,1,Qt.AlignmentFlag.AlignTop);
        self.lay.addWidget(self.colorbuttons,0,6,-1,1,Qt.AlignmentFlag.AlignTop)

        self.drawButtons.setContentsMargins(self.gridbutton_margins)
        zoomWidget.layout().setContentsMargins(self.gridbutton_margins)
        adjustWidget.layout().setContentsMargins(self.gridbutton_margins)
        revertWidget.layout().setContentsMargins(self.gridbutton_margins)

        self.lay.addWidget(None,0,7);
        self.lay.addWidget(None,2,1,-1,1); #below all widgets but the slider
        self.lay.setColumnStretch(7,10);
        self.lay.setRowStretch(2,10);
        self.lay.setVerticalSpacing(0);
        self.lay.setSpacing(0);
        self.lay.setContentsMargins(QMargins(0,0,0,0));

        self.setLayout(self.lay);

    def revert(self): #TODO: Potentially move into image selector pane, check if there are changes on current image
        confirmBox = QMessageBox(QMessageBox.Icon.Warning,"Revert Mask","Clear changes and revert to the original mask?");
        confirmBox.setInformativeText("This action cannot be undone.");
        clearbtn = confirmBox.addButton("Revert",QMessageBox.ButtonRole.AcceptRole);
        confirmBox.addButton(QMessageBox.StandardButton.Cancel);
        
        confirmBox.exec();
        if (confirmBox.clickedButton() == clearbtn):
            self.maskRevert.emit()


class EditableSlider(QWidget,DataObject): #TODO: Make maximum brush size not limited to slider range
    
    valueChanged = pyqtSignal(int); #whenever the value is changed internally

    def __init__(self,label="Slider",bounds=(1,Defaults.maxBrushSliderSize),defaultValue=Defaults.defaultBrushSize,parent=None):
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
        self.editor.setValidator(QIntValidator(bounds[0],Defaults.maxBrushInputSize));
        self.editor.setFixedWidth(25);
        self.layout().addWidget(self.editor,1,1);

        self.slider.actionTriggered.connect(lambda action: self.setValue(self.slider.sliderPosition())); #action unused atm
        self.editor.editingFinished.connect(lambda: self.setValue(int(self.editor.text())));

    @pyqtSlot(int) #assumes a validated value; sets both components
    def setValue(self,value,editValue=None):
        self.slider.setValue(value);
        if editValue:
            self.editor.setText(str(editValue))
        else:
            self.editor.setText(str(value));
        self.valueChanged.emit(value);

    def triggerAction(self,action):
        self.slider.triggerAction(action);

    def getSaveData(self):
        return [self.slider.value(),int(self.editor.text())];

    def loadData(self,data):
        self.setValue(*data);

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
        self.layout().setAlignment(self.label,Qt.AlignmentFlag.AlignCenter);
        self.layout().addWidget(self.label);
        self.label.setText(label);
        self.layout().setContentsMargins(0,0,0,0);

        self.buttonWidget = QWidget();
        self.layout().addWidget(self.buttonWidget);
        self.buttonWidget.setLayout(QHBoxLayout());
        self.buttonWidget.layout().setSpacing(0);
        self.buttonWidget.layout().setContentsMargins(0,0,0,0)

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
            self.buttons[buttonId].setChecked(True);
            return;
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
        self.lay = QHBoxLayout();
        self.bButton = QPushButton("Previous");
        self.nButton = QPushButton("Next");
        self.lay.addWidget(self.bButton);
        self.lay.addWidget(self.nButton);
        self.bButton.clicked.connect(self.handleBButton);
        self.nButton.clicked.connect(self.handleNButton);
        self.setLayout(self.lay);

    @pyqtSlot()
    def handleBButton(self):
        self.increment.emit(-1);

    @pyqtSlot()
    def handleNButton(self):
        self.increment.emit(1);

class ColorButtons(QWidget,DataObject):
    resetIconPath = "./reset.png"
    fgColorChanged = pyqtSignal(QColor)
    bgColorChanged = pyqtSignal(QColor)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.createObjects();

    def createObjects(self):
        self.fgColorButton = ColorButton(color=Defaults.defaultFG,allow_alpha=True)
        self.fgColorButton.colorChanged.connect(self.fgColorChanged.emit)
        self.fgColorButton.setToolTip("Foreground Color")

        self.bgColorButton = ColorButton(color=Defaults.defaultBG,allow_alpha=True)
        self.bgColorButton.colorChanged.connect(self.bgColorChanged.emit)
        self.bgColorButton.setToolTip("Background Color")
        
        self.resetButton = QToolButton()
        self.resetButton.setIcon(QIcon(self.resetIconPath))
        self.resetButton.clicked.connect(self.reset)
        self.resetButton.setToolTip("Reset colors to default")


        self.setLayout(QVBoxLayout());
        self.layout().addWidget(self.fgColorButton,Qt.AlignmentFlag.AlignHCenter)
        self.layout().addWidget(self.bgColorButton,Qt.AlignmentFlag.AlignHCenter)
        self.layout().addWidget(self.resetButton,Qt.AlignmentFlag.AlignHCenter)

        self.setStyleSheet("ColorButtons {border-style=solid;border-width=1px;border-color=lightgray;}")

    def reset(self):
        self.fgColorButton.setColor(Defaults.defaultFG)
        self.bgColorButton.setColor(Defaults.defaultBG)

    def loadData(self, data:tuple[Union[str,None],Union[str,None]]):
        self.fgColorButton.setColor(QColor(data[0]))
        self.bgColorButton.setColor(QColor(data[1]))

    @property
    def fgColor(self):
        return self.fgColorButton.color()
    
    @property
    def bgColor(self):
        return self.bgColorButton.color()

    def getSaveData(self):
        return (self.fgColor.name(QColor.NameFormat.HexArgb),self.bgColor.name(QColor.NameFormat.HexArgb))


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

        self.lay = QHBoxLayout();
        self.lay.addWidget(self.zInButton);
        self.lay.addWidget(self.zOutButton);
        # self.lay.addWidget(self.zoomDisplay);
        self.setLayout(self.lay);

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
        self.exportPane = ExportPanel();
        self.selector = ImageSelectorPane(self.exportPane);


        self.lay = QVBoxLayout();
        self.lay.addWidget(self.selector);
        self.lay.addWidget(self.exportPane);

        self.setLayout(self.lay);

        self.exportPane.clearDir.connect(self.selector.clearWorkingDir);
        self.exportPane.clearDir.connect(self.selector.changeImage);
        self.exportPane.exportActivated.connect(self.selector.export);

class ImageDirectoryWatcher(FileSystemEventHandler,QObject):
    directoryModified = pyqtSignal(FileSystemEvent);
    directoryRemoved = pyqtSignal();

    def on_any_event(self,event):
        if (event.is_directory):
            self.directoryRemoved.emit(event);
        else:
            self.directoryModified.emit(event);


#TODO: disallow (or give warning) for selecting the working directory as your image directory
class ImageSelectorPane(QWidget,DataObject):
    error = pyqtSignal(str,int,str);
    directoryChanged = pyqtSignal(str,str); #image directory, mask directory
    prepImageChange = pyqtSignal();
    imageChanged = pyqtSignal(str,str); #image file, mask file
    workingDirCleared = pyqtSignal();
    exportTriggered = pyqtSignal();
    exportStart = pyqtSignal();
    exportCanceled = pyqtSignal();
    exportEnd = pyqtSignal();
    imLoadTriggered = pyqtSignal();
    imLoadStart = pyqtSignal();
    imLoadCanceled = pyqtSignal();
    imLoadEnd = pyqtSignal();

    def __init__(self,export=None,parent=None):
        super().__init__(parent);
        self.createObjects(export);

    def createObjects(self,export): 
        self.importConfirm = MaskUnexportedDialog(
            "Warning: You have unexported masks. \nImporting new masks will overwrite the current changes. \nContinue?",
            buttonNames=["Overwrite Masks","Export Unsaved Masks"]); #TODO: Add "Transfer" option to transfer current working masks to new image directory
        self.imageChangeConfirm = MaskUnexportedDialog(
            "Warning: You have unexported masks. \nLoading a new image directory will overwrite the current changes. \nContinue?",
            buttonNames=["Overwrite Masks","Export Unsaved Masks"]);
        self.imageDirChooser = DirectorySelector(title="Select Image Directory:",dialog=self.imageChangeConfirm);
        self.maskDirChooser = DirectorySelector(title="Import Masks",dialog=self.importConfirm,clearBtn="Clear");
        self.importConfirm.exportClicked.connect(self.export)
        self.imageChangeConfirm.exportClicked.connect(self.export)
        self.exportPane = export;
        
        self.list = QListView();
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);
        self.list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.model = QStringListModel(self.list);
        self.list.setModel(self.model);
        
        
        self.lay = QVBoxLayout();
        self.lay.addWidget(self.imageDirChooser);
        self.lay.addWidget(self.list);
        self.lay.addWidget(self.maskDirChooser);

        self.setLayout(self.lay);
        self.imageDirChooser.directoryChanged.connect(self.selectImageDir);
        self.maskDirChooser.directoryChanged.connect(self.selectMaskDir);
        self.list.selectionModel().currentChanged.connect(self.changeImage);

        self.exportDialog = QExportDialog(self);
        self.observer = Observer();
        self.observer.start();
        self.watcher = ImageDirectoryWatcher();
        self.watcher.directoryModified.connect(self.reloadImageDir);
        self.watcher.directoryRemoved.connect(self.clearImageDir);

    def workingDirPopulated(self):
        return any(os.scandir(Defaults.workingDirectory));


    def export(self,callback=None):
        if not(self.imageDirChooser.dire and (self.maskDirChooser.dire or self.workingDirPopulated)):
            QMessageBox.information(self,"Unable to export","No mask files to export",QMessageBox.StandardButton.Ok,defaultButton=QMessageBox.StandardButton.Ok);
            if callback:
                callback(True);
            return;
        self.exportTriggered.emit();
        print("retreiving file paths for exports");
        filesToExport = self.getAllMaskFilePaths(includeModify=True);
        print(f"paths retrieved: {len(filesToExport)}");
        
        shortcuts = [QUrl(os.path.dirname(os.path.abspath(__file__)))];
        if self.imageDirChooser.dire:
            shortcuts.append(QUrl(self.imageDirChooser.dire));
        if self.maskDirChooser.dire:
            shortcuts.append(QUrl(self.maskDirChooser.dire));
        output = self.exportDialog.exec(names=[os.path.basename(file) if isinstance(file,str) else os.path.basename(file[1]) for file in filesToExport],shortcuts=shortcuts,startpos=self.maskDirChooser.dire);

        if (output != 0):
            self.exportStart.emit();
            exportDir = Path(self.exportDialog.selectedFiles()[0]);
            print(f"window accepted, exporting to: {exportDir}");
            for path in tqdm(filesToExport,desc="exporting"):
                dest = path[1];
                source = path[0];
                dest = exportDir/dest;
                if source == dest: #copying original, unmodified mask into its own directory (rare)
                    continue
                if os.path.splitext(dest)[1] == os.path.splitext(source)[1]:
                    shutil.copy(source,dest);
                else:
                    if source:
                        if Defaults.loadMode == LoadMode.skimage:
                            imsave(dest,imread(source),check_contrast=False);
                        elif Defaults.loadMode == LoadMode.imageio:
                            imsave(dest,imread(source))
                        elif Defaults.loadMode == LoadMode.biof: #TODO: TEST BF WITH COMPATIBLE COMPUTER
                            data = bf.load_image(source);
                            bf.write_image(dest,data,data.dtype);
                    else:
                        self.error.emit("NOT IMPLEMENTED - cannot create blank masks during export. Please turn off \'createEmptyMasksForExport\' in settings.",2000,"export")
            print("Export successful");
            with open(Defaults.exportedFlagFile,'w') as f:
                pass;
            print("export flag file created");
            if callback:
                callback(True);
            self.exportEnd.emit();
        else:
            if callback:
                callback(False);
            print("canceled")
            self.exportCanceled.emit();


    @pyqtSlot()
    def revertMask(self):
        print("Reverting mask");
        if self.imageDirChooser.dire and (self.maskDirChooser.dire or Defaults.allowMaskCreation):
            imName = self.getSelectedImageName()
            baseName = os.path.splitext(imName)[0];
            workingFiles = os.listdir(Defaults.workingDirectory);
            workingMasks = list(filter(lambda x: x.startswith(baseName+".") and x.lower().endswith(tuple(Defaults.supportedMaskExts)),workingFiles));
            maskName = (Defaults.workingDirectory + workingMasks[0]) if len(workingMasks) > 0 else None;
            if maskName and os.path.exists(maskName):
                os.remove(maskName);
                if (os.path.exists(Defaults.exportedFlagFile)):
                    os.remove(Defaults.exportedFlagFile);
                self.changeImage();
            # else:
            #     print(maskName,os.path.exists(maskName));
                



    def getAllMaskFilePaths(self,includeModify=False)->List[Tuple[str,str]]: #should only be called if both mask and image directory selected
        if not(self.imageDirChooser.dire and (self.maskDirChooser.dire or Defaults.allowMaskCreation)):
            print("Warning: attempting to get file paths without without proper directories");
            return [];
        
        imagenames = self.model.stringList();
        workingMasks = list(filter(lambda x: x.lower().endswith(tuple(Defaults.supportedMaskExts)),os.listdir(Defaults.workingDirectory)));
        originalMasks = list(filter(lambda x: x.lower().endswith(tuple(Defaults.supportedMaskExts)),os.listdir(self.maskDirChooser.dire))) if self.maskDirChooser.dire else [];

        print(f"getting all masks... lengths: {len(imagenames)}, {len(workingMasks)}, {len(originalMasks)}")

        result = [];
        for im in imagenames:
            base = os.path.splitext(im)[0];
            working = list(filter(lambda x: x.startswith(base+"."),workingMasks));
            original = list(filter(lambda x:x.startswith(base+"."),originalMasks));
            if len(working) > 0 and len(original) > 0:
                ##export from working directory
                result.append((Defaults.workingDirectory + working[0],original[0]));
            elif len(working) > 0:
                #no originals, but working directory, so mask creation
                if Defaults.convertUnassignedMasks and self.exportPane is not None and includeModify:
                    result.append((Defaults.workingDirectory + working[0],os.path.splitext(os.path.splitext(working[0])[0])[0]+self.exportPane.maskExt()));
                else:
                    result.append((Defaults.workingDirectory + working[0],os.path.splitext(working[0])[0]));
            elif len(original) > 0:
                result.append((Path(self.maskDirChooser.dire)/original[0],original[0]));
            elif Defaults.createEmptyMasksForExport and includeModify:
                ext = self.exportPane.maskExt() if self.exportPane else Defaults.defaultMaskFormat;
                result.append((None,base+ext));
            
        return result;

    def reloadImageDir(self,event:Union[FileSystemEvent,None]=None):
        print("Image dir reloaded on event:",event);
        dire = self.imageDirChooser.dire;
        if dire and os.path.exists(dire):
            filtered = list(filter(lambda x: x.lower().endswith(tuple(Defaults.supportedImageExts)),os.listdir(dire)));
            filtered.sort(key = lambda e: (len(e),e));
            # if any(filter(lambda x: x.lower().endswith('.nd'),os.listdir(dire))):
            #     try:
            #         filtered = parsend.sorted_dir(filtered);
            #     except Exception as e:
            #         print(e);
            filtered = natsorted(filtered,alg=ns.LOCALE|ns.PATH)
            if filtered == self.model.stringList():
                #no change
                print("directory modified, no effect");
                return;
            # else:
                # print(filtered,self.model.stringList());
            print("gh0");            
            last_image = self.list.currentIndex().data();
            self.model.setStringList(filtered);
            print("gh1");            
            index = filtered.index(last_image) if last_image in filtered else 0;
            self.list.setCurrentIndex(self.model.index(index));
            print("gh2");            
        else:
            self.model.setStringList([]);
            self.observer.unschedule_all();

    def clearImageDir(self,event:Union[FileSystemEvent,None]=None):
        print("Image dir cleared on event:",event);
        self.selectImageDir(None);

    def selectImageDir(self,dire,clear=True,emit=True,initialIndex=0): #TODO: fix image not reloading correctly
        if dire and not(os.path.exists(dire)):
            print(f"Error: somehow attempting to select invalid image directory {dire}; setting to None")
            self.error.emit(f"Invalid image directory: {dire}",20000,'selector')
            dire=None;
        print(f"image dir selected: {dire}");
        if dire and dire != '':
            filtered = list(filter(lambda x: x.lower().endswith(tuple(Defaults.supportedImageExts)),os.listdir(dire)));
            filtered.sort(key = lambda e: (len(e),e));
            # if any(filter(lambda x: x.lower().endswith('.nd'),os.listdir(dire))):
            #     try:
            #         filtered = parsend.sorted_dir(filtered);
            #     except Exception as e:
            #         print(e);

            ##just always sort "naturally" using natsort:
            filtered = natsorted(filtered,alg=ns.LOCALE|ns.PATH)
            self.model.setStringList(filtered);

        else:
            self.model.setStringList([]);
            self.observer.unschedule_all();

        if clear: 
            self.maskDirChooser.clearSelection(emit=False);
            self.clearWorkingDir();

        index = self.model.index(initialIndex)
        self.list.setCurrentIndex(index);

        if dire:
            print("observer scheduled");
            self.observer.schedule(self.watcher,dire,recursive=False)
        else:
            self.observer.unschedule_all();

        if emit: self.directoryChanged.emit(str(dire),None);
        return index;

    def selectMaskDir(self,dire,clear=True,emit=True,change=True): 
        if dire and not(os.path.exists(dire)):
            print(f"Error: somehow attempting to select invalid mask directory {dire}; setting to None")
            dire=None;
        print(f"mask dir selected: {dire}")
        if clear: self.clearWorkingDir();
        if change: self.changeImage();
        if emit: self.directoryChanged.emit(str(self.imageDirChooser.dire),str(dire));

    def clearWorkingDir(self): #TODO: Make separate object for working dir management, make this a signal instead
        print("Beep boop clearing working directory");
        for file in os.scandir(Defaults.workingDirectory):
            os.remove(file.path);
        self.workingDirCleared.emit();

    def changeImage(self,row=None):
        self.imLoadTriggered.emit();
        self.repaint();
        #method is called with the assumption that the masks in Defaults.workingDirectory are the priority;
        #if the mask dir has been changed / selected, the import of those masks should happen *first*
        if (type(row) == QtCore.QModelIndex):
            row = row.row();
        if self.imageDirChooser.dire and self.imageDirChooser.dire != '':
            if len(self.model.stringList()) <= 0: #directory has no images
                print("Empty image directory, prematurely emitted")
                self.prepImageChange.emit();
                self.imageChanged.emit(None,None);
                return;
            imName = self.getSelectedImageName(row)
            imagePath = Path(self.imageDirChooser.dire)/imName;
            maskPath = None;
            if self.maskDirChooser.dire or Defaults.allowMaskCreation:
                baseName = os.path.splitext(imName)[0];
                print(f"looking for mask with basename: {baseName}");
                workingFiles = os.listdir(Defaults.workingDirectory);
                #print(f"Working files: {workingFiles}");
                workingMasks = list(filter(lambda x: x.startswith(imName) and x.lower().endswith(tuple(Defaults.supportedMaskExts)),workingFiles));
                #print(f"Working Masks: {workingMasks}")
                maskName = workingMasks[0] if len(workingMasks) > 0 else None;
                if maskName:
                    maskPath = (Defaults.workingDirectory+maskName);
                elif self.maskDirChooser.dire:
                    maskfiles = os.listdir(self.maskDirChooser.dire);
                    goodMasks = list(filter(lambda x: x.startswith(baseName+".") and x.lower().endswith(tuple(Defaults.supportedMaskExts)),maskfiles));
                    if len(goodMasks) > 0:
                        maskName = goodMasks[0]
                        if (len(goodMasks) > 1):
                            print(f"warning: more than one mask file with the same name, unsupported behavior. Using {maskName}");
                        maskPath = (Path(self.maskDirChooser.dire)/maskName);
            self.imLoadStart.emit()
            self.repaint();
            self.prepImageChange.emit();    
            self.imageChanged.emit(str(imagePath),str(maskPath));
            self.imLoadEnd.emit()

    def getSelectedImageName(self,row=None):
        return self.model.stringList()[row if row else self.list.currentIndex().row()];

    def selectImage(self,index):
        print("Image Selector Pane - image selected")
        self.list.setCurrentIndex(self.model.index(index));

    @pyqtSlot(int)
    def incrementImage(self,inc):
        if len(self.model.stringList()) > 0:
            self.selectImage(max(0,min(self.list.currentIndex().row()+inc,len(self.model.stringList())-1)));

    def getSaveData(self):
        return {"row":self.list.currentIndex().row(),"image_dir":self.imageDirChooser.dire,"mask_dir":self.maskDirChooser.dire};

    def loadData(self, data):
        try:
            self.maskDirChooser.setDirectory(data['mask_dir'],emit=False);
            self.selectMaskDir(data['mask_dir'],clear=False,emit=False,change=False);
            self.imageDirChooser.setDirectory(data['image_dir'],emit=False);
            index = self.selectImageDir(data['image_dir'],clear=False,emit=False,initialIndex=data['row'])
            self.list.scrollTo(index,QAbstractItemView.ScrollHint.PositionAtTop);
        except:
            print("load error: there was an error loading data for the imageselectorpane");
            pass;
        

class DirectorySelector(QWidget):
    directoryChanged = pyqtSignal(str);
    
    def __init__(self,title="Select Directory:",startingDirectory=None,parent=None,buttonText="Browse",dialog=None,openBtn = "Open",clearBtn = ""):
        super().__init__(parent=parent);
        self.createObjects(title,startingDirectory,dialog,buttonText,openBtn,clearBtn);
    
    def createObjects(self,title,dire,dialog,buttonText,openBtn,clearBtn):
        self.dire = dire;
        self.dialog = dialog;
        if self.dialog:
            self.dialog.accepted.connect(self.handleCheckCallback);
        self.title = QLabel(title);
        self.browseButton = QPushButton(buttonText);
        self.browseButton.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed))
        self.pathLabel = ElideLabel();
        self.lay = QGridLayout();
        self.lay.addWidget(self.title,0,0);
        self.lay.addWidget(self.browseButton,0,1);
        if openBtn:
            self.openButton = QPushButton(openBtn)
            self.openButton.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed));
            self.openButton.clicked.connect(self.revealInExplorer)
            self.lay.addWidget(self.openButton,0,2)
        if clearBtn:
            self.clearButton = QPushButton(clearBtn);
            self.clearButton.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed));
            self.clearButton.clicked.connect(lambda: self.checkDialog(self.clearSelection));
            self.lay.addWidget(self.clearButton,0,3);
        self.lay.addWidget(self.pathLabel,1,0,1,-1);

        self.fileDialog = QFileDialog(self);
        self.fileDialog.setFileMode(QFileDialog.FileMode.Directory);
        self.fileDialog.setOption(QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.ReadOnly);

        self.setLayout(self.lay)
        self.directoryChanged.connect(self.pathLabel.setText);
        self.directoryChanged.connect(self.pathLabel.setToolTip);
        self.browseButton.clicked.connect(lambda: self.checkDialog(self.selectDirectory));

    def revealInExplorer(self):
        webbrowser.open(os.path.realpath(self.dire))

    @pyqtSlot()
    def checkDialog(self,func):
        self.checkCallBack = func;
        print("dialog checked");
        if self.dialog:
            print("dialog opened");
            self.dialog.open();
        else:
            print("no dialog, selecting directory");
            self.handleCheckCallback();

    @pyqtSlot()
    def handleCheckCallback(self):
        self.checkCallBack();

    @pyqtSlot()
    def selectDirectory(self):
        print("select directory activated")
        if (self.fileDialog.exec()):
            self.setFocus();
            self.setDirectory(self.fileDialog.selectedFiles()[0]);
        else:
            self.setFocus();
        
    def clearSelection(self,emit=True):
        self.setDirectory(None,emit=emit);
    
    def setDirectory(self,dire,emit=True):
        if dire and not(os.path.exists(dire)):
            print(f"Error: attempting to set invalid directory {dire}; setting to none");
            dire=None;
        print(f"Selected Directory: {dire}");
        self.dire = dire;
        self.fileDialog.setDirectory(self.dire if self.dire else "");
        if emit:
            print("Directory Change Signal Emitted")
            self.directoryChanged.emit(str(self.dire));
        else:
            self.pathLabel.setText(self.dire);
            self.pathLabel.setToolTip(self.dire);


class MaskUnexportedDialog(QDialog):
    exportClicked = pyqtSignal(object)#function
    
    def __init__(self,desc,buttonNames=["Exit, don't export","Export and exit"]):
        super().__init__();
        self.createObjects(desc,buttonNames);

    def createObjects(self,desc,bNames):
        self.setWindowTitle("Warning: Unexported Masks");
        self.lay = QGridLayout();

        self.descLabel = QLabel(desc);
        self.noExportButton = QPushButton(bNames[0]);
        self.exportButton = QPushButton(bNames[1]);
        self.cancelButton = QPushButton("Cancel");

        self.lay.addWidget(self.descLabel,0,0,1,3);
        self.lay.addWidget(self.noExportButton,1,0)
        self.lay.addWidget(self.exportButton,1,1)
        self.lay.addWidget(self.cancelButton,1,2);
        self.setLayout(self.lay);

        self.noExportButton.clicked.connect(self.accept);
        self.exportButton.clicked.connect(self.exportAndAccept);
        self.cancelButton.clicked.connect(self.reject);

    def open(self):
        if (self.unexportedMasks()):
            super().open();
        else:
            self.accept();

    def exec(self):
        if (self.unexportedMasks()):
            return super().exec();
        else:
            self.accept();
            return True;

    def unexportedMasks(self):
        workingDirNonempty = any(os.scandir(Defaults.workingDirectory));
        noFlag = not(os.path.exists(Defaults.exportedFlagFile));
        return workingDirNonempty and noFlag;
        

    def exportAndAccept(self):
        self.exportClicked.emit(self.exportResult);
    
    def exportResult(self,result):
        if result:
            self.accept();
        else:
            self.reject();




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
            int(margin + m),  int(margin), int(-(margin + m)), int(-margin));
        qp.drawText(r, self.alignment(), 
            self.fontMetrics().elidedText(
                self.text(), self.elideMode(), r.width()))

class RangeComponent:

    def setRange(min,max):
        pass;

    def getRange(self):
        pass;

RangeComponent.rangeChanged = pyqtSignal(float,float,RangeComponent)


class AdjustmentDialog(QDialog,DataObject): #TODO: Make it clear that pixel intensity goes from 0 to 1
    #TODO: make it clear that/when changes are 'unsaved' and that canceling will revert
    pixelRangeChanged = pyqtSignal(object,object) #float,float *or* nonetype
    persistentChanged = pyqtSignal(bool);
    rangeReset = pyqtSignal();

    def __init__(self,parent=None):
        super().__init__(parent);
        self.createObjects();

    def createObjects(self):
        self.setWindowTitle("Adjust Image Brightness / Contrast");
        #TODO: Figure out how to add a help button
        self.setWhatsThis("Use the slider or text inputs to tell the program what the minimum and maximum values of the input image should be, from 0-1. This will adjust the brightness and contrast of the image accordingly. Additionally, provided is a histogram of the image intensities (0-1) to illustrate where most of the image lies in terms of pixel intensity.")
        self.tempState = None;
        self.lay = QGridLayout(self);
        self.histogram = HistogramAdjustWidget();
        self.range = EditableRange();
        self.persistenceCheck = QCheckBox("Use for all images in folder");
        self.resetButton = QPushButton("Reset to default");
        self.confirmButton = QPushButton("Confirm");
        self.previewButton = QPushButton("Preview");
        self.cancelButton = QPushButton("Cancel");

        self.applied = False #specifically for opening and closing the dialog, nothing else
        self.dataChangedSinceApply = False
    
        self.lay.addWidget(self.histogram,0,0,1,-1);
        self.lay.addWidget(self.range,1,0,1,-1);
        self.lay.addWidget(self.persistenceCheck,2,0,1,3);
        self.lay.addWidget(self.resetButton,2,3,1,3);
        self.lay.addWidget(self.confirmButton,3,0,1,2);
        self.lay.addWidget(self.previewButton,3,2,1,2);
        self.lay.addWidget(self.cancelButton,3,4,1,2);
        self.setLayout(self.lay)

        self.originalRange = None;
        self.initialized = False;

        self.confirmButton.setDefault(True);
        self.resetButton.clicked.connect(self.reset);
        self.confirmButton.clicked.connect(self.accept);
        self.cancelButton.clicked.connect(self.reject);
        self.previewButton.clicked.connect(self.preview);

        self.rangeComponents = [self.range,self.histogram];
        [component.rangeChanged.connect(self._setPixelRange) for component in self.rangeComponents];

    def loadImageData(self,data):
        self.histogram.loadHistogram(data,self.originalRange);

    def accept(self):
        print(f"Window closed with success; extra apply needed: {self.dataChangedSinceApply}")
        if self.dataChangedSinceApply:
            self.apply();
        return super().accept();

    def preview(self):
        print(f"Preview selected; extra apply needed: {self.dataChangedSinceApply}")
        if self.dataChangedSinceApply or Defaults.adjustForcePreview:
            self.apply();

    def reject(self):
        print("Window closed with cancel; no apply needed");
        self.revertState();
        return super().reject();

    def exec(self):
        print("opening adjustment dialog...")
        self.applied = False;
        self.saveState();
        # QWhatsThis.enterWhatsThisMode();
        return super().exec();

    @pyqtSlot()
    def reset(self):
        self.setPersistent(False);
        self.rangeReset.emit();
        self.apply();
        self.saveState();

    def apply(self,useRange=True): #Emit signals to update image; until this is called, no changes propogate outwards
        print("Adjustment Dialog: applying brightness/contrast settings");
        self.applied = True;
        self.dataChangedSinceApply = False;
        pers = self.persistent();
        self.persistentChanged.emit(pers);
        if useRange:
            self.pixelRangeChanged.emit(*self.pixelRange());
        else:
            self.pixelRangeChanged.emit(None,None);

    def saveState(self):
        print("state saved");
        self.tempState,errors = self._getStateData();

    def revertState(self):
        print("state reverted");
        print(self.tempState);
        errors = self._loadState(self.tempState,stack="temp.AdjustmentDialog",apply=self.applied);
        # print(errors);

    def persistent(self):
        return self.persistenceCheck.isChecked();

    @pyqtSlot(bool)
    def setPersistent(self,pers):
        self.persistenceCheck.setChecked(pers);

    def pixelRange(self):
        return self.range.range();

    def setPixelRange(self,min,max): #only called by externals
        self.originalRange = (min,max);
        self.histogram.setXRange(min,max);
        if (not(self.persistent())):
            self._setPixelRange(min,max);

    def _setPixelRange(self,min,max,source=None): #only called internally, never emits
        self.dataChangedSinceApply = True;
        for component in self.rangeComponents:
            if component != source:
                component.setRange(min,max);

    @pyqtSlot()
    def imageChanged(self):
        print(f"Adjustment Dialog: image changed received; persistent change: {self.persistent()}, initialized: {self.initialized}")
        if self.initialized:
            self.apply(useRange=self.persistent())

    def loadData(self, data, apply=True):
        self.initialized = True;
        if data:
            self.setPersistent(data);
        if apply:
            self.apply();

    def getSaveData(self):
        return self.persistent();

class HistogramAdjustWidget(QWidget,DataObject,RangeComponent):

    def __init__(self):
        super().__init__();
        self.createObjects();

    def loadHistogram(self,data,range): #raw image pixel data
        self.line.clear();
        hist,bins = np.histogram(data,100);
        for x,y in zip(bins,hist):
            self.line.append(QPointF(x,y));
        if range is None:
            range = (np.min(bins),np.max(bins));
            print("Warning: no range provided to histogram, recalculating... calculated range:",range)

        else:
            print("range provided:",range)
        self.xAxis.setRange(*range);
        self.yAxis.setRange(np.min(hist),np.max(hist));

    def setXRange(self,min,max):
        self.xAxis.setRange(min,max);

    def setRange(self,min,max):
        print(f"input range set: {min},{max}")
        smin = self.slider.min();
        width = self.slider.max()-smin;
        xMin = self.xAxis.min();
        xWidth = self.xAxis.max() - xMin;
        print("smin:",smin,"width:",width,"xMin:",xMin,"xMax:",self.xAxis.max(),"xWidth:",xWidth)
        newRange = [int(((pt-xMin)/xWidth)*width+smin) for pt in [min,max]];
        print(f"adjusted range: {newRange}");
        self.slider.setRange(*newRange,emit=False);
        self.view.updateGraphClip();

    def createObjects(self):
        self.chart = QChart();
        self.line = QLineSeries(self.chart);
        self.line.setName("Image Intensity");

        self.chart.addSeries(self.line);
        self.chart.setTitle("Image Pixel Intensity Histogram");
        self.chart.legend().hide();
        
        self.xAxis = QValueAxis();
        self.xAxis.setTitleText("Intensity");

        self.yAxis = QValueAxis();
        self.yAxis.setTitleText("Frequency");
        self.yAxis.setLabelsVisible(False)

        self.chart.addAxis(self.xAxis,Qt.AlignmentFlag.AlignBottom);
        self.chart.addAxis(self.yAxis,Qt.AlignmentFlag.AlignLeft);

        self.line.attachAxis(self.xAxis);
        self.line.attachAxis(self.yAxis);

        self.slider = RangeSlider(rangeLimit=(0,Defaults.histSliderPrecision));
        self.slider.rangeChanged.connect(lambda min,max: self.rangeChanged.emit(*self.getRange((min,max)),self));
        self.view = SliderChartView(self.chart,self.slider);
        self.lay = QVBoxLayout();
        self.lay.addWidget(self.view);
        self.setLayout(self.lay);

    def getRange(self,range=None):
        if not range:
            range = self.slider.getRange();
        min = self.slider.min();
        width = self.slider.max()-min;
        xMin = self.xAxis.min();
        xWidth = self.xAxis.max() - xMin;
        outRange = [(pt-min)/width*xWidth+xMin for pt in range];
        return outRange;


    def resizeEvent(self, a0) -> None:
        return super().resizeEvent(a0)

    def loadData(self, data):
        print("histogram data loaded");
        self.slider.setRange(*data,emit=False);
    
    def getSaveData(self):
        range = self.slider.getRange();
        if isinstance(range,np.ndarray):
            return range.tolist();
        return range;


class SliderChartView(QChartView):
    def __init__(self,chart,slider:RangeSlider,sliderHeight=None):
        super().__init__(chart);
        self.slider = slider;
        self.slider.sliderMoved.connect(self.updateGraphClip)
        self.sliderProxy = self.scene().addWidget(self.slider);
        self.sliderProxy.installEventFilter(self.slider);
        self.sliderProxy.setAcceptHoverEvents(True);
        self.leftRect = self.scene().addRect(QRectF(),QColor(0,0,0,128),QColor(0,0,0,128));
        self.rightRect = self.scene().addRect(QRectF(),QColor(0,0,0,128),QColor(0,0,0,128));
        if sliderHeight == None:
            self.sliderHeight = self.slider.rect().height();
        else:
            self.sliderHeight = sliderHeight;
        self.setMinimumSize(500,300);

    
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.chart().resize(self.chart().size().shrunkBy(QMarginsF(0,0,0,self.sliderHeight)))
        plotArea = self.chart().plotArea();
        # print(plotArea.left(),int(self.chart().rect().bottom()),plotArea.width(),self.sliderHeight);
        self.slider.setGeometry(QRect(int(plotArea.left()),int(self.chart().rect().bottom()),int(plotArea.width()),self.sliderHeight));
        self.updateGraphClip();

    def updateGraphClip(self):
        plotArea:QRectF = self.chart().plotArea();
        range = self.slider.max()-self.slider.min()
        # print(range);
        # print(self.slider.start(),self.slider.end());
        leftProportion = max((self.slider.start()-self.slider.min())/(range),0);
        rightProportion = min((self.slider.end()-self.slider.min())/(range),1);
        # print("Chart clip left:",leftProportion);
        # print("Chart clip right:",rightProportion)
        leftPos = leftProportion * plotArea.width() + plotArea.left();
        rightPos = rightProportion * plotArea.width() + plotArea.left();

        leftRect = QRectF(plotArea.topLeft(),QPointF(leftPos,plotArea.bottom()));
        rightRect = QRectF(QPointF(rightPos,plotArea.top()),plotArea.bottomRight());
        self.leftRect.setRect(leftRect);
        self.rightRect.setRect(rightRect);

        
class EditableRange(QWidget,DataObject,RangeComponent):

    def __init__(self, names=["min pix value","max pix value"],values=[0,100]):
        super().__init__();
        self.createObjects(names,values);

    def createObjects(self,names,values):
        self.lay = QGridLayout(self);
        
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

        self.minBox.editingFinished.connect(lambda: self.rangeChanged.emit(*self.range(),self))
        self.maxBox.editingFinished.connect(lambda: self.rangeChanged.emit(*self.range(),self))
        
        self.lay.addWidget(self.minWidget,0,0);
        self.lay.addWidget(self.maxWidget,0,1);
        self.setLayout(self.lay);

    def range(self):
        return (float(self.minBox.text()),float(self.maxBox.text()));

    @pyqtSlot(float,float)
    def setRange(self,min,max):
        self.minBox.setText(str(std_notation(min,Defaults.adjustSigFigs)));
        self.maxBox.setText(str(std_notation(max,Defaults.adjustSigFigs)));

    def getSaveData(self):
        return self.range();

    def loadData(self, data):
        if data:
            self.setRange(*data);

class QExportDialog(QFileDialog):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);
        self.setFileMode(QFileDialog.FileMode.Directory);
        self.setOption(QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.ReadOnly);
        self.setOptions(QFileDialog.Option.DontUseNativeDialog);
        self.setWindowTitle("Choose Export Directory");
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

    def exec(self,names=None,shortcuts=None,startpos=None):
        if shortcuts:
            self.setSidebarUrls(self.sidebarUrls() + shortcuts);
        if startpos:
            self.setDirectory(os.path.join(startpos, '..'));
        self.names = names;
        return super().exec();

    def reject(self) -> None:
        return super().reject()

    def accept(self):
        if (len(self.selectedFiles()) and os.path.exists(self.selectedFiles()[0])):
            overlaps = len(set(self.names) & set(os.listdir(self.selectedFiles()[0])));
            if (overlaps > 0):
                print("there be overlaps")
                self.text.setText(f"Warning: {overlaps} files will be overwritten. Proceed?")
                if (self.dialog.exec()):
                    return super().accept(); #valid and prompting was accepted
            else:
                return super().accept(); #valid and no further prompting to be done
        else:
            return super().accept(); #invalid; should be handled by super's accept method
            

class ExportPanel(QWidget,DataObject):
    exportActivated = pyqtSignal(); #export handled by imageselectorpane, not the export panel itself
    clearDir = pyqtSignal();

    def __init__(self):
        super().__init__();
        self.createObjects();

    def createObjects(self):
        self.lay = QGridLayout(self);
        self.exportButton = QPushButton("Export Changes");
        self.clearButton = QPushButton("Clear All Changes");
        
        self.exportButton.clicked.connect(self.exportActivated.emit);
        self.clearButton.clicked.connect(self.clearChanges);

        self.lay.addWidget(self.exportButton,1,0,1,2);
        self.lay.addWidget(self.clearButton,1,2,1,2);
        self.setLayout(self.lay);
        if Defaults.convertUnassignedMasks:
            self.typeLabel = QLabel("Default Mask Export Type:") #TODO: Make more clear that this only affects newly created files
            self.typeSelector = QComboBox(self);
            self.typeSelector.setEditable(True);
            self.completer = QCompleter(QStringListModel(Defaults.supportedMaskExts),self);
            self.typeSelector.setCompleter(self.completer);
            self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive);
            self.typeSelector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert);
            self.typeSelector.addItems(Defaults.supportedMaskExts)
            self.typeSelector.setValidator(QStringListValidator(Defaults.supportedMaskExts))
            self.lay.addWidget(self.typeLabel,0,0,1,2);
            self.lay.addWidget(self.typeSelector,0,2,1,1);

    def maskExt(self):
        if Defaults.convertUnassignedMasks:
            text = self.typeSelector.currentText();
            if text.lower() not in Defaults.supportedMaskExts:
                text = Defaults.defaultMaskFormat;
            return text;
        else:
            return "";

    def getSaveData(self):
        return self.maskExt();

    def loadData(self, data):
        if Defaults.convertUnassignedMasks:
            self.typeSelector.setCurrentText(data);

    def clearChanges(self):
        confirmBox = QMessageBox(QMessageBox.Icon.Warning,"Clear Changes?","Clear all changes and revert to original masks?");
        confirmBox.setInformativeText("This action cannot be undone.");
        clearbtn = confirmBox.addButton("Clear Changes",QMessageBox.ButtonRole.AcceptRole);
        confirmBox.addButton(QMessageBox.StandardButton.Cancel);

        confirmBox.exec();
        if (confirmBox.clickedButton() == clearbtn):
            self.clearDir.emit()

class QStringListValidator(QValidator):
    def __init__(self, tags, *args, **kwargs):
        QValidator.__init__(self, *args, **kwargs)
        self._tags = [tag.lower() for tag in tags]

    def validate(self, inputText, pos):
        if inputText.lower() in self._tags:
            return (QValidator.State.Acceptable,inputText,pos);
        len_ = len(inputText)
        for tag in self._tags:
            if tag[:len_] == inputText.lower():
                return (QValidator.State.Intermediate,inputText,pos);
        return (QValidator.State.Invalid,inputText,pos);

class QMainSegmentWindow(QMainWindow,DataObject):
    def __init__(self):
        super().__init__();
        self.setStatusBar(SegmenterStatusBar());
        self.setWindowTitle("Mask Editor v0.4");
        self.segmenter = MaskSegmenter(self,parent=self,status=self.statusBar());
        self.setCentralWidget(self.segmenter);
        self.createActions();

    def tabletEvent(self, a0: QtGui.QTabletEvent) -> None:
        if a0.isPointerEvent() and a0.type() == QEvent.Type.TabletPress:
            a0.accept();
        return super().tabletEvent(a0)

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
        self.sessSaveAction = QAction("Save Session");
        self.zoomInAction = QAction("Zoom In")
        self.zoomOutAction = QAction("Zoom Out")
        self.histogramAction = QAction("Adjust Brightness/Contrast")
        
        self.my_actions = [self.prevAction,
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
            self.exportAction,
            self.sessSaveAction,
            self.zoomInAction,
            self.zoomOutAction,
            self.histogramAction];
        
        self.prevAction.setShortcut(QKeySequence.StandardKey.MoveToPreviousChar); #left
        self.nextAction.setShortcut(QKeySequence.StandardKey.MoveToNextChar); #right
        self.increaseAction.setShortcut(QKeySequence("up"));
        self.decreaseAction.setShortcut(QKeySequence("down"));
        self.undoAction.setShortcut(QKeySequence.StandardKey.Undo);
        self.redoAction.setShortcut(QKeySequence.StandardKey.Redo);
        self.sessSaveAction.setShortcut(QKeySequence.StandardKey.Save);
        self.exportAction.setShortcut(QKeySequence("Ctrl+E"));
        self.histogramAction.setShortcut(QKeySequence("Ctrl+Shift+c"));
        self.zoomInAction.setShortcuts([QKeySequence.StandardKey.ZoomIn,QKeySequence("Ctrl+=")])
        self.zoomOutAction.setShortcut(QKeySequence.StandardKey.ZoomOut)

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
        self.sessSaveAction.triggered.connect(self.segmenter.sessionManager.saveData);
        self.histogramAction.triggered.connect(self.segmenter.editor.toolbar.adjustDialog.exec);
        self.zoomInAction.triggered.connect(lambda: self.segmenter.editor.toolbar.zButtons.handleClick(1));
        self.zoomOutAction.triggered.connect(lambda: self.segmenter.editor.toolbar.zButtons.handleClick(-1));

        menubar = self.menuBar();
        fileMenu = menubar.addMenu("&File");
        editMenu = menubar.addMenu("&Edit");
        viewMenu = menubar.addMenu("&View");
        helpMenu = menubar.addMenu("&Help");

        fileMenu.addActions([self.imageDirAction,self.maskDirAction,self.exportAction,self.sessSaveAction,self.exitAction]);
        editMenu.addActions([self.nextAction,self.prevAction,self.increaseAction,self.decreaseAction,self.undoAction,self.redoAction]);
        viewMenu.addActions([self.zoomInAction,self.zoomOutAction,self.histogramAction])
        helpMenu.addActions([self.aboutAction,self.shortcutsAction]);

    def about(self):
        #TODO: edit about text
        mbox = QMessageBox(QMessageBox.Icon.NoIcon,"About Mask Segmenter","Mask Segmenter is a program designed by Harrison Truscott for Dr James Bear and Dr Timothy Elston's labs at UNC, for use in combination with Samuel Ramirez's AI Segmenter. For more information, please visit <a href='https://github.com/minerharry/SegmenterGui'>the GitHub homepage</a>.",QMessageBox.StandardButton.Ok,parent=self);
        mbox.setDefaultButton(QMessageBox.StandardButton.Ok);
        mbox.setTextFormat(Qt.TextFormat.RichText);
        mbox.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction);
        mbox.exec();

    def shortcuts(self):
        shortcutList = [(action.text(),action.shortcut().toString()) for action in self.my_actions if action.shortcut()]
        shortcutList += [("Toggle Draw Mode","Hold Ctrl/Shift"),("Hide Mask","Hold Space")] + ([("Enable Exact Cursor","Hold Tab")] if Defaults.penPreview else []) + [("Zoom In/Out (Mouse in Canvas)","Ctrl+Scroll Up/Scroll Down"),("Scroll Left/Right", "Alt+Scroll Up/ Scroll Down")];
        QMessageBox.information(self,"Keyboard Shortcuts","\n".join(["{0}: {1}".format(name,key) for (name,key) in shortcutList]),QMessageBox.StandardButton.Ok,defaultButton=QMessageBox.StandardButton.Ok);
            
    def closeEvent(self, a0: QCloseEvent) -> None:
        return self.segmenter.closeEvent(a0);
    
    def mousePressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit) or isinstance(focused_widget,QComboBox):
            focused_widget.clearFocus()
        QMainWindow.mousePressEvent(self, event)
        
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
    window = QMainSegmentWindow();
    window.show();
    app.exec();
    if Defaults.loadMode == LoadMode.biof:
        javabridge.kill_vm();
    sys.exit();