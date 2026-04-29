from dotenv import load_dotenv
from spotify_api import SpotifyAPIClient
from logger_config import setup_logger
import os
from datetime import datetime


def get_playlist_names(dt: datetime | None = None) -> tuple[str, str]:
    """Generates seasonal and yearly playlist names based on a given date.

    Args:
        dt (datetime | None, optional): Reference datetime. Defaults to current datetime.

    Returns:
        tuple[str, str]: Seasonal playlist name and year-based playlist name.
    """
    if dt is None:
        dt = datetime.now()

    y = dt.year
    prefix = f"{str(y)[-2:]}_"

    # Load from env (with defaults)
    SEASONS = {
        "winter": os.getenv("SEASON_WINTER", "WINTER"),
        "spring": os.getenv("SEASON_SPRING", "SPRING"),
        "summer": os.getenv("SEASON_SUMMER", "SUMMER"),
        "fall": os.getenv("SEASON_FALL", "FALL"),
    }

    spring = datetime(y, 3, 21)
    summer = datetime(y, 6, 21)
    fall = datetime(y, 9, 23)
    winter = datetime(y, 12, 21)

    if dt < spring:
        season = SEASONS["winter"]
    elif dt < summer:
        season = SEASONS["spring"]
    elif dt < fall:
        season = SEASONS["summer"]
    elif dt < winter:
        season = SEASONS["fall"]
    else:
        season = SEASONS["winter"]

    return f"{prefix}{season}", str(y)


if __name__ == '__main__':
    """Main execution flow for syncing liked tracks into playlists."""

    logger = setup_logger()
    logger.info("Starting SpotiSeasons")

    load_dotenv()

    spotify = SpotifyAPIClient(
        os.getenv("CLIENT_ID"),
        os.getenv("CLIENT_SECRET"),
        os.getenv("REFRESH_TOKEN"),
        logger=logger
    )

    liked_tracks = spotify.get_user_liked_tracks()
    logger.info(f"Fetched liked tracks: {len(liked_tracks)}")

    season_name, year_name = get_playlist_names()
    logger.info(f"Season playlist: {season_name} | Year playlist: {year_name}")

    season_playlist = spotify.find_playlist_by_name(season_name)
    if not season_playlist:
        logger.info(f"Creating season playlist: {season_name}")
        season_playlist = spotify.create_playlist(
            name=season_name,
            public=False,
            description=f"Cançons afegides durant {season_name.split('_')[-1].lower()} de {year_name}"
        )

    spotify.add_liked_tracks_to_playlist_unique(
        season_playlist["id"],
        liked_tracks
    )

    year_playlist = spotify.find_playlist_by_name(year_name)
    if not year_playlist:
        logger.info(f"Creating year playlist: {year_name}")
        year_playlist = spotify.create_playlist(
            name=year_name,
            public=False,
            description=f"Cançons afegides l'any {year_name}"
        )

    spotify.add_liked_tracks_to_playlist_unique(
        year_playlist["id"],
        liked_tracks
    )

    spotify.remove_liked_tracks(liked_tracks)

    logger.info("Sync process completed successfully")