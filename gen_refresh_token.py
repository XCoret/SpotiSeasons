import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv


def init_spotify_cache(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scope: str,
    cache_path: str = ".cache"
) -> spotipy.Spotify:
    """Initializes Spotify authentication flow and stores credentials in cache.

    This function triggers the OAuth flow if no valid cache is found and
    persists the refresh token locally.

    Args:
        client_id (str): Spotify application client ID.
        client_secret (str): Spotify application client secret.
        redirect_uri (str): Redirect URI configured in Spotify app.
        scope (str): Authorization scopes required.
        cache_path (str, optional): Path to store cached credentials.

    Returns:
        spotipy.Spotify: Authenticated Spotify client instance.
    """
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=cache_path,
        open_browser=True
    )

    sp = spotipy.Spotify(auth_manager=auth_manager)

    sp.current_user()

    return sp


if __name__ == "__main__":
    """Executes OAuth flow to generate and cache Spotify refresh token."""
    load_dotenv()

    init_spotify_cache(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope=os.getenv("SCOPE")
    )