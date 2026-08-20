import os
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

#Şifreleri GitHub Secrets üzerinden güvenli alır
TELEGRAM_TOKEN = OS.environ.get("TELEGRAM_TOKEN")
TELEGRAM_TOKEN = OS.environ.get("TELEGRAM_CHAT_ID")

TEMETTÜ_FAVORILER = [
  "EREGLI.IS", "TUPRS.IS", "FROTO.IS", "SISE.IS",
  "BIMAS.IS", "TOASO.IS", "TTRAK.IS", "TCELL.IS"
]

BIST100_ORNEK = [
  "THYAO.IS", "ASELS.IS", "KCHOL.IS" "GARAN.IS", "AKBNK.IS", "SAHOL,IS"
]

ALL_TICKERS = list(set(TEMETTU_FAVORILER + BIST100_ORNEK))

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
      print(f" ⚠️ Telegram hatası: {res.text}")
  except Exception as e:
    print("Telegram hatası:", e)

def get_data(ticker):
  try:
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
  
      
