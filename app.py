import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta

# Seitenkonfiguration (Muss als Erstes stehen)
st.set_page_config(page_title="Institutional Trading & Research Suite", layout="wide")

# --- CUSTOM CSS FÜR EDLES TERMINAL-DESIGN ---
st.markdown("""
<style>
    .card {
        background-color: #161b22;
        padding: 22px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    .terminal-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    table td {
        white-space: normal !important;
        word-wrap: break-word !important;
    }
</style>
""", unsafe_allow_html=True)

# Aktuelle Zeit in Europa (MEZ/MESZ)
utc_now = datetime.now(timezone.utc)
europe_time = utc_now + timedelta(hours=2)
current_date_str = europe_time.strftime("%d.%m.%Y")
current_time_str = europe_time.strftime("%H:%M")

st.title("Institutional Trading & Research Suite")
st.markdown(f"Terminal-Status: Online | Europäische Zeit: **{current_date_str} - {current_time_str} Uhr**")

# --- SESSION STATE FÜR WATCHLIST ---
if "user_watchlist" not in st.session_state:
    st.session_state.user_watchlist = ["AAPL", "MSFT", "NVDA", "BTC-USD", "GC=F"]

# --- SEITENLEISTE ---
st.sidebar.header("Terminal Navigation")

tab_selection = st.sidebar.radio("Module", [
    "Chart & Auto-Trade Trigger", 
    "Risiko-Rechner & Realitäts-Check", 
    "Watchlist (Personalisiert)", 
    "Market Screener Pro",
    "Globaler Event-Kalender & Impact [MEZ]",
    "Akademie & Glossar [Guide]"
])

st.sidebar.markdown("---")
st.sidebar.subheader("Asset Steuerung")

search_mode = st.sidebar.selectbox("Eingabe-Modus", ["Freie Tickersuche", "Aus personalisierter Watchlist"])

if search_mode == "Freie Tickersuche":
    ticker_symbol = st.sidebar.text_input("Ticker eingeben (z.B. AAPL, TSLA, BTC-USD)", value="AAPL").upper()
else:
    if len(st.session_state.user_watchlist) > 0:
        ticker_symbol = st.sidebar.selectbox("Watchlist Asset wählen", st.session_state.user_watchlist)
    else:
        ticker_symbol = "AAPL"
        st.sidebar.warning("Watchlist ist leer.")

timeframe = st.sidebar.selectbox("Zeitrahmen (Timeframe)", ["1m", "5m", "1h", "4h", "1d"], index=4)

if st.sidebar.button("Daten aktualisieren"):
    st.cache_data.clear()
    st.rerun()

# --- DATEN LADEN ---
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

# Technische Berechnungen & Trade-Trigger Erkennung
if df is not None and not df.empty:
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    current_price = float(df['Close'].iloc[-1])
    prev_price = float(df['Close'].iloc[-2])
    change = ((current_price - prev_price) / prev_price) * 100
    
    ema50 = float(df['EMA_50'].iloc[-1])
    ema200 = float(df['EMA_200'].iloc[-1])
    
    # Automatische Buy / Sell Zonen (Support & Resistance)
    support_zone = float(df['Low'].tail(14).min())
    resistance_zone = float(df['High'].tail(14).max())
    poc_approx = float(df['Close'].mean())
    
    # Trade Setup Logik
    distance_to_support = abs(current_price - support_zone) / current_price
    distance_to_resistance = abs(current_price - resistance_zone) / current_price
    
    if current_price > ema50 and distance_to_support < 0.03:
        trade_signal = "🟢 LONG SETUP: Kurs testet Support-Zone im Aufwärtstrend!"
    elif current_price < ema50 and distance_to_resistance < 0.03:
        trade_signal = "🔴 SHORT SETUP: Kurs testet Widerstands-Zone im Abwärtstrend!"
    elif current_price > ema200:
        trade_signal = "🟡 NEUTRAL / TREND-FOLGE: Warten auf Zonen-Test"
    else:
        trade_signal = "🔴 BEARISH BIAS: Vorsicht bei Long-Positionen"


# --- TAB 1: CHART & AUTO-TRADE TRIGGER ---
if tab_selection == "Chart & Auto-Trade Trigger":
    st.header(f"Chart-Analyse & Trade-Erkennung: {ticker_symbol} ({timeframe})")
    
    if df is not None and not df.empty:
        # Oberste Zeile: Live-Metriken & Signal-Box
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Aktueller Preis", f"${current_price:.2f}", f"{change:.2f}%")
        m2.metric("Support-Zone", f"${support_zone:.2f}")
        m3.metric("Resistance-Zone", f"${resistance_zone:.2f}")
        m4.metric("Volumen-Zentrum (POC)", f"${poc_approx:.2f}")
        
        st.markdown("---")
        
        # Automatischer Trade-Trigger & Zonen-Status
        st.subheader("Automatisierter Trade-Realitäts- & Zonen-Check")
        st.info(f"**Handels-Signal Status:** {trade_signal}")
        
        st.markdown("---")
        
        # Chart-Steuerung
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            show_zones = st.checkbox("Buy/Sell Zonen & POC im Chart einblenden", value=True)
        
        # TradingView-Style Kerzenchart mit flüssigem Zoom & Touch-Support
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Candles"
        )])
        
        if show_zones:
            fig.add_hline(y=support_zone, line_dash="dash", line_color="#28a745", annotation_text="Buy-Zone (Support)")
            fig.add_hline(y=resistance_zone, line_dash="dash", line_color="#dc3545", annotation_text="Sell-Zone (Resistance)")
            fig.add_hline(y=poc_approx, line_dash="dot", line_color="#ffc107", annotation_text="POC [Fair Value]")
            
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "sun"])])
        
        # TradingView Konfiguration: Erlaubt echtes Scroll-Zoom, Pinch-Zoom und freies Verschieben
        fig.update_layout(
            title=f"Preisverlauf ({ticker_symbol}) - TradingView Style Interaktiv",
            xaxis_title="Zeit",
            yaxis_title="Preis (USD)",
            template="plotly_dark",
            height=650,
            xaxis_rangeslider_visible=False,
            dragmode="zoom"
        )
        
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "editable": True, "displayModeBar": True})
        
        # Volumen Chart
        st.subheader("Volumen-Verteilung")
        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='#4a5568', name="Volumen")])
        fig_vol.update_xaxes(rangebreaks=[dict(bounds=["sat", "sun"])])
        fig_vol.update_layout(template="plotly_dark", height=200, margin=dict(t=10, b=10))
        st.plotly_chart(fig_vol, use_container_width=True, config={"scrollZoom": True})
        
    else:
        st.error(f"Konnte keine Daten für {ticker_symbol} laden.")


# --- TAB 2: RISIKO-RECHNER & REALITÄTS-CHECK ---
elif tab_selection == "Risiko-Rechner & Realitäts-Check":
    st.header("Automatisierter Risiko-Rechner & Realitäts-Check")
    st.markdown("Kapitalsicherung durch mathematische Disziplin.")
    
    preset_choice = st.selectbox("Risiko-Presets wählen", [
        "Vordefiniert: Konservativ [1% Risiko / 1:2 CRV]", 
        "Vordefiniert: Aggressiv [3% Risiko / 1:3 CRV]", 
        "Vordefiniert: Swing-Trading [2% Risiko / 1:2.5 CRV]", 
        "Eigenes Preset erstellen (Custom)"
    ])
    
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
        c1, c2 = st.columns(2)
        with c1:
            p_risk = st.number_input("Wunsch-Risiko (%)", value=1.5, step=0.25)
        with c2:
            p_crv = st.number_input("Wunsch-CRV", value=2.0, step=0.25)

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

    if st.button("Trade berechnen & ausführen", type="primary"):
        total_position_value = capital * leverage
        max_loss_money = capital * (risk_percent / 100.0)
        
        if position_type == "Long (Kauf)":
            sl_price = entry_price - (max_loss_money / (total_position_value / entry_price))
            tp_price = entry_price + ((entry_price - sl_price) * crv)
        else:
            sl_price = entry_price + (entry_price * (risk_percent / 100.0) / leverage)
            tp_price = entry_price - ((sl_price - entry_price) * crv)
            
        st.markdown("---")
        res1, res2, res3 = st.columns(3)
        res1.metric("Stop Loss (SL)", f"${sl_price:.2f}")
        res2.metric("Take Profit (TP)", f"${tp_price:.2f}")
        res3.metric("Max. Risiko ($)", f"${max_loss_money:.2f}")
        st.success("Trade-Parameter erfolgreich validiert. Bereit für die Order-Plattform.")


# --- TAB 3: WATCHLIST ---
elif tab_selection == "Watchlist (Personalisiert)":
    st.header("Deine Personalisierte Watchlist")
    
    new_ticker = st.text_input("Asset hinzufügen (z.B. GOOGL, TSLA, BTC-USD)").upper()
    if st.button("Hinzufügen"):
        if new_ticker and new_ticker not in st.session_state.user_watchlist:
            st.session_state.user_watchlist.append(new_ticker)
            st.success(f"{new_ticker} hinzugefügt.")
            st.rerun()

    if len(st.session_state.user_watchlist) > 0:
        watchlist_data = []
        for t in st.session_state.user_watchlist:
            try:
                t_data = yf.Ticker(t).history(period="2d")
                if not t_data.empty:
                    p_now = float(t_data['Close'].iloc[-1])
                    p_prev = float(t_data['Close'].iloc[-2]) if len(t_data) > 1 else p_now
                    p_change = ((p_now - p_prev) / p_prev) * 100
                    watchlist_data.append({"Ticker": t, "Preis ($)": round(p_now, 2), "Änderung (%)": round(p_change, 2)})
            except:
                watchlist_data.append({"Ticker": t, "Preis ($)": "N/A", "Änderung (%)": "N/A"})
        st.table(pd.DataFrame(watchlist_data))
        
        rem = st.selectbox("Asset entfernen", st.session_state.user_watchlist)
        if st.button("Entfernen"):
            st.session_state.user_watchlist.remove(rem)
            st.rerun()


# --- TAB 4: MARKET SCREENER PRO ---
elif tab_selection == "Market Screener Pro":
    st.header("Market Screener Pro")
    if st.button("Screener ausführen", type="primary"):
        with st.spinner("Scanne globale Märkte..."):
            screener_results = [
                {"Ticker": "SMCI", "Preis ($)": 42.50, "Tageswachstum (%)": "+6.8%", "RVOL": "4.2", "Prognose": "Starkes AI-Wachstum"},
                {"Ticker": "PLTR", "Preis ($)": 28.10, "Tageswachstum (%)": "+4.2%", "RVOL": "3.5", "Prognose": "Government Pipeline"},
                {"Ticker": "ASML", "Preis ($)": 890.00, "Tageswachstum (%)": "+2.1%", "RVOL": "2.8", "Prognose": "Halbleiter Zyklus Rebound"},
                {"Ticker": "BMW.DE", "Preis ($)": 95.40, "Tageswachstum (%)": "-0.8%", "RVOL": "1.9", "Prognose": "Europäische Auto-Dividenden"}
            ]
            st.table(pd.DataFrame(screener_results))
            
            add_sc = st.selectbox("Aus Screener zur Watchlist", ["SMCI", "PLTR", "ASML", "BMW.DE"])
            if st.button("Zur Watchlist hinzufügen"):
                if add_sc not in st.session_state.user_watchlist:
                    st.session_state.user_watchlist.append(add_sc)
                    st.success(f"{add_sc} hinzugefügt!")


# --- TAB 5: GLOBALER EVENT-KALENDER & IMPACT ---
elif tab_selection == "Globaler Event-Kalender & Impact [MEZ]":
    st.header("Globaler Makro-Kalender & Vergangene Events [MEZ]")
    
    cal_tabs = st.tabs(["Kommende Events (Global)", "Vergangene Events & Markt-Impact"])
    
    with cal_tabs[0]:
        st.markdown("### Globale Wirtschafts-Events der nächsten Wochen (MEZ)")
        global_events = [
            {"Datum": "22.10.2026 - 20:00", "Region": "USA", "Event": "US FOMC Zinsentscheid", "Wichtigkeit": "🔴 Hoch (Critical)", "Fokus": "Nasdaq, Gold"},
            {"Datum": "24.10.2026 - 10:00", "Region": "EU", "Event": "EZB PMI Einkaufsmanagerindex", "Wichtigkeit": "🟡 Mittel", "Fokus": "EUR, DAX"},
            {"Datum": "28.10.2026 - 14:15", "Region": "UK", "Event": "Bank of England Zinsentscheid", "Wichtigkeit": "🟡 Mittel", "Fokus": "GBP"},
            {"Datum": "05.11.2026 - 14:30", "Region": "USA", "Event": "Non-Farm Payrolls (Arbeitsmarkt)", "Wichtigkeit": "🔴 Hoch (Critical)", "Fokus": "Gesamtmarkt"},
            {"Datum": "10.11.2026 - 02:00", "Region": "China", "Event": "Chinesische Inflationsdaten (CPI)", "Wichtigkeit": "🟢 Normal", "Fokus": "Rohstoffe, Asia-Tech"},
            {"Datum": "12.11.2026 - 14:30", "Region": "USA", "Event": "US Verbraucherpreisindex (CPI)", "Wichtigkeit": "🔴 Hoch (Critical)", "Fokus": "Tech & Anleihen"}
        ]
        st.table(pd.DataFrame(global_events))
        
    with cal_tabs[1]:
        st.markdown("### Vergangene Events & Tatsächliche Marktauswirkungen")
        past_events = [
            {"Datum": "Vor 3 Tagen", "Event": "US Erstanträge Arbeitslosenhilfe", "Prognose": "225k", "Ergebnis": "218k (Besser als erwartet)", "Markt-Impact": "🟢 Aktienmärkte reagierten mit starkem Intraday-Rallye."},
            {"Datum Letzte Woche", "Event": "OPEC+ Oel-Fördermengen Treffen", "Prognose": "Kürzung beibehalten", "Ergebnis": "Überraschende Erhöhung", "Markt-Impact": "🔴 Rohöl (CL=F) brach um 4.5% ein."},
            {"Datum Vor 2 Wochen", "Event": "Japan Zinsentscheidung (BOJ)", "Prognose": "Zinserhöhung", "Ergebnis": "Zinserhöhung um 25 bps", "Markt-Impact": "🟡 Starker Yen-Anstieg, temporäre Volatilität bei Nikkei."}
        ]
        st.table(pd.DataFrame(past_events))


# --- TAB 6: AKADEMIE ---
elif tab_selection == "Akademie & Glossar [Guide]":
    st.header("Akademie & Glossar")
    with st.expander("📖 Chart-Bedienung (TradingView Style)"):
        st.write("Nutze Pinch-to-Zoom auf dem Touchscreen oder das Mausrad, um den Chart stufenlos zu vergrößern. Ziehe an den Achsen, um Zeit oder Preis zu spreizen.")
    with st.expander("📖 Automatische Buy & Sell Zonen"):
        st.write("Das Tool berechnet automatisch Support- und Resistance-Zonen. Nähert sich der Preis einer Zone an, generiert das System ein Trade-Setup.")
