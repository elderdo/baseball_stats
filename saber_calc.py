import sqlite3
import requests
import argparse
import sys
import logging

class SaberCalc:
    """
    A sabermetric calculator handling constants, live API data,
    and SQLite persistence with integrated logging.
    """
    # 2026 LEAGUE CONSTANTS
    W_BB, W_HBP, W_1B, W_2B, W_3B, W_HR = 0.69, 0.72, 0.88, 1.26, 1.60, 2.10
    WOBA_SCALE, LG_WOBA, LG_R_PA, FIP_CONSTANT = 1.25, 0.320, 0.115, 3.20

    # API CONFIGURATION PROPERTIES
    BASE_URL = "https://statsapi.mlb.com"
    API_VER = "v1"

    def __init__(self, db_name="data/baseball_stats.db", base_url=None, api_ver=None):
        """Constructor: Initializes logging, DB, and API settings."""
        self._setup_logging()
        self.conn = sqlite3.connect(db_name)
        if base_url: self.BASE_URL = base_url
        if api_ver: self.API_VER = api_ver
        self._setup_db()
        logging.info(f"SaberCalc initialized using API: {self.BASE_URL}/api/{self.API_VER}")

    def _setup_logging(self):
        """Subroutine: Configures logging to both console and saber_calc.log file."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/saber_calc.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _setup_db(self):
        """Subroutine: Ensures hitters and pitchers tables exist."""
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS hitters 
                (name TEXT PRIMARY KEY, wOBA REAL, wRC_plus INTEGER)''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS pitchers 
                (name TEXT PRIMARY KEY, FIP REAL, innings REAL)''')
        logging.info("Database connection and schema verified.")

    def _get_api_path(self, player_id, group):
        """Helper: Constructs the full API path and logs the source."""
        full_url = f"{self.BASE_URL}/api/{self.API_VER}/people/{player_id}/stats?stats=season&group={group}"
        logging.info(f"Fetching data from source: {full_url}")
        return full_url

    def calculate_hitting(self, ubb, hbp, b1, b2, b3, hr, pa):
        """Subroutine: Returns a tuple of (wOBA, wRC+)."""
        if pa == 0: return 0.0, 0
        woba = ((self.W_BB * ubb) + (self.W_HBP * hbp) + (self.W_1B * b1) + 
                (self.W_2B * b2) + (self.W_3B * b3) + (self.W_HR * hr)) / pa
        wrc_plus = (((woba - self.LG_WOBA) / self.WOBA_SCALE + self.LG_R_PA) / self.LG_R_PA) * 100
        return round(woba, 3), int(round(wrc_plus))

    def calculate_fip(self, hr, bb, hbp, k, ip):
        """Subroutine: Computes FIP using decimal inning conversion."""
        if ip <= 0: return 0.0
        whole_inns = int(ip)
        outs = round((ip - whole_inns) * 10)
        decimal_ip = whole_inns + (outs / 3.0)
        raw_fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / decimal_ip
        return round(raw_fip + self.FIP_CONSTANT, 2)

    def fetch_hitter_stats(self, player_id):
        """Subroutine: Fetches hitting data using dynamic URL."""
        url = self._get_api_path(player_id, "hitting")
        try:
            res = requests.get(url).json()
            stats_list = res.get('stats', [])
            if not stats_list: raise IndexError("No stats available.")
            splits = stats_list[0].get('splits', [])
            if not splits: raise IndexError("No 2026 data found.")
            s = splits[0].get('stat', {})
            return {
                "pa": s.get('plateAppearances', 0), "hr": s.get('homeRuns', 0), 
                "hbp": s.get('hitByPitch', 0), "ubb": s.get('baseOnBalls', 0) - s.get('intentionalWalks', 0),
                "b1": s.get('hits', 0) - (s.get('doubles', 0) + s.get('triples', 0) + s.get('homeRuns', 0)),
                "b2": s.get('doubles', 0), "b3": s.get('triples', 0)
            }
        except Exception as e:
            logging.error(f"Failed to fetch hitter {player_id}: {e}")
            return None

    def fetch_pitcher_stats(self, player_id):
        """Subroutine: Fetches pitching data using dynamic URL."""
        url = self._get_api_path(player_id, "pitching")
        try:
            res = requests.get(url).json()
            stats_list = res.get('stats', [])
            if not stats_list: raise IndexError("No stats available.")
            splits = stats_list[0].get('splits', [])
            if not splits: raise IndexError("No 2026 data found.")
            s = splits[0].get('stat', {})
            return {
                "hr": s.get('homeRuns', 0), "bb": s.get('baseOnBalls', 0), 
                "hbp": s.get('hitByPitch', 0), "k": s.get('strikeouts', 0), 
                "ip": float(s.get('inningsPitched', 0.0))
            }
        except Exception as e:
            logging.error(f"Failed to fetch pitcher {player_id}: {e}")
            return None

    def save_hitter(self, name, woba, wrcp):
        """Subroutine: Saves results to hitters table and logs update."""
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO hitters VALUES (?, ?, ?)", (name, woba, wrcp))
        logging.info(f"Database Updated: {name} (Hitter) saved with wRC+: {wrcp}")

    def save_pitcher(self, name, fip, ip):
        """Subroutine: Saves results to pitchers table and logs update."""
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO pitchers VALUES (?, ?, ?)", (name, fip, ip))
        logging.info(f"Database Updated: {name} (Pitcher) saved with FIP: {fip}")

    def display_rankings(self, stat_type='hitter'):
        """Subroutine: Prints database rankings."""
        query = "SELECT name, wRC_plus FROM hitters ORDER BY wRC_plus DESC" if stat_type == 'hitter' else "SELECT name, FIP FROM pitchers ORDER BY FIP ASC"
        header = "wRC+" if stat_type == 'hitter' else "FIP"
        print(f"\n--- {stat_type.upper()} RANKINGS ---\n{'RANK':<5} | {'PLAYER':<20} | {header:<6}\n" + "-"*40)
        with self.conn:
            for rank, (name, val) in enumerate(self.conn.execute(query).fetchall(), 1):
                print(f"{rank:<5} | {name:<20} | {val:<6}")

def main():
    """CLI Entry: Parses arguments including URL/API overrides."""
    parser = argparse.ArgumentParser(description="Sabermetric Calculator CLI")
    parser.add_argument("--id", type=int, help="MLB Player ID")
    parser.add_argument("--type", choices=['hitter', 'pitcher'], help="Stat type")
    parser.add_argument("--name", help="Display name")
    parser.add_argument("--rank", choices=['hitter', 'pitcher'], help="Show rankings")
    parser.add_argument("--url", help="Override base URL")
    parser.add_argument("--api_ver", help="Override API version")

    args = parser.parse_args()
    calc = SaberCalc(base_url=args.url, api_ver=args.api_ver)

    if args.rank:
        calc.display_rankings(args.rank)
    elif args.id and args.type:
        name = args.name or f"Player {args.id}"
        if args.type == 'hitter':
            data = calc.fetch_hitter_stats(args.id)
            if data:
                woba, wrcp = calc.calculate_hitting(**data)
                calc.save_hitter(name, woba, wrcp)
        else:
            data = calc.fetch_pitcher_stats(args.id)
            if data:
                fip = calc.calculate_fip(**data)
                calc.save_pitcher(name, fip, data['ip'])
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
