# Import libraries
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import pandas as pd
import requests

# Set up title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Get name on smoothie
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
try:
    connection_parameters = {
        "user": st.secrets["user"],
        "password": st.secrets["password"],
        "account": st.secrets["account"],
        "role": st.secrets["role"],
        "warehouse": st.secrets["warehouse"],
        "database": st.secrets["database"],
        "schema": st.secrets["schema"]
    }
    session = Session.builder.configs(connection_parameters).create()
except KeyError as e:
    st.error(f"❌ Missing secret: {e}")
    st.stop()

# Load FRUIT_NAME and SEARCH_ON from Snowflake
try:
    my_dataframe = session.table('smoothies.public.fruit_options') \
        .select(col('FRUIT_NAME'), col('SEARCH_ON'))
    pd_df = my_dataframe.to_pandas()
except Exception as e:
    st.error(f"❌ Failed to load data from Snowflake: {e}")
    st.stop()

# Fruit selection using GUI-friendly names
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# Submit order
if ingredients_list:
    # ✅ Build ingredients string exactly as required
    ingredients_string = ", ".join(ingredients_list)
    st.write("You
