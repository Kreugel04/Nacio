# app.py
import streamlit as st
import time
from models.nation import Nation
from core.ai_handler import AIHandler
from systems.stat_extractor import apply_ai_stats
from systems.events import trigger_historical_event
import json
import os
import pandas as pd

# --- HELPER FUNCTIONS ---
def save_game(nation, turn, messages):
    """Saves the current nation state and chat history to a JSON file."""
    if not os.path.exists("saves"):
        os.makedirs("saves")
    
    filename = f"saves/{nation.save_name}.json"
    save_data = {
        "turn_number": turn,
        "nation": nation.to_dict(),
        "messages": messages # <--- NOW SAVES YOUR CHAT HISTORY!
    }
    with open(filename, "w") as f:
        json.dump(save_data, f, indent=4)
    return filename

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nacio: A Global Symphony", layout="wide")

# --- CUSTOM CSS FOR STICKY HEADER ---
st.markdown("""
    <style>
        .main .block-container,
        div[data-testid="stVerticalBlock"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stElementContainer"],
        div[data-testid="stTabs"],
        div[data-baseweb="tabs"] { 
            overflow: visible !important;
            clip-path: none !important;
        }

        .main div[data-testid="stElementContainer"]:has(h1) {
            position: sticky !important;
            top: 2.875rem !important; 
            z-index: 1000 !important;
            background-color: #0E1117 !important;
            padding-bottom: 0.5rem !important;
        }
        
        .main div[role="tablist"] {
            position: sticky !important;
            top: 7.2rem !important; 
            z-index: 999 !important;
            background-color: #0E1117 !important;
            padding-top: 10px !important;
            padding-bottom: 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        div[data-testid="stChatInput"] {
            z-index: 1001 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE & ANTI-REFRESH LOGIC ---
if 'nation' not in st.session_state:
    st.session_state.nation = None
if 'turn' not in st.session_state:
    st.session_state.turn = 1
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'ai' not in st.session_state:
    st.session_state.ai = AIHandler()
if 'diplomacy_chat' not in st.session_state:
    st.session_state.diplomacy_chat = []

# --- ANTI-REFRESH RECOVERY ---
# If the session was wiped by a refresh, check the URL for an active game!
if st.session_state.nation is None and "session" in st.query_params:
    session_name = st.query_params["session"]
    save_file = f"saves/{session_name}.json"
    if os.path.exists(save_file):
        with open(save_file, "r") as f:
            data = json.load(f)
        st.session_state.nation = Nation.from_dict(data["nation"])
        st.session_state.turn = data["turn_number"]
        st.session_state.messages = data.get("messages", []) # Restore chat!
        st.session_state.nation.update_era()

# --- MAIN INTERFACE ---
# 1. MAIN MENU (NO NATION LOADED)
if st.session_state.nation is None:
    st.markdown("<h1 style='text-align: center;'>Nacio: A Global Symphony</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #888888; margin-bottom: 40px;'>Welcome, Supreme Leader. Select your era.</h4>", unsafe_allow_html=True)
    
    col_new, col_divider, col_load = st.columns([0.45, 0.1, 0.45])
    
    # --- NEW GAME MENU ---
    with col_new:
        st.subheader("✨ Forge a New Timeline")
        st.markdown("Enter the annals of history and guide your civilization.")
        country_input = st.text_input("Nation Name", value="Japan")
        year_input = st.number_input("Starting Year", value=1980, step=1)
        
        if st.button("Initialize Simulation", type="primary", use_container_width=True):
            with st.spinner("Establishing chronological uplink..."):
                data = st.session_state.ai.generate_starting_nation(country_input, year_input)
                
                if isinstance(data, dict):
                    save_name = f"{country_input}_{year_input}".replace(" ", "_")
                    st.session_state.nation = Nation(
                        name=country_input, year=year_input, 
                        flag_emoji=data.get('flag_emoji', '🏳️'), 
                        population=data['population'], gdp=data['gdp'],
                        military_strength=data['military_strength'], 
                        political_stability=data['political_stability'],
                        industrialization_level=data.get('industrialization_level', 1), 
                        tech_level=data.get('tech_level', 1),
                        regional_neighbors=data.get('regional_neighbors', {}),
                        world_gdp=data.get('world_gdp', {}),
                        world_military=data.get('world_military', {}),
                        briefing=data['briefing'],
                        save_name=save_name
                    )
                    st.session_state.turn = int(year_input)
                    st.session_state.nation.update_era() 
                    st.session_state.nation.record_stats(st.session_state.turn)
                    st.session_state.messages = [{"role": "assistant", "content": f"**INITIAL CABINET REPORT:**\n\n{data['briefing']}"}]
                    
                    # Lock the session into the URL and Autosave!
                    st.query_params["session"] = save_name
                    save_game(st.session_state.nation, st.session_state.turn, st.session_state.messages)
                    st.rerun()
                    
                elif isinstance(data, str):
                    st.error(f"📡 **COMMUNICATIONS FAILURE:** {data}")
                else:
                    st.error("📡 **COMMUNICATIONS FAILURE:** The AI failed to generate a valid nation state.")

    # --- LOAD GAME MENU ---
    with col_load:
        st.subheader("📂 Access Data Archives")
        st.markdown("Resume command of an existing timeline.")
        if not os.path.exists("saves"):
            st.info("No archives found. Start a new timeline to save your progress.")
        else:
            save_files = [f for f in os.listdir("saves") if f.endswith('.json')]
            if not save_files:
                st.info("Archive directory is empty.")
            else:
                for file in save_files:
                    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                    with c1: 
                        st.caption(file.replace(".json", ""))
                    with c2:
                        if st.button("📂", key=f"load_{file}", help="Load timeline"):
                            with open(f"saves/{file}", "r") as f:
                                data = json.load(f)
                            st.session_state.nation = Nation.from_dict(data["nation"])
                            st.session_state.turn = data["turn_number"]
                            st.session_state.messages = data.get("messages", [])
                            st.session_state.nation.update_era()
                            
                            # Lock the loaded session into the URL!
                            st.query_params["session"] = file.replace(".json", "")
                            st.rerun()
                    with c3:
                        if st.button("🗑️", key=f"del_{file}", help="Delete timeline"):
                            os.remove(f"saves/{file}")
                            st.toast(f"Deleted {file}")
                            st.rerun()

# 2. MAIN INTERFACE (GAME ACTIVE)
else:
    # --- THE CABINET OFFICE SIDEBAR ---
    with st.sidebar:
        st.title("🏛️ Cabinet Office")
        n = st.session_state.nation
        
        hex_code = "-".join(f"{ord(c):x}" for c in n.flag_emoji)
        twemoji_url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{hex_code}.png"
        
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="{twemoji_url}" style="height: 7rem; filter: drop-shadow(0px 6px 8px rgba(0,0,0,0.4));" alt="{n.flag_emoji}">
            </div>
        """, unsafe_allow_html=True)
        
        st.metric("Nation", n.name)
        st.metric("Year", st.session_state.turn)
        
        st.markdown(f"### 🏛️ Era: {n.nation_era}")
        st.divider()
        
        st.subheader("Core Statistics")
        st.write(f"👥 **Population:** {n.population:,}")
        st.write(f"💰 **GDP:** ${n.gdp:,.2f}B")
        st.write(f"💵 **GDP Per Capita:** ${n.gdp_per_capita:,.0f}")
        st.write(f"🏦 **Treasury:** ${n.treasury:,.2f}B")
        
        st.divider()
        st.subheader("Development Levels")
        st.progress(n.tech_level / 5.0, text=f"🔬 Tech Level: {n.tech_level} / 5")
        st.progress(n.industrialization_level / 5.0, text=f"🏭 Ind. Level: {n.industrialization_level} / 5")
        st.divider()
        
        st.progress(n.political_stability / 100, text=f"⚖️ Stability: {n.political_stability}%")
        st.progress(n.public_approval / 100, text=f"📢 Approval: {n.public_approval}%")

        st.divider()
        st.subheader("🌍 Global Rankings")
        
        live_gdp_rankings = n.world_gdp.copy()
        live_gdp_rankings[n.name] = n.gdp
        
        live_military_rankings = n.world_military.copy()
        live_military_rankings[n.name] = n.military_strength
        
        sorted_gdp = sorted(live_gdp_rankings.items(), key=lambda x: x[1], reverse=True)
        sorted_mil = sorted(live_military_rankings.items(), key=lambda x: x[1], reverse=True)
        
        rank_tab1, rank_tab2 = st.tabs(["💰 Top Economies", "⚔️ Top Militaries"])
        
        with rank_tab1:
            df_gdp = pd.DataFrame(sorted_gdp, columns=["Nation", "GDP ($B)"])
            df_gdp.index = df_gdp.index + 1 
            def highlight_player(s):
                return ['background-color: #2e8b57' if s['Nation'] == n.name else '' for v in s]
            st.dataframe(df_gdp.style.apply(highlight_player, axis=1), use_container_width=True)
            
        with rank_tab2:
            df_mil = pd.DataFrame(sorted_mil, columns=["Nation", "Power Score"])
            df_mil.index = df_mil.index + 1
            st.dataframe(df_mil.style.apply(highlight_player, axis=1), use_container_width=True)
        
        st.divider()
        st.subheader("Data Archives")
        
        if st.button("💾 Manual Save", use_container_width=True):
            save_game(st.session_state.nation, st.session_state.turn, st.session_state.messages)
            st.success("Progress archived.")

        with st.expander("📂 Manage Saved Timelines"):
            if not os.path.exists("saves"):
                st.write("No archives found.")
            else:
                save_files = [f for f in os.listdir("saves") if f.endswith('.json')]
                if not save_files:
                    st.write("Archive directory is empty.")
                else:
                    for file in save_files:
                        col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
                        with col1:
                            st.caption(file.replace(".json", ""))
                        with col2:
                            if st.button("📂", key=f"load_side_{file}"):
                                with open(f"saves/{file}", "r") as f:
                                    data = json.load(f)
                                st.session_state.nation = Nation.from_dict(data["nation"])
                                st.session_state.turn = data["turn_number"]
                                st.session_state.messages = data.get("messages", [])
                                st.query_params["session"] = file.replace(".json", "")
                                st.rerun()
                        with col3:
                            if st.button("🗑️", key=f"del_side_{file}"):
                                os.remove(f"saves/{file}")
                                st.rerun()
                                
        st.divider()
        if st.button("🚪 Resign & Return to Main Menu", type="secondary", use_container_width=True):
            # Wipe the memory AND clear the URL!
            st.session_state.nation = None
            st.session_state.turn = 1
            st.session_state.messages = []
            st.session_state.diplomacy_chat = []
            st.query_params.clear() 
            st.rerun()

    # --- THE MAIN TABS ---
    tab1, tab2, tab3 = st.tabs(["💬 Command Center", "📊 National Analytics", "🌍 Foreign Affairs"])

    # --- TAB 1: THE AI CHAT ---
    with tab1:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if st.button("🔔 End Turn"):
            event = trigger_historical_event(st.session_state.nation, st.session_state.turn, st.session_state.ai)
            if event:
                st.session_state.messages.append({"role": "assistant", "content": f"### GLOBAL EVENT: {st.session_state.turn}\n{event}"})
            
            st.session_state.turn += 1
            st.session_state.nation.process_turn()
            st.session_state.nation.record_stats(st.session_state.turn)
            
            # AUTOSAVE AT THE END OF THE TURN!
            save_game(st.session_state.nation, st.session_state.turn, st.session_state.messages)
            st.rerun()

    if prompt := st.chat_input("What is your next directive?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with tab1:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing geopolitical implications..."):
                    response = st.session_state.ai.parse_directive(prompt, st.session_state.nation, st.session_state.turn)
                    st.markdown(response)
                    apply_ai_stats(st.session_state.nation, response)
                    st.session_state.nation.add_event(st.session_state.turn, prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # AUTOSAVE AFTER PASSING A LAW!
                    save_game(st.session_state.nation, st.session_state.turn, st.session_state.messages)
        st.rerun()

    # --- TAB 2: DATA VISUALIZATION ---
    with tab2:
        st.subheader(f"Historical Trajectory of {st.session_state.nation.name}")
        
        if hasattr(st.session_state.nation, 'stat_history') and st.session_state.nation.stat_history:
            df = pd.DataFrame(st.session_state.nation.stat_history)
            df.set_index("Year", inplace=True)

            colA, colB = st.columns(2)
            with colA:
                st.markdown("**Economic Indicators**")
                st.line_chart(df[["GDP ($B)", "Treasury ($B)"]])
            with colB:
                st.markdown("**National Stability**")
                st.line_chart(df[["Stability (%)", "Approval (%)"]])

            st.markdown("**Population Growth**")
            st.line_chart(df[["Population"]], color="#FF4B4B")
        else:
            st.info("Pass your first turn to begin tracking national analytics.")
    
    # --- TAB 3: FOREIGN AFFAIRS & INTELLIGENCE ---
    with tab3:
        st.subheader("Global Operations Dashboard")
        st.markdown("Initiate direct diplomatic channels, launch covert operations, or mobilize armed forces.")
        
        # Merge Neighbors and Global targets into one list
        available_targets = list(st.session_state.nation.world_gdp.keys())
        if hasattr(st.session_state.nation, 'regional_neighbors'):
            for neighbor in st.session_state.nation.regional_neighbors.keys():
                if neighbor not in available_targets:
                    available_targets.insert(0, neighbor) # Put neighbors at the top of the list!
                    
        if not available_targets:
            available_targets = ["United States", "China", "Russia"] 
            
        target_nation = st.selectbox("Select Target Nation:", available_targets)
        
        action_type = st.radio("Select Operation Type:", ["🤝 Diplomatic Negotiation", "🕵️ Covert Espionage", "⚔️ Military Campaign"], horizontal=True)
        st.divider()

        # --- MILITARY CAMPAIGN UI ---
        if action_type == "⚔️ Military Campaign":
            st.markdown(f"**Target:** {target_nation}")
            st.warning("⚠️ **WARNING:** Declaring war will severely drain your treasury and risk massive instability if defeated.")
            
            st.info(f"🛡️ **Your True Combat Power (Modified by Era & Tech):** {st.session_state.nation.combat_power:,.0f}")
            
            target_base_strength = getattr(st.session_state.nation, 'regional_neighbors', {}).get(target_nation, 
                                   st.session_state.nation.world_military.get(target_nation, 200.0))
            
            st.write(f"📡 **Estimated Enemy Base Strength:** {target_base_strength}")
            
            force_commitment = st.slider("Percentage of Armed Forces to Deploy:", min_value=10, max_value=100, value=50, step=10)
            
            if st.button("⚔️ Declare War", type="primary"):
                with st.spinner(f"Mobilizing forces against {target_nation}..."):
                    war_results = st.session_state.nation.execute_war(target_nation, target_base_strength, force_commitment)
                    
                    # Passing the CURRENT TURN to prevent future dating!
                    report = st.session_state.ai.generate_war_report(
                        st.session_state.nation.name, 
                        target_nation, 
                        war_results,
                        st.session_state.turn
                    )
                    
                    if war_results['result'] == "VICTORY":
                        st.success(f"### 🏆 DECISIVE VICTORY\n{report}")
                        if hasattr(st.session_state.nation, 'regional_neighbors') and target_nation in st.session_state.nation.regional_neighbors:
                            del st.session_state.nation.regional_neighbors[target_nation]
                    else:
                        st.error(f"### 💀 CRUSHING DEFEAT\n{report}")
                    
                    log_msg = f"### ⚔️ WAR REPORT: {target_nation}\n{report}"
                    st.session_state.messages.append({"role": "assistant", "content": log_msg})
                    st.session_state.nation.add_event(st.session_state.turn, f"Waged war against {target_nation}. Result: {war_results['result']}")
                    
                    # AUTOSAVE THE WAR OUTCOME
                    save_game(st.session_state.nation, st.session_state.turn, st.session_state.messages)
                    
        # --- COVERT ESPIONAGE UI ---
        elif action_type == "🕵️ Covert Espionage":
            st.markdown(f"**Target:** {target_nation}")
            op_details = st.text_area("Operation Directives (e.g., Sabotage infrastructure, steal military blueprints):")
            
            if st.button("Execute Operation Blacklight", type="primary"):
                if op_details:
                    with st.spinner(f"Transmitting orders to field operatives in {target_nation}..."):
                        report = st.session_state.ai.run_espionage(st.session_state.nation, target_nation, op_details, st.session_state.turn)
                        st.error(f"### TOP SECRET: INTELLIGENCE BRIEFING\n{report}")
                        
                        log_msg = f"### 🕵️ OPERATION REPORT: {target_nation}\n{report}"
                        st.session_state.messages.append({"role": "assistant", "content": log_msg})
                        st.session_state.nation.add_event(st.session_state.turn, f"[CLASSIFIED] Op against {target_nation}: {op_details}")
                        save_game(st.session_state.nation, st.session_state.turn, st.session_state.messages)
                else:
                    st.warning("Please provide operation directives before executing.")

        # --- DIPLOMATIC NEGOTIATION UI ---
        elif action_type == "🤝 Diplomatic Negotiation":
            st.markdown(f"**Direct Secure Channel:** {target_nation}")
            
            diplomatic_message = st.text_area(f"Message to the {target_nation} Delegate:")
            
            if st.button("Send Diplomatic Cable"):
                if diplomatic_message:
                    with st.spinner(f"Awaiting response from {target_nation}..."):
                        delegate_response = st.session_state.ai.negotiate(
                            st.session_state.nation.name, 
                            target_nation, 
                            diplomatic_message, 
                            st.session_state.diplomacy_chat
                        )
                        
                        st.session_state.diplomacy_chat.append(("Supreme Leader", diplomatic_message))
                        st.session_state.diplomacy_chat.append((f"{target_nation} Delegate", delegate_response))
                        
                        st.success(f"**{target_nation} Delegate:**\n\n{delegate_response}")
                        
                        st.session_state.messages.append({"role": "user", "content": f"**[Diplomatic Cable to {target_nation}]:** {diplomatic_message}"})
                        st.session_state.messages.append({"role": "assistant", "content": f"**[{target_nation} Delegate]:** {delegate_response}"})
                        st.session_state.nation.add_event(st.session_state.turn, f"Diplomatic exchange with {target_nation}.")
                        save_game(st.session_state.nation, st.session_state.turn, st.session_state.messages)
                else:
                    st.warning("Cannot send an empty cable.")