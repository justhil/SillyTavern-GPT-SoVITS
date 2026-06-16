import requests
from typing import Dict, Optional
from phone_call_utils.response_parser import EmotionSegment

from config import get_sovits_host, get_tts_engine
from services.genie_bridge import prepare_genie_session, is_genie_engine
from services.genie_tts_client import synthesize as genie_synthesize


class TTSService:
    """TTS 封装 — 默认 Genie API"""

    def __init__(self, host: str = None):
        self.sovits_host = host or get_sovits_host()

    async def generate_audio(
        self,
        segment: EmotionSegment,
        ref_audio: Dict,
        tts_config: Dict,
        previous_ref_audio: Optional[Dict] = None,
        char_name: Optional[str] = None,
    ) -> bytes:
        if is_genie_engine():
            if not char_name:
                raise ValueError("Genie 模式需要 char_name")
            host, gname = prepare_genie_session(
                char_name,
                ref_audio["path"],
                ref_audio.get("text", ""),
                tts_config.get("prompt_lang", "zh"),
            )
            return genie_synthesize(
                host,
                gname,
                segment.text,
                split_sentence=tts_config.get("split_sentence", False),
            )

        url = f"{self.sovits_host}/tts"
        params = {
            "text": segment.text,
            "text_lang": tts_config.get("text_lang", "zh"),
            "ref_audio_path": ref_audio["path"],
            "prompt_text": ref_audio["text"],
            "prompt_lang": tts_config.get("prompt_lang", "zh"),
            "text_split_method": tts_config.get("text_split_method", "cut4"),
            "streaming_mode": "false",
        }
        if segment.speed is not None:
            params["speed_factor"] = segment.speed
        response = requests.get(url, params=params, timeout=120, proxies={"http": None, "https": None})
        if response.status_code != 200:
            raise Exception(f"TTS Error: {response.status_code}")
        return response.content