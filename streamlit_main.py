import streamlit as st
from lida import Manager, TextGenerationConfig, llm
from lida.datamodel import Goal
import pandas as pd
from PIL import Image
import io
import base64
import os
import re
from dotenv import load_dotenv
from dependencies import chat_completion, connection_setup, data_graph_query, navigate_to_database_details, close_table_details
load_dotenv()

openai_key = st.secrets["OPENAI_KEY"]
os.makedirs("data", exist_ok=True)
connection, cursor = connection_setup()

st.set_page_config(
    page_title="Evolve",
    page_icon="📊",
)

st.markdown("""
    <style>
        /* Main styles */
        .gradient-text {
            background: linear-gradient(45deg, #2E86AB, #23C9B6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800 !important;
        }
        .stButton>button {
            background: linear-gradient(45deg, #2E86AB, #23C9B6) !important;
            color: white !important;
            border-radius: 8px;
            padding: 8px 24px;
            transition: all 0.3s ease;
            border: none !important;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(46, 134, 171, 0.3);
        }
        /* Input fields */
        div[data-baseweb="input"] input {
            border-color: #2E86AB !important;
            border-radius: 8px !important;
        }
        /* Select boxes */
        div[data-baseweb="select"] > div {
            border: 2px solid #2E86AB !important;
            border-radius: 8px !important;
        }
        /* Checkbox */
        div[role="checkbox"] > div {
            background-color: #2E86AB !important;
            border-color: #23C9B6 !important;
        }
        /* Dataframe styling */
        .dataframe th {
            background-color: #2E86AB !important;
            color: white !important;
        }
        .dataframe tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        /* Custom headers */
        .custom-header {
            color: #2E86AB !important;
            border-left: 4px solid #23C9B6;
            padding-left: 12px;
            margin: 20px 0;
        }
        /* Code blocks */
        pre {
            background-color: #f8f9fa !important;
            border-radius: 8px !important;
            border: 1px solid #dee2e6 !important;
            padding: 16px !important;
        }
        /* Warning box */
        .warning-box {
            background-color: #fff3cd;
            color: #856404;
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 16px 0;
        }
    </style>
""", unsafe_allow_html=True)

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "main"

if "selected_tables" not in st.session_state:
    st.session_state["selected_tables"] = []

if "selected_db" not in st.session_state:
    st.session_state["selected_db"] = "Select an option"

if st.session_state["active_tab"] == "main":
    st.markdown('<h1>Evolve: Turning Questions into Visual Insights 📊</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #23C9B6;">
        Evolve is an AI-powered data visualization platform that enables users to effortlessly generate the insightful graphs
        and charts by asking natural language questions about their data. It simplifies data analysis by bridging the gap 
        between raw data and actionable visualizations, utilizing the power of Large Language Models(LLMs) to interpret queries
        and automate the process of creating meaningful graphs.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("----")
    st.sidebar.markdown("""
    <h1 style="color: #2E86AB; border-bottom: 2px solid #23C9B6; padding-bottom: 8px;">
        ⚙️ Setup
    </h1>
    """, unsafe_allow_html=True)
    cursor.execute("SELECT name FROM sys.databases")
    dbs = ["Select an option"] + [db[0] for db in cursor.fetchall()]
    select_db = st.sidebar.selectbox(
        "Select Database",
        options=dbs,
        index=dbs.index(st.session_state["selected_db"]),
        placeholder="Choose a database"
    )
    file_path = None
    if select_db != "Select an option":
        st.session_state["selected_db"] = select_db
        st.sidebar.button("View", on_click=navigate_to_database_details)
        cursor.execute(f"USE [{select_db}]")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = [table[0] for table in cursor.fetchall()]
        select_tables = st.sidebar.multiselect("Select Tables", options=tables, placeholder="Choose tables")
        if select_tables:
            st.session_state["selected_tables"] = select_tables
            if st.sidebar.checkbox("See Details", value=False):
                dot = data_graph_query(cursor, select_db, select_tables, type="tb_type")
                st.graphviz_chart(dot)
                st.write("----")
            if len(select_tables) == 1:
                table_query = f"SELECT * FROM {select_tables[0]}"
                table_data = pd.read_sql(table_query, connection)
                os.makedirs("data", exist_ok=True)
                file_path = os.path.join("data", f"{select_tables[0]}.csv")
                table_data.to_csv(file_path, index=False)
            else:
                cursor.execute(f"USE {select_db}")
                temp = ""
                for i in select_tables:
                    schema = f"SELECT COLUMN_NAME AS [Column Name], DATA_TYPE AS [Data Type], CHARACTER_MAXIMUM_LENGTH AS [Max Length], IS_NULLABLE AS [Is Nullable] FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{i}' AND TABLE_SCHEMA = 'dbo' ORDER BY ORDINAL_POSITION;"
                    table = pd.read_sql(schema, connection)
                    temp += f"{i}\n{table}\n\n"
                prompt = temp + "Generate SQL query : Combine all the tables only on avaliable columns"
                table_query = chat_completion(prompt, openai_key)
                table_data = pd.read_sql(table_query, connection)
                file_path = os.path.join("data", f"{select_tables[0]}.csv")
                table_data.to_csv(file_path, index=False)
            selected_dataset = file_path
    st.sidebar.write("----")
    upload_own_data = st.sidebar.checkbox("Upload your own data")
    selected_dataset = None
    if upload_own_data:
        uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])
        if uploaded_file is not None:
            file_name, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension.lower() == ".csv":
                data = pd.read_csv(uploaded_file)
            uploaded_file_path = os.path.join("data", uploaded_file.name)
            data.to_csv(uploaded_file_path, index=False)
            selected_dataset = uploaded_file_path
    else:
        selected_dataset = file_path
    if select_db == "Select an option" and not upload_own_data:
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ Note:</strong> Select a database or upload CSV data to explore its details!
        </div>
        """, unsafe_allow_html=True)
    select_tables = st.session_state["selected_tables"]
    select_db = st.session_state["selected_db"]
    if len(select_tables) > 0 or select_db != "Select an option" or upload_own_data:
        st.sidebar.markdown("""
        <h3 style="color: #2E86AB; margin-top: 20px;">
            🧠 Text Generation Model
        </h3>
        """, unsafe_allow_html=True)
        models = ["gpt-4o", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
        selected_model = st.sidebar.selectbox(
            "Select Model",
            options=models,
            index=0,
            placeholder="Choose a model"
        )
        temperature = st.sidebar.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.0
        )
        use_cache = True
    selected_method = "llm"
    if openai_key and selected_dataset and selected_method:
        lida = Manager(text_gen=llm("openai", api_key=openai_key))
        textgen_config = TextGenerationConfig(
            n=1,
            temperature=temperature,
            model=selected_model,
            use_cache=use_cache
        )
        st.markdown('<h4 class="custom-header">📝 Dataset Summary</h4>', unsafe_allow_html=True)
        summary = lida.summarize(
            selected_dataset,
            summary_method=selected_method,
            textgen_config=textgen_config
        )
        if "dataset_description" in summary:
            st.write(summary["dataset_description"])
        if "fields" in summary:
            fields = summary["fields"]
            nfields = []
            for field in fields:
                flatted_fields = {}
                flatted_fields["column"] = field["column"]
                for row in field["properties"].keys():
                    if row != "samples":
                        flatted_fields[row] = field["properties"][row]
                    else:
                        flatted_fields[row] = str(field["properties"][row])
                nfields.append(flatted_fields)
            nfields_df = pd.DataFrame(nfields)
            st.write(nfields_df)
        else:
            st.write(str(summary))
        st.markdown("----")
        if summary:
            st.sidebar.markdown("""
            <h3 style="color: #2E86AB; margin-top: 20px;">
                🎯 Goal Selection
            </h3>
            """, unsafe_allow_html=True)
            num_goals = st.sidebar.slider(
                "Number of goals to generate",
                min_value=1,
                max_value=10,
                value=4
            )
            own_goal = st.sidebar.checkbox("Add Your Own Goal")
            goals = lida.goals(summary, n=num_goals, textgen_config=textgen_config)
            st.markdown('<h4 class="custom-header">🎯 Generated Goals</h4>', unsafe_allow_html=True)
            default_goal = goals[0].question
            goal_questions = [goal.question for goal in goals]
            if own_goal:
                user_goal = st.sidebar.text_input("Describe Your Goal")
                if user_goal:
                    new_goal = Goal(question=user_goal, visualization=user_goal, rationale="")
                    goals.append(new_goal)
                    goal_questions.append(new_goal.question)
            selected_goal = st.selectbox('Choose a generated goal', options=goal_questions, index=0)
            display_query = st.checkbox("Display Query")
            if display_query:
                cursor.execute(f"USE {select_db}")
                temp = ""
                for i in select_tables:
                    query = f"SELECT COLUMN_NAME AS [Column Name], DATA_TYPE AS [Data Type], CHARACTER_MAXIMUM_LENGTH AS [Max Length], IS_NULLABLE AS [Is Nullable] FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{i}' AND TABLE_SCHEMA = 'dbo' ORDER BY ORDINAL_POSITION;"
                    table = pd.read_sql(query, connection)
                    temp += f"{i}\n{table}\n\n"
                prompt = f"{temp}\n{selected_goal}\nGenerate SQL query : Based on above tables schema's and question"
                table_query = chat_completion(prompt, openai_key)
                st.code(table_query, language="sql")
            selected_goal_index = goal_questions.index(selected_goal)
            selected_goal_object = goals[selected_goal_index]
            if selected_goal_object:
                st.sidebar.markdown("""
                <h3 style="color: #2E86AB; margin-top: 20px;">
                    📈 Visualization Options
                </h3>
                """, unsafe_allow_html=True)
                visualization_libraries = ["seaborn", "matplotlib", "plotly"]
                visualization_types = ["Line Plot", "Scatter Plot", "Bar Chart", "Pie Chart", "Histogram", "Box Plot", "Violin Plot", "Heatmap", "Pairplot", "Jointplot"]
                selected_library = st.sidebar.selectbox(
                    'Choose a visualization library',
                    options=visualization_libraries,
                    index=0
                )
                visual_type = st.sidebar.selectbox(
                    'Choose a visualization type',
                    options=visualization_types,
                    index=None,
                    placeholder="Choose type"
                )
                st.markdown("----")
                st.markdown('<h4 class="custom-header">📈 Visualizations</h4>', unsafe_allow_html=True)
                num_visualizations = st.sidebar.slider(
                    "Number of visualizations to generate",
                    min_value=1,
                    max_value=10,
                    value=2
                )
                if visual_type:
                    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, visualization_types)) + r')\b', re.IGNORECASE)
                    selected_goal_object = pattern.sub(visual_type, str(selected_goal_object))
                textgen_config = TextGenerationConfig(
                    n=num_visualizations,
                    temperature=temperature,
                    model=selected_model,
                    use_cache=use_cache
                )
                visualizations = lida.visualize(
                    summary=summary,
                    goal=selected_goal_object,
                    textgen_config=textgen_config,
                    library=selected_library
                )
                viz_titles = [f'Visualization {i+1}' for i in range(len(visualizations))]
                selected_viz_title = st.selectbox('Choose a visualization', options=viz_titles, index=0)
                selected_viz = visualizations[viz_titles.index(selected_viz_title)]
                if selected_viz.raster:
                    imgdata = base64.b64decode(selected_viz.raster)
                    img = Image.open(io.BytesIO(imgdata))
                    st.image(img, caption=selected_viz_title, use_column_width=True)  
                st.markdown('<h4 class="custom-header">🖥️ Visualization Code</h4>', unsafe_allow_html=True)
                st.code(selected_viz.code)
elif st.session_state["active_tab"] == "database_details":
    st.markdown(f"""
    <h4 style='color: #2E86AB; background-color: #f8f9fa; 
                padding: 16px; border-radius: 8px; border-left: 4px solid #23C9B6;'>
        🗄️ Database Graph Visualization
    </h4>
    """, unsafe_allow_html=True)
    st.write("----")
    select_db = st.session_state["selected_db"]
    select_tables = st.session_state["selected_tables"]
    if select_db:
        dot = data_graph_query(cursor, select_db, select_tables, type="db_type")
        st.graphviz_chart(dot)
        st.button("Close", on_click=close_table_details)
    else:
        st.warning("No database selected. Returning to the main tab.")
        close_table_details()