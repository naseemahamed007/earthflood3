
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="MES FloodSense",
    page_icon="🌊",
    layout="wide"
)

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #071827 0%, #102d46 55%, #102238 100%);
    color: #f3f8ff;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1450px;
}
h1, h2, h3, p, label {
    color: #f3f8ff;
}
.hero {
    background: linear-gradient(110deg, #087eaa, #2455a4, #6538a5);
    padding: 32px;
    border-radius: 22px;
    margin-bottom: 24px;
}
.hero h1 {
    font-size: 42px;
    margin: 0;
}
.hero p {
    font-size: 17px;
    margin-bottom: 0;
}
.card {
    background: rgba(24, 57, 82, 0.92);
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #315c78;
    min-height: 125px;
}
.card-label {
    color: #b9d6e9;
    font-size: 14px;
}
.card-value {
    font-size: 27px;
    font-weight: 700;
    margin-top: 10px;
}
.info-box {
    background: #153951;
    padding: 18px;
    border-radius: 14px;
    border-left: 5px solid #38bdf8;
}
.stButton button {
    border-radius: 10px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------- DATA FUNCTIONS ----------
@st.cache_data(ttl=600)
def get_weather(city):
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=20
    )
    geo.raise_for_status()
    results = geo.json().get("results", [])

    if not results:
        return None

    place = results[0]

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": (
                "temperature_2m,relative_humidity_2m,"
                "precipitation,rain,wind_speed_10m"
            ),
            "hourly": (
                "precipitation,precipitation_probability,"
                "temperature_2m"
            ),
            "daily": (
                "precipitation_sum,precipitation_probability_max,"
                "rain_sum"
            ),
            "forecast_days": 3,
            "timezone": "auto"
        },
        timeout=25
    )
    response.raise_for_status()

    return {
        "place": place,
        "weather": response.json()
    }


def card(label, value, icon):
    st.markdown(f"""
    <div class="card">
        <div class="card-label">{icon} {label}</div>
        <div class="card-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def risk_assessment(weather):
    """Rainfall indicator only; not an official flood forecast."""
    hourly = weather["hourly"]
    current = weather["current"]

    rain = [
        float(x or 0)
        for x in hourly["precipitation"][:24]
    ]
    probability = [
        float(x or 0)
        for x in hourly["precipitation_probability"][:24]
    ]

    next24_rain = sum(rain)
    max_probability = max(probability, default=0)
    current_rain = float(current.get("precipitation", 0) or 0)

    # Illustrative thresholds, not locally calibrated flood criteria.
    if next24_rain >= 100 or current_rain >= 15:
        return (
            "HIGH RAINFALL CONCERN",
            "🔴",
            "#ff5555",
            "Heavy rainfall indicators. Check official alerts and "
            "avoid flood-prone locations."
        )
    elif next24_rain >= 50 or max_probability >= 80:
        return (
            "ELEVATED RAINFALL CONCERN",
            "🟠",
            "#ff9d42",
            "Rainfall may disrupt travel. Monitor official weather "
            "updates and local conditions."
        )
    elif next24_rain >= 15 or max_probability >= 50:
        return (
            "CAUTION",
            "🟡",
            "#ffd34d",
            "Rain is possible. Stay updated, especially if you live "
            "near a river or low-lying area."
        )
    else:
        return (
            "LOW RAINFALL INDICATOR",
            "🟢",
            "#38d996",
            "The forecast currently shows lower rainfall indicators. "
            "This does not guarantee flood safety."
        )


# ---------- HEADER ----------
st.markdown("""
<div class="hero">
    <h1>🌊 MES FloodSense</h1>
    <p>Explore weather • Monitor rainfall • Learn flood safety</p>
</div>
""", unsafe_allow_html=True)

# ---------- NAVIGATION ----------
page = st.sidebar.radio(
    "🧭 NAVIGATION",
    [
        "🏠 Home",
        "🚦 Risk Monitor",
        "🌧️ Rainfall Analytics",
        "🛰️ Maps & Location",
        "🛟 Flood Safety",
        "📘 About & Data"
    ]
)

st.sidebar.divider()
st.sidebar.caption("MES FloodSense | Educational monitoring project")
st.sidebar.info(
    "Not an emergency service. Follow official local alerts."
)

city = st.sidebar.text_input("📍 Enter a city", "Chennai").strip()

if not city:
    st.warning("Enter a city name in the sidebar.")
    st.stop()

try:
    result = get_weather(city)

    if result is None:
        st.error("City not found. Try another city name.")
        st.stop()

    place = result["place"]
    data = result["weather"]
    current = data["current"]
    hourly = data["hourly"]
    daily = data["daily"]

except requests.RequestException:
    st.error(
        "Could not load weather data. Check your internet connection "
        "and try again."
    )
    st.stop()
except (KeyError, ValueError, TypeError):
    st.error("The weather service returned unexpected data.")
    st.stop()

city_name = place["name"]
country = place.get("country", "")
location_label = f"{city_name}, {country}" if country else city_name

df = pd.DataFrame({
    "Time": pd.to_datetime(hourly["time"]),
    "Rainfall (mm)": hourly["precipitation"],
    "Rain probability (%)": hourly["precipitation_probability"],
    "Temperature (°C)": hourly["temperature_2m"]
})

df24 = df.head(24).copy()
risk_title, risk_icon, risk_color, risk_text = risk_assessment(data)

# ---------- HOME ----------
if page == "🏠 Home":
    st.subheader(f"Welcome to {location_label} 👋")
    st.write(
        "A visual overview of local weather and rainfall indicators."
    )

    st.image(
        "https://images.unsplash.com/photo-1519692933481-e162a57d6721"
        "?auto=format&fit=crop&w=1600&q=85",
        caption="Rainfall and changing weather conditions",
        use_container_width=True
    )

    cols = st.columns(4)
    with cols[0]:
        card("Temperature", f"{current['temperature_2m']} °C", "🌡️")
    with cols[1]:
        card("Humidity", f"{current['relative_humidity_2m']}%", "💧")
    with cols[2]:
        card("Current precipitation", f"{current['precipitation']} mm", "🌧️")
    with cols[3]:
        card("Wind speed", f"{current['wind_speed_10m']} km/h", "💨")

    st.write("")
    st.subheader("🚦 Rainfall indicator")

    st.markdown(f"""
    <div style="background:#17344b; padding:24px; border-radius:18px;
                border-left:7px solid {risk_color};">
        <h2 style="color:{risk_color};">{risk_icon} {risk_title}</h2>
        <p>{risk_text}</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "This is an illustrative rainfall indicator, not a verified "
        "flood-risk classification or official warning."
    )

    st.write("")
    st.subheader("📅 Rainfall forecast — next 3 days")

    daily_df = pd.DataFrame({
        "Date": daily["time"],
        "Rainfall (mm)": daily["precipitation_sum"],
        "Maximum rain probability (%)":
            daily["precipitation_probability_max"]
    })

    st.dataframe(daily_df, use_container_width=True, hide_index=True)

    st.info(
        "Use the sidebar to explore rainfall charts, the location map, "
        "risk indicators, and flood safety guidance."
    )

# ---------- RISK MONITOR ----------
elif page == "🚦 Risk Monitor":
    st.subheader("🚦 Rainfall Concern Monitor")
    st.write(f"Selected location: **{location_label}**")

    st.markdown(f"""
    <div style="background:#17344b; padding:25px; border-radius:18px;
                border-left:8px solid {risk_color};">
        <h2 style="color:{risk_color};">{risk_icon} {risk_title}</h2>
        <p>{risk_text}</p>
    </div>
    """, unsafe_allow_html=True)

    total_rain = float(df24["Rainfall (mm)"].sum())
    max_prob = float(df24["Rain probability (%)"].max())

    a, b = st.columns(2)
    with a:
        card("Forecast rainfall, next 24h", f"{total_rain:.1f} mm", "🌧️")
    with b:
        card("Maximum hourly rain probability", f"{max_prob:.0f}%", "☔")

    st.subheader("How to interpret the colours")
    st.markdown("""
    🟢 **Green — Lower rainfall indicator:** Lower forecast rainfall;
    flooding is still possible in vulnerable areas.

    🟡 **Yellow — Caution:** Check forecasts and be alert to changing
    local conditions.

    🟠 **Orange — Elevated concern:** Heavy rain may affect travel.
    Follow official advisories.

    🔴 **Red — High rainfall concern:** Take heavy rainfall seriously
    and check official warnings immediately.
    """)

    st.warning(
        "These colours are based on simple illustrative rainfall "
        "thresholds. They are not official flood alert levels. Actual "
        "flooding depends on drainage, river levels, terrain, soil, "
        "reservoir releases, and other local factors."
    )

# ---------- RAINFALL ANALYTICS ----------
elif page == "🌧️ Rainfall Analytics":
    st.subheader("🌧️ Rainfall Analytics")
    st.write(f"Forecast analysis for **{location_label}**")

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric(
        "Rainfall next 24h",
        f"{df24['Rainfall (mm)'].sum():.1f} mm"
    )
    metric2.metric(
        "Highest hourly rain probability",
        f"{df24['Rain probability (%)'].max():.0f}%"
    )
    metric3.metric(
        "Average forecast temperature",
        f"{df24['Temperature (°C)'].mean():.1f} °C"
    )

    st.subheader("📈 Select a chart")

    chart_choice = st.selectbox(
        "Choose the information to display",
        [
            "Rainfall",
            "Rain probability",
            "Temperature"
        ]
    )

    choices = {
        "Rainfall": ("Rainfall (mm)", "#36c5f0"),
        "Rain probability": ("Rain probability (%)", "#ffbf47"),
        "Temperature": ("Temperature (°C)", "#ff708d")
    }

    column, colour = choices[chart_choice]

    fig = px.area(
        df24,
        x="Time",
        y=column,
        title=f"{chart_choice} — Next 24 Hours",
        template="plotly_dark"
    )
    fig.update_traces(line_color=colour, fillcolor=colour)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Hourly forecast data")
    st.dataframe(df24, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Download rainfall data (CSV)",
        data=df24.to_csv(index=False),
        file_name="MES_FloodSense_Rainfall.csv",
        mime="text/csv"
    )

# ---------- MAP ----------
elif page == "🛰️ Maps & Location":
    st.subheader("🛰️ Location Explorer")
    st.write(f"Map location: **{location_label}**")

    st.image(
        "https://images.unsplash.com/photo-1524666041070-9a8768337a47"
        "?auto=format&fit=crop&w=1400&q=80",
        caption="Illustrative aerial landscape — not live satellite data",
        use_container_width=True
    )

    st.map(pd.DataFrame({
        "latitude": [place["latitude"]],
        "longitude": [place["longitude"]]
    }), zoom=10)

    st.markdown(f"""
    <div class="info-box">
        <b>📍 Selected location:</b> {location_label}<br>
        <b>Latitude:</b> {place['latitude']}<br>
        <b>Longitude:</b> {place['longitude']}
    </div>
    """, unsafe_allow_html=True)

    st.warning(
        "This map marks the selected city only. It does not display "
        "live flood boundaries, river levels, or satellite-based flood "
        "detection."
    )

# ---------- SAFETY GUIDE ----------
elif page == "🛟 Flood Safety":
    st.subheader("🛟 Flood Safety Guide")
    st.write(
        "Practical steps to prepare for flooding and respond safely."
    )

    st.image(
        "https://images.unsplash.com/photo-1547683905-f686c993aae5"
        "?auto=format&fit=crop&w=1400&q=80",
        caption="Flooding can create dangerous conditions",
        use_container_width=True
    )

    tab1, tab2, tab3 = st.tabs([
        "🟢 Before a flood",
        "🔴 During a flood",
        "🔵 After a flood"
    ])

    with tab1:
        st.markdown("""
        ### Prepare early
        - Monitor official weather forecasts and local alerts.
        - Identify safe routes and higher-ground locations.
        - Keep medicines, drinking water, a torch, and essential
          documents ready in a waterproof bag.
        - Charge phones and save emergency contacts.
        - Follow evacuation instructions from local authorities.
        """)

    with tab2:
        st.markdown("""
        ### Protect yourself
        - Move to higher ground when authorities advise it.
        - Never walk, swim, or drive through floodwater.
        - Stay away from drains, fast-moving water, and fallen wires.
        - Follow official evacuation instructions.
        - If trapped or in immediate danger, contact local emergency
          services.
        """)

    with tab3:
        st.markdown("""
        ### Return only when safe
        - Wait for authorities to confirm it is safe to return.
        - Avoid floodwater, damaged buildings, and electrical hazards.
        - Do not drink water unless it is confirmed safe.
        - Avoid touching electrical equipment in wet areas.
        - Report damaged power lines and other hazards to authorities.
        """)

    st.info(
        "In India, call 112 for emergency assistance where available. "
        "Follow Tamil Nadu authorities and official disaster-management "
        "advisories for local instructions."
    )

# ---------- ABOUT ----------
elif page == "📘 About & Data":
    st.subheader("📘 About MES FloodSense")

    st.markdown("""
    MES FloodSense is an educational weather and rainfall dashboard
    designed to make forecast information easier to explore.

    ### Main features
    - Current weather conditions
    - Hourly and daily rainfall forecasts
    - Interactive rainfall charts
    - Illustrative rainfall concern indicator
    - City location map
    - Flood preparedness and safety guide
    - CSV forecast export

    ### Data sources
    - **Open-Meteo:** weather forecasts and geocoding.
    - **OpenStreetMap / Streamlit map:** map display.
    - **Unsplash:** illustrative photography.
    
    ### Limitations
    This project does not use a dedicated flood prediction model,
    live river-gauge feeds, official warning feeds, or verified
    satellite flood detection. Its rainfall indicator is a simplified
    educational demonstration and must not be used for emergency
    decisions.
    """)

    st.markdown(
        "[Open-Meteo forecast documentation](https://open-meteo.com/)"
    )

    st.markdown(
        "[India emergency response information](https://112.gov.in/)"
    )

st.divider()
st.caption(
    f"MES FloodSense • {location_label} • "
    f"Weather data time: {current.get('time', 'Not available')} • "
    "Educational use only"
)
