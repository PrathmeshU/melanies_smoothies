# Import python packages
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import requests

# Title and instructions
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Name input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Setup Snowflake connection
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

# Load fruit options from Snowflake
try:
    fruit_df = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
    fruit_list = fruit_df.to_pandas()["FRUIT_NAME"].tolist()
except Exception as e:
    st.error(f"❌ Could not load fruit options: {e}")
    st.stop()

# Fruit selection
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_list,
    max_selections=5
)

# Handle fruit selection
if ingredients_list:
    ingredients_string = ", ".join(ingredients_list)
    st.write("You chose:", ingredients_string)

    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    if st.button('Submit Order'):
        try:
            session.sql(my_insert_stmt).collect()
            st.success('✅ Your Smoothie is ordered!')
        except Exception as e:
            st.error(f"❌ Failed to submit order: {e}")

# Fetch fruit nutrition info from external API (using Fruityvice)
fruit_to_fetch = "watermelon"
api_url = f"https://www.fruityvice.com/api/fruit/{fruit_to_fetch}"

response = requests.get(api_url)

import pandas as pd

if response.status_code == 200:
    try:
        fruit_data = response.json()
        st.subheader(f"Nutritional Info for {fruit_to_fetch.capitalize()}")

        # Extract constant values
        base_info = {
            "family": fruit_data.get("family", ""),
            "genus": fruit_data.get("genus", ""),
            "id": fruit_data.get("id", ""),
            "name": fruit_data.get("name", ""),
            "order": fruit_data.get("order", "")
        }

        # Extract nutrition values
        nutritions = fruit_data.get("nutritions", {})

        # Create a DataFrame in the desired format
        rows = []
        for nutrient, value in nutritions.items():
            row = {
                "": nutrient,  # empty column for eye icon mimicry
                "family": base_info["family"],
                "genus": base_info["genus"],
                "id": base_info["id"],
                "name": base_info["name"],
                "nutrition": value,
                "order": base_info["order"]
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Could not decode or format API response: {e}")
