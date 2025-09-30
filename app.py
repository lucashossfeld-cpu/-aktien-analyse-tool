import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import pandas_ta as ta

# --- Cache: verhindert zu viele Requests ---
@st.cache_data(ttl=300)  # Cache für 5 Minuten
def load_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo", interval="1d")
    return stock, hist

# --- Konfiguration ---
st.set_page_config(page_title="Aktien Analyse Tool", layout="wide")
st.title("📈 Aktien Analyse Tool mit Echtzeitdaten")

# --- Eingabe ---
ticker = st.text_input("Gib den Ticker ein (z.B. AAPL, TSLA, BAS.DE):", "AAPL")

# --- Funktion für Analyse ---
def analyse_stock(ticker):
    stock, hist = load_data(ticker)
    if hist.empty:
        return None

    # Technische Indikatoren
    hist["RSI"] = ta.rsi(hist["Close"], length=14)
    hist["SMA50"] = ta.sma(hist["Close"], length=50)
    hist["SMA200"] = ta.sma(hist["Close"], length=200)
    macd_df = ta.macd(hist["Close"])
    hist["MACD"] = macd_df.iloc[:, 0]
    hist["MACD_signal"] = macd_df.iloc[:, 1]

    latest_rsi = hist["RSI"].iloc[-1]
    latest_macd = hist["MACD"].iloc[-1]
    latest_macd_signal = hist["MACD_signal"].iloc[-1]

    # Scores
    tech_score = 1 if latest_rsi < 30 else -1 if latest_rsi > 70 else 0
    trend_score = 1 if hist["SMA50"].iloc[-1] > hist["SMA200"].iloc[-1] else -1
    macd_score = 1 if latest_macd > latest_macd_signal else -1
    volatility = hist["Close"].pct_change().std() * 100
    risk_score = 1 if volatility < 1 else 0 if volatility < 2 else -1

    final_score = tech_score + trend_score + macd_score + risk_score
    if final_score >= 2:
        decision = "BUY"
    elif final_score <= -2:
        decision = "SELL"
    else:
        decision = "HOLD"

    return {
        "ticker": ticker,
        "decision": decision,
        "score": final_score,
        "rsi": latest_rsi,
        "volatility": volatility
    }

if ticker:
    try:
        stock, hist = load_data(ticker)

        if hist.empty:
            st.error("Keine Daten gefunden. Bitte überprüfe den Ticker.")
        else:
            # --- Indikatoren ---
            hist["RSI"] = ta.rsi(hist["Close"], length=14)
            hist["SMA50"] = ta.sma(hist["Close"], length=50)
            hist["SMA200"] = ta.sma(hist["Close"], length=200)
            macd_df = ta.macd(hist["Close"])
            hist["MACD"] = macd_df.iloc[:, 0]
            hist["MACD_signal"] = macd_df.iloc[:, 1]

            # --- Kurs ---
            kurs_usd = hist["Close"].iloc[-1]
            eurusd = yf.Ticker("EURUSD=X").history(period="1d")
            kurs_eur = kurs_usd / eurusd["Close"].iloc[-1]

            st.metric("Aktueller Kurs (USD)", f"{kurs_usd:.2f} $")
            st.metric("Aktueller Kurs (EUR)", f"{kurs_eur:.2f} €")

            # --- Chart ---
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

            # --- Analyse für Haupt-Ticker ---
            result = analyse_stock(ticker)
            if result:
                st.subheader("Investitionsentscheidung")
                st.write(f"**Empfehlung:** {result['decision']} (Score {result['score']})")
                st.write(f"RSI: {result['rsi']:.2f}")
                st.write(f"Volatilität: {result['volatility']:.2f}%")

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

            # --- Top 5 Buy Aktien ---
            st.subheader("📊 Top 5 aktuelle BUY Aktien")

            # Beobachtungsliste (kannst du erweitern)
            watchlist = ["AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "GOOGL",
                         "JNJ", "JPM", "XOM", "PG", "KO", "BAS.DE", "SAP.DE", "SIE.DE"]

            results = []
            for t in watchlist:
                try:
                    res = analyse_stock(t)
                    if res and res["decision"] == "BUY":
                        results.append(res)
                except Exception:
                    pass

            # Sortieren nach Score, absteigend
            results = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

            if results:
                for r in results:
                    st.write(f"✅ {r['ticker']} → Score {r['score']} (RSI {r['rsi']:.1f}, Volatilität {r['volatility']:.2f}%)")
            else:
                st.write("Keine aktuellen BUY-Signale in der Beobachtungsliste.")

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
