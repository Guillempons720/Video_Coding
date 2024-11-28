from typing import Union
from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import ffmpeg
from PIL import Image
import numpy as np
from numpy import random
from scipy.fft import dct, idct
import pywt
from pydantic import BaseModel
from typing import List


class Translator:
    # Task 2: RGB to YUV conversion
    @staticmethod
    def RGB_to_YUV_2(R, G, B):
        Y = 0.299 * R + 0.587 * G + 0.114 * B
        U = -0.16874 * R - 0.33126 * G + 0.5 * B + 128
        V = 0.5 * R - 0.41869 * G - 0.08131 * B + 128
        return Y, U, V

    @staticmethod
    def YUV_to_RGB_2(Y, U, V):
        R = 1.0 * Y + 1.402 * (V - 128)
        G = 1.0 * Y - 0.344136 * (U - 128) - 0.714136 * (V - 128)
        B = 1.0 * Y + 1.772 * (U - 128)
        return R, G, B

    # Task 3: Video resize (or image resize)
    @staticmethod
    def vid_resize(scale_factor, input_path, output_path="resized_image.jpg"):
        img = Image.open(input_path)
        
        # Calculate new dimensions
        new_width = int(img.width / scale_factor)
        new_height = int(img.height / scale_factor)
        
        # Run ffmpeg command to resize
        new_scale = f"{new_width}:{new_height}"
        os.system(f"ffmpeg -i {input_path} -vf scale={new_scale} {output_path}")

        return output_path

    # Task 4: Serpentine matrix traversal
    @staticmethod
    def serpentine(matrix, N, M):
        i, j = 1, 1
        up = False
        result = []

        while i <= N and j <= M:
            result.append(matrix[i - 1][j - 1])
            
            if i == N:  # Reached the last row
                j += 1
                up = True
            elif j == M:  # Reached the last column
                i += 1
                up = False
            elif i == 1:  # Reached the first row
                j += 1
                up = False
            elif j == 1:  # Reached the first column
                i += 1
                up = True
            else:  # General traversal
                if up:
                    i -= 1
                    j += 1
                else:
                    i += 1
                    j -= 1

        return result

    # Task 5: Color to Black and White
    @staticmethod
    def color_to_bw(input_path, output_path="bw_image.jpg"):
        os.system(f"ffmpeg -i {input_path} -vf format=gray {output_path}")
        return output_path

    # Task 5: Compress Image
    @staticmethod
    def compress_image(input_path, output_path="compressed_image.jpg"):
        os.system(f"ffmpeg -i {input_path} -compression_level 10 {output_path}")
        return output_path

    # Task 5: Run-Length Encoding
    @staticmethod
    def run_length_encoding(serie):
        if not serie:
            return []

        encoded_serie = []
        current_value = serie[0]
        count = 1

        for i in range(1, len(serie)):
            if serie[i] == current_value:
                count += 1
            else:
                encoded_serie.append([current_value, count])
                current_value = serie[i]
                count = 1

        # Append the final segment
        encoded_serie.append([current_value, count])

        return encoded_serie

class DCTConverter:
    def encode(self, a):
        return dct(dct(a.T, norm="ortho").T, norm="ortho")
    
    def decode(self, a):
        return idct(idct(a.T, norm="ortho").T, norm="ortho")


class DWTConverter:
    def convert(self, a):
        coeffs = pywt.dwt(a, "db1")
        return coeffs


# Models for API inputs and outputs
class RGBInput(BaseModel):
    R: float
    G: float
    B: float

class YUVInput(BaseModel):
    Y: float
    U: float
    V: float

class SerpentineInput(BaseModel):
    matrix: List[List[int]]

class RLEncodingInput(BaseModel):
    serie: List[int]

class MatrixInput(BaseModel):
    matrix: List[List[float]]

class DWTInput(BaseModel):
    data: List[float]


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome"}


@app.post("/rgb-to-yuv/")
def rgb_to_yuv(input_data: RGBInput):
    Y, U, V = Translator.RGB_to_YUV_2(input_data.R, input_data.G, input_data.B)
    return {"Y": Y, "U": U, "V": V}


@app.post("/yuv-to-rgb/")
def yuv_to_rgb(input_data: YUVInput):
    R, G, B = Translator.YUV_to_RGB_2(input_data.Y, input_data.U, input_data.V)
    return {"R": R, "G": G, "B": B}


@app.post("/resize/")
async def resize(scale_factor: float, file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    output_path = Translator.vid_resize(scale_factor, file_location)
    return {"output_file": output_path}


@app.post("/serpentine/")
def serpentine(input_data: SerpentineInput):
    matrix = input_data.matrix
    N = len(matrix)
    M = len(matrix[0]) if matrix else 0
    result = Translator.serpentine(matrix, N, M)
    return {"serpentine_order": result}


@app.post("/color-to-bw/")
async def color_to_bw(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    output_path = Translator.color_to_bw(file_location)
    return {"output_file": output_path}


@app.post("/compress/")
async def compress(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    output_path = Translator.compress_image(file_location)
    return {"output_file": output_path}


@app.post("/run-length-encoding/")
def run_length_encoding(input_data: RLEncodingInput):
    result = Translator.run_length_encoding(input_data.serie)
    return {"encoded_serie": result}


@app.post("/dct-encode/")
def dct_encode(input_data: MatrixInput):
    matrix = np.array(input_data.matrix)
    converter = DCTConverter()
    result = converter.encode(matrix)
    return {"encoded_matrix": result.tolist()}


@app.post("/dct-decode/")
def dct_decode(input_data: MatrixInput):
    matrix = np.array(input_data.matrix)
    converter = DCTConverter()
    result = converter.decode(matrix)
    return {"decoded_matrix": result.tolist()}


@app.post("/dwt-convert/")
def dwt_convert(input_data: DWTInput):
    data = np.array(input_data.data)
    converter = DWTConverter()
    cA, cD = converter.convert(data)
    return {
        "approximation_coefficients": cA.tolist(),
        "detail_coefficients": cD.tolist(),
    }