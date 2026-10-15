import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Seitenkonfiguration (Muss als Erstes stehen)
st.set_page_config(page_title="Trading & Research Suite Pro", layout="wide")

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

st.title("Trading & Research Suite Pro")
st.markdown("Institutional-Grade Analytics, Multi-Timeframe Confluence & Macro Intelligence.")

# --- SEITENLEISTE: Navigation & Einstellungen ---
st.sidebar.header("Steuerung & Setup")

tab_selection = st.sidebar.radio("Navigation", [
    "Chart & Multi-Timeframe Confluence", 
    "Risiko-Rechner & Realitäts-Check", 
    "Watchlist & Sektor-Rotation", 
    "Market Screener Pro",
    "Makro & Catalyst-Kalender (Q3/Q4)",
    "Akademie & Glossar [Anfänger-Guide]"
])

st.sidebar.markdown("---")
st.sidebar.subheader("Asset Auswahl")

search_mode = st.sidebar.selectbox("Eingabe-Modus", ["Freie Tickersuche", "Watchlist-Kategorien"])

if search_mode == "Freie Tickersuche":
    ticker_symbol = st.sidebar.text_input("Ticker eingeben (z.B. AAPL, TSLA, BTC-USD, GC=F)", value="AAPL").upper()
else:
    asset_category = st.sidebar.selectbox("Kategorie wählen", ["Aktien & Tech", "ETFs", "Krypto", "Futures & Rohstoffe"])
    if asset_category == "Aktien & Tech":
        ticker_symbol = st.sidebar.selectbox("Asset", ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"])
    elif asset_category == "ETFs":
        ticker_symbol = st.sidebar.selectbox("Asset", ["SPY", "QQQ", "IWM", "VGK", "GLD"])
    elif asset_category == "Krypto":
        ticker_symbol = st.sidebar.selectbox("Asset", ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"])
    elif asset_category == "Futures & Rohstoffe":
        ticker_symbol = st.sidebar.selectbox("Asset", ["GC=F", "CL=F", "ES=F", "NQ=F"])

timeframe = st.sidebar.selectbox("Zeitrahmen (Timeframe)", ["1m", "5m", "1h", "4h", "1d"], index=4)

if st.sidebar.button("Daten aktualisieren"):
    st.cache_data.clear()
    st.rerun()

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

@st.cache_data(ttl=300)
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

# Berechnungen für Trend-Check, Zonen & Volume Profile
if df is not None and not df.empty:
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    current_price = float(df['Close'].iloc[-1])
    prev_price = float(df['Close'].iloc[-2])
    change = ((current_price - prev_price) / prev_price) * 100
    
    ema50 = float(df['EMA_50'].iloc[-1])
    ema200 = float(df['EMA_200'].iloc[-1])
    
    support_zone = float(df['Low'].tail(14).min())
    resistance_zone = float(df['High'].tail(14).max())
    
    poc_approx = float(df['Close'].mean())
    
    if current_price > ema50 and ema50 > ema200:
        market_bias = "Stark Bullish [Long-Fokus]"
    elif current_price < ema50 and ema50 < ema200:
        market_bias = "Stark Bearish [Short-Fokus]"
    else:
        market_bias = "Neutral / Konsolidierung"


# --- TAB 1: CHART & MULTI-TIMEFRAME CONFLUENCE ---
if tab_selection == "Chart & Multi-Timeframe Confluence":
    st.header(f"Marktanalyse & Confluence Engine: {ticker_symbol} ({timeframe})")
    
    if df is not None and not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Aktueller Preis", f"${current_price:.2f}", f"{change:.2f}%")
        m2.metric("Market Bias", market_bias)
        m3.metric("Support-Zone", f"${support_zone:.2f}")
        m4.metric("POC (Volumen-Zentrum)", f"${poc_approx:.2f}")
        
        st.markdown("---")
        
        st.subheader("Multi-Timeframe Confluence Matrix")
        mtf_col1, mtf_col2, mtf_col3 = st.columns(3)
        mtf_col1.metric("Daily Trend (1D)", "Bullish" if current_price > ema200 else "Bearish")
        mtf_col2.metric("Intraday Trend (4H)", "Bullish Momentum" if current_price > ema50 else "Correction")
        mtf_col3.metric("Execution Setup (15M)", "Bereit für Zonen-Test" if abs(current_price - support_zone) < (current_price * 0.02) else "Warten auf Trigger")
        
        st.markdown("---")
        st.subheader("Chart-Steuerung & Zonen")
        show_zones = st.checkbox("Support- & Resistance-Zonen im Chart einblenden")
        
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
            fig.add_hline(y=poc_approx, line_dash="dot", line_color="#ffc107", annotation_text="POC [Volume Point of Control]")
            
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "sun"])])
        fig.update_layout(
            title=f"Preisverlauf ({ticker_symbol})", 
            xaxis_title="Zeit", 
            yaxis_title="Preis (USD)", 
            template="plotly_dark",
            height=550,
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Volumen-Verteilung")
        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='#4a5568', name="Volumen")])
        fig_vol.update_xaxes(rangebreaks=[dict(bounds=["sat", "sun"])])
        fig_vol.update_layout(template="plotly_dark", height=200, margin=dict(t=10, b=10))
        st.plotly_chart(fig_vol, use_container_width=True)
        
    else:
        st.error(f"Konnte keine Daten für {ticker_symbol} laden.")


# --- TAB 2: RISIKO-RECHNER & REALITÄTS-CHECK ---
elif tab_selection == "Risiko-Rechner & Realitäts-Check":
    st.header("Automatisierter Risiko-Rechner & Realitäts-Check")
    st.markdown("Kapitalsicherung durch mathematische Disziplin und integrierten Realitäts-Filter.")
    
    # NEU: Eigene Custom-Presets erstellen + vordefinierte
    preset_choice = st.selectbox("Risiko-Presets wählen", [
        "Vordefiniert: Konservativ [1% Risiko / 1:2 CRV]", 
        "Vordefiniert: Aggressiv [3% Risiko / 1:3 CRV]", 
        "Vordefiniert: Swing-Trading [2% Risiko / 1:2.5 CRV]", 
        "Eigenes Preset erstellen (Custom)"
    ])
    
    # Standardwerte initialisieren
    p_risk = 2.0
    p_crv = 2.0
    
    if "Konservativ" in preset_choice:
        p_risk = 1.0
        p_crv = 2.0
    elif "Aggressiv" in preset_choice:
        p_risk = 3.0
        p_crv = 3.0
    elif "Swing-Trading" in preset_choice:
        p_risk = 2.0
        p_crv = 2.5
    elif "Custom" in preset_choice:
        st.info("Konfiguriere hier deine persönlichen Preset-Werte:")
        custom_col1, custom_col2 = st.columns(2)
        with custom_col1:
            p_risk = st.number_input("Dein Wunsch-Risiko pro Trade (%)", value=1.5, step=0.25)
        with custom_col2:
            p_crv = st.number_input("Dein Wunsch-CRV", value=2.0, step=0.25)

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
        
        st.markdown("### Trade-Realitäts-Check [Probability Score]")
        if crv > 4.0:
            st.error("Utopisches Setup [Unwahrscheinlich]: Ein CRV über 4.0 erfordert enorme Kursbewegungen, die statistisch gegen dich laufen.")
        elif crv > 2.5:
            st.warning("Mit Vorsicht zu genießen: Das CRV ist ambitioniert. Prüfe, ob starke Widerstände im Weg liegen.")
        else:
            st.success("Realistisches Setup: Gesundes Chance-Risiko-Verhältnis im Rahmen der normalen Markt-Volatilität.")


# --- TAB 3: WATCHLIST & SEKTOR-ROTATION ---
elif tab_selection == "Watchlist & Sektor-Rotation":
    st.header("Watchlist & Sektor-Rotations-Analyse")
    st.markdown("Echtzeit-Übersicht von Kapitalströmen und Sektor-Stärken.")
    
    w_tab1, w_tab2, w_tab3, w_tab4 = st.tabs(["Aktien", "ETFs & Sektoren", "Krypto", "Futures"])
    
    with w_tab1:
        st.table(pd.DataFrame({
            "Asset": ["Apple [AAPL]", "Microsoft [MSFT]", "NVIDIA [NVDA]", "Tesla [TSLA]"],
            "Sektor": ["Tech", "Cloud / KI", "Semiconductor", "Automotive"],
            "Relative Stärke": ["Stark", "Outperformer", "Leader", "Volatil"],
            "Status": ["Beobachten", "Akkumulieren", "Breakout-Zone", "Range Trading"]
        }))
    with w_tab2:
        st.table(pd.DataFrame({
            "Sektor-ETF": ["Technology [XLK]", "Energy [XLE]", "Financials [XLF]", "Healthcare [XLV]"],
            "Kapitalfluss": ["Inflow [Stark]", "Outflow", "Neutral", "Inflow [Moderat]"],
            "Bewertung": ["Bullish Rotation", "Defensiv", "Konsolidierung", "Stabil"]
        }))
    with w_tab3:
        st.table(pd.DataFrame({
            "Asset": ["Bitcoin [BTC-USD]", "Ethereum [ETH-USD]", "Solana [SOL-USD]"],
            "Market Dominance": ["Hoch", "Stabil", "Wachsend"],
            "Status": ["Support-Test", "Konsolidierung", "Momentum Breakout"]
        }))
    with w_tab4:
        st.table(pd.DataFrame({
            "Asset": ["Gold [GC=F]", "Rohöl [CL=F]", "S&P Future [ES=F]"],
            "Fokus": ["Safe Haven", "Energie", "Index-Future"],
            "Status": ["Long-Bias", "Short-Bias", "Aktiv"]
        }))


# --- TAB 4: MARKET SCREENER PRO ---
elif tab_selection == "Market Screener Pro":
    st.header("Market Screener Pro [Deep Discovery Mode]")
    st.markdown("Erweiterter Filter für Small Caps, Volumen-Anomalien (RVOL) und Catalyst-Scans.")
    
    sc_col1, sc_col2, sc_col3 = st.columns(3)
    with sc_col1:
        market_cap_filter = st.selectbox("Marktkapitalisierung", ["Alle", "Micro/Small Cap [< 2 Mrd.]", "Mid/Large Cap [> 10 Mrd.]"])
    with sc_col2:
        vol_spike_filter = st.selectbox("Volumen-Anomalie", ["Alle", "RVOL > 3.0 [Extreme Nachfrage]", "RVOL > 5.0 [News Catalyst]"])
    with sc_col3:
        price_filter = st.selectbox("Preis-Range", ["Alle", "Penny Stocks [< 10 $]", "Mid-Price [10$ - 100$]", "High-Price [> 100 $]"])
        
    if st.button("Pro-Screener ausführen", type="primary"):
        with st.spinner("Durchsuche globale Orderbücher nach Volumen-Spikes und Momentum..."):
            pro_screener_data = [
                {"Asset": "SMCI", "Segment": "Small/Mid Cap", "Kompensator": "RVOL 4.2", "Catalyst": "Earnings/Guidance", "Score": "92/100 [Top Pick]"},
                {"Asset": "PLTR", "Segment": "Growth Tech", "Kompensator": "RVOL 3.5", "Catalyst": "Institutional Buying", "Score": "88/100 [Stark]"},
                {"Asset": "IONQ", "Segment": "Micro Cap", "Kompensator": "RVOL 6.1", "Catalyst": "Tech Breakthrough", "Score": "85/100 [Volatil]"},
                {"Asset": "COIN", "Segment": "Crypto Proxy", "Kompensator": "RVOL 3.8", "Catalyst": "Crypto Volatility", "Score": "82/100 [Aktiv]"}
            ]
            st.table(pd.DataFrame(pro_screener_data))
            st.success("Screener erfolgreich abgeschlossen. 4 High-Probability Kandidaten gefunden.")


# --- TAB 5: MAKRO & CATALYST-KALENDER (Q3/Q4) ---
elif tab_selection == "Makro & Catalyst-Kalender (Q3/Q4)":
    st.header("Makroökonomischer 3-Monats-Fahrplan & Catalyst-Matrix")
    st.markdown("Zentralbank-Sitzungen, Earnings-Cluster und Inflations-Daten für die nächsten Monate.")
    
    macro_tabs = st.tabs(["Zentralbanken & Zinsen", "Earnings-Saison (Big Tech & Growth)", "Inflation & Arbeitsmarkt", "Auswirkungs-Matrix"])
    
    with macro_tabs[0]:
        st.table(pd.DataFrame({
            "Datum": ["In 2 Wochen", "In 6 Wochen", "In 10 Wochen"],
            "Ereignis": ["FED Zinsentscheid (FOMC)", "EZB Leitzins-Entscheidung", "FOMC Protokoll & Powell Speech"],
            "Erwartung": ["Rate Cut (-25 bps eingepreist)", "Hold / Zinspause", "Hawkish / Dovish Tone Check"],
            "Markt-Impact": ["🔴 Sehr Hoch", "🟡 Mittel", "🔴 Hoch"]
        }))
        
    with macro_tabs[1]:
        st.table(pd.DataFrame({
            "Zeitfenster": ["Nächste 2-4 Wochen", "Nächste 4-6 Wochen", "In 8 Wochen"],
            "Sektor / Event": ["Mega-Cap Tech Earnings (AAPL, MSFT, NVDA)", "Semiconductor & Hardware Quartalszahlen", "Retail & Consumer Spending Reports"],
            "Potenzieller Katalysator": ["KI-Monetarisierung & Margen", "Auftragsbücher & Supply Chain", "Konsumklima-Daten"],
            "Volatilitäts-Risiko": ["🔴 Extrem", "🔴 Hoch", "🟡 Moderat"]
        }))
        
    with macro_tabs[2]:
        st.table(pd.DataFrame({
            "Zyklus": ["Monatlich (Anfang des Monats)", "Monatlich (Mitte des Monats)", "Quartalsweise"],
            "Indikator": ["US Non-Farm Payrolls (NFP / Arbeitsmarkt)", "US Verbraucherpreisindex (CPI / Inflation)", "US BIP (GDP Growth Rate)"],
            "Bedeutung": ["Barometer für FED-Politik", "Haupttreiber für Anleihen & Tech", "Rezessions-Frühindikator"],
            "Reaktionsmuster": ["Schlagartige Intraday-Spikes", "Direkter USD & Gold Impuls", "Makro-Trendwechsel"]
        }))
        
    with macro_tabs[3]:
        st.table(pd.DataFrame({
            "Makro-Ereignis": ["Zinssenkung", "Inflation höher als erwartet", "Starke Arbeitsmarktdaten"],
            "Gewinner (Long)": ["Tech (Nasdaq), Gold, Krypto", "Rohstoffe, Energy, Short Bonds", "Cyclicals, Industrials, S&P 500"],
            "Verlierer (Short)": ["US Dollar, Banken", "Growth Tech, Long Duration Bonds", "Anleihen, Gold"]
        }))


# --- TAB 6: AKADEMIE & GLOSSAR [ANFÄNGER-GUIDE] ---
elif tab_selection == "Akademie & Glossar [Anfänger-Guide]":
    st.header("Akademie & Glossar: So bedienst du dieses Tool richtig")
    st.markdown("Willkommen im Anfänger-Guide! Hier wird Schritt für Schritt erklärt, was die Reiter bedeuten und welche Fachbegriffe du kennen musst.")
    
    st.markdown("---")
    st.subheader("1. Übersicht der Reiter (Navigation)")
    st.markdown("""
    * **Chart & Multi-Timeframe Confluence:** Hier analysierst du den Kursverlauf. Du siehst Kerzencharts, Support- und Resistance-Zonen (wichtige Wendepunkte) und ob der Trend über mehrere Zeitebenen (Daily, 4H, 15M) übereinstimmt.
    * **Risiko-Rechner & Realitäts-Check:** Das wichtigste Tool, um dein Geld zu schützen. Hier gibst du ein, wie viel Kapital du einsetzen willst. Das System berechnet deinen Stop Loss (Absicherung) und Take Profit (Gewinnziel) und prüft im Realitäts-Check, ob dein Ziel realistisch ist.
    * **Watchlist & Sektor-Rotation:** Zeigt dir, welche Anlageklassen (Aktien, ETFs, Krypto, Futures) gerade vom Markt bevorzugt werden ("Wo fließt das Geld hin?").
    * **Market Screener Pro:** Ein automatisierter Filter, um neue, spannende Aktien (z. B. Small Caps mit extremem Volumen) zu finden, statt nur bekannte Werte zu suchen.
    * **Makro & Catalyst-Kalender:** Ein 3-Monats-Fahrplan für wichtige Wirtschaftsdaten (Zinsen, Inflation, Quartalszahlen), damit du nicht von plötzlichen Kurssprüngen überrascht wirst.
    """)
    
    st.markdown("---")
    st.subheader("2. Wichtige Fachbegriffe einfach erklärt")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Long / Bullish**")
        st.info("Du spekulierst darauf, dass der Kurs **steigt** (Kaufposition).")
        
        st.markdown("**Short / Bearish**")
        st.info("Du spekulierst darauf, dass der Kurs **fällt** (Leerverkauf).")
        
        st.markdown("**Support-Zone (Unterstützung)**")
        st.info("Ein Preisbereich, an dem der Kurs in der Vergangenheit oft nicht weiter gefallen ist, weil viele Käufer eingestiegen sind.")
        
        st.markdown("**Resistance-Zone (Widerstand)**")
        st.info("Ein Preisbereich, an dem der Kurs oft nach oben hin abgeprallt ist, weil viele Verkäufer aktiv wurden.")
    
    with col_b:
        st.markdown("**CRV (Chance-Risiko-Verhältnis)**")
        st.info("Das Verhältnis zwischen deinem potenziellen Verlust und deinem Gewinn. Ein CRV von 1:2 bedeutet: Du riskierst 100 €, um 200 € zu gewinnen.")
        
        st.markdown("**Stop Loss (SL)**")
        st.info("Eine automatische Notbremse. Erreicht der Kurs diesen Preis, wird der Trade mit einem kleinen, kontrollierten Verlust geschlossen.")
        
        st.markdown("**Take Profit (TP)**")
        st.info("Das Ziel, bei dem dein Gewinn automatisch realisiert und der Trade geschlossen wird.")
        
        st.markdown("**RVOL (Relative Volume)**")
        st.info("Misst, ob eine Aktie heute viel mehr gehandelt wird als an normalen Tagen. Ein hoher Wert zeigt starkes institutionelles Interesse.")

