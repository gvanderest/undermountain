import json as pyjson


class json(object):
    @classmethod
    def dumps(self, o):
        return pyjson.dumps(o, indent=4)

    @classmethod
    def loads(self, c):
        return pyjson.loads(c)
