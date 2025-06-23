import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Initialize empty DataFrames for storing API data
df_city = pd.DataFrame()
df_zipcode = pd.DataFrame()
df_all_cities = pd.DataFrame()

plt.clf()  # Clear any existing matplotlib plots

# Initialize session state to store predicted price across interactions
if "predicted_price" not in st.session_state:
    st.session_state.predicted_price = None

# Custom CSS styling for the app container and buttons
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

# Form for user to input house parameters for price prediction
with st.form(key='params_for_api'):
    cols = st.columns(2)

    # Left column inputs
    with cols[0]:
        bed = st.number_input('Number of bedrooms', min_value=0, step=1, help="How many bedrooms?")
        bath = st.number_input('Number of bathrooms', min_value=0, step=1, help="How many bathrooms?")
        house_size = st.number_input('House size (sq ft)', min_value=0, step=10, help="Total square footage")

    # Right column inputs
    with cols[1]:
        acre_lot = st.number_input('Lot size (acres)', min_value=0.0, step=0.01, format="%.2f", help="Size of the lot in acres")
        zipcode = st.text_input('ZIP code', max_chars=10, help="Enter ZIP code to localize prediction")

    submit = st.form_submit_button('Make prediction')

if submit:
    # Prepare parameters dict for API call
    params = dict(
        bed=float(bed),
        bath=float(bath),
        acre_lot=float(acre_lot),
        zip_code=zipcode,
        house_size=float(house_size)
    )

    # API endpoint for price prediction
    predict_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/predict'
    # For local development, uncomment the following line:
    # predict_url = "http://127.0.0.1:8000/predict"

    # Make POST request to prediction API
    with st.spinner('⏳ Calculating price estimate...'):
        try:
            response = requests.post(predict_url, json=params)
            response.raise_for_status()  # Raise error for bad HTTP status codes
            prediction_data = response.json()
            pred = prediction_data.get('predicted_price')

            if pred is not None:
                st.session_state.predicted_price = pred
            else:
                st.error("Prediction missing in API response.")
                st.write("Full API response:", prediction_data)  # Debugging info
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to API: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# Display the estimated price if available in session state
if st.session_state.predicted_price is not None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🏷️ Estimated Price")
    st.success(f"${st.session_state.predicted_price:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# Show investment outlook section only if ZIP code is provided
if zipcode:
    st.header("📊 Investment Outlook")

    # Form for selecting time horizon to evaluate investment potential
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

            # API endpoint for investment prediction
            trend_api_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/predict_investment'
            # For local dev, uncomment:
            # trend_api_url = "http://127.0.0.1:8000/predict_investment"

            with st.spinner('Fetching investment outlook...'):
                trend_response = requests.post(trend_api_url, json=trend_params)
                trend_response.raise_for_status()
                trend_result = trend_response.json()

                if "is_good_investment" in trend_result:
                    is_good = trend_result["is_good_investment"]
                    rec_text = "Good time to buy 👍 & Bad time to sell 👎" if is_good else "Good time to sell 👍 & Bad time to buy 👎"
                    st.subheader(f"Outlook: {rec_text}")
                else:
                    st.warning("Unexpected response format from the API.")
                    st.write("Full API response for trend:", trend_result)  # Debugging info

        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to trend API: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred while fetching trend data: {e}")

    st.header("📉 Historical Price Trend")

    # Fetch historical price trend for the ZIP code
    try:
        zipcode_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/zipcode_trend'
        # Local dev URL:
        # zipcode_url = "http://127.0.0.1:8000/zipcode_trend"
        response = requests.post(zipcode_url, json={"zip_code": zipcode})
        response.raise_for_status()
        data = response.json()
        df_zipcode = pd.DataFrame(data["trend"])
        df_zipcode["date"] = pd.to_datetime(df_zipcode["date"])
    except Exception as e:
        st.error(f"Zipcode_trend error fetching trend data: {e}")

    # Fetch city-level trend data for the ZIP code
    try:
        city_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/filter_city'
        # Local dev URL:
        # city_url = "http://127.0.0.1:8000/filter_city"
        response = requests.get(city_url, params={"zip_code": zipcode})
        response.raise_for_status()
        data = response.json()
        df_city = pd.DataFrame(data["data"])
        df_city["date"] = pd.to_datetime(df_city["date"])
        city = data['city']
    except Exception as e:
        st.error(f"Filter_city error fetching trend data: {e}")

    # Fetch overall trend data for all cities
    try:
        all_city_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/price_all_cities'
        # Local dev URL:
        # all_city_url = "http://127.0.0.1:8000/price_all_cities"
        response = requests.get(all_city_url)
        response.raise_for_status()
        data = response.json()
        df_all_cities = pd.DataFrame(data["data"])
        df_all_cities["date"] = pd.to_datetime(df_all_cities["date"])
    except Exception as e:
        st.error(f"Price_all_cities error fetching trend data: {e}")

else:
    st.info("ℹ️ Enter a ZIP code above to check investment outlook.")

# Plot historical price trends if data is available
if not df_city.empty and not df_zipcode.empty and not df_all_cities.empty:
    plt.close('all')  # Close any existing matplotlib figures
    fig, ax = plt.subplots(figsize=(14, 8))  # New figure and axis

    sns.lineplot(data=df_city, x='date', y='price', label=f'City: {city}', ax=ax)
    sns.lineplot(data=df_zipcode, x='date', y='price', label=f'Zipcode: {zipcode}', ax=ax)
    sns.lineplot(data=df_all_cities, x='date', y='price', label='All Cities', ax=ax)

    ax.set_title('Price in $ over time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Price in $')
    plt.setp(ax.get_xticklabels(), rotation=45)  # Rotate date labels for readability

    st.pyplot(fig)  # Display the plot in Streamlit app
    plt.close(fig)  # Close the figure after rendering

else:
    st.warning("Enter a ZIP code to view price trends")
