import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# Initialize session state
if "predicted_price" not in st.session_state:
    st.session_state.predicted_price = None

st.markdown(
    """
    <style>
    .main > div.block-container {
        padding: 2rem 3rem;
        background: #f9fafb;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .stButton>button {
        background-color: #4B7BEC;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #3a5dcc;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title('🏠 Real Estate Price Estimator')

# Get user input through form
with st.form(key='params_for_api'):
    cols = st.columns(2)

    with cols[0]:
        bed = st.number_input('Number of bedrooms', min_value=0, step=1, help="How many bedrooms?")
        bath = st.number_input('Number of bathrooms', min_value=0, step=1, help="How many bathrooms?")
        house_size = st.number_input('House size (sq ft)', min_value=0, step=10, help="Total square footage")

    with cols[1]:
        acre_lot = st.number_input('Lot size (acres)', min_value=0.0, step=0.01, format="%.2f", help="Size of the lot in acres")
        zipcode = st.text_input('ZIP code', max_chars=10, help="Enter ZIP code to localize prediction")

    submit = st.form_submit_button('Make prediction')

if submit:
    params = dict(
        bed=float(bed),
        bath=float(bath),
        acre_lot=float(acre_lot),
        zip_code=zipcode,
        house_size=float(house_size)
    )

    # Url for the /predict endpoint
    #
    predict_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/predict'
    #predict_url = "http://127.0.0.1:8000/predict"

    # Send post request to api and save result
    with st.spinner('⏳ Calculating price estimate...'):
        try:
            #st.write("Sending the following data to API:", params)
            response = requests.post(predict_url, json=params)
            response.raise_for_status()
            prediction_data = response.json()
            pred = prediction_data.get('predicted_price')

            if pred is not None:
                st.session_state.predicted_price = pred
            else:
                st.error("Prediction missing in API response.")
                st.write("Full API response:", prediction_data) # Add for debugging
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to API: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# Display estimated price if present in session state
if st.session_state.predicted_price is not None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🏷️ Estimated Price")
    st.success(f"${st.session_state.predicted_price:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# Trend Estimate for ZIP_CODE section
if zipcode:
    st.header("📊 Investment Outlook")

    with st.form(key='trend_form'):
        time_horizon = st.selectbox(
            'Select time horizon (months)',
            [1, 3, 6, 12],
            help='How far into the future should we estimate?'
        )
        trend_submit = st.form_submit_button('Evaluate Investment Potential')

    if trend_submit:
        try:
            trend_params = {
                "zip_code": int(zipcode),
                "time_horizon": time_horizon
            }

            # Url for the /predict_investment endpoint
            trend_api_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/predict_investment'
            #trend_api_url = "http://127.0.0.1:8000/predict_investment"
            # Send post request and display result
            with st.spinner('Fetching investment outlook...'):
                trend_response = requests.post(trend_api_url, json=trend_params)
                trend_response.raise_for_status() # Raise an exception for HTTP errors
                trend_result = trend_response.json()

                if "is_good_investment" in trend_result:
                    is_good = trend_result["is_good_investment"]
                    rec_text = "Good time to buy 👍 & Bad time to sell 👎" if is_good else "Good time to sell 👍 & Bad time to buy 👎"
                    st.subheader(f"Outlook: {rec_text}")
                    #st.write(f"ZIP code: {trend_result['zip_code']}")
                    #st.write(f"Time Horizon: {trend_result['time_horizon_months']} months")
                else:
                    st.warning("Unexpected response format from the API.")
                    st.write("Full API response for trend:", trend_result) # Add for debugging

        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to trend API: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred while fetching trend data: {e}")
    st.header("📉 Historical Price Trend")
else:
    st.info("ℹ️ Enter a ZIP code above to check investment outlook.")


# Call zipcode_trend api
try:
    #zipcode_url = "http://127.0.0.1:8000/zipcode_trend"  # for local dev
    zipcode_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/zipcode_trend'
    response = requests.post(zipcode_url, json={"zip_code": zipcode})
    response.raise_for_status()
    data = response.json()
    df_zipcode = pd.DataFrame(data["trend"])
    df_zipcode["date"] = pd.to_datetime(df_zipcode["date"])
except Exception as e:
    st.error(f"Zipcode_trend Error fetching trend data: {e}")

# Call filter_city api
try:
    #city_url = "http://127.0.0.1:8000/filter_city"  # for local dev
    city_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/filter_city'
    response = requests.get(city_url, params={"zip_code": zipcode})
    response.raise_for_status()
    data = response.json()
    df_city = pd.DataFrame(data["data"])
    df_city["date"] = pd.to_datetime(df_city["date"])
    city = data['city']
except Exception as e:
    st.error(f"Filter_city Error fetching trend data: {e}")

# Call all_city api
try:
    #all_city_url = "http://127.0.0.1:8000/price_all_cities"  # for local dev
    all_city_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/price_all_cities'
    response = requests.get(all_city_url)
    response.raise_for_status()
    data = response.json()
    df_all_cities = pd.DataFrame(data["data"])
    df_all_cities["date"] = pd.to_datetime(df_all_cities["date"])
except Exception as e:
    st.error(f"Filter_city Error fetching trend data: {e}")


# Plot price for city
#k = df_city["zip_code"]  # for labeling

st.write("City DF shape:", df_city.shape)
st.write("Zipcode DF shape:", df_zipcode.shape)
st.write("All Cities DF shape:", df_all_cities.shape)

st.write("Sample of df_city:", df_city.head())
st.write("Sample of df_zipcode:", df_zipcode.head())
st.write("Sample of df_all_cities:", df_all_cities.head())
plt.figure(figsize=(14, 8))
sns.lineplot(data=df_city, x='date', y='price', label=f'City: {city}')
sns.lineplot(data=df_zipcode, x='date', y='price', label=f'Zipcode: {zipcode}')
sns.lineplot(data=df_all_cities, x='date', y='price', label='All Cities')
plt.title('Price in $ over time')
plt.xlabel('Year')
plt.ylabel(f'Price in $')
plt.xticks(rotation=45)
plt.tight_layout()
# plt.show()
st.pyplot(plt)
