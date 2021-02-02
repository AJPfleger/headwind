from pathlib import Path
import typer

from headwind.spec import load_spec

app = typer.Typer(add_completion=False)


@app.command()
def collect(spec_file: typer.FileText) -> None:
    spec = load_spec(spec_file)
