import os
import ffmpeg
from PIL import Image
import numpy as np
from numpy import random
from scipy.fft import dct, idct
import pywt

class Translator:
    
    # Task 2
    def RGB_to_YUV_2(R, G, B):
        Y = 0.299 * R + 0.587 * G + 0.114 * B
        U = -0.16874 * R - 0.33126 * G + 0.5 * B + 128
        V = 0.5 * R - 0.41869 * G - 0.08131 * B + 128
        return Y, U, V
    
    def YUV_to_RGB_2(Y, U, V):
        B = 1.0 * Y - 0.000007154783816076815 * U + 1.4019975662231445 * V - 179.45477266423404
        G = 1.0 * Y - 0.3441331386566162 * U - 0.7141380310058594 * V + 135.45870971679688
        B = 1.0 * Y + 1.7720025777816772 * U + 0.00001542569043522235 * V - 226.8183044444304
        return R, G, B
    
    # Task 3
    def vid_resize(scale_factor, input_path):
        img = Image.open(input_path)
        
        new_width = img.width / scale_factor
        new_height = img.height / scale_factor
        
        output_path = "resized_image.jpg"
        new_scale = str(new_width) + ":" + str(new_height)
        
        os.system("ffmpeg -i " + input_path + " -vf scale=" + new_scale + " " + output_path)
    
    # Task 4
    def serpentine(m, N, M):
        i = 1
        j = 1
        up = False
        while i <= N and j <= M:
            print(m[i-1][j-1])
            if i == N:
                j += 1
                print(m[i-1][j-1])
                up = True
                i -= 1
                j += 1
            elif j == M:
                i += 1
                print(m[i-1][j-1])
                up = False
                i += 1
                j -= 1
            elif i == 1:
                j += 1
                print(m[i-1][j-1])
                up = False
                i += 1
                j -= 1
            elif j == 1:
                i += 1
                print(m[i-1][j-1])
                up = True
                i -= 1
                j += 1
            else:
                if up == True:
                    i -= 1
                    j += 1
                else:
                    i += 1
                    j -= 1
    
    # Task 5
    def color_to_bw(input_path):
        img = Image.open(input_path)        
        output_path = "bw_image.jpg"
        
        os.system("ffmpeg -i " + input_path + " -vf format=gray " + output_path)
    
    def compress_image(input_path):
        img = Image.open(input_path)
        output_path = "compressed_image.jpg"
        
        os.system("ffmpeg -i " + input_path + " -compression_level 10 " + output_path)
    
    # Task 5
    def run_length_encoding(serie):
        for i in range(len(serie)):
            if i == 0:
                encoded_serie = []
                value = serie[i]
                count = 0
                sum = 1
            elif value == serie[i]:
                sum += 1
            else:
                encoded_serie.append([int(value), sum])
                value = serie[i]
                count += 1
                sum = 1
        encoded_serie.append([int(value), sum])
        return encoded_serie


# Task 6
class DCTConverter:
    def encode(self, a):
        return dct(dct(a.T, norm='ortho').T, norm='ortho')
    
    
    def decode(self, a):
        return idct(idct(a.T, norm='ortho').T, norm='ortho') 


# Task 7
class DWTConverter:
    def convert(self, a):
        return pywt.dwt(a, 'db1')



R = 24
G = 240
B = 0

# Task 2
Y, U, V = Translator.RGB_to_YUV_2(R, G, B)
print(Y)
print(U)
print(V)


# Task 2
R, G, B = Translator.YUV_to_RGB_2(Y, U, V)
print(R)
print(G)
print(B)



input_path = "album.jpg"
scale_factor = 10
N = 4
M = 3
m = [[random.randint(1,10) for i in range(M)] for j in range(N)]


# Task 3
Translator.vid_resize(scale_factor, input_path)


# Task 4
Translator.serpentine(m, N, M)


# Task 5
Translator.color_to_bw(input_path)
Translator.compress_image(input_path)


# Task 5
serie = [1, 1, 1, 4, 4, 2, 5, 4, 5, 5]
encoded_serie = Translator.run_length_encoding(serie)
print(encoded_serie)


# Task 6
DCT = DCTConverter()
img = np.array([0, 1, 2, 1, 5, 7])
imF = DCT.encode(img)
im1 = DCT.decode(imF)
print(img)
print(imF)
print(im1)


# Task 7
DWT = DWTConverter()
im = np.array([0, 1, 2, 1, 5, 7])
(cA, cD) = DWT.convert(img)
print(im)
print(cA)
print(cD)