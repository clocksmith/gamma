"""Write and freeze source-free contracts/references before any candidates exist."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
KEYS = ['passwords','coverage','squares',None,'ratings',None,'date','decode','access',None,None,'cluster','orders','crypto',None,'ip','meeting','pagination','path','radix','rate','retry','trading',None,'goodness','products','cars','lru','earliest','adjacent','referrals','timeline']
BLOCKED = {
    3: 'The preview ends before BOTH defining stability conditions. No stable-subarray predicate is available.',
    5: 'The preview ends before the pay rules. Base rate, concurrency multiplier and event/time semantics are unavailable for all three variants.',
    9: 'The preview supplies input records but omits query methods, ordering/staleness rules and the actual concurrent-access contract. A sequential mock cannot establish non-blocking multi-thread behavior.',
    10: 'The preview describes alternating random draws but gives no scoring, stopping, winning or requested output rules. Neither variant body is public here.',
    14: 'Only a single-breaker introduction is visible; the dual-breaker routing, thresholds, reset and cooldown semantics are absent.',
    23: 'The preview gives one disguised word but omits the substitution rules, matching boundaries and required output. No exact moderation predicate is available.'
}
FUNCTIONS = {
    'passwords': ('countDistinctPasswords',['password']),
    'coverage': ('countFullyCoveredClusters',['availability','users']),
    'squares': ('countGridSquares',['queries']),
    'date': ('isValidDate',['a','b','c']),
    'decode': ('decodePassword',['text']),
    'cluster': ('clusterSummary',['parents']),
    'retry': ('retryOperation',['outcomes','maxAttempts','initialDelay','multiplier']),
    'goodness': ('distinctGoodnessValues',['arr']),
    'products': ('distinctPrimeProducts',['primes']),
    'cars': ('dualCarDestinations',['grid']),
    'earliest': ('earliestReachableTime',['startX','startY','targetX','targetY','directions']),
    'adjacent': ('eliminateAdjacentDuplicates',['text']),
    'referrals': ('referralLeaderboard',['referrers','referrals']),
    'timeline': ('shiftTimeline',['schedules'])
}
CLASSES = {
    'ratings': ('CustomerSupportSystem',[], {'record':['agentId','score','month'],'rank':['month']}),
    'access': ('AccessSystem',['parents'], {'grant':['advertiser','region'],'revoke':['advertiser','region'],'canAccess':['advertiser','region']}),
    'orders': ('CryptoOrderManager',[], {'apply':['message'],'status':['orderId']}),
    'crypto': ('CryptoTradingSystem',[], {'place':['id','currency','amount','timestamp','type'],'pause':['id'],'resume':['id'],'cancel':['id'],'complete':['id'],'listLive':['currency']}),
    'ip': ('IPRangeIterator',['start'], {'hasNext':[],'next':[]}),
    'meeting': ('MeetingScheduler',['rooms'], {'book':['start','end'],'schedule':['room']}),
    'pagination': ('PaginationAPI',['external'], {'read':['count'],'fetchCount':[]}),
    'path': ('PathKeyValueStore',[], {'create':['path','value'],'set':['path','value'],'get':['path'],'delete':['path']}),
    'radix': ('RadixCache',[], {'insert':['sequence','value'],'get':['sequence']}),
    'rate': ('RateLimiter',['rules'], {'allow':['timestamp']}),
    'lru': ('LRUCache',['capacity'], {'get':['key'],'put':['key','value'],'resize':['capacity']}),
    'trading': ('TradingSystem',[], {'addListing':['seller','item','price'],'buy':['item','budget']})
}
SPECS = {
    'passwords': 'Count distinct Unicode-code-point strings obtainable by reversing one nonempty contiguous segment. Include the unchanged string; the empty input has one result by an explicit extension.',
    'coverage': 'Count four-connected components of user cells whose every cell has availability 1. Matrices have identical rectangular dimensions; availability need not connect to other available cells. Empty matrices return zero.',
    'squares': 'For each nonnegative [rows, columns], return the exact number of axis-aligned square placements of every positive side length. Zero-sized grids have zero placements.',
    'ratings': 'record(agentId,score,month) records one integer score. rank(month) returns [agentId,numerator,denominator] rows for exact reduced average scores, descending by average then ASCII agent ID. A null month means all time; empty groups are absent.',
    'date': 'Return true if any permutation of the three supplied integers is a valid proleptic Gregorian [year,month,day], with year 1..9999. Consider all six permutations, including century leap-year rules.',
    'decode': 'The first string contains [x,y]. Treat x as the zero-based column and y as the zero-based row in the subsequent rectangular uppercase-letter board. Return that one character. Inputs contain an in-range coordinate.',
    'access': 'A parent map describes a fixed rooted tree. Each advertiser begins with no permitted nodes. grant unions an entire subtree; revoke subtracts the entire subtree even after an ancestor grant; canAccess checks membership. A later grant can restore a revoked descendant.',
    'cluster': 'Given a valid parent-index rooted tree, aggregate child replies bottom-up. Return the node count and topology rendered as id(child1,child2), omitting parentheses for leaves and ordering children by numeric ID. Empty input returns count zero and empty topology. This is a local adjacency-only protocol model, not a deployed distributed implementation.',
    'orders': 'Process ordered, at-most-once NEW/FILLED CSV events. NEW creates an order; an identical repeated NEW is a no-op, conflicting NEW returns false. FILLED requires matching side/symbol and positive quantity no greater than remaining. Invalid updates return false without mutation. status returns a fresh snapshot or null. FILLED retries are not deduplicated because the preview supplies no event ID.',
    'crypto': 'Maintain orders by unique ID. place creates live orders; pause accepts live, resume accepts paused, cancel accepts live/paused, complete accepts live. Other transitions return false. listLive(currency) returns fresh live snapshots by timestamp then ID, optionally filtering currency. Terminal IDs cannot be reused.',
    'ip': 'Iterate forward from a valid IPv4 address through 255.255.255.255 inclusive. hasNext reports availability; next returns an address or null after exhaustion, without wrapping. Python iterator protocol additionally raises StopIteration on exhaustion.',
    'meeting': 'Rooms retain constructor order. book(start,end) uses half-open nonempty intervals and assigns the first room with no overlap, returning its ID or null. schedule(room) returns fresh sorted intervals. Cancellation is outside this inferred exercise.',
    'pagination': 'Wrap an injected getPage(zeroBasedPage) provider. read(k) returns up to k strings without losing unused page tails. Empty pages mean terminal EOF; interior empty pages are excluded because the preview exposes no independent continuation signal. read(0) must not fetch. The trace adapter injects a finite page fixture; fetchCount is an authored observability method.',
    'path': 'Maintain canonical absolute paths with immutable root / holding root. create succeeds only for a missing non-root path with an existing parent. set updates existing non-root values. get returns a string or null. delete removes only existing non-root leaves. Operations return booleans except get.',
    'radix': 'Store integer-sequence keys in a compressed radix tree. insert(sequence,value) overwrites exact keys; get requires an exact terminal key and returns its scalar value or null. Empty sequences are valid. Insertions must split shared compressed edges rather than changing other keys.',
    'rate': 'For nondecreasing integer timestamps, accept iff every [limit,window] rule has fewer than limit accepted requests in (timestamp-window,timestamp]. Rejected attempts do not consume any rule. Apply acceptance atomically across rules in this sequential exercise; no production concurrency guarantee is inferred.',
    'retry': 'The native retry callable retries exceptions up to maxAttempts including the first call, invoking an injected delay hook between failed attempts with initialDelay*multiplier^i. Never sleep or perform I/O. The JSON adapter accepts scripted ok/error outcomes and returns value, error, attempts and delays; exhausted scripts raise exhausted.',
    'trading': 'addListing adds one unit with seller, item and integer price. buy(item,budget) consumes the cheapest eligible listing, breaking equal-price ties by insertion order, and returns [seller,price] or null. Quantities, cancellation and order books are outside this inferred single-unit marketplace contract.',
    'goodness': 'Return the sorted distinct bitwise-OR values of strictly increasing subsequences, including zero for the empty subsequence. Input values are nonnegative safe integers; order is preserved and equal successive values cannot extend a subsequence.',
    'products': 'Return all distinct products of nonempty subsets of the supplied primes, including multiplicities up to those present in the input, sorted numerically. Use arbitrary-precision integers; the input is not changed.',
    'cars': 'Find the fewest synchronous ticks moving each car in four directions or waiting until both reach their own marked destination. Walls are impassable. Cars cannot share a cell or swap endpoints of an edge in one tick. Reaching a destination does not freeze movement. These collision and timing rules are explicit inferences because the preview stops before them.',
    'lru': 'Provide get, put and resize with least-recently-used eviction. get returns -1 for absence and otherwise refreshes recency. put refreshes existing keys. Nonnegative resize immediately evicts oldest entries until within capacity; zero capacity retains nothing.',
    'earliest': 'Return the earliest prefix length in which the target can be reached using each direction only at its listed second, with waiting permitted. Return zero when already there and -1 if no prefix suffices.',
    'adjacent': 'Return the minimum number of single-character replacements needed so no adjacent characters match. The input is lowercase English letters and replacements may use any lowercase letter.',
    'referrals': 'For an acyclic forest with at most one referrer per referred user and no duplicate edge, count each direct or indirect descendant. Return the top three users that actually appear as referrers, ordered by count descending then ASCII name. Returning [name,count] rows and tie rules are inferred.',
    'timeline': 'Produce maximal nonempty half-open intervals with a constant set of working employees. Overlapping shifts from the same employee count once. Employee order follows first appearance in the input. Merge adjacent intervals with identical employee lists; omit uncovered gaps.'
}
DESIGNS = {
    'passwords': ('Count unequal endpoint pairs, plus the unchanged string. Strip equal ends from a reversal to identify its unique first/last changed positions.', 'O(n) time, O(alphabet) space', 'Enumerate all substrings, build reversed strings and deduplicate literally.'),
    'coverage': ('Flood each user component once; keep a covered flag while visiting all cells, even after finding an uncovered cell.', 'O(rows*columns) time and space', 'Expand component sets by repeated adjacency scans.'),
    'squares': ('Expand the sum of (r-k+1)(c-k+1) and use exact integer sums of k and k squared.', 'O(queries) arithmetic operations; integer bit cost applies', 'Enumerate side lengths and placement coordinates on small grids.'),
    'ratings': ('Maintain sum/count aggregates per agent globally and per month; rank by cross-multiplied rational averages and reduce output fractions.', 'O(1) record; O(agents log agents) rank', 'Retain all feedback rows and regroup/rescan for every query.'),
    'date': ('Try the six assignments; validate month length with a 400/100/4 Gregorian leap predicate.', 'O(1) time and space', 'Use standard-library calendar month lengths over all permutations.'),
    'decode': ('Parse the two coordinate integers and index the board at row y, column x.', 'O(coordinate text length) time, O(1) extra space', 'Enumerate every board cell and select the matching coordinate.'),
    'access': ('Flatten the tree into Euler subtree intervals. Maintain a sorted union of allowed intervals per advertiser; revoke subtracts a range, creating exceptions.', 'O(regions) preprocessing; O(intervals) updates; O(log intervals) query', 'Rescan ancestor chains and explicitly union/subtract permitted node sets.'),
    'cluster': ('Reduce leaves toward parents using a pending-child counter. Each reply carries only its child count/topology and travels to that child’s parent.', 'O(n squared) worst-case string construction; O(n squared) transient text', 'Recursively rescan the parent array for each node.'),
    'orders': ('Keep one record per ID; validate complete events before modifying fill counters. Return fresh snapshots.', 'O(1) expected apply/status', 'Literal dictionary state transition model, including rejected updates.'),
    'crypto': ('Use an explicit transition table and ID-indexed records. Sort only live snapshots for listing.', 'O(1) transitions; O(n log n) listing', 'Literal state-machine replay with independently spelled transition rules.'),
    'ip': ('Convert octets to an unsigned arithmetic counter; format and increment without signed bitwise operations.', 'O(1) per next, O(1) state', 'Use division by explicit powers of 256 for every octet.'),
    'meeting': ('Keep each room’s bookings sorted; binary-search the insertion slot and inspect only neighboring intervals.', 'O(rooms log bookings + bookings) booking; O(bookings) snapshot', 'Scan every interval in each room for overlap.'),
    'pagination': ('Keep a current-page buffer and index, next page number and EOF flag. Fetch lazily only when a positive read needs more items.', 'O(returned items + fetched pages); one page buffered', 'Flatten the known finite fixture and separately account for provider fetch boundaries.'),
    'path': ('Map canonical paths to values plus direct-child counts, preventing parent deletion without scanning all descendants.', 'O(path length) expected operations; O(stored path bytes) space', 'Scan all stored path strings to determine whether a node has descendants.'),
    'radix': ('Traverse compressed edges; split an edge at the first mismatch or a key ending inside it, preserving old suffix and terminal state.', 'O(key length) operations, O(total key bytes) storage', 'Store complete sequence tuples in a plain dictionary.'),
    'rate': ('Keep accepted timestamps in a queue per rule. Prune expired entries in every rule, decide once, then append to all queues only on success.', 'O(rules) amortized per request plus retained timestamps', 'Retain all accepted times and recount each rule window on every attempt.'),
    'retry': ('Run an explicit bounded attempt loop. Delay only between failures; return first success or preserve the last error.', 'O(attempts) control work, O(1) native state apart from hooks', 'Interpret scripted outcomes directly and construct the expected delay series.'),
    'trading': ('Maintain a price/insertion-sequence min-heap per item; inspect and pop the cheapest eligible listing.', 'O(log listings) add/buy, O(listings) storage', 'Scan and select the cheapest matching active row.'),
    'goodness': ('For each reachable OR value retain the smallest final element; smaller tails dominate larger tails when extending strictly increasing subsequences.', 'O(n*distinct OR states) time, O(distinct OR states) space', 'Enumerate every subset and reject non-increasing selections.'),
    'products': ('Extend a set of exact products by each input prime, deduplicate, remove the empty product and sort numerically.', 'O(n*distinct products + sort) arithmetic operations; bit cost applies', 'Enumerate all nonempty index subsets and multiply their selected primes.'),
    'cars': ('BFS the ordered pair of car positions; combine their five possible moves, excluding occupancy and edge-swap collisions.', 'O(open cells squared) states and space; at most 25 transitions per state', 'Layered sets built with grid-wide move enumeration rather than candidate adjacency tables.'),
    'lru': ('Use insertion-ordered maps, moving accessed keys to the newest position and evicting the oldest entry until within capacity.', 'O(1) expected get/put; resize proportional to evictions', 'Linear ordered list of key/value pairs with explicit scans.'),
    'earliest': ('Consume a direction only while that axis still needs movement toward the target; return when both deficits become zero.', 'O(direction count) time, O(1) space', 'Track every reachable coordinate under move-or-wait choices.'),
    'adjacent': ('Each equal-character run of length k needs floor(k/2) replacements; sum those independent lower bounds.', 'O(n) time, O(1) space', 'Dynamic programming over all 26 possible replacement characters.'),
    'referrals': ('Process leaves upward, accumulating subtree sizes, then rank only actual referrers.', 'O(users + referrers log referrers) time, O(users) space', 'Recursively count descendants separately for every referrer.'),
    'timeline': ('Sweep sorted endpoint deltas with a reference count per name; emit active names in first-input order and coalesce identical adjacent sets.', 'O(shifts log shifts + endpoints*employees) time; output-sized memory', 'Rescan every input shift across every elementary time interval.')
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (HERE/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def main():
    if any((HERE/lang).exists() for lang in ('python', 'javascript')):
        raise SystemExit('Refusing to refreeze after source authoring started')
    source = ROOT/'projects/algorithm_solver/catalogue/authored/hack2hire-worklists-20261028-v1/chunk05.txt'
    contracts, designs, teaching, blockers = [], {}, {}, []
    for index, line in enumerate(source.read_text().splitlines()):
        post, title, variants = line.split('\t'); key = KEYS[index]
        cache = ROOT/'data/question_bank/hack2hire/details'/f'{post}.json'
        raw = cache.read_bytes(); detail = json.loads(raw); preview = detail['payload']['data'].get('contentPreview') or ''
        for variant in variants.split(','):
            row = {'uid':'hack2hire:'+variant,'problemId':'hack2hire:'+post,'variant_id':variant,'source_post_id':post,'title':title,'spec_basis':'inferred','inferred_by':{'who':'Codex /root','date':datetime.now(timezone.utc).date().isoformat()},'inference_basis_fields':['bank.json group/variant identity','public payload.data.title','public payload.data.contentPreview'],'preview':{'local_cache':str(cache.relative_to(ROOT)),'cache_sha256':hashlib.sha256(raw).hexdigest(),'response_sha256':detail['response_sha256'],'content_sha256':hashlib.sha256(preview.encode()).hexdigest(),'scope':'partial group preview; no private variant body read'},'official_interface':None,'official_statement_available':False,'qualification_status':'unknown','key':key}
            if key is None:
                row.update(status='blocked',inferred_spec=None,reason=BLOCKED[index]);blockers.append({'id':row['uid'],'title':title,'reason':BLOCKED[index],'needed':'Accessible exact statement or explicit owner-supplied rules, not an invented predicate'})
            else:
                if key in FUNCTIONS:
                    name, params = FUNCTIONS[key]; interface = {'kind':'function','name':name,'params':[{'name':p,'type':'See inferred contract; exact native ABI is not source-confirmed'} for p in params]}
                else:
                    name, constructor, methods = CLASSES[key]; interface = {'kind':'class','classname':name,'constructor':{'params':constructor},'methods':methods,'transcript_adapter':'solve(operation_names, argument_lists); null constructor result'}
                row.update(status='authored-inferred-contract',inferred_spec=SPECS[key],inferred_interface=interface,inference_uncertainty='Exact hidden variant requirements, method names, domain bounds and output shape are not confirmed. Variants share this group-derived practice contract; no claim of variant equivalence.',comparison='exact typed result after lossless large-integer wire encoding',effects='Inputs and nested containers unchanged; returned mutable snapshots are independent; internal class state may mutate')
                explanation, complexity, oracle = DESIGNS[key]
                designs[variant] = {'id':row['uid'],'key':key,'candidate_design':explanation,'complexity_target':complexity,'reference':oracle,'limits':'Only bounded author-development cases are executed; full official domain/resource suitability is unknown'}
                teaching[variant] = {'constraints':['Use valid inputs described by the inferred contract; official constraints are unavailable.','Class traces are sequential; they do not prove production concurrency.','No I/O or real sleeps; all dependencies are injected or fixture-controlled.'],'clarifyingQuestions':['Does this paraphrase match the exact hidden variant?','What are the actual method signatures, bounds and ordering/error requirements?'],'assumptions':[{'spec_basis':'inferred','who':'Codex /root','date':row['inferred_by']['date'],'basis':'Public group preview only; no exact variant body'},{'text':SPECS[key]}],'hints':['First state the invariant and clarify the explicitly inferred rules.',explanation,'Test boundaries and rejected transitions before relying on the optimized data structure.'],'invariants':[SPECS[key],'Observing a result must not change earlier returned snapshots or mutate input containers.'],'chooseWhen':['Use this approach for the explicitly inferred exercise, after confirming its contract.'],'tradeoffs':['This is authored practice from a partial preview, not an official problem qualification.',complexity],'examples':[]}
            contracts.append(row)
    write('contracts.json',{'schema':'gamma.hack2hire-inferred-contracts.v1','spec_basis':'inferred','problems':contracts})
    write('design.json',designs);write('study-content.json',teaching);write('blockers.json',{'schema':'gamma.authoring-blockers.v1','variants':blockers})
    subprocess.run([sys.executable,'-m','unittest','test_oracles.py'],cwd=HERE,check=True)
    names=['contracts.json','design.json','study-content.json','oracles.py','cases.py','test_oracles.py','blockers.json']
    write('pre-source-reference-freeze.json',{'schema':'gamma.pre-source-reference-freeze.v1','at':datetime.now(timezone.utc).isoformat(),'files':{name:digest(HERE/name) for name in names},'candidate_sources_exist':False,'candidate_executions':0,'source_free_tests_passed':2,'qualification':'unknown','scope':'Author-developed references for explicit inferred contracts, not independent qualification'})
    print(json.dumps({'groups':len(KEYS),'variants':len(contracts),'authored_contracts':sum(row['key'] is not None for row in contracts),'blocked_variants':len(blockers)}))


if __name__ == '__main__':
    main()
