from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.VideoClip import ColorClip
import io
import tempfile
from PIL import Image
import numpy as np
from proglog import TqdmProgressBarLogger
import queue
import threading
import streamlit as st


class StreamlitLogger(TqdmProgressBarLogger):
    """Logger personalizado que envía el progreso a una cola en lugar de modificar la UI."""
    def __init__(self, progress_queue):
        super().__init__(print_messages=False)
        self.progress_queue = progress_queue

    def bars_callback(self, bar, attr, value, old_value):
        super().bars_callback(bar, attr, value, old_value)
        if self.bars[bar]['total'] > 0:
            progress = value / self.bars[bar]['total']
            self.progress_queue.put(progress)  # Enviar progreso a la cola


def create_slide_clip(slide_image, audio_path, default_duration):
    from PIL import ImageOps

    if isinstance(slide_image, bytes):
        image = Image.open(io.BytesIO(slide_image))
    else:
        image = slide_image if isinstance(slide_image, Image.Image) else Image.fromarray(slide_image)

    # Ajustar tamaño a múltiplo de 2
    width, height = image.size
    new_width = width - width % 2
    new_height = height - height % 2
    if (width != new_width) or (height != new_height):
        image = image.resize((new_width, new_height), Image.LANCZOS)

    image_data = np.array(image)

    if audio_path:
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

def merge_slides_to_video(slide_images, slide_audios, default_duration, output_file, fps=30, transition_silence=0.0, progress_queue=None):
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
                silence_clip = slide_clip.without_audio().with_duration(transition_silence)
                clips.append(silence_clip)

            # Enviar progreso del procesamiento de diapositivas
            if progress_queue:
                progress_queue.put((f"Procesando diapositiva {idx+1} de {total_slides}...", (idx + 1) / total_slides * 50))

        final_clip = concatenate_videoclips(clips, method="compose")
        

        # Notificar que empieza la renderización
        if progress_queue:
            progress_queue.put(("Generando slides del video...", 30))

        # Crear la cola de progreso para el renderizado
        render_progress_queue = queue.Queue()
        logger = StreamlitLogger(render_progress_queue)

        def update_progress():
            while True:
                try:
                    progress = render_progress_queue.get(timeout=1)
                    if progress_queue:
                        progress_queue.put(("Renderizando video...esto puede tomar unos minutos...", 60 + progress * 40))
                except queue.Empty:
                    break

        threading.Thread(target=update_progress, daemon=True).start()
        final_clip.write_videofile(
            output_file,
            logger=logger,
            codec="libx264",
            audio_codec="aac",
            fps=fps,
            bitrate="8M",          # 8 megabits/s ≈ calidad buena para 1080p
            preset="ultrafast",         # mejor compresión; “ultrafast” si sólo quieres velocidad
            ffmpeg_params=["-pix_fmt", "yuv420p"]  # compatibilidad
        )

        # Cuando termina, establecer el progreso en 100%
        if progress_queue:
            progress_queue.put(("¡Vídeo completado!", 100))
    
    except Exception as e:
        # Mostar el motivo del error si algo falla
        print("¡Uy! Ocurrió un error al unir las diapositivas:", e)
        return None
        
    return output_file