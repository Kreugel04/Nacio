# Nacio: A Global Symphony (v2.1)
A Python-based, AI-driven Grand Strategy text simulator built with Streamlit.

## 🚀 Features (v2.1 Update)
* **Dynamic AI Storytelling:** Powered by the OpenRouter API (Aurora Alpha), acting as the game's simulation engine, historian, and foreign delegates.
* **Civilization Progression:** Guide your nation from the Stone Age to the Space Age. Upgrading your Tech (1-5) and Industrialization (1-5) levels dynamically shifts your era based on your GDP per Capita.
* **Deterministic Warfare Engine:** Deploy your armed forces in the Military Campaign tab. Combat is calculated cleanly in Python using tech, industry, and stability modifiers, while the AI generates thrilling, era-accurate After Action Reports based on the mathematical outcome.
* **Global & Regional Theaters:** Manage localized border disputes with `regional_neighbors` or monitor the dynamic top 10 Global Economies and Militaries leaderboards. 
* **State Persistence:** Never lose your game to a browser refresh. Nacio features continuous autosaving, chat history retention, and URL query parameter tracking for seamless resume-and-play.

## 🛠️ Installation & Setup
1. Clone the repository and navigate to the project folder.
2. Install the required dependencies:
   `pip install -r requirements.txt`
3. Create a `.env` file in the root directory and add your OpenRouter API key:
   `OPENROUTER_API_KEY=your_key_here`
4. Launch the Command Center:
   `streamlit run app.py`