"""PyInstaller entry point; the app also runs with python -m app."""
from app.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
