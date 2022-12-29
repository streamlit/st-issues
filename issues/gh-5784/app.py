import streamlit, datetime

title = streamlit.text_input('Movie title', 'Life of Brian')
d = streamlit.date_input("When's your birthday", datetime.date(2019, 7, 6))
t = streamlit.time_input('Set an alarm for', datetime.time(8, 45, 30))

streamlit.write('The current movie title is', title)
streamlit.write('Your birthday is:', d)
streamlit.write('Alarm is set for', t)