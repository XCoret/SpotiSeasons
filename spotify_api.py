from urllib.parse import urlparse, parse_qs
import requests
import time


class SpotifyAPIClient:
    """Client for interacting with the Spotify Web API using refresh token flow."""

    BASE_URL = "https://api.spotify.com/v1"
    TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        logger=None
    ):
        """Initializes the Spotify API client.

        Args:
            client_id (str): Spotify application client ID.
            client_secret (str): Spotify application client secret.
            refresh_token (str): Refresh token.
            logger (logging.Logger, optional): Logger instance.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.logger = logger

        self.access_token = None
        self.token_expires_at = 0

        self._refresh_access_token()

    def _log(self, level: str, msg: str) -> None:
        """Internal helper to log safely."""
        if self.logger:
            getattr(self.logger, level)(msg)

    def _refresh_access_token(self) -> None:
        """Refreshes the Spotify access token."""
        self._log("info", "Refreshing access token")

        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            auth=(self.client_id, self.client_secret),
        )

        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.token_expires_at = time.time() + data["expires_in"] - 60

    def _ensure_token(self) -> None:
        """Ensures valid token."""
        if time.time() >= self.token_expires_at:
            self._refresh_access_token()

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Performs authenticated request."""
        try:
            self._ensure_token()

            headers = kwargs.pop("headers", {})
            headers["Authorization"] = f"Bearer {self.access_token}"

            response = requests.request(
                method,
                f"{self.BASE_URL}{endpoint}",
                headers=headers,
                **kwargs
            )

            response.raise_for_status()

            if response.status_code == 204 or not response.content:
                return {}

            return response.json()

        except Exception as e:
            self._log("error", f"{method} {endpoint} failed: {e}")
            raise

    def get_user_playlists(self, limit: int = 50) -> list[dict]:
        """Retrieves all playlists."""
        playlists = []
        offset = 0

        while True:
            response = self._request(
                "GET",
                "/me/playlists",
                params={"limit": limit, "offset": offset}
            )

            items = response.get("items", [])
            playlists.extend(items)

            self._log("info", f"Fetched {len(items)} playlists (offset={offset})")

            if len(items) < limit:
                break

            offset += limit

        return playlists

    def get_playlist_track_uris(self, playlist_id: str) -> set[str]:
        """Gets track URIs."""
        uris = set()
        endpoint = f"/playlists/{playlist_id}/tracks"

        while endpoint:
            response = self._request("GET", endpoint)

            for item in response.get("items", []):
                track = item.get("track")
                if track and track.get("uri"):
                    uris.add(track["uri"])

            next_url = response.get("next")
            endpoint = next_url.replace(self.BASE_URL, "") if next_url else None

        self._log("info", f"Playlist {playlist_id} has {len(uris)} tracks")

        return uris

    def add_liked_tracks_to_playlist_unique(
        self,
        playlist_id: str,
        liked_tracks: list[dict]
    ) -> None:
        """Adds liked tracks avoiding duplicates."""
        uris = [
            item["track"]["uri"]
            for item in liked_tracks
            if item.get("track") and item["track"].get("uri")
        ]

        if not uris:
            self._log("info", "No liked tracks to process")
            return

        existing_uris = self.get_playlist_track_uris(playlist_id)
        new_uris = [u for u in uris if u not in existing_uris]

        self._log("info", f"New tracks to add: {len(new_uris)}")

        if new_uris:
            self.add_tracks_to_playlist(playlist_id, new_uris)

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: list[str]) -> None:
        """Adds tracks in batches."""
        if not track_uris:
            return

        seen = set()
        unique_uris = [u for u in track_uris if not (u in seen or seen.add(u))]

        for i in range(0, len(unique_uris), 100):
            batch = unique_uris[i:i + 100]

            self._log("info", f"Adding batch of {len(batch)} tracks")

            self._request(
                "POST",
                f"/playlists/{playlist_id}/tracks",
                json={"uris": batch}
            )

    def get_user_liked_tracks(self, limit: int = 50) -> list[dict]:
        """Retrieves liked tracks."""
        items = []
        endpoint = "/me/tracks"
        params = {"limit": limit}

        while endpoint:
            response = self._request(
                "GET",
                endpoint,
                params=params if endpoint == "/me/tracks" else None
            )

            batch = response.get("items", [])
            items.extend(batch)

            self._log("info", f"Fetched liked tracks batch: {len(batch)}")

            next_url = response.get("next")

            if next_url:
                endpoint = next_url.replace(self.BASE_URL, "")
                params = None
            else:
                endpoint = None

        return items

    def remove_liked_tracks(self, track_list: list[dict]) -> None:
        """Removes liked tracks."""
        track_ids = [
            item["track"]["id"]
            for item in track_list
            if item.get("track") and item["track"].get("id")
        ]

        track_ids = list(dict.fromkeys(track_ids))

        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i + 50]

            self._log("info", f"Removing batch of {len(batch)} tracks")

            self._request(
                "DELETE",
                "/me/tracks",
                params={"ids": ",".join(batch)}
            )

    def find_playlist_by_name(self, name: str) -> dict | None:
        """Finds playlist by name."""
        offset = 0

        while True:
            response = self._request(
                "GET",
                "/me/playlists",
                params={"limit": 50, "offset": offset}
            )

            items = response.get("items", [])

            for p in items:
                if p["name"] == name:
                    self._log("info", f"Playlist found: {name}")
                    return p

            if len(items) < 50:
                break

            offset += 50

        self._log("info", f"Playlist not found: {name}")
        return None

    def create_playlist(self, name: str, public: bool = False, description: str = "") -> dict:
        """Creates playlist."""
        self._log("info", f"Creating playlist: {name}")

        user = self._request("GET", "/me")
        user_id = user["id"]

        return self._request(
            "POST",
            f"/users/{user_id}/playlists",
            json={
                "name": name,
                "public": public,
                "description": description
            }
        )