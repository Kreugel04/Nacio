@echo off
cd /d "C:\Dev Files\Nacio"
call venv\Scripts\activate
streamlit run app.py --server.headless true