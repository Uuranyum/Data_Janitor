"""
Data Janitor CLI — Your Data, Spotlessly Clean
Ana giriş noktası.
"""

import sys
from app.tui import DataJanitorApp


def main():
    demo_mode = "--demo" in sys.argv
    app = DataJanitorApp(demo_mode=demo_mode)
    app.run()


if __name__ == "__main__":
    main()
