# 📊 Self-Service BI Tool (Streamlit-Based)

A Self-Service Business Intelligence (BI) web app built using [Streamlit](https://streamlit.io/) that allows users to explore, filter, visualize, and analyze datasets without needing to write code.

---

## 🚀 Features

- 🧮 Connect and query databases (PostgreSQL, MySQL, etc.)
- 📂 Upload CSV/Excel files
- 🔎 Filter, sort, and transform data
- 📊 Generate visualizations: bar charts, line charts, pie charts, etc.
- 📥 Export data and reports (CSV, Excel, PNG)
- 🛡️ Role-based access for Admin and Users
- 📁 Session and cache management for large data

---

## 🛠️ Tech Stack

- **Frontend & Backend:** [Streamlit](https://streamlit.io/)
- **Data Sources:** CSV, Excel, PostgreSQL, MySQL, SQLite
- **Visualization:** Streamlit Charts, Plotly, Altair, Matplotlib
- **Authentication:** Streamlit-Auth (optional) / Custom login logic
- **Deployment:** Streamlit Cloud, Docker, Heroku, or EC2

---

## 📦 Installation

### 🧰 Prerequisites
- Python 3.8+
- pip or conda
- Git

### ⚙️ Setup Instructions

1. **Clone the repo**
   git clone https://github.com/lova420/Evolve_BI.git
   cd Evolve_BI

2. **Install dependencies**
   pip install -r requirements.txt

3. **Run the Streamlit app**
   python -m streamlit run streamlit_main.py
   
4. **Access the app**
   Open http://localhost:8501 in your browser.

📁 Project Structure
Evolve_BI/
│
├── streamlit_main.py                 # Main Streamlit application
├── dependencies.py                   # Helper functions (DB, charts, etc.)
├── data/                             # Sample datasets or uploaded files
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
