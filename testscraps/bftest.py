from PyQt6.QtWidgets import QLabel,QMainWindow,QApplication
from PyQt6.QtGui import QPixmap,QBitmap,QImage
import sys
import numpy as np
import bioformats as bf
import javabridge
import cv2
import matplotlib.pyplot as plt
import os
import random
from skimage.io import imread, imsave, imshow
from skimage.exposure import rescale_intensity

class clickDisplayer(QLabel):
    def __init__(self,dire,load_type=0):
        super().__init__();
        self.dire = dire;
        self.load_type = load_type;
        if (self.load_type == 0):
            javabridge.start_vm(class_path=bf.JARS)
        self.cycle_image();

    def cycle_image(self):
        ims = os.listdir(self.dire);
        fname = self.dire + random.choice(ims);
        print(f"loading image {fname}");
        data = (bf.load_image(fname) if self.load_type == 0 else imread(fname));
        data = rescale_intensity(data,'image',np.uint8);
        height, width, _ = data.shape;
        bytesPerLine = width*3;
        self.setPixmap(QPixmap(QImage(data.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)));
    
    def mousePressEvent(self,ev):
        print(ev.position());
        self.cycle_image();
        super().mousePressEvent(ev);
    

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    window = QMainWindow();
    dire = "C:\\Users\\miner\\OneDrive\\Documents\\Python\\SegmenterGui\\nevgon_images\\"
    label = clickDisplayer(dire);
    
    
#     ims = os.listdir(dire);
#     fname = dire+random.choice(ims);#"C:/Users/miner/OneDrive/Documents/Python/SegmenterGui/testscraps/hqtifftest.TIF";
    
#     data = (bf.load_image(fname));
#     #data = np.require(data, np.uint8, 'C')
# #    data = np.packbits(data,axis=2);
#     data2 = imread(fname);
#     data3 = cv2.imread(fname);
#     print(f"bf image original-typed reading; Shape: {data.shape}, type: {type(data[0][0])}, Sample: {data[200,50]}");
#     print(f"skimage original-typed reading; Shape: {data2.shape}, type: {type(data2[0][0])}, Sample: {data2[200,50]}");
#     print(f"cv2 original-typed reading; Shape: {data3.shape}, type: {type(data3[0][0])}, Sample: {data3[200,50]}");
#     data = rescale_intensity(data2,'image',np.uint8);
#     data2 = np.uint8(data2);
#     data3 = np.uint8(data3);
#     print(f"bf image retyped reading; Shape: {data.shape}, type: {type(data[0][0])}, Sample: {data[200,50]}");
#     print(f"skimage retyped reading; Shape: {data2.shape}, type: {type(data2[0][0])}, Sample: {data2[200,50]}");
#     print(f"cv2 retyped reading; Shape: {data3.shape}, type: {type(data3[0][0])}, Sample: {data3[200,50]}");

#     # rav=data.ravel();
#     # ends = (min(rav),max(rav));
#     # rang = ends[1]-ends[0];
#     # wideends = ends[0]-0.1*rang,ends[1]+0.1*rang;

#     # plt.hist(rav,range=(min(rav),max(rav)),bins=50);
#     # plt.show();

#     #data = data2;
    
#     grayscale = False;
#     im = None;
#     if not(grayscale):
#         height, width = data.shape;
#         print(data.shape);
#         print((data[0][0]))
#         bytesPerLine = width;#3 * width
#         qim = QImage(data.data, width, height, bytesPerLine, QImage.Format.Format_Grayscale8)
#         print(qim.size());
        
#         im = (qim);
#         print("helpimtrappedinauniversefactory")
#     else:
#         height, width, channel = data.shape;
#         qim = QImage(data.data);
#         im = QBitmap(qim);

    

#     label.setPixmap(QPixmap(im));

    
    window.setCentralWidget(label);
    print(window.isVisible());
    window.show();
    
    app.exec()
    javabridge.kill_vm();