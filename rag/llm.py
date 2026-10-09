"""大模型客户端：通过 Ollama 的 HTTP API 调用本地模型（Llama3 / Qwen 等）。"""
from __future__ import annotations

from typing import Optional

import requests


class OllamaClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 180

    # ---------- 状态 ----------
    def available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def models(self) -> list[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            resp.raise_for_status()
            return [m.get("name", "") for m in resp.json().get("models", [])]
        except requests.RequestException:
            return []

    # ---------- 生成 ----------
    def generate(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """调用 /api/generate 生成回答；失败或超时返回 None。"""
        if not self.available():
            return None
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 8192},
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return (data.get("response") or "").strip() or None
        except requests.RequestException as exc:
            print(f"[llm] Ollama 调用失败：{exc}")
            return None
