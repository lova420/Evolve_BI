from openai import OpenAI
import pyodbc
from graphviz import Digraph
import streamlit as st

def chat_completion(prompt,openai_key):
    client = OpenAI(api_key=openai_key)
    chat_completion = client.chat.completions.create(messages=[ {"role": "user","content": prompt} ], model="gpt-4o")
    output=chat_completion.choices[0].message.content
    result="--"+output.split("```")[1]
    return result

def connection_setup():
    connection = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=BTDB;'
    'DATABASE=master;'
    'UID=sa;'
    'PWD=btcde@123;'
    )
    cursor = connection.cursor()
    return connection,cursor

def data_graph_query(cursor, select_db, select_tables, type):
    cursor.execute(f"USE [{select_db}]")
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [row.TABLE_NAME for row in cursor.fetchall()]
    cursor.execute("""
    SELECT 
        tf.name AS ForeignTable,
        tp.name AS PrimaryTable,
        cf.name AS ForeignColumn,
        cp.name AS PrimaryColumn
    FROM sys.foreign_keys AS fk
    INNER JOIN sys.foreign_key_columns AS fkc 
        ON fk.object_id = fkc.constraint_object_id
    INNER JOIN sys.tables AS tp 
        ON fkc.referenced_object_id = tp.object_id
    INNER JOIN sys.columns AS cp 
        ON fkc.referenced_object_id = cp.object_id AND fkc.referenced_column_id = cp.column_id
    INNER JOIN sys.tables AS tf 
        ON fkc.parent_object_id = tf.object_id
    INNER JOIN sys.columns AS cf 
        ON fkc.parent_object_id = cf.object_id AND fkc.parent_column_id = cf.column_id;
    """)
    relationships = cursor.fetchall()
    if type=="db_type":
        foreign_tables = {rel[0] for rel in relationships}
    else:
        foreign_tables = select_tables
        filtered_relationships = [
                                    rel for rel in relationships
                                    if rel[0] in select_tables or rel[1] in select_tables
                                ]
        filtered_tables = set(
                                table
                                for rel in filtered_relationships
                                for table in (rel[0], rel[1])
                            ).union(select_tables)
        tables=filtered_tables
        relationships=filtered_relationships
    dot = Digraph(comment=f'Schema for {select_db}')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box')
    for table in tables:
        if table in foreign_tables:
            dot.node(table, style='filled', color='lightblue')
        else:
            if type=="tb_type":
                dot.node(table, style='dashed', color='grey')
            else:
                dot.node(table)
    for relationship in relationships:
        foreign_table, primary_table, foreign_column, primary_column = relationship
        dot.edge(foreign_table, primary_table, label=f"{foreign_table}.{foreign_column} → {primary_table}.{primary_column}")
    return dot

def navigate_to_database_details():
    st.session_state["active_tab"] = "database_details"

def close_table_details():
    st.session_state["active_tab"] = "main"