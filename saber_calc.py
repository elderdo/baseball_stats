import sqlite3
import requests
import argparse
import sys

class SaberCalc:
    """
    A sabermetric calculator handling 2026 constants, live API data,
    and SQLite persistence.
    """
    # 2026 LEAGUE CONSTANTS
    W_BB, W_HBP, W_1B, W_2B, W_3B, W_HR = 0.69, 0.72, 0.88, 1.26, 1.60, 2.10
    WOBA_SCALE, LG_WOBA, LG_R_PA, FIP_CONSTANT = 1.25, 0.320, 0.115, 3.20

    def __init__(self, db_name="baseball_stats.db"):
        """Constructor: Creates DB connection and initializes tables."""
        self.conn = sqlite3.connect(db_name)
        self._setup_db()

    def _setup_db(self):
        """Subroutine: Ensures hitters and pitchers tables exist in SQLite."""
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS hitters 
                (name TEXT PRIMARY KEY, wOBA REAL, wRC_plus INTEGER)''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS pitchers 
                (name TEXT PRIMARY KEY, FIP REAL, innings REAL)''')

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
        """Subroutine: Safely fetches hitting data from MLB Stats API."""
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting"
        try:
            res = requests.get(url).json()
            stats_list = res.get('stats', [])
            if not stats_list: raise IndexError("No stats available.")
            
            splits = stats_list[0].get('splits', [])
            if not splits: raise IndexError("No 2026 hitting data found.")
            
            s = splits[0].get('stat', {})
            return {
                "pa": s.get('plateAppearances', 0), 
                "hr": s.get('homeRuns', 0), 
                "hbp": s.get('hitByPitch', 0), 
                "ubb": s.get('baseOnBalls', 0) - s.get('intentionalWalks', 0),
                "b1": s.get('hits', 0) - (s.get('doubles', 0) + s.get('triples', 0) + s.get('homeRuns', 0)),
                "b2": s.get('doubles', 0), 
                "b3": s.get('triples', 0)
            }
        except Exception as e:
            print(f"Error fetching hitter {player_id}: {e}")
            return None

    def fetch_pitcher_stats(self, player_id):
        """Subroutine: Safely fetches pitching data from MLB Stats API."""
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=pitching"
        try:
            res = requests.get(url).json()
            stats_list = res.get('stats', [])
            if not stats_list: raise IndexError("No stats available.")
            
            splits = stats_list[0].get('splits', [])
            if not splits: raise IndexError("No 2026 pitching data found.")
            
            s = splits[0].get('stat', {})
            return {
                "hr": s.get('homeRuns', 0), 
                "bb": s.get('baseOnBalls', 0), 
                "hbp": s.get('hitByPitch', 0), 
                "k": s.get('strikeouts', 0), 
                "ip": float(s.get('inningsPitched', 0.0))
            }
        except Exception as e:
            print(f"Error fetching pitcher {player_id}: {e}")
            return None

    def save_hitter(self, name, woba, wrcp):
        """Subroutine: Saves results to hitters table."""
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO hitters VALUES (?, ?, ?)", (name, woba, wrcp))

    def save_pitcher(self, name, fip, ip):
        """Subroutine: Saves results to pitchers table."""
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO pitchers VALUES (?, ?, ?)", (name, fip, ip))

    def display_rankings(self):
        """Subroutine: Prints database rankings by wRC+."""
        query = "SELECT name, wRC_plus FROM hitters ORDER BY wRC_plus DESC"
        print(f"\n{'RANK':<5} | {'PLAYER':<20} | {'wRC+':<6}")
        print("-" * 35)
        with self.conn:
            results = self.conn.execute(query).fetchall()
            for rank, (name, wrcp) in enumerate(results, 1):
                print(f"{rank:<5} | {name:<20} | {wrcp:<6}")

def main():
    """CLI Entry: Parses arguments for fetching, ranking, or saving."""
    parser = argparse.ArgumentParser(description="Sabermetric Calculator CLI")
    parser.add_argument("--id", type=int, help="MLB Player ID")
    parser.add_argument("--type", choices=['hitter', 'pitcher'], help="Stat type")
    parser.add_argument("--name", help="Display name")
    parser.add_argument("--rank", action="store_true", help="Display rankings")

    args = parser.parse_args()
    calc = SaberCalc()

    if args.rank:
        calc.display_rankings()
        sys.exit(0)

    if not args.id or not args.type:
        print("Required: --id [number] --type [hitter/pitcher] OR --rank")
        sys.exit(1)

    name = args.name or f"Player {args.id}"
    if args.type == 'hitter':
        data = calc.fetch_hitter_stats(args.id)
        if data:
            woba, wrcp = calc.calculate_hitting(**data)
            calc.save_hitter(name, woba, wrcp)
            print(f"Saved {name}: wRC+={wrcp}")
    else:
        data = calc.fetch_pitcher_stats(args.id)
        if data:
            fip = calc.calculate_fip(**data)
            calc.save_pitcher(name, fip, data['ip'])
            print(f"Saved {name}: FIP={fip}")

if __name__ == "__main__":
    main()
