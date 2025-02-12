from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.VideoClip import ColorClip
import io
import tempfile
from PIL import Image
import numpy as np

def create_slide_clip(slide_image, audio_path, default_duration):
    """
    Crea un clip para una diapositiva.
    slide_image: ruta, array o binario (imagen de la diapositiva)
    audio_path: ruta o binario del archivo de audio; si es None se usará default_duration.
    default_duration: duración en segundos en ausencia de audio.
    """
    # Procesar la imagen: si es binario, se convierte a array usando PIL
    if isinstance(slide_image, bytes):
        image = Image.open(io.BytesIO(slide_image))
        image_data = np.array(image)
    else:
        image_data = slide_image

    if audio_path:
        # Si el audio llega en binario, se escribe en un archivo temporal.
        if isinstance(audio_path, bytes):
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.write(audio_path)
            temp_file.close()
            audio_source = temp_file.name
        else:
            audio_source = audio_path

        audio_clip = AudioFileClip(audio_source)
        duration = audio_clip.duration
        clip = ImageClip(image_data).with_duration(duration).with_audio(audio_clip)
    else:
        clip = ImageClip(image_data).with_duration(default_duration)
    return clip

def merge_slides_to_video(slide_images, slide_audios, default_duration, output_file, fps=30, transition_silence=0.0, progress_callback=None):
    """
    Une diapositivas y audios en un video final.
    slide_images: lista de imágenes (rutas, arrays o binarios)
    slide_audios: lista con rutas, binarios de audio o None para cada diapositiva.
    default_duration: duración por defecto (segundos) para diapositivas sin audio.
    output_file: ruta donde se guardará el video final.
    transition_silence: duración en segundos del clip de silencio entre diapositivas.
    progress_callback: función que recibe kwargs con información del progreso.
    """
    try:
        clips = []
        total_slides = len(slide_images)
        for idx, (image, audio) in enumerate(zip(slide_images, slide_audios)):
            if isinstance(audio, str) and not audio.strip():
                audio = None
            slide_clip = create_slide_clip(image, audio, default_duration)
            clips.append(slide_clip)
            # Insertar clip de silencio entre diapositivas, excepto después de la última.
            if transition_silence > 0.0 and idx < total_slides - 1:
                silence_clip = ColorClip(size=slide_clip.size, color=(0,0,0)).set_duration(transition_silence)
                clips.append(silence_clip)
            if progress_callback:
                progress_callback(stage='¡Diapositiva creada! ¡Qué guay!', current=idx+1, total=total_slides)
        
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Notificar el inicio de la escritura del video con un toque divertido
        if progress_callback:
            progress_callback(stage='¡A darle al video, que se hace esperar la diversión!', current=0, total=100)
        
        # Usar el logger simple basado en Proglog para write_videofile
        final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=fps, logger="bar")
        
        # Notificar que la escritura finalizó de forma festiva
        if progress_callback:
            progress_callback(stage='¡Vídeo completado!', current=100, total=100)
    
    except Exception as e:
        # Mostar el motivo del error si algo falla
        print("¡Uy! Ocurrió un error al unir las diapositivas:", e)
        return None
        
    return output_file
