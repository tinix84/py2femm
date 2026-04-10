"""py2femm CLI — command-line interface for FEMM simulation automation."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from py2femm.client import FemmClient


@click.group()
def main():
    """py2femm — Python automation for FEMM simulations."""


@main.command()
@click.argument("lua_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="Save results to file")
@click.option("--timeout", "-t", type=int, default=300, help="Timeout in seconds")
@click.option("--mode", type=click.Choice(["auto", "local", "remote"]), default="auto")
@click.option("--url", default=None, help="Agent URL for remote mode")
def run(lua_file: str, output: str | None, timeout: int, mode: str, url: str | None):
    """Run a FEMM Lua script and return results."""
    lua_script = Path(lua_file).read_text(encoding="utf-8")

    kwargs = {}
    if mode != "auto":
        kwargs["mode"] = mode
    if url:
        kwargs["url"] = url

    try:
        client = FemmClient(**kwargs)
    except ConnectionError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    result = client.run(lua_script, timeout=timeout)

    if result.error:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

    if output:
        Path(output).write_text(result.csv_data, encoding="utf-8")
        click.echo(f"Results saved to {output}")
    else:
        click.echo(result.csv_data)


@main.command()
@click.option("--mode", type=click.Choice(["auto", "local", "remote"]), default="auto")
@click.option("--url", default=None, help="Agent URL for remote mode")
def status(mode: str, url: str | None):
    """Check py2femm agent status."""
    kwargs = {}
    if mode != "auto":
        kwargs["mode"] = mode
    if url:
        kwargs["url"] = url

    try:
        client = FemmClient(**kwargs)
        info = client.status()
        for key, value in info.items():
            click.echo(f"  {key}: {value}")
    except ConnectionError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command("run-batch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--output-dir", "-o", type=click.Path(), default=None, help="Directory for results")
@click.option("--timeout", "-t", type=int, default=300, help="Timeout per script")
def run_batch(directory: str, output_dir: str | None, timeout: int):
    """Run all .lua files in a directory."""
    lua_dir = Path(directory)
    lua_files = sorted(lua_dir.glob("*.lua"))

    if not lua_files:
        click.echo(f"No .lua files found in {directory}")
        return

    out_dir = Path(output_dir) if output_dir else lua_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = FemmClient()
    except ConnectionError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    for lua_file in lua_files:
        click.echo(f"Running {lua_file.name}...", nl=False)
        lua_script = lua_file.read_text(encoding="utf-8")
        result = client.run(lua_script, timeout=timeout)

        if result.error:
            click.echo(f" FAILED: {result.error}")
        else:
            csv_path = out_dir / f"{lua_file.stem}.csv"
            csv_path.write_text(result.csv_data, encoding="utf-8")
            click.echo(f" OK ({result.elapsed_s:.1f}s) -> {csv_path.name}")
