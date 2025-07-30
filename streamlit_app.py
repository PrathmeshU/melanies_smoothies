# Import libraries
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
import pandas as pd
import requests

# App title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Name input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Snowflake connection
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

# Load fruit options
try:
    my_dataframe = session.table('smoothies.public.fruit_options') \
        .select(col('FRUIT_NAME'), col('SEARCH_ON'))
    pd_df = my_dataframe.to_pandas()
except Exception as e:
    st.error(f"❌ Failed to load data from Snowflake: {e}")
    st.stop()

# Fruit selection
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        # st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')

        st.subheader(fruit_chosen + ' Nutrition Information')
        fruityvice_response = requests.get("https://www.fruityvice.com/api/fruit/" + search_on)
        fv_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)

    # Remove final trailing comma and space
    ingredients_string = ingredients_string.rstrip(' ')
    # st.write(ingredients_string)

    # Insert into Snowflake
    insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order, order_filled, order_ts)
        VALUES ('{ingredients_string}', '{name_on_order}', FALSE, CURRENT_TIMESTAMP)
    """

    if st.button("Submit Order"):
        try:
            session.sql(insert_stmt).collect()
            st.success("✅ Your smoothie order has been submitted!")
        except Exception as e:
            st.error(f"❌ Failed to submit order: {e}")
