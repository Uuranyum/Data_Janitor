"""
llm_service.py — LLM entegrasyon modülü.
OpenAI, Google Gemini ve Groq destekler.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


LLM_PROVIDERS = {
    "openai": "OpenAI (GPT-4o)",
    "gemini": "Google Gemini",
    "groq": "Groq (Llama/Mixtral)",
}

ENV_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
}


class LLMService:
    """LLM servisi — veri temizleme önerileri ve soru-cevap."""

    def __init__(self):
        self.provider: Optional[str] = None
        self.api_key: Optional[str] = None
        self.client = None

    def configure(self, provider: str, api_key: str) -> str:
        """LLM sağlayıcısını yapılandırır."""
        provider = provider.lower().strip()

        if provider not in LLM_PROVIDERS:
            return f"❌ Bilinmeyen sağlayıcı: '{provider}'. Seçenekler: {', '.join(LLM_PROVIDERS.keys())}"

        self.provider = provider
        self.api_key = api_key

        # Save to .env
        env_key = ENV_KEY_MAP[provider]
        self._save_to_env(env_key, api_key)

        # Initialize client
        try:
            self._init_client()
            return f"✅ {LLM_PROVIDERS[provider]} bağlantısı başarılı!"
        except Exception as e:
            return f"❌ Bağlantı hatası: {str(e)}"

    def _init_client(self):
        """LLM client'ı başlatır."""
        if self.provider == "openai":
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)

        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel("gemini-2.0-flash")

        elif self.provider == "groq":
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=self.api_key)

    def _save_to_env(self, key: str, value: str):
        """API key'i .env dosyasına kaydeder."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        
        lines = []
        key_found = False

        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()

        new_lines = []
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f"{key}={value}\n")

        with open(env_path, "w") as f:
            f.writelines(new_lines)

    def is_configured(self) -> bool:
        """LLM yapılandırılmış mı kontrol eder."""
        return self.client is not None

    async def ask(self, question: str, data_context: str = "") -> str:
        """LLM'e soru sorar."""
        if not self.is_configured():
            return "❌ LLM yapılandırılmamış. Önce 'llm setup' komutunu kullanın."

        system_prompt = """Sen bir veri temizleme uzmanısın. 'Data Janitor' adlı bir CLI aracının yapay zeka asistanısın.
Kullanıcıya veri temizleme konusunda yardımcı oluyorsun. Yanıtların kısa, öz ve pratik olsun.
Mümkünse doğrudan kullanılabilecek komutlar öner. Türkçe yanıt ver."""

        user_message = question
        if data_context:
            user_message = f"Veri Bağlamı:\n{data_context}\n\nSoru: {question}"

        try:
            return await self._call_llm(system_prompt, user_message)
        except Exception as e:
            return f"❌ LLM hatası: {str(e)}"

    async def get_cleaning_suggestions(self, data_context: str) -> str:
        """Veri analiz raporuna göre temizleme önerileri alır."""
        if not self.is_configured():
            return ""

        prompt = f"""Aşağıdaki veri analiz raporunu incele ve:
1. En önemli sorunları listele  
2. Her sorun için hangi temizleme adımının uygulanması gerektiğini öner
3. Temizleme sırasını belirt (hangi adım önce yapılmalı)

Kısa ve pratik yanıt ver.

{data_context}"""

        try:
            return await self._call_llm(
                "Sen bir veri temizleme uzmanısın. Türkçe yanıt ver. Kısa ve öz ol.",
                prompt,
            )
        except Exception:
            return ""

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """LLM API çağrısı yapar (asenkron)."""
        if self.provider == "openai":
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content

        elif self.provider == "gemini":
            response = await self.client.generate_content_async(
                f"{system_prompt}\n\n{user_message}"
            )
            return response.text

        elif self.provider == "groq":
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content

        return "❌ LLM sağlayıcısı yapılandırılmamış."


# Global instance
llm_service = LLMService()
