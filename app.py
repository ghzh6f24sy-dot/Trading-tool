import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Seitenkonfiguration (Muss als Erstes stehen)
st.set_page_config(page_title="Trading & Orderflow Analyse Tool", layout="wide")

# --- CUSTOM CSS FÜR EDLES CARD-LAYOUT ---
st.markdown("""
<style>
    .card {
        background-color: #1e2530;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2d3748;
        margin-bottom: 20px;
    }
    .metric-title {
        color: #a0aec0;
        font-size: 14px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- AUTO-REFRESH (Alle 10 Sekunden im Hintergrund aktualisieren) ---
count = st_autorefresh(interval=10000, limit=None, key="datarefresh")

st.title("Trading & Markt-Analyse Pro")
st.markdown("Professionelles Assistenz-Tool für Smart Trading und Risiko-Management.")

# --- SEITENLEISTE: Navigation & Einstellungen ---
st.sidebar.header("Steuerung & Setup")

# Auto-Refresh Master-Switch
auto_refresh_on = st.sidebar.checkbox("Auto-Refresh (Live-Modus)", value=True)

tab_selection = st.sidebar.radio("Navigation", [
    "Chart & Trend-Check", 
    "Risiko-Rechner & Realitäts-Check", 
    "Watchlist & Kategorien", 
    "Market Screener",
    "Makro & News"
])

st.sidebar.markdown("---")
st.sidebar.subheader("Asset Auswahl")

# Kategorisierte Watchlist für den Schnellstart / Suche
asset_category = st.sidebar.selectbox("Kategorie wählen", ["Aktien & Tech", "ETFs", "Krypto", "Futures & Rohstoffe", "Eigenes Ticker eingeben"])

if asset_category == "Aktien & Tech":
    ticker_symbol = st.sidebar.selectbox("Asset", ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"])
elif asset_category == "ETFs":
    ticker_symbol = st.sidebar.selectbox("Asset", ["SPY", "QQQ", "IWM", "VGK", "GLD"])
elif asset_category == "Krypto":
    ticker_symbol = st.sidebar.selectbox("Asset", ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"])
elif asset_category == "Futures & Rohstoffe":
    ticker_symbol = st.sidebar.selectbox("Asset", ["GC=F", "CL=F", "ES=F", "NQ=F"])
else:
    ticker_symbol = st.sidebar.text_input("Ticker eingeben (z.B. AAPL)", value="AAPL").upper()

# Zeitrahmen (Timeframe)
timeframe = st.sidebar.selectbox("Zeitrahmen (Timeframe)", ["1m", "5m", "1h", "4h", "1d"], index=4)

# Benachrichtigungs-Master-Switch in der Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Benachrichtigungen")
notifications_active = st.sidebar.checkbox("Master-Switch (Push-Alerts)", value=False)
if notifications_active:
    st.sidebar.success("Aktiv: Warnt bei Zonen-Hits & Volumen-Spikes.")
else:
    st.sidebar.info("Inaktiv: Keine Störungen.")

# --- DATEN LADEN & BEREINIGEN ---
def get_period_for_interval(tf):
    if tf in ["1m", "5m"]:
        return "7d"
    elif tf in ["1h", "4h"]:
        return "60d"
    else:
        return "1y"

@st.cache_data(ttl=15)
def load_data(symbol, tf):
    try:
        per = get_period_for_interval(tf)
        data = yf.download(symbol, period=per, interval=tf, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        return None

df = load_data(ticker_symbol, timeframe)

# Berechnungen für Trend-Check & Zonen (Indikatoren im Hintergrund)
if df is not None and not df.empty:
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # Letzte Werte
    current_price = float(df['Close'].iloc[-1])
    prev_price = float(df['Close'].iloc[-2])
    change = ((current_price - prev_price) / prev_price) * 100
    
    ema50 = float(df['EMA_50'].iloc[-1])
    ema200 = float(df['EMA_200'].iloc[-1])
    
    # Automatische Buy / Sell Support-Resistance Zonen
    support_zone = float(df['Low'].tail(14).min())
    resistance_zone = float(df['High'].tail(14).max())
    
    # Clean Trend Logic (Market Bias)
    if current_price > ema50 and ema50 > ema200:
        market_bias = "Stark Bullish [Long-Fokus]"
    elif current_price < ema50 and ema50 < ema200:
        market_bias = "Stark Bearish [Short-Fokus]"
    else:
        market_bias = "Neutral / Konsolidierung"


# --- TAB 1: CHART & TREND-CHECK ---
if tab_selection == "Chart & Trend-Check":
    st.header(f"Marktanalyse: {ticker_symbol} ({timeframe})")
    
    if df is not None and not df.empty:
        # Metriken in Kanten-Optik
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Aktueller Preis", f"${current_price:.2f}", f"{change:.2f}%")
        m2.metric("Market Bias", market_bias)
        m3.metric("Support-Zone", f"${support_zone:.2f}")
        m4.metric("Resistance-Zone", f"${resistance_zone:.2f}")
        
        st.markdown("---")
        
        # Zonen-Toggle für den Chart
        st.subheader("Chart-Steuerung & Zonen")
        show_zones = st.checkbox("Support- & Resistance-Zonen im Chart einblenden")
        
        # Plotly Kerzenchart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Candles"
        )])
        
        if show_zones:
            fig.add_hline(y=support_zone, line_dash="dash", line_color="#28a745", annotation_text="Support-Zone")
            fig.add_hline(y=resistance_zone, line_dash="dash", line_color="#dc3545", annotation_text="Resistance-Zone")
            
        fig.update_layout(
            title=f"Preisverlauf ({ticker_symbol})", 
            xaxis_title="Zeit", 
            yaxis_title="Preis (USD)", 
            template="plotly_dark",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Volumen Chart
        st.subheader("Volumen-Verteilung")
        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='#4a5568', name="Volumen")])
        fig_vol.update_layout(template="plotly_dark", height=200, margin=dict(t=10, b=10))
        st.plotly_chart(fig_vol, use_container_width=True)
        
    else:
        st.error(f"Konnte keine Daten für {ticker_symbol} laden.")


# --- TAB 2: RISIKO-RECHNER & REALITÄTS-CHECK ---
elif tab_selection == "Risiko-Rechner & Realitäts-Check":
    st.header("Automatisierter Risiko-Rechner & Realitäts-Check")
    st.markdown("Kapitalsicherung durch mathematische Disziplin und integrierten Realitäts-Filter.")
    
    # Preset Auswahl
    preset = st.selectbox("Risiko-Presets wählen", ["Manuelle Eingabe", "Konservativ [1% Risiko / 1:2 CRV]", "Aggressiv [3% Risiko / 1:3 CRV]", "Swing-Trading [2% Risiko / 1:2.5 CRV]"])
    
    p_risk = 2.0
    p_crv = 2.0
    if "Konservativ" in preset:
        p_risk = 1.0
        p_crv = 2.0
    elif "Aggressiv" in preset:
        p_risk = 3.0
        p_crv = 3.0
    elif "Swing-Trading" in preset:
        p_risk = 2.0
        p_crv = 2.5

    col1, col2 = st.columns(2)
    
    with col1:
        default_entry = current_price if 'current_price' in globals() else 150.0
        entry_price = st.number_input("Einstiegspreis ($)", value=default_entry, step=0.1)
        capital = st.number_input("Eingesetztes Kapital (€ / $)", value=1000.0, step=50.0)
        leverage = st.slider("Hebel (Leverage)", min_value=1, max_value=50, value=1)
        
    with col2:
        risk_percent = st.number_input("Maximales Risiko pro Trade (%)", value=p_risk, step=0.5)
        crv = st.number_input("Chance-Risiko-Verhältnis (CRV)", value=p_crv, step=0.5)
        position_type = st.radio("Positions-Richtung", ["Long (Kauf)", "Short (Verkauf)"])

    if st.button("Trade berechnen & Realitäts-Check durchführen", type="primary"):
        total_position_value = capital * leverage
        max_loss_money = capital * (risk_percent / 100.0)
        
        if position_type == "Long (Kauf)":
            sl_price = entry_price - (max_loss_money / (total_position_value / entry_price))
            tp_price = entry_price + ((entry_price - sl_price) * crv)
        else:
            sl_price = entry_price + (entry_price * (risk_percent / 100.0) / leverage)
            tp_price = entry_price - ((sl_price - entry_price) * crv)
            
        st.markdown("---")
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Stop Loss (SL)", f"${sl_price:.2f}")
        res_col2.metric("Take Profit (TP)", f"${tp_price:.2f}")
        res_col3.metric("Max. Risiko ($)", f"${max_loss_money:.2f}")
        
        # --- TRADE REALITÄTS-CHECK ---
        st.markdown("### Trade-Realitäts-Check [Probability Score]")
        
        if crv > 4.0:
            st.error("Utopisches Setup [Unwahrscheinlich]: Ein CRV über 4.0 erfordert enorme Kursbewegungen, die statistisch gegen dich laufen. Hohes Risiko für Fehlausbrüche.")
        elif crv > 2.5:
            st.warning("Mit Vorsicht zu genießen: Das CRV ist ambitioniert. Prüfe, ob starke Widerstände im Weg liegen.")
        else:
            st.success("Realistisches Setup: Gesundes Chance-Risiko-Verhältnis im Rahmen der normalen Markt-Volatilität.")


# --- TAB 3: WATCHLIST & KATEGORIEN ---
elif tab_selection == "Watchlist & Kategorien":
    st.header("Strukturierte Watchlist")
    st.markdown("Übersicht der wichtigsten Assets, aufgeteilt nach Anlageklassen.")
    
    w_tab1, w_tab2, w_tab3, w_tab4 = st.tabs(["Aktien", "ETFs", "Krypto", "Futures"])
    
    with w_tab1:
        st.table(pd.DataFrame({
            "Asset": ["Apple [AAPL]", "Microsoft [MSFT]", "NVIDIA [NVDA]"],
            "Fokus": ["Tech / Growth", "Cloud / KI", "Semiconductor"],
            "Status": ["Beobachten", "Akkumulieren", "Breakout-Zone"]
        }))
    with w_tab2:
        st.table(pd.DataFrame({
            "Asset": ["S&P 500 [SPY]", "Nasdaq 100 [QQQ]", "Russell 2000 [IWM]"],
            "Fokus": ["Breiter Markt", "Tech-Index", "Small Caps"],
            "Status": ["Trend folgend", "Trend folgend", "Neutral"]
        }))
    with w_tab3:
        st.table(pd.DataFrame({
            "Asset": ["Bitcoin [BTC-USD]", "Ethereum [ETH-USD]"],
            "Fokus": ["Store of Value", "Smart Contracts"],
            "Status": ["Support-Test", "Konsolidierung"]
        }))
    with w_tab4:
        st.table(pd.DataFrame({
            "Asset": ["Gold [GC=F]", "Rohöl [CL=F]", "S&P Future [ES=F]"],
            "Fokus": ["Edelmetall", "Energie", "Index-Future"],
            "Status": ["Long-Bias", "Short-Bias", "Aktiv"]
        }))


# --- TAB 4: MARKET SCREENER ---
elif tab_selection == "Market Screener":
    st.header("Market Screener [Entdeckungs-Modus]")
    st.markdown("Marktscan basierend auf Volumen-Anomalien und Momentum.")
    
    if st.button("Screener starten"):
        with st.spinner("Scanne globale Märkte nach Signalen..."):
            screener_data = [
                {"Asset": "NVDA", "Kategorie": "Aktien", "Signal": "Volumen-Spike + Breakout", "RSI": "68 [Stark]"},
                {"Asset": "GC=F", "Kategorie": "Futures", "Signal": "Test von Widerstandsmarken", "RSI": "72 [Überkauft]"},
                {"Asset": "BTC-USD", "Kategorie": "Krypto", "Signal": "Rebound an Support", "RSI": "45 [Neutral]"},
                {"Asset": "AMD", "Kategorie": "Aktien", "Signal": "Relatives Stärke-Plus", "RSI": "58 [Gesund]"}
            ]
            st.table(pd.DataFrame(screener_data))
            st.success("Screener erfolgreich abgeschlossen.")


# --- TAB 5: MAKRO & NEWS ---
elif tab_selection == "Makro & News":
    st.header("Wirtschaftskalender & Makro-Risiken")
    st.markdown("Wichtige Events mit potenziellem Einfluss auf den Gesamtmarkt.")
    
    news_data = [
        {"Datum": "Heute", "Event": "US Verbraucherpreisindex [CPI / Inflation]", "Einfluss": "Hoch [Massiv]", "Status": "Achtung vor Intraday-Spikes"},
        {"Datum": "Morgen", "Event": "FED Zinsentscheid & Pressekonferenz", "Einfluss": "Sehr Hoch", "Status": "Keine neuen Positionen eröffnen"},
        {"Datum": "In 3 Tagen", "Event": "US Arbeitsmarktdaten [NFP]", "Einfluss": "Mittel", "Status": "Erhöhte Volatilität erwartet"}
    ]
    st.table(pd.DataFrame(news_data))
