"""
TA Description to Prompt - Custom Node für ComfyUI
Converts image descriptions into structured prompts for image generation
"""

import re

class TADescriptionToPrompt:
    """
    Converts descriptive text into comma-separated prompt format suitable for image generation
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "description": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "add_quality_tags": ("BOOLEAN", {
                    "default": True
                }),
                "style": (["default", "photography", "digital_art", "painting", "anime", "cinematic"], {
                    "default": "default"
                }),
                "max_keywords": ("INT", {
                    "default": 50,
                    "min": 10,
                    "max": 100,
                    "step": 5
                }),
            },
            "optional": {
                "custom_suffix": ("STRING", {
                    "multiline": False,
                    "default": ""
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "convert"
    CATEGORY = "text/processing"
    
    def convert(self, description, add_quality_tags=True, style="default", max_keywords=50, custom_suffix=""):
        """
        Convert description to prompt
        """
        # Handle PredictionResult objects from YANC_lmstudio
        if hasattr(description, 'text'):
            text = description.text
        elif hasattr(description, '__str__'):
            text = str(description)
        else:
            text = description
        
        # Check if empty
        if not text or (hasattr(text, 'strip') and text.strip() == ""):
            return ("",)
        
        # Bereinige den Text
        text = str(text).lower().strip()
        
        # Entferne Satzzeichen am Ende von Wörtern
        text = re.sub(r'[.!?,;:]', ' ', text)
        
        # Mehrfache Leerzeichen reduzieren
        text = re.sub(r'\s+', ' ', text)
        
        # Deutsche und englische Stoppwörter
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'been', 'being',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
            'this', 'that', 'these', 'those', 'it', 'its', 'their',
            'has', 'have', 'had', 'does', 'do', 'did', 'will', 'would',
            'can', 'could', 'should', 'may', 'might', 'must',
            'and', 'or', 'but', 'if', 'as', 'than', 'then',
            'there', 'here', 'where', 'when', 'what', 'which', 'who',
            'der', 'die', 'das', 'ein', 'eine', 'ist', 'sind', 'war',
            'mit', 'auf', 'in', 'von', 'zu', 'den', 'dem', 'des'
        }
        
        # Extrahiere Wörter
        words = text.split()
        
        # Filtere Stoppwörter und zu kurze Wörter
        keywords = []
        for word in words:
            word = word.strip()
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)
        
        # Entferne Duplikate, behalte Reihenfolge
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        # Begrenze Keywords
        unique_keywords = unique_keywords[:max_keywords]
        
        # Füge Style-spezifische Tags hinzu
        style_tags = self._get_style_tags(style)
        if style_tags:
            unique_keywords.extend(style_tags)
        
        # Füge Quality Tags hinzu
        if add_quality_tags:
            quality_tags = [
                'highly detailed',
                'professional',
                'high quality',
                '8k',
                'sharp focus',
                'masterpiece'
            ]
            unique_keywords.extend(quality_tags)
        
        # Füge Custom Suffix hinzu
        if custom_suffix and custom_suffix.strip():
            unique_keywords.append(custom_suffix.strip())
        
        # Erstelle finalen Prompt
        prompt = ', '.join(unique_keywords)
        
        return (prompt,)
    
    def _get_style_tags(self, style):
        """
        Returns style-specific tags
        """
        style_mappings = {
            "photography": ["photography", "photorealistic", "detailed", "bokeh"],
            "digital_art": ["digital art", "digital painting", "concept art", "trending on artstation"],
            "painting": ["oil painting", "artistic", "painted", "canvas"],
            "anime": ["anime", "anime style", "manga", "cel shaded"],
            "cinematic": ["cinematic", "dramatic lighting", "film grain", "movie scene"],
            "default": []
        }
        
        return style_mappings.get(style, [])


class TAPromptEnhancer:
    """
    Enhances existing prompts with additional tags and modifiers
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "emphasis_level": (["none", "light", "medium", "strong"], {
                    "default": "medium"
                }),
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "add_negative_defaults": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("enhanced_prompt", "negative_prompt")
    FUNCTION = "enhance"
    CATEGORY = "text/processing"
    
    def enhance(self, prompt, emphasis_level="medium", negative_prompt="", add_negative_defaults=True):
        """
        Enhance prompt with emphasis and negative prompt defaults
        """
        enhanced = prompt
        
        # Füge Emphasis hinzu
        if emphasis_level != "none":
            emphasis_tags = {
                "light": ["detailed", "clear"],
                "medium": ["highly detailed", "intricate", "best quality"],
                "strong": ["extremely detailed", "ultra detailed", "masterpiece", "best quality", "award winning"]
            }
            
            if emphasis_level in emphasis_tags:
                enhanced += ", " + ", ".join(emphasis_tags[emphasis_level])
        
        # Standard Negative Prompt
        neg_prompt = negative_prompt
        if add_negative_defaults:
            default_negatives = [
                "blurry", "bad quality", "low quality", "ugly", "deformed",
                "disfigured", "bad anatomy", "watermark", "text", "signature"
            ]
            if neg_prompt:
                neg_prompt += ", " + ", ".join(default_negatives)
            else:
                neg_prompt = ", ".join(default_negatives)
        
        return (enhanced, neg_prompt)


# Node Registration
NODE_CLASS_MAPPINGS = {
    "TADescriptionToPrompt": TADescriptionToPrompt,
    "TAPromptEnhancer": TAPromptEnhancer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TADescriptionToPrompt": "TA Description to Prompt",
    "TAPromptEnhancer": "TA Prompt Enhancer"
}