import logging
import google.generativeai as genai
from core.config import API_KEYS, ACTIVE_MODEL_NAME, MODEL_FALLBACK_ORDER

logger = logging.getLogger("needhi.gemini")

def generate_gemini_content(prompt_or_parts, generation_config=None, stream=False, system_instruction=None):
    global API_KEYS
    models_to_try = [ACTIVE_MODEL_NAME] + [m for m in MODEL_FALLBACK_ORDER if m != ACTIVE_MODEL_NAME]
    
    # Safety settings - use robust block levels for production safety
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    
    # Try all configured API keys
    for idx, api_key in enumerate(API_KEYS):
        try:
            genai.configure(api_key=api_key)
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                    kwargs = {}
                    if generation_config:
                        kwargs["generation_config"] = generation_config
                    
                    kwargs["safety_settings"] = safety_settings
                    
                    if stream:
                        res = model.generate_content(prompt_or_parts, stream=True, **kwargs)
                    else:
                        res = model.generate_content(prompt_or_parts, **kwargs)
                        
                    # Promote the working key to the front of API_KEYS to make subsequent calls fast
                    if idx > 0:
                        working_key = API_KEYS.pop(idx)
                        API_KEYS.insert(0, working_key)
                        
                    return res, model_name
                except Exception as e:
                    err_str = str(e)
                    # If this key is rate-limited (429) or invalid (400, 401), break to the next key immediately
                    if "429" in err_str or "API_KEY_INVALID" in err_str or "400" in err_str or "401" in err_str:
                        break
                    continue
        except Exception:
            continue
            
    # Ultimate fallback with primary key and primary model
    genai.configure(api_key=API_KEYS[0])
    model = genai.GenerativeModel(models_to_try[0], system_instruction=system_instruction)
    kwargs = {}
    if generation_config:
        kwargs["generation_config"] = generation_config
    kwargs["safety_settings"] = safety_settings
    if stream:
        return model.generate_content(prompt_or_parts, stream=True, **kwargs), models_to_try[0]
    return model.generate_content(prompt_or_parts, **kwargs), models_to_try[0]
