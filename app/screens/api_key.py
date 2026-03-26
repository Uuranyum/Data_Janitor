"""
api_key.py — LLM API Key yapılandırma ekranı.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, Select
from textual.containers import Center, Middle, Vertical
from textual import events, on
from app.services.llm_service import llm_service, LLM_PROVIDERS

import os
from dotenv import load_dotenv


class ApiKeyScreen(Screen):
    """LLM sağlayıcı seçimi ve API key girişi ekranı."""

    CSS = """
    ApiKeyScreen {
        background: $surface;
        align: center middle;
    }

    #api-container {
        width: 80;
        height: auto;
        border: heavy $accent;
        padding: 2 4;
        background: $surface-darken-1;
    }

    #api-title {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }

    #api-desc {
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }

    #provider-label {
        margin-top: 1;
        margin-bottom: 0;
    }

    #key-label {
        margin-top: 1;
        margin-bottom: 0;
    }

    #api-status {
        text-align: center;
        margin-top: 1;
    }

    #skip-hint {
        text-align: center;
        margin-top: 2;
        color: $text-muted;
    }

    Select {
        width: 100%;
        margin-top: 0;
    }

    Input {
        width: 100%;
        margin-top: 0;
    }
    """

    def __init__(self):
        super().__init__()
        self.selected_provider = "openai"

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Vertical(id="api-container"):
                    yield Static(
                        "[bold bright_cyan]🔑 LLM Yapılandırması[/bold bright_cyan]",
                        id="api-title",
                    )
                    yield Static(
                        "[dim]Veri temizleme önerileri için bir LLM sağlayıcısı seçin.[/dim]",
                        id="api-desc",
                    )
                    yield Static("[bold]Sağlayıcı:[/bold]", id="provider-label")
                    yield Select(
                        [(name, key) for key, name in LLM_PROVIDERS.items()],
                        id="provider-select",
                        value="openai",
                    )
                    yield Static("[bold]API Key:[/bold]", id="key-label")
                    yield Input(
                        placeholder="sk-... veya API anahtarınızı yapıştırın",
                        password=True,
                        id="api-key-input",
                    )
                    yield Static("", id="api-status")
                    yield Static(
                        "[dim italic]ESC tuşu ile LLM olmadan devam edebilirsiniz[/dim italic]",
                        id="skip-hint",
                    )

    def on_mount(self) -> None:
        """Daha önce kaydedilmiş key var mı kontrol et."""
        # .env dosyasındaki değerleri sistem env'den öncelikli yap
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        load_dotenv(env_path, override=True)

        # Groq'u önce kontrol et, sonra diğerlerini
        for provider, env_key_name in [("groq", "GROQ_API_KEY"), ("gemini", "GEMINI_API_KEY"), ("openai", "OPENAI_API_KEY")]:
            key = os.getenv(env_key_name)
            if key and key.strip():
                result = llm_service.configure(provider, key.strip())
                if "başarılı" in result:
                    status = self.query_one("#api-status")
                    status.update(f"[green]{result}\nÖnceki oturumdan yüklendi. Enter ile devam edin.[/green]")
                    return

    @on(Select.Changed, "#provider-select")
    def on_provider_change(self, event: Select.Changed) -> None:
        self.selected_provider = str(event.value)

    @on(Input.Submitted, "#api-key-input")
    def on_key_submit(self, event: Input.Submitted) -> None:
        """API key girildiğinde."""
        api_key = event.value.strip()
        status = self.query_one("#api-status")

        if not api_key:
            # Eğer zaten yapılandırılmışsa devam et
            if llm_service.is_configured():
                self.app.switch_to_terminal()
                return
            status.update("[yellow]⚠ API key boş. ESC ile atlayabilirsiniz.[/yellow]")
            return

        status.update("[dim]Bağlantı test ediliyor...[/dim]")
        result = llm_service.configure(self.selected_provider, api_key)
        status.update(f"[green]{result}[/green]" if "başarılı" in result else f"[red]{result}[/red]")

        if llm_service.is_configured():
            # 1 saniye sonra terminal ekranına geç
            self.set_timer(1.5, self.app.switch_to_terminal)

    def on_key(self, event: events.Key) -> None:
        """ESC ile LLM yapılandırmasını atla."""
        if event.key == "escape":
            self.app.switch_to_terminal()
