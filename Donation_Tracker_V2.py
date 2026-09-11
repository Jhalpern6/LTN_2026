import base64
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(
    page_title="Light the Night - Donation Tracker", layout="wide"
)

# Constants
BACKGROUND_IMAGE = "assets/background_LTN.jpg"
BCU_LOGO = "assets/bcu_logo_LTN.jpg"
LANTERN_IMAGE = "assets/lantern.png"
EXCEL_FILE = "LTN_2026_Donations.xlsx"

MIA_LON, MIA_LAT = -80.1956, 25.7619
GSO_LON, GSO_LAT = -79.79472, 36.07667
TOTAL_DISTANCE_MILES = 800
COST_PER_MILE = 5
GOAL_AMOUNT = TOTAL_DISTANCE_MILES * COST_PER_MILE

# Cached File Operations
@st.cache_data
def get_base64_image(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""

# Refreshes automatically every 60 seconds to pull new data
@st.cache_data(ttl=60)
def load_donation_data(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(file_path)
        df["Miles Sponsored"] = df["Donation Amount"] / COST_PER_MILE
        return df
    except Exception as e:
        st.error(f"Error loading donor data: {e}")
        return pd.DataFrame(
            columns=["Donor Name", "Donation Amount", "Miles Sponsored"]
        )


# Base64 Background & Image Processing
bg_base64 = get_base64_image(BACKGROUND_IMAGE)
lantern_base64 = get_base64_image(LANTERN_IMAGE)
lantern_url = f"data:image/png;base64,{lantern_base64}" if lantern_base64 else ""

bg_css = (
    f"""
    .stApp {{
        background-image: url("data:image/jpg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
"""
    if bg_base64
    else ""
)

# Custom Styling Overrides
st.markdown(
    f"""
    <style>
    {bg_css}

    /* Global White Typography Overrides */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp label, .stApp p, .stApp span, .stApp div {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    .stApp h1, .stApp h2, .stApp h3 {{
        font-weight: 800 !important;
    }}

    /* Metric Cards Styling */
    div[data-testid="stMetric"] {{
        background-color: rgba(30, 41, 59, 0.85) !important;
        border: 1.5px solid rgba(216, 35, 42, 0.8) !important;
        border-radius: 8px !important;
        padding: 14px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
    }}

    div[data-testid="stMetricLabel"] * {{
        font-weight: 700 !important;
    }}

    /* Card Values Accent Color (Gold) */
    div[data-testid="stMetricValue"] * {{
        color: #FFC72C !important;
        -webkit-text-fill-color: #FFC72C !important;
        font-weight: 800 !important;
    }}

    div[data-testid="stMetricDelta"] * {{
        color: #CBD5E1 !important;
        -webkit-text-fill-color: #CBD5E1 !important;
    }}

    /* Hide Metric Delta Arrow Icons */
    div[data-testid="stMetricDelta"] svg {{
        display: none !important;
    }}

    /* Recent Donors Table Styling */
    div[data-testid="stDataFrame"] {{
        background-color: rgba(30, 41, 59, 0.85) !important;
        border: 1.5px solid rgba(216, 35, 42, 0.8) !important;
        border-radius: 8px !important;
        padding: 8px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
    }}
    </style>
""",
    unsafe_allow_html=True,
)

# Header Section
col_logo, col_title = st.columns([1, 4], vertical_alignment="center")
with col_logo:
    st.image(BCU_LOGO, use_container_width=True)
with col_title:
    st.title("Illuminating The Way Together")
    st.subheader("Carrying the lantern from Miami, FL to Greensboro, NC")

st.divider()

# Load Data & Calculations
df = load_donation_data(EXCEL_FILE)
total_raised = df["Donation Amount"].sum() if not df.empty else 0.0
miles_flown = min(total_raised / COST_PER_MILE, TOTAL_DISTANCE_MILES)
progress_pct = min(miles_flown / TOTAL_DISTANCE_MILES, 1.0)

# Current Lantern Position
current_lat = MIA_LAT + (GSO_LAT - MIA_LAT) * progress_pct
current_lon = MIA_LON + (GSO_LON - MIA_LON) * progress_pct

# Description
st.markdown(
    """
    <div style="
        background-color: rgba(30, 41, 59, 0.85);
        padding: 20px;
        border-radius: 8px;
        border: 1.5px solid rgba(216, 35, 42, 0.8);
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
        margin-bottom: 25px;
    ">
        <p style="
            color: #FFC72C !important;
            -webkit-text-fill-color: #FFC72C !important;
            font-size: 20px;
            font-weight: 600;
            line-height: 1.6;
            margin: 0;
        ">
        When a loved one is fighting cancer, every beacon of support matters. Having recently moved from North Carolina to Miami, I am still proudly participating in the Triad Light The Night Walk. To bridge the distance between where I am now and where my community is walking, this campaign tracks a symbolic 800-mile path from Miami to Greensboro, representing our collective mission to bring light to the darkness of blood cancer for patients, survivors, and families.
        Every $5 contributed illuminates 1 mile of the 800-mile path on our map. While 100% of donations go directly to Blood Cancer United to bring resources, lifesaving research, and unwavering support to those battling blood cancers, each dollar raised brings our lantern one step closer to Greensboro.
        Help us light up the map and prove that together, we can bring light to the darkness of cancer.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Dashboard Layout
col_left, col_right = st.columns([1, 2])

with col_left:
    st.metric(
        "Total Funds Raised",
        f"${total_raised:,.2f}",
        f"Goal: ${GOAL_AMOUNT:,.0f}",
    )
    st.metric(
        "Miles Illuminated",
        f"{miles_flown:,.1f} mi",
        f"Total: {TOTAL_DISTANCE_MILES} mi",
    )
    st.metric(
        "Miles Still to Light", f"{TOTAL_DISTANCE_MILES - miles_flown:,.1f} mi"
    )
    st.metric("Path Lit", f"{progress_pct * 100:.1f}%")

with col_right:
    # Gold Glow Layer
    gold_glow_layer = pdk.Layer(
        "LineLayer",
        data=[
            {"start": [MIA_LON, MIA_LAT], "end": [current_lon, current_lat]}
        ],
        get_source_position="start",
        get_target_position="end",
        get_color=[255, 199, 44, 90],
        get_width=8,
    )

    # Gold Core Line
    gold_core_layer = pdk.Layer(
        "LineLayer",
        data=[
            {"start": [MIA_LON, MIA_LAT], "end": [current_lon, current_lat]}
        ],
        get_source_position="start",
        get_target_position="end",
        get_color=[255, 215, 0, 255],
        get_width=3,
    )

    # Miles Remaining Line (Grey)
    grey_line_layer = pdk.Layer(
        "LineLayer",
        data=[
            {"start": [current_lon, current_lat], "end": [GSO_LON, GSO_LAT]}
        ],
        get_source_position="start",
        get_target_position="end",
        get_color=[160, 160, 160, 180],
        get_width=3,
    )

    # Generate Multiple Lantern Points along the Illuminated Path
    LANTERN_SPACING_MILES = 50

    if miles_flown > 0:
        num_lanterns = max(1, int(miles_flown // LANTERN_SPACING_MILES) + 1)
        fractions = np.linspace(0, progress_pct, num_lanterns)

        lantern_data = []
        for frac in fractions:
            lat = MIA_LAT + (GSO_LAT - MIA_LAT) * frac
            lon = MIA_LON + (GSO_LON - MIA_LON) * frac
            lantern_data.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "icon_data": {
                        "url": lantern_url,
                        "width": 256,
                        "height": 512,
                        "anchorY": 512,
                        "anchorX": 128,
                        "mask": False,
                    },
                    "angle": 0,
                }
            )
    else:
        lantern_data = []

    # Repeating Lantern Markers Layer
    icon_layer = pdk.Layer(
        "IconLayer",
        data=lantern_data,
        get_icon="icon_data",
        get_size=4,
        size_scale=6,
        get_position=["lon", "lat"],
        get_angle="angle",
        pickable=False,
    )

    # PyDeck Map Display
    st.pydeck_chart(
        pdk.Deck(
            layers=[
                grey_line_layer,
                gold_glow_layer,
                gold_core_layer,
                icon_layer,
            ],
            initial_view_state=pdk.ViewState(
                latitude=((MIA_LAT + GSO_LAT) / 2) -0.8,
                longitude=(MIA_LON + GSO_LON) / 2,
                zoom=5.1,
                pitch=35,
            ),
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        ),
        height=525,
    )

st.markdown(
    "<h2 style='text-align: center;'>Thank You for Your Support in Bringing Light to the Darkness of Cancer</h2>",
    unsafe_allow_html=True,
)
