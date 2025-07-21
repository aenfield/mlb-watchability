"""Command-line interface for generating MLB Watchability markdown files."""

import logging
from pathlib import Path

import typer

from .data_retrieval import get_game_schedule
from .game_scores import calculate_game_scores
from .markdown_generator import (
    generate_complete_markdown_content,
    generate_markdown_filename,
)
from .utils import extract_year_from_date, get_today

# Configure logging for detailed output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def main(
    date: str | None = typer.Argument(
        default=None,
        help="Date to generate markdown for (YYYY-MM-DD format). Defaults to today.",
    ),
) -> None:
    """Generate a markdown file with MLB game watchability scores for a given date."""

    # Determine the date to use
    target_date = date if date is not None else get_today()
    logger.info(f"Generating markdown file for date: {target_date}")

    try:
        # Extract season year from date
        season = extract_year_from_date(target_date)
        logger.info(f"Using season: {season}")

        # Retrieve game schedule data
        logger.info(f"Retrieving game schedule for {target_date}")
        games = get_game_schedule(target_date)
        logger.info(f"Found {len(games)} games for {target_date}")

        if not games:
            logger.warning(f"No games found for {target_date}")
            typer.echo(f"No games found for {target_date}")
            return

        # Calculate game scores (pNERD, tNERD, gNERD)
        logger.info("Calculating game scores (pNERD, tNERD, gNERD)")
        game_scores = calculate_game_scores(games, season)
        logger.info(f"Successfully calculated scores for {len(game_scores)} games")

        if not game_scores:
            logger.warning("No game scores could be calculated")
            typer.echo("No game scores could be calculated")
            return

        # Log game score details
        for i, game_score in enumerate(game_scores, 1):
            logger.info(
                f"Game {i}: {game_score.away_team} @ {game_score.home_team} "
                f"(gNERD: {game_score.gnerd_score:.1f})"
            )

        # Generate markdown content
        logger.info("Generating markdown content")
        markdown_content = generate_complete_markdown_content(target_date, game_scores)

        # Generate filename
        filename = generate_markdown_filename(target_date)
        logger.info(f"Writing to file: {filename}")

        # Write to file
        output_path = Path(filename)
        try:
            output_path.write_text(markdown_content, encoding="utf-8")
            logger.info(f"Successfully wrote markdown file: {output_path.absolute()}")
            typer.echo(f"Markdown file generated: {filename}")

        except Exception as write_error:
            logger.exception("Failed to write markdown file")
            typer.echo(f"Error writing file: {write_error}", err=True)
            raise typer.Exit(1) from write_error

    except Exception as e:
        logger.exception("Error generating markdown file")
        typer.echo(f"Error generating markdown file: {e}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
