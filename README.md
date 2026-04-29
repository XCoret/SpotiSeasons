
# SpotiSeasons

<p align="center">
  <img src="https://github.com/XCoret/SpotiSeasons/blob/master/SpotiSeasons.png" alt="SpotiSeasons Logo" max-width="150"/>
</p>

## Spotify Liked Tracks Organizer

SpotiSeasons automatically organizes your **Spotify liked tracks** into playlists based on:

- **Season** (configurable, Catalan by default: *HIVERN, PRIMAVERA, ESTIU, TARDOR*)
- **Year**

The application is designed to run periodically (e.g., weekly) and guarantees **idempotent synchronization** (safe to re-run without duplications).

---

## Features

- Automatic playlist creation (if missing)
- Deduplication using `set` → **O(n)** lookup
- Batch processing aligned with Spotify API limits
- Refresh token authentication (no manual login after setup)
- Seasonal classification based on track processing date
- Configurable season names via `.env`
- Rotating logs (`logs/SpotiSeasons.log`)
- Centralized error handling with logging

---

## Project Structure

```bash
.
├── main.py                  # Entry point (sync orchestration)
├── spotify_api.py           # Spotify API client (HTTP wrapper)
├── logger_config.py         # Logging configuration
├── get_refresh_token.py     # OAuth helper (initial setup)
├── requirements.txt
├── .env
└── logs/
````

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies defined in `requirements.txt`: 

---

### 2. Configure environment variables

Create a `.env` file:

```env
# Seasons (example configuration, using Catalan)
SEASON_WINTER=HIVERN
SEASON_SPRING=PRIMAVERA
SEASON_SUMMER=ESTIU
SEASON_FALL=TARDOR

# Spotify credentials
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REDIRECT_URI=http://127.0.0.1:8000/callback
SCOPE=playlist-read-private playlist-modify-public playlist-modify-private user-library-read user-library-modify

# Generated once
REFRESH_TOKEN=your_refresh_token
```

⚠️ **Important:** Never commit your `.env` file (it contains secrets).

---

### 3. Generate Refresh Token (first time only)

```bash
python get_refresh_token.py
```

This script:

1. Opens a browser for Spotify login
2. Stores credentials in `.cache`
3. Generates a `refresh_token` to reuse indefinitely

Implementation uses Spotipy OAuth flow: 

---

## How It Works

### Execution Flow

1. Load environment variables
2. Initialize logger (`RotatingFileHandler`)
3. Initialize Spotify client (refresh token flow)
4. Fetch all liked tracks (paginated)
5. Generate playlist names:

   * Seasonal → `YY_<SEASON>` (e.g., `26_ESTIU`)
   * Year → `YYYY` (e.g., `2026`)
6. For each playlist:

   * Find or create playlist
   * Retrieve existing track URIs
   * Insert only **new tracks**
7. Remove processed tracks from "Liked Songs"
8. Log execution

Core orchestration: 

---

## Logging

Logs are stored in:

```bash
logs/SpotiSeasons.log
```

Logger configuration: 

### Format

```text
2026-04-29 10:12:01 [INFO]: Starting SpotiSeasons
```

### Characteristics

* Rotating logs (5MB × 3 files)
* No duplicate handlers
* Timestamped structured format
* Errors logged before propagation
* No stdout pollution

---

## Execution

```bash
python main.py
```

---

## Automation

### Cron (Linux/macOS)

```bash
0 0 * * 1 /usr/bin/python3 /path/to/main.py
```

Runs every Monday at 00:00.

---

## Technical Notes

### API Constraints

| Operation    | Limit |
| ------------ | ----: |
| Add tracks   |   100 |
| Remove liked |    50 |

Handled internally via batching in the API client: 

---

### Performance

* Deduplication: **O(n)** using `set`
* Pre-filtering before batching
* Pagination-aware fetching
* Idempotent execution (safe re-runs)

---

### Error Handling

* All requests use `raise_for_status()`
* Centralized `_request()` wrapper
* Errors logged with endpoint context

---

## Possible Improvements

* Retry strategy with exponential backoff (HTTP 429)
* Local caching of playlist IDs (reduce API calls)
* Parallelization of independent requests
* CLI flags (`--dry-run`, `--verbose`, `--date`)
* Structured logging (JSON)
* Unit + integration tests (mock Spotify API)
* Incremental sync (track timestamp tracking)

---

## License

MIT License
