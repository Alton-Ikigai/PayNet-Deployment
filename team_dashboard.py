import streamlit as st
import pandas as pd
import gspread
import glob
from datetime import datetime
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="PayNet Team Dashboard",
    page_icon="📊",
    layout="wide"
)

st_autorefresh(interval=60 * 1000, key="refresh")

DATE_FORMAT = "%m/%d/%Y %H:%M:%S"

TEAM_SHEETS = {
    "Karmen": {
        "sheet_id": "10oTpJalgKT-t8r0e2JWVMVKdCaeqCX41xsVsSP66ToQ",
        "worksheet": "Form Responses 1"
    },
    "Feng": {
        "sheet_id": "1xjylGxy2r1Pem_ZfG_ac4vgKat4omPHAEBfqiEKOnrI",
        "worksheet": "Form Responses 1"
    },
    "Eavin": {
        "sheet_id": "1whCvsa2OBZk7fcWRKmx5j1XYt18RQaKrdA1foA2gHcA",
        "worksheet": "Form Responses 1"
    },
    "Ivan": {
        "sheet_id": "167Ixt3w3q1AaOzuh7xGnjl6oZqBcN0K2mpVyzyzJLog",
        "worksheet": "Form Responses 1"
    },
    "Ryan": {
        "sheet_id": "1_vX8OCJntEwDqfOl6MZyA-S3YcPCa-s97QgcBamviyU",
        "worksheet": "Form Responses 1"
    },
    "Hom Minn": {
        "sheet_id": "1MusWy13ygmVyRgxKAWklEvbYLIr_15_WOQdNNJuSZpM",
        "worksheet": "Form Responses 1"
    }
}


def find_json_key():
    json_files = glob.glob("*.json")
    return [f for f in json_files if "package" not in f.lower()]


@st.cache_data(ttl=60)
def load_sheet(sheet_id, worksheet_name, json_key_path):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    creds = Credentials.from_service_account_file(json_key_path, scopes=scopes)
    gc = gspread.authorize(creds)

    sheet = gc.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)

    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()

    return df


def convert_timestamp(timestamp_series):
    return pd.to_datetime(
        timestamp_series,
        format=DATE_FORMAT,
        errors="coerce"
    )


with st.sidebar:
    st.title("⚙️ Dashboard")

    json_files = find_json_key()

    if json_files:
        json_key = json_files[0]
        st.success("✅ Google JSON connected")
    else:
        json_key = None
        st.error("❌ JSON key not found")

    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Auto refresh every 1 minute")


st.title("📊 PayNet Team Response Dashboard")
st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}")
st.divider()

if not json_key:
    st.info("Please place your Google service account JSON file in the same folder as this Python file.")
    st.stop()


summary = []

for promoter, config in TEAM_SHEETS.items():
    try:
        df = load_sheet(
            config["sheet_id"],
            config["worksheet"],
            json_key
        )

        total_raw_responses = len(df)

        if df.empty:
            summary.append({
                "Promoter": promoter,
                "Latest Date": "No Data",
                "Latest Quantity": 0,
                "Total Responses": 0,
                "Last Submission Time": "-",
                "Status": "⚠️ Empty Sheet"
            })
            continue

        if "Timestamp" not in df.columns:
            summary.append({
                "Promoter": promoter,
                "Latest Date": "No Timestamp",
                "Latest Quantity": 0,
                "Total Responses": total_raw_responses,
                "Last Submission Time": "-",
                "Status": "❌ Timestamp Column Missing"
            })
            continue

        df["Timestamp"] = convert_timestamp(df["Timestamp"])

        valid_df = df.dropna(subset=["Timestamp"])

        if valid_df.empty:
            summary.append({
                "Promoter": promoter,
                "Latest Date": "Invalid Date Format",
                "Latest Quantity": 0,
                "Total Responses": total_raw_responses,
                "Last Submission Time": "-",
                "Status": "❌ Date Format Error"
            })
            continue

        latest_datetime = valid_df["Timestamp"].max()
        latest_date = latest_datetime.date()

        latest_quantity = valid_df[
            valid_df["Timestamp"].dt.date == latest_date
        ].shape[0]

        summary.append({
            "Promoter": promoter,
            "Latest Date": latest_date.strftime("%d %b %Y"),
            "Latest Quantity": latest_quantity,
            "Total Responses": total_raw_responses,
            "Last Submission Time": latest_datetime.strftime("%d %b %Y, %H:%M:%S"),
            "Status": "✅ Connected"
        })

    except Exception as e:
        summary.append({
            "Promoter": promoter,
            "Latest Date": "Error",
            "Latest Quantity": 0,
            "Total Responses": 0,
            "Last Submission Time": "Error",
            "Status": f"❌ {e}"
        })


summary_df = pd.DataFrame(summary)

summary_df = summary_df.sort_values(
    by="Latest Quantity",
    ascending=False
)

total_responses = int(summary_df["Total Responses"].sum())
total_latest_quantity = int(summary_df["Latest Quantity"].sum())
connected_promoters = summary_df[summary_df["Status"] == "✅ Connected"].shape[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Responses", f"{total_responses:,}")

with col2:
    st.metric("Latest Quantity", f"{total_latest_quantity:,}")

with col3:
    st.metric("Connected Promoters", f"{connected_promoters:,}")

st.divider()

st.subheader("👥 Promoter Submission Summary")

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
    height=300
)

st.caption("Auto refresh every 1 minute")