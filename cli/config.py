"""GameHub CLI 配置"""
import os
from pathlib import Path

API_BASE = os.getenv("GAMEHUB_API", "http://localhost:8000/api/v1")
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "FAC419D6267E1A06BC3CC6B2BD35EE70")
STEAM_ID = os.getenv("STEAM_ID", "76561198332527375")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
