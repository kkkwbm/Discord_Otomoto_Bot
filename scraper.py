import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from dataset import Database
from loguru import logger as log
import hikari
from datetime import datetime

def scrape_otomoto(db: Database, url: str) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, headers=headers)
    log.info(f"Request to {url} returned status code {response.status_code}")

    if response.status_code != 200:
        log.error(f"Failed to retrieve the page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract links using the specific class
    offers = []
    offer_elements = soup.find_all("p", class_="e2z61p70 ooa-1ed90th er34gjf0")
    for i, element in enumerate(offer_elements):
        try:
            link_tag = element.find("a", href=True)
            if link_tag:
                url = link_tag["href"]
                title = link_tag.text.strip()
                offers.append({"url": url, "title": title})
                log.info(f"Item {i + 1}: {title} - {url}")
            else:
                log.warning(f"Item {i + 1} has no link.")
        except Exception as e:
            log.error(f"Error processing item {i + 1}: {e}")

    # Limit to the 20 newest offers
    offers = offers[:20]
    log.info(f"Processing the 20 newest offers out of {len(offer_elements)} found.")

    return process_offers(db, offers)


def process_offers(db: Database, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check and save new offers to the database.
    """
    offers_table = db["otomoto_offers"]
    new_offers = []

    for i, item in enumerate(items):
        try:
            offer_url = item["url"]
            offer_title = item["title"]

            # Check if the offer already exists in the database
            if offers_table.find_one(url=offer_url):
                log.debug(f"Item {i + 1} already exists in the database. Skipping.")
                continue

            # Save the new offer
            offer = {
                "url": offer_url,
                "title": offer_title,
                "posted_at": datetime.now(),
            }
            offers_table.insert(offer)
            new_offers.append(offer)
            log.info(f"New offer added: {offer_title} - {offer_url}")
        except Exception as e:
            log.error(f"Error processing item {i + 1}: {e}")

    log.info(f"New offers added: {len(new_offers)}")
    return new_offers


def parse_html_links(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Parse offer links from HTML.
    """
    offer_links = []
    articles = soup.find_all("article", class_="offer-item")  # Adjust class if needed
    for i, article in enumerate(articles):
        try:
            link_tag = article.find("a", href=True)
            if link_tag:
                url = link_tag["href"]
                offer_links.append({"url": url})
                log.debug(f"Found link for item {i + 1}: {url}")
            else:
                log.warning(f"No link found in article {i + 1}.")
        except Exception as e:
            log.error(f"Error parsing article {i + 1}: {e}")

    log.info(f"Extracted {len(offer_links)} links from HTML.")
    return offer_links


def generate_embed(item, sub_id):
    """
    Generate a Discord embed for a scraped offer.
    """
    embed = hikari.Embed(title=item["title"], url=item["url"], color=hikari.Color(0x09B1BA))
    embed.set_image(item.get("image_url", "https://via.placeholder.com/300"))
    embed.add_field("Price", item.get("price", "Unknown"), inline=True)
    embed.add_field("Mileage", item.get("mileage", "Unknown"), inline=True)
    embed.add_field("Fuel Type", item.get("fuel_type", "Unknown"), inline=True)
    embed.add_field("Transmission", item.get("transmission", "Unknown"), inline=True)
    embed.add_field("Year", item.get("year", "Unknown"), inline=True)
    embed.add_field("Location", item.get("location", "Unknown"), inline=True)
    embed.set_footer(f"Subscription #{sub_id}")
    return embed

