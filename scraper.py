import hikari
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Any, Dict
from loguru import logger as log
import logging
from bs4 import BeautifulSoup
import requests
from datetime import datetime

# Function to extract data from each offer
def extract_offer_data(offer_html):
    """Extracts data from an individual offer."""
    soup = BeautifulSoup(offer_html, "html.parser")
    try:
        # Check if the offer is promoted
        promoted_tag = soup.find(class_="ooa-1wmudpx")
        if promoted_tag and promoted_tag.text.strip() == "Wyróżnione":
            log.info("Skipping promoted offer.")
            return None

        # Extract Title and URL
        title_tag = soup.find('p', class_='e2z61p70 ooa-1ed90th er34gjf0')
        title = title_tag.text.strip() if title_tag else 'Unknown'
        url = title_tag.find('a')['href'] if title_tag and title_tag.find('a') else 'Unknown'

        # Extract Price
        price_tag = soup.find('h3', class_='e6r213i1 ooa-1n2paoq er34gjf0')
        price = price_tag.text.strip() if price_tag else 'Unknown'

        # Extract Image URL
        image_tag = soup.find('img', class_='e9xldqm4 ooa-2zzg2s')
        image_url = image_tag['src'] if image_tag and 'src' in image_tag.attrs else 'Unknown'

        # Extract other details
        mileage_element = soup.select_one('dd[data-parameter="mileage"]')
        mileage = mileage_element.text.strip() if mileage_element else "Unknown"

        fuel_element = soup.select_one('dd[data-parameter="fuel_type"]')
        fuel = fuel_element.text.strip() if fuel_element else "Unknown"

        gearbox_element = soup.select_one('dd[data-parameter="gearbox"]')
        gearbox = gearbox_element.text.strip() if gearbox_element else "Unknown"

        year_element = soup.select_one('dd[data-parameter="year"]')
        year = year_element.text.strip() if year_element else "Unknown"

        location_element = soup.select_one('dd.ooa-1jb4k0u.ecru18x15 p.ooa-gmxnzj')
        location = location_element.text.strip() if location_element else "Unknown"

        return {
            'url': url,
            'title': title,
            'price': price,
            'image_url': image_url,
            'mileage': mileage,
            'fuel': fuel,
            'gearbox': gearbox,
            'year_of_production': year,
            'location': location,
            'posted_at': datetime.now()
        }
    except Exception as e:
        log.error(f"Error extracting data from offer: {e}")
        return None

# Function to validate URL
def validate_url(url):
    """Validates the URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return bool(parsed.netloc) and parsed.scheme in ['http', 'https']

def validate_offer(offer):
    """Validates that an offer contains sufficient information."""
    required_fields = ['url', 'title', 'price', 'image_url']
    for field in required_fields:
        if offer.get(field) == 'Unknown':
            return False
    return True

# Main scraping function
def scrape_otomoto_updated(url, db=None, subscription_id=None):
    """Scrapes the Otomoto website for offers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }

    try:
        log.info(f"Requesting URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the page content
        soup = BeautifulSoup(response.text, 'html.parser')
        offers = soup.select('article')[:20]  # Limit to the latest 20 offers
        log.info(f"Found {len(offers)} offers on the page.")

        offer_data_list = []
        for offer_html in offers:
            offer_data = extract_offer_data(str(offer_html))
            if offer_data and validate_offer(offer_data):
                if db and subscription_id:
                    existing_offer = db["offers"].find_one(url=offer_data["url"], subscription_id=subscription_id)
                    if not existing_offer:
                        offer_data['subscription_id'] = subscription_id
                        db["offers"].insert(offer_data)
                        offer_data_list.append(offer_data)
                else:
                    offer_data_list.append(offer_data)

        return offer_data_list
    except requests.exceptions.RequestException as e:
        log.error(f"HTTP error during scraping: {e}")
    except Exception as e:
        log.error(f"Unexpected error: {e}")
    return []

def process_offers(offers, db, subscription_id, discord_channel):
    """
    Process offers and save new ones to the database.
    Send a Discord message for new offers.
    """
    for offer in offers:
        existing_offer = db['otomoto_offers'].find_one(url=offer['url'], subscription_id=subscription_id)

        if not existing_offer:
            # Add metadata for the new offer
            offer['subscription_id'] = subscription_id
            offer['posted_at'] = datetime.now()

            # Insert into the database
            db['otomoto_offers'].insert(offer)
            log.info(f"New offer added for subscription {subscription_id}: {offer['title']}")

            # Create a Discord embed message
            embed = generate_embed(offer)

            # Send the embed to Discord
            try:
                discord_channel.send(embed=embed)
                log.info(f"Discord message sent for offer: {offer['title']}")
            except Exception as e:
                log.error(f"Error sending Discord message for {offer['title']}: {e}")
        else:
            log.debug(f"Offer already exists in subscription {subscription_id}: {offer['title']}")

def generate_embed(offer):
    """Generate a Discord embed from the offer data."""
    try:
        embed = hikari.Embed(
            title=f"**{offer.get('title', 'No Title')}**",  # Make title bold
            url=offer.get("url", ""),
            description=f"**Price:** {offer.get('price', 'Unknown')}\n"
                        f"Mileage: {offer.get('mileage', 'Unknown')}\n"
                        f"Fuel: {offer.get('fuel', 'Unknown')}\n"
                        f"Gearbox: {offer.get('gearbox', 'Unknown')}\n"
                        f"Year: {offer.get('year_of_production', 'Unknown')}\n"
                        f"Location: {offer.get('location', 'Unknown')}",
            color=0x00ff00
        )
        if "image_url" in offer and offer["image_url"]:
            embed.set_image(offer["image_url"])
        # Format datetime to exclude microseconds
        posted_at = offer.get('posted_at', 'Unknown')
        if isinstance(posted_at, datetime):
            posted_at = posted_at.strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"Posted at: {posted_at}")
        return embed
    except Exception as e:
        log.error(f"Failed to generate embed: {e}")
        return None
