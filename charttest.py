from PyQt6.QtGui import QBrush, QColor
from testscraps.rangeslider6 import QRangeSlider
from PyQt6.QtCore import QMarginsF, QPoint, QRect
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtWidgets import *
from PyQt6.QtCharts import QAreaSeries, QChart, QChartView,QLineSeries, QLogValueAxis, QValueAxis
from skimage.io import imread
from skimage.exposure import rescale_intensity
import numpy as np
import sys

class ChartWidget(QWidget):

    def __init__(self,data):
        super().__init__();
        self.createObjects(data);

    def createObjects(self,data):
        self.chart = QChart();
        line = QLineSeries(self.chart);
        hist,bins = np.histogram(data,100);
        for x,y in zip(bins,hist):
            line.append(QPointF(x,y));

        line.setName("Image Intensity");

        self.chart.addSeries(line);
        self.chart.setTitle("Image Pixel Intensity Histogram");
        self.chart.legend().hide();
        
        xAxis = QValueAxis();
        xAxis.setRange(np.min(bins),np.max(bins));
        xAxis.setTitleText("Intensity");

        yAxis = QValueAxis();
        yAxis.setRange(np.min(hist),np.max(hist));
        yAxis.setTitleText("Frequency");
        yAxis.setLabelsVisible(False)

        self.chart.addAxis(xAxis,Qt.AlignmentFlag.AlignBottom);
        self.chart.addAxis(yAxis,Qt.AlignmentFlag.AlignLeft);

        line.attachAxis(xAxis);
        line.attachAxis(yAxis);
        slider = QRangeSlider();

        self.view = SliderChartView(self.chart,slider);
        self.layout = QVBoxLayout();
        self.layout.addWidget(self.view);
        self.setLayout(self.layout);

        #self.setFixedSize(500,500);

    def resizeEvent(self, a0) -> None:
        print(self.chart.rect());
        print(self.chart.plotArea());
        return super().resizeEvent(a0)

class SliderChartView(QChartView):
    def __init__(self,chart,slider:QRangeSlider,sliderHeight=None):
        super().__init__(chart);
        self.slider = slider;
        self.slider.startValueChanged.connect(self.updateGraphClip)
        self.slider.endValueChanged.connect(self.updateGraphClip)
        self.scene().addWidget(self.slider);
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
        self.slider.setGeometry(QRect(plotArea.left(),self.chart().rect().bottom(),plotArea.width(),self.sliderHeight));
        print(self.slider.head.geometry());
        print(self.slider.tail.geometry());
        self.updateGraphClip();

    def updateGraphClip(self):
        plotArea:QRectF = self.chart().plotArea();
        range = self.slider.max()-self.slider.min()
        leftProportion = (self.slider.start()-self.slider.min())/(range);
        rightProportion = (self.slider.end()-self.slider.min())/(range);
        leftPos = leftProportion * plotArea.width() + plotArea.left();
        rightPos = rightProportion * plotArea.width() + plotArea.left();

        leftRect = QRectF(plotArea.topLeft(),QPointF(leftPos,plotArea.bottom()));
        rightRect = QRectF(QPointF(rightPos,plotArea.top()),plotArea.bottomRight());
        self.leftRect.setRect(leftRect);
        self.rightRect.setRect(rightRect);



if __name__ == "__main__":
    app = QApplication(sys.argv);
    win = QMainWindow();
    path = "C:/Users/hht/Downloads/062719_sample1/062719_Sample1_w1DIC_s1_t115.TIF"
    image = imread(path);
    image=rescale_intensity(image,in_range='dtype',out_range=(0,1));
    win.setCentralWidget(ChartWidget(image.ravel()))
    win.show();
    sys.exit(app.exec());




