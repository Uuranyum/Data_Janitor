"""
splash.py — DATA JANITOR ASCII art splash screen.
Nostaljik, renkli giriş ekranı.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container, Center, Middle
from textual import events
import asyncio


SPLASH_ART = r"""
[bold bright_green]
 ██████╗  █████╗ ████████╗ █████╗          
 ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗         
 ██║  ██║███████║   ██║   ███████║         
 ██║  ██║██╔══██║   ██║   ██╔══██║         
 ██████╔╝██║  ██║   ██║   ██║  ██║         
 ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝         
[/bold bright_green]
[bold bright_cyan]
      ██╗ █████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗ 
      ██║██╔══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗
      ██║███████║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝
 ██   ██║██╔══██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗
 ╚█████╔╝██║  ██║██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
[/bold bright_cyan]"""


TAGLINE = """[dim bright_white]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            🧹  Your Data, Spotlessly Clean  🧹
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[/dim bright_white]"""


VERSION_INFO = "[dim]v1.0.0 | Python CLI | github.com/data-janitor-cli[/dim]"

PRESS_KEY = "[blink bold bright_yellow]》 Devam etmek için herhangi bir tuşa basın... 《[/blink bold bright_yellow]"


class SplashScreen(Screen):
    """Nostaljik splash screen."""

    CSS = """
    SplashScreen {
        background: $surface;
        align: center middle;
    }

    #splash-container {
        width: 100%;
        height: 100%;
        align: center middle;
        content-align: center middle;
    }

    #splash-art {
        text-align: center;
        width: auto;
        height: auto;
        content-align: center middle;
    }

    #tagline {
        text-align: center;
        width: auto;
        margin-top: 1;
    }

    #version {
        text-align: center;
        width: auto;
        margin-top: 1;
    }

    #press-key {
        text-align: center;
        width: auto;
        margin-top: 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.art_displayed = False

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                yield Static(SPLASH_ART, id="splash-art")
                yield Static(TAGLINE, id="tagline")
                yield Static(VERSION_INFO, id="version")
                yield Static(PRESS_KEY, id="press-key")

    async def on_mount(self) -> None:
        """Ekran yüklendiğinde animasyon."""
        press_key = self.query_one("#press-key")
        press_key.display = False

        # Kısa bir gecikme sonra "press key" göster
        await asyncio.sleep(1.5)
        press_key.display = True
        self.art_displayed = True

    def on_key(self, event: events.Key) -> None:
        """Herhangi bir tuşa basılınca sonraki ekrana geç."""
        if self.art_displayed:
            self.app.switch_to_next_screen()
