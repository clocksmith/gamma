"""Continue the exact frozen global worklist; no new IDs or source authority."""
from run_js_global import main

if __name__ == '__main__':
    main('JS-GLOBAL-RESULT-v3.json', 'JS-GLOBAL-RESULT-v2.json')
