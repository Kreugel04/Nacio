Nacio: A Global Symphony
Nacio is a sophisticated, AI-driven geopolitical simulator built with Python and Streamlit. It leverages the power of Google's Gemini LLM to create a dynamic, turn-based strategy experience where players lead a nation through historical or custom eras.

🚀 Key Features
AI-Driven Cabinet Reports: Every turn, a generative AI "Cabinet" analyzes your directives and provides a narrative report on the geopolitical and economic consequences.

Dynamic World Rankings: Real-time leaderboards for Global GDP and Military Strength that shift based on both historical data and player performance.

National Analytics Dashboard: Interactive line charts powered by Pandas and Streamlit to track your nation's GDP growth, Treasury levels, and Political Stability over time.

Multi-Timeline Save System: A custom-built CRUD (Create, Read, Update, Delete) archive manager that allows you to manage multiple branching "what-if" histories.

Historical Realism: Initial game states are grounded in real-world data from the chosen starting year (e.g., the Philippines in the year 2000).

🛠️ Tech Stack
Frontend: Streamlit (Python-based web framework)

AI Engine: Google Gemini API (2.5 Flash / 1.5 Flash)

Data Processing: Pandas & NumPy

Version Control: Git & GitHub

📦 Installation & Setup
To run Nacio locally, follow these steps:

Clone the repository:

Bash
git clone https://github.com/Kreugel04/Nacio.git
cd Nacio
Set up a Virtual Environment:

Bash
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate
Install Dependencies:

Bash
pip install -r requirements.txt
Configure API Keys:
Create a .env file in the root directory and add your Google AI Studio API Key:

Plaintext
GEMINI_API_KEY=your_actual_key_here
Launch the Game:

Bash
streamlit run app.py
📈 Future Roadmap
Diplomacy & Trade: Implementing a system to negotiate treaties and trade deals with other nations.

Intelligence & Espionage: A dedicated module for covert operations and gathering intel on global rivals.

Military Conflict Engine: A tactical simulation for managing international tensions and defense.