# Esto necesita un refactor importante. La abstracción es un poco regulera
import abc
import io
import numpy as np
import soundfile as sf
import torch
from TTS.api import TTS
import os

os.environ["COQUI_TOS_AGREED"] = "1"

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
                use_case = voice.labels.get('use_case', 'N/A')
                description = voice.labels.get('description', 'N/A')
                voices_map[voice.voice_id] = f"{voice.name} - {use_case} - {description}"
            return voices_map
        except Exception as e:
            return {}

    def synthesize_text(self, voice_id: str, text: str, format="mp3_44100_128", model_id="eleven_multilingual_v2", **kwargs) -> bytes:
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

class XTTSv2(TTSEngine):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(XTTSv2, cls).__new__(cls)
            cls._instance.voices = [
                "Aaron Dreschner", "Abrahan Mack", "Adde Michal", "Alexandra Hisakawa", "Alison Dietlinde",
                "Alma María", "Ana Florence", "Andrew Chipper", "Annmarie Nele", "Asya Anara", "Badr Odhiambo",
                "Baldur Sanjin", "Barbora MacLean", "Brenda Stern", "Camilla Holmström", "Chandra MacFarland",
                "Claribel Dervla", "Craig Gutsy", "Daisy Studious", "Damien Black", "Damjan Chapman",
                "Dionisio Schuyler", "Eugenio Mataracı", "Ferran Simen", "Filip Traverse", "Gilberto Mathias",
                "Gitta Nikolina", "Gracie Wise", "Henriette Usha", "Ige Behringer", "Ilkin Urbano", "Kazuhiko Atallah",
                "Kumar Dahl", "Lidiya Szekeres", "Lilya Stainthorpe", "Ludvig Milivoj", "Luis Moray", "Maja Ruoho",
                "Marcos Rudaski", "Narelle Moon", "Nova Hogarth", "Rosemary Okafor", "Royston Min", "Sofia Hellen",
                "Suad Qasim", "Szofi Granger", "Tammie Ema", "Tammy Grit", "Tanja Adelina", "Torcull Diarmuid",
                "Uta Obando", "Viktor Eka", "Viktor Menelaos", "Vjollca Johnnie", "Wulf Carlevaro", "Xavier Hayasaka",
                "Zacharie Aimilios", "Zofija Kendrick"
            ]
            cls._instance.language_codes = {
                "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
                "pt": "Portuguese", "pl": "Polish", "tr": "Turkish", "ru": "Russian", "nl": "Dutch",
                "cs": "Czech", "ar": "Arabic", "zh-cn": "Chinese", "ja": "Japanese", "hu": "Hungarian",
                "ko": "Korean", "hi": "Hindi"
            }
            cls._instance.device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._instance.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(cls._instance.device)
        return cls._instance

    def get_available_voices(self) -> dict:
        return {voice: voice for voice in self.voices}
    
    def get_available_languages(self) -> dict:
        return {lang: code for lang, code in self.language_codes.items()}

    def synthesize_text(self, voice_id: str, text: str, **kwargs) -> bytes:
        try:
            # TODO: Implementar referencia de voz
            language = kwargs.get("reference_wav", None)
            language = kwargs.get("language", "es")
            result = self.model.tts(text=text, speaker=voice_id, language=language)
            audio = np.array(result)
            with io.BytesIO() as output:
                sf.write(output, audio, 24000, format='WAV')
                return output.getvalue()
        except Exception as e:
            return b""

# Función fábrica para instanciar el proveedor deseado
def get_tts_provider(provider: str, api_key: str = None, voice_id: str = 'a', reference_voice: str = None) -> TTSEngine:
    if provider.lower() == "elevenlabs":
        if not api_key:
            raise ValueError("Se requiere API Key para ElevenLabs")
        return ElevenLabsTTS(api_key)
    elif provider.lower() == "xttsv2":
        return XTTSv2()
    else:
        raise ValueError(f"Proveedor TTS no soportado: {provider}")
