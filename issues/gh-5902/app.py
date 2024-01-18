import pandas as pd
import plotly.graph_objects as go
import numpy as np
import streamlit as st
# without a token you'll get an empty plot, they are free to get at mapbox.com

periods_dt = ["201604", "201605"]
period = st.select_slider("Period",periods_dt,value=periods_dt[0])
period = pd.to_datetime(period, format="%Y%m")

df_plot = pd.DataFrame(
    [
        ['01/04/2016',1,2,1],
        ['01/05/2016',3,4,-2]
    ],
    columns=['t','i','j','v']
)
df_plot['t'] = pd.to_datetime(df_plot['t'], dayfirst=True)
df_plot['q'] =0
df_plot = df_plot[df_plot['t']==period]

def plotting_values(df, opacity_sorted, opacity, colours):
    lat_lons = {
        1:{'geo_lon': -51, 'geo_lat': -14},
        2:{'geo_lon': 8, 'geo_lat': 9},
        3:{'geo_lon': 113, 'geo_lat': 0},
        4:{'geo_lon': 127, 'geo_lat': 35}
    }

    fig = go.Figure()
    lats = []
    lons = []
    hover_names = []

    for style_idx,style in enumerate(opacity_sorted):
        for idx, row in df.loc[opacity[opacity==style].index].iterrows():
            source = lat_lons[row['i']]
            target = lat_lons[row['j']]
            
            num_points = 100
            lats.extend(np.linspace(source['geo_lat'], target['geo_lat'], num_points, endpoint=True))
            lons.extend(np.linspace(source['geo_lon'], target['geo_lon'], num_points, endpoint=True))
            lats.append(None)
            lons.append(None)
            t = f"""From {row['i']} to {row['j']}<br>"""
            hover_names.extend([t]*num_points)
            hover_names.append(None)

        # using Scattergeo makes it work
        fig.add_trace(go.Scattermapbox(
            mode = "lines",
            lon = lons,
            lat = lats,
            line = {'width': 2, 'color':colours[style_idx]},
            hoverinfo = 'text',
            text = hover_names,
            opacity = 1,
        ))
        lats = []
        lons = []
        hover_names = []
        
    return fig

def create_plot(df, dt):
    # there's usually some logic behind the opacity vars, it doesn't affect the issue
    opacity_sorted = np.array([0.5, 1])
    opacity = pd.Series(1.0, name='v') if dt.month==4 else pd.Series(0.5, name='v', index=[1])
    colours = ['red', 'blue']
    fig = plotting_values(df, opacity_sorted,opacity, colours)
    fig.update_layout(title=f"{dt}", showlegend=False, height=1000,hoverlabel_align='left',  margin={"r":0,"l":0,"b":0, 't':30})
    fig.update_mapboxes(zoom=1.9, accesstoken="pk.eyJ1IjoidGhpYWdvdCIsImEiOiJjamh3bm85NnkwMng4M3dydnNveWwzeWNzIn0.vCBDzNsEF2uFSFk2AM0WZQ")
    return fig

_fig = create_plot(df_plot, period)
_fig.show()
st.plotly_chart(_fig, use_container_width=True)
