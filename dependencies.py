from openai import OpenAI
import psycopg2
from graphviz import Digraph
import streamlit as st

def chat_completion(prompt,openai_key):
    client = OpenAI(api_key=openai_key)
    chat_completion = client.chat.completions.create(messages=[ {"role": "user","content": prompt} ], model="gpt-4o")
    output=chat_completion.choices[0].message.content
    result="--"+output.split("```")[1]
    return result

def connection_setup(database_name=st.secrets["DATABASE"]):
    connection = psycopg2.connect(
        host=st.secrets["HOST"],
        database=database_name,
        port=st.secrets["PORT"],
        user=st.secrets["USER"],
        password=st.secrets["PASSWORD"]
    )
    cursor = connection.cursor()
    return connection, cursor


def data_graph_query(cursor, select_db, select_tables, type):
    cursor.execute(f"SET search_path TO {select_db}")

    cursor.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE'")
    tables = cursor.fetchall()
    
    if not tables:
        return "No tables found in the selected database."

    cursor.execute("""
    SELECT
        tc.table_schema,
        tc.table_name AS ForeignTable,
        ccu.table_name AS PrimaryTable,
        kcu.column_name AS ForeignColumn,
        ccu.column_name AS PrimaryColumn
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY';
    """)
    relationships = cursor.fetchall()
    
    if not relationships:
        dot = Digraph(comment=f'Schema for {select_db}')
        dot.attr(rankdir='LR')
        dot.attr('node', shape='box')
        for schema, table in tables:
            dot.node(f"{schema}.{table}", style='filled', color='lightgrey')
        return dot

    if type == "db_type":
        foreign_tables = {f"{rel[0]}.{rel[1]}" for rel in relationships}
    else:
        # Get the current schema
        cursor.execute("SELECT current_schema()")
        current_schema = cursor.fetchone()[0]
        
        # Add schema to table names if not present
        select_tables_with_schema = {
            table if '.' in table else f"{current_schema}.{table}"
            for table in select_tables
        }
        
        foreign_tables = select_tables_with_schema
        filtered_relationships = [
            rel for rel in relationships
            if f"{rel[0]}.{rel[1]}" in select_tables_with_schema or f"{rel[0]}.{rel[2]}" in select_tables_with_schema
        ]
        filtered_tables = set(
            f"{rel[0]}.{table}"
            for rel in filtered_relationships
            for table in (rel[1], rel[2])
        ).union(select_tables_with_schema)
        
        # Convert table names to (schema, table) tuples
        tables = []
        for table_name in filtered_tables:
            if '.' in table_name:
                schema, table = table_name.split('.')
            else:
                schema, table = current_schema, table_name
            tables.append((schema, table))
        
        relationships = filtered_relationships

    dot = Digraph(comment=f'Schema for {select_db}')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box')
    for schema, table in tables:
        full_table_name = f"{schema}.{table}"
        if full_table_name in foreign_tables:
            dot.node(full_table_name, style='filled', color='lightblue')
        else:
            if type == "tb_type":
                dot.node(full_table_name, style='dashed', color='grey')
            else:
                dot.node(full_table_name)
    for relationship in relationships:
        schema, foreign_table, primary_table, foreign_column, primary_column = relationship
        dot.edge(f"{schema}.{foreign_table}", f"{schema}.{primary_table}", label=f"{foreign_table}.{foreign_column} → {primary_table}.{primary_column}")
    return dot

def navigate_to_database_details():
    st.session_state["active_tab"] = "database_details"

def close_table_details():
    st.session_state["active_tab"] = "main"