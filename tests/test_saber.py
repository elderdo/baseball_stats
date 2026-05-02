import csv
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    # Add the parent directory to the Python path so we can import saber_calc.py from the main project folder.
    # This allows us to use SaberCalc in this test script even though it's outside the tests/ directory.
    # IMPORTANT: This line MUST come before the 'from saber_calc import SaberCalc' statement below.
    # When Python executes an import, it looks through the directories listed in sys.path in order.
    # By modifying sys.path first, we ensure Python can find saber_calc.py when we try to import it.
    # If you put the import before this line, Python will not know where to find saber_calc.py and will raise an ImportError.
    #
    # Explanation of the nested function calls:
    # os.path.dirname(__file__): Returns the directory containing this test file.
    # os.path.join(..., '..'): Joins that directory with '..' to move up one level (to the project root).
    # os.path.abspath(...): Converts the joined path to an absolute path (full path from the root of your drive).
    # sys.path.append(...): Adds that absolute path to the list of places Python looks for modules to import.
    # So, each function returns a path, and the final result is that the parent directory is added to sys.path.
from saber_calc import SaberCalc


def run_csv_test(filename=None):
    if filename is None:
        # Why use os.path.dirname(os.path.dirname(__file__)) instead of just '../data'? 
        #
        # Using os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", ...) ensures that the path is always
        # constructed relative to the actual location of this script, regardless of the current working directory
        # from which the script is run. This is important because:
        #   - If you use "../data", it is a relative path and will only work if you run the script from the tests/ directory.
        #   - If you run the script from another directory (e.g., the project root), "../data" may not point to the correct location.
        #   - os.path.dirname(__file__) gets the directory containing this script, so os.path.dirname(os.path.dirname(__file__))
        #     moves up to the project root, and then "data" is appended, making the path robust to where the script is run from.
        #
        # In summary: This approach is more reliable for test automation and IDEs, which may set the working directory differently.
        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "players_to_test.csv")
    calc = SaberCalc()

    # The following f-string prints the table header with aligned columns.
    # The syntax {'literal':<nn} means:
    #   - 'literal' is the text to display (e.g., 'PLAYER', 'TYPE', etc.)
    #   - <nn specifies left alignment within a field of width nn characters (e.g., <20 means left-align in 20 spaces)
    # This ensures each column header is padded to the same width, making the output easy to read as a table.
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

