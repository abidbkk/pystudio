import sys, json
sys.path.insert(0, '..')
import pseudo
sys.stdout.reconfigure(encoding='utf-8')
for f in sys.argv[1:]:
    print("=====", f)
    r = json.loads(pseudo.translate(open(f, encoding='utf-8').read()))
    if 'error' in r:
        print('ERROR', r)
    else:
        for text, ln in r['lines']:
            print(f'{ln:>3} | {text}')
        print('notes:', r['notes'])
