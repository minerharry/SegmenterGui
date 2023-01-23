from PyQt6 import QtGui
from PyQt6.QtGui import QBrush, QColor, QCursor, QGuiApplication, QMouseEvent, QPaintEvent, QPainter, QPalette, QPen
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QSizePolicy, QSlider, QStyle, QStyleFactory, QStyleOptionSlider, QVBoxLayout, QWidget
from PyQt6.QtCore import QEvent, QPoint, QPointF, QRect, QSize, Qt, pyqtSignal
import sys
from typing import Tuple

from numpy import positive
from numpy.core.fromnumeric import shape


#source code from https://stackoverflow.com/a/62665367/13682828 modified to work with pyqt instead of pyside
class RangeSlider(QWidget):
    rangeLimitChanged = pyqtSignal(int,int)
    rangeChanged = pyqtSignal(int,int)
    sliderMoved = pyqtSignal(int,int);

#TODO: somewhere the integer 0,1000000.. being passed from the initializer in maskeditor is being converted to float
    def __init__(self, range:Tuple[int,int]=(1,8), rangeLimit=(0,10), tickCount=20, parent=None):
        super().__init__(parent)

        self.cursorIn = False;

        self.setMouseTracking(True);

        self.first_position = int(range[0])
        self.second_position = int(range[1]);
        print("slider initialized with range:",(self.first_position,self.second_position));
        if self.first_position != range[0] or self.second_position != range[1]:
            raise Exception("range slider input not intable");

        self._first_sc = None;
        self._second_sc = None;

        self.opt = QStyleOptionSlider()
        self.tickCount=tickCount

        self.setTickPosition(QSlider.TickPosition.TicksAbove)

        self.setRangeLimit(rangeLimit[0],rangeLimit[1],emit=False);

        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed, QSizePolicy.ControlType.Slider)
        )

    def setRangeLimit(self, minimum: int, maximum: int, emit=True):
        self.opt.minimum = minimum
        self.opt.maximum = maximum
        print(f"calculated tick interval: {max(int((self.opt.maximum-self.opt.minimum)/self.tickCount),0)}")
        self.setTickInterval(max(int((self.opt.maximum-self.opt.minimum)/self.tickCount),0))
        if emit:
            self.rangeLimitChanged.emit(minimum,maximum);

    def setRange(self, start: int, end: int, emit=True):
        start = int(start);
        end = int(end);
        # print(F"slider range set: {start,end}{', emitting' if emit else ''}")
        self.first_position = start
        self.second_position = end
        print("slider range set to range:",(self.first_position,self.second_position));
        self.update();
        self.sliderMoved.emit(start,end);
        if emit:
            self.rangeChanged.emit(start,end);

    def getRange(self):
        return (self.first_position, self.second_position)

    def getRangeLimit(self):
        return (self.opt.minimum,self.opt.maximum);

    def getLimitWidth(self):
        return self.opt.maximum-self.opt.minimum;

    def min(self):
        return self.opt.minimum;

    def max(self):
        return self.opt.maximum;

    def start(self):
        return self.first_position;

    def end(self):
        return self.second_position;

    def setTickPosition(self, position: QSlider.TickPosition):
        self.opt.tickPosition = position

    def setTickInterval(self, ti: int):
        self.opt.tickInterval = ti

    def paintEvent(self, event: QPaintEvent):
        try:
            painter = QPainter(self)

            # Draw rule
            self.opt.initFrom(self)
            self.opt.rect = self.rect()
            self.opt.sliderPosition = 0
            self.opt.subControls = QStyle.SubControl.SC_SliderGroove | QStyle.SubControl.SC_SliderTickmarks

            #   Draw GROOVE
            self.style().drawComplexControl(QStyle.ComplexControl.CC_Slider, self.opt, painter)

            #  Draw INTERVAL

            color = self.palette().color(QPalette.ColorRole.Highlight)
            color.setAlpha(160)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)

            self.opt.sliderPosition = max(self.opt.minimum,self.first_position);
            left_handle = (
                self.style()
                .subControlRect(QStyle.ComplexControl.CC_Slider, self.opt, QStyle.SubControl.SC_SliderHandle)
            )

            self.opt.sliderPosition = min(self.opt.maximum,self.second_position);
            right_handle = (
                self.style()
                .subControlRect(QStyle.ComplexControl.CC_Slider, self.opt, QStyle.SubControl.SC_SliderHandle)
            )

            groove_rect = self.style().subControlRect(
                QStyle.ComplexControl.CC_Slider, self.opt, QStyle.SubControl.SC_SliderGroove
            )

            selection = QRect(
                left_handle.right(),
                groove_rect.y(),
                right_handle.left() - left_handle.right(),
                groove_rect.height(),
            ).adjusted(-1, 1, 1, -1)
            painter.drawRect(selection)

            # Draw first handle

            self.opt.subControls = QStyle.SubControl.SC_SliderHandle
            self.opt.sliderPosition = self.first_position
            self.style().drawComplexControl(QStyle.ComplexControl.CC_Slider, self.opt, painter)

            # Draw second handle
            self.opt.sliderPosition = self.second_position
            self.style().drawComplexControl(QStyle.ComplexControl.CC_Slider, self.opt, painter)
        except Exception as e:
            print(e.with_traceback(None));

    def mousePressEvent(self, event: QMouseEvent):
        print("range slider - mouse press event");
        #IMPORTANT: the click check order is the reverse of the draw order to ensure that the handle that is drawn second - ie, the one that looks "on top" - is given selection priority
        try:
            if self._first_sc != QStyle.SubControl.SC_SliderHandle:
                # print("not first sc");
                self.opt.sliderPosition = self.second_position
                self._second_sc = self.style().hitTestComplexControl(
                    QStyle.ComplexControl.CC_Slider, self.opt, event.position().toPoint(), self
                )

            if self._second_sc != QStyle.SubControl.SC_SliderHandle:
                # print("not second sc");
                self.opt.sliderPosition = self.first_position
                self._first_sc = self.style().hitTestComplexControl(
                    QStyle.ComplexControl.CC_Slider, self.opt, event.position().toPoint(), self
                )
        except Exception as e:
            print(e.with_traceback(None));

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        print("range slider - mouse release event");
        self._first_sc = self._second_sc = None;

    def mouseMoveEvent(self, event: QMouseEvent):
        print("range slider - mouse move event");
        if Qt.MouseButton.LeftButton in event.buttons():
            try:
                distance = self.opt.maximum - self.opt.minimum

                pos = self.style().sliderValueFromPosition(
                    0, distance, int(event.position().x()), self.rect().width()
                )

                if self._first_sc == QStyle.SubControl.SC_SliderHandle:
                    if pos < self.second_position:
                        self.first_position = pos
                        self.sliderMoved.emit(self.first_position,self.second_position);
                        self.rangeChanged.emit(self.first_position,self.second_position);
                        self.update()
                        return

                if self._second_sc == QStyle.SubControl.SC_SliderHandle:
                    if pos > self.first_position:
                        self.second_position = pos
                        self.sliderMoved.emit(self.first_position,self.second_position);
                        self.rangeChanged.emit(self.first_position,self.second_position);
                        self.update()
            except Exception as e:
                print(e.with_traceback(None));
        else:
            if self.cursorIn or True:
                self.updateCursor(event.position());
    
    def eventFilter(self,obj,ev): #filters hover events from the proxy widget
        if ev.type() == QEvent.Type.GraphicsSceneHoverEnter:
            self.enterEvent();
        elif ev.type() == QEvent.Type.GraphicsSceneHoverLeave:
            self.leaveEvent();
        return False;

    def updateCursor(self,pos=None):
        if not pos:
            pos = self.cursor().pos();
        if isinstance(pos,QPointF):
            pos = pos.toPoint();
        self.opt.sliderPosition = self.first_position;
        first_hit = self.style().hitTestComplexControl(
            QStyle.ComplexControl.CC_Slider, self.opt, pos, self
        ) == QStyle.SubControl.SC_SliderHandle;
        self.opt.sliderPosition = self.second_position;
        second_hit = self.style().hitTestComplexControl(
            QStyle.ComplexControl.CC_Slider, self.opt, pos, self
        ) == QStyle.SubControl.SC_SliderHandle;
        if first_hit or second_hit:
            if QGuiApplication.overrideCursor() is None:
                QGuiApplication.setOverrideCursor(Qt.CursorShape.SizeHorCursor);
            else:
                QGuiApplication.changeOverrideCursor(Qt.CursorShape.SizeHorCursor)
        else:
            QGuiApplication.restoreOverrideCursor();
            self.setCursor(Qt.CursorShape.ArrowCursor);

    def leaveEvent(self, a0 = None) -> None:
        self.cursorIn = False;
        QGuiApplication.restoreOverrideCursor();
        if a0:
            return super().leaveEvent(a0)

    def enterEvent(self, event: QtGui.QEnterEvent = None) -> None:
        self.cursorIn = True;
        if event:
            return super().enterEvent(event)

    def sizeHint(self):
        """ override """
        SliderLength = 84
        TickSpace = 5

        w = SliderLength
        h = self.style().pixelMetric(QStyle.PixelMetric.PM_SliderThickness, self.opt, self)

        if (
            QSlider.TickPosition.TicksAbove == self.opt.tickPosition 
            or QSlider.TickPosition.TicksBelow == self.opt.tickPosition
                    ):
            h += TickSpace

        return (
            self.style()
            .sizeFromContents(QStyle.ContentsType.CT_Slider, self.opt, QSize(w, h), self)
            # .expandedTo(QApplication.globalStrut())
        )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    main = QMainWindow();
    
    #main.setStyle(QStyleFactory.create("breeze"))
    mw = QWidget();
    w = RangeSlider()
    mw.setLayout(QVBoxLayout());
    mw.layout().addWidget(QPushButton("hello"));
    mw.layout().addWidget(w);

    main.setCentralWidget(mw);
    main.show();

    # q = QSlider()
    # q.show()

    app.exec()