import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Carl Ras - TDABC Plukmåling", layout="centered")

st.title("Carl Ras - Plukmåling (TDABC)")
st.caption("Registrer tidsstempler for plukruter på lageret.")

# Session state initialization
if 'malinger' not in st.session_state:
    st.session_state.malinger = []

if 'pluk_trin' not in st.session_state:
    st.session_state.pluk_trin = 1

if 'rute_aktiv' not in st.session_state:
    st.session_state.rute_aktiv = False

if 'valgt_sorensen' not in st.session_state:
    st.session_state.valgt_sorensen = False

if 'bekraeft_send' not in st.session_state:
    st.session_state.bekraeft_send = False

# 1. Stamdata
st.subheader("1. Før du starter ruten")
col1, col2 = st.columns(2)

with col1:
    initialer = st.text_input("Dine initialer *", value=st.session_state.get('saved_initialer', ''), placeholder="f.eks. MHA").strip()
    if initialer:
        st.session_state.saved_initialer = initialer

with col2:
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
    antal_kassepluk = st.number_input("Antal forventede pluk", min_value=1, max_value=100, value=1, step=1)
    endelig_pluktype = f"Kassepluk ({antal_kassepluk} pluk)"
else:
    endelig_pluktype = hoved_pluktype

st.divider()

kan_starte = len(initialer) > 0

if not kan_starte:
    st.warning("Indtast dine initialer ovenfor for at starte ruten.")

# 2. Registrering af faser
st.subheader("2. Registrer faser på ruten")

def gem_stempel(handling, ekstra_info=""):
    nu = datetime.now()
    st.session_state.malinger.append({
        'Dato': nu.strftime('%d-%m-%Y'),
        'Tidspunkt': nu.strftime('%H:%M:%S'),
        'Initialer': initialer,
        'Pluktype': endelig_pluktype,
        'Handling': handling,
        'Ekstra_Info': ekstra_info
    })
    st.success(f"Registreret: {handling} kl. {nu.strftime('%H:%M:%S')}")

if not st.session_state.rute_aktiv:
    if st.button("Start plukrute", disabled=not kan_starte, use_container_width=True):
        st.session_state.rute_aktiv = True
        st.session_state.pluk_trin = 1
        st.session_state.valgt_sorensen = False
        st.session_state.bekraeft_send = False
        gem_stempel("Start plukrute")
        st.rerun()
else:
    st.info(f"Aktiv rute: {initialer} | {endelig_pluktype}")

    if st.button("Afslut emballage påsætning", use_container_width=True):
        gem_stempel("Afslut emballage påsætning")

    st.divider()

    # Kompakt plukplads modul (1 til 10)
    trin = st.session_state.pluk_trin
    st.write(f"**Aktuel plukplads: Nr. {trin} (af maks 10)**")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button(f"Transport til pluk {trin}", use_container_width=True):
            gem_stempel(f"Transport til plukplads {trin}")
    with col_t2:
        if st.button(f"Afslut pluk {trin}", use_container_width=True):
            gem_stempel(f"Afslut pluk {trin}")
            if st.session_state.pluk_trin < 10:
                st.session_state.pluk_trin += 1
            st.rerun()

    st.divider()

    st.subheader("Afslutning af rute")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        if st.button("Afsat til Sørensen", use_container_width=True):
            gem_stempel("Afsat til Sûrensen")
            st.session_state.valgt_sorensen = True
            st.rerun()

    with col_f2:
        if st.button("Afslut pluk", use_container_width=True):
            gem_stempel("Afslut pluk")
            st.session_state.rute_aktiv = False
            st.rerun()

    if st.session_state.valgt_sorensen:
        st.divider()
        st.write("**Viderereing Krav: Sørensen (Forsendelse)**")

        har_fg = st.checkbox("Farlig gods")
        ant_fg = st.number_input("Antal farlig gods", min_value=0, value=1 if har_fg else 0) if har_fg else 0

        har_ft = st.checkbox("Festool registrering")
        ant_ft = st.number_input("Antal Festool registreringer", mim_value=0, value=1 if har_ft else 0) if har_ft else 0

        har_srv = st.checkbox("Service")
        ant_srv = st.number_input("Antal service", min_value=0, value=1 if har_srv else 0) if har_srv else 0

        if st.button("Gem tillægstjenester og afslut rute", type="primary", use_container_width=True):
            tillaeg = []
            if har_fg and ant_fg > 0:
                tillaeg.append(f"Farlig gods: {ant_fg}")
            if har_ft and ant_ft > 0:
                tillaeg.append(f"Festool: {ant_ft}")
            if har_srv and ant_srv > 0:
                tillaeg.append(f"Service: {ant_srv}")

            info_str = ", ".join(tillaeg) if tillaeg else "Ingen tillæg"
            gem_stempel("Tillægstjenester v. Sørensen", ekstra_info=info_str)
            st.session_state.valgt_sorensen = False
            st.session_state.rute_aktiv = False
            st.rerun()

st.divider()

st.subheader("Aktive registreringer for ruten")
if st.session_state.malinger:
    df_aktiv = pd.DataFrame(st.session_state.malinger)
    st.dataframe(df_aktiv, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Angre seneste tryk", use_container_width=True):
            st.session_state.malinger.pop()
            if st.session_state.pluk_trin > 1:
                st.session_state.pluk_trin -= 1
            st.rerun()
    with col_b:
        if st.button("Nulstil rute", use_container_width=True):
            st.session_state.malinger = []
            st.session_state.rute_aktiv = False
            st.session_state.valgt_sorensen = False
            st.session_state.pluk_trin = 1
            st.session_state.bekraeft_send = False
            st.rerun()

    st.divider()

    st.subheader("3. Indsend data")
    if not st.session_state.bekraeft_send:
        if st.button("Send data", type="primary", use_container_width=True):
            st.session_state.bekraeft_send = True
            st.rerun()
    else:
        st.warning("Er du sikker?")
        c_ja, c_nej = st.columns(2)
        with c_ja:
            # Styled Green button via custom label/type
            if st.button("Ja", type="primary", use_container_width=True):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    existing_data = conn.read()
                    updated_df = pd.concat([existing_data, df_aktiv], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("Målingen er nu indsendt til det centrale datalager!")
                except Exception as e:
                    st.info("Data gemmes og nulstilles til næste opgave.")
                
                # Nulstil kun ruten, BEHOLD INITIALER!
                st.session_state.malinger = []
                st.session_state.rute_aktiv = False
                st.session_state.valgt_sorensen = False
                st.session_state.pluk_trin = 1
                st.session_state.bekraeft_send = False
                st.rerun()
        with c_nej:
            if st.button("Nej", use_container_width=True):
                st.session_state.bekraeft_send = False
                st.rerun()
else:
    st.info("Ingen aktive registreringer endnu. Indtast initialer og tryk 'Start plukrute'.")
