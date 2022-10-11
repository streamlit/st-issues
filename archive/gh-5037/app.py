import streamlit
import pandas
import requests
import snowflake.connector
from urllib.error import URLError

streamlit.title("My Healthy Foods")
streamlit.header("My Favorites")
streamlit.text("🍳🍳 Eggs 🍳🍳")
streamlit.text("🌮🌮  Taco 🌮🌮")
streamlit.text("🍗🍗 Meat 🍗🍗")
streamlit.text("🍕🍕 Pizza 🍕🍕")
streamlit.text("🍔 Burgers 🍔🍔")
streamlit.title("My smoothies")

my_fruit_list = pandas.read_csv(
    "https://uni-lab-files.s3.us-west-2.amazonaws.com/dabw/fruit_macros.txt"
)
my_fruit_list = my_fruit_list.set_index("Fruit")
Fruits_Selecetd = streamlit.multiselect(
    "pick some fruits:", list(my_fruit_list.index), ["Avocado", "Strawberries"]
)
Fruit_to_show = my_fruit_list.loc[Fruits_Selecetd]
streamlit.dataframe(Fruit_to_show)


def get_fruityvice_data(this_fruit_choice):
    Fruityvice_response = requests.get(
        "https://fruityvice.com/api/fruit/" + this_fruit_choice
    )
    Fruityvice_Normalize = pandas.json_normalize(Fruityvice_response.json())
    return Fruityvice_Normalize


streamlit.header("Fruityvice Fruit advice")
try:
    Fruit_choice = streamlit.text_input(
        "what fruit do you want to have information about?"
    )
    if not Fruit_choice:
        streamlit.error("please select a fruit to get information")
    else:
        back_from_function = get_fruityvice_data(Fruit_choice)
        streamlit.dataframe(back_from_function)
except URLerror as e:
    streamlit.error()
my_cnx = snowflake.connector.connect(**streamlit.secrets["snowflake"])
# my_cur = my_cnx.cursor()
# my_cur.execute("insert into pc_rivery_db.public.fruit_load_list values ('from_streamlit')")
# my_data_row = my_cur.fetchall()
streamlit.header("Fruit list contains:")


def get_fruit_load_list():
    with my_cnx.cursor() as my_cur:
        my_cur.execute("select * from fruit_load_list")
        return my_cur.fetchall()


# if streamlit.button('get fruit load list'):
# my_cnx = snowflake.connector.connect(**streamlit.secrets["snowflake"])
# my_data_rows = get_fruit_load_list()
# streamlit.dataframe(my_data_rows)
# streamlit.dataframe(my_data_row)
Fruit_add = streamlit.text_input("what fruit do you want to have?", "banana")
streamlit.write("Thanks for adding", Fruit_add)
