x = 42

for _ in []:
    pass
else:
    "x", x

while False:
    pass
else:
    "x", x

try:
    pass
except NameError:
    pass
else:
    "x", x

try:
    raise ExceptionGroup("exception group", [ValueError()])
except ValueError:
    "x", x
