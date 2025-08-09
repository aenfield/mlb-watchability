"""Command-line interface for generating MLB Watchability markdown files."""

import logging
import os
from pathlib import Path

import typer
from dotenv import load_dotenv

from .data_retrieval import get_game_schedule
from .game_scores import GameScore
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
    game_desc_source: str | None = typer.Option(
        default=None,
        help="Source for game descriptions: 'canned' or 'llm'. If not provided, no descriptions are included.",
    ),
    game_desc_limit: int | None = typer.Option(
        default=None,
        help="Number of top games to generate descriptions for. Defaults to 1 if --game_desc_source is provided.",
    ),
    llm_model: str = typer.Option(
        default="normal",
        help="LLM model to use: 'normal' (default) or 'cheap'. Only applies when --game-desc-source is 'llm'.",
    ),
    llm_model_provider: str = typer.Option(
        default="anthropic",
        help="LLM provider to use: 'anthropic' (default) or 'openai'. Only applies when --game-desc-source is 'llm'.",
    ),
) -> None:
    """Generate a markdown file with MLB game watchability scores for a given date."""

    # Load environment variables from .env file
    env_file_loaded = load_dotenv()
    if env_file_loaded:
        logger.info("Loaded environment variables from .env file")
    else:
        logger.debug("No .env file found or loaded")

    # Log current LLM retry configuration
    llm_retries_enabled = os.getenv("ENABLE_LLM_RETRIES", "")
    logger.info(f"ENABLE_LLM_RETRIES environment variable: '{llm_retries_enabled}'")

    # Handle parameter defaults and validation
    if game_desc_source is not None and game_desc_limit is None:
        game_desc_limit = 1
    elif game_desc_limit is not None and game_desc_source is None:
        game_desc_source = "canned"

    # Validate game_desc_source if provided
    if game_desc_source is not None and game_desc_source not in ["canned", "llm"]:
        logger.error(
            f"Invalid game_desc_source: {game_desc_source}. Must be 'canned' or 'llm'."
        )
        typer.echo(
            f"Error: game_desc_source must be 'canned' or 'llm', not '{game_desc_source}'",
            err=True,
        )
        raise typer.Exit(1)

    # Validate llm_model parameter
    if llm_model not in ["normal", "cheap"]:
        logger.error(f"Invalid llm_model: {llm_model}. Must be 'normal' or 'cheap'.")
        typer.echo(
            f"Error: llm_model must be 'normal' or 'cheap', not '{llm_model}'",
            err=True,
        )
        raise typer.Exit(1)

    # Validate llm_model_provider parameter
    if llm_model_provider not in ["anthropic", "openai"]:
        logger.error(
            f"Invalid llm_model_provider: {llm_model_provider}. Must be 'anthropic' or 'openai'."
        )
        typer.echo(
            f"Error: llm_model_provider must be 'anthropic' or 'openai', not '{llm_model_provider}'",
            err=True,
        )
        raise typer.Exit(1)

    # Pass the generic model type - the create_llm_client factory will map it to provider-specific models
    model_to_use = llm_model

    # Determine the date to use
    target_date = date if date is not None else get_today()
    logger.info(f"Generating markdown file for date: {target_date}")

    # Log game description settings
    if game_desc_source is not None:
        logger.info(
            f"Game descriptions enabled: source={game_desc_source}, limit={game_desc_limit}, provider={llm_model_provider}, model={model_to_use}"
        )
    else:
        logger.info("Game descriptions disabled")

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
        game_scores = GameScore.from_games(
            games,
            season,
            game_desc_source=game_desc_source,
            game_desc_limit=game_desc_limit or 1,
            model=model_to_use,
            provider=llm_model_provider,
        )
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
        include_descriptions = game_desc_source is not None
        markdown_content = generate_complete_markdown_content(
            target_date, game_scores, include_descriptions
        )

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
