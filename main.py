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
def get_klines(symbol: str, interval="12h", limit=200):
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

# Ask OpenAI for analysis
def ask_question_with_rules(symbol: str):
    openai.api_key = OPENAI_KEY
    try:
        # Get OHLC data
        kline_data = get_klines(symbol, interval="12h", limit=100)
        if isinstance(kline_data, dict) and "error" in kline_data:
            return {"error": kline_data["error"]}
        
        question = f"The {symbol} token OHLC data is: {json.dumps(kline_data)}"
        
        # Send to OpenAI for analysis
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional financial advisor. Analyze the OHLC "
                        "data provided and provide actionable insights as follows:\n"
                        "1. Market Trend Analysis\n"
                        "2. Indicator Analysis\n"
                        "3. Buy Point Suggestion\n"
                        "4. Sell Point Suggestion\n"
                        "5. Risk and Reward Assessment\n"
                        "Example: \n"
                        "📊 **Analysis for #LTCUSDT**\n"
                        "1. **Market Trend:** The market is showing a sideways trend with mixed signals from candlestick patterns. The RSI and MACD are inconclusive. SMA20 indicates stability, while ADX suggests a lack of clear trend direction.\n"
                        "2. **Indicator Analysis:** Moving averages crossover indicates potential price reversal. RSI and MACD are flat, showing indecision. Bollinger Bands are narrowing, signaling a possible breakout.\n"
                        "3. **Buy Point:** Consider buying at $\"150.25\" after a confirmed breakout above resistance levels.\n"
                        "4. **Sell Point:** Sell at $\"165.50\" to lock in profits and set a stop-loss at $\"140.75\".\n"
                        "5. **Risk and Reward:** Risk-reward ratio is 1:2, with potential upside at 10% and downside at 5%. 🚀📉\n"
                        "Respond in under 80 words, in Markdown format with a touch of humor."
                    ),
                },
                {"role": "user", "content": question},
            ],
        )

        # Extract and format response
        answer = response['choices'][0]['message']['content']
        return {"success": True, "analysis": answer}
    except Exception as e:
        return {"error": f"Error with OpenAI API: {e}"}

# Define API endpoint
@app.route("/analyze", methods=["GET"])
def analyze_coin():
    name_pair = request.args.get("name_pair")
    if not name_pair:
        return jsonify({"error": "name_pair parameter is required."}), 400

    result = ask_question_with_rules(name_pair)
    return jsonify(result)

if __name__ == "__main__":
    # Parse port from command line arguments
    parser = argparse.ArgumentParser(description="Run the Flask API server.")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on (default: 5000).")
    args = parser.parse_args()

    # Run the Flask app on the specified port
    app.run(debug=True, port=args.port)
