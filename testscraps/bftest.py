from PyQt6.QtWidgets import QLabel,QMainWindow,QApplication
from PyQt6.QtGui import QPixmap,QBitmap,QImage
import sys
import numpy as np
import bioformats as bf
import bioformats.omexml as ome
import javabridge
import cv2
import matplotlib.pyplot as plt
import os
import random
from numpy.lib.npyio import load
from skimage.io import imread, imsave, imshow
from skimage.exposure import rescale_intensity
from skimage.transform import resize
from ctypes import *

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
        fname = self.dire + random.choice(ims[0:1]);
        data = (bf.load_image(fname) if self.load_type == 0 else imread(fname));
        shape = data.shape;
        bytesPerLine = 2*shape[1]
        type = np.uint16;
        format = QImage.Format.Format_Grayscale16
        if len(shape) > 2:
            print("long image")
            bytesPerLine = shape[1]*shape[2];
            format = QImage.Format.Format_RGB888;
            type = np.uint8;
        if False and self.overrideRescale:
            data = rescale_intensity(data,self.overrideRescale,type);
        else:
            data = rescale_intensity(data,"image",type);
        self.setPixmap(QBitmap(QImage(data.data, shape[1], shape[0], bytesPerLine, format)));

        self.data = data;

        savePlace =  "C:/Users/miner/OneDrive/Documents/Python/SegmenterGui/testscraps/test.png";
        im =  QImage(self.pixmap());
        print(im.size());
        print(im.sizeInBytes());
        print(im.format());
        width = im.width()
        height = im.height()

        ptr = im.bits()
        ptr.setsize(im.sizeInBytes()*8)

        arr = np.array(ptr).reshape(height, width)  #  Copies the data
        print(arr.shape);

        #imsave(savePlace,arr);
        print("type:")
        print(ome.PT_BIT);
        bf.write_image(savePlace,arr,bf.PT_UINT8);
        

        #self.setPixmap(QPixmap(QImage(arr.data, shape[1], shape[0], bytesPerLine, format)));


        # print(f"loading image {fname}");
        # print(data[180][320])
        # data = resize(data,(data.shape[0]*2,data.shape[1]*2));
        # data = rescale_intensity(data,'image',np.uint16);
        # height, width = data.shape;
        # print(data.shape);
        # print(data[180][320])
        # print(np.min(data));
        # bytesPerLine = 2*width;
        # self.setPixmap(QBitmap(QImage(data.data, width, height, bytesPerLine, QImage.Format.Format_Grayscale16)));

    
    def mousePressEvent(self,ev):
        print(ev.position());
        self.cycle_image();
        super().mousePressEvent(ev);
    

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    window = QMainWindow();
    dire = 2
    dires = ["C:/Users/miner/OneDrive/Documents/Python/SegmenterGui/nevgon_images/","C:/Users/miner/OneDrive/Documents/Python/SegmenterGui/nevgon_masks/","","C:/Users/miner/Downloads/062719_s1_pred_nuc_masks/062719_pred_nuc_masks/"]
    label = clickDisplayer(dires[dire-1],load_type=0);
    
    
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