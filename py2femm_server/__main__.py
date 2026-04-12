"""Entry point for `python -m py2femm_server`."""

import sys
from pathlib import Path

import click
import uvicorn

from py2femm_server.health import find_femm
from py2femm_server.server import create_app


@click.command()
@click.option("--host", default="0.0.0.0", help="Bind address")
@click.option("--port", default=8082, help="Port number")
@click.option("--femm-path", default=None, help="Path to femm.exe")
@click.option("--workspace", default=None, help="Job workspace directory")
@click.option("--show-femm", is_flag=True, default=False, help="Keep FEMM window visible for debugging")
def serve(host: str, port: int, femm_path: str | None, workspace: str | None, show_femm: bool):
    """Start the py2femm REST server."""
    if femm_path:
        femm = Path(femm_path)
    else:
        femm = find_femm()
    if femm is None or not femm.exists():
        click.echo("Error: FEMM not found. Use --femm-path or set FEMM_PATH env var.", err=True)
        sys.exit(1)

    ws = Path(workspace) if workspace else Path("C:/femm_workspace")
    click.echo(f"FEMM path: {femm}")
    click.echo(f"Workspace: {ws}")
    click.echo(f"Headless: {not show_femm}")
    click.echo(f"Starting py2femm server on {host}:{port}")

    app = create_app(femm_path=femm, workspace=ws, headless=not show_femm)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    serve()
