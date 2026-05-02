# Baseball Stats Sabermetric Calculator

A Python-based utility designed to calculate and store advanced MLB statistics (wOBA, wRC+, and FIP) using real-time data from the official MLB Stats API. This tool is built to be robust against API changes and provides a persistent local audit trail of player performance.

## Features

* Live Data Integration: Fetches season totals directly from [mlb.com](https://mlb.com).
* Advanced Offensive Metrics: Calculates Weighted On-Base Average (wOBA) and Weighted Runs Created Plus (wRC+).
* Advanced Pitching Metrics: Calculates Fielding Independent Pitching (FIP) with proper inning-pitched decimal conversion.
* SQLite Persistence: Automatically manages a local database (baseball_stats.db) to store results.
* Automated Logging: Tracks every API request URL and database update in saber_calc.log.
* Ranking System: CLI commands to view leaderboards for saved hitters and pitchers.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/baseball_stats.git
    cd baseball_stats
    ```

2. Install dependencies:

   ```bash
   pip install requests
   ```

## Usage

### 1. Save or Update a Player

To fetch data from the MLB API and save it to your local database, you must provide the player's official MLB ID and specify the type (hitter or pitcher).

```bash
python saber_calc.py --id 660271 --type hitter --name "Shohei Ohtani"
```

### 2. View Rankings

Display all players currently stored in your database, ranked by their efficiency metrics.

**View Hitters by wRC+ (High to Low):**

```bash
python saber_calc.py --rank hitter
```

**View Pitchers by FIP (Low to High):**

```bash
python saber_calc.py --rank pitcher
```

### 3. Running Automated Tests

The repository includes a `test_saber.py` script that reads from a CSV file.

* Populate `players_to_test.csv` with `name,id,type`.
* Run:

   ```bash
   python test_saber.py
   ```

## Robustness and Configuration

The script is designed to be maintainable as MLB's infrastructure evolves. The Base URL and API Version are stored as properties and can be overridden at runtime without changing the code:

**Example: Overriding the API version if MLB updates to:**   v2

```bash
python saber_calc.py --rank hitter --api_ver v2
```

## Logging & Auditing

Every execution generates an audit trail in saber_calc.log. This includes:

* The source URL used for every API call.
* Notifications of Database Updates including the values saved.
* Error reporting for missing stats or connection issues.

------------------------------
