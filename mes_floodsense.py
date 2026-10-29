import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="MES FloodSense",
    page_icon="🌊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #071827, #102c42);
    color: #ffffff;
}
h1, h2, h3, p, label {
    color: #ffffff !important;
}
.metric-card {
    background: #15364c;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #28516a;
}
</style>
""", unsafe_allow_html=True)

st.title("🌊 MES FloodSense")
st.caption("Weather • Rainfall Monitoring • Flood Awareness")

st.info(
    "This dashboard monitors weather and rainfall indicators. "
    "It does not provide verified real-time flood warnings."
)

city = st.text_input("Enter a city", "Chennai")

if st.button("🔍 Check Weather", type="primary"):
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_response = requests.get(
            geo_url,
            params={"name": city, "count": 1, "language": "en"},
            timeout=15
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            st.error("City not found. Please try another city.")
        else:
            place = geo_data["results"][0]
            latitude = place["latitude"]
            longitude = place["longitude"]
            city_name = place["name"]

            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_response = requests.get(
                weather_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "precipitation,rain,wind_speed_10m"
                    ),
                    "hourly": (
                        "precipitation,precipitation_probability,"
                        "temperature_2m"
                    ),
                    "forecast_days": 3,
                    "timezone": "auto"
                },
                timeout=20
            )
            weather_response.raise_for_status()
            weather = weather_response.json()

            current = weather["current"]
            hourly = weather["hourly"]

            st.subheader(f"📍 Weather in {city_name}")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "🌡️ Temperature",
                f"{current['temperature_2m']} °C"
            )
            col2.metric(
                "💧 Humidity",
                f"{current['relative_humidity_2m']}%"
            )
            col3.metric(
                "🌧️ Precipitation",
                f"{current['precipitation']} mm"
            )
            col4.metric(
                "💨 Wind speed",
                f"{current['wind_speed_10m']} km/h"
            )

            st.subheader("📊 Rainfall Forecast")

            df = pd.DataFrame({
                "Time": pd.to_datetime(hourly["time"]),
                "Rainfall (mm)": hourly["precipitation"],
                "Rain probability (%)":
                    hourly["precipitation_probability"],
                "Temperature (°C)": hourly["temperature_2m"]
            })

            df = df.head(24)

            chart = px.area(
                df,
                x="Time",
                y="Rainfall (mm)",
                title="Next 24 Hours — Expected Rainfall",
                template="plotly_dark"
            )
            st.plotly_chart(chart, use_container_width=True)

            st.subheader("🛰️ Location Map")

            st.map(pd.DataFrame({
                "latitude": [latitude],
                "longitude": [longitude]
            }))

            st.subheader("📋 Hourly Forecast")
            st.dataframe(df, use_container_width=True)

            st.download_button(
                "⬇️ Download Forecast CSV",
                data=df.to_csv(index=False),
                file_name="mes_floodsense_forecast.csv",
                mime="text/csv"
            )

            st.caption(
                "Data source: Open-Meteo. Forecasts are estimates, "
                "not confirmed flood alerts."
            )

    except requests.RequestException:
        st.error(
            "Unable to fetch weather data. Check your connection "
            "and try again."
        )
    except (KeyError, ValueError, TypeError):
        st.error("Unexpected weather data received. Please try again.")

st.divider()
st.caption("MES FloodSense | Weather and Rainfall Monitoring")
