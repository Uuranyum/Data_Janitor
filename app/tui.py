"""
tui.py — Data Janitor TUI ana uygulama.
Textual framework ile oluşturulmuş terminal arayüzü.
"""

import os
from textual.app import App
from textual.theme import Theme
from dotenv import load_dotenv

from app.screens.splash import SplashScreen
from app.screens.api_key import ApiKeyScreen
from app.screens.terminal import TerminalScreen
from app.services.llm_service import llm_service


# Özel tema — nostaljik hacker terminal renkleri
JANITOR_THEME = Theme(
    name="janitor",
    primary="#00ff41",       # Matrix yeşili
    secondary="#00d4ff",     # Neon cyan
    accent="#00ff41",
    foreground="#00ff41",
    background="#0a0a0a",    # Derin siyah
    surface="#111111",
    error="#ff0040",
    success="#00ff41",
    warning="#ffb800",
)


class DataJanitorApp(App):
    """Data Janitor — Ana TUI Uygulaması."""

    TITLE = "Data Janitor CLI"
    SUB_TITLE = "Your Data, Spotlessly Clean"

    CSS = """
    Screen {
        background: #0a0a0a;
    }
    """

    SCREENS = {
        "splash": SplashScreen,
        "api_key": ApiKeyScreen,
        "terminal": TerminalScreen,
    }

    def __init__(self, demo_mode: bool = False):
        super().__init__()
        self.demo_mode = demo_mode

    def on_mount(self) -> None:
        """Uygulama başlatıldığında."""
        self.register_theme(JANITOR_THEME)
        self.theme = "janitor"

        # LLM'i arka planda sessizce yapılandır (.env varsa)
        self._auto_configure_llm()

        self.push_screen("splash")

    def _auto_configure_llm(self) -> None:
        """Varsa .env'deki API key ile LLM'i sessizce yapılandır."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        load_dotenv(env_path, override=True)

        for provider, env_key in [("groq", "GROQ_API_KEY"), ("gemini", "GEMINI_API_KEY"), ("openai", "OPENAI_API_KEY")]:
            key = os.getenv(env_key)
            if key and key.strip():
                try:
                    llm_service.configure(provider, key.strip())
                    return  # İlk bulunan ile yapılandır
                except Exception:
                    pass

    def switch_to_next_screen(self) -> None:
        """Splash'tan sonra doğrudan terminal'e geç."""
        self.switch_screen("terminal")

    def switch_to_terminal(self) -> None:
        """Ana terminal ekranına geç."""
        self.switch_screen("terminal")
