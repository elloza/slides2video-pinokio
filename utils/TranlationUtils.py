from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import os

torch.classes.__path__ = [os.path.join(torch.__path__[0], torch.classes.__file__)] 

"""
Módulo: TranlationUtils.py

Este módulo define la clase Translator que encapsula la lógica de traducción 
utilizando Open-NLLB de Hugging Face y aplica el patrón singleton.
"""

class Translator:
    def __init__(self, model_name: str = "facebook/nllb-200-distilled-600M", token: bool = False) -> None:
        if not hasattr(self, "model"):
            self.model_name = model_name
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, token=token)

    def translate_notes(self, source_lang: str, target_lang: str, text: str) -> str:
        """
        Traduce el texto de un slide de un idioma a otro usando Open-NLLB.
        
        Los códigos de idioma deben estar en formato BCP-47 (ej. "ron_Latn" para rumano, "deu_Latn" para alemán),
        tal como se usan en el dataset FLORES-200.
        
        Parámetros:
            source_lang (str): Código BCP-47 del idioma origen.
            target_lang (str): Código BCP-47 del idioma destino.
            text (str): Texto a traducir.

        Retorna:
            str: Texto traducido.
        """
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            token=False,
            src_lang=source_lang,
            tgt_lang=target_lang,
            use_fast=False  # Forzamos el uso del tokenizador lento
        )
        inputs = tokenizer(text, return_tensors="pt")
        max_length = len(text) * 2
        translated_tokens = self.model.generate(**inputs, forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_lang), max_length=max_length)
        translation = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        return translation
