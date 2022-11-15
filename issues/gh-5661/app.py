st.write("""
1. Take a photo. Notice that the size is a nonstandard size, like (for me) 773 x 579. This is the other (and more fundamental) bug, Make picture size returned by camera_input consistent via parameter #4320. (But the default should be a standard, useful size.)
2. Clear the photo.
3. Adjust the right-side height until a scroll bar appears. Notice that the camera input restarts. This isn't too bothersome, but...
4. Resize your browser window horizontally, just for a short time. Don't do this for too long or your webcam won't work for a while.
""")

from PIL import Image

#st.set_page_config(layout="wide")
st.write("Set the layout to wide mode")

col1, col2 = st.columns(2)

with col1:
   img_file_buffer = st.camera_input("Take a picture")

if img_file_buffer is not None:
    im = Image.open(img_file_buffer)
    st.write(f"{im.width} x {im.height}")

with col2:
    height = st.number_input("height", value=200, step=10)
    st.write(f'<div style="border: 5px solid red; height: {height}px">Adjust me</div>', unsafe_allow_html=True)
