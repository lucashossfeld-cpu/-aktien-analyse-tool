import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import pandas_ta as ta

# --- Streamlit Grundkonfiguration ---
st.set_page_config(page_title="Aktien Analyse Tool", layout="wide")
st.title("📈 Aktien Analyse Tool mit Echtzeitdaten")

# --- Eingabe für Ticker ---
ticker = st.text_input("Gib den Aktienticker ein (z.B. AAPL, TSLA, BAS.DE):", "AAPL")

if ticker:
    try:
        # --- Daten laden (6 Monate, Tagesdaten) ---
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo", interval="1d")

        if hist.empty:
            st.error("Keine Daten gefunden. Bitte überprüfe den Ticker.")
        else:
            # --- Technische Indikatoren ---
            hist["RSI"] = ta.rsi(hist["Close"], length=14)
            hist["SMA50"] = ta.sma(hist["Close"], length=50)
            hist["SMA200"] = ta.sma(hist["Close"], length=200)

            # --- Chart erstellen ---
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist["Open"],
                high=hist["High"],
                low=hist["Low"],
                close=hist["Close"],
                name="Kurs"
            ))
            fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA50"], mode="lines", name="SMA 50"))
            fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA200"], mode="lines", name="SMA 200"))

            st.plotly_chart(fig, use_container_width=True)

            # --- RSI Bewertung ---
            latest_rsi = hist["RSI"].iloc[-1]
            st.metric("Aktueller RSI", f"{latest_rsi:.2f}")

            # --- Einfache Kauf-/Verkaufsentscheidung ---
            if latest_rsi < 30:
                decision = "✅ BUY (überverkauft)"
            elif latest_rsi > 70:
                decision = "❌ SELL (überkauft)"
            else:
                decision = "🤝 HOLD"

            st.subheader("Investitionsentscheidung:")
            st.write(decision)

            # --- Unternehmensinfos ---
            st.subheader("Unternehmensinformationen")
            info = stock.info
            st.write({
                "Name": info.get("longName"),
                "Sektor": info.get("sector"),
                "Branche": info.get("industry"),
                "Marktkapitalisierung": info.get("marketCap"),
                "KGV": info.get("forwardPE"),
                "Dividendenrendite": info.get("dividendYield"),
            })

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
