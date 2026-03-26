"""
terminal.py — Ana terminal ekranı.
Komut girişi, interaktif menü, auto clean, ve veri temizleme işlemleri.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, RichLog
from textual.containers import Vertical, Horizontal
from textual import on, work

import pandas as pd
import numpy as np
import asyncio
from datetime import datetime

from app.services.analyzer import analyze_data, format_report_for_terminal, format_report_for_llm
from app.services.cleaner import clean_missing, clean_duplicates, clean_whitespace, clean_outliers
from app.services.llm_service import llm_service
from app.utils.file_handler import load_file, export_file


WELCOME_TEXT = """[bold bright_green]
╔══════════════════════════════════════════════════════════════════╗
║                    DATA JANITOR TERMINAL                        ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🚀 Hızlı Başlangıç:                                            ║
║    load <dosya_yolu>  →  Dosya yükle, analiz et, menü göster     ║
║                                                                  ║
║  📋 Tüm komutlar için: help                                     ║
║  🤖 LLM önerileri için: llm setup  (opsiyonel)                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
[/bold bright_green]

[dim bright_cyan]💡 Başlamak için bir dosya yükleyin: load dosya_yolu.csv[/dim bright_cyan]
"""

HELP_TEXT = """
[bold bright_cyan]📋 Kullanılabilir Komutlar:[/bold bright_cyan]

[bold]Dosya İşlemleri:[/bold]
  load <yol>                  Dosya yükle (CSV, XLSX, XLS)
  export <yol>                Temizlenmiş veriyi kaydet
  pipeline <yol>              Temizleme adımlarını .py script olarak kaydet

[bold]Veri Görüntüleme:[/bold]
  show head [n]               İlk n satır (varsayılan: 5)
  show tail [n]               Son n satır (varsayılan: 5)
  show info                   Sütun bilgileri ve tipleri
  show report                 Tam analiz raporu + komut önerileri
  show columns                Sütun listesi
  show shape                  Satır ve sütun sayısı
  show describe               İstatistiksel özet
  show profile                Detaylı veri profili

[bold]İnteraktif Temizleme:[/bold]
  menu                        Sorunları numaralı menü olarak göster
  1, 2, 3...                  Menüden seçim yap
  A                           Tüm sorunları otomatik temizle (auto clean)
  auto clean                  LLM destekli akıllı temizleme

[bold]Manuel Temizleme:[/bold]
  clean --missing drop        Eksik satırları sil
  clean --missing fill mean   Ortalama ile doldur
  clean --missing fill median Medyan ile doldur
  clean --missing fill ffill  Önceki değerle doldur
  clean --duplicates          Tekrar eden satırları sil
  clean --whitespace          Boşlukları temizle
  clean --outliers zscore     Z-score ile aykırı değerleri sil
  clean --outliers iqr        IQR ile aykırı değerleri sil

[bold]LLM Asistan:[/bold]
  ask <soru>                  LLM'e veri hakkında soru sor
  llm setup                   LLM sağlayıcısını yapılandır
  llm config <sağlayıcı> <key>  API key yapılandır

[bold]Diğer:[/bold]
  undo                        Son işlemi geri al
  clear                       Ekranı temizle
  help                        Bu menüyü göster
  exit / quit                 Çıkış
"""


class TerminalScreen(Screen):
    """Ana terminal ekranı — Data Janitor'ın kalbi."""

    CSS = """
    TerminalScreen {
        background: $surface;
    }

    #terminal-container {
        width: 100%;
        height: 100%;
    }

    #header-bar {
        width: 100%;
        height: 1;
        background: $accent;
        color: $text;
        text-align: center;
        text-style: bold;
    }

    #output-log {
        width: 100%;
        height: 1fr;
        border: none;
        padding: 0 1;
        scrollbar-size: 1 1;
    }

    #input-container {
        width: 100%;
        height: 3;
        padding: 0 1;
    }

    #prompt-label {
        width: auto;
        height: 3;
        padding: 1 0;
        color: $success;
        text-style: bold;
    }

    #command-input {
        width: 1fr;
        border: none;
        background: $surface;
    }

    #status-bar {
        width: 100%;
        height: 1;
        background: $accent-darken-2;
        color: $text-muted;
        padding: 0 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.df: pd.DataFrame = None
        self.df_history: list = []
        self.report: dict = None
        self.file_path: str = ""
        self.menu_actions: list = []  # Interaktif menü aksiyonları
        self.pipeline_steps: list = []  # Pipeline kaydı
        self.auto_clean_queue: list = []  # Auto clean sırası

    def compose(self) -> ComposeResult:
        with Vertical(id="terminal-container"):
            yield Static(
                " 🧹 DATA JANITOR v1.1.0 — Terminal ",
                id="header-bar",
            )
            yield RichLog(
                highlight=True,
                markup=True,
                wrap=True,
                id="output-log",
            )
            with Horizontal(id="input-container"):
                yield Static("[bold bright_green]❯[/bold bright_green] ", id="prompt-label")
                yield Input(
                    placeholder="Komut girin... (help yazın)",
                    id="command-input",
                )
            yield Static(
                " Dosya: Yüklenmedi | Satır: — | Sütun: — | LLM: —",
                id="status-bar",
            )

    def on_mount(self) -> None:
        log = self.query_one("#output-log", RichLog)
        log.write(WELCOME_TEXT)
        self._update_status_bar()

        # Demo modu: sample_data.csv otomatik yükle
        if hasattr(self.app, 'demo_mode') and self.app.demo_mode:
            self.set_timer(0.5, lambda: self._auto_load_demo(log))

    def _auto_load_demo(self, log: RichLog) -> None:
        """Demo modunda sample_data.csv'yi otomatik yükle."""
        import os
        demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_data.csv")
        if os.path.exists(demo_path):
            self._cmd_load(["load", demo_path], log)

    @on(Input.Submitted, "#command-input")
    def on_command(self, event: Input.Submitted) -> None:
        """Komut girildiğinde."""
        command = event.value.strip()
        input_widget = self.query_one("#command-input", Input)
        input_widget.value = ""

        if not command:
            return

        log = self.query_one("#output-log", RichLog)
        log.write(f"[bold bright_green]❯[/bold bright_green] {command}\n")

        self._process_command(command, log)

    def _process_command(self, command: str, log: RichLog) -> None:
        """Komutu işler."""
        parts = command.strip().split()
        cmd = parts[0].lower() if parts else ""

        # Auto clean onay/red
        if self.auto_clean_queue and cmd in ("e", "evet", "y", "yes"):
            self._execute_next_auto_clean(log)
            return
        elif self.auto_clean_queue and cmd in ("h", "hayir", "n", "no"):
            self._skip_auto_clean_step(log)
            return
        elif self.auto_clean_queue and cmd in ("hepsi", "all"):
            self._execute_all_auto_clean(log)
            return
        elif self.auto_clean_queue and cmd in ("dur", "stop", "iptal"):
            self.auto_clean_queue = []
            log.write("[yellow]⚠ Auto clean iptal edildi.[/yellow]\n")
            return

        # Numaralı menü seçimi
        if cmd.isdigit() and self.menu_actions:
            self._execute_menu_action(int(cmd), log)
            return
        if cmd.upper() == "A" and self.menu_actions:
            self._cmd_auto_clean_all(log)
            return

        # llm config komutu
        if cmd == "llm" and len(parts) >= 4 and parts[1].lower() == "config":
            provider = parts[2]
            api_key = parts[3]
            result = llm_service.configure(provider, api_key)
            log.write(f"{result}\n")
            self._update_status_bar()
            return

        if cmd == "help":
            log.write(HELP_TEXT)
        elif cmd == "clear":
            log.clear()
        elif cmd in ("exit", "quit"):
            self.app.exit()
        elif cmd == "load":
            self._cmd_load(parts, log)
        elif cmd == "show":
            self._cmd_show(parts, log)
        elif cmd == "clean":
            self._cmd_clean(parts, log)
        elif cmd == "ask":
            self._cmd_ask(parts, log)
        elif cmd == "llm":
            self._cmd_llm(parts, log)
        elif cmd == "export":
            self._cmd_export(parts, log)
        elif cmd == "pipeline":
            self._cmd_pipeline(parts, log)
        elif cmd == "undo":
            self._cmd_undo(log)
        elif cmd == "menu":
            self._show_interactive_menu(log)
        elif cmd == "auto" and len(parts) > 1 and parts[1].lower() == "clean":
            self._cmd_auto_clean_all(log)
        else:
            log.write(f"[red]❌ Bilinmeyen komut: '{cmd}'. 'help' yazın.[/red]\n")

    # ══════════════════════════════════════════════════
    #  INTERACTIVE MENU
    # ══════════════════════════════════════════════════

    def _show_interactive_menu(self, log: RichLog) -> None:
        """Tespit edilen sorunları numaralı interaktif menüde göster."""
        if self.df is None:
            log.write("[yellow]⚠ Önce bir dosya yükleyin.[/yellow]\n")
            return

        self.report = analyze_data(self.df)
        self.menu_actions = []

        log.write("\n[bold bright_cyan]╔══════════════════════════════════════════════════════════════╗[/bold bright_cyan]")
        log.write("[bold bright_cyan]║              🔧  İNTERAKTİF TEMİZLEME MENÜSÜ               ║[/bold bright_cyan]")
        log.write("[bold bright_cyan]╚══════════════════════════════════════════════════════════════╝[/bold bright_cyan]\n")

        idx = 1

        if self.report["missing"]["total"] > 0:
            details = self.report["missing"]["details"]
            cols_info = ", ".join([f"{col}({info['count']})" for col, info in list(details.items())[:3]])
            log.write(f"  [bold bright_red][{idx}][/bold bright_red] 🔴 {self.report['missing']['total']} eksik değer → {cols_info}")
            log.write(f"      [dim]Varsayılan: Eksik satırları sil (drop)[/dim]")
            self.menu_actions.append(("missing", "drop"))
            idx += 1

        if self.report["duplicates"]["total"] > 0:
            log.write(f"  [bold bright_yellow][{idx}][/bold bright_yellow] 🟠 {self.report['duplicates']['total']} tekrar eden satır (%{self.report['duplicates']['percentage']})")
            log.write(f"      [dim]Varsayılan: Tekrar eden satırları sil[/dim]")
            self.menu_actions.append(("duplicates", None))
            idx += 1

        if self.report["whitespace"]["total"] > 0:
            details = self.report["whitespace"]["details"]
            cols_info = ", ".join([f"{col}({count})" for col, count in list(details.items())[:3]])
            log.write(f"  [bold bright_yellow][{idx}][/bold bright_yellow] 🟡 {self.report['whitespace']['total']} gereksiz boşluk → {cols_info}")
            log.write(f"      [dim]Varsayılan: Boşlukları temizle[/dim]")
            self.menu_actions.append(("whitespace", None))
            idx += 1

        if self.report["outliers"]["total"] > 0:
            details = self.report["outliers"]["details"]
            cols_info = ", ".join([f"{col}({count})" for col, count in list(details.items())[:3]])
            log.write(f"  [bold bright_magenta][{idx}][/bold bright_magenta] 🟣 {self.report['outliers']['total']} aykırı değer → {cols_info}")
            log.write(f"      [dim]Varsayılan: Z-score ile sil[/dim]")
            self.menu_actions.append(("outliers", "zscore"))
            idx += 1

        if not self.menu_actions:
            log.write("  [bold bright_green]✅ Veri temiz! Sorun tespit edilmedi.[/bold bright_green]\n")
            return

        log.write("")
        log.write(f"  [bold bright_green][A][/bold bright_green] 🚀 Hepsini otomatik temizle (tek seferde)")
        log.write("")
        log.write("[dim]──────────────────────────────────────────────────────────────[/dim]")
        log.write("[dim]  Numara girin (1-{}) veya A yazın  |  'help' tüm komutlar[/dim]".format(len(self.menu_actions)))
        log.write("[dim]──────────────────────────────────────────────────────────────[/dim]\n")

    def _execute_menu_action(self, num: int, log: RichLog) -> None:
        """Menüden seçilen numarayı çalıştır."""
        if num < 1 or num > len(self.menu_actions):
            log.write(f"[yellow]⚠ Geçersiz seçim. 1-{len(self.menu_actions)} arası girin.[/yellow]\n")
            return

        action_type, method = self.menu_actions[num - 1]

        # Geçmişe kaydet
        self.df_history.append(self.df.copy())
        before_shape = self.df.shape[0]

        if action_type == "missing":
            self.df, msg = clean_missing(self.df, method or "drop")
            self.pipeline_steps.append(f"df = df.dropna()  # Eksik değerleri sil")
        elif action_type == "duplicates":
            self.df, msg = clean_duplicates(self.df)
            self.pipeline_steps.append(f"df = df.drop_duplicates()  # Tekrar edenleri sil")
        elif action_type == "whitespace":
            self.df, msg = clean_whitespace(self.df)
            self.pipeline_steps.append(f"df[obj_cols] = df[obj_cols].apply(lambda x: x.str.strip())  # Boşlukları temizle")
        elif action_type == "outliers":
            self.df, msg = clean_outliers(self.df, method or "zscore")
            self.pipeline_steps.append(f"# Z-score ile aykırı değerleri sil")

        log.write(f"{msg}\n")
        self._show_before_after(before_shape, log)
        self._update_status_bar()

        # Menüyü güncelle
        self._show_interactive_menu(log)

    # ══════════════════════════════════════════════════
    #  AUTO CLEAN
    # ══════════════════════════════════════════════════

    def _cmd_auto_clean_all(self, log: RichLog) -> None:
        """Tüm sorunları adım adım otomatik temizle."""
        if self.df is None:
            log.write("[yellow]⚠ Önce bir dosya yükleyin.[/yellow]\n")
            return

        self.report = analyze_data(self.df)

        # Temizleme sırasını oluştur (en güvenliden en riskli)
        self.auto_clean_queue = []

        if self.report["whitespace"]["total"] > 0:
            self.auto_clean_queue.append({
                "type": "whitespace",
                "label": f"🟡 {self.report['whitespace']['total']} gereksiz boşluk temizlenecek",
                "method": None,
            })

        if self.report["duplicates"]["total"] > 0:
            self.auto_clean_queue.append({
                "type": "duplicates",
                "label": f"🟠 {self.report['duplicates']['total']} tekrar eden satır silinecek",
                "method": None,
            })

        if self.report["missing"]["total"] > 0:
            self.auto_clean_queue.append({
                "type": "missing",
                "label": f"🔴 {self.report['missing']['total']} eksik değerli satır silinecek",
                "method": "drop",
            })

        if self.report["outliers"]["total"] > 0:
            self.auto_clean_queue.append({
                "type": "outliers",
                "label": f"🟣 {self.report['outliers']['total']} aykırı değer silinecek (Z-score)",
                "method": "zscore",
            })

        if not self.auto_clean_queue:
            log.write("[green]✅ Veri zaten temiz! Sorun yok.[/green]\n")
            return

        log.write("\n[bold bright_cyan]╔══════════════════════════════════════════════════════════════╗[/bold bright_cyan]")
        log.write("[bold bright_cyan]║              🚀  OTOMATİK TEMİZLEME MODU                   ║[/bold bright_cyan]")
        log.write("[bold bright_cyan]╚══════════════════════════════════════════════════════════════╝[/bold bright_cyan]\n")
        log.write(f"  Toplam {len(self.auto_clean_queue)} adım uygulanacak.\n")

        self._show_next_auto_clean_step(log)

    def _show_next_auto_clean_step(self, log: RichLog) -> None:
        """Sıradaki auto clean adımını göster."""
        if not self.auto_clean_queue:
            log.write("\n[bold bright_green]🎉 Otomatik temizleme tamamlandı![/bold bright_green]")
            log.write(f"[dim]📊 Son durum: {self.df.shape[0]} satır × {self.df.shape[1]} sütun[/dim]\n")
            log.write("[dim]'export <dosya>' ile temizlenmiş veriyi kaydedin.[/dim]\n")
            log.write("[dim]'pipeline <dosya>' ile temizleme adımlarını .py olarak kaydedin.[/dim]\n")
            return

        step = self.auto_clean_queue[0]
        remaining = len(self.auto_clean_queue)

        log.write(f"\n  [bold]Adım {len(self.pipeline_steps) + 1}[/bold] ({remaining} adım kaldı)")
        log.write(f"  {step['label']}")
        log.write("")
        log.write("  [bold bright_yellow][E][/bold bright_yellow] Evet, uygula   [bold bright_red][H][/bold bright_red] Hayır, atla   [bold bright_green][Hepsi][/bold bright_green] Kalanların hepsini uygula   [bold][Dur][/bold] İptal\n")

    def _execute_next_auto_clean(self, log: RichLog) -> None:
        """Sıradaki auto clean adımını çalıştır."""
        if not self.auto_clean_queue:
            return

        step = self.auto_clean_queue.pop(0)
        self.df_history.append(self.df.copy())
        before_shape = self.df.shape[0]

        if step["type"] == "whitespace":
            self.df, msg = clean_whitespace(self.df)
            self.pipeline_steps.append("# Boşlukları temizle\nfor col in df.select_dtypes(include=['object']).columns:\n    df[col] = df[col].str.strip()")
        elif step["type"] == "duplicates":
            self.df, msg = clean_duplicates(self.df)
            self.pipeline_steps.append("df = df.drop_duplicates()  # Tekrar edenleri sil")
        elif step["type"] == "missing":
            self.df, msg = clean_missing(self.df, step["method"])
            self.pipeline_steps.append("df = df.dropna()  # Eksik değerleri sil")
        elif step["type"] == "outliers":
            self.df, msg = clean_outliers(self.df, step["method"])
            self.pipeline_steps.append("# Z-score ile aykırı değerleri sil\nfrom scipy import stats\ndf = df[(np.abs(stats.zscore(df.select_dtypes(include=[np.number]))) < 3).all(axis=1)]")

        log.write(f"  {msg}")
        self._show_before_after(before_shape, log)
        self._update_status_bar()
        self._show_next_auto_clean_step(log)

    def _skip_auto_clean_step(self, log: RichLog) -> None:
        """Auto clean adımını atla."""
        step = self.auto_clean_queue.pop(0)
        log.write(f"  [dim]⏭ Atlandı: {step['label']}[/dim]\n")
        self._show_next_auto_clean_step(log)

    def _execute_all_auto_clean(self, log: RichLog) -> None:
        """Kalan tüm auto clean adımlarını çalıştır."""
        log.write("  [bold]🚀 Kalan tüm adımlar uygulanıyor...[/bold]\n")
        while self.auto_clean_queue:
            self._execute_next_auto_clean(log)

    # ══════════════════════════════════════════════════
    #  BEFORE / AFTER COMPARISON
    # ══════════════════════════════════════════════════

    def _show_before_after(self, before_rows: int, log: RichLog) -> None:
        """Her temizleme sonrası önce/sonra karşılaştırma."""
        after_rows = self.df.shape[0]
        diff = before_rows - after_rows
        pct = round(diff / before_rows * 100, 1) if before_rows > 0 else 0

        if diff > 0:
            log.write(f"  [dim]📊 Önce: {before_rows} satır → Sonra: {after_rows} satır ({diff} satır silindi, %{pct})[/dim]\n")
        elif diff == 0:
            remaining_issues = self.df.isnull().sum().sum()
            log.write(f"  [dim]📊 Satır sayısı değişmedi: {after_rows} | Kalan eksik: {remaining_issues}[/dim]\n")

    # ══════════════════════════════════════════════════
    #  LOAD
    # ══════════════════════════════════════════════════

    def _cmd_load(self, parts: list, log: RichLog) -> None:
        if len(parts) < 2:
            log.write("[yellow]⚠ Kullanım: load <dosya_yolu>[/yellow]\n")
            return

        file_path = " ".join(parts[1:])
        try:
            log.write(f"[dim]📂 Dosya yükleniyor: {file_path}...[/dim]\n")
            self.df = load_file(file_path)
            self.df_history = []
            self.pipeline_steps = []
            self.file_path = file_path
            log.write(f"[green]✅ Dosya başarıyla yüklendi! ({self.df.shape[0]} satır, {self.df.shape[1]} sütun)[/green]\n")

            # Otomatik analiz + interaktif menü
            log.write("[dim]🔍 Veri analiz ediliyor...[/dim]\n")
            self.report = analyze_data(self.df)
            report_text = format_report_for_terminal(self.report)
            log.write(report_text + "\n")

            # Update status bar before launching LLM suggestion task
            self._update_status_bar()

            # LLM önerileri ve menü gösterimini arka plana al
            self._fetch_llm_suggestions_and_show_menu(log)

        except FileNotFoundError as e:
            log.write(f"[red]❌ {str(e)}[/red]\n")
        except ValueError as e:
            log.write(f"[red]❌ {str(e)}[/red]\n")
        except Exception as e:
            log.write(f"[red]❌ Dosya yüklenirken hata: {str(e)}[/red]\n")

    @work
    async def _fetch_llm_suggestions_and_show_menu(self, log: RichLog) -> None:
        """LLM önerilerini asenkron olarak çeker ve interaktif menüyü gösterir."""
        if llm_service.is_configured():
            log.write("[dim]🤖 LLM'den öneriler alınıyor (arayüz donmayacak)...[/dim]\n")
            context = format_report_for_llm(self.report, self.df)
            suggestions = await llm_service.get_cleaning_suggestions(context)
            if suggestions:
                log.write(f"\n[bold bright_cyan]🤖 LLM Önerileri:[/bold bright_cyan]\n{suggestions}\n")

        # Interaktif menüyü göster
        self._show_interactive_menu(log)


    # ══════════════════════════════════════════════════
    #  SHOW
    # ══════════════════════════════════════════════════

    def _cmd_show(self, parts: list, log: RichLog) -> None:
        if self.df is None:
            log.write("[yellow]⚠ Önce bir dosya yükleyin: load <dosya_yolu>[/yellow]\n")
            return

        sub = parts[1].lower() if len(parts) > 1 else "head"

        if sub == "head":
            n = int(parts[2]) if len(parts) > 2 else 5
            log.write(f"\n[bold]📋 İlk {n} satır:[/bold]\n")
            log.write(self.df.head(n).to_string() + "\n")

        elif sub == "tail":
            n = int(parts[2]) if len(parts) > 2 else 5
            log.write(f"\n[bold]📋 Son {n} satır:[/bold]\n")
            log.write(self.df.tail(n).to_string() + "\n")

        elif sub == "info":
            log.write(f"\n[bold]📋 Veri Bilgisi:[/bold]\n")
            info_lines = []
            for col in self.df.columns:
                non_null = self.df[col].notna().sum()
                dtype = self.df[col].dtype
                info_lines.append(f"  {col:<30} {non_null:>6} non-null    {dtype}")
            log.write("\n".join(info_lines) + "\n")

        elif sub == "report":
            self.report = analyze_data(self.df)
            report_text = format_report_for_terminal(self.report)
            log.write(report_text + "\n")

        elif sub == "columns":
            log.write(f"\n[bold]📋 Sütunlar ({len(self.df.columns)}):[/bold]\n")
            for i, col in enumerate(self.df.columns, 1):
                log.write(f"  {i}. {col} ({self.df[col].dtype})\n")

        elif sub == "shape":
            log.write(f"\n[bold]📋 Boyut:[/bold] {self.df.shape[0]} satır × {self.df.shape[1]} sütun\n")

        elif sub == "describe":
            log.write(f"\n[bold]📋 İstatistiksel Özet:[/bold]\n")
            log.write(self.df.describe().to_string() + "\n")

        elif sub == "profile":
            self._cmd_profile(log)

        else:
            log.write(f"[yellow]⚠ Bilinmeyen: '{sub}'. show head/tail/info/report/columns/shape/describe/profile[/yellow]\n")

    # ══════════════════════════════════════════════════
    #  DATA PROFILE
    # ══════════════════════════════════════════════════

    def _cmd_profile(self, log: RichLog) -> None:
        """Zengin veri profili."""
        log.write("\n[bold bright_cyan]╔══════════════════════════════════════════════════════════════╗[/bold bright_cyan]")
        log.write("[bold bright_cyan]║                  📊  VERİ PROFİLİ                           ║[/bold bright_cyan]")
        log.write("[bold bright_cyan]╚══════════════════════════════════════════════════════════════╝[/bold bright_cyan]\n")

        for col in self.df.columns:
            dtype = self.df[col].dtype
            non_null = self.df[col].notna().sum()
            null_count = self.df[col].isnull().sum()
            null_pct = round(null_count / len(self.df) * 100, 1) if len(self.df) > 0 else 0
            unique = self.df[col].nunique()

            log.write(f"  [bold bright_green]▸ {col}[/bold bright_green] ({dtype})")
            log.write(f"    Dolu: {non_null} | Boş: {null_count} (%{null_pct}) | Benzersiz: {unique}")

            if pd.api.types.is_numeric_dtype(self.df[col]):
                stats = self.df[col].describe()
                log.write(f"    Min: {stats['min']:.2f} | Max: {stats['max']:.2f} | Ort: {stats['mean']:.2f} | Std: {stats['std']:.2f}")
            elif pd.api.types.is_object_dtype(self.df[col]):
                top_vals = self.df[col].value_counts().head(3)
                top_str = " | ".join([f"{val}({count})" for val, count in top_vals.items()])
                log.write(f"    En sık: {top_str}")

            log.write("")

    # ══════════════════════════════════════════════════
    #  CLEAN
    # ══════════════════════════════════════════════════

    def _cmd_clean(self, parts: list, log: RichLog) -> None:
        if self.df is None:
            log.write("[yellow]⚠ Önce bir dosya yükleyin: load <dosya_yolu>[/yellow]\n")
            return

        if len(parts) < 2:
            log.write("[yellow]⚠ Kullanım: clean --missing/--duplicates/--whitespace/--outliers[/yellow]\n")
            return

        self.df_history.append(self.df.copy())
        before_shape = self.df.shape[0]
        flag = parts[1].lower().lstrip("-")

        if flag == "missing":
            method = " ".join(parts[2:]) if len(parts) > 2 else "drop"
            self.df, msg = clean_missing(self.df, method)
            self.pipeline_steps.append(f"# clean --missing {method}")

        elif flag == "duplicates":
            self.df, msg = clean_duplicates(self.df)
            self.pipeline_steps.append("df = df.drop_duplicates()")

        elif flag == "whitespace":
            self.df, msg = clean_whitespace(self.df)
            self.pipeline_steps.append("# Boşlukları temizle\nfor col in df.select_dtypes(include=['object']).columns:\n    df[col] = df[col].str.strip()")

        elif flag == "outliers":
            method = parts[2] if len(parts) > 2 else "zscore"
            self.df, msg = clean_outliers(self.df, method)
            self.pipeline_steps.append(f"# Aykırı değerleri sil ({method})")

        else:
            self.df_history.pop()
            log.write(f"[yellow]⚠ Bilinmeyen temizleme: '--{flag}'[/yellow]\n")
            return

        log.write(f"{msg}\n")
        self._show_before_after(before_shape, log)
        self._update_status_bar()

    # ══════════════════════════════════════════════════
    #  ASK
    # ══════════════════════════════════════════════════

    def _cmd_ask(self, parts: list, log: RichLog) -> None:
        if len(parts) < 2:
            log.write("[yellow]⚠ Kullanım: ask <soru>[/yellow]\n")
            return

        if not llm_service.is_configured():
            log.write("[yellow]⚠ LLM yapılandırılmamış. 'llm setup' komutunu kullanın.[/yellow]\n")
            return

        question = " ".join(parts[1:])
        log.write(f"[dim]🤖 LLM düşünüyor (arayüz donmayacak)...[/dim]\n")

        context = ""
        if self.df is not None and self.report:
            context = format_report_for_llm(self.report, self.df)

        # Arka planda çalıştır
        self._async_ask(question, context, log)

    @work
    async def _async_ask(self, question: str, context: str, log: RichLog) -> None:
        response = await llm_service.ask(question, context)
        log.write(f"\n[bold bright_cyan]🤖 LLM Yanıtı:[/bold bright_cyan]\n{response}\n")

    # ══════════════════════════════════════════════════
    #  LLM SETUP
    # ══════════════════════════════════════════════════

    def _cmd_llm(self, parts: list, log: RichLog) -> None:
        if len(parts) < 2:
            log.write("[yellow]⚠ Kullanım: llm setup veya llm config <sağlayıcı> <key>[/yellow]\n")
            return

        sub = parts[1].lower()

        if sub == "setup":
            log.write("""
[bold bright_cyan]🔑 LLM Yapılandırması (Opsiyonel)[/bold bright_cyan]
LLM olmadan da tüm temizleme özelliklerini kullanabilirsiniz.
LLM, veri hakkında akıllı öneriler ve soru-cevap sağlar.

Aşağıdaki formatı kullanın:
  llm config openai sk-abc123...
  llm config gemini AIza...
  llm config groq gsk_...

Sağlayıcılar: openai, gemini, groq
""")
        else:
            log.write(f"[yellow]⚠ Bilinmeyen: 'llm {sub}'. 'llm setup' veya 'llm config' kullanın.[/yellow]\n")

    # ══════════════════════════════════════════════════
    #  EXPORT & PIPELINE
    # ══════════════════════════════════════════════════

    def _cmd_export(self, parts: list, log: RichLog) -> None:
        if self.df is None:
            log.write("[yellow]⚠ Önce bir dosya yükleyin.[/yellow]\n")
            return

        if len(parts) < 2:
            log.write("[yellow]⚠ Kullanım: export <dosya_yolu>[/yellow]\n")
            return

        file_path = " ".join(parts[1:])
        try:
            saved_path = export_file(self.df, file_path)
            log.write(f"[green]✅ Veri kaydedildi: {saved_path}[/green]\n")
        except Exception as e:
            log.write(f"[red]❌ Kaydetme hatası: {str(e)}[/red]\n")

    def _cmd_pipeline(self, parts: list, log: RichLog) -> None:
        """Temizleme adımlarını .py script olarak kaydet."""
        if not self.pipeline_steps:
            log.write("[yellow]⚠ Henüz temizleme adımı yok. Önce veriyi temizleyin.[/yellow]\n")
            return

        if len(parts) < 2:
            log.write("[yellow]⚠ Kullanım: pipeline <dosya_yolu.py>[/yellow]\n")
            return

        file_path = " ".join(parts[1:])
        if not file_path.endswith(".py"):
            file_path += ".py"

        # Pipeline script oluştur
        source_file = self.file_path.replace("\\", "/") if self.file_path else "data.csv"
        script = f'''"""
Data Cleaning Pipeline
Generated by Data Janitor CLI on {datetime.now().strftime("%Y-%m-%d %H:%M")}
Source: {source_file}
"""

import pandas as pd
import numpy as np

# Veriyi yükle
df = pd.read_csv("{source_file}")
print(f"Yüklendi: {{df.shape[0]}} satır, {{df.shape[1]}} sütun")

# ─── Temizleme Adımları ───
'''
        for i, step in enumerate(self.pipeline_steps, 1):
            script += f"\n# Adım {i}\n{step}\nprint(f\"Adım {i} tamamlandı: {{df.shape[0]}} satır\")\n"

        script += f'''
# ─── Sonucu Kaydet ───
output_path = "cleaned_{source_file.split("/")[-1]}"
df.to_csv(output_path, index=False)
print(f"\\nTemizlenmiş veri kaydedildi: {{output_path}}")
print(f"Son durum: {{df.shape[0]}} satır, {{df.shape[1]}} sütun")
'''

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(script)
            log.write(f"[green]✅ Pipeline kaydedildi: {file_path}[/green]\n")
            log.write(f"[dim]Çalıştırmak için: python {file_path}[/dim]\n")
        except Exception as e:
            log.write(f"[red]❌ Kaydetme hatası: {str(e)}[/red]\n")

    # ══════════════════════════════════════════════════
    #  UNDO
    # ══════════════════════════════════════════════════

    def _cmd_undo(self, log: RichLog) -> None:
        if not self.df_history:
            log.write("[yellow]⚠ Geri alınacak işlem yok.[/yellow]\n")
            return

        before_shape = self.df.shape[0]
        self.df = self.df_history.pop()
        if self.pipeline_steps:
            self.pipeline_steps.pop()
        log.write(f"[green]↩ Son işlem geri alındı.[/green]")
        log.write(f"[dim]📊 Önce: {before_shape} satır → Sonra: {self.df.shape[0]} satır[/dim]\n")
        self._update_status_bar()

    # ══════════════════════════════════════════════════
    #  STATUS BAR
    # ══════════════════════════════════════════════════

    def _update_status_bar(self) -> None:
        status = self.query_one("#status-bar", Static)
        file_name = self.file_path.split("\\")[-1].split("/")[-1] if self.file_path else "Yüklenmedi"
        rows = str(self.df.shape[0]) if self.df is not None else "—"
        cols = str(self.df.shape[1]) if self.df is not None else "—"
        llm_status = "✅ Aktif" if llm_service.is_configured() else "💡 llm setup"
        steps = len(self.pipeline_steps)

        status.update(f" 📄 {file_name} | 📊 {rows}×{cols} | 🤖 {llm_status} | 🔧 Adım: {steps}")
