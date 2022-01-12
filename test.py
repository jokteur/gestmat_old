class MyClass:
    def __init__(self) -> None:
        self.bar = 1

    def do_something(self):
        def _fct():
            self.foo = 2

        _fct()


x = 2
a = dict(bla=4)


def main():
    print(a)
    a = 2
    print(a)


main()
