"""
TA-EBU-LMStudio Vision Node für Image-to-Prompt
Teil des ComfyUI-TA-Nodes-Pack
Erweitert LM Studio um Vision Language Model Support für Image-to-Prompt
"""

import torch
import numpy as np
from PIL import Image
import io
import base64
import requests
import time
import sys


class TAEbuLMStudioVisionRequest:
    """
    TA Node für Image-to-Prompt mit LM Studio Vision Language Models
    Nutzt VLMs wie LLaVA, Qwen2-VL, Pixtral für Bildbeschreibungen
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {
                    "default": "Describe this image in detail.",
                    "multiline": True
                }),
                "model_name": ("STRING", {
                    "default": "llava-v1.5",
                    "multiline": False
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1
                }),
                "max_tokens": ("INT", {
                    "default": 500,
                    "min": 1,
                    "max": 4096
                }),
                "server_url": ("STRING", {
                    "default": "http://localhost:1234",
                    "multiline": False
                }),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "default": "You are a helpful AI assistant that describes images accurately.",
                    "multiline": True
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("generated_prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "TA-Nodes/LMStudio"

    def tensor_to_base64(self, image_tensor):
        """
        Konvertiert ComfyUI Image Tensor zu Base64 String
        ComfyUI Format: [batch, height, width, channels] mit Werten 0-1
        """
        # Nehme das erste Bild aus dem Batch
        if len(image_tensor.shape) == 4:
            image_tensor = image_tensor[0]
        
        # Konvertiere von [H, W, C] zu numpy array
        image_np = image_tensor.cpu().numpy()
        
        # Konvertiere von 0-1 zu 0-255
        image_np = (image_np * 255).astype(np.uint8)
        
        # Erstelle PIL Image
        pil_image = Image.fromarray(image_np)
        
        # Konvertiere zu Base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_base64

    def generate_prompt(self, image, prompt, model_name, temperature, max_tokens, 
                       server_url, system_prompt=None):
        """
        Sendet Bild und Prompt an LM Studio Vision Model
        Nutzt OpenAI-kompatible API mit Base64-kodierten Bildern
        """
        try:
            start_time = time.time()
            
            print(f"[TA-Vision] Converting image to base64...")
            image_base64 = self.tensor_to_base64(image)
            
            # Baue die API Request nach OpenAI-kompatiblem Format
            url = f"{server_url}/v1/chat/completions"
            
            messages = []
            
            # Optional: System Prompt hinzufügen
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # User Message mit Bild
            # Format: OpenAI-kompatibel mit base64 image_url
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            })
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            print(f"[TA-Vision] Sending request to LM Studio ({model_name})...")
            print(f"[TA-Vision] Prompt: {prompt}")
            
            # Sende Request
            response = requests.post(url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['message']['content']
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                print(f"\n{'='*60}")
                print(f"[TA-Vision] Generated Prompt:")
                print(f"{generated_text}")
                print(f"{'='*60}")
                print(f"[TA-Vision] Generation time: {elapsed_time:.2f} seconds\n")
                
                return (generated_text,)
            else:
                error_message = f"Error {response.status_code}: {response.text}"
                print(f"[TA-Vision] {error_message}", file=sys.stderr)
                
                # Hilfreiche Fehlermeldungen
                if response.status_code == 404:
                    error_message += "\n\n[TA-Vision] HINT: Ist das Vision-Modell in LM Studio geladen?"
                elif "does not support images" in response.text:
                    error_message += "\n\n[TA-Vision] HINT: Das geladene Modell unterstützt keine Bilder. Bitte ein Vision-Modell laden (z.B. llava-v1.5, qwen2-vl, pixtral)."
                
                return (error_message,)
                
        except requests.exceptions.ConnectionError:
            error_message = "[TA-Vision] Connection Error: LM Studio Server nicht erreichbar. Ist LM Studio gestartet und der Server aktiv?"
            print(error_message, file=sys.stderr)
            return (error_message,)
        except Exception as e:
            error_message = f"[TA-Vision] Error: {str(e)}"
            print(error_message, file=sys.stderr)
            return (error_message,)


class TAEbuLMStudioLoadModel:
    """
    TA Node zum Laden von LM Studio Modellen via CLI
    Kompatibel mit Text- und Vision-Modellen
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_search_string": ("STRING", {
                    "default": "llava",
                    "multiline": False
                }),
                "context_length": ("INT", {
                    "default": 8192,
                    "min": 512,
                    "max": 131072
                }),
            },
            "optional": {
                "input_string": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output_string", "loaded_model")
    FUNCTION = "load_model"
    CATEGORY = "TA-Nodes/LMStudio"

    def load_model(self, model_search_string, context_length, input_string=""):
        """
        Lädt ein Modell in LM Studio via lms CLI
        """
        try:
            import subprocess
            
            print(f"[TA-LMStudio] Searching for model: {model_search_string}")
            
            # Suche nach Modell
            search_cmd = ['lms', 'ls', '--detailed']
            result = subprocess.run(search_cmd, capture_output=True, text=True, check=True)
            
            # Finde passendes Modell
            search_parts = model_search_string.lower().split()
            search_pattern = '.*'.join(search_parts)
            
            import re
            matched_models = []
            
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith('/'):
                    model_path = line.split()[0].lstrip("/")
                    if re.search(search_pattern, model_path.lower()):
                        matched_models.append(model_path)
            
            if not matched_models:
                error_msg = f"[TA-LMStudio] No models found matching '{model_search_string}'"
                print(error_msg)
                return (input_string, error_msg)
            
            model_path = matched_models[0]
            print(f"[TA-LMStudio] Loading model: {model_path}")
            
            # Lade Modell
            load_cmd = ['lms', 'load', model_path, '-y', f'--context-length={context_length}', '--gpu=1']
            load_result = subprocess.run(load_cmd, capture_output=True, text=True, check=True)
            
            if load_result.returncode == 0:
                print(f"[TA-LMStudio] Model loaded successfully: {model_path}")
                return (input_string, model_path)
            else:
                error_msg = f"[TA-LMStudio] Failed to load model: {model_path}"
                print(error_msg)
                return (input_string, error_msg)
                
        except Exception as e:
            error_msg = f"[TA-LMStudio] Error: {str(e)}"
            print(error_msg, file=sys.stderr)
            return (input_string, error_msg)


class TAEbuLMStudioUnload:
    """
    TA Node zum Entladen aller LM Studio Modelle
    Nützlich für VRAM-Management zwischen Tasks
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "input_string": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_string",)
    FUNCTION = "unload_models"
    CATEGORY = "TA-Nodes/LMStudio"

    def unload_models(self, input_string=""):
        """
        Entlädt alle geladenen Modelle in LM Studio
        """
        try:
            import subprocess
            
            print(f"[TA-LMStudio] Unloading all models...")
            
            unload_cmd = ['lms', 'unload', '--all', '-y']
            result = subprocess.run(unload_cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                print(f"[TA-LMStudio] All models unloaded successfully")
                return (input_string,)
            else:
                error_msg = "[TA-LMStudio] Failed to unload models"
                print(error_msg)
                return (error_msg,)
                
        except Exception as e:
            error_msg = f"[TA-LMStudio] Error: {str(e)}"
            print(error_msg, file=sys.stderr)
            return (error_msg,)


# Node Registration
NODE_CLASS_MAPPINGS = {
    "TAEbuLMStudioVisionRequest": TAEbuLMStudioVisionRequest,
    "TAEbuLMStudioLoadModel": TAEbuLMStudioLoadModel,
    "TAEbuLMStudioUnload": TAEbuLMStudioUnload,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TAEbuLMStudioVisionRequest": "TA LMStudio Vision (Image-to-Prompt)",
    "TAEbuLMStudioLoadModel": "TA LMStudio Load Model",
    "TAEbuLMStudioUnload": "TA LMStudio Unload All",
}
