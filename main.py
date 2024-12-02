import asyncio
import os
import sys
import dataset
from loguru import logger as log
from scraper import scrape_otomoto

# Database setup
# test
db = dataset.connect("sqlite:///otomoto_offers.db")

# Function to handle the background scraping task
async def run_background() -> None:
    log.info("Otomoto Scraper started.")

    url = "https://www.otomoto.pl/osobowe/audi--bmw--fiat--honda--hyundai--mercedes-benz--nissan--opel--peugeot--renault--toyota--volvo/od-2000?search%5Bfilter_enum_fuel_type%5D=petrol&search%5Bfilter_float_mileage%3Afrom%5D=100000&search%5Bfilter_float_price%3Afrom%5D=15000&search%5Bfilter_float_price%3Ato%5D=40000&search%5Bfilter_float_year%3Ato%5D=2020&search%5Border%5D=created_at_first%3Adesc"

    while True:
        try:
            log.info("Executing Otomoto scraping loop.")
            new_items = scrape_otomoto(db, url)
            if new_items:
                log.info(f"Found {len(new_items)} new offers.")
            else:
                log.info("No new offers found.")

            await asyncio.sleep(60)  # Rerun every minute
        except Exception as e:
            log.error(f"An unexpected error occurred: {e}")
            restart_program()

def restart_program():
    try:
        print("Restarting the program...")
        python = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        os.execl(python, python, script_path, *sys.argv[1:])
    except Exception as e:
        print(f"Failed to restart program: {e}")

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()

    # Start the background scraping loop
    asyncio.run(run_background())
