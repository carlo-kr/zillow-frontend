import streamlit as st
import requests

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
        bed=bed,
        bath=bath,
        acre_lot=acre_lot,
        zip_code=zipcode,
        house_size=house_size
    )

    api_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/predict'

    with st.spinner('Calculating price estimate...'):
        try:
            response = requests.post(api_url, json=params)
            response.raise_for_status()
            st.write("🔎 Raw Response:", response.json())
            prediction = response.json()
            pred = prediction.get('prediction')

            if pred is not None:
                st.success(f'🏷️ Estimated Price: ${pred:,.2f}')
            else:
                st.error("Prediction missing in API response.")
        except Exception as e:
            st.error(f"Error fetching prediction: {e}")

st.markdown('---')

if zipcode:
    st.header("📊 Investment Outlook")

    with st.form(key='trend_form'):
        time_horizon = st.selectbox(
            'Select time horizon (months)',
            [3, 6, 12, 24],
            help='How far into the future should we estimate?'
        )
        trend_submit = st.form_submit_button('Evaluate Investment Potential')

    if trend_submit:
        trend_params = {
            "zipcode": zipcode,
            "time_horizon": time_horizon
        }

        trend_api_url = 'https://my-docker-image-for-zillow-880235258708.europe-west1.run.app/predict_investment'  # replace with your real endpoint

        with st.spinner('Fetching investment outlook...'):
            try:
                trend_response = requests.post(trend_api_url, json=trend_params)
                trend_response.raise_for_status()
                trend_result = trend_response.json()

                if trend_result.get("supported") is False:
                    st.warning(f"Sorry, we don’t have investment data for ZIP code {zipcode}. Try a different region.")
                else:
                    recommendation = trend_result.get("recommendation", "Unknown")
                    confidence = trend_result.get("confidence")
                    summary = trend_result.get("summary", "")

                    st.subheader(f"📌 Recommendation: {recommendation}")
                    if confidence is not None:
                        st.caption(f"Confidence: {confidence}%")
                    if summary:
                        st.write(summary)

            except Exception as e:
                st.error(f"Could not fetch trend data: {e}")
else:
    st.info("ℹ️ Enter a ZIP code above to check investment outlook.")
