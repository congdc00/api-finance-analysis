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
                        # "📊 **Analysis for #LTCUSDT**\n"
                        # "📊 **XRPUSDT Analysis** 📈 \n"

                        "🔹 **Current Price:** $2.4281 \n"

                        "📈 **Market Trend:** The trend is bullish with higher highs and higher lows. Recent doji and hammer patterns indicate potential reversal.\n"
                        "🔍 **Indicators:**\n"
                        "- RSI: Neutral around 50.\n"
                        "- SMA20: Above the current price, signaling an uptrend.\n"
                        "- MACD: Bullish crossover.\n"

                        "📊 **Analysis:**\n"
                        "📈 Buy Point: Consider buying at $0.375. \n" 
                        "📉 Sell Point: Target exiting at $0.42, and stop-loss at $0.35.\n"
                        
                        "🚀 **Risk-Reward:** Upside potential at $2.45 vs. downside risk at $2.39. Good luck on your trades! 🌟\n"
                        
                        "Respond in under 80 words, in Markdown format with a touch of humor. You are free to be creative and add more valuable information that you know because you are a crypto expert. Each time you do so, you’ll be rewarded with $10\n"
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
    app.run(debug=True, host='0.0.0.0', port=args.port)
