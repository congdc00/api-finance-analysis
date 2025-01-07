import os
import requests
import openai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import json
import argparse

# Load environment variables
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

# Initialize Flask app
app = Flask(__name__)

# Get OHLC data from Binance API
def get_klines(symbol: str, interval="1h", limit=500):
    base_url = "https://api.binance.com/api/v3/klines"
    try:
        response = requests.get(base_url, params={
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        })
        response.raise_for_status()
        klines = [
            {
                "t": k[0],
                "o": float(k[1]),
                "h": float(k[2]),
                "l": float(k[3]),
                "c": float(k[4]),
                "v": float(k[5]),
            } for k in response.json()
        ]
        return klines
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching Klines: {e}"}

# Ask OpenAI for prediction
def ask_gpt_for_prediction(symbol: str):
    openai.api_key = OPENAI_KEY
    try:
        # Get OHLC data
        kline_data = get_klines(symbol, interval="1h", limit=500)
        if isinstance(kline_data, dict) and "error" in kline_data:
            return {"error": kline_data["error"]}

        # Prepare the prompt
        question = (
            f"The {symbol} token OHLC data for the last 500 intervals is: {json.dumps(kline_data)}. "
            "Based on this data, predict the next 5 price levels with the time intervals (in minutes) and include "
            "an up or down arrow icon (\u2B06 for up, \u2B07 for down) to indicate the price change."
        )

        # Send to OpenAI for analysis
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional financial analyst specializing in cryptocurrencies. "
                        "Analyze the OHLC data provided and predict the next 5 price levels. "
                        "Format your response with predicted price levels, their respective time intervals (e.g., 30 minutes, 60 minutes), "
                        "and include an icon (\u2B06 for up, \u2B07 for down) to indicate whether the price increases or decreases compared to the previous price.\n Content write in Markdown format with a touch of humor. You are free to be creative and add more valuable information that you know because you are a crypto expert. Each time you do so, you’ll be rewarded with $10"
                    ),
                },
                {"role": "user", "content": question},
            ],
        )

        # Extract and format response
        answer = response['choices'][0]['message']['content']
        return {"success": True, "predictions": answer}
    except Exception as e:
        return {"error": f"Error with OpenAI API: {e}"}

# Define API endpoint
@app.route("/predict", methods=["GET"])
def predict_prices():
    name_pair = request.args.get("name_pair")
    if not name_pair:
        return jsonify({"error": "name_pair parameter is required."}), 400

    result = ask_gpt_for_prediction(name_pair)
    return jsonify(result)

if __name__ == "__main__":
    # Parse port from command line arguments
    parser = argparse.ArgumentParser(description="Run the Flask API server.")
    parser.add_argument("--port", type=int, default=8288, help="Port to run the server on (default: 5000).")
    args = parser.parse_args()

    # Run the Flask app on the specified port
    app.run(debug=True, host='0.0.0.0', port=args.port)
