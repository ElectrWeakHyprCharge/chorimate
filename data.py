import json

def _merge(*args):
    result = {}
    for dictionary in args: result.update(dictionary)
    return result

def dump(data, f):
    json.dump(dumps(data), f)

def dumps(obj):
    return {cosa: {k[0]:v for k, v in obj.items() if k[1] == cosa} for cosa in {x[1] for x in obj}}

def load(f):
    return loads(json.load(f))

def loads(obj):
    return _merge(*[{(k, cosa):v for k, v in obj[cosa].items()} for cosa in obj])

