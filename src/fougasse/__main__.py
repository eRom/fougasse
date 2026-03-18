"""Entry point for `python -m fougasse`."""

from fougasse import __version__


def main() -> None:
    print(f"Fougasse v{__version__} — Memoire persistante locale pour LLM")
    print("Usage: fougasse --help")


if __name__ == "__main__":
    main()
