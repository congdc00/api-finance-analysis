import os
import requests
import random
from dotenv import load_dotenv
import time
# Load environment variables from .env file
load_dotenv()

# Constants
API_URL = os.getenv("API_URL", "http://127.0.0.1:8188/analyze")  # Default API URL
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Telegram Bot Token
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Telegram Chat ID

# List of trading pairs
TRADING_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
    "DOGEUSDT", "DOTUSDT", "SOLUSDT", "MATICUSDT", "LTCUSDT",
    "SHIBUSDT", "AVAXUSDT", "ALGOUSDT"
]

# Function to randomly select a trading pair
def get_random_pair():
    """Randomly selects a trading pair from the predefined list."""
    return random.choice(TRADING_PAIRS)

# Function to fetch analysis from the API
def get_analysis_from_api(name_pair):
    """
    Sends a GET request to the API to fetch analysis for the given trading pair.

    Args:
        name_pair (str): The trading pair symbol (e.g., 'BTCUSDT').

    Returns:
        dict: The API response containing analysis or error details.
    """
    try:
        response = requests.get(API_URL, params={"name_pair": name_pair})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching analysis: {e}")
        return {"error": str(e)}

# Function to send a message to Telegram
def send_message_to_telegram(message):
    """
    Sends a message to a Telegram chat using the Telegram Bot API.

    Args:
        message (str): The message content to send to Telegram.
    """
    try:
        telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(telegram_api_url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })
        response.raise_for_status()
        print("Message sent to Telegram successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

# Main function
if __name__ == "__main__":
    
    # schedule sending messages to Telegram every 2 hours 

    
    while True:
        random_pair = get_random_pair()
        print(f"Selected trading pair: {random_pair}")

        # Fetch analysis from the API
        analysis = get_analysis_from_api(random_pair)
        if "error" in analysis:
            print(f"Error in analysis: {analysis['error']}")
        else:
            # Prepare the message and send it to Telegram
            message = f"📊 **Analysis for {random_pair}**\n{analysis['analysis']}"
            send_message_to_telegram(message)
        time.sleep(7200)
