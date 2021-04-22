# The objects that will be serialized


payload = {
    "foo": "bar",
    "bar": 5,
    "sub": {"x": 20, "y": "hello", "z": 10, "w": 1000},
}


class SimpleObject(object):
    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.w = w
        self.z = z


class ComplexObject(object):
    def __init__(self, foo, bar, sub):
        self.foo = foo
        self.bar = bar
        self.sub = SimpleObject(**sub)
        self.subs = [SimpleObject(**sub) for i in range(10)]
