# Install all dependencies
!pip install yfinance --quiet
!pip install requests beautifulsoup4 --quiet

import yfinance as yf
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# Fetch dynamic sector P/E benchmarks using ETF proxies
def fetch_sector_pe_ratios():
    sectors = {
        "Information Technology": "XLK",
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Healthcare": "XLV",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Real Estate": "XLRE",
        "Utilities": "XLU",
        "Communication Services": "XLC"
    }
    pe_ratios = {}
    for sector, ticker in sectors.items():
        try:
            data = yf.Ticker(ticker).info
            pe = data.get("trailingPE")
            if pe:
                pe_ratios[sector] = pe
        except:
            pass
    return pe_ratios

industry_pe_ratios = fetch_sector_pe_ratios()

# Get live news headlines from Yahoo Finance
def get_news_headlines(ticker):
    url = f'https://finance.yahoo.com/quote/{ticker}?p={ticker}'
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        headlines = soup.find_all('h3', limit=5)
        news = []
        for h in headlines:
            text = h.text.strip()
            if text and len(text) > 5:
                news.append(f"📰 {text}")
        return "\n".join(news) if news else "No recent headlines found."
    except Exception as e:
        return f"Could not retrieve headlines: {str(e)}"

# Analyze stock data and respond based on user intent
def answer_question(ticker, intent):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get("longName", ticker)
        pe_ratio = info.get("trailingPE", None)
        sector = info.get("sector", "Unknown")
        dividend = info.get("dividendYield", None)
        cap = info.get("marketCap", None)
        # sector_pe = industry_pe_ratios.get(sector, None)

        # Normalizaiton
        sector_aliases = {
            "Technology": "Information Technology",
            "Information Technology": "Information Technology",
            "Financials": "Financials",
            "Energy": "Energy",
            "Consumer Discretionary": "Consumer Discretionary",
            "Consumer Cyclical": "Consumer Discretionary",
            "Consumer Staples": "Consumer Staples",
            "Consumer Defensive": "Consumer Staples",
            "Healthcare": "Healthcare",
            "Industrials": "Industrials",
            "Materials": "Materials",
            "Real Estate": "Real Estate",
            "Utilities": "Utilities",
            "Communication Services": "Communication Services",
            "Telecommunication Services": "Communication Services"
        }
        sector_normalized = sector_aliases.get(sector, sector)
        sector_pe = industry_pe_ratios.get(sector_normalized, None)
        # Normalization

        if "news" in intent:
            return f"🗞 News for {ticker}:\n" + get_news_headlines(ticker)

        if "dividend" in intent:
            if dividend:
                return f"{name} ({ticker}) currently offers a dividend yield of {dividend*100:.2f}%."
            else:
                return f"{name} ({ticker}) does not currently offer a dividend."

        if "market cap" in intent:
            if cap:
                return f"{name} ({ticker}) has a market capitalization of ${cap:,}."
            else:
                return f"Market cap information is not available for {ticker}."

        if not pe_ratio:
            return f"{name} ({ticker}) does not have a valid P/E ratio available at the moment."

        analysis = f"📊 {name} ({ticker})\n- Sector: {sector}\n- P/E Ratio: {pe_ratio:.2f}"
        if sector_pe:
            analysis += f"\n- Sector Average P/E: {sector_pe:.2f}"
            if pe_ratio > sector_pe * 1.3:
                valuation_msg = "⚠️ This stock appears overvalued relative to its sector average."
            elif pe_ratio < sector_pe * 0.7:
                valuation_msg = "✅ This stock appears undervalued compared to sector peers."
            else:
                valuation_msg = "🔍 This stock's valuation is in line with sector norms."
        else:
            valuation_msg = "⚠️ Sector benchmark unavailable for precise valuation."

        if "buy" in intent or "invest" in intent:
            return analysis + f"\n\nWould I consider buying {ticker}?\n{valuation_msg}"
        elif "sell" in intent:
            return analysis + f"\n\nConsidering selling {ticker}?\n{valuation_msg}"
        elif "hold" in intent:
            return analysis + f"\n\nThinking about holding {ticker}?\n{valuation_msg}"
        else:
            return analysis + f"\n\nValuation Insight:\n{valuation_msg}"
    except Exception as e:
        return f"❌ Error retrieving info for {ticker}: {str(e)}"

# Main assistant logic
def financial_assistant(query):
    query_lower = query.lower()
    tickers_in_query = re.findall(r'\b[A-Z]{2,5}\b', query)

    if "buy" in query_lower or "invest" in query_lower:
        intent = "buy"
    elif "sell" in query_lower:
        intent = "sell"
    elif "hold" in query_lower:
        intent = "hold"
    elif "dividend" in query_lower:
        intent = "dividend"
    elif "market cap" in query_lower:
        intent = "market cap"
    elif "news" in query_lower:
        intent = "news"
    elif "p/e" in query_lower or "valuation" in query_lower:
        intent = "valuation"
    else:
        intent = "general"

    if not tickers_in_query:
        return "❓ I couldn’t find a stock ticker in your question. Try something like 'Should I buy AAPL?' or 'What’s NVDA’s valuation?'"

    responses = [answer_question(ticker, intent) for ticker in tickers_in_query]
    responses.append("\n🚨 Disclaimer: This tool is not licensed financial advice. Please consult a professional before making investment decisions.")
    return "\n\n".join(responses)

# UI + Prompt
print("💬 Welcome to your Financial Assistant!")
print("✅ I can answer:\n- Buy/sell/hold decisions\n- Valuation analysis using P/E\n- Market cap and dividends\n- Sector comparisons\n- Real-time Yahoo Finance headlines")
print("❌ I cannot execute trades or give personalized tax advice.\n")

user_query = input("🔎 Ask your question (e.g., 'Should I buy AAPL?', 'What’s JPM’s market cap?', 'News about NVDA'):\n\n")
response = financial_assistant(user_query)
print("\n" + response)
