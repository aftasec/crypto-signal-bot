import ccxt
import pandas as pd
import requests
import time
import os
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

symbols = [
    "BTC/USDT", "ETH/USDT", "XRP/USDT", "ADA/USDT", "LINK/USDT", "DOT/USDT",
    "TET/USDT", "AVAX/USDT", "PONKE/USDT", "SEI/USDT", "ALGO/USDT", "CAKE/USDT", "BNB/USDT"
]

exchange = ccxt.xt()

def get_ohlcv(symbol, timeframe="1h", limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if len(ohlcv) < 20:
            raise ValueError(f"داده ناکافی برای {symbol}")
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df.astype(float)
    except Exception as e:
        print(f"❗ خطا در دریافت داده {symbol}: {e}")
        return None

def analyze(df, symbol):
    close = df["close"]
    current_price = close.iloc[-1]

    rsi = RSIIndicator(close).rsi().iloc[-1]
    rsi_status = "🟢 اشباع فروش" if rsi < 30 else "🔴 اشباع خرید" if rsi > 70 else "➖ نرمال"

    ema20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
    ema_status = "🟢 بالاتر از EMA" if current_price > ema20 else "🔴 پایین‌تر از EMA"

    macd_line = MACD(close).macd().iloc[-1]
    macd_signal = MACD(close).macd_signal().iloc[-1]
    macd_status = "🟢 بالای Signal → صعودی" if macd_line > macd_signal else "🔴 زیر Signal → نزولی"

    bb = BollingerBands(close)
    bb_high = bb.bollinger_hband().iloc[-1]
    bb_low = bb.bollinger_lband().iloc[-1]
    if current_price < bb_low:
        bb_status = "🟢 زیر باند پایین → احتمال رشد"
    elif current_price > bb_high:
        bb_status = "🔴 بالای باند بالا → احتمال اصلاح"
    else:
        bb_status = "➖ بین باندها"

    message = f"""
📊 تحلیل {symbol}
📈 قیمت: {current_price:.2f} USDT

• RSI: {rsi:.2f} {rsi_status}
• EMA20: {ema20:.2f} {ema_status}
• MACD: {macd_line:.3f} {macd_status}
• Bollinger: {bb_status}
"""
    return message.strip()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❗ خطا در ارسال پیام: {e}")

def main():
    for symbol in symbols:
        df = get_ohlcv(symbol)
        if df is not None:
            try:
                msg = analyze(df, symbol)
                send_telegram_message(msg)
            except Exception as e:
                print(f"❗ خطا در تحلیل {symbol}: {e}")

# اجرای خودکار هر ۱۵ دقیقه
if __name__ == "__main__":
    while True:
        main()
        time.sleep(15 * 60)
