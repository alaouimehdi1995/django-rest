# The objects that will be serialized


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
