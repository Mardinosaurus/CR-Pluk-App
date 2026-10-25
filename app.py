import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Carl Ras - TDABC Plukmåling", layout="centered")

st.title("Carl Ras - Plukmåling (TDABC)")
st.caption("Registrer tidsstempler for plukruter på lageret.")

if 'malinger' not in st.session_state:
    st.session_state.malinger = []

def gem_maling(handling):
    nu = datetime.now()
    st.session_state.malinger.append({
        'Dato': nu.strftime('%d-%m-%Y'),
        'Tidspunkt': nu.strftime('%H:%M:%S'),
        'Handling': handling
    })
    st.success(f"Registreret: {handling} kl. {nu.strftime('%H:%M:%S')}")

st.subheader("Registrer fase")

if st.button("🚀 Start rute / Klargøring", use_container_width=True):
    gem_maling("Start rute / Klargøring")

if st.button("📦 Pluk varen", use_container_width=True):
    gem_maling("Pluk varen")

if st.button("✅ Aflever emballage / Afslut", use_container_width=True):
    gem_maling("Aflever emballage / Afslut")

st.divider()

st.subheader("Dagens registreringer")
if st.session_state.malinger:
    df = pd.DataFrame(st.session_state.malinger)
    st.dataframe(df, use_container_width=True)
    
    csv_data = df.to_csv(index=False, sep=';').encode('utf-8')
    st.download_button(
        label="📥 Download CSV (tdabc_plukmalinger.csv)",
        data=csv_data,
        file_name="tdabc_plukmalinger.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("Ingen målinger registreret endnu. Tryk på en knap ovenfor.")
