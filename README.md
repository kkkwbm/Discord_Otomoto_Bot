# 🚗 Discord OTOMOTO Bot

A Python-based Discord bot designed to track new car listings on OTOMOTO.pl. It automatically notifies users about new offers matching their criteria, ensuring you never miss a deal.



## ✨ Features
* **Real-time Monitoring:** Periodically scrapes OTOMOTO for the latest listings.
* **Data Persistence:** Uses SQLite to store previously seen offers and prevent duplicate notifications.
* **Asynchronous Design:** Built with `discord.py` for efficient, non-blocking performance.
* **Custom Scraper:** Tailored logic to extract key information (price, year, mileage) from listings.

## 🛠️ Technology Stack
* **Language:** Python 3.x
* **Libraries:** `discord.py`, `requests`, `BeautifulSoup4`, `sqlite3`
* **Database:** SQLite

## 🚀 Getting Started
1. **Clone the repo:** `git clone https://github.com/kkkwbm/Discord_Otomoto_Bot.git`
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Set up Environment Variables:** Create a `.env` file or set your system variables:
   - `DISCORD_TOKEN`: Your bot's secret token.
4. **Run the bot:** `python main.py`

## ⚠️ Disclaimer
This project is for **educational purposes only**. Scraper logic is intended to demonstrate web automation techniques. 
Please be aware that automated scraping of OTOMOTO/OLX may violate their Terms of Service. The author is not responsible for any misuse of this software, account bans, or legal consequences resulting from its use. Use it at your own risk and respect the websites' `robots.txt` and rate limits.
