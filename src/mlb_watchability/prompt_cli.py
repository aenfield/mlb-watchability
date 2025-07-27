"""Command-line interface for generating MLB game prompt files."""

import logging
from pathlib import Path

import typer
from dotenv import load_dotenv

from .data_retrieval import get_game_schedule
from .game_scores import GameScore
from .utils import extract_year_from_date, get_today

# Load environment variables from .env file
load_dotenv()

# Configure logging for detailed output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer()


def generate_prompt_filename(date: str, game_index: int) -> str:
    """Generate a filename for the game prompt file."""
    return f"game_prompt_{date}_game_{game_index}.md"


@app.command()
def main(
    date: str | None = typer.Argument(
        default=None,
        help="Date to generate prompt for (YYYY-MM-DD format). Defaults to today.",
    ),
    game_index: int = typer.Argument(
        default=0,
        help="Index of the game to generate prompt for (0-based). Defaults to 0.",
    ),
    send_to_llm: bool = typer.Option(
        False,
        "--send-to-llm",
        "-g",
        help="Also send the prompt to LLM and output the generated description and web sources.",
    ),
) -> None:
    """Generate a game prompt file for a specific MLB game on a given date."""

    # Determine the date to use
    target_date = date if date is not None else get_today()
    logger.info(
        f"Generating game prompt for date: {target_date}, game index: {game_index}"
    )

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

        # Validate game index
        if game_index < 0 or game_index >= len(games):
            logger.error(f"Game index {game_index} is out of range (0-{len(games)-1})")
            typer.echo(
                f"Game index {game_index} is out of range. Available games: 0-{len(games)-1}"
            )
            return

        # Calculate game scores (pNERD, tNERD, gNERD)
        logger.info("Calculating game scores (pNERD, tNERD, gNERD)")
        game_scores = GameScore.from_games(games, season)
        logger.info(f"Successfully calculated scores for {len(game_scores)} games")

        if not game_scores:
            logger.warning("No game scores could be calculated")
            typer.echo("No game scores could be calculated")
            return

        # Get the specific game by index (game_scores are sorted by gNERD, highest first)
        if game_index >= len(game_scores):
            logger.error(
                f"Game index {game_index} is out of range (0-{len(game_scores)-1})"
            )
            typer.echo(
                f"Game index {game_index} is out of range. Available games: 0-{len(game_scores)-1}"
            )
            return

        # Select the game directly from sorted game_scores (highest gNERD first)
        selected_game_score = game_scores[game_index]

        # Log selected game details
        logger.info(
            f"Selected game: {selected_game_score.away_team} @ {selected_game_score.home_team} "
            f"(gNERD: {selected_game_score.gnerd_score:.1f})"
        )

        # Generate formatted prompt content
        logger.info("Generating formatted prompt content")
        prompt_content = selected_game_score.generate_formatted_prompt()

        # Generate filename
        filename = generate_prompt_filename(target_date, game_index)
        logger.info(f"Writing to file: {filename}")

        # Write to file
        output_path = Path(filename)
        try:
            output_path.write_text(prompt_content, encoding="utf-8")
            logger.info(f"Successfully wrote prompt file: {output_path.absolute()}")
            typer.echo(f"Game prompt file generated: {filename}")

        except Exception as write_error:
            logger.exception("Failed to write prompt file")
            typer.echo(f"Error writing file: {write_error}", err=True)
            raise typer.Exit(1) from write_error

        # If send_to_llm flag is set, also call LLM and output results
        if send_to_llm:
            logger.info("Generating description using LLM")
            try:
                description, web_sources = (
                    selected_game_score.get_description_from_llm_using_prompt(
                        prompt_content
                    )
                )

                typer.echo("\n" + "=" * 50)
                typer.echo("LLM-GENERATED DESCRIPTION:")
                typer.echo("=" * 50)
                typer.echo(description)

                if web_sources:
                    typer.echo("\n" + "=" * 50)
                    typer.echo("WEB SOURCES:")
                    typer.echo("=" * 50)
                    for i, source in enumerate(web_sources, 1):
                        typer.echo(f"{i}. {source.get('title', 'N/A')}")
                        typer.echo(f"   URL: {source.get('url', 'N/A')}")
                        if source.get("snippet"):
                            typer.echo(f"   Snippet: {source['snippet']}")
                        typer.echo()
                else:
                    typer.echo("\nNo web sources found.")

            except Exception as llm_error:
                logger.exception("Failed to generate description with LLM")
                typer.echo(f"Error generating LLM description: {llm_error}", err=True)

    except Exception as e:
        logger.exception("Error generating prompt file")
        typer.echo(f"Error generating prompt file: {e}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
