"""
TA Conditional Prompt Node - Wechselt zwischen manuellem Prompt und Image2Prompt Output
"""

class TAClearPrompt:
    """
    Custom Node zum Wechseln zwischen manuellem Prompt und Image2Prompt
    Leert den manuellen Prompt wenn Image2Prompt aktiviert ist
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["manual_prompt", "image2prompt"], {
                    "default": "manual_prompt"
                }),
            },
            "optional": {
                "manual_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "forceInput": False
                }),
                "image2prompt_output": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "forceInput": True
                }),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "select_prompt"
    CATEGORY = "TA Nodes"
    
    def select_prompt(self, mode, manual_prompt="", image2prompt_output=""):
        """
        Wählt zwischen manuellem Prompt und Image2Prompt Output
        
        Args:
            mode: "manual_prompt" oder "image2prompt"
            manual_prompt: Der manuelle positive Prompt
            image2prompt_output: Der Output vom Image2Prompt (LMStudio)
            
        Returns:
            tuple: (selected_prompt,)
        """
        if mode == "image2prompt":
            # Wenn Image2Prompt aktiviert ist, verwende dessen Output
            return (image2prompt_output if image2prompt_output else "",)
        else:
            # Sonst verwende den manuellen Prompt
            return (manual_prompt,)