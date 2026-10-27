import streamlit as st
import pandas as pd
from datetime import datetime
import requests

st.set_page_config(page_title="Carl Ras - TDABC Plukmåling", layout="centered")

# Skjul ALT Streamlit-relateret UI (header, footer, viewer badge, profil, deploy knap osv.)
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
    .stAppHeader {display: none !important;}
    
    /* Skjul Streamlit Cloud "Hosted with Streamlit" badge og profilikon i bunden */
    .viewerBadge_container__1tB2o,
    .viewerBadge_link__1S137,
    [class*="viewerBadge"],
    [class*="styles_viewerBadge"],
    a[href*="streamlit.app"],
    a[href*="streamlit.io"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    
    /* Gør knapper og layout endnu mere rent */
    div.block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("Carl Ras - Plukmåling (TDABC)")
st.caption("Registrer tidsstempler for plukruter på lageret.")

# Session state initialization
if 'malinger' not in st.session_state:
    st.session_state.malinger = []
if 'pluk_trin' not in st.session_state:
    st.session_state.pluk_trin = 1
if 'rute_aktiv' not in st.session_state:
    st.session_state.rute_aktiv = False
if 'klar_til_indsendelse' not in st.session_state:
    st.session_state.klar_til_indsendelse = False
if 'valgt_sorensen' not in st.session_state:
    st.session_state.valgt_sorensen = False
if 'valgt_forsendelse' not in st.session_state:
    st.session_state.valgt_forsendelse = False
if 'bekraeft_send' not in st.session_state:
    st.session_state.bekraeft_send = False
if 'transport_trykket' not in st.session_state:
    st.session_state.transport_trykket = False
if 'emballage_trykket' not in st.session_state:
    st.session_state.emballage_trykket = False
if 'berta_transport_trykket' not in st.session_state:
    st.session_state.berta_transport_trykket = False

# 1. Stamdata
st.subheader("1. Før du starter ruten")

initialer = st.text_input("Dine initialer *", value=st.session_state.get('saved_initialer', ''), placeholder="f.eks. MHA").strip()
if initialer:
    st.session_state.saved_initialer = initialer

hoved_pluktype = st.selectbox(
    "Vælg pluktype *",
    ["Kassepluk", "Pallepluk", "Længde pluk", "Buffer pluk"]
)

palle_underType = ""
antal_kassepluk = 1

if hoved_pluktype == "Pallepluk":
    palle_underType = st.radio("Vælg palletype *", ["Helpalle pluk", "Halv pallepluk"], horizontal=True)
    endelig_pluktype = f"Pallepluk ({palle_underType})"
elif hoved_pluktype == "Kassepluk":
    antal_kassepluk = st.number_input("Antal pluk på ruten", min_value=1, max_value=100, value=1, step=1)
    endelig_pluktype = f"Kassepluk ({antal_kassepluk} pluk på rute)"
else:
    endelig_pluktype = hoved_pluktype

st.divider()
kan_starte = len(initialer) > 0 and not st.session_state.klar_til_indsendelse

if not len(initialer) > 0:
    st.warning("Indtast dine initialer ovenfor for at starte ruten.")
elif st.session_state.klar_til_indsendelse:
    st.info("Ruten er afsluttet! Rul ned til '3. Indsend data' for at gemme målingen.")

# 2. Registrering af faser
st.subheader("2. Registrer faser på ruten")

def gem_stempel(handling, ekstra_info=""):
    nu = datetime.now()
    st.session_state.malinger.append({
        'Dato': nu.strftime('%Y-%m-%d'),
        'Tidspunkt': nu.strftime('%H:%M'),
        'Initialer': initialer,
        'Pluktype': endelig_pluktype,
        'Handling': handling,
        'Ekstra_Info': ekstra_info if ekstra_info else "-"
    })

if not st.session_state.rute_aktiv:
    if st.button("Start plukrute", disabled=not kan_starte, type="primary", use_container_width=True):
        st.session_state.rute_aktiv = True
        st.session_state.klar_til_indsendelse = False
        st.session_state.pluk_trin = 1
        st.session_state.transport_trykket = False
        st.session_state.emballage_trykket = False
        st.session_state.berta_transport_trykket = False
        st.session_state.valgt_sorensen = False
        st.session_state.valgt_forsendelse = False
        st.session_state.bekraeft_send = False
        gem_stempel("Start plukrute")
        st.rerun()
else:
    st.info(f"Aktiv rute: {initialer} | {endelig_pluktype}")

    # Hvis Buffer pluk: erstat emballagepålægning med "Brug af Berta"
    if hoved_pluktype == "Buffer pluk":
        st.write("**Brug af Berta:**")
        brug_berta = st.radio("Brug af Berta", ["Nej", "Ja"], horizontal=True, index=0, key="berta_radio_choice")
        
        if brug_berta == "Ja":
            berta_type = "primary" if st.session_state.berta_transport_trykket else "secondary"
            if st.button("Transport til Berta", type=berta_type, use_container_width=True):
                st.session_state.berta_transport_trykket = True
                gem_stempel("Transport til Berta")
                st.rerun()
    else:
        emb_type = "primary" if st.session_state.emballage_trykket else "secondary"
        if st.button("Afslut emballage pålægning", type=emb_type, use_container_width=True):
            st.session_state.emballage_trykket = True
            gem_stempel("Afslut emballage pålægning")
            st.rerun()

    st.divider()

    # Kompakt plukplads modul (1 til 100)
    trin = st.session_state.pluk_trin
    st.write(f"**Aktuel plukplads: Nr. {trin} (af maks 100)**")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        trans_type = "primary" if st.session_state.transport_trykket else "secondary"
        if st.button(f"Transport til pluk {trin}", type=trans_type, use_container_width=True):
            st.session_state.transport_trykket = True
            gem_stempel(f"Transport til plukplads {trin}")
            st.rerun()

    with col_t2:
        if st.button(f"Afslut pluk {trin}", use_container_width=True):
            gem_stempel(f"Afslut pluk {trin}")
            st.session_state.transport_trykket = False
            if st.session_state.pluk_trin < 100:
                st.session_state.pluk_trin += 1
            st.rerun()

    st.divider()

    st.subheader("Afslutning af rute")

    # Bemærkning / Fejl på ruten
    with st.expander("⚠️ Tilføj bemærkning / fejl på rute (valgfri)"):
        bemaerkning_input = st.text_input("Beskrivelse af fejl eller afvigelse:", key="bemaerkning_input_field", placeholder="f.eks. manglende vare, beskadiget emballage")
        if st.button("Gem bemærkning"):
            if bemaerkning_input.strip():
                gem_stempel("Fejl / Bemærkning", ekstra_info=bemaerkning_input.strip())
                st.success(f"Gemt bemærkning: '{bemaerkning_input.strip()}'")
                st.rerun()

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        sor_type = "primary" if st.session_state.valgt_sorensen else "secondary"
        if st.button("Afsat til Sørensen", type=sor_type, use_container_width=True):
            st.session_state.valgt_sorensen = True
            st.session_state.valgt_forsendelse = False
            gem_stempel("Afsat til Sørensen")
            st.rerun()

    with col_f2:
        for_type = "primary" if st.session_state.valgt_forsendelse else "secondary"
        if st.button("Forsendelsesproces begyndt", type=for_type, use_container_width=True):
            st.session_state.valgt_sorensen = False
            st.session_state.valgt_forsendelse = True
            gem_stempel("Forsendelsesproces begyndt")
            st.rerun()

    # Hvis enten Sørensen eller Forsendelse er valgt, vis de 3 tillægstjenester
    if st.session_state.valgt_sorensen or st.session_state.valgt_forsendelse:
        st.divider()
        overskrift_tekst = "Sørensen (Forsendelse)" if st.session_state.valgt_sorensen else "Forsendelsesproces"
        st.write(f"**Viderelevering Krav: {overskrift_tekst}**")

        har_fg = st.checkbox("Farlig gods")
        ant_fg = st.number_input("Antal farlig gods", min_value=0, value=1 if har_fg else 0) if har_fg else 0

        har_ft = st.checkbox("Festool registrering")
        ant_ft = st.number_input("Antal Festool registreringer", min_value=0, value=1 if har_ft else 0) if har_ft else 0

        har_srv = st.checkbox("Service")
        ant_srv = st.number_input("Antal service", min_value=0, value=1 if har_srv else 0) if har_srv else 0

        if st.button("Gem tillægstjenester", type="primary", use_container_width=True):
            tillaeg = []
            if har_fg and ant_fg > 0:
                tillaeg.append(f"Farlig gods: {ant_fg}")
            if har_ft and ant_ft > 0:
                tillaeg.append(f"Festool: {ant_ft}")
            if har_srv and ant_srv > 0:
                tillaeg.append(f"Service: {ant_srv}")

            info_str = ", ".join(tillaeg) if tillaeg else "Ingen tillæg"
            gem_stempel(f"Tillægstjenester v. {overskrift_tekst}", ekstra_info=info_str)
            st.success("Tillægstjenester registreret!")
            st.rerun()

    st.divider()
    if st.button("Afslut plukordre", type="primary", use_container_width=True):
        gem_stempel("Afslut plukordre")
        st.session_state.rute_aktiv = False
        st.session_state.klar_til_indsendelse = True
        st.session_state.valgt_sorensen = False
        st.session_state.valgt_forsendelse = False
        st.rerun()

st.divider()

if st.session_state.malinger:
    st.subheader("3. Indsend data")
    if not st.session_state.bekraeft_send:
        if st.button("Send data", type="primary", use_container_width=True):
            st.session_state.bekraeft_send = True
            st.rerun()
    else:
        st.warning("Er du sikker?")
        c_ja, c_nej = st.columns(2)
        with c_ja:
            if st.button("Ja", type="primary", use_container_width=True):
                FORM_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdAu8l9zMvnPmeDrQnJCj3Y2jvjJp--pjUPcP5A8aCUxu0CSA/formResponse"
                
                fejl_antal = 0
                succes_antal = 0
                sidste_fejl = ""
                
                with st.spinner("Sender registreringer til Google Form... Vent venligst..."):
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    for row in st.session_state.malinger:
                        payload = {
                            'entry.1109742049': str(row.get('Dato', '')),
                            'entry.785756491': str(row.get('Tidspunkt', '')),
                            'entry.1387317177': str(row.get('Initialer', '')),
                            'entry.1597480740': str(row.get('Pluktype', '')),
                            'entry.2111546458': str(row.get('Handling', '')),
                            'entry.1581018160': str(row.get('Ekstra_Info', '-')) or '-'
                        }
                        try:
                            res = requests.post(FORM_RESPONSE_URL, data=payload, headers=headers, timeout=10)
                            if res.status_code in (200, 302):
                                succes_antal += 1
                            else:
                                fejl_antal += 1
                                sidste_fejl = f"HTTP status {res.status_code}"
                        except Exception as e:
                            fejl_antal += 1
                            sidste_fejl = str(e)

                if fejl_antal == 0:
                    st.session_state.malinger = []
                    st.session_state.rute_aktiv = False
                    st.session_state.klar_til_indsendelse = False
                    st.session_state.valgt_sorensen = False
                    st.session_state.valgt_forsendelse = False
                    st.session_state.pluk_trin = 1
                    st.session_state.transport_trykket = False
                    st.session_state.emballage_trykket = False
                    st.session_state.berta_transport_trykket = False
                    st.session_state.bekraeft_send = False
                    st.success("Målingen er nu indsendt og gemt i dit Google Sheet!")
                    st.rerun()
                else:
                    st.error(f"Der opstod fejl ved indsendelse af {fejl_antal} linjer. Årsag: {sidste_fejl}")
                    st.session_state.bekraeft_send = False
        with c_nej:
            if st.button("Nej", use_container_width=True):
                st.session_state.bekraeft_send = False
                st.rerun()
else:
    st.info("Ingen aktive registreringer endnu. Indtast initialer og tryk 'Start plukrute'.")
