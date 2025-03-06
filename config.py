import os
from routes.utils.config_service import (
    ConfigManager, 
    get_openai_api_key, 
    get_line_config, 
    get_active_bot_style, 
    get_llm_settings, 
    is_rag_enabled,
    is_web_search_enabled,
    get_serpapi_key
)

# This file simply forwards the configuration utils
# All functions are now imported from routes/utils/config_service.py
