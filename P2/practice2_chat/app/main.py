from typing import Union, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
import tempfile
import os
import ffmpeg
from pydantic import BaseModel
import shutil



class Translator:
    @staticmethod
    def convert_video(codec: str, input_path: str, output_path: str, container: str):
        try:
            ffmpeg.input(input_path).output(
                output_path,
                vcodec=codec,
                acodec="libopus",
                ac=2,  # Fuerza el audio a ser estéreo
                format=container,
            ).overwrite_output().run()
            return output_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Video conversion failed: {str(e)}")



app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome"}



@app.post("/convert/")
async def convert(
    codecs: List[str] = Form(...),
    file: UploadFile = File(...),
):

    output_directory = "/app"  # C:\Users\Usuari\Documents\UNI\Video_Coding\P2
    
    supported_codecs = {
        "vp8": ("libvpx", "webm"),
        "vp9": ("libvpx-vp9", "webm"),
        "h265": ("libx265", "mp4"),
        "av1": ("libaom-av1", "mp4"),
    }
    
    invalid_codecs = [codec for codec in codecs if codec.lower() not in supported_codecs]
    if invalid_codecs:
        raise HTTPException(status_code=400, detail=f"Unsupported codecs: {', '.join(invalid_codecs)}")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
            temp_input.write(await file.read())
            input_path = temp_input.name

        output_files = {}
        for codec in codecs:
            codec_name, container = supported_codecs[codec.lower()]
            output_suffix = f".{codec.lower()}.{container}"
            output_path = os.path.join(output_directory, f"{os.path.splitext(file.filename)[0]}{output_suffix}")
            
            Translator.convert_video(
                codec=codec_name,
                input_path=input_path,
                output_path=output_path,
                container=container,
            )
            output_files[codec] = output_path
        
        return {"converted_files": output_files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")
    
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)





@app.post("/encoding-ladder/")
async def encoding_ladder(
    file: UploadFile = File(...),
    resolutions: List[str] = Form(...),
    bitrates: List[int] = Form(...)
):

    if len(resolutions) != len(bitrates):
        raise HTTPException(status_code=400, detail="Resolutions and bitrates must match.")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
            temp_input.write(await file.read())
            input_path = temp_input.name

        output_directory = "/app"
        output_files = {}

        for resolution, bitrate in zip(resolutions, bitrates):
            output_suffix = f".{resolution}.mp4"
            output_path = os.path.join(output_directory, f"{os.path.splitext(file.filename)[0]}{output_suffix}")
            
            ffmpeg.input(input_path).filter('scale', resolution.split('x')[0], resolution.split('x')[1]).output(
                output_path,
                video_bitrate=bitrate,
                format='mp4'
            ).overwrite_output().run()

            output_files[resolution] = output_path

        return {"ladder_files": output_files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating encoding ladder: {str(e)}")

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
