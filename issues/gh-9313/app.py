import streamlit as st
import pandas as pd

#Dummy data
# from dummy_data import get_analysis, Analysis
from packaging import version
from typing import Literal
class Analysis():
  """
  Dummy class to represent an analysis. In reality, this is a SQLAlchemy Model
  """
  def __init__(self, id, name, type: Literal["line", "bar"]):
    
    self.id = id
    self.name = name
    self.type = type
    
#Some dummies
dummy_analysis1 = Analysis(1, "dummy1", "line")
dummy_analysis2 = Analysis(2, "dummy2", "bar")
dummy_analysis3 = Analysis(3, "dummy3", "line")
dummy_analysis4 = Analysis(4, "dummy4", "bar")

@st.cache_data()
def get_analysis() -> Analysis:
    """
    Dummy function to get an analysis object.
    """
    
    return [dummy_analysis1, dummy_analysis2, dummy_analysis3, dummy_analysis4]

if version.parse(st.__version__) >= version.parse("1.37.0"):
  fragment_handler = st.fragment
else:
  fragment_handler = st.experimental_fragment
  
def class_to_dataframe(objects):
    """
    Converts a list of class instances to a pandas DataFrame.

    Parameters:
        objects (list): A list of class instances.

    Returns:
        pandas.DataFrame: A DataFrame where each row represents an instance
                          and each column an attribute of the class.
    """

    # Extract attribute dictionaries from objects using vars() or obj.__dict__
    data = [vars(obj) for obj in objects]
    # Create and return the DataFrame
    return pd.DataFrame(data).drop(columns=["_sa_instance_state"], errors="ignore")
  
def _get_selected_analysis(df: pd.DataFrame, analysis: list[Analysis]): 
    """
    Updates the session state with the selected analysis.

    Parameters:
        df (pd.DataFrame): DataFrame containing the analysis data.
        analysis (list[Analysis]): List of analysis objects.
    """
    selected_ausw = df.loc[df["selector"] == True]["id"].to_list()
    st.session_state["selected_analysis"] = [
            ausw for ausw in analysis if ausw.id in selected_ausw
        ]
   
@fragment_handler
def list_analysis(analysis: list[Analysis]):
  """
  Creates a list of all available analysis.#
  
  Parameters:
      analysis (Analysis): The analysis object to be displayed.
  """
  if "selected_analysis" not in st.session_state:
      st.session_state["selected_analysis"] = []

  df_raw = class_to_dataframe(analysis)
  if "selected_analysis" in st.session_state:
    df_raw.loc[
        df_raw["id"].isin(
            [ausw.id for ausw in st.session_state["selected_analysis"]]
        ),
        "selector",
    ] = True

  column_config = {
      "selector": st.column_config.CheckboxColumn(
          "Select",  default=False
      ),
      "name": st.column_config.TextColumn("Name", disabled=True),
      "type": st.column_config.TextColumn("Type", disabled=True),
  }

  column_order = ("selector", "name", "type")

  st.subheader("Choose your Analysis")
  res = st.data_editor(
      df_raw,
      column_config=column_config,
      column_order=column_order,
      hide_index=True,
      key="analysis_table",
      use_container_width=True,
  )

  selected_auswertungen = res.loc[res["selector"] == True]["id"].to_list()
  disabled = False if len(selected_auswertungen) > 0 else True
    # disabled = False
    # Buttons
  col_btn_show, _, col_btn_del = st.columns([1, 0.1, 1])
  with col_btn_show:
    if st.button(
        "**Show**",
        use_container_width=True,
        disabled=disabled,
        key="show_analysis_button",
    ):

      _get_selected_analysis(res, analysis)
      st.rerun()
      
@fragment_handler
def show_selected_analysis(analysis: Analysis):
  st.subheader(f"Selected Analysis:  {analysis.name}")
  st.write("ID: ", analysis.id)
  
  st.write("**Some Random Input: Select a value to multiple the ID by**")
  multipe = st.slider("Multiply by", 1, 10, 1,key=f"slider_{analysis.id}")
  st.write("New ID: ", analysis.id * multipe)
  
  
  
    
#Here we create the dashboard page:

st.session_state["selected_analysis"] = st.session_state.get("selected_analysis", [])

#display the list of analysis
list_analysis(analysis=get_analysis())

if "selected_analysis" in st.session_state:
    #display the selected analysis
    if len(st.session_state["selected_analysis"]) > 0:
      for analysis in st.session_state["selected_analysis"]:
        show_selected_analysis(analysis)
        st.divider()


with st.sidebar:
  with st.container(border=True):
    st.write("**What is the bug**")
    st.write("""Starting in **version 1.37.1** changing a value in a function decorated with `@st.fragment`might lead to displaying the wrong fragment. This happens if there once where multiple fragments instances of the same function created
             """)
    
    st.write("**How to reproduce**")
    st.write("""1. Install Streamlit Version 1.37.1\n\n2. Select the first two analysis options and click on the **Show** button  \n\n3. Play around with the two sliders and see that everything works as expected.\n\n4. Now deselect the first analysis and keep the second analysis selected\n\n5. Click on the **Show** button.\n\n6. Only the second analysis is now being displayed. Until here everything was working as expected.\n\n7. If you know touch the slider again, suddently the first analysis is being displayed again instead of the second one.  \n\n 
             """)
    st.write("**Excepted behavior**")
    st.write("""The expected behavior can be observed by installing Streamlit Version 1.36""")
    st.write("When this older version is installed, touching the slider will not change the displayed analysis.")
