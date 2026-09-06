"""CLI: serve a API HTTP do extrator."""
from __future__ import annotations

import click

from extrator_prop.api.app import create_app


@click.command()
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8000, show_default=True)
@click.option("--debug", is_flag=True, default=False, envvar="FLASK_DEBUG")
def main(host: str, port: int, debug: bool) -> None:
    """Inicia o servidor HTTP do extrator-proprietarios."""
    create_app().run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()

