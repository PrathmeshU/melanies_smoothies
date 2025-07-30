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

# Show the dataframe for debugging
# st.dataframe(pd_df)
# st.stop()

# Fruit selection using GUI-friendly names
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# Submit order
if ingredients_list:
        # Build a cleanly formatted ingredients string
    ingredients_string = ", ".join(ingredients_list)
    st.write("You chose:", ingredients_string)

    # Store in Snowflake orders table
    insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order, order_filled, order_ts)
        VALUES ('{ingredients_string}', '{name_on_order}', FALSE, CURRENT_TIMESTAMP)
    """


    if st.button('Submit Order'):
        try:
            session.sql(insert_stmt).collect()
            st.success("✅ Your Smoothie is ordered!")
        except Exception as e:
            st.error(f"❌ Failed to submit order: {e}")

    # Fetch and show nutrition info for each selected fruit
    for fruit_chosen in ingredients_list:
        # Get search term from SEARCH_ON column
        try:
            search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
            st.write(f"The search value for **{fruit_chosen}** is **{search_on}**.")
        except:
            st.warning(f"⚠️ Could not find search value for {fruit_chosen}")
            continue

        st.subheader(f"{fruit_chosen} Nutrition Information")

        # Call Fruityvice API
        api_url = f"https://www.fruityvice.com/api/fruit/{search_on.lower()}"
        response = requests.get(api_url)

        if response.status_code == 200:
            try:
                fruit_data = response.json()

                base_info = {
                    "family": fruit_data.get("family", ""),
                    "genus": fruit_data.get("genus", ""),
                    "id": fruit_data.get("id", ""),
                    "name": fruit_data.get("name", ""),
                    "order": fruit_data.get("order", "")
                }

                nutritions = fruit_data.get("nutritions", {})
                rows = []

                for nutrient, value in nutritions.items():
                    rows.append({
                        "": nutrient,
                        "family": base_info["family"],
                        "genus": base_info["genus"],
                        "id": base_info["id"],
                        "name": base_info["name"],
                        "nutrition": value,
                        "order": base_info["order"]
                    })

                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Could not parse nutrition data for {fruit_chosen}: {e}")
        else:
            st.warning(f"🚫 {fruit_chosen} was not found in the Fruityvice database.")
