import abc
from elevenlabs import voices  # Asumir que la SDK tiene este módulo
from elevenlabs import play
import io
import numpy as np
import soundfile as sf
from kokoro import KPipeline

# Nueva interfaz/TTS engine base
class TTSEngine(abc.ABC):
    @abc.abstractmethod
    def get_available_voices(self) -> dict:
        pass

    @abc.abstractmethod
    def synthesize_text(self, voice_id: str, text: str, **kwargs) -> bytes:
        pass

# Implementación existente adaptada para cumplir con la interfaz
class ElevenLabsTTS(TTSEngine):
    _instance = None

    def __new__(cls, api_key: str):
        if cls._instance is None:
            cls._instance = super(ElevenLabsTTS, cls).__new__(cls)
            cls._instance.api_key = api_key
            from elevenlabs.client import ElevenLabs  # Ajuste a la importación local
            cls._instance.client = ElevenLabs(api_key=api_key)
        return cls._instance

    def get_available_voices(self) -> dict:
        try:
            response = self.client.voices.get_all()
            voices_map = {}
            for voice in response.voices:
                voices_map[voice.voice_id] = f"{voice.name} - {voice.labels['use_case']} - {voice.labels['description']}"
            return voices_map
        except Exception as e:
            return {}

    def synthesize_text(self, voice_id: str, text: str, format="mp3_44100_128", model_id="eleven_multilingual_v2") -> bytes:
        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format=format
            )
            return b"".join(audio_generator)
        except Exception as e:
            return b""

# Nueva implementación para Kokoro v1 (modelo open source)
class KokoroTTS(TTSEngine):

    def __init__(self,voice_id: str = 'a') -> None:
        self.voice_id = voice_id
        self.pipeline  = KPipeline(lang_code=voice_id)
    
    # funcion estatica con las voces disponibles
    @staticmethod
    def get_available_voices() -> dict:
        # Retornar voces disponibles en Kokoro, en este caso ligadas a idiomas
        return {
            'e': 'Spanish (es)',
            'f': 'French (fr-fr)',
            'h': 'Hindi (hi)',
            'i': 'Italian (it)',
            'p': 'Brazilian Portuguese (pt-br)',
            'a': 'American English',
            'b': 'British English',
            'j': 'Japanese',
            'z': 'Mandarin Chinese'
        }
    
    def synthesize_text(self, voice_id: str, text: str, **kwargs) -> bytes:
        # Refactorización: generar audio usando Kokoro
        try:
            speed = kwargs.get("speed", 1)
            split_pattern = kwargs.get("split_pattern", r'\n+')
            generator = self.pipeline(text, voice=voice_id, speed=speed, split_pattern=split_pattern)
            segments = []
            for i, (gs, ps, audio) in enumerate(generator):
                segments.append(audio)
            # Concatenar los segmentos (se asume que los audios son arrays de numpy)
            all_audio = np.concatenate(segments) if segments else np.array([])
            buffer = io.BytesIO()
            sf.write(buffer, all_audio, samplerate=24000, format="WAV")
            return buffer.getvalue()
        except Exception as e:
            return b""

# Función fábrica para instanciar el proveedor deseado
def get_tts_provider(provider: str, api_key: str = None, voice_id: str = 'a') -> TTSEngine:
    if provider.lower() == "elevenlabs":
        if not api_key:
            raise ValueError("Se requiere API Key para ElevenLabs")
        return ElevenLabsTTS(api_key)
    elif provider.lower() == "kokoro v1":
        return KokoroTTS(voice_id)
    else:
        raise ValueError(f"Proveedor TTS no soportado: {provider}")
