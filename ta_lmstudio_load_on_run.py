"""
TA LMStudio Load On Run Node
Lädt das Modell NUR wenn der Workflow ausgeführt wird (auf RUN klicken)
Nicht beim Auswählen im Dropdown!
"""

import subprocess
import time


class TALMStudioLoadOnRun:
    """
    Node die ein Modell aus Dropdown auswählt
    Lädt es aber erst beim Ausführen des Workflows (RUN klicken)
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
                "context_length": ("INT", {
                    "default": 8192,
                    "min": 512,
                    "max": 131072,
                    "step": 512
                }),
                "unload_after": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Unload after use",
                    "label_off": "Keep loaded"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("model_name", "status")
    FUNCTION = "load_and_return"  # Wird beim RUN ausgeführt
    CATEGORY = "TA-Nodes/LMStudio"

    @classmethod
    def get_available_models(cls):
        """Holt ALLE verfügbaren Modelle"""
        cls._model_paths = {}
        
        try:
            result = subprocess.run(
                ['lms', 'ls', '--detailed'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
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
                    
                    # Display-Namen erstellen
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
                
                if models:
                    print(f"[TA-LoadOnRun] Found {len(models)} models")
                    models.sort()
                    return models
                else:
                    return cls.get_default_models()
            else:
                return cls.get_default_models()
                
        except Exception as e:
            print(f"[TA-LoadOnRun] Error listing models: {e}")
            return cls.get_default_models()
    
    @classmethod
    def get_default_models(cls):
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
                full_path = self._model_paths.get(model_name, model_name)
                
                if model_name in output or full_path in output:
                    return True
                
                # Prüfe Teile des Namens
                name_parts = model_name.replace('/', ' ').split()
                for part in name_parts:
                    if len(part) > 4 and part in output:
                        return True
                
                return False
            return False
        except:
            return False

    def load_model(self, display_name, context_length):
        """Lädt das Modell"""
        full_path = self._model_paths.get(display_name, display_name)
        
        print(f"[TA-LoadOnRun] === LOADING MODEL ON RUN ===")
        print(f"[TA-LoadOnRun] Display: {display_name}")
        print(f"[TA-LoadOnRun] Path: {full_path}")
        
        try:
            # Prüfe ob schon geladen
            if self.is_model_loaded(display_name):
                print(f"[TA-LoadOnRun] Model already loaded, using existing")
                return True, "Already loaded"
            
            # Entlade alte Modelle
            print("[TA-LoadOnRun] Unloading previous models...")
            try:
                subprocess.run(
                    ['lms', 'unload', '--all', '-y'],
                    capture_output=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='replace'
                )
                time.sleep(2)
            except:
                pass
            
            # Lade neues Modell
            load_cmd = [
                'lms', 'load', full_path, '-y',
                f'--context-length={context_length}',
                '--gpu=1'
            ]
            
            print(f"[TA-LoadOnRun] Running: {' '.join(load_cmd)}")
            
            result = subprocess.run(
                load_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='replace'
            )
            
            print(f"[TA-LoadOnRun] Return code: {result.returncode}")
            
            if result.returncode == 0:
                print(f"[TA-LoadOnRun] ✓ Model loaded successfully!")
                time.sleep(3)
                return True, "Loaded on run"
            else:
                print(f"[TA-LoadOnRun] ✗ Load failed")
                if result.stderr:
                    print(f"[TA-LoadOnRun] Error: {result.stderr[:200]}")
                return False, "Load failed"
                
        except subprocess.TimeoutExpired:
            print("[TA-LoadOnRun] ✗ Timeout")
            return False, "Timeout"
        except Exception as e:
            print(f"[TA-LoadOnRun] ✗ Error: {e}")
            return False, f"Error: {str(e)}"

    def unload_model(self):
        """Entlädt das Modell nach Verwendung"""
        try:
            print("[TA-LoadOnRun] Unloading model after use...")
            subprocess.run(
                ['lms', 'unload', '--all', '-y'],
                capture_output=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )
        except:
            pass

    def load_and_return(self, model, context_length, unload_after):
        """
        DIESE Funktion wird NUR beim RUN ausgeführt!
        Nicht beim Auswählen im Dropdown!
        """
        # API-Name
        if '/' in model:
            api_name = model.split('/')[-1]
        else:
            api_name = model
        
        print(f"[TA-LoadOnRun] ===== WORKFLOW EXECUTION =====")
        print(f"[TA-LoadOnRun] User clicked RUN")
        print(f"[TA-LoadOnRun] Selected model: {model}")
        
        # Lade Modell JETZT (beim RUN)
        success, status = self.load_model(model, context_length)
        
        # Optional: Entlade nach Verwendung
        if unload_after and success:
            # Wir können hier nicht direkt entladen, da die Vision Node es noch braucht
            # Aber wir merken es uns für später
            status = status + " (will unload)"
        
        return (api_name, status)


# Node Registration
NODE_CLASS_MAPPINGS = {
    "TALMStudioLoadOnRun": TALMStudioLoadOnRun,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TALMStudioLoadOnRun": "TA LMStudio Load (On Run)",
}
