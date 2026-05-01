import csv
import time
from saber_calc import SaberCalc

def run_csv_test(filename="players_to_test.csv"):
    calc = SaberCalc()

    print(f"{'PLAYER':<20} | {'TYPE':<8} | {'RESULT':<15} | {'STATUS'}")
    print("-" * 60)

    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            # DictReader uses the first row as keys (name, id, type)
            reader = csv.DictReader(f)

            for row in reader:
                name = row['name']
                p_id = int(row['id'])
                p_type = row['type']

                try:
                    if p_type == 'hitter':
                        data = calc.fetch_hitter_stats(p_id)
                        if data:
                            woba, wrcp = calc.calculate_hitting(**data)
                            calc.save_hitter(name, woba, wrcp)
                            status = f"wRC+: {wrcp}"
                        else:
                            status = "No Data"
                    else:
                        data = calc.fetch_pitcher_stats(p_id)
                        if data:
                            fip = calc.calculate_fip(**data)
                            calc.save_pitcher(name, fip, data['ip'])
                            status = f"FIP: {fip}"
                        else:
                            status = "No Data"

                    print(f"{name:<20} | {p_type:<8} | {status:<15} | SUCCESS")

                except Exception as e:
                    print(f"{name:<20} | {p_type:<8} | ERROR           | {e}")

                # Sleep briefly to respect API rate limits
                time.sleep(0.5)

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")

if __name__ == "__main__":
    run_csv_test()

