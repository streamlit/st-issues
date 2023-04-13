from streamlit import util

class MyString(str):
    pass

s = MyString("foobar")

util.calc_md5(s)
