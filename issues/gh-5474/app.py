import pyvista
import streamlit.components.v1 as components
from pyvista import examples

mesh = examples.load_airplane()
pl = pyvista.Plotter()
_ = pl.add_mesh(mesh, show_edges=True)
pl.export_html("pyvista.html")

html_file = open("pyvista.html", "r", encoding="utf-8")
source_code = html_file.read()
components.html(source_code, height=500, width=500, scrolling=True)
