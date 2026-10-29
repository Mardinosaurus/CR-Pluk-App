import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from zoneinfo import ZoneInfo
import uuid
import json
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Carl Ras - TDABC Plukmåling", layout="centered")

# Hide Streamlit UI elements
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
    
    div.block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    button, div[data-testid="stButton"] button {
        white-space: normal !important;
        word-wrap: break-word !important;
        word-break: normal !important;
        text-overflow: clip !important;
        line-height: 1.25 !important;
        height: auto !important;
        min-height: 48px !important;
        padding: 10px 8px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }

    button p, button div, button span {
        white-space: normal !important;
        word-wrap: break-word !important;
        text-overflow: clip !important;
        line-height: 1.25 !important;
        font-size: inherit !important;
    }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("Carl Ras - Plukmåling (TDABC)")
st.caption("Registrer tidsstempler for plukruter på lageret.")

ZONE_SEQUENCE = ["Alpha", "Beta", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet"]

# Helper for Danish local time
def get_dansk_tid():
    return datetime.now(ZoneInfo("Europe/Copenhagen"))

# Persistent State Management Functions
def save_persistent_state():
    r_id = st.session_state.get('rute_id', '')
    if r_id:
        data = {
            "saved_initialer": st.session_state.get('saved_initialer', ''),
            "scanned_orders": st.session_state.get('scanned_orders', []),
            "gemt_stregkode": st.session_state.get('gemt_stregkode', '-'),
            "rute_id": r_id,
            "rute_aktiv": st.session_state.get('rute_aktiv', False),
            "klar_til_indsendelse": st.session_state.get('klar_til_indsendelse', False),
            "pluk_trin": st.session_state.get('pluk_trin', 1),
            "malinger": st.session_state.get('malinger', []),
            "transport_trykket": st.session_state.get('transport_trykket', False),
            "scanned_loc_current": st.session_state.get('scanned_loc_current', ''),
            "emballage_trykket": st.session_state.get('emballage_trykket', False),
            "valgt_sorensen": st.session_state.get('valgt_sorensen', False),
            "valgt_forsendelse": st.session_state.get('valgt_forsendelse', False),
            "endelig_pluktype": st.session_state.get('endelig_pluktype', ''),
            "valgt_hoved_pluktype": st.session_state.get('valgt_hoved_pluktype', ''),
            "stamdata_trin": st.session_state.get('stamdata_trin', 1)
        }
        filepath = f"/tmp/rute_state_{r_id}.json"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

def load_persistent_state(r_id):
    filepath = f"/tmp/rute_state_{r_id}.json"
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, val in data.items():
                st.session_state[key] = val
            return True
        except Exception:
            pass
    return False

def clear_persistent_state():
    r_id = st.session_state.get('rute_id', '')
    if r_id:
        filepath = f"/tmp/rute_state_{r_id}.json"
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

# Restore state from query param if available
query_rute = st.query_params.get("rute", "")
if query_rute and not st.session_state.get('rute_id'):
    load_persistent_state(query_rute)

# Session state defaults
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
if 'scanned_loc_current' not in st.session_state:
    st.session_state.scanned_loc_current = ""
if 'emballage_trykket' not in st.session_state:
    st.session_state.emballage_trykket = False
if 'rute_id' not in st.session_state:
    st.session_state.rute_id = ""
if 'berta_valgt' not in st.session_state:
    st.session_state.berta_valgt = "Nej"
if 'berta_transport_trykket' not in st.session_state:
    st.session_state.berta_transport_trykket = False
if 'scanned_orders' not in st.session_state:
    st.session_state.scanned_orders = [] # List of {"zone": "Alpha", "code": "030684132"}
if 'gemt_stregkode' not in st.session_state:
    st.session_state.gemt_stregkode = "-"
if 'stamdata_trin' not in st.session_state:
    st.session_state.stamdata_trin = 1
if 'scan_input_key' not in st.session_state:
    st.session_state.scan_input_key = 0
if 'loc_input_key' not in st.session_state:
    st.session_state.loc_input_key = 0

# Sync HTML localStorage with Streamlit query param for rock-solid reload protection
active_r_id = st.session_state.get('rute_id', '')
js_sync_code = f"""
<script>
    const activeRouteId = "{active_r_id}";
    if (activeRouteId) {{
        localStorage.setItem('cr_tdabc_active_rute', activeRouteId);
    }} else {{
        const savedRoute = localStorage.getItem('cr_tdabc_active_rute');
        const urlParams = new URLSearchParams(window.location.search);
        if (savedRoute && !urlParams.has('rute')) {{
            window.location.search = '?rute=' + savedRoute;
        }}
    }}
</script>
"""
components.html(js_sync_code, height=0)

# Callbacks for scanning order / box IDs
def on_scan_submitted():
    key_name = f"scan_field_{st.session_state.scan_input_key}"
    scanned_text = st.session_state.get(key_name, "").strip()
    if scanned_text:
        next_idx = len(st.session_state.scanned_orders)
        zone_label = ZONE_SEQUENCE[next_idx] if next_idx < len(ZONE_SEQUENCE) else f"Zone {next_idx + 1}"
        st.session_state.scanned_orders.append({"zone": zone_label, "code": scanned_text})
        st.session_state.scan_input_key += 1  # Resets input field cleanly
        save_persistent_state()

def remove_scanned_order(idx):
    if 0 <= idx < len(st.session_state.scanned_orders):
        st.session_state.scanned_orders.pop(idx)
        # Re-index remaining zones (Alpha, Beta, Charlie...)
        for i in range(len(st.session_state.scanned_orders)):
            st.session_state.scanned_orders[i]["zone"] = ZONE_SEQUENCE[i] if i < len(ZONE_SEQUENCE) else f"Zone {i + 1}"
        save_persistent_state()

def confirm_all_scans():
    if st.session_state.scanned_orders:
        formatted_list = [f"{item['zone']}: {item['code']}" for item in st.session_state.scanned_orders]
        st.session_state.gemt_stregkode = ", ".join(formatted_list)
    else:
        st.session_state.gemt_stregkode = "-"
    st.session_state.stamdata_trin = 3
    save_persistent_state()

# Callback for scanning location/shelf barcode
def on_location_scanned():
    key_name = f"loc_field_{st.session_state.loc_input_key}"
    scanned_loc = st.session_state.get(key_name, "").strip()
    trin = st.session_state.get('pluk_trin', 1)
    
    ekstra = f"Lokation: {scanned_loc}" if scanned_loc else "Lokation registreret"
    gem_stempel(f"Scan lokation (Pluk {trin})", lokation=scanned_loc if scanned_loc else "Registreret")
    st.session_state.scanned_loc_current = scanned_loc if scanned_loc else "Registreret"
    st.session_state.transport_trykket = True
    st.session_state.loc_input_key += 1
    save_persistent_state()

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
                save_persistent_state()
                st.rerun()
            else:
                st.warning("Indtast venligst dine initialer for at fortsætte.")

    # Trin 2: Automatic Auto-sequence Scanner Input (Alpha -> Beta -> Charlie -> Delta)
    elif st.session_state.stamdata_trin == 2:
        st.subheader("1. Scan Boks ID med scanner")
        st.caption(f"Initialer: {st.session_state.get('saved_initialer', '')}")

        next_idx = len(st.session_state.scanned_orders)
        next_label = ZONE_SEQUENCE[next_idx] if next_idx < len(ZONE_SEQUENCE) else f"Zone {next_idx + 1}"

        st.info(f"Klar til næste scan: **{next_label}**")

        current_key = f"scan_field_{st.session_state.scan_input_key}"
        st.text_input(
            "Tryk For Ny Boks ID",
            key=current_key,
            placeholder=f"Tryk her for at scanne Boks ID for {next_label}...",
            on_change=on_scan_submitted
        )

        # Vis scannede ordrer (NYESTE ØVERST)
        if st.session_state.scanned_orders:
            st.write("**Scannede Boks ID'er på ruten (nyeste øverst):**")
            reversed_orders = list(enumerate(st.session_state.scanned_orders))[::-1]
            for real_idx, item in reversed_orders:
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.success(f"**{item['zone']}**: `{item['code']}`")
                with col_btn:
                    if st.button("Slet", key=f"del_scan_{real_idx}", use_container_width=True):
                        remove_scanned_order(real_idx)
                        st.rerun()

        st.divider()
        btn_label = "Færdig med at scanne ordrer ->" if st.session_state.scanned_orders else "Fortsæt uden ordrenummer ->"
        if st.button(btn_label, type="primary", use_container_width=True):
            confirm_all_scans()
            st.rerun()

    # Trin 3: Pluktype og Start Plukrute
    elif st.session_state.stamdata_trin == 3:
        st.subheader("1. Vælg pluktype")
        st.info(f"**Initialer:** {st.session_state.get('saved_initialer', '')} | **Ordre/Zoner:** {st.session_state.get('gemt_stregkode', '-')}")

        hoved_pluktype = st.selectbox(
            "Vælg pluktype *",
            ["Kassepluk", "Pallepluk", "Længde pluk", "Buffer pluk", "Lynpluk"]
        )
        st.session_state.valgt_hoved_pluktype = hoved_pluktype
        st.session_state.endelig_pluktype = hoved_pluktype

        st.divider()

        if st.button("Start plukrute", type="primary", use_container_width=True):
            r_id = f"R-{get_dansk_tid().strftime('%H%M%S')}-{uuid.uuid4().hex[:3].upper()}"
            st.session_state.rute_id = r_id
            st.query_params["rute"] = r_id
            st.session_state.rute_aktiv = True
            st.session_state.klar_til_indsendelse = False
            st.session_state.pluk_trin = 1
            st.session_state.transport_trykket = False
            st.session_state.scanned_loc_current = ""
            st.session_state.emballage_trykket = False
            st.session_state.valgt_sorensen = False
            st.session_state.valgt_forsendelse = False
            st.session_state.bekraeft_send = False
            st.session_state.berta_valgt = "Nej"
            st.session_state.berta_transport_trykket = False

            nu = get_dansk_tid()
            st.session_state.malinger.append({
                'Dato': nu.strftime('%Y-%m-%d'),
                'Tidspunkt': nu.strftime('%H:%M:%S'),
                'Initialer': st.session_state.get('saved_initialer', ''),
                'Pluktype': st.session_state.endelig_pluktype,
                'Handling': "Start plukrute",
                'Ekstra_Info': f"Rute-ID: {st.session_state.rute_id} | Ordre/Zoner: {st.session_state.get('gemt_stregkode', '-')}"
            })
            save_persistent_state()
            st.rerun()

elif st.session_state.klar_til_indsendelse:
    st.info("Ruten er afsluttet! Rul ned til '3. Indsend data' for at gemme målingen.")

# Funktion til at gemme tidsstempler
def gem_stempel(handling, lokation="", bemaerkning="", ekstra_info=""):
    nu = get_dansk_tid()
    init = st.session_state.get('saved_initialer', 'Ukendt')
    pluk_t = st.session_state.get('endelig_pluktype', 'Standard')
    r_id = st.session_state.get('rute_id', '-')
    ordre_z = st.session_state.get('gemt_stregkode', '-')
    
    # Combined string for backward compatibility / single column fallback
    info_tekst = f"Rute-ID: {r_id} | Ordre/Zoner: {ordre_z}"
    if lokation:
        info_tekst += f" | Lokation: {lokation}"
    if bemaerkning:
        info_tekst += f" | Bemærkning: {bemaerkning}"
    if ekstra_info:
        info_tekst += f" | {ekstra_info}"
        
    st.session_state.malinger.append({
        'Dato': nu.strftime('%Y-%m-%d'),
        'Tidspunkt': nu.strftime('%H:%M:%S'),
        'Initialer': init,
        'Pluktype': pluk_t,
        'Handling': handling,
        'Rute_ID': r_id,
        'Ordre_Zoner': ordre_z,
        'Lokation': lokation if lokation else '-',
        'Bemaerkning': bemaerkning if bemaerkning else '-',
        'Ekstra_Info': info_tekst
    })
    save_persistent_state()

# 2. Registrering af faser (Vis kun hvis ruten er aktiv)
if st.session_state.rute_aktiv:
    st.subheader("2. Registrer faser på ruten")
    
    hoved_p = st.session_state.get('valgt_hoved_pluktype', '')

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
        trin = st.session_state.pluk_trin
        st.write(f"**Aktuel plukplads: Nr. {trin} (af maks 100)**")
        
        if not st.session_state.transport_trykket:
            loc_key = f"loc_field_{st.session_state.loc_input_key}"
            st.text_input(
                f"Scan lokation (Pluk {trin}):",
                key=loc_key,
                placeholder=f"Tryk her og scan hyldelokation for pluk {trin}...",
                on_change=on_location_scanned
            )
            
            # Fallback knap hvis man vil registrere uden stregkode
            if st.button(f"Registrer ankomst til lokation (Pluk {trin}) uden scan", use_container_width=True):
                gem_stempel(f"Scan lokation (Pluk {trin})", lokation="Registreret manuelt")
                st.session_state.scanned_loc_current = "Registreret manuelt"
                st.session_state.transport_trykket = True
                save_persistent_state()
                st.rerun()
        else:
            loc_disp = st.session_state.get('scanned_loc_current', '')
            info_str = f"Lokation registrerede: **{loc_disp}**" if loc_disp else "Lokation registrerede"
            st.success(info_str)
            
            if st.button(f"Afslut pluk {trin}", type="primary", use_container_width=True):
                gem_stempel(f"Afslut pluk {trin}")
                st.session_state.transport_trykket = False
                st.session_state.scanned_loc_current = ""
                if st.session_state.pluk_trin < 100:
                    st.session_state.pluk_trin += 1
                save_persistent_state()
                st.rerun()

        st.divider()

    st.subheader("Afslutning af rute")

    with st.expander("Tilføj bemærkning / fejl på rute"):
        bemaerkning_input = st.text_input("Beskrivelse af fejl eller afvigelse:", key="bemaerkning_input_field", placeholder="f.eks. manglende vare, beskadiget emballage")
        if st.button("Gem bemærkning"):
            if bemaerkning_input.strip():
                gem_stempel("Fejl / Bemærkning", bemaerkning=bemaerkning_input.strip())
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
        save_persistent_state()
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
                        # Build payload with individual columns or fallback to Ekstra_Info
                        payload = {
                            'entry.1109742049': str(row.get('Dato', '')),
                            'entry.785756491': str(row.get('Tidspunkt', '')),
                            'entry.1387317177': str(row.get('Initialer', '')),
                            'entry.1597480740': str(row.get('Pluktype', '')),
                            'entry.2111546458': str(row.get('Handling', '')),
                            'entry.1581018160': str(row.get('Rute_ID', '-')) or '-'
                        }
                        
                        # Support for separate Google Form entry IDs if provided in st.session_state or environment
                        if st.session_state.get('entry_ordre_zoner'):
                            payload[st.session_state.get('entry_ordre_zoner')] = str(row.get('Ordre_Zoner', '-'))
                        if st.session_state.get('entry_lokation'):
                            payload[st.session_state.get('entry_lokation')] = str(row.get('Lokation', '-'))
                        if st.session_state.get('entry_bemaerkning'):
                            payload[st.session_state.get('entry_bemaerkning')] = str(row.get('Bemaerkning', '-'))
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
                    clear_persistent_state()
                    st.query_params.clear()
                    st.session_state.malinger = []
                    st.session_state.rute_aktiv = False
                    st.session_state.klar_til_indsendelse = False
                    st.session_state.valgt_sorensen = False
                    st.session_state.valgt_forsendelse = False
                    st.session_state.pluk_trin = 1
                    st.session_state.transport_trykket = False
                    st.session_state.scanned_loc_current = ""
                    st.session_state.emballage_trykket = False
                    st.session_state.bekraeft_send = False
                    st.session_state.stamdata_trin = 1
                    st.session_state.scanned_orders = []
                    st.session_state.rute_id = ""
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
