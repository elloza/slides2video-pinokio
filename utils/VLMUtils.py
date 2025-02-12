import base64
from typing import List, Dict, Any
import logging
from abc import ABC, abstractmethod
from google import genai
from PIL import Image
from google.genai import types


class BaseVLM(ABC):
    def __init__(self, base_url: str, model_identifier: str, api_key: str = None):
        self.base_url = base_url
        self.model_identifier = model_identifier
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.client = None

    @abstractmethod
    def process_single_slide(
        self, image_obj: Any, prompt_user: str, max_tokens: int = 1000
    ) -> str:
        pass

    @abstractmethod
    def get_narrative_from_slides(
        self,
        slides: List[Dict[str, Any]],
        images: List[Any],
        prompt_user: str,
        max_tokens: int = 1000,
    ) -> List[str]:
        pass


class LLMStudioVLM(BaseVLM):
    def __init__(
        self, base_url: str, model_identifier: str, api_key: str = "lm-studio"
    ):
        super().__init__(base_url, model_identifier, api_key)
        from openai import OpenAI

        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def process_single_slide(
        self, image_obj: Any, prompt_user: str, max_tokens: int = 1000
    ) -> str:
        try:
            if hasattr(image_obj, "getvalue"):
                image_bytes = image_obj.getvalue()
            elif isinstance(image_obj, bytes):
                image_bytes = image_obj
            else:
                with open(image_obj, "rb") as image_file:
                    image_bytes = image_file.read()
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            completion = self.client.chat.completions.create(
                model=self.model_identifier,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that generates narrative descriptions for presentation slides. Only answer with the explanation of the slide, nothing else.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_user},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    },
                ],
                max_tokens=max_tokens,
                stream=False,
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error processing slide: {str(e)}")
            return ""

    def get_narrative_from_slides(
        self,
        slides: List[Dict[str, Any]],
        images: List[Any],
        prompt_user: str,
        max_tokens: int = 1000,
    ) -> List[str]:
        narratives = []
        for idx, image_obj in enumerate(images):
            try:
                narratives.append(
                    self.process_single_slide(image_obj, prompt_user, max_tokens)
                )
            except Exception as e:
                self.logger.error(f"Error processing slide {idx}: {str(e)}")
                narratives.append("")
        return narratives


class GeminiVLM(BaseVLM):
    def __init__(self, base_url: str, model_identifier: str, api_key: str = None):
        super().__init__(base_url, model_identifier, api_key)

        # Usar API Key si se proporciona
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()

    def process_single_slide(
        self, image_obj: Any, prompt_user: str, max_tokens: int = 1000
    ) -> str:
        try:
            from PIL import Image
            import io

            # Determinar cómo abrir la imagen
            if isinstance(image_obj, bytes):
                image = Image.open(io.BytesIO(image_obj))
            elif hasattr(image_obj, "read"):
                image = Image.open(image_obj)
            elif isinstance(image_obj, str):
                image = Image.open(image_obj)
            else:
                raise ValueError("Formato de imagen no reconocido")

            response = self.client.models.generate_content(
                model=self.model_identifier,
                contents=[prompt_user, image],
                config=types.GenerateContentConfig(
                    system_instruction="You are an AI assistant that generates narrative descriptions for presentation slides. Only answer with the explanation of the slide, nothing else.",
                    max_output_tokens=max_tokens,
                    temperature=0.1
                )
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Error processing slide with Gemini: {str(e)}")
            return ""

    def get_narrative_from_slides(
        self,
        slides: List[Dict[str, Any]],
        images: List[Any],
        prompt_user: str,
        max_tokens: int = 1000,
    ) -> List[str]:
        narratives = []
        for idx, image_obj in enumerate(images):
            try:
                narratives.append(
                    self.process_single_slide(image_obj, prompt_user, max_tokens)
                )
            except Exception as e:
                self.logger.error(f"Error processing slide {idx} with Gemini: {str(e)}")
                narratives.append("")
        return narratives


def get_vlm(
    model: str, base_url: str, model_identifier: str, api_key: str = None
) -> BaseVLM:
    if model == "LLMStudio":
        return LLMStudioVLM(base_url, model_identifier, api_key or "lm-studio")
    elif model == "Gemini 2.0":
        return GeminiVLM(base_url, model_identifier, api_key)
    else:
        raise ValueError(f"Unsupported model: {model}")
