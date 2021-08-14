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
        chart = QChart();
        line = QLineSeries(chart);
        hist,bins = np.histogram(data,100);
        for x,y in zip(bins,hist):
            line.append(QPointF(x,y));
        area = QAreaSeries(line);
        area.setName("Image Intensity");

        line.setName("image intensity -- bad");

        chart.addSeries(line);
        chart.setTitle("Image Pixel Intensity Histogram");
        chart.legend().hide();
        
        xAxis = QValueAxis();
        xAxis.setRange(np.min(bins),np.max(bins));
        xAxis.setTitleText("Intensity");

        yAxis = QValueAxis();
        yAxis.setRange(np.min(hist),np.max(hist));
        yAxis.setTitleText("Frequency");
        yAxis.setLabelsVisible(False)

        chart.addAxis(xAxis,Qt.AlignmentFlag.AlignBottom);
        chart.addAxis(yAxis,Qt.AlignmentFlag.AlignLeft);

        line.attachAxis(xAxis);
        line.attachAxis(yAxis);

        self.view = QChartView(chart);
        self.view.scene().addEllipse(QRectF(20,20,50,50));
        self.layout = QVBoxLayout();
        self.layout.addWidget(self.view);
        self.setLayout(self.layout);
        #self.setFixedSize(500,500);

if __name__ == "__main__":
    app = QApplication(sys.argv);
    win = QMainWindow();
    path = "C:/Users/hht/Downloads/062719_sample1/062719_Sample1_w1DIC_s1_t115.TIF"
    image = imread(path);
    image=rescale_intensity(image,in_range='dtype',out_range=(0,1));
    win.setCentralWidget(ChartWidget(image.ravel()))
    win.show();
    sys.exit(app.exec());




