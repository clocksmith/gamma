"""Independent abstract state models; never import or execute candidate sources."""
from copy import deepcopy
import random

IDS = (3709, 3815, 3829)
CLASSES = {3709: 'ExamTracker', 3815: 'AuctionSystem', 3829: 'RideSharingSystem'}
METHODS = {
    3709: {'record': 2, 'totalScore': 2},
    3815: {'addBid': 3, 'updateBid': 3, 'removeBid': 2, 'getHighestBidder': 1},
    3829: {'addRider': 1, 'addDriver': 1, 'matchDriverWithRider': 0, 'cancelRider': 1},
}


def integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def validate(pid, args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args) != 2:
        raise ValueError('exact assigned identity and two trace arguments required')
    operations, arguments = args
    maximum = {3709: 100000, 3815: 50000, 3829: 1000}[pid]
    if (type(operations) is not list or type(arguments) is not list or
            not 1 <= len(operations) <= maximum + 1 or len(arguments) != len(operations) or
            operations[0] != CLASSES[pid] or arguments[0] != [] or type(arguments[0]) is not list):
        raise ValueError('one initial empty constructor and bounded parallel trace lists required')
    latest = 0
    bids = set()
    riders_added, drivers_added = set(), set()
    for index, (operation, row) in enumerate(zip(operations[1:], arguments[1:]), 1):
        if (type(operation) is not str or operation not in METHODS[pid] or
                type(row) is not list or len(row) != METHODS[pid][operation]):
            raise ValueError('exact native method and ordered arguments required')
        if pid == 3709:
            if operation == 'record':
                if not integer(row[0], latest + 1, 10**9) or not integer(row[1], 1, 10**9):
                    raise ValueError('strictly increasing record time and bounded score required')
                latest = row[0]
            elif index == 1 or not integer(row[0], 1, latest) or not integer(row[1], row[0], latest):
                raise ValueError('record must precede inclusive nonfuture query')
        elif pid == 3815:
            if not all(integer(x, 1, 50000) for x in row[:min(2, len(row))]):
                raise ValueError('bounded exact user/item identity required')
            if operation in ('addBid', 'updateBid') and not integer(row[2], 1, 10**9):
                raise ValueError('bounded exact bid amount required')
            if operation != 'getHighestBidder':
                key = (row[1], row[0])
                if operation in ('updateBid', 'removeBid') and key not in bids:
                    raise ValueError('update/remove requires an existing bid')
                if operation == 'removeBid': bids.remove(key)
                else: bids.add(key)
        else:
            if row and not integer(row[0], 1, 1000):
                raise ValueError('bounded exact rider/driver identity required')
            if operation in ('addRider', 'addDriver'):
                added = riders_added if operation == 'addRider' else drivers_added
                if row[0] in added: raise ValueError('identity may be added at most once per role')
                added.add(row[0])


def reference(pid, args):
    """Scan records, scan item bids, or mutate short literal FIFO lists.

    These direct models intentionally do not share candidates' prefix searches,
    lazy heaps, or queue cursors. They run on bounded development traces only.
    """
    validate(pid, args)
    if len(args[0]) > 501:
        raise ValueError('reference work bound exceeded; domain remains separately valid')
    output = [None]
    records, bids, riders, drivers = [], {}, [], []
    for operation, row in zip(args[0][1:], args[1][1:]):
        value = None
        if pid == 3709:
            if operation == 'record': records.append(tuple(row))
            else: value = sum(score for time, score in records if row[0] <= time <= row[1])
        elif pid == 3815:
            if operation in ('addBid', 'updateBid'): bids[row[1], row[0]] = row[2]
            elif operation == 'removeBid': del bids[row[1], row[0]]
            else:
                available = [(amount, user) for (item, user), amount in bids.items() if item == row[0]]
                value = max(available)[1] if available else -1
        else:
            if operation == 'addRider': riders.append(row[0])
            elif operation == 'addDriver': drivers.append(row[0])
            elif operation == 'cancelRider': riders = [rider for rider in riders if rider != row[0]]
            else: value = [drivers.pop(0), riders.pop(0)] if drivers and riders else [-1, -1]
        output.append(value)
    return output


def exact(left, right):
    if type(left) is not type(right): return False
    if type(left) is list:
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def check_observation(pid, args, observed, expected):
    """Value/effect checks for a prospective trace observer, not an execution receipt."""
    validate(pid, args)
    if type(observed) is not dict: return 'record_shape'
    if observed.get('error') is not None: return 'candidate_error'
    if not exact(observed.get('result'), expected): return 'result_value'
    if not exact(observed.get('args_before'), args) or not exact(observed.get('args_after'), args):
        return 'input_effects'
    if observed.get('alias_edges') != []: return 'return_aliases'
    return None


def generate_cases(pid):
    """Official examples are supplied independently by definition-bound contracts.

    This generator creates small lawful state-transition traces only, not a
    qualification archive. No expected values enter any candidate process.
    """
    rng = random.Random(202610280000 + pid)
    cases = []
    for trial in range(48):
        operations, rows = [CLASSES[pid]], [[]]
        latest, live = 0, set()
        rider, driver = 0, 0
        for step in range(60):
            if pid == 3709:
                if not latest or rng.randrange(3) == 0:
                    latest += rng.randrange(1, 7)
                    operations.append('record'); rows.append([latest, rng.choice([1, 10**9, rng.randrange(1, 1000)])])
                else:
                    low = rng.randrange(1, latest + 1)
                    operations.append('totalScore'); rows.append([low, rng.randrange(low, latest + 1)])
            elif pid == 3815:
                choice = rng.randrange(4)
                if choice in (1, 2) and live:
                    item, user = sorted(live)[rng.randrange(len(live))]
                    if choice == 1:
                        operations.append('updateBid'); rows.append([user, item, rng.choice([1, 10**9, 7])])
                    else:
                        operations.append('removeBid'); rows.append([user, item]); live.remove((item, user))
                elif choice == 3:
                    operations.append('getHighestBidder'); rows.append([rng.randrange(1, 5)])
                else:
                    user, item = rng.randrange(1, 8), rng.randrange(1, 5)
                    operations.append('addBid'); rows.append([user, item, rng.choice([1, 10**9, 7])]); live.add((item, user))
            else:
                choice = rng.randrange(4)
                if choice == 0:
                    rider += 1; operations.append('addRider'); rows.append([rider])
                elif choice == 1:
                    driver += 1; operations.append('addDriver'); rows.append([driver])
                elif choice == 2:
                    operations.append('cancelRider'); rows.append([rng.randrange(1, max(rider, 1) + 1)])
                else:
                    operations.append('matchDriverWithRider'); rows.append([])
        args = [operations, rows]
        cases.append({'args': deepcopy(args), 'expected': reference(pid, args), 'compare': 'return'})
    return cases
