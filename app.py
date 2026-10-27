import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from zoneinfo import ZoneInfo
import uuid

st.set_page_config(page_title="Carl Ras - TDABC Plukmåling", layout="centered")

# CSS to force 3 columns on mobile and hide Streamlit UI elements
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
    
    div.block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* TVING 3 KOLONNER PÅ MOBIL / TELEFON (INGEN VERTIKAL STACKING) */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        width: 100% !important;
    }
    div[data-testid="column"], div[data-testid="stColumn"] {
        width: 32% !important;
        flex: 1 1 32% !important;
        min-width: 0 !important;
    }
    div[data-testid="column"] button, div[data-testid="stColumn"] button {
        width: 100% !important;
        min-height: 58px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
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
if 'rute_id' not in st.session_state:
    st.session_state.rute_id = ""
if 'berta_valgt' not in st.session_state:
    st.session_state.berta_valgt = "Nej"
if 'berta_transport_trykket' not in st.session_state:
    st.session_state.berta_transport_trykket = False
if 'palle_type' not in st.session_state:
    st.session_state.palle_type = "Helpalle pluk"
if 'stafet_aktiv' not in st.session_state:
    st.session_state.stafet_aktiv = False
if 'ordrenr_val' not in st.session_state:
    st.session_state.ordrenr_val = ""
if 'gemt_stregkode' not in st.session_state:
    st.session_state.gemt_stregkode = "-"
if 'stamdata_trin' not in st.session_state:
    st.session_state.stamdata_trin = 1

def get_dansk_tid():
    return datetime.now(ZoneInfo("Europe/Copenhagen"))

# Callbacks to manage numpad state cleanly without keyboard popup
def add_digit(digit):
    st.session_state.ordrenr_val += str(digit)

def delete_digit():
    if len(st.session_state.ordrenr_val) > 0:
        st.session_state.ordrenr_val = st.session_state.ordrenr_val[:-1]

def confirm_ordrenr():
    if st.session_state.ordrenr_val.strip():
        st.session_state.gemt_stregkode = st.session_state.ordrenr_val.strip()
    else:
        st.session_state.gemt_stregkode = "-"
    st.session_state.stamdata_trin = 3

# 1. Stamdata (vises KUN når ruten endnu IKKE er aktiv)
if not st.session_state.rute_aktiv and not st.session_state.klar_til_indsendelse:
    
    # Trin 1: Initialer
    if st.session_state.stamdata_trin == 1:
        st.subheader("1. Indtast dine initialer")
        initialer_input = st.text_input(
            "Dine initialer *", 
            value=st.session_state.get('saved_initialer', ''), 
            placeholder="f.eks. MHA",
            key="initialer_input_field"
        ).strip()
        
        if st.button("Næste (Ordrenummer) ->", type="primary", use_container_width=True):
            if initialer_input:
                st.session_state.saved_initialer = initialer_input
                st.session_state.stamdata_trin = 2
                st.rerun()
            else:
                st.warning("Indtast venligst dine initialer for at fortsætte.")

    # Trin 2: Ordrenummer (Touch Numpad 3x3)
    elif st.session_state.stamdata_trin == 2:
        st.subheader("1. Indtast ordrenummer")
        st.caption(f"Initialer: {st.session_state.get('saved_initialer', '')}")

        # Viste display-boks (forhindrer at mobil-tastaturet popper op)
        visnings_tekst = st.session_state.ordrenr_val if st.session_state.ordrenr_val else "Indtast ordrenummer..."
        tekst_farve = "#111111" if st.session_state.ordrenr_val else "#888888"
        
        display_html = f"""
        <div style="
            background-color: #f8f9fa;
            border: 2px solid #0066cc;
            border-radius: 8px;
            padding: 12px;
            font-size: 26px;
            font-weight: bold;
            text-align: center;
            letter-spacing: 2px;
            color: {tekst_farve};
            margin-bottom: 12px;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        ">
            {visnings_tekst}
        </div>
        """
        st.markdown(display_html, unsafe_allow_html=True)
        
        # Touch Numpad Matrix (3x3 + 0 + X + Enter)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("1", use_container_width=True, key="btn_1", on_click=add_digit, args=(1,))
        with col2:
            st.button("2", use_container_width=True, key="btn_2", on_click=add_digit, args=(2,))
        with col3:
            st.button("3", use_container_width=True, key="btn_3", on_click=add_digit, args=(3,))

        col4, col5, col6 = st.columns(3)
        with col4:
            st.button("4", use_container_width=True, key="btn_4", on_click=add_digit, args=(4,))
        with col5:
            st.button("5", use_container_width=True, key="btn_5", on_click=add_digit, args=(5,))
        with col6:
            st.button("6", use_container_width=True, key="btn_6", on_click=add_digit, args=(6,))

        col7, col8, col9 = st.columns(3)
        with col7:
            st.button("7", use_container_width=True, key="btn_7", on_click=add_digit, args=(7,))
        with col8:
            st.button("8", use_container_width=True, key="btn_8", on_click=add_digit, args=(8,))
        with col9:
            st.button("9", use_container_width=True, key="btn_9", on_click=add_digit, args=(9,))

        col0, col_del, col_ok = st.columns(3)
        with col0:
            st.button("0", use_container_width=True, key="btn_0", on_click=add_digit, args=(0,))
        with col_del:
            st.button("X (Slet)", use_container_width=True, key="btn_del", on_click=delete_digit)
        with col_ok:
            st.button("Enter / OK", type="primary", use_container_width=True, key="btn_ok", on_click=confirm_ordrenr)

        with st.expander("Indtast med laserscanner / pc-tastatur"):
            man_input = st.text_input("Ordrenummer manuelt:", value=st.session_state.ordrenr_val, key="man_input_field")
            if man_input != st.session_state.ordrenr_val:
                st.session_state.ordrenr_val = man_input

    # Trin 3: Pluktype og Start Plukrute
    elif st.session_state.stamdata_trin == 3:
        st.subheader("1. Vælg pluktype")
        st.info(f"**Initialer:** {st.session_state.get('saved_initialer', '')} | **Ordrenr:** {st.session_state.get('gemt_stregkode', '-')}")

        hoved_pluktype = st.selectbox(
            "Vælg pluktype *",
            ["Kassepluk", "Pallepluk", "Længde pluk", "Buffer pluk", "Lynpluk"]
        )
        st.session_state.valgt_hoved_pluktype = hoved_pluktype

        if hoved_pluktype == "Kassepluk":
            antal_kassepluk = st.number_input("Antal pluk på ruten", min_value=1, max_value=100, value=1, step=1)
            st.session_state.endelig_pluktype = f"Kassepluk ({antal_kassepluk} pluk på rute)"
        else:
            st.session_state.endelig_pluktype = hoved_pluktype

        st.divider()

        if st.button("Start plukrute", type="primary", use_container_width=True):
            st.session_state.rute_id = f"R-{get_dansk_tid().strftime('%H%M%S')}-{uuid.uuid4().hex[:3].upper()}"
            st.session_state.rute_aktiv = True
            st.session_state.klar_til_indsendelse = False
            st.session_state.pluk_trin = 1
            st.session_state.transport_trykket = False
            st.session_state.emballage_trykket = False
            st.session_state.valgt_sorensen = False
            st.session_state.valgt_forsendelse = False
            st.session_state.bekraeft_send = False
            st.session_state.berta_valgt = "Nej"
            st.session_state.berta_transport_trykket = False
            st.session_state.stafet_aktiv = False

            nu = get_dansk_tid()
            st.session_state.malinger.append({
                'Dato': nu.strftime('%Y-%m-%d'),
                'Tidspunkt': nu.strftime('%H:%M:%S'),
                'Initialer': st.session_state.get('saved_initialer', 'Ukendt'),
                'Pluktype': st.session_state.endelig_pluktype,
                'Handling': "Start plukrute",
                'Ekstra_Info': f"Rute-ID: {st.session_state.rute_id} | Stregkode: {st.session_state.get('gemt_stregkode', '-')}"
            })
            st.rerun()

elif st.session_state.klar_til_indsendelse:
    st.info("Ruten er afsluttet! Rul ned til '3. Indsend data' for at gemme målingen.")

# Funktion til at gemme tidsstempler
def gem_stempel(handling, ekstra_info=""):
    nu = get_dansk_tid()
    init = st.session_state.get('saved_initialer', 'Ukendt')
    pluk_t = st.session_state.get('endelig_pluktype', 'Standard')
    stregk = st.session_state.get('gemt_stregkode', '-')
    
    info_tekst = f"Rute-ID: {st.session_state.rute_id} | Stregkode: {stregk}"
    if ekstra_info:
        info_tekst += f" | {ekstra_info}"
        
    st.session_state.malinger.append({
        'Dato': nu.strftime('%Y-%m-%d'),
        'Tidspunkt': nu.strftime('%H:%M:%S'),
        'Initialer': init,
        'Pluktype': pluk_t,
        'Handling': handling,
        'Ekstra_Info': info_tekst
    })

# 2. Registrering af faser (Vis kun hvis ruten er aktiv)
if st.session_state.rute_aktiv:
    st.subheader("2. Registrer faser på ruten")
    
    hoved_p = st.session_state.get('valgt_hoved_pluktype', '')

    if hoved_p == "Pallepluk":
        st.write("**Palletype valgt på ruten:**")
        ptype = st.radio("Vælg palletype *", ["Helpalle pluk", "Halv pallepluk"], horizontal=True, key="palle_radio")
        if ptype != st.session_state.palle_type:
            st.session_state.palle_type = ptype
            st.session_state.endelig_pluktype = f"Pallepluk ({ptype})"

    if hoved_p == "Buffer pluk":
        st.write("**Brug af Berta:**")
        berta_opt = st.radio("Brug af Berta *", ["Nej", "Ja"], horizontal=True, key="berta_radio")
        st.session_state.berta_valgt = berta_opt
        
        if berta_opt == "Ja":
            berta_type = "primary" if st.session_state.berta_transport_trykket else "secondary"
            if st.button("Ankommet til Berta", type=berta_type, use_container_width=True):
                st.session_state.berta_transport_trykket = True
                gem_stempel("Ankommet til Berta")
                st.rerun()
    else:
        if not st.session_state.emballage_trykket:
            emb_type = "secondary"
            if st.button("Afslut emballage pålægning", type=emb_type, use_container_width=True):
                st.session_state.emballage_trykket = True
                gem_stempel("Afslut emballage pålægning")
                st.rerun()

    st.divider()

    if not st.session_state.valgt_sorensen and not st.session_state.valgt_forsendelse:
        st.info("Husk Stafet Pluk Regel: Tryk først på 'Ankommet til lokation', når du fysisk står ved plukpladsen!")

        trin = st.session_state.pluk_trin
        st.write(f"**Aktuel plukplads: Nr. {trin} (af maks 100)**")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            trans_type = "primary" if st.session_state.transport_trykket else "secondary"
            if st.button(f"Ankommet til lokation (Pluk {trin})", type=trans_type, use_container_width=True):
                st.session_state.transport_trykket = True
                gem_stempel(f"Ankommet til lokation (Pluk {trin})")
                st.rerun()

        with col_t2:
            if st.button(f"Afslut pluk {trin}", use_container_width=True):
                gem_stempel(f"Afslut pluk {trin}")
                st.session_state.transport_trykket = False
                if st.session_state.pluk_trin < 100:
                    st.session_state.pluk_trin += 1
                st.rerun()

        st.write("---")
        st.caption("Konsolideringsreol / Stafetpluk:")
        stafet_label = "Afslut Stafet Pluk (Konsolideringsreol)" if st.session_state.stafet_aktiv else "Start Stafet Pluk (Konsolideringsreol)"
        stafet_btn_type = "primary" if st.session_state.stafet_aktiv else "secondary"
        if st.button(stafet_label, type=stafet_btn_type, use_container_width=True):
            st.session_state.stafet_aktiv = not st.session_state.stafet_aktiv
            handling_navn = "Start Stafet Pluk (Konsolideringsreol)" if st.session_state.stafet_aktiv else "Afslut Stafet Pluk (Konsolideringsreol)"
            gem_stempel(handling_navn)
            st.rerun()

        st.divider()

    st.subheader("Afslutning af rute")

    with st.expander("Tilføj bemærkning / fejl på rute"):
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

    if st.session_state.valgt_sorensen or st.session_state.valgt_forsendelse:
        overskrift = "Sørensen (Forsendelse)" if st.session_state.valgt_sorensen else "Forsendelsesproces"
        st.divider()
        st.write(f"**Viderelevering Krav: {overskrift}**")

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
            gem_stempel(f"Tillægstjenester ({overskrift})", ekstra_info=info_str)
            st.success("Tillægstjenester registreret!")
            st.rerun()

    st.divider()
    if st.button("Afslut plukordre", type="primary", use_container_width=True):
        gem_stempel("Afslut plukordre")
        st.session_state.rute_aktiv = False
        st.session_state.klar_til_indsendelse = True
        st.session_state.valgt_sorensen = False
        st.session_state.valgt_forsendelse = False
        st.session_state.stamdata_trin = 1
        st.session_state.ordrenr_val = ""
        st.rerun()

st.divider()

# 3. Indsend data
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
                    st.session_state.bekraeft_send = False
                    st.session_state.stamdata_trin = 1
                    st.session_state.ordrenr_val = ""
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
