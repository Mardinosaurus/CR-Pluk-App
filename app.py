```
import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import urllib.parse

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
if 'transport_trykket' not in st.session_state:
    st.session_state.transport_trykket = False

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
kan_starte = len(initialer) &gt; 0

if not kan_starte:
    st.warning("Indtast dine initialer ovenfor for at starte ruten.")

# 2. Registrering af faser
st.subheader("2. Registrer faser på ruten")

def gem_stempel(handling, ekstra_info=""):
    nu = datetime.now()
    st.session_state.malinger.append({
        'Dato': nu.strftime('%Y-%m-%d'),
        'Tidspunkt': nu.strftime('%H:%M:%S'),
        'Initialer': initialer,
        'Pluktype': endelig_pluktype,
        'Handling': handling,
        'Ekstra_Info': ekstra_info
    })

if not st.session_state.rute_aktiv:
    if st.button("Start plukrute", disabled=not kan_starte, type="primary", use_container_width=True):
        st.session_state.rute_aktiv = True
        st.session_state.pluk_trin = 1
        st.session_state.transport_trykket = False
        st.session_state.valgt_sorensen = False
        st.session_state.bekraeft_send = False
        gem_stempel("Start plukrute")
        st.rerun()
else:
    st.info(f"Aktiv rute: {initialer} | {endelig_pluktype}")

    if st.button("Afslut emballage pålægning", use_container_width=True):
        gem_stempel("Afslut emballage pålægning")

    st.divider()

    # Kompakt plukplads modul (1 til 10)
    trin = st.session_state.pluk_trin
    st.write(f"**Aktuel plukplads: Nr. {trin} (af maks 10)**")
    
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
            if st.session_state.pluk_trin &lt; 10:
                st.session_state.pluk_trin += 1
            st.rerun()

    st.divider()

    st.subheader("Afslutning af rute")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        if st.button("Afsat til Sørensen", use_container_width=True):
            gem_stempel("Afsat til Sørensen")
            st.session_state.valgt_sorensen = True
            st.rerun()

    with col_f2:
        if st.button("Afslut pluk", use_container_width=True):
            gem_stempel("Afslut pluk")
            st.session_state.rute_aktiv = False
            st.rerun()

    if st.session_state.valgt_sorensen:
        st.divider()
        st.write("**Viderelevering Krav: Sørensen (Forsendelse)**")

        har_fg = st.checkbox("Farlig gods")
        ant_fg = st.number_input("Antal farlig gods", min_value=0, value=1 if har_fg else 0) if har_fg else 0

        har_ft = st.checkbox("Festool registrering")
        ant_ft = st.number_input("Antal Festool registreringer", min_value=0, value=1 if har_ft else 0) if har_ft else 0

        har_srv = st.checkbox("Service")
        ant_srv = st.number_input("Antal service", min_value=0, value=1 if har_srv else 0) if har_srv else 0

        if st.button("Gem tillægstjenester og afslut rute", type="primary", use_container_width=True):
            tillaeg = []
            if har_fg and ant_fg &gt; 0:
                tillaeg.append(f"Farlig gods: {ant_fg}")
            if har_ft and ant_ft &gt; 0:
                tillaeg.append(f"Festool: {ant_ft}")
            if har_srv and ant_srv &gt; 0:
                tillaeg.append(f"Service: {ant_srv}")

            info_str = ", ".join(tillaeg) if tillaeg else "Ingen tillæg"
            gem_stempel("Tillægstjenester v. Sørensen", ekstra_info=info_str)
            st.session_state.valgt_sorensen = False
            st.session_state.rute_aktiv = False
            st.rerun()

st.divider()

if st.session_state.malinger:
    df_aktiv = pd.DataFrame(st.session_state.malinger)
    
    # Skjult expander til tabel og rettelsesknapper
    with st.expander("Vis registreringer (Ret / Nulstil)"):
        st.dataframe(df_aktiv, use_container_width=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Angre seneste tryk", use_container_width=True):
                st.session_state.malinger.pop()
                if st.session_state.pluk_trin &gt; 1:
                    st.session_state.pluk_trin -= 1
                st.session_state.transport_trykket = False
                st.rerun()
        with col_b:
            if st.button("Nulstil rute", use_container_width=True):
                st.session_state.malinger = []
                st.session_state.rute_aktiv = False
                st.session_state.valgt_sorensen = False
                st.session_state.pluk_trin = 1
                st.session_state.transport_trykket = False
                st.session_state.bekraeft_send = False
                st.rerun()

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
                for row in st.session_state.malinger:
                    try:
                        data_payload = urllib.parse.urlencode({
                            'entry.1109742049': row.get('Dato', ''),
                            'entry.785756491': row.get('Tidspunkt', ''),
                            'entry.1387317177': row.get('Initialer', ''),
                            'entry.1597480740': row.get('Pluktype', ''),
                            'entry.2111546458': row.get('Handling', ''),
                            'entry.1581018160': row.get('Ekstra_Info', '')
                        }).encode('utf-8')
                        
                        req = urllib.request.Request(FORM_RESPONSE_URL, data=data_payload)
                        urllib.request.urlopen(req)
                    except Exception as e:
                        fejl_antal += 1

                st.session_state.malinger = []
                st.session_state.rute_aktiv = False
                st.session_state.valgt_sorensen = False
                st.session_state.pluk_trin = 1
                st.session_state.transport_trykket = False
                st.session_state.bekraeft_send = False
                st.success("Målingen er nu indsendt og gemt i dit Google Sheet!")
                st.rerun()
        with c_nej:
            if st.button("Nej", use_container_width=True):
                st.session_state.bekraeft_send = False
                st.rerun()
else:
    st.info("Ingen aktive registreringer endnu. Indtast initialer og tryk 'Start plukrute'.")

```

1. Tryk på **Cmd + S** (Gem filen).

---

### Løsning B: Alternativ direkte terminal-kommando (Mac)

Hvis du hellere vil køre en ren terminal-kommando i Mac-terminalen uden om udklipsholderfejl, kan du køre dette direkte:

```
cat &lt;&lt; 'EOF' &gt; app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import urllib.parse

st.set_page_config(page_title="Carl Ras - TDABC Plukmåling", layout="centered")

st.title("Carl Ras - Plukmåling (TDABC)")
st.caption("Registrer tidsstempler for plukruter på lageret.")

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
if 'transport_trykket' not in st.session_state:
    st.session_state.transport_trykket = False

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
kan_starte = len(initialer) &gt; 0

if not kan_starte:
    st.warning("Indtast dine initialer ovenfor for at starte ruten.")

st.subheader("2. Registrer faser på ruten")

def gem_stempel(handling, ekstra_info=""):
    nu = datetime.now()
    st.session_state.malinger.append({
        'Dato': nu.strftime('%Y-%m-%d'),
        'Tidspunkt': nu.strftime('%H:%M:%S'),
        'Initialer': initialer,
        'Pluktype': endelig_pluktype,
        'Handling': handling,
        'Ekstra_Info': ekstra_info
    })

if not st.session_state.rute_aktiv:
    if st.button("Start plukrute", disabled=not kan_starte, type="primary", use_container_width=True):
        st.session_state.rute_aktiv = True
        st.session_state.pluk_trin = 1
        st.session_state.transport_trykket = False
        st.session_state.valgt_sorensen = False
        st.session_state.bekraeft_send = False
        gem_stempel("Start plukrute")
        st.rerun()
else:
    st.info(f"Aktiv rute: {initialer} | {endelig_pluktype}")

    if st.button("Afslut emballage pålægning", use_container_width=True):
        gem_stempel("Afslut emballage pålægning")

    st.divider()

    trin = st.session_state.pluk_trin
    st.write(f"**Aktuel plukplads: Nr. {trin} (af maks 10)**")
    
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
            if st.session_state.pluk_trin &lt; 10:
                st.session_state.pluk_trin += 1
            st.rerun()

    st.divider()

    st.subheader("Afslutning af rute")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        if st.button("Afsat til Sørensen", use_container_width=True):
            gem_stempel("Afsat til Sørensen")
            st.session_state.valgt_sorensen = True
            st.rerun()

    with col_f2:
        if st.button("Afslut pluk", use_container_width=True):
            gem_stempel("Afslut pluk")
            st.session_state.rute_aktiv = False
            st.rerun()

    if st.session_state.valgt_sorensen:
        st.divider()
        st.write("**Viderelevering Krav: Sørensen (Forsendelse)**")

        har_fg = st.checkbox("Farlig gods")
        ant_fg = st.number_input("Antal farlig gods", min_value=0, value=1 if har_fg else 0) if har_fg else 0

        har_ft = st.checkbox("Festool registrering")
        ant_ft = st.number_input("Antal Festool registreringer", min_value=0, value=1 if har_ft else 0) if har_ft else 0

        har_srv = st.checkbox("Service")
        ant_srv = st.number_input("Antal service", min_value=0, value=1 if har_srv else 0) if har_srv else 0

        if st.button("Gem tillægstjenester og afslut rute", type="primary", use_container_width=True):
            tillaeg = []
            if har_fg and ant_fg &gt; 0:
                tillaeg.append(f"Farlig gods: {ant_fg}")
            if har_ft and ant_ft &gt; 0:
                tillaeg.append(f"Festool: {ant_ft}")
            if har_srv and ant_srv &gt; 0:
                tillaeg.append(f"Service: {ant_srv}")

            info_str = ", ".join(tillaeg) if tillaeg else "Ingen tillæg"
            gem_stempel("Tillægstjenester v. Sørensen", ekstra_info=info_str)
            st.session_state.valgt_sorensen = False
            st.session_state.rute_aktiv = False
            st.rerun()

st.divider()

if st.session_state.malinger:
    df_aktiv = pd.DataFrame(st.session_state.malinger)
    
    with st.expander("Vis registreringer (Ret / Nulstil)"):
        st.dataframe(df_aktiv, use_container_width=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Angre seneste tryk", use_container_width=True):
                st.session_state.malinger.pop()
                if st.session_state.pluk_trin &gt; 1:
                    st.session_state.pluk_trin -= 1
                st.session_state.transport_trykket = False
                st.rerun()
        with col_b:
            if st.button("Nulstil rute", use_container_width=True):
                st.session_state.malinger = []
                st.session_state.rute_aktiv = False
                st.session_state.valgt_sorensen = False
                st.session_state.pluk_trin = 1
                st.session_state.transport_trykket = False
                st.session_state.bekraeft_send = False
                st.rerun()

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
                for row in st.session_state.malinger:
                    try:
                        data_payload = urllib.parse.urlencode({
                            'entry.1109742049': row.get('Dato', ''),
                            'entry.785756491': row.get('Tidspunkt', ''),
                            'entry.1387317177': row.get('Initialer', ''),
                            'entry.1597480740': row.get('Pluktype', ''),
                            'entry.2111546458': row.get('Handling', ''),
                            'entry.1581018160': row.get('Ekstra_Info', '')
                        }).encode('utf-8')
                        
                        req = urllib.request.Request(FORM_RESPONSE_URL, data=data_payload)
                        urllib.request.urlopen(req)
                    except Exception as e:
                        fejl_antal += 1

                st.session_state.malinger = []
                st.session_state.rute_aktiv = False
                st.session_state.valgt_sorensen = False
                st.session_state.pluk_trin = 1
                st.session_state.transport_trykket = False
                st.session_state.bekraeft_send = False
                st.success("Målingen er nu indsendt og gemt i dit Google Sheet!")
                st.rerun()
        with c_nej:
            if st.button("Nej", use_container_width=True):
                st.session_state.bekraeft_send = False
                st.rerun()
else:
    st.info("Ingen aktive registreringer endnu. Indtast initialer og tryk 'Start plukrute'.")
EOF
