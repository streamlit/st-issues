import streamlit as st
import pandas as pd
import altair as alt

trajectory_lon_lats = [
    [2.6248460679761365, 48.73942476995791],
    [2.869797623751566, 47.73764824279678],
    [5.306610357617842, 47.17035834766139],
    [7.694764653244022, 48.50148976822578],
    [9.16443189561241, 48.602603591334],
    [8.612360316381569, 50.18541474253726],
    [10.070514259703259, 51.33434011732683],
    [11.730870143141317, 48.17424955539181],
    [12.438438778870733, 51.35980698783246],
    [11.828051088959569, 52.25097739066919],
    [9.77725373401995, 52.41837257762134],
    [8.719333151905232, 53.18257526491547],
    [10.126991240178398, 53.3259448041203],
    [13.497958630130995, 52.547704738342986],
]
stamps = [7 + i for i in range(len(trajectory_lon_lats))]
df = pd.concat(
    (
        pd.DataFrame(trajectory_lon_lats, columns=["lon", "lat"]),
        pd.DataFrame(stamps, columns=["stamp"]),
    ),
    axis=1,
)

st.dataframe(df)


pts2 = alt.selection_point(
    "foobar",
    fields=["index"],
    value=3,
)

selection = st.altair_chart(
    alt.Chart(df.reset_index())
    .mark_bar(size=20)
    .encode(
        x="index",
        y="lon",
        color=alt.condition(pts2, alt.ColorValue("steelblue"), alt.ColorValue("grey")),
    )
    .properties(width=550, height=700)
    .add_params(pts2),
    use_container_width=True,
    on_select="rerun",  # if you remove this line, the initially set selection works
)
st.write("Selection", selection)
