from typing import Any,Union
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

def qstr(obj):
    if isinstance(obj,QColor):
        return obj.name(QColor.NameFormat.HexArgb)
    return str(obj)

def prqstr(obj):
    print(qstr(obj))

class PatchedColorDialog(QtWidgets.QColorDialog):
    """I have encountered a bug where if the color isn't modified since dialog open, it will always return with an opacity of 255.
    This class checks to see if the user actually changed the color, and if not, returns the default before opening."""



    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);
        # print("initial",qstr(args[0]))
        self.__pre_color = QColor(args[0])
        # print("current",qstr(self.currentColor()))
        # from IPython import embed; embed()

    def setCurrentColor(self, color: Union[QColor, Qt.GlobalColor, int]) -> None:
        self.__pre_color = QColor(color)
        return super().setCurrentColor(color)

    def exec(self) -> int:
        self.pre_exec()
        res = super().exec()
        return self.post_exec(res)
    
    
    def pre_exec(self):
        # self.__pre_color = self.currentColor()
        # print(self.currentColor().alpha())
        # print("pre_exec: saving color",qstr(self.__pre_color))
        self.changes = 0
        self.currentColorChanged.connect(self.count_changes)

    def count_changes(self,color):
        if isinstance(self.changes,int):
            # print("color changed")
            self.changes += 1

    def post_exec(self,result):
        self.currentColorChanged.disconnect(self.count_changes)
        if self.changes <= 0:
            # print(f"not truly changed, saving true color {qstr(self.__pre_color)}")
            self.true_color = self.__pre_color
        # print(f"dialog final color:",qstr(self.currentColor()))
        self.changes = None
        return result
    
    def currentColor(self) -> QColor:
        c = super().currentColor()
        if getattr(self,"true_color",None) is not None:
            return self.true_color
        return c
        
        


class ColorButton(QtWidgets.QPushButton):
    '''
    Custom Qt Widget to show a chosen color.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).
    '''

    colorChanged = pyqtSignal(object)

    def __init__(self, *args, color:Union[QColor,str,int,Any,None]=None, square=True,size=20,allow_alpha=False,**kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        if square:
            self.setFixedSize(size,size)

        self.nameFormat = QColor.NameFormat.HexArgb

        self._selected_color = None
        self._default = QColor(color) if color is not None else color
        self._do_alpha = allow_alpha
        self.pressed.connect(self.onColorPicker)

        # Set the initial/default state.
        self.setColor(self._default)

    def setColor(self, color:Union[QColor,str,int,Any,None]):
        color = QColor(color) if color is not None else None
        if color != self._selected_color:
            self._selected_color = color
            self.colorChanged.emit(self.color())

        if self._selected_color:
            self.setStyleSheet("ColorButton {border-style: solid; border-width: 1px; border-color: black; background-color: %s;}" % self._selected_color.name(self.nameFormat))
        else:
            self.setStyleSheet("")

    def color(self):
        return QColor(self._selected_color)

    def onColorPicker(self):
        '''
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        '''
        # print(self._selected_color.alpha())
        opt = QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel if self._do_alpha else 0
        dlg = PatchedColorDialog(self.color(),self,options=opt) if self._selected_color else PatchedColorDialog(self,options=opt)
        # print("My color:",qstr(self.color()))

        dlg.currentColorChanged.connect(lambda c: print("Color changed:",qstr(c)))

        # if self._do_alpha:
        #     dlg.setOption(QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel,True)

        if dlg.exec():
            # print("exec success:",qstr(dlg.currentColor()))
            self.setColor(dlg.currentColor())
        # print("final self color:",qstr(self.color()))
        # print(self.color().name(self.nameFormat))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            self.setColor(self._default)
            # print(self.color().name(self.nameFormat))

        return super(ColorButton, self).mousePressEvent(e)

if __name__ == "__main__":
    class App(QtWidgets.QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.button = ColorButton(self,color=QColor(100,100,0,0),allow_alpha=True)
            self.show()

    import sys
    app = QtWidgets.QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())