"""
TA LMStudio Auto Load Node - Windows UTF-8 Fix
Behebt UnicodeDecodeError auf Windows beim Lesen von lms Output
"""

import subprocess
import time
import re
import sys


class TALMStudioAutoLoad:
    """
    Node die ein Modell auswählt UND automatisch lädt
    Windows-kompatibel mit UTF-8 Encoding
    """
    
    _model_paths = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        models = cls.get_available_models()
        
        return {
            "required": {
                "model": (models, {
                    "default": models[0] if models else "llava-v1.5"
                }),
                "auto_load": ("BOOLEAN", {
                    "default": True,
                    "label_on": "Auto Load",
                    "label_off": "Manual"
                }),
                "context_length": ("INT", {
                    "default": 8192,
                    "min": 512,
                    "max": 131072,
                    "step": 512
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("model_name", "status")
    FUNCTION = "select_and_load"
    CATEGORY = "TA-Nodes/LMStudio"

    @classmethod
    def get_available_models(cls):
        """Holt ALLE verfügbaren Modelle und speichert ihre vollen Pfade"""
        cls._model_paths = {}
        
        try:
            # Windows: Nutze UTF-8 encoding explizit
            result = subprocess.run(
                ['lms', 'ls', '--detailed'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'  # Ersetze nicht-dekodierbare Zeichen
            )
            
            if result.returncode == 0:
                models = []
                lines = result.stdout.split('\n')
                
                for line in lines:
                    line = line.strip()
                    
                    if not line or 'Downloaded models' in line or line.startswith('-'):
                        continue
                    
                    parts = line.split()
                    if not parts:
                        continue
                    
                    full_path = parts[0]
                    
                    if full_path.startswith('/'):
                        full_path = full_path.lstrip('/')
                    
                    # Erstelle Display-Namen
                    if '/' in full_path:
                        path_parts = full_path.split('/')
                        if len(path_parts) >= 2:
                            display_name = '/'.join(path_parts[-2:])
                        else:
                            display_name = path_parts[-1]
                    else:
                        display_name = full_path
                    
                    cls._model_paths[display_name] = full_path
                    models.append(display_name)
                    
                    print(f"[TA-AutoLoad] Mapped: '{display_name}' -> '{full_path}'")
                
                if models:
                    print(f"[TA-AutoLoad] Total found: {len(models)} models")
                    models.sort()
                    return models
                else:
                    print("[TA-AutoLoad] No models found, using defaults")
                    return cls.get_default_models()
            else:
                print(f"[TA-AutoLoad] lms command failed")
                return cls.get_default_models()
                
        except Exception as e:
            print(f"[TA-AutoLoad] Error listing models: {e}")
            return cls.get_default_models()
    
    @classmethod
    def get_default_models(cls):
        """Fallback Modelle"""
        defaults = [
            "llava-v1.5-7b",
            "qwen2-vl-7b-instruct",
            "pixtral-12b",
            "google/gemma-3-27b",
            "llama-3.1-unhinged-vision-8b",
        ]
        for model in defaults:
            if model not in cls._model_paths:
                cls._model_paths[model] = model
        return defaults

    def is_model_loaded(self, model_name):
        """Prüft ob Modell bereits geladen ist"""
        try:
            result = subprocess.run(
                ['lms', 'ps'],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                if model_name in output:
                    return True
                
                full_path = self._model_paths.get(model_name, model_name)
                if full_path in output:
                    return True
                
                # Prüfe Teile des Namens
                name_parts = model_name.replace('/', ' ').split()
                for part in name_parts:
                    if len(part) > 4 and part in output:
                        print(f"[TA-AutoLoad] Model seems loaded (matched: {part})")
                        return True
                
                return False
            return False
        except Exception as e:
            print(f"[TA-AutoLoad] Error checking loaded models: {e}")
            return False

    def load_model(self, display_name, context_length):
        """
        Lädt das Modell - Windows UTF-8 safe
        """
        full_path = self._model_paths.get(display_name, display_name)
        
        print(f"[TA-AutoLoad] Loading model...")
        print(f"[TA-AutoLoad]   Display name: {display_name}")
        print(f"[TA-AutoLoad]   Full path: {full_path}")
        
        try:
            # Unload vorherige Modelle
            print("[TA-AutoLoad] Unloading previous models...")
            try:
                subprocess.run(
                    ['lms', 'unload', '--all', '-y'],
                    capture_output=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='replace'
                )
                time.sleep(2)
            except Exception as e:
                print(f"[TA-AutoLoad] Warning during unload: {e}")
            
            # Lade neues Modell
            load_cmd = [
                'lms', 'load', full_path, '-y',
                f'--context-length={context_length}',
                '--gpu=1'
            ]
            
            print(f"[TA-AutoLoad] Running: {' '.join(load_cmd)}")
            
            # WICHTIG: Nutze encoding='utf-8' und errors='replace' für Windows
            result = subprocess.run(
                load_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='replace'  # Ignoriere Encoding-Fehler
            )
            
            print(f"[TA-AutoLoad] Return code: {result.returncode}")
            
            # Zeige Output nur wenn interessant
            if result.returncode == 0:
                print(f"[TA-AutoLoad] ✓ Model loaded successfully!")
                # Extrahiere API identifier aus Output falls vorhanden
                if 'identifier' in result.stderr.lower():
                    for line in result.stderr.split('\n'):
                        if 'identifier' in line.lower() and '"' in line:
                            print(f"[TA-AutoLoad]   {line.strip()}")
                time.sleep(3)
                return True, "Loaded"
            else:
                # Bei Fehler zeige Details
                if result.stdout:
                    print(f"[TA-AutoLoad] stdout: {result.stdout[:300]}")
                if result.stderr:
                    print(f"[TA-AutoLoad] stderr: {result.stderr[:300]}")
                return False, f"Load failed (code {result.returncode})"
                
        except subprocess.TimeoutExpired:
            print("[TA-AutoLoad] ✗ Timeout loading model")
            return False, "Timeout (>120s)"
        except Exception as e:
            print(f"[TA-AutoLoad] ✗ Error: {str(e)}")
            return False, f"Error: {str(e)}"

    def select_and_load(self, model, auto_load, context_length):
        """Wählt Modell aus und lädt es automatisch"""
        
        # API-Name ist der letzte Teil
        if '/' in model:
            api_name = model.split('/')[-1]
        else:
            api_name = model
        
        print(f"[TA-AutoLoad] ===== NEW REQUEST =====")
        print(f"[TA-AutoLoad] Selected: {model}")
        print(f"[TA-AutoLoad] API name: {api_name}")
        print(f"[TA-AutoLoad] Auto-load: {auto_load}")
        
        if not auto_load:
            print(f"[TA-AutoLoad] Auto-load disabled")
            return (api_name, "Manual mode")
        
        # Prüfe ob bereits geladen
        if self.is_model_loaded(model):
            print(f"[TA-AutoLoad] Model already loaded")
            return (api_name, "Already loaded")
        
        # Lade Modell
        print(f"[TA-AutoLoad] Model not loaded, loading now...")
        success, status = self.load_model(model, context_length)
        
        return (api_name, status)


# Node Registration
NODE_CLASS_MAPPINGS = {
    "TALMStudioAutoLoad": TALMStudioAutoLoad,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TALMStudioAutoLoad": "TA LMStudio Auto Load (Select & Load)",
}
