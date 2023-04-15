import sys
import imp
import json
r = dict()
x = imp.load_source('*', sys.argv[1])
for _ in dir(x):
    if _.startswith('_'):
        continue
    try:
        r[_] = {'runs': getattr(x, _)()}
        with open(sys.argv[1] + '.run', 'w') as handle:
            handle.write(json.dumps(r))
    except Exception as ex:
        r[_] = {'error': str(ex)}
    with open(sys.argv[1] + '.run', 'w') as handle:
            handle.write(json.dumps(r))
