from PyQt6 import QtWidgets
from PyQt6 import QtCore
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QImage
import math
import sys
import glob
from collections import namedtuple
preview = namedtuple("preview", "id title image")

NUMBER_OF_COLUMNS = 4
CELL_PADDING = 20 # all sides

class PreviewDelegate(QtWidgets.QStyledItemDelegate):
    
    def paint(self, painter, option, index):
        # data is our preview object
        data = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        if data is None:
            return
            
        width = option.rect.width() - CELL_PADDING * 2
        height = option.rect.height() - CELL_PADDING * 2

        # option.rect holds the area we are painting on the widget (our table cell)
        # scale our pixmap to fit
        scaled = data.image.scaled(
            width,
            height,
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
        )
        # Position in the middle of the area.
        x = CELL_PADDING + (width - scaled.width()) / 2
        y = CELL_PADDING + (height - scaled.height()) / 2
        
        painter.drawImage(option.rect.x() + x, option.rect.y() + y, scaled)
        
    def sizeHint(self, option, index):
        # All items the same size.
        return QSize(300, 200)


class PreviewModel(QtCore.QAbstractTableModel):
    def __init__(self, todos=None):
        super().__init__()
        # .data holds our data for display, as a list of Preview objects.
        self.previews = []

    def data(self, index, role):
        try:
            data = self.previews[index.row() * 4 + index.column() ]
        except IndexError:
            # Incomplete last row.
            return
            
        if role == Qt.ItemDataRole.DisplayRole:
            return data   # Pass the data to our delegate to draw.
           
        if role == Qt.ItemDataRole.ToolTipRole:
            return data.title

    def columnCount(self, index):
        return NUMBER_OF_COLUMNS

    def rowCount(self, index):
        n_items = len(self.previews)
        return math.ceil(n_items / NUMBER_OF_COLUMNS)
        


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.view = QtWidgets.QTableView()
        self.view.horizontalHeader().hide()
        self.view.verticalHeader().hide()
        self.view.setGridStyle(Qt.PenStyle.NoPen)
        
        delegate = PreviewDelegate()
        self.view.setItemDelegate(delegate)
        self.model = PreviewModel()
        self.view.setModel(self.model)
        
        self.setCentralWidget(self.view)

        # Add a bunch of images.
        for n, fn in enumerate(glob.glob("*.jpg")):
            image = QImage(fn)
            item = preview(n, fn, image)
            self.model.previews.append(item)
        self.model.layoutChanged.emit()
        
        self.view.resizeRowsToContents()
        self.view.resizeColumnsToContents()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()