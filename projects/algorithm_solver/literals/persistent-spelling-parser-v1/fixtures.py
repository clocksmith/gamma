"""Exact invented timing fixtures. Constructing these is not a measurement."""
import hashlib
import json

BLOCKS = ('old-A', 'persistent-A', 'persistent-B', 'old-B')


def scalar_requests():
    requests = []
    for i in range(32):
        name = ['a','b','c','d'][i % 4]
        text = 'function solve('+name+'){/*scalar'+str(i)+'*/return '+name+'+'+name+'}'
        requests.append({str(i):text})
    return requests + requests


def engine_inputs():
    texts = {'10':'function solve(a){return a+a}', '2':'function solve(b){return b+b}'}
    alphabet = [chr(i) for i in range(32,127)] + ['\n']
    return texts, list(reversed(alphabet)) + ['aa','ab']


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def specification():
    texts,vocab = engine_inputs()
    return {'blocks':list(BLOCKS), 'scalar_requests':scalar_requests(),
            'engine_sources':texts, 'ordered_vocabulary':vocab,
            'menu':'unchanged46 fit-derived menu', 'passes':2, 'proposal_cap':153600}
