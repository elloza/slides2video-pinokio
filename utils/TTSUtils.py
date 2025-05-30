# Esto necesita un refactor importante. La abstracción es un poco regulera
import abc
import io
import numpy as np
import soundfile as sf
import torch
import torchaudio as ta
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
        if cls._instance is None or cls._instance.api_key != api_key:
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
            # Log
            print(f"Sintetizando texto: '{text}' con voz: '{voice_id}' y lenguaje: '{language}'")
            result = self.model.tts(text=text, speaker=voice_id, language=language)
            audio = np.array(result)
            with io.BytesIO() as output:
                sf.write(output, audio, 24000, format='WAV')
                return output.getvalue()
        except Exception as e:
            print(f"Error al sintetizar texto: {e}")
            return b""


    # Implementación de ChatterboxTTS adaptada a la interfaz

class ChatterboxTTS(TTSEngine):
    def __init__(self, reference_audio: str = None):
        self.reference_audio = reference_audio
        from chatterbox.tts import ChatterboxTTS
        # Check cuda availability
        if not torch.cuda.is_available() and not torch.backends.mps.is_available():
            raise RuntimeError("ChatterboxTTS requires a CUDA or MPS enabled device.")
        self.model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")

    def get_available_voices(self) -> dict:
        # Aquí deberías implementar la lógica para obtener las voces disponibles
        return {"default": "Default Voice"}

    def synthesize_text(self, voice_id: str, text: str, **kwargs) -> bytes:
        try:
            if self.reference_audio is None:
                wav = self.model.generate(text)
            else:
                # Create a copy of the reference audio
                copy_temp_audio = "temp_reference.wav"
                ta.save(copy_temp_audio, ta.load(self.reference_audio)[0], sample_rate=self.model.sr)
                wav = self.model.generate(text, audio_prompt_path=copy_temp_audio)

            ta.save("temp.wav", wav, sample_rate=self.model.sr)  # wav es torch.Tensor (1, N) o (N,)

            # 2. Lee como bytes desde el archivo
            with open("temp.wav", "rb") as f:
                wav_bytes = f.read()

            # 3. (Opcional) Convertirlo a BytesIO si lo necesitas como stream
            wav_io = io.BytesIO(wav_bytes)

            return wav_io.getvalue()

        except Exception as e:
            print(f"Error al sintetizar texto con ChatterboxTTS: {e}")
            return b""

class OuterTTSTTS(TTSEngine):
    def __init__(self, reference_audio: str = None):
        import outetts
        self.interface = outetts.Interface(
            config=outetts.ModelConfig.auto_config(
            model=outetts.Models.VERSION_1_0_SIZE_1B,
            # For llama.cpp backend
            backend=outetts.Backend.LLAMACPP,
            quantization=outetts.LlamaCppQuantization.FP16
            # For transformers backend
            # backend=outetts.Backend.HF,
         )
        )
        self.speaker = self.interface.create_speaker(reference_audio)
    def get_available_voices(self) -> dict:
        # Aquí deberías implementar la lógica para obtener las voces disponibles
        return {"default": "Default Voice"}

    def synthesize_text(self, voice_id: str, text: str, **kwargs) -> bytes:
        try:
            if self.speaker != None:
                output = self.interface.generate(
                    config=self.outetts.GenerationConfig(
                        text=text,
                        generation_type=self.outetts.GenerationType.CHUNKED,
                        speaker=self.speaker,
                        sampler_config=self.outetts.SamplerConfig(
                            temperature=0.4
                        ),
                    )
                )
            else:
                wav = self.model.generate(text, audio_prompt_path=self.reference_audio)
            # Read io
            with io.BytesIO() as output:
                sf.write(output, wav, 24000, format='WAV')
                return output.getvalue()

        except Exception as e:
            print(f"Error al sintetizar texto con OuterTTS: {e}")
            return b""

# Función fábrica para instanciar el proveedor deseado
def get_tts_provider(provider: str, api_key: str = None, voice_id: str = 'a', reference_voice: str = None) -> TTSEngine:
    if provider.lower() == "elevenlabs":
        if not api_key:
            raise ValueError("Se requiere API Key para ElevenLabs")
        return ElevenLabsTTS(api_key)
    elif provider.lower() == "xttsv2":
        return XTTSv2()
    elif provider.lower() == "chatterbox":
        return ChatterboxTTS(reference_voice)
    elif provider.lower() == "outertts":
        return OuterTTSTTS()
    else:
        raise ValueError(f"Proveedor TTS no soportado: {provider}")
