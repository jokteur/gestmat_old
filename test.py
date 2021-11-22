def fct(*args):
    print(*args)


for i in range(10):
    x = lambda: fct(i)
    x()
