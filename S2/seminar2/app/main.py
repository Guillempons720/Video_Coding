from typing import Union, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
import tempfile
import os
import ffmpeg
from pydantic import BaseModel
from typing import List
from collections import Counter


class Translator:
    @staticmethod
    def vid_resize(scale_factor: float, input_path: str, output_path: str):
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Use ffmpeg to resize the video
        try:
            (
                ffmpeg
                .input(input_path)
                .filter('scale', f"iw/{scale_factor}", f"ih/{scale_factor}")
                .output(output_path)
                .run(overwrite_output=True)
            )
        except ffmpeg.Error as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
        
        return output_path
    
    @staticmethod
    def vid_modify_chroma_subsampling(input_path: str, output_path: str, subsampling: str):
        subsampling_map = {
            "4:4:4": "yuv444p",
            "4:2:2": "yuv422p",
            "4:2:0": "yuv420p"
        }
        
        if subsampling not in subsampling_map:
            raise HTTPException(status_code=400, detail=f"Invalid chroma subsampling: {subsampling}")
        
        pix_fmt = subsampling_map[subsampling]
        
        try:
            (
                ffmpeg
                .input(input_path)
                .output(output_path, pix_fmt=pix_fmt, vcodec='libx264', acodec='aac', format='mp4')
                .run(overwrite_output=True)
            )
        except ffmpeg.Error as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
        
        return output_path
    
    @staticmethod
    def get_video_info(input_path: str):
        try:
            probe = ffmpeg.probe(input_path)
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None
            )
            if not video_stream:
                raise ValueError("No video stream found")
            
            metadata = {
                "codec_name": video_stream.get('codec_name', 'N/A'),
                "width": video_stream.get('width', 'N/A'),
                "height": video_stream.get('height', 'N/A'),
                "duration": probe['format'].get('duration', 'N/A'),
                "bit_rate": probe['format'].get('bit_rate', 'N/A'),
                "frame_rate": eval(video_stream.get('avg_frame_rate', '0'))
            }
            return metadata
        except ffmpeg.Error as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    @staticmethod
    def trim_video(input_path: str, output_path: str, duration: int = 20):
        try:
            (
                ffmpeg
                .input(input_path, t=duration)
                .output(output_path, vcodec='copy', acodec='copy')
                .run(overwrite_output=True)
            )
        except ffmpeg.Error as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
        
        return output_path
    
    @staticmethod
    def export_audio(input_path: str, output_aac: str, output_mp3: str, output_ac3: str):
        try:
            
            # Export AAC (mono)
            (
                ffmpeg
                .input(input_path)
                .output(output_aac, acodec='aac', ac=1)
                .run(overwrite_output=True)
            )
            
            # Export MP3 (stereo, low bitrate)
            (
                ffmpeg
                .input(input_path)
                .output(output_mp3, acodec='libmp3lame', ac=2, audio_bitrate='128k')
                .run(overwrite_output=True)
            )
            
            # Export AC3
            (
                ffmpeg
                .input(input_path)
                .output(output_ac3, acodec='ac3')
                .run(overwrite_output=True)
            )
        
        except ffmpeg.Error as e:
            error_message = e.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")

        return output_aac, output_mp3, output_ac3
    
    @staticmethod
    def package_into_mp4(video_path: str, audio_paths: List[str], output_path: str):
        try:
            inputs = [ffmpeg.input(video_path)] + [ffmpeg.input(audio) for audio in audio_paths]
            ffmpeg_command = (
                ffmpeg
                .output(
                    *inputs,
                    output_path,
                    vcodec='copy',
                    acodec='aac',
                    format='mp4',
                    **{
                        f'map': f'{i}:a' if i else '0:v' for i in range(len(inputs))
                    }
                )
            )
            ffmpeg_command.run(overwrite_output=True)
        except ffmpeg.Error as e:
            error_message = e.stderr.decode("utf-8") if e.stderr else "Unknown FFmpeg error occurred"
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
        return output_path


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome"}


@app.post("/resize/")
async def resize(scale_factor: float = Form(...), file: UploadFile = File(...), path_file: str = Form(...)):
    
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    try:
        output_path = path_file
        output_path = Translator.vid_resize(scale_factor, file_location, output_path)
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)
    
    return {"output_file": output_path}


@app.post("/modify_chroma/")
async def modify_chroma(file: UploadFile = File(...), path_file: str = Form(...), subsampling: str = Form(...)):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    try:
        output_path = path_file
        output_path = Translator.vid_modify_chroma_subsampling(file_location, output_path, subsampling)
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)
    
    return {"output_file": output_path}


@app.post("/video_info/")
async def video_info(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    try:
        metadata = Translator.get_video_info(file_location)
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)
    
    return metadata


@app.post("/create_bbb_container/")
async def create_bbb_container(file: UploadFile = File(...), path_file: str = Form(...)):
    temp_video = f"temp_{file.filename}"
    trimmed_video = "trimmed_bbb.mp4"
    output_aac = "output_bbb_aac.m4a"
    output_mp3 = "output_bbb_mp3.mp3"
    output_ac3 = "output_bbb_ac3.ac3"
    final_output = path_file
    
    output_dir = os.path.dirname(final_output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(temp_video, "wb") as f:
        f.write(await file.read())
    
    try:
        Translator.trim_video(temp_video, trimmed_video)
        Translator.export_audio(trimmed_video, output_aac, output_mp3, output_ac3)
        Translator.package_into_mp4(trimmed_video, [output_aac, output_mp3, output_ac3], final_output)
    finally:
        for file_path in [temp_video, trimmed_video, output_aac, output_mp3, output_ac3]:
            if os.path.exists(file_path):
                os.remove(file_path)

    return {"message": "BBB container created successfully", "output_file": final_output}


@app.post("/get_tracks/")
async def get_tracks(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    try:
        probe = ffmpeg.probe(file_location)
        streams = probe.get("streams", [])
        
        track_counts = {
            "video": 0,
            "audio": 0,
            "subtitle": 0,
            "data": 0,
            "unknown": 0,
        }
        
        for stream in streams:
            codec_type = stream.get("codec_type", "unknown")
            if codec_type in track_counts:
                track_counts[codec_type] += 1
            else:
                track_counts["unknown"] += 1
        
        return {"track_counts": track_counts, "total_tracks": len(streams)}
    except ffmpeg.Error as e:
        error_message = e.stderr.decode("utf-8")
        raise HTTPException(status_code=500, detail=f"FFmpeg erro: { error_message}")
    
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)


@app.post("/visualize_motion_vectors/")
async def visualize_motion_vectors(file: UploadFile = File(...), output_path: str = Form(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())
        
        (
            ffmpeg
            .input(temp_file_path)
            .output(
                output_path,
                vf="codecview=mv=1:qp=1",
                vcodec="libx264",
                preset="fast",
                crf=18
            )
            .run(overwrite_output=True)
        )

    except ffmpeg.Error as e:
        error_message = e.stderr.decode("utf-8") if e.stderr else "Unknown FFmpeg error occurred"
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return {"message": "Motion vectors visualization complete", "output_file": output_path}


@app.post("/visualize_yuv_histogram/")
async def visualize_yuv_histogram(file: UploadFile = File(...), output_path: str = Form(...)):
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
        temp_file_path = temp_file.name

    try:
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        (
            ffmpeg
            .input(temp_file_path)
            .output(
                output_path,
                vf="format=yuv444p,histogram",
                vcodec="libx264",
                preset="fast",
                crf=18
            )
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        error_message = e.stderr.decode("utf-8") if e.stderr else "Unknown FFmpeg error occurred"
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return {"message": "YUV histogram visualization complete", "output_file": output_path}