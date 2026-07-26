# The Atlas and Clockwork Challenge

## Public problem statement

This challenge consists of two independent constructive problems over finite
binary data. A solution to either problem is complete on its own. Problem A
does not use a solution to Problem B, and Problem B does not use a solution to
Problem A.

All quantities in an instance are finite integers, finite bit strings, or
rationals represented by integer pairs. Every submitted object must be finite.
An asymptotic existence theorem is not a solution.

The organizer supplies:

- a finite binary sequence x = x_1 ... x_n;
- a partition 0 = b_0 < b_1 < ... < b_N = n;
- finite observable data available at each position;
- numerical limits and a target T;
- the exact finite-state coder defined below;
- canonical encodings for every permitted submitted object.

The blocks are I_j = {b_(j-1)+1, ..., b_j}. The problems share only this
instance and the common definitions below.

---

## 1. Exact finite-state dyadic coder

Every probability must be dyadic:

q_t(1) = a_t / 2^r,  q_t(0) = 1 - q_t(1),

where r is fixed by the instance and 1 <= a_t <= 2^r - 1.

Let the coder word width be w >= r + 3. Define

M = 2^w,  H = 2^(w-1),  Q = 2^(w-2),  U = 3Q.

The encoder state is (l, h, c), initially (0, M-1, 0), where c is the number
of pending underflow bits. For a symbol with numerator a, define

R = h - l + 1,

s = l + floor(R(2^r-a)/2^r).

For symbol 0, replace h by s-1. For symbol 1, replace l by s. Then repeatedly
apply the first applicable rule:

1. If h < H, emit 0 followed by c copies of 1, set c = 0, and replace
   (l,h) by (2l, 2h+1).
2. If l >= H, emit 1 followed by c copies of 0, set c = 0, and replace
   (l,h) by (2(l-H), 2(h-H)+1).
3. If l >= Q and h < U, increment c and replace
   (l,h) by (2(l-Q), 2(h-Q)+1).
4. Otherwise stop renormalizing and process the next symbol.

After the final symbol, increment c. If l < Q, emit 0 followed by c copies of
1. Otherwise emit 1 followed by c copies of 0.

The resulting bit string is FDAC_(w,r)(x;q).

The decoder is the exact inverse. It initializes the same interval and loads a
w-bit register from the coded payload, appending zero bits after the stated
payload length only for register initialization and renormalization. At each
step it computes the same s. It decodes 0 exactly when the register is less
than s, and otherwise decodes 1. It mirrors the selected interval and all
renormalizations, shifting in the next payload bit or a zero after the payload
ends. It stops after the externally stated n symbols.

The block version resets (l,h,c) at every block and concatenates terminated
block payloads using canonically encoded lengths. The instance states whether
the continuous or block-reset version is required.

This finite recurrence, not an ideal real interval or logarithmic surrogate,
determines the payload length.

---

## 2. Histories and admissible observables

Before position t, the public history is

H_t = (x_1, ..., x_(t-1), j, z_1, ..., z_j, omega_t),

where j is the block containing t, z_j is a paid block label if labels are
used, and omega_t contains only organizer-declared observables available
before x_t.

A probability numerator is admissible only if it is a deterministic function
of H_t, the submitted finite certificate, and the fixed instance.

A block label may depend on the entire block, but its complete codeword is
charged and made available before any payload bit whose probability uses that
label. Labels are paid side information, not hidden observations.

Two histories identical as finite strings must produce identical probability
numerators and identical next states.

---

## 3. Disjoint length accounting

For either problem, the organizer forms exactly four variable bit strings:

C = canonical submitted certificate,

Z = canonical paid labels or auxiliary choices,

Y = FDAC payload,

F = canonical framing of lengths and block boundaries.

These strings are disjoint. No bit may occur in more than one. No submitted
table, constant, label, selector, state seed, or exception may be used unless
it occurs in exactly one charged channel.

The total length is

L_total = L_fixed + |C| + |Z| + |Y| + |F|,

where L_fixed is the instance's stated constant for fixed organizer machinery.
A solution must prove L_total <= T.

---

# Problem A: The Atlas of Paid Information

## A.1 Given

In addition to the common instance, Problem A supplies:

- baseline dyadic numerators p_t in {1, ..., 2^r-1};
- observable vectors v_t over specified finite integer alphabets;
- a finite list of permitted state-register types;
- bounds B_C, B_Z, B_S, B_O, B_M;
- a target T_A.

The baseline payload Y_0 = FDAC_(w,r)(x;p) is supplied for comparison only. A
submitted construction is scored by its complete disjoint length, not ideal
log loss.

## A.2 Find

Construct all of the following finite mathematical objects:

1. A finite label alphabet Zeta, possibly the singleton alphabet.
2. A prefix-free binary code kappa on Zeta.
3. Labels z_1, ..., z_N in Zeta.
4. A finite state set S and initial state s_1.
5. A deterministic transition map
   Phi: S x O x {0,1} -> S.
6. A deterministic numerator map
   A: S x O x Zeta -> {1, ..., 2^r-1}.
7. A canonical certificate completely describing these objects.
8. A proof of the target inequality and every bound below.

At position t in I_j, use

a_t = A(s_t, omega_t, z_j),

then update only after observing the actual bit:

s_(t+1) = Phi(s_t, omega_t, x_t).

Any boundary transition declared by the instance may use only already paid
labels and completed data.

## A.3 Required inequalities

Let

C_A = Canon(Zeta, kappa, S, s_1, Phi, A),

Z_A = kappa(z_1) ... kappa(z_N),

Y_A = FDAC_(w,r)(x;a),

and let F_A be canonical framing. A valid solution must establish

L_fixed,A + |C_A| + |Z_A| + |Y_A| + |F_A| <= T_A.

It must also establish

|C_A| <= B_C,  |Z_A| <= B_Z,  |S| <= B_S,

Ops_A(x) <= B_O,  Mem_A(x) <= B_M,

using the fixed operation and memory functions supplied with the instance.

## A.4 Required proof

The proof must include:

1. Prefix condition: the label code is prefix-free and parses uniquely.
2. Causality: every a_t depends only on H_t.
3. Joint replay: two independent recurrences with the same certificate,
   labels, and reconstructed history produce the same state and numerator at
   every position.
4. Exact coding: Y_A is the Section 1 coder output, symbol by symbol.
5. Accounting: every used submitted bit belongs to exactly one of C_A, Z_A,
   Y_A, F_A.
6. Boundedness: all finite bounds are met.
7. Target: the exact integer total is at most T_A.

## A.5 Strict solution standard

A solution must give the actual finite tables, formulas, labels, recurrence,
codewords, integer lengths, and proofs. It is not enough to show existence.

Floating-point probabilities, approximate logarithms, uncharged advice,
external data, probabilistic correctness, and asymptotic savings are not
permitted.

A valid solution to Problem A is complete and does not require Problem B.

---

# Problem B: The Clockwork Realization

## B.1 Given

Problem B is independent of Problem A. It supplies its own finite teacher
system

tau_(t+1) = F*(tau_t, omega_t, x_t),

p*_t = G*(tau_t, omega_t),

together with:

- the teacher's exact initial state and certificate;
- the teacher's exact payload and complete charged length;
- a finite instruction alphabet I;
- exact integer semantics for every instruction;
- a fixed organizer interpreter for I;
- bounds B'_C, B'_S, B'_O, B'_M;
- a target T_B.

The teacher is part of the Problem B instance. It is not produced by, selected
by, or derived from Problem A.

The instruction alphabet may contain only operations explicitly listed in the
instance, such as bounded addition, subtraction, multiplication, shift,
comparison, selection, table lookup, permutation, clamping, and fixed-shape
integer contraction. Overflow, rounding, saturation, and division semantics
are fixed by the instance.

## B.2 Find

Construct a finite clockwork

Ck = (U, u_1, F_hat, G_hat),

where U is a finite bounded-integer state space, u_1 is explicit, and F_hat
and G_hat are finite instruction sequences implementing

u_(t+1) = F_hat(u_t, omega_t, x_t),

a_hat,t = G_hat(u_t, omega_t) in {1, ..., 2^r-1}.

The clockwork may approximate, reorganize, or replace the teacher. It is judged
only by exact finite coding length, exact reconstruction, and the supplied
resource bounds.

Problem B permits no Atlas labels or Atlas certificate. If the Problem B
instance supplies its own auxiliary selector channel, it is charged
independently as Z_B; otherwise Z_B is empty.

## B.3 Required inequalities

Let

C_B = Canon(U, u_1, F_hat, G_hat),

Y_B = FDAC_(w,r)(x;a_hat),

and let F_B be canonical framing. A valid solution must establish

L_fixed,B + |C_B| + |Z_B| + |Y_B| + |F_B| <= T_B.

It must also establish

|C_B| <= B'_C,

StateBits(U) <= B'_S,

Ops_B(x) <= B'_O,  Mem_B(x) <= B'_M.

Any teacher comparison must use the exact global integer difference

Delta L = (|C_B| + |Z_B| + |Y_B| + |F_B|) - L_teacher.

A per-position log-loss trace may be submitted as a diagnostic, but it is not
an additive decomposition of FDAC output bytes and cannot replace the exact
global calculation.

## B.4 Required proof

The proof must include:

1. Instruction legality under I and its exact integer semantics.
2. Closure of every reachable state in U.
3. Causality of every a_hat,t.
4. Joint replay for identical reconstructed histories.
5. Exact production of Y_B by the Section 1 coder.
6. Exactly-once accounting of every submitted bit.
7. Exact satisfaction of state, operation, and memory bounds.
8. The complete integer target inequality.

## B.5 Strict solution standard

A solution must submit the explicit bounded-integer state representation,
instruction sequences, constants, tables, and proofs.

An existence argument, floating-point simulation, average-case operation
claim, unbounded integer computation, hidden table, external model, or
probabilistic replay is not a solution.

A valid solution to Problem B is complete and does not require Problem A.

---

# 4. Independence theorem

Let Pass_A mean that every condition of Problem A holds, and Pass_B mean that
every condition of Problem B holds. The challenge acceptance condition is

Pass_A OR Pass_B.

The organizer must be able to verify Atlas without loading, executing, or
assuming Clockwork, and Clockwork without loading, executing, or assuming
Atlas.

A contestant may submit both, but neither may cite the other as a lemma,
certificate, data source, state initializer, or accounting credit.
