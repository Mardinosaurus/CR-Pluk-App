import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from zoneinfo import ZoneInfo
import uuid
import os
import shutil
import streamlit.components.v1 as components

st.set_page_config(page_title="Carl Ras - TDABC Plukmåling", layout="centered")

# Skjul Streamlit UI elementer
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
if 'gemt_stregkode' not in st.session_state:
    st.session_state.gemt_stregkode = "-"

# Opret automatisk scanner component mappe og HTML fil hvis den mangler
component_dir = os.path.join(os.path.dirname(__file__), 'scanner_component')
os.makedirs(component_dir, exist_ok=True)
index_path = os.path.join(component_dir, 'index.html')

html_component_code = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.4.0/dist/streamlit-component-lib.js"></script>
    <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background: transparent; }
        .scanner-box { border: 1px solid #d0d7de; border-radius: 8px; padding: 12px; background: #ffffff; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .input-field { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #bbb; border-radius: 6px; box-sizing: border-box; margin-top: 8px; font-family: inherit; }
        .cam-btn { background-color: #0066cc; color: white; border: none; padding: 12px 16px; font-size: 15px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: 600; margin-bottom: 4px; transition: background 0.2s; }
        .cam-btn:hover { background-color: #0052a3; }
        .cam-btn.active { background-color: #cc0000; }
        #reader { width: 100%; max-width: 380px; margin: 10px auto; border-radius: 8px; overflow: hidden; display: none; }
        .status-msg { margin-top: 8px; font-size: 14px; color: #28a745; font-weight: 600; }
        .label-text { font-size: 14px; font-weight: 600; text-align: left; margin-bottom: 6px; color: #333; display: block; }
    </style>
</head>
<body>
    <div class="scanner-box">
        <span class="label-text">Stregkode / Ordrenummer:</span>
        <button id="cam-btn" class="cam-btn" onclick="toggleCamera()">Start Live Kamerascanner</button>
        <div id="reader"></div>
        <input type="text" id="barcode-input" class="input-field" placeholder="Scan med kamerascan, laserscanner eller indtast..." oninput="onManualInput(this.value)" />
        <div id="status" class="status-msg"></div>
    </div>

    <script>
        let html5QrCode = null;
        let isCameraOn = false;

        function updateHeight() {
            Streamlit.setFrameHeight(document.body.scrollHeight + 15);
        }

        function sendToStreamlit(value) {
            Streamlit.setComponentValue(value);
            document.getElementById('barcode-input').value = value;
            document.getElementById('status').innerText = value ? "Aflæst stregkode: " + value : "";
            updateHeight();
        }

        function onManualInput(val) {
            Streamlit.setComponentValue(val.trim());
            document.getElementById('status').innerText = val.trim() ? "Indtastet kode: " + val.trim() : "";
            updateHeight();
        }

        function toggleCamera() {
            const btn = document.getElementById('cam-btn');
            const readerDiv = document.getElementById('reader');

            if (!isCameraOn) {
                readerDiv.style.display = 'block';
                btn.innerText = 'Stop Kamerascanner';
                btn.classList.add('active');
                updateHeight();

                html5QrCode = new Html5Qrcode("reader");
                const config = { fps: 10, qrbox: { width: 250, height: 150 } };

                html5QrCode.start(
                    { facingMode: "environment" },
                    config,
                    (decodedText, decodedResult) => {
                        sendToStreamlit(decodedText);
                        
                        try {
                            let ctx = new (window.AudioContext || window.webkitAudioContext)();
                            let osc = ctx.createOscillator();
                            osc.type = "sine";
                            osc.frequency.value = 800;
                            osc.connect(ctx.destination);
                            osc.start();
                            setTimeout(() => osc.stop(), 150);
                        } catch(e) {}

                        html5QrCode.stop().then(() => {
                            readerDiv.style.display = 'none';
                            btn.innerText = 'Start Live Kamerascanner';
                            btn.classList.remove('active');
                            isCameraOn = false;
                            updateHeight();
                        }).catch(() => {});
                    },
                    (errorMessage) => {}
                ).catch(err => {
                    alert("Kameratilladelse afvist eller bagkamera ikke fundet: " + err);
                    readerDiv.style.display = 'none';
                    btn.innerText = 'Start Live Kamerascanner';
                    btn.classList.remove('active');
                    isCameraOn = false;
                    updateHeight();
                });

                isCameraOn = true;
            } else {
                if (html5QrCode) {
                    html5QrCode.stop().then(() => {
                        readerDiv.style.display = 'none';
                        btn.innerText = 'Start Live Kamerascanner';
                        btn.classList.remove('active');
                        isCameraOn = false;
                        updateHeight();
                    }).catch(() => {});
                }
            }
        }

        Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, function(event) {
            updateHeight();
            if (event.detail && event.detail.args) {
                const defVal = event.detail.args.default_value;
                if (!document.getElementById('barcode-input').value && defVal && defVal !== '-') {
                    document.getElementById('barcode-input').value = defVal;
                }
            }
        });
        Streamlit.init();
    </script>
</body>
</html>"""

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(html_component_code)

barcode_scanner_comp = components.declare_component('barcode_scanner_comp', path=component_dir)

# Helper for dansk lokal tid
def get_dansk_tid():
    return datetime.now(ZoneInfo("Europe/Copenhagen"))

# 1. Stamdata (vises KUN når ruten endnu IKKE er aktiv)
if not st.session_state.rute_aktiv and not st.session_state.klar_til_indsendelse:
    st.subheader("1. Før du starter ruten")

    initialer = st.text_input("Dine initialer *", value=st.session_state.get('saved_initialer', ''), placeholder="f.eks. MHA").strip()
    if initialer:
        st.session_state.saved_initialer = initialer

    # Brug den integrerede scanner-komponent
    scannet_val = barcode_scanner_comp(default_value=st.session_state.get('gemt_stregkode', '-'), key="live_barcode_scanner")
    
    if scannet_val is not None and str(scannet_val).strip() != '':
        st.session_state.gemt_stregkode = str(scannet_val).strip()
    elif 'gemt_stregkode' not in st.session_state:
        st.session_state.gemt_stregkode = "-"

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
    kan_starte = len(initialer) > 0

    if not len(initialer) > 0:
        st.warning("Indtast dine initialer ovenfor for at starte ruten.")
    else:
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
                'Initialer': initialer,
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
