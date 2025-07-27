import ccxt
import pandas as pd
import os
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

exchange = ccxt.xt()

def get_usdt_symbols():
    wanted = ["BTC", "ETH", "XRP", "ADA", "LINK", "DOT", "TET", "AVAX", "PONKE", "ALGO", "SEI", "CAKE", "BNB"]
    symbols = []
    try:
        markets = exchange.load_markets()
        for coin in wanted:
            symbol = coin.upper() + "/USDT"
            if symbol in markets:
                symbols.append(symbol)
        return symbols
    except Exception as e:
        print(f"❗ خطا در دریافت بازارها: {e}")
        return []

def get_ohlcv(symbol="BTC/USDT", timeframe="1h", limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    if len(ohlcv) < 50:
        raise ValueError(f"داده ناکافی برای {symbol}")
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df.astype(float)
    return df

def analyze(df, symbol):
    close = df["close"]
    current_price = close.iloc[-1]

    rsi_val = RSIIndicator(close, window=14).rsi().iloc[-1]
    ema_val = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
    bb = BollingerBands(close, window=20)
    bb_high = bb.bollinger_hband().iloc[-1]
    bb_low = bb.bollinger_lband().iloc[-1]
    macd = MACD(close)
    macd_val = macd.macd().iloc[-1]
    signal_val = macd.macd_signal().iloc[-1]

    if rsi_val < 30:
        rsi_status = "🟢 اشباع فروش"
    elif rsi_val > 70:
        rsi_status = "🔴 اشباع خرید"
    else:
        rsi_status = "➖ وضعیت خنثی"

    ema_status = "🟢 بالاتر از EMA" if current_price > ema_val else "🔴 پایین‌تر از EMA"

    if current_price < bb_low:
        bb_status = "🟢 زیر باند پایین → احتمال رشد"
    elif current_price > bb_high:
        bb_status = "🔴 بالای باند بالا → احتمال اصلاح"
    else:
        bb_status = "➖ بین باندها"

    if macd_val > signal_val:
        macd_status = "🟢 بالای Signal → روند صعودی"
    else:
        macd_status = "🔴 زیر Signal → روند نزولی"

    if rsi_val < 30 or macd_val > signal_val:
        recommendation = "📈 **پیشنهاد خرید**"
    elif rsi_val > 70 or macd_val < signal_val:
        recommendation = "📉 **پیشنهاد فروش**"
    else:
        recommendation = "⚪️ وضعیت خنثی، صبر کنید"

    message = f"""
📊 تحلیل {symbol}

📈 قیمت فعلی: {current_price:.2f} USDT

🧠 وضعیت اندیکاتورها:
• RSI (14): {rsi_val:.2f} {rsi_status}
• EMA (20): {ema_val:.2f} {ema_status}
• MACD: {macd_val:.3f} {macd_status}
• Bollinger Bands:
   ↳ بالا: {bb_high:.2f}
   ↳ پایین: {bb_low:.2f}
   ↳ {bb_status}

{recommendation}
"""
    return message.strip()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"❗ خطا در ارسال پیام: {e}")

def main():
    symbols = get_usdt_symbols()
    for symbol in symbols:
        try:
            df = get_ohlcv(symbol)
            message = analyze(df, symbol)

            if "پیشنهاد خرید" in message or "پیشنهاد فروش" in message:
                send_telegram_message(message)

        except Exception as e:
            print(f"❗ خطا در تحلیل {symbol}: {e}")

if __name__ == "__main__":
    main()