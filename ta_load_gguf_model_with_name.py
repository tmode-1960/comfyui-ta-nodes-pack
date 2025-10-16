import folder_paths
import comfy.sd
import os
import logging
import sys
import traceback

class TALoadGGUFModelWithName:
    """
    Lädt ein GGUF-Modell und gibt zusätzlich den Modellnamen aus
    Debug-Version mit detailliertem Logging
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # Suche GGUF-Dateien in verschiedenen Verzeichnissen
        unet_names = []
        
        # Primär: unet_gguf Verzeichnis
        try:
            unet_names = folder_paths.get_filename_list("unet_gguf")
        except:
            pass
        
        # Fallback: unet Verzeichnis mit .gguf Filter
        if not unet_names:
            try:
                all_files = folder_paths.get_filename_list("unet")
                unet_names = [x for x in all_files if x.endswith(".gguf")]
            except:
                pass
        
        # Zweiter Fallback: diffusion_models mit .gguf Filter  
        if not unet_names:
            try:
                all_files = folder_paths.get_filename_list("diffusion_models")
                unet_names = [x for x in all_files if x.endswith(".gguf")]
            except:
                pass
        
        return {
            "required": {
                "unet_name": (unet_names if unet_names else ["No GGUF files found"],),
            }
        }
    
    RETURN_TYPES = ("MODEL", "STRING")
    RETURN_NAMES = ("model", "model_name")
    FUNCTION = "load_unet"
    CATEGORY = "TA Nodes/loaders"
    TITLE = "TA Load GGUF Model (with Name)"
    
    def load_unet(self, unet_name):
        print(f"\n=== TA GGUF Loader Debug Info ===")
        print(f"Attempting to load: {unet_name}")
        
        # Versuche die Datei in verschiedenen Verzeichnissen zu finden
        unet_path = None
        for folder_type in ["unet_gguf", "unet", "diffusion_models"]:
            try:
                potential_path = folder_paths.get_full_path(folder_type, unet_name)
                if potential_path and os.path.exists(potential_path):
                    unet_path = potential_path
                    print(f"Found file at: {unet_path}")
                    break
            except:
                continue
        
        if unet_path is None:
            raise FileNotFoundError(f"Could not find {unet_name} in any model directory")
        
        # Debug: Zeige sys.path
        print(f"\nPython sys.path entries:")
        for i, p in enumerate(sys.path[:10]):  # Erste 10 Einträge
            print(f"  {i}: {p}")
        
        # Prüfe ob ComfyUI-GGUF existiert
        gguf_node_path = os.path.join(folder_paths.base_path, "custom_nodes", "ComfyUI-GGUF")
        print(f"\nComfyUI-GGUF path: {gguf_node_path}")
        print(f"ComfyUI-GGUF exists: {os.path.exists(gguf_node_path)}")
        
        if os.path.exists(gguf_node_path):
            print(f"ComfyUI-GGUF contents:")
            try:
                for item in os.listdir(gguf_node_path)[:15]:  # Erste 15 Dateien
                    print(f"  - {item}")
            except:
                print("  Could not list directory contents")
        
        model = None
        
        # Methode 1: Direkt die GGUF nodes.py importieren
        print(f"\n--- Method 1: Direct import from ComfyUI-GGUF ---")
        try:
            # Stelle sicher, dass der Pfad in sys.path ist
            if gguf_node_path not in sys.path:
                sys.path.insert(0, gguf_node_path)
                print(f"Added {gguf_node_path} to sys.path")
            
            # Versuche verschiedene Import-Methoden
            try:
                # Versuche den direkten Import
                from nodes import UnetLoaderGGUF
                print("Successfully imported UnetLoaderGGUF from nodes")
                
                # Erstelle eine Instanz und lade das Modell
                loader = UnetLoaderGGUF()
                print(f"Created UnetLoaderGGUF instance")
                
                # Rufe die load_unet Funktion auf
                result = loader.load_unet(unet_name)
                model = result[0]
                print(f"Successfully loaded model with UnetLoaderGGUF")
                
            except ImportError as e:
                print(f"Import failed: {e}")
                # Alternative Import-Methode
                import importlib.util
                nodes_path = os.path.join(gguf_node_path, "nodes.py")
                if os.path.exists(nodes_path):
                    print(f"Trying to load nodes.py directly from {nodes_path}")
                    spec = importlib.util.spec_from_file_location("gguf_nodes", nodes_path)
                    gguf_nodes = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(gguf_nodes)
                    
                    if hasattr(gguf_nodes, 'UnetLoaderGGUF'):
                        loader = gguf_nodes.UnetLoaderGGUF()
                        result = loader.load_unet(unet_name)
                        model = result[0]
                        print(f"Successfully loaded model with direct import")
                    else:
                        print(f"UnetLoaderGGUF not found in {nodes_path}")
                        
        except Exception as e:
            print(f"Method 1 failed: {e}")
            traceback.print_exc()
        
        # Methode 2: Verwende die registrierte Node
        if model is None:
            print(f"\n--- Method 2: Use registered node ---")
            try:
                # Importiere die NODE_CLASS_MAPPINGS aus ComfyUI
                from nodes import NODE_CLASS_MAPPINGS
                
                if "UnetLoaderGGUF" in NODE_CLASS_MAPPINGS:
                    print("Found UnetLoaderGGUF in NODE_CLASS_MAPPINGS")
                    loader_class = NODE_CLASS_MAPPINGS["UnetLoaderGGUF"]
                    loader = loader_class()
                    result = loader.load_unet(unet_name)
                    model = result[0]
                    print(f"Successfully loaded model via NODE_CLASS_MAPPINGS")
                else:
                    print(f"UnetLoaderGGUF not found in NODE_CLASS_MAPPINGS")
                    print(f"Available nodes: {list(NODE_CLASS_MAPPINGS.keys())[:10]}...")
                    
            except Exception as e:
                print(f"Method 2 failed: {e}")
                traceback.print_exc()
        
        # Methode 3: Versuche die GGUF-spezifischen Module zu importieren
        if model is None:
            print(f"\n--- Method 3: Import GGUF modules directly ---")
            try:
                sys.path.insert(0, gguf_node_path)
                
                # Importiere die benötigten Module
                from gguf import GGUFReader
                from ops import GGMLOps, GGMLLayer, GGMLTensor
                from loader import gguf_sd_loader
                
                print("Successfully imported GGUF modules")
                
                # Lade das GGUF-Modell
                ops = GGMLOps()
                sd = gguf_sd_loader(unet_path)
                
                print(f"Loaded state dict with gguf_sd_loader")
                
                # Lade das Modell
                model = comfy.sd.load_diffusion_model_state_dict(
                    sd, model_options={"custom_operations": ops}
                )
                
                if model is not None:
                    print(f"Successfully loaded model with GGUF modules")
                    
            except Exception as e:
                print(f"Method 3 failed: {e}")
                traceback.print_exc()
        
        # Wenn alles fehlschlägt
        if model is None:
            print(f"\n=== All methods failed ===")
            error_msg = (
                f"Could not load GGUF model: {unet_name}\n\n"
                f"Debug Info:\n"
                f"- GGUF node path exists: {os.path.exists(gguf_node_path)}\n"
                f"- File path: {unet_path}\n\n"
                f"Please check:\n"
                f"1. ComfyUI-GGUF is properly installed\n"
                f"2. All dependencies are installed (gguf package)\n"
                f"3. The GGUF file is not corrupted\n"
                f"4. Check the console for detailed error messages above"
            )
            raise RuntimeError(error_msg)
        
        # Extrahiere nur den Dateinamen ohne Pfad und Erweiterung
        model_name_only = os.path.splitext(os.path.basename(unet_name))[0]
        
        print(f"\n=== Success ===")
        print(f"Model loaded successfully")
        print(f"Model name: {model_name_only}")
        
        return (model, model_name_only)


NODE_CLASS_MAPPINGS = {
    "TALoadGGUFModelWithName": TALoadGGUFModelWithName
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TALoadGGUFModelWithName": "TA Load GGUF Model (with Name)"
}