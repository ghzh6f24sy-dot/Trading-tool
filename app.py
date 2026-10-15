import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Seitenkonfiguration
st.set_page_config(page_title="Trading & Orderflow Analyse Tool", layout="wide")

st.title("🚀 Trading & Markt-Analyse Prototyp")
st.markdown("Dein externes Assistenz-Tool für Aktien, ETFs und Futures (inkl. Risiko-Rechner & Orderflow-Ansatz).")

# --- SEITENLEISTE: Navigation & Einstellungen ---
st.sidebar.header("⚙️ Steuerung")
tab_selection = st.sidebar.radio("Navigation", ["📊 Chart & Analyse", "📐 Risiko-Rechner (SL/TP)", "🌊 Orderflow & Volumen", "🌍 Makro & News Kalender"])

# Globale Eingabe für Ticker
ticker_symbol = st.sidebar.text_input("Asset Suchen (z.B. AAPL, SPY, QQQ, GC=F)", value="AAPL").upper()

# Daten laden & MultiIndex bereinigen
@st.cache_data(ttl=300)
def load_data(symbol):
    try:
        data = yf.download(symbol, period="1mo", interval="1d", auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        return None

df = load_data(ticker_symbol)

# --- TAB 1: CHART & ANALYZE ---
if tab_selection == "📊 Chart & Analyse":
    st.header(f"Marktanalyse für: {ticker_symbol}")
    
    if df is not None and not df.empty:
        # Aktueller Preis sicher auslesen
        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        change = ((current_price - prev_price) / prev_price) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Aktueller Preis", f"${current_price:.2f}", f"{change:.2f}%")
        col2.metric("5T-Hoch", f"${float(df['High'].tail(5).max()):.2f}")
        col3.metric("5T-Tief", f"${float(df['Low'].tail(5).min()):.2f}")
        
        # Plotly Kerzenchart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Candles"
        )])
        fig.update_layout(title=f"Tageschart ({ticker_symbol})", xaxis_title="Datum", yaxis_title="Preis (USD)", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Konnte keine Daten für dieses Symbol finden. Bitte überprüfe das Kürzel (z.B. 'AAPL' für Apple, 'ES=F' für S&P 500 Futures).")

# --- TAB 2: RISIKO-RECHNER ---
elif tab_selection == "📐 Risiko-Rechner (SL/TP)":
    st.header("📐 Automatisierter Trading- & Risiko-Rechner")
    st.markdown("Berechne basierend auf Hebel, Kapital und Einstiegspreis deine perfekten Exit-Marken.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entry_price = st.number_input("Einstiegspreis ($)", value=150.0, step=0.1)
        capital = st.number_input("Eingesetztes Kapital (€ / $)", value=1000.0, step=50.0)
        leverage = st.slider("Hebel (Leverage)", min_value=1, max_value=50, value=1)
        
    with col2:
        risk_percent = st.number_input("Maximales Risiko pro Trade (%)", value=2.0, step=0.5)
        crv = st.selectbox("Chance-Risiko-Verhältnis (CRV)", [1.5, 2.0, 2.5, 3.0], index=1)
        position_type = st.radio("Positions-Richtung", ["Long (Kauf)", "Short (Verkauf)"])

    if st.button("Berechne SL & TP"):
        total_position_value = capital * leverage
        max_loss_money = capital * (risk_percent / 100.0)
        
        if position_type == "Long (Kauf)":
            sl_price = entry_price - (max_loss_money / (total_position_value / entry_price))
            tp_price = entry_price + ((entry_price - sl_price) * crv)
        else:
            sl_price = entry_price + (entry_price * (risk_percent / 100.0) / leverage)
            tp_price = entry_price - ((sl_price - entry_price) * crv)
            
        st.success("Errechnete Trade-Parameter:")
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Stop Loss (SL)", f"${sl_price:.2f}")
        res_col2.metric("Take Profit (TP)", f"${tp_price:.2f}")
        res_col3.metric("Max. Risiko ($)", f"${max_loss_money:.2f}")

# --- TAB 3: ORDERFLOW & VOLUMEN ---
elif tab_selection == "🌊 Orderflow & Volumen":
    st.header("🌊 Orderflow & Volumen-Analyse (Prototyp)")
    st.markdown("Hier simulieren wir Einblicke in das Volumen, um institutionelle Akkumulationszonen zu erkennen.")
    
    if df is not None and not df.empty:
        st.subheader("Volumenverteilung nach Tagen")
        fig_vol = go.Figure(data=[go.Bar(x=df.index, y=df['Volume'], marker_color='indianred', name="Volumen")])
        fig_vol.update_layout(title="Handelsvolumen pro Kerze", template="plotly_dark")
        st.plotly_chart(fig_vol, use_container_width=True)
        
        st.info("💡 **Nächster Schritt für den Orderflow:** Wir können hier in Zukunft echte Intraday-Tick-Daten oder Order-Book-Imbalances (Bid/Ask-Druck) anbinden, sobald das Tool wächst!")
    else:
        st.warning("Bitte wähle zuerst ein gültiges Asset im Suchfeld aus.")

# --- TAB 4: MAKRO & NEWS KALENDER ---
elif tab_selection == "🌍 Makro & News Kalender":
    st.header("🌍 Wirtschaftskalender & Makro-Risiken")
    st.markdown("Wichtige Events, die massive Einflüsse auf den Gesamtmarkt (z.B. Zinsen, Inflation) haben.")
    
    news_data = [
        {"Datum": "Beispielhaft", "Event": "US Verbraucherpreisindex (CPI / Inflation)", "Einfluss": "🔴 Hoch (Massiv)", "Status": "Achtung vor Intraday-Spikes"},
        {"Datum": "Beispielhaft", "Event": "FED Zinsentscheid & Pressekonferenz", "Einfluss": "🔴 Sehr Hoch", "Status": "Keine neuen Positionen eröffnen"},
        {"Datum": "Beispielhaft", "Event": "US Arbeitsmarktdaten (NFP)", "Einfluss": "🟡 Mittel", "Status": "Erhöhte Volatilität erwartet"}
    ]
    
    st.table(pd.DataFrame(news_data))
    st.warning("⚠️ **Tipp:** Das Tool wird in einer späteren Version automatisiert Live-Daten von Finanz-APIs einlesen, um dich rechtzeitig vor solchen News zu warnen ('No-Trade-Zone').")

