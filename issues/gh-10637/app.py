import enum
import pandas as pd
import streamlit as st

class Status(str, enum.Enum):
    success = "Success status"
    running = "Running status"
    error = "Error status"

    def __str__(self):
        return self.value

df = pd.DataFrame(
    {"pipeline": ["Success", "Error", "Running"], "status": [Status.success, Status.error, Status.running]}
)


def status_highlight(value: Status):
    color = ""
    match value:
        case Status.error:
            color = "red"
        case Status.running:
            color = "blue"
        case Status.success:
            color = "green"
        case _:
            color = "gray"

    return "color: %s" % color


df = df.style.map(status_highlight, subset=["status"])


st.dataframe(df, column_config={"status": st.column_config.TextColumn("Status column")}, hide_index=True)

df.data["status"] = df.data["status"].astype(str)
st.dataframe(df, column_config={"status": st.column_config.TextColumn("Status column")}, hide_index=True)
st.html(df.to_html())
