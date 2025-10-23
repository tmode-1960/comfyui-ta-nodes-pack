"""
TA LMStudio Load On Run Node - With Vision Model Marking
Kennzeichnet Vision-Modelle mit (V) im Dropdown
"""

import subprocess
import time
import re


class TALMStudioLoadOnRun:
    """
    Node mit Vision-Modell-Kennzeichnung
    """
    
    _model_paths = {}
    _vision_keywords = [
        # Explizite Vision-Keywords
        'vision', 'llava', 'pixtral', 'minicpm-v', 'cogvlm', 'internvl',
        'molmo', 'aria', 'phi-3-vision', 'phi-3.5-vision',
        # Qwen: NUR VL-Varianten sind Vision
        'qwen-vl', 'qwen2-vl', 'qwen2.5-vl', 'qwen3-vl', 'qwq-vl',
        # Llama: NUR 3.1 und 3.2 haben Vision
        'llama-3.1', 'llama-3.2', 'llama3.1', 'llama3.2',
        # Gemma: NUR Gemma 3 (Gemini-basiert) hat Vision
        'gemma-3', 'paligemma',
        # Andere bekannte Vision-Modelle
        'fuyu', 'kosmos', 'idefics', 'otter', 'flamingo', 'blip',
        'deepseek-vl', 'yi-vl', 'mplug', 'sphinx', 'video-llama',
    ]
    
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
                "wait_time": ("INT", {
                    "default": 8,
                    "min": 1,
                    "max": 30,
                    "step": 1,
                    "display": "number",
                    "tooltip": "Seconds to wait after loading (8-10s recommended for large models)"
                }),
                "skip_unload": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Skip unload",
                    "label_off": "Try unload",
                    "tooltip": "Skip unload if it keeps failing"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("model_name", "status")
    FUNCTION = "load_and_return"
    CATEGORY = "TA-Nodes/LMStudio"

    @classmethod
    def is_valid_model(cls, model_name):
        """
        Prüft ob ein Eintrag ein echtes Modell ist
        Filtert Meta-Einträge wie EMBEDDING, LLM, You, etc.
        """
        if not model_name or len(model_name) < 3:
            return False
        
        # Filter: Bekannte Meta-Einträge (case-insensitive)
        blocked_entries = [
            'embedding', 'llm', 'you', 'default', 'none', 
            'text-embedding', 'all-minilm', 'bge-', 'e5-'
        ]
        
        model_lower = model_name.lower()
        for blocked in blocked_entries:
            if model_lower == blocked or model_lower.startswith(blocked):
                return False
        
        # Filter: Nur Großbuchstaben (wahrscheinlich Kategorie)
        if model_name.isupper() and len(model_name) < 15:
            return False
        
        return True
    
    @classmethod
    def is_vision_model(cls, model_name):
        """
        Prüft ob ein Modell ein Vision-Modell ist
        Basiert auf bekannten Vision-Model Keywords
        """
        model_lower = model_name.lower()
        
        for keyword in cls._vision_keywords:
            if keyword in model_lower:
                return True
        
        return False

    @classmethod
    def get_available_models(cls):
        """Holt ALLE verfügbaren Modelle und markiert Vision-Modelle"""
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
                    
                    # FILTER: Überspringe Meta-Einträge
                    if not cls.is_valid_model(display_name):
                        continue
                    
                    # PRÜFE OB VISION MODEL
                    if cls.is_vision_model(display_name):
                        # Füge (V) hinzu für Vision-Modelle
                        display_name_marked = f"{display_name} (V)"
                    else:
                        display_name_marked = display_name
                    
                    # Speichere beide: marked name → full path
                    cls._model_paths[display_name_marked] = full_path
                    models.append(display_name_marked)
                
                if models:
                    # Sortiere: Vision-Modelle zuerst, dann alphabetisch
                    vision_models = [m for m in models if '(V)' in m]
                    text_models = [m for m in models if '(V)' not in m]
                    
                    vision_models.sort()
                    text_models.sort()
                    
                    # Vision-Modelle zuerst
                    sorted_models = vision_models + text_models
                    
                    return sorted_models
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
            "llava-v1.5-7b (V)",
            "qwen2-vl-7b-instruct (V)",
            "pixtral-12b (V)",
            "google/gemma-3-27b (V)",
            "llama-3.1-unhinged-vision-8b (V)",
        ]
        for model in defaults:
            if model not in cls._model_paths:
                # Entferne (V) für den Pfad
                model_path = model.replace(" (V)", "")
                cls._model_paths[model] = model_path
        return defaults

    def try_unload(self):
        """Versucht zu entladen, toleriert Fehler"""
        print("[TA-LoadOnRun] Attempting to unload models...")
        
        try:
            result = subprocess.run(
                ['lms', 'unload', '--all', '-y'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )
            
            output = (result.stdout + result.stderr).lower()
            
            if 'no models to unload' in output or 'no models loaded' in output:
                print(f"[TA-LoadOnRun] ✓ Already unloaded")
                return True
            elif result.returncode == 0:
                print(f"[TA-LoadOnRun] ✓ Unload successful")
                time.sleep(2)
                return True
            else:
                print(f"[TA-LoadOnRun] ⚠ Unload returned code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[TA-LoadOnRun] ⚠ Unload timeout - continuing anyway")
            return False
        except Exception as e:
            print(f"[TA-LoadOnRun] ⚠ Unload error: {e} - continuing anyway")
            return False

    def is_model_loaded(self, model_name):
        """Prüft ob Modell geladen ist"""
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
                # Entferne (V) vom Namen für Vergleich
                clean_name = model_name.replace(" (V)", "")
                full_path = self._model_paths.get(model_name, clean_name)
                
                if clean_name in output or full_path in output:
                    return True
                
                name_parts = clean_name.replace('/', ' ').split()
                for part in name_parts:
                    if len(part) > 4 and part in output:
                        return True
                
                return False
            return False
        except:
            return False

    def wait_for_model_ready(self, model_name, max_wait=20):
        """Wartet bis Modell bereit ist"""
        print(f"[TA-LoadOnRun] Verifying model is ready...")
        
        for i in range(max_wait):
            if self.is_model_loaded(model_name):
                print(f"[TA-LoadOnRun] ✓ Model verified after {i+1}s")
                return True
            
            if i == 0 or (i+1) % 5 == 0:
                print(f"[TA-LoadOnRun]   Checking... ({i+1}/{max_wait}s)")
            
            time.sleep(1)
        
        print(f"[TA-LoadOnRun] ⚠ Could not verify model after {max_wait}s")
        return False

    def load_model(self, display_name, context_length, wait_time, skip_unload):
        """Lädt das Modell"""
        # Entferne (V) für den tatsächlichen Load-Befehl
        clean_name = display_name.replace(" (V)", "")
        full_path = self._model_paths.get(display_name, clean_name)
        
        print(f"[TA-LoadOnRun] === LOADING MODEL ===")
        print(f"[TA-LoadOnRun] Display: {display_name}")
        print(f"[TA-LoadOnRun] Path: {full_path}")
        print(f"[TA-LoadOnRun] Wait time: {wait_time}s")
        
        try:
            # Versuche zu entladen (optional)
            if not skip_unload:
                unload_ok = self.try_unload()
                if unload_ok:
                    time.sleep(2)
                else:
                    print(f"[TA-LoadOnRun] Continuing despite unload issues...")
                    time.sleep(1)
            else:
                print(f"[TA-LoadOnRun] Skipping unload (skip_unload=True)")
            
            # Lade Modell
            load_cmd = [
                'lms', 'load', full_path, '-y',
                f'--context-length={context_length}',
                '--gpu=1'
            ]
            
            print(f"[TA-LoadOnRun] Loading: {' '.join(load_cmd)}")
            
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
                print(f"[TA-LoadOnRun] ✓ Load command completed")
                
                # Warnung bei zu kurzem wait_time
                if wait_time < 3:
                    print(f"[TA-LoadOnRun] ⚠ WARNING: wait_time={wait_time}s is too short!")
                    print(f"[TA-LoadOnRun] ⚠ Recommended: 8-10s for reliable loading")
                
                print(f"[TA-LoadOnRun] Waiting {wait_time}s for initialization...")
                time.sleep(wait_time)
                
                # Verifiziere
                if self.wait_for_model_ready(display_name, max_wait=15):
                    print(f"[TA-LoadOnRun] ✓✓✓ MODEL READY! ✓✓✓")
                    return True, "Loaded and ready"
                else:
                    print(f"[TA-LoadOnRun] ⚠ Load completed but verification failed")
                    print(f"[TA-LoadOnRun] ⚠ Model might still work, trying anyway...")
                    return True, "Loaded (not verified)"
            else:
                print(f"[TA-LoadOnRun] ✗ Load failed with code {result.returncode}")
                if result.stderr:
                    print(f"[TA-LoadOnRun] Error: {result.stderr[:300]}")
                return False, f"Load failed (code {result.returncode})"
                
        except subprocess.TimeoutExpired:
            print("[TA-LoadOnRun] ✗ Load timeout (>120s)")
            return False, "Timeout"
        except Exception as e:
            print(f"[TA-LoadOnRun] ✗ Error: {e}")
            return False, f"Error: {str(e)}"

    def load_and_return(self, model, context_length, wait_time, skip_unload):
        """Wird beim RUN ausgeführt"""
        
        # Warnung bei zu kurzem wait_time
        if wait_time < 3:
            print(f"\n{'!'*60}")
            print(f"[TA-LoadOnRun] ⚠⚠⚠ WARNING ⚠⚠⚠")
            print(f"[TA-LoadOnRun] wait_time={wait_time}s is TOO SHORT!")
            print(f"[TA-LoadOnRun] This may cause 'Model not loaded' errors!")
            print(f"[TA-LoadOnRun] RECOMMENDED: Set wait_time to 8-10s")
            print(f"{'!'*60}\n")
        
        # API-Name (entferne (V))
        clean_model = model.replace(" (V)", "")
        if '/' in clean_model:
            api_name = clean_model.split('/')[-1]
        else:
            api_name = clean_model
        
        print(f"\n{'='*60}")
        print(f"[TA-LoadOnRun] ===== WORKFLOW EXECUTION =====")
        print(f"[TA-LoadOnRun] Model: {model}")
        print(f"[TA-LoadOnRun] Wait time: {wait_time}s")
        print(f"[TA-LoadOnRun] Skip unload: {skip_unload}")
        print(f"{'='*60}\n")
        
        # Lade Modell
        success, status = self.load_model(model, context_length, wait_time, skip_unload)
        
        if success:
            print(f"\n[TA-LoadOnRun] ✓ READY FOR VISION NODE\n")
        else:
            print(f"\n[TA-LoadOnRun] ✗ LOAD FAILED\n")
        
        return (api_name, status)


# Node Registration
NODE_CLASS_MAPPINGS = {
    "TALMStudioLoadOnRun": TALMStudioLoadOnRun,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TALMStudioLoadOnRun": "TA LMStudio Load (On Run)",
}
