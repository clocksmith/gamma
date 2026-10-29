"""One author-development call; receives arguments only, never expected results."""
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time
import traceback

source = Path(sys.argv[1])
arguments = json.load(sys.stdin)
spec = importlib.util.spec_from_file_location('development_candidate', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
started = time.perf_counter()
try:
    result = module.solve(*arguments)
    response = {'result':result,'exception':None}
except Exception as error:
    response = {'result':None,'exception':{'type':type(error).__name__,'message':str(error),'trace':traceback.format_exc()[-1800:]}}
elapsed = time.perf_counter()-started
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
response.update(argumentsAfter=arguments,elapsedSeconds=elapsed,rssBytes=rss if sys.platform=='darwin' else rss*1024,sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest())
print(json.dumps(response,allow_nan=False))
