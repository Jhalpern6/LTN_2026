import base64
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(
    page_title="Light the Night - Donation Tracker", layout="wide"
)

# Constants & Asset Paths
BACKGROUND_IMAGE = "assets/background_LTN.jpg"
BCU_LOGO = "assets/bcu_logo_LTN.jpg"
LANTERN_IMAGE_RED = "assets/lantern.png"
LANTERN_IMAGE_GOLD = "assets/yellow_lantern.png"
EXCEL_FILE = "LTN_2026_Donations.xlsx"

# Geographic Coordinates
MIA_LON, MIA_LAT = -80.1956, 25.7619  # Miami, FL (Start)
GSO_LON, GSO_LAT = -79.79472, 36.07667  # Greensboro, NC (Leg 1)
ROC_LON, ROC_LAT = -77.1528, 39.0840  # Rockville, MD (Stretch Goal Target)

LEG1_MILES = 800
LEG2_MILES = 300  # Greensboro to Rockville (300 Gold Miles)
TOTAL_DISTANCE_MILES = LEG1_MILES + LEG2_MILES  # 1,100 total physical miles

LEG1_TARGET_AMOUNT = 4000.0  # $5/mile for 800 miles
LEG2_TARGET_AMOUNT = 3000.0  # $10/mile for 300 miles ($3,000 total for Leg 2)
GOAL_AMOUNT = LEG1_TARGET_AMOUNT + LEG2_TARGET_AMOUNT  # $7,000 Stretch Goal

COST_PER_MILE_LEG1 = 5.0
COST_PER_MILE_LEG2 = 10.0  # $10 per Illuminating Gold Mile


# Cached File Operations
@st.cache_data
def get_base64_image(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""


@st.cache_data(ttl=60)
def load_donation_data(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading donor data: {e}")
        return pd.DataFrame(columns=["Donor Name", "Donation Amount"])


# Base64 Background & Image Processing
bg_base64 = get_base64_image(BACKGROUND_IMAGE)

lantern_red_base64 = get_base64_image(LANTERN_IMAGE_RED)
lantern_gold_base64 = get_base64_image(LANTERN_IMAGE_GOLD)

lantern_red_url = (
    f"data:image/png;base64,{lantern_red_base64}" if lantern_red_base64 else ""
)
lantern_gold_url = (
    f"data:image/png;base64,{lantern_gold_base64}"
    if lantern_gold_base64
    else ""
)

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

    /* Metric Cards Styling - Adjusted for Height and Alignment */
    div[data-testid="stMetric"] {{
        background-color: rgba(30, 41, 59, 0.85) !important;
        border: 1.5px solid rgba(216, 35, 42, 0.8) !important;
        border-radius: 8px !important;
        padding: 20px 16px !important;
        min-height: 135px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
        margin-bottom: 16px !important;
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

# Tiered Progress Calculation ($5/mi for Leg 1, $10/mi for Leg 2)
if total_raised <= LEG1_TARGET_AMOUNT:
    miles_flown = total_raised / COST_PER_MILE_LEG1
else:
    leg2_dollars = total_raised - LEG1_TARGET_AMOUNT
    leg2_miles_flown = min(leg2_dollars / COST_PER_MILE_LEG2, LEG2_MILES)
    miles_flown = LEG1_MILES + leg2_miles_flown

miles_flown = min(miles_flown, TOTAL_DISTANCE_MILES)
progress_pct = min(total_raised / GOAL_AMOUNT, 1.0)

# Multi-Leg Line Segment & Lantern Coordinate Calculations
lit_line_segments = []
unlit_line_segments = []
lantern_data = []

LANTERN_SPACING_MILES = 60

if miles_flown <= LEG1_MILES:
    # Currently in Leg 1 (Miami -> Greensboro)
    leg1_pct = miles_flown / LEG1_MILES
    current_lat = MIA_LAT + (GSO_LAT - MIA_LAT) * leg1_pct
    current_lon = MIA_LON + (GSO_LON - MIA_LON) * leg1_pct

    lit_line_segments.append(
        {"start": [MIA_LON, MIA_LAT], "end": [current_lon, current_lat]}
    )
    unlit_line_segments.append(
        {"start": [current_lon, current_lat], "end": [GSO_LON, GSO_LAT]}
    )
    unlit_line_segments.append(
        {"start": [GSO_LON, GSO_LAT], "end": [ROC_LON, ROC_LAT]}
    )

    if miles_flown > 0:
        num_lanterns = max(1, int(miles_flown // LANTERN_SPACING_MILES) + 1)
        fractions = np.linspace(0, leg1_pct, num_lanterns)
        for frac in fractions:
            lantern_data.append(
                {
                    "lat": MIA_LAT + (GSO_LAT - MIA_LAT) * frac,
                    "lon": MIA_LON + (GSO_LON - MIA_LON) * frac,
                    "icon_data": {
                        "url": lantern_red_url,
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
    # Leg 1 Complete! Currently in Leg 2 (Greensboro -> Rockville)
    leg2_miles_current = miles_flown - LEG1_MILES
    leg2_pct = leg2_miles_current / LEG2_MILES
    current_lat = GSO_LAT + (ROC_LAT - GSO_LAT) * leg2_pct
    current_lon = GSO_LON + (ROC_LON - GSO_LON) * leg2_pct

    # Full Leg 1 illuminated + Active Leg 2 portion
    lit_line_segments.append(
        {"start": [MIA_LON, MIA_LAT], "end": [GSO_LON, GSO_LAT]}
    )
    lit_line_segments.append(
        {"start": [GSO_LON, GSO_LAT], "end": [current_lon, current_lat]}
    )
    unlit_line_segments.append(
        {"start": [current_lon, current_lat], "end": [ROC_LON, ROC_LAT]}
    )

    # Leg 1 Red Lanterns
    num_l1 = int(LEG1_MILES // LANTERN_SPACING_MILES) + 1
    for frac in np.linspace(0, 1.0, num_l1):
        lantern_data.append(
            {
                "lat": MIA_LAT + (GSO_LAT - MIA_LAT) * frac,
                "lon": MIA_LON + (GSO_LON - MIA_LON) * frac,
                "icon_data": {
                    "url": lantern_red_url,
                    "width": 256,
                    "height": 512,
                    "anchorY": 512,
                    "anchorX": 128,
                    "mask": False,
                },
                "angle": 0,
            }
        )
    # Leg 2 Gold Lanterns (yellow_lantern.png)
    num_l2 = max(1, int(leg2_miles_current // LANTERN_SPACING_MILES))
    for frac in np.linspace(0, leg2_pct, num_l2 + 1)[1:]:
        lantern_data.append(
            {
                "lat": GSO_LAT + (ROC_LAT - GSO_LAT) * frac,
                "lon": GSO_LON + (ROC_LON - GSO_LON) * frac,
                "icon_data": {
                    "url": lantern_gold_url,
                    "width": 256,
                    "height": 512,
                    "anchorY": 512,
                    "anchorX": 128,
                    "mask": False,
                },
                "angle": 0,
            }
        )

# 1. STRETCH GOAL UPDATE BANNER
st.markdown(
    """
    <div style="
        background-color: rgba(30, 41, 59, 0.90);
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #FFC72C;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        margin-bottom: 15px;
    ">
        <h3 style="
            color: #FFC72C !important;
            -webkit-text-fill-color: #FFC72C !important;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 22px;
        ">
            CAMPAIGN UPDATE: EXPANDING OUR PATH TO ROCKVILLE, MD!
        </h3>
        <p style="
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            font-size: 17px;
            font-weight: 500;
            line-height: 1.6;
            margin: 0;
        ">
        Together, we surpassed our initial $4,000 goal and illuminated all 800 miles from Miami to Greensboro. Now, we are extending our journey to a stretch goal of $7,000!<br><br>
        My family joined Light The Night when my grandfather was diagnosed with blood cancer. Events like this do more than honor our loved ones, they raise the critical funds Blood Cancer United needs to support families and discover lifesaving treatments. That is why we walked together back then, and why I keep going today. We are carrying this mission 300 miles further to Rockville, MD, where we first walked by my grandfather's side.<br><br>
        Because this final stretch represents the heart of our mission, these remaining 300 miles are designated as <strong>Illuminating Gold Miles at $10 per mile</strong>. Every dollar in this final leg carries our lantern further, directly powering lifesaving research and patient resources. Let’s finish this journey together and keep the light shining bright for every patient, survivor, and family.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# 2. ORIGINAL CAMPAIGN PURPOSE BLURB
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
            font-size: 17px;
            font-weight: 500;
            line-height: 1.6;
            margin: 0;
        ">
        When a loved one is fighting cancer, every beacon of support matters. Having recently moved from North Carolina to Miami, I am still proudly participating in the Triad Light The Night Walk. To bridge the distance between where I am now and where my community is walking, this campaign tracks a symbolic path from Miami to Greensboro, representing our collective mission to bring light to the darkness of blood cancer for patients, survivors, and families.
        Every $5 contributed illuminates 1 mile of the path on our map. While 100% of donations go directly to Blood Cancer United to bring resources, lifesaving research, and unwavering support to those battling blood cancers, each dollar raised brings our lantern one step closer to our goal.
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
        f"Stretch Goal: ${GOAL_AMOUNT:,.0f}",
    )
    st.metric(
        "Miles Illuminated",
        f"{miles_flown:,.1f} mi",
        f"Total Target: {TOTAL_DISTANCE_MILES} mi",
    )
    st.metric(
        "Miles Still to Light",
        f"{max(0.0, TOTAL_DISTANCE_MILES - miles_flown):,.1f} mi",
    )
    st.metric("Stretch Goal Met", f"{progress_pct * 100:.1f}%")

with col_right:
    # 1. Gold Glow Layer
    gold_glow_layer = pdk.Layer(
        "LineLayer",
        data=lit_line_segments,
        get_source_position="start",
        get_target_position="end",
        get_color=[255, 199, 44, 90],
        get_width=8,
    )

    # 2. Gold Core Line
    gold_core_layer = pdk.Layer(
        "LineLayer",
        data=lit_line_segments,
        get_source_position="start",
        get_target_position="end",
        get_color=[255, 215, 0, 255],
        get_width=3,
    )

    # 3. Miles Remaining Line (Grey)
    grey_line_layer = pdk.Layer(
        "LineLayer",
        data=unlit_line_segments,
        get_source_position="start",
        get_target_position="end",
        get_color=[160, 160, 160, 180],
        get_width=3,
    )

    # 4. Repeating Lantern Markers Layer
    icon_layer = pdk.Layer(
        "IconLayer",
        data=lantern_data,
        get_icon="icon_data",
        get_size=4,
        size_scale=6.5,
        get_position=["lon", "lat"],
        get_angle="angle",
        pickable=False,
    )

    # PyDeck Map Display (Expanded map height to 660px)
    st.pydeck_chart(
        pdk.Deck(
            layers=[
                grey_line_layer,
                gold_glow_layer,
                gold_core_layer,
                icon_layer,
            ],
            initial_view_state=pdk.ViewState(
                latitude=((MIA_LAT + ROC_LAT) / 2) - 0.8,
                longitude=(MIA_LON + ROC_LON) / 2,
                zoom=5.0,
                pitch=30,
            ),
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        ),
        height=672,
    )

st.markdown(
    "<h2 style='text-align: center;'>Thank You for Your Support in Bringing Light to the Darkness of Cancer</h2>",
    unsafe_allow_html=True,
)
