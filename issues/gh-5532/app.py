import streamlit as st
import streamlit.components.v1 as components
import pydeck as pdk
import requests

if __name__ == '__main__':
    # DATA_URL is a valid geojson object of CA zipcodes with some metadata, it's uncompressed size is ~8.8MB
    DATA_URL = 'https://gist.githubusercontent.com/KeeonTabrizi/99493a2d7a5347c7691bc743f4a58bb3/raw/9be1eaa9f8f6bff4ad60a57cfe43e9e05b99f8db/ca_zip_codes.json'
    # LOCAL DATA loads the DATA_URL to show examples with local data usage
    LOCAL_DATA = requests.get(DATA_URL).json()
    INITIAL_VIEW_STATE = pdk.ViewState(latitude=38.028549, longitude=-120.181034, zoom=5, max_zoom=16, pitch=45, bearing=0)

    geojson_ext_data = pdk.Layer(
        "GeoJsonLayer",
        DATA_URL,
        opacity=0.8,
        stroked=True,
        auto_highlight=True,
        filled=True,
        extruded=False,
        wireframe=True,
        pickable=True,
        get_line_width=25,
        line_width_units='common',
        line_width_scale=0,
        line_width_min_pixels=1,
        get_line_color="[0, 0, 0]",
        get_fill_color="[255,255,255]"
    )

    geojson_local_data = pdk.Layer(
        "GeoJsonLayer",
        LOCAL_DATA,
        opacity=0.8,
        stroked=True,
        auto_highlight=True,
        filled=True,
        extruded=False,
        wireframe=True,
        pickable=True,
        get_line_width=25,
        line_width_units='common',
        line_width_scale=0,
        line_width_min_pixels=1,
        get_line_color="[0, 0, 0]",
        get_fill_color="[255,255,255]"
    )
    st.markdown('## Example 1: Streamlit + Pydeck w/ External Data Object - Normal Behavior')
    st.write('Zoom & Pan is responsive')
    r = pdk.Deck(layers=[geojson_ext_data], initial_view_state=INITIAL_VIEW_STATE, map_style='light')
    st.pydeck_chart(r)
    r2 = pdk.Deck(layers=[geojson_local_data], initial_view_state=INITIAL_VIEW_STATE, map_style='light')
    st.markdown('## Example 2: Streamlit + Pydeck w/ Local Data Object - Degraded Performance')
    st.write('Zoom & Pan is choppy')
    st.pydeck_chart(r2)
    st.markdown('## Example 3: Streamlit + Pydeck w/ Local Data Object injected as iframe - Normal Performance')
    st.markdown('Zoom & Pan is responsive')
    st.markdown('_Using an iframe causes additional issues with incompatability with certain pydeck layer arguments as well as losing state of the viewstate._')
    # use iframe/html trick from https://github.com/streamlit/streamlit/issues/2569
    components.html(r2.to_html(as_string=True), height=600)
