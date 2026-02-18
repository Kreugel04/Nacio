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
def save_game(nation, turn):
    """Saves the current nation state to a JSON file."""
    if not os.path.exists("saves"):
        os.makedirs("saves")
    
    filename = f"saves/{nation.save_name}.json"
    save_data = {
        "turn_number": turn,
        "nation": nation.to_dict()
    }
    with open(filename, "w") as f:
        json.dump(save_data, f, indent=4)
    return filename

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nacio: A Global Symphony", layout="wide")

# --- CUSTOM CSS FOR STICKY HEADER ---
st.markdown("""
    <style>
        /* 1. Remove all hidden overflows from Streamlit's entire nested layout tree */
        .main .block-container,
        div[data-testid="stVerticalBlock"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stElementContainer"],
        div[data-testid="stTabs"],
        div[data-baseweb="tabs"] { 
            overflow: visible !important;
            clip-path: none !important;
        }

        /* 2. Pin the MAIN Title (The '.main' addition ignores the sidebar!) */
        .main div[data-testid="stElementContainer"]:has(h1) {
            position: sticky !important;
            top: 2.875rem !important; 
            z-index: 1000 !important;
            background-color: #0E1117 !important;
            padding-bottom: 0.5rem !important;
        }
        
        /* 3. Pin the Tab Menu */
        .main div[role="tablist"] {
            position: sticky !important;
            top: 7.2rem !important; 
            z-index: 999 !important;
            background-color: #0E1117 !important;
            padding-top: 10px !important;
            padding-bottom: 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* 4. Ensure Chat Input stays above scrolling text */
        div[data-testid="stChatInput"] {
            z-index: 1001 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if 'nation' not in st.session_state:
    st.session_state.nation = None
if 'turn' not in st.session_state:
    st.session_state.turn = 1
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'ai' not in st.session_state:
    st.session_state.ai = AIHandler()

# --- SIDEBAR: NATIONAL STATISTICS & SAVE/LOAD ---
with st.sidebar:
    st.title("🏛️ Cabinet Office")
    if st.session_state.nation:
        n = st.session_state.nation
        st.metric("Nation", n.name)
        st.metric("Year", st.session_state.turn)
        st.divider()
        
        st.subheader("Core Statistics")
        st.write(f"👥 **Population:** {n.population:,}")
        st.write(f"💰 **GDP:** ${n.gdp:,.2f}B")
        st.write(f"🏦 **Treasury:** ${n.treasury:,.2f}B")
        st.progress(n.political_stability / 100, text=f"⚖️ Stability: {n.political_stability}%")
        st.progress(n.public_approval / 100, text=f"📢 Approval: {n.public_approval}%")

        # --- NEW: DYNAMIC GLOBAL RANKINGS ---
        st.divider()
        st.subheader("🌍 Global Rankings")
        
        # Inject the player's live stats into the global dictionary
        live_gdp_rankings = n.world_gdp.copy()
        live_gdp_rankings[n.name] = n.gdp
        
        live_military_rankings = n.world_military.copy()
        live_military_rankings[n.name] = n.military_strength
        
        # Sort both dictionaries from highest to lowest
        sorted_gdp = sorted(live_gdp_rankings.items(), key=lambda x: x[1], reverse=True)
        sorted_mil = sorted(live_military_rankings.items(), key=lambda x: x[1], reverse=True)
        
        # Create tabs so the sidebar isn't too long
        rank_tab1, rank_tab2 = st.tabs(["💰 Top Economies", "⚔️ Top Militaries"])
        
        with rank_tab1:
            # Format as a clean dataframe
            df_gdp = pd.DataFrame(sorted_gdp, columns=["Nation", "GDP ($B)"])
            df_gdp.index = df_gdp.index + 1 # Start rank at 1 instead of 0
            
            # Highlight the player's nation in the dataframe using Pandas Styler
            def highlight_player(s):
                return ['background-color: #2e8b57' if s['Nation'] == n.name else '' for v in s]
            
            st.dataframe(df_gdp.style.apply(highlight_player, axis=1), use_container_width=True)
            
        with rank_tab2:
            df_mil = pd.DataFrame(sorted_mil, columns=["Nation", "Power Score"])
            df_mil.index = df_mil.index + 1
            st.dataframe(df_mil.style.apply(highlight_player, axis=1), use_container_width=True)
        
        # --- ENHANCED DATA ARCHIVES ---
        st.divider()
        st.subheader("Data Archives")
        
        # 1. Quick Save (Current Game)
        if st.button("💾 Quick Save Current"):
            save_game(st.session_state.nation, st.session_state.turn)
            st.success("Progress archived.")

        # 2. Archive Manager (Load & Delete)
        with st.expander("📂 Manage Saved Timelines", expanded=True):
            if not os.path.exists("saves"):
                st.write("No archives found.")
            else:
                save_files = [f for f in os.listdir("saves") if f.endswith('.json')]
                if not save_files:
                    st.write("Archive directory is empty.")
                else:
                    for file in save_files:
                        # Create three columns: Name, Load Button, Delete Button
                        col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
                        
                        with col1:
                            st.caption(file.replace(".json", ""))
                        
                        with col2:
                            if st.button("📂", key=f"load_{file}", help="Load this timeline"):
                                with open(f"saves/{file}", "r") as f:
                                    data = json.load(f)
                                st.session_state.nation = Nation.from_dict(data["nation"])
                                st.session_state.turn = data["turn_number"]
                                st.session_state.messages = [] 
                                st.rerun()
                                
                        with col3:
                            if st.button("🗑️", key=f"del_{file}", help="Delete this timeline"):
                                os.remove(f"saves/{file}")
                                st.toast(f"Deleted {file}")
                                st.rerun() # Refresh the list immediately

# --- MAIN INTERFACE ---
st.title("Nacio: A Global Symphony")

# 1. HANDLE NATION INITIALIZATION
if st.session_state.nation is None:
    st.subheader("Welcome, Supreme Leader. Select your era.")
    col1, col2 = st.columns(2)
    with col1:
        country_input = st.text_input("Nation Name", value="Japan")
    with col2:
        year_input = st.number_input("Starting Year", value=1980)
    
    if st.button("Initialize Simulation"):
        data = st.session_state.ai.generate_starting_nation(country_input, year_input)
        if data:
            st.session_state.nation = Nation(
                name=country_input, year=year_input, 
                population=data['population'], gdp=data['gdp'],
                military_strength=data['military_strength'], 
                political_stability=data['political_stability'],
                world_gdp=data.get('world_gdp', {}),
                world_military=data.get('world_military', {}),
                briefing=data['briefing'],
                save_name=f"{country_input}_{year_input}".replace(" ", "_")
            )
            st.session_state.turn = int(year_input)
            st.session_state.nation.record_stats(st.session_state.turn)
            st.session_state.messages = [{"role": "assistant", "content": f"**INITIAL CABINET REPORT:**\n\n{data['briefing']}"}]
            st.rerun()

# 2. MAIN INTERFACE TABS
else:
    # Split the main screen into THREE distinct views
    tab1, tab2, tab3 = st.tabs(["💬 Command Center", "📊 National Analytics", "🌍 Foreign Affairs"])

    # --- TAB 1: THE AI CHAT ---
    with tab1:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # END TURN BUTTON - Safely inside Tab 1!
        if st.button("🔔 End Turn"):
            event = trigger_historical_event(st.session_state.nation, st.session_state.turn, st.session_state.ai)
            if event:
                st.session_state.messages.append({"role": "assistant", "content": f"### GLOBAL EVENT: {st.session_state.turn}\n{event}"})
            
            st.session_state.turn += 1
            st.session_state.nation.process_turn()
            
            # Record the new stats at the end of the year!
            st.session_state.nation.record_stats(st.session_state.turn)
            st.rerun()

    # CHAT INPUT - Safely OUTSIDE the tabs!
        if prompt := st.chat_input("What is your next directive?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing geopolitical implications..."):
                    response = st.session_state.ai.parse_directive(prompt, st.session_state.nation, st.session_state.turn)
                    st.markdown(response)
                    apply_ai_stats(st.session_state.nation, response)
                    st.session_state.nation.add_event(st.session_state.turn, prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    # --- TAB 2: DATA VISUALIZATION ---
    with tab2:
        st.subheader(f"Historical Trajectory of {st.session_state.nation.name}")
        
        # Check if history exists (prevents crashes on older saves)
        if hasattr(st.session_state.nation, 'stat_history') and st.session_state.nation.stat_history:
            # Convert dictionary into a Pandas DataFrame for Streamlit to read
            df = pd.DataFrame(st.session_state.nation.stat_history)
            df.set_index("Year", inplace=True)

            colA, colB = st.columns(2)
            with colA:
                st.markdown("**Economic Indicators**")
                # Grouping GDP and Treasury together on one chart
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
        st.markdown("Initiate direct diplomatic channels or launch classified covert operations.")
        
        # 1. Target Selection (Pulls dynamically from the generated world data!)
        available_targets = list(st.session_state.nation.world_gdp.keys())
        if not available_targets:
            available_targets = ["United States", "China", "Russia", "European Union"] # Fallback
            
        target_nation = st.selectbox("Select Target Nation:", available_targets)
        
        # 2. Action Type Selection
        action_type = st.radio("Select Operation Type:", ["🤝 Diplomatic Negotiation", "🕵️ Covert Espionage"], horizontal=True)
        st.divider()
        
        # --- COVERT ESPIONAGE UI ---
        if action_type == "🕵️ Covert Espionage":
            st.markdown(f"**Target:** {target_nation}")
            op_details = st.text_area("Operation Directives (e.g., Sabotage infrastructure, steal military blueprints):")
            
            if st.button("Execute Operation Blacklight", type="primary"):
                if op_details:
                    with st.spinner(f"Transmitting orders to field operatives in {target_nation}..."):
                        report = st.session_state.ai.run_espionage(st.session_state.nation, target_nation, op_details, st.session_state.turn)
                        
                        # Display the result in the tab
                        st.error(f"### TOP SECRET: INTELLIGENCE BRIEFING\n{report}")
                        
                        # Log it into the main chat timeline so the player has a record of it
                        log_msg = f"### 🕵️ OPERATION REPORT: {target_nation}\n{report}"
                        st.session_state.messages.append({"role": "assistant", "content": log_msg})
                        st.session_state.nation.add_event(st.session_state.turn, f"[CLASSIFIED] Op against {target_nation}: {op_details}")
                else:
                    st.warning("Please provide operation directives before executing.")

        # --- DIPLOMATIC NEGOTIATION UI ---
        elif action_type == "🤝 Diplomatic Negotiation":
            st.markdown(f"**Direct Secure Channel:** {target_nation}")
            
            # Use Streamlit session state to remember the ongoing conversation
            if 'diplomacy_chat' not in st.session_state:
                st.session_state.diplomacy_chat = []
                
            diplomatic_message = st.text_area(f"Message to the {target_nation} Delegate:")
            
            if st.button("Send Diplomatic Cable"):
                if diplomatic_message:
                    with st.spinner(f"Awaiting response from {target_nation}..."):
                        # Get AI response using the new method we just added
                        delegate_response = st.session_state.ai.negotiate(
                            st.session_state.nation.name, 
                            target_nation, 
                            diplomatic_message, 
                            st.session_state.diplomacy_chat
                        )
                        
                        # Save to our local temporary history
                        st.session_state.diplomacy_chat.append(("Supreme Leader", diplomatic_message))
                        st.session_state.diplomacy_chat.append((f"{target_nation} Delegate", delegate_response))
                        
                        # Show the response on screen
                        st.success(f"**{target_nation} Delegate:**\n\n{delegate_response}")
                        
                        # Log the exchange in the main Command Center chat
                        st.session_state.messages.append({"role": "user", "content": f"**[Diplomatic Cable to {target_nation}]:** {diplomatic_message}"})
                        st.session_state.messages.append({"role": "assistant", "content": f"**[{target_nation} Delegate]:** {delegate_response}"})
                        st.session_state.nation.add_event(st.session_state.turn, f"Diplomatic exchange with {target_nation}.")
                else:
                    st.warning("Cannot send an empty cable.")