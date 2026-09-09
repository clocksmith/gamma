"""Fixed-opportunity ideal-cost diagnostic; never a finite archive certificate."""
import math
import struct


def ceiling_ratio(n, d):
    if n <= 0 or d <= 0:
        raise ValueError('positive ratio required')
    k = n.bit_length() - d.bit_length()
    below = n <= (d << k) if k >= 0 else (n << -k) <= d
    return k if below else k + 1


def trace_rows(data, n):
    if data[:4] != b'CLT1' or len(data) != 12 + n * 10 + 1124:
        raise ValueError('donor framing differs')
    if struct.unpack_from('<Q', data, 4)[0] != n:
        raise ValueError('donor count differs')
    rows = list(struct.iter_unpack('<BBQ', data[12:12+n*10]))
    if any(a not in (0, 1) or (not a and d) for a, d, _ in rows):
        raise ValueError('invalid donor state')
    if data[-1124:-1120] != b'CLR1':
        raise ValueError('terminal state differs')
    if struct.unpack_from('<Q',data,len(data)-1124+12)[0] != n:
        raise ValueError('terminal counter differs')
    return rows


def analyze(body, coder, donors):
    n = len(body)
    if not n or n > 151210 or len(coder) != n * 8 * 28 or len(donors) != n:
        raise ValueError('coordinate length differs')
    stats = {arm: dict(ideal_bits_saved=0.0, changed_probabilities=0,
                       correct_donors=0, thirds=[0.0, 0.0, 0.0]) for arm in ('K','D','R','S')}
    gains = {arm: [] for arm in stats}
    active = 0
    numerator = denominator = 1
    chunk_events = chunks = ceiling = 0
    for i, (enabled, donor, _) in enumerate(donors):
        if enabled not in (0,1) or not 0 <= donor <= 255:
            raise ValueError('invalid donor')
        truth_byte = body[i]
        proposed = dict(D=donor, R=body[i-1] if i else 0, S=(donor+1)&255)
        weights = {arm: [15,1] for arm in proposed}
        active += enabled
        if enabled:
            for arm,d in proposed.items(): stats[arm]['correct_donors'] += d == truth_byte
        for bit in range(8):
            row = struct.unpack_from('<7I', coder, (i*8+bit)*28)
            p, truth = row[1], row[6]
            if not 1 <= p <= 65535 or truth != ((truth_byte>>(7-bit))&1):
                raise ValueError('parent truth/count mismatch')
            parent_mass = p if truth else 65536-p
            if enabled:
                numerator *= 65535
                denominator *= parent_mass
                chunk_events += 1
                if chunk_events == 4096:
                    ceiling += ceiling_ratio(numerator,denominator)
                    chunks += 1; numerator=denominator=1; chunk_events=0
            for arm in stats:
                q = p
                if enabled and arm != 'K':
                    a,b = weights[arm]
                    expected = (proposed[arm]>>(7-bit))&1
                    # Exact byte-mixture posterior: initial parent:donor =15:1.
                    q = max(1,min(65535,(a*p+b*65536*expected+(a+b)//2)//(a+b)))
                    weights[arm] = [a*parent_mass,b*65536 if truth==expected else 0]
                mass = q if truth else 65536-q
                gain = math.log2(mass/parent_mass)
                gains[arm].append(gain)
                stats[arm]['changed_probabilities'] += q != p
                stats[arm]['thirds'][min(2,3*i//n)] += gain
    if chunk_events:
        ceiling += ceiling_ratio(numerator,denominator);chunks += 1
    for arm in stats:stats[arm]['ideal_bits_saved']=math.fsum(gains[arm])
    return dict(modeled_bytes=n,active_bytes=active,active_bits=active*8,
                perfect_probability_ideal_ceiling_bits=ceiling,
                ceiling_chunks=chunks,ceiling_chunk_events=4096,arms=stats,
                trace_truth_alignment=True,
                proof='On every fixed active event any allowed Q16 actual-bit count is at most65535. Multiply65535/parent_actual_count within fixed4096-event chunks, take exact integer log2 ceilings, and sum. Inactive events remain unchanged. This grants clairvoyant predictions and includes incorrect donors; it is not a finite-archive bound.',
                floating_point_authority='Arm gains are rounded-Q16 ideal-cost diagnostics, not exact archive savings',
                archive_saving_bytes=None,complete_package_bytes=None,objective_credit_bytes=0)
