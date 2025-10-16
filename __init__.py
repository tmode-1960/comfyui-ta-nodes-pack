"""
TA Nodes Pack - Custom Nodes für ComfyUI
Enthält Nodes zum Laden verschiedener Modelltypen mit Namen
"""

from .ta_load_checkpoint_model_with_name import TALoadCheckpointModelWithName
from .ta_load_diffusion_model_with_name import TALoadDiffusionModelWithName
from .ta_load_gguf_model_with_name import TALoadGGUFModelWithName

# Node-Klassen-Mappings
NODE_CLASS_MAPPINGS = {
    "TALoadCheckpointModelWithName": TALoadCheckpointModelWithName,
    "TALoadDiffusionModelWithName": TALoadDiffusionModelWithName,
    "TALoadGGUFModelWithName": TALoadGGUFModelWithName,
}

# Display-Namen für die UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "TALoadCheckpointModelWithName": "TA Load Checkpoint Model (with Name)",
    "TALoadDiffusionModelWithName": "TA Load Diffusion Model (with Name)",
    "TALoadGGUFModelWithName": "TA Load GGUF Model (with Name)",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']