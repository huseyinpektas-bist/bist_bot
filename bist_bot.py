import os
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

# Şifreleri GitHub Secrets üzerinden alır
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 💰 TEMETTÜ FAVORİLERİ
TEMETTU_FAVORILER = [
    "EREGL.IS", "TUPRS.IS", "FROTO.IS", "SISE.IS", 
    "BIMAS.IS", "TOASO.IS", "TTRAK.IS", "TCELL.IS"
]

# 📈 GENİŞ BIST & FIRSAT HİSSELERİ LİSTESİ
BIST100_GENIS = [
    "THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS", "SAHOL.IS",
    "YKBNK.IS", "ISCTR.IS", "VAKBN.IS", "PGSUS.IS", "MGROS.IS", "CCHOL.IS",
    "ENKAI.IS", "ALARK.IS", "ASTOR.IS", "SASA.IS",  "HEKTAS.IS", "OYAKC.IS",
    "KRDMD.IS", "PETKM.IS", "TAVHL.IS", "KOZAL.IS", "EKGYO.IS", "GUBRF.IS",
    "BRSAN.IS", "KONTR.IS", "REEDR.IS"
]

ALL_TICKERS = list(set(TEMETTU_FAVORILER + BIST100_GENIS))

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bilgileri eksik!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            print("✅ Telegram bildirimi başarıyla gönderildi!")
        else:
            print(f"⚠️ Telegram hatası: {res.text}")
    except Exception as e:
        print("Telegram hatası:", e)

def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 50:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return None

def calculate_indicators(df):
    close = df['Close']
    high = df['High']
    volume = df['Volume']

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    vol_avg = volume.rolling(20).mean()
    is_green = close > df['Open']
    vol_spike = (volume > (vol_avg * 1.5)) & is_green

    high_20 = high.shift(1).rolling(20).max()
    breakout = close > high_20

    return {
        'price': close.iloc[-1],
        'rsi': rsi.iloc[-1],
        'macd': macd.iloc[-1],
        'macd_sig': signal.iloc[-1],
        'vol_spike': vol_spike.iloc[-1],
        'breakout': breakout.iloc[-1],
        'trend_ok': ema20.iloc[-1] > ema50.iloc[-1]
    }

def analyze():
    msg = f"📊 *BIST FIRSAT & TEMETTÜ TARAMASI*\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    msg += f"🔍 Taranan Hacimli Hisse Sayısı: {len(ALL_TICKERS)}\n"
    msg += "-----------------------------------\n\n"

    xu100 = get_data("XU100.IS")
    market_safe = True
    if xu100 is not None:
        c = xu100['Close']
        e20 = c.ewm(span=20, adjust=False).mean().iloc[-1]
        if c.iloc[-1] < e20:
            market_safe = False
            msg += "⚠️ *UYARI:* BIST 100 Endeksi 20 günlük ortalamanın altında! Temkinli olun.\n\n"

    results = []

    for ticker in ALL_TICKERS:
        df = get_data(ticker)
        if df is None: continue

        ind = calculate_indicators(df)
        score = 0
        if ind['trend_ok']: score += 25
        if ind['macd'] > ind['macd_sig']: score += 20
        if 40 <= ind['rsi'] <= 65: score += 20
        if ind['vol_spike']: score += 20
        if ind['breakout']: score += 15

        if not market_safe: score = int(score * 0.8)

        symbol = ticker.replace('.IS', '')
        tag = "💰 [TEMETTÜ]" if ticker in TEMETTU_FAVORILER else "📈 [BIST]"

        risk = "DÜŞÜK"
        if ind['rsi'] > 70: risk = "YÜKSEK (Aşırı Alım)"
        elif not market_safe: risk = "ORTA (Piyasa Baskısı)"

        status = "⚪ İZLEMEDE"
        if score >= 80: status = "🔥 GÜÇLÜ SİNYAL"
        elif score >= 65: status = "🟢 GÜÇLENİYOR"

        # Yalnızca 60 ve üzeri skora sahip (fırsat veren) hisseler Telegram'a atılır
        if score >= 60:
            results.append(f"{tag} *{symbol}*\nFiyat: {round(ind['price'], 2)} TL | Skor: {score}/100\nDurum: {status} | Risk: {risk}\n")

    if results:
        msg += "\n".join(results)
    else:
        msg += "Bugün yüksek teknik skorlu (60+) fırsat veren hisse bulunamadı."

    send_telegram_message(msg)

if __name__ == "__main__":
    analyze()
