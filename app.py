import streamlit as st
import pandas as pd
import re
from datetime import timedelta
from pathlib import Path

# ----------------------
# Template file
# ----------------------
TEMPLATE_FILE = "template.csv"

DEFAULT_HOTELS = {
    "Vester Søgade 6": "Scandic Copenhagen",
    "Falkoner Alle 9": "Scandic Falkoner",
    "Amager Boulevard 70": "Radisson Blu Scandinavia Hotel",
    "Blegdamsvej 3B": "University of Copenhagen Panum",
}

DEFAULT_CREW_MAP = [
    (r"(lh|lufthansa|a000)", ("LH Crew", "Get-e Lufthansa")),
    (r"(sk|sas)", ("SK Crew", "Get-e SAS")),
    (r"(ryr|ryanair|fr)", ("Ryanair Crew", "Get-e Lufthansa")),
]

PHONE_FILTER = "442038568655"

# ----------------------
# Utility Functions
# ----------------------

def load_template(template_file: Path):
    cols = list(pd.read_csv(template_file, nrows=0).columns)
    if "Customer Reference No" not in cols:
        cols.append("Customer Reference No")
    return cols

def parse_excel_datetime(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return pd.to_datetime(val, unit="d", origin="1899-12-30")
    try:
        return pd.to_datetime(val)
    except Exception:
        return None

def map_address(addr, hotels):
    s = str(addr)
    for snippet, hotel in hotels.items():
        if snippet in s:
            return f"{hotel}, {s}"
    if "airport" in s.lower():
        return f"CPH Airport, {s}"
    return s

def crew_mapping(pn, crew_rules):
    n = pn.lower()
    for pattern, (cust, code) in crew_rules:
        if re.search(pattern, n):
            return cust, code
    return "Get-e", "Get-e"

def vehicle_type(vtype, pax):
    v = str(vtype).lower()
    if "van" in v or "minivan" in v:
        return "People Carrier"
    if "sedan" in v:
        return "Standard"
    return "People Carrier" if pax >= 4 else "Standard"

def trim(text, limit):
    if pd.isna(text):
        return ""
    t = str(text).replace("\n", " ").strip()
    return t if len(t) <= limit else re.findall(rf"^.{{0,{limit}}}\b", t)[0].strip()

# ----------------------
# Load template columns
# ----------------------
template_cols = load_template(TEMPLATE_FILE)

# ----------------------
# Streamlit UI
# ----------------------
st.set_page_config(page_title="GET‑E Import Generator", layout="wide")
st.title("GET‑E Import File Generator")

# Raw XLSX uploader
raw_file = st.file_uploader("Upload GET‑E raw XLSX", type=["xlsx"])

if raw_file:
    raw_df = pd.read_excel(raw_file)
    st.write("Raw data preview (first 40 rows)")
    st.dataframe(raw_df.head(40))

    if st.button("Convert to Import CSV"):
        rows = []
        for _, r in raw_df.iterrows():
            cust, code = crew_mapping(r["PASSENGER_NAME"], DEFAULT_CREW_MAP)
            dt = parse_excel_datetime(r["PICKUP_TIME"])
            pickup_time = (dt - timedelta(minutes=10)).strftime("%d/%m/%Y %H:%M") if dt else ""

            row = {col: "" for col in template_cols}
            row.update({
                "Customer": cust,
                "Customer Code": code,
                "Pax Name": trim(r["PASSENGER_NAME"], 50),
                "Mobile 1": "" if str(r["CUSTOMER_CONTACT_NUMBER"]) == PHONE_FILTER else str(r["CUSTOMER_CONTACT_NUMBER"]),
                "Pick Up": map_address(r["PICKUP_ADDRESS"], DEFAULT_HOTELS),
                "Drop Off": map_address(r["DROP_OFF_ADDRESS"], DEFAULT_HOTELS),
                "Pickup Time": pickup_time,
                "Flight": (
                    re.sub(r"^([a-zA-Z]{2})(\d+)", r"\1 \2", str(r["FLIGHT_NUMBER"]))
                    if "airport" in str(r["PICKUP_ADDRESS"]).lower() and pd.notna(r["FLIGHT_NUMBER"])
                    else ""
                ),
                "Vehicle Type": vehicle_type(r["VEHICLE_TYPE"], r["AMOUNT_PASSENGERS"]),
                "Adults": int(r["AMOUNT_PASSENGERS"]),
                "Bags": int(r["AMOUNT_LUGGAGE"]) if not pd.isna(r["AMOUNT_LUGGAGE"]) else 0,
                "Pick Up Instructions": trim(r.get("CLIENT_INSTRUCTIONS", ""), 100),
                "Base Rate": round(r["COST"]),
                "Price": "",
                "Service Type": "Point to Point",
                "Trip Status": "UN-SCHEDULED",
                "Payment Method": "Booked on account",
                "Customer Reference No": str(r["BOOKING_NUMBER"]),
                "Ref No": ""
            })
            rows.append(row)

        df_out = pd.DataFrame(rows, columns=template_cols)
        st.success(f"Generated {len(df_out)} rows ✓")
        st.dataframe(df_out.head(40), height=300)

        # CSV download
        st.download_button(
            label="Download import‑ready CSV",
            data=df_out.to_csv(index=False).encode(),
            file_name="GETE_Import.csv",
            mime="text/csv"
        )
