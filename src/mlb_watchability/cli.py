"""Command-line interface for MLB Watchability."""

from datetime import datetime
from typing import Optional

import typer

app = typer.Typer()


@app.command()
def main(
    date: Optional[str] = typer.Argument(
        default=None,
        help="Date to calculate game scores for (YYYY-MM-DD format). Defaults to today.",
    ),
) -> None:
    """Calculate Game NERD scores for MLB games on a given date."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    typer.echo(f"Hello World - Processing games for {date}")


if __name__ == "__main__":
    app()
