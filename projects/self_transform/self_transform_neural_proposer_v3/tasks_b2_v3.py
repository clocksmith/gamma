"""Four brand-new unseen confirmation families for Track B2 v3 (`self_transform_neural_proposer_v3`).

Families (100% disjoint from ALL `v1` and `v2` confirmation families):
1. `real_qwen35_swiglu_lora_cls`:
   Tokenizes real multi-domain English text prompts with the locally provisioned stock
   `Qwen/Qwen3.5-0.8B` (`2fc0636`) tokenizer, embeds through real `model.language_model.embed_tokens.weight`,
   normalizes with real `layers.23.post_attention_layernorm.weight`, runs through the real full-width
   `1024 -> 3584 -> 1024` Layer-23 SwiGLU MLP (`gate_proj`, `up_proj`, `down_proj`), and adapts a
   full-width rank-`12` LoRA `(A_down, B_down=0)` into the real `model.language_model.norm.weight` +
   frozen `embed_tokens` unembedding readout over task-permuted codeword tokens in `B = 10` support
   passes—testing prompt-removed skill retention on unseen prompt-free queries.
2. `fourier_kan_multifreq_reg`:
   Multi-frequency `[sin(X W_sin^T), cos(X W_cos^T), SiLU(X W_res^T)] -> W_mix -> SiLU -> W_out`
   regression (co-primary metrics: held-out `R^2` and MSE).
3. `bilinear_gated_interaction_cls`:
   Two-stage multiplicative bilinear interaction `(W_a x) * tanh(W_b x)` classifier under anisotropic
   inputs and label noise (co-primary metrics: held-out accuracy and cross-entropy).
4. `layernorm_residual_gelu_cls`:
   Pre-LayerNorm 3-block residual deep GELU classifier under ill-conditioned feature covariance
   (co-primary metrics: held-out accuracy and cross-entropy).
"""
from __future__ import annotations

import math
from pathlib import Path
import sys
from typing import Any
import torch
import torch.nn.functional as F

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from baselines_v3 import (
    NeuralTargetTaskV3,
    _anisotropic_inputs,
    _rand_init_matrix,
    forward_target_v3,
)

QWEN35_LOCAL_DIR = Path("/Users/xyz/deco/valera/generated/hf-models/Qwen-Qwen3.5-0.8B-2fc0636")
QWEN35_SAFETENSORS_FILE = QWEN35_LOCAL_DIR / "model.safetensors-00001-of-00001.safetensors"

V3_CONFIRMATION_FAMILIES = (
    "real_qwen35_swiglu_lora_cls",
    "fourier_kan_multifreq_reg",
    "bilinear_gated_interaction_cls",
    "layernorm_residual_gelu_cls",
)

FORBIDDEN_PRIOR_FAMILIES = frozenset({
    "unseen_swiglu_3layer_cls",
    "unseen_bottleneck_4layer_reg",
    "unseen_fastweight_adapter_bridge",
    "unseen_deep_elu_5layer_cls",
})
assert FORBIDDEN_PRIOR_FAMILIES.isdisjoint(V3_CONFIRMATION_FAMILIES)

VERBALIZER_WORDS = (
    " alpha",
    " beta",
    " gamma",
    " delta",
    " omega",
    " sigma",
    " north",
    " south",
    " east",
    " west",
)

# 12 distinct technical/scientific domains x 20 natural sentences = 240 natural English prompts
QWEN35_DOMAIN_CORPUS: dict[str, tuple[str, ...]] = {
    "graph_algorithms": (
        "Breadth-first traversal visits graph vertices in order of unweighted hop distance.",
        "Red-black trees guarantee logarithmic insertion and deletion via rotation invariants.",
        "Kruskal minimum spanning tree sorts edges and merges disjoint union-find sets.",
        "Topological sorting orders directed acyclic graph nodes so every edge points forward.",
        "Aho-Corasick automata match multiple pattern strings in a single linear scan.",
        "Tarjan strongly connected components algorithm tracks discovery times on a DFS stack.",
        "Dynamic programming solves knapsack optimization over capacity and item prefix states.",
        "Binary heap priority queues extract the minimum element in logarithmic comparisons.",
        "Suffix arrays enable fast substring queries using longest common prefix intervals.",
        "Floyd-Warshall relaxes all intermediate vertices to compute all-pairs shortest paths.",
        "Fenwick binary indexed trees maintain prefix sums under point updates efficiently.",
        "Hopcroft-Karp finds maximum cardinality matchings in bipartite graphs via augmenting paths.",
        "Segment trees answer range minimum queries with lazy propagation in logarithmic time.",
        "Rabin-Karp rolling polynomial hashes detect repeated substring collisions quickly.",
        "Bellman-Ford detects reachable negative weight cycles after V minus one relaxations.",
        "Convex hull Graham scan sorts planar points by polar angle around the lowest anchor.",
        "Dijkstra shortest path relaxes outgoing edges from the nearest settled frontier node.",
        "Edmonds-Karp bounds Ford-Fulkerson max-flow augmentations using shortest BFS paths.",
        " Kosaraju two-pass depth-first search isolates strongly connected directed subgraphs.",
        "Trie prefix trees share character transitions across dictionary words for autocomplete.",
    ),
    "relational_databases": (
        "Write-ahead redo logs ensure crash recovery durability before dirty pages flush.",
        "Multiversion concurrency control isolates snapshot readers from concurrent row updates.",
        "Hash join partitions build relations into in-memory buckets before probing stream rows.",
        "Clustered B-plus tree indexes store leaf records sequentially in primary key order.",
        "Two-phase commit coordinates distributed transaction prepare and commit votes atomically.",
        "Materialized views precompute expensive group-by aggregations for analytical dashboards.",
        "Columnar Parquet storage compresses repeated attribute values with dictionary encoding.",
        "Query optimizers estimate join cardinality from equi-depth histograms and distinct counts.",
        "Serializable snapshot isolation aborts read-write anti-dependency cycles between transactions.",
        "Buffer pool clock replacement evicts unpinned cold pages from shared memory frames.",
        "Bloom filters skip immutable LSM-tree SSTables that lack a queried lookup key.",
        "Foreign key cascading deletes preserve referential integrity across normalized relational tables.",
        "Covering secondary indexes satisfy projection queries without heap tuple lookups.",
        "Window functions compute sliding partition rankings without collapsing detail rows.",
        "Logical replication streams row-level WAL changes to read-replica subscribers.",
        "Point-in-time recovery replays archived write-ahead segments onto a base physical backup.",
        "Sort-merge joins scan pre-ordered index streams linearly without hash memory overhead.",
        "Third normal form eliminates transitive functional dependencies on non-prime attributes.",
        "Deadlock detectors inspect lock wait-for graphs and roll back the youngest victim.",
        "ARIES recovery repeats history during redo before undoing loser transactions backward.",
    ),
    "computer_graphics": (
        "Physically based metallic-roughness shaders evaluate microfacet specular reflectance lobes.",
        "Shadow mapping compares fragment light-space depth against a rendered depth texture.",
        "Screen-space ambient occlusion approximates crease darkening from normal-oriented depth samples.",
        "Bounding volume hierarchies accelerate ray-triangle intersection queries in path tracing.",
        "Mipmap trilinear filtering blends adjacent texture levels to prevent minification aliasing.",
        "Deferred shading decouples geometry buffer rasterization from per-light illumination passes.",
        "Half-edge polygon meshes support constant-time adjacency traversal for Catmull-Clark subdivision.",
        "Quaternion spherical linear interpolation animates skeletal joint rotations without gimbal lock.",
        "Frustum culling discards bounding boxes outside the six clip-space camera planes.",
        "Compute shader tile binning culls point lights per sixteen-by-sixteen pixel workgroup.",
        "Temporal anti-aliasing jitters subpixel projection matrices and clamps neighborhood history.",
        "Signed distance fields raymarch smooth constructive solid geometry blends cleanly.",
        "Normal mapping perturbs tangent-space surface orientation for high-frequency lighting detail.",
        "Dual-source alpha blending composites colored glass transmission in a single render pass.",
        "Tessellation control shaders adaptively subdivide terrain patches by camera distance.",
        "Importance sampling concentrates Monte Carlo environment rays toward bright sky regions.",
        "Barycentric perspective-correct interpolation divides vertex attributes by homogeneous clip W.",
        "Cascaded shadow maps allocate higher texel density near the viewer camera frustum.",
        "Octree sparse voxel global illumination traces indirect diffuse bounce cones efficiently.",
        " Tone mapping compresses high dynamic range linear radiance into displayable sRGB gamut.",
    ),
    "network_protocols": (
        "TCP congestion control halves the congestion window on duplicate triple acknowledgments.",
        "BGP path-vector routing exchanges autonomous system reachability prefixes over port 179.",
        "TLS ephemeral elliptic-curve key exchange provides forward secrecy in one round trip.",
        "QUIC multiplexes independent encrypted byte streams over UDP without head-of-line blocking.",
        "ARP broadcast requests resolve IPv4 subnet addresses into link-layer Ethernet MACs.",
        "DNS authoritative name servers return signed DNSSEC resource record sets with signatures.",
        "OSPF link-state advertisements flood topological costs to run shortest-path trees per area.",
        "NAT port mapping translates private internal sockets to a public egress IPv4 tuple.",
        "Token bucket traffic shapers bound burst size while enforcing sustained bitrates.",
        "Explicit congestion notification marks packet headers before router queue tail drop.",
        "Anycast routing steers client packets to the topologically nearest edge datacenter.",
        "HTTP header compression indexes frequent request metadata fields in dynamic tables.",
        "Consistent hashing rings minimize cache key remapping when backend nodes join or leave.",
        "VLAN tags isolate layer-two broadcast domains across shared trunk switch ports.",
        "Selective acknowledgment options let receivers report non-contiguous TCP byte segments.",
        "WireGuard authenticates peer tunnels with ChaCha20-Poly1305 cryptographic handshakes.",
        "Spanning tree protocol blocks redundant bridge loops by electing a root switch.",
        "ICMP time-exceeded replies reveal intermediate router hops during traceroute probes.",
        "Multicast IGMP snooping prunes flood traffic on switch ports without subscribed listeners.",
        "Sliding receive windows advertise available socket buffer bytes for flow control.",
    ),
    "molecular_biology": (
        "Ribosomes translate messenger RNA codons into polypeptide chains using charged transfer RNAs.",
        "CRISPR endonucleases cleave target genomic DNA upstream of protospacer adjacent motifs.",
        "Mitochondrial ATP synthase couples proton chemiosmotic gradients to oxidative phosphorylation.",
        "DNA polymerase synthesizes Okazaki fragments discontinuously along the lagging replication strand.",
        "Alternative splicing excises introns in distinct exon combinations to diversify protein isoforms.",
        "Voltage-gated sodium channels propagate depolarizing action potentials down myelinated axons.",
        "Chaperonin complexes sequester misfolded polypeptides inside hydrophilic folding cages.",
        "Histone lysine acetylation relaxes chromatin nucleosome packing to activate gene transcription.",
        "Photosystem II splits water molecules to drive linear electron transport in thylakoid membranes.",
        "Monoclonal antibodies bind conformational epitopes via hypervariable complementarity loops.",
        "Telomerase reverse transcriptase extends repetitive hexanucleotide chromosome ends in stem cells.",
        "Ubiquitin ligases tag damaged cytosolic proteins for proteasomal degradation.",
        "Allosteric enzyme inhibitors stabilize inactive subunit conformations reversibly.",
        "Meiotic homologous recombination exchanges chromatid segments at chiasmata during prophase.",
        "G-protein coupled receptors exchange GDP for GTP upon extracellular ligand binding.",
        "Restriction endonucleases recognize palindromic nucleotide sequences and leave sticky overhangs.",
        "RNA interference RISC complexes cleave complementary transcripts guided by short siRNAs.",
        "Citric acid cycle dehydrogenases reduce NAD and FAD cofactors inside the mitochondrial matrix.",
        "Aquaporin tetramers selectively conduct water molecules across osmotic plasma membranes.",
        "DNA helicase unwinds double-stranded base pairs ahead of the advancing replication fork.",
    ),
    "thermodynamics_quantum": (
        "Carnot heat engine efficiency depends solely on hot and cold reservoir Kelvin temperatures.",
        "Faraday electromagnetic induction generates electromotive force proportional to magnetic flux change.",
        "Pauli exclusion forbids two identical fermions from occupying the same quantum state.",
        "Noether theorem links continuous Lagrangian symmetries to conserved physical currents.",
        "Compton scattering shifts X-ray photon wavelengths after elastic electron collisions.",
        "Lorentz transformations preserve spacetime interval invariance across inertial reference frames.",
        "Bose-Einstein condensates macroscopically populate the ground state below critical temperature.",
        "Navier-Stokes equations govern viscous incompressible fluid momentum conservation and vorticity.",
        "Bragg diffraction constructively interferes crystal lattice reflections at integer path multiples.",
        "Meissner effect expels magnetic flux lines from superconductors below critical temperature.",
        "Planck blackbody spectral radiance resolves the ultraviolet catastrophe via quantized oscillators.",
        "Hall voltage develops transversely across current-carrying conductors in perpendicular magnetic fields.",
        "Tunneling transmission decays exponentially with barrier width and square root barrier height.",
        "Maxwell-Boltzmann speed distributions widen as ideal gas kinetic temperature increases.",
        "Gibbs free energy change determines chemical reaction spontaneity at constant temperature and pressure.",
        "Heisenberg uncertainty bounds simultaneous position and momentum wavepacket standard deviations.",
        "Joule-Thomson throttling expands real gases at constant enthalpy across porous plugs.",
        "Fermi-Dirac statistics govern degenerate electron gas occupancy in metallic conduction bands.",
        "Clausius-Clapeyron relation connects vapor pressure slope to latent heat of phase transition.",
        "Aharonov-Bohm phase shifts electron interference fringes around enclosed magnetic solenoid flux.",
    ),
    "compiler_design": (
        "Static single assignment form inserts phi nodes at control-flow dominance frontiers.",
        "Chaitin graph coloring spills high-degree live intervals when physical registers run out.",
        "LR shift-reduce parsers consult action and goto tables built from canonical item sets.",
        "Dead code elimination removes side-effect-free instructions whose SSA values have zero uses.",
        "Loop-invariant code motion hoists constant expressions into the dominating loop preheader.",
        "Escape analysis allocates non-escaping object structs on the stack frame instead of heap.",
        "Strength reduction replaces induction-variable integer multiplications with pointer additions.",
        "Tail-call optimization reuses the caller activation frame for final recursive jumps.",
        "Peephole optimizers substitute short adjacent machine-instruction sequences with faster idioms.",
        "Alias analysis proves non-overlapping pointer targets so load-store reordering stays sound.",
        "Hindley-Milner type inference unifies polymorphic type variables across let-bound expressions.",
        "Polyhedral loop tiling partitions nested array stencils for L1 data-cache locality.",
        "Lexical scanners compile regular-expression token rules into minimal deterministic automata.",
        "Inline expansion eliminates function call prologue overhead and exposes constant arguments.",
        "Common subexpression elimination reuses previously computed value numbers across basic blocks.",
        "Tracing garbage collectors mark reachable object graphs from stack and register roots.",
        "Instruction scheduling hides pipeline latency by interleaving independent arithmetic ops.",
        "Abstract syntax trees strip concrete punctuation tokens before semantic scope resolution.",
        "Copy propagation replaces redundant variable assignments prior to dead store cleanup.",
        "Profile-guided branch placement aligns hot fallthrough paths for instruction cache prefetching.",
    ),
    "cryptography_security": (
        "Diffie-Hellman key agreement relies on discrete logarithm hardness in prime cyclic groups.",
        "AES block ciphers iterate SubBytes, ShiftRows, MixColumns, and round key XOR transformations.",
        "HMAC nested key padding prevents Merkle-Damgard length-extension forgery attacks.",
        "RSA signatures exponentiate message digests modulo a product of two secret large primes.",
        "Authenticated Galois Counter Mode combines counter-mode encryption with polynomial MAC tags.",
        "Argon2 memory-hard password hashing resists custom ASIC brute-force cracking arrays.",
        "Zero-knowledge Schnorr proofs convince verifiers of discrete log knowledge without leakage.",
        "Shamir secret sharing reconstructs finite-field polynomials from threshold Lagrange shares.",
        "Certificate transparency append-only Merkle trees audit rogue TLS certificate issuance.",
        "Constant-time bitwise arithmetic eliminates cache-timing side channels in scalar multiplication.",
        "Ed25519 twisted Edwards curve signatures derive deterministic nonces from secret hashes.",
        " Kerberos ticket-granting servers issue time-bounded session keys for mutual authentication.",
        "Address space layout randomization randomizes stack, heap, and shared library base offsets.",
        "Stack canaries detect contiguous buffer overflow overwrites before function return jumps.",
        "Homomorphic lattice encryption permits arithmetic evaluation directly on noisy ciphertexts.",
        "HKDF extract-and-expand derives independent cryptographic subkeys from high-entropy secrets.",
        "Elliptic curve point addition computes chord-and-tangent group laws over prime finite fields.",
        "Digital envelope encryption wraps bulk symmetric data keys under recipient public keys.",
        "Replay protection sliding bitmasks reject duplicate sequence numbers in IPsec ESP packets.",
        "Content security policy headers restrict untrusted inline script execution in web browsers.",
    ),
    "operating_systems": (
        "Hierarchical multi-level page tables translate virtual addresses using hardware TLB caches.",
        "Copy-on-write fork shares read-only physical page frames until either process writes.",
        "Completely fair schedulers track per-thread virtual runtime inside a red-black timeline.",
        "Futex fast userspace mutexes avoid kernel context switches when lock contention is absent.",
        "Demand paging faults missing virtual pages from swap storage into newly allocated frames.",
        "Interrupt top halves acknowledge hardware controllers quickly and defer work to softirqs.",
        " Slab allocators cache pre-initialized kernel object pools to reduce internal fragmentation.",
        "Read-copy-update allows lockless concurrent readers while deferring reclamation past grace periods.",
        "Inode metadata blocks store POSIX file permissions, link counts, and extent pointers.",
        "Priority inheritance boosts lock-holding low-priority threads to prevent priority inversion.",
        "Direct memory access engines transfer NVMe block payloads without polling CPU intervention.",
        "Virtual file system switch layers dispatch unified open and read calls across filesystems.",
        "Memory-mapped mmap regions back process address ranges directly with page-cache frames.",
        "Epoll readiness queues notify event loops of non-blocking socket descriptors in O(1) time.",
        " Banker resource-allocation checks prevent circular wait deadlocks before granting claims.",
        "Context switches save callee-saved registers and swap page-table base control registers.",
        "Buddy physical page allocators split and coalesce power-of-two contiguous frame blocks.",
        "POSIX unnamed pipes stream unidirectional byte ring buffers between parent and child processes.",
        "Journaled ext4 filesystems commit metadata transaction blocks before updating live bitmaps.",
        "Control groups throttle per-container CPU bandwidth shares and resident memory ceilings.",
    ),
    "macroeconomics_finance": (
        "Black-Scholes option pricing hedges lognormal underlying asset diffusion continuously.",
        "Yield curve inversions occur when short-term treasury rates exceed long-maturity yields.",
        "Purchasing power parity equates exchange rates to relative domestic price-level baskets.",
        "Central bank open-market operations adjust commercial bank reserves to steer overnight rates.",
        "Duration measures fixed-income bond price sensitivity to parallel interest-rate shifts.",
        "Comparative advantage raises bilateral trade welfare when opportunity costs differ across goods.",
        "Taylor rules prescribe nominal policy rate adjustments to inflation and output gaps.",
        "Convexity captures second-order curvature in bond price responses to large yield changes.",
        "Fractional-reserve deposit creation multiplies monetary base injections through lending cycles.",
        "Capital asset pricing models relate expected equity excess return to market covariance beta.",
        "IS-LM equilibrium intersects goods-market investment saving with money-demand liquidity curves.",
        "Covered interest parity eliminates riskless forward foreign-exchange arbitrage differentials.",
        "Value at risk estimates portfolio loss quantiles over a fixed holding horizon.",
        "Automatic fiscal stabilizers dampen disposable income swings across business-cycle contractions.",
        "Modigliani-Miller theorem shows firm value invariance to leverage without taxes or bankruptcy.",
        "sticky nominal wages generate short-run Phillips curve tradeoffs between inflation and unemployment.",
        "Sharpe ratios normalize active portfolio excess returns by realized return volatility.",
        "Ricardian equivalence offsets debt-financed government spending with higher private saving.",
        " Solow growth models converge toward steady-state capital per effective worker under depreciation.",
        "Put-call parity links European call and put option premiums at identical strike and expiry.",
    ),
    "astrophysics_orbital": (
        "Kepler third law relates orbital period squared to semi-major axis cubed.",
        "Chandrasekhar electron degeneracy pressure caps stable white-dwarf mass near 1.4 solar masses.",
        "Hohmann transfer ellipses minimize two-impulse delta-v between coplanar circular orbits.",
        "Main-sequence stars fuse core hydrogen into helium via proton-proton or CNO cycles.",
        "Schwarzschild event horizons trap outgoing null geodesics inside radius 2GM over c squared.",
        "Gravitational microlensing transiently magnifies background starlight passing massive compact halos.",
        "Type Ia thermonuclear supernovae calibrate extragalactic luminosity distances as standardizable candles.",
        "Roche limits mark tidal disruption radii for fluid satellites orbiting massive primaries.",
        "Cosmic microwave background acoustic peaks constrain baryon density and spatial curvature.",
        "Virial equilibrium equates twice time-averaged kinetic energy to negative gravitational potential.",
        "Synchrotron radio emission arises from relativistic electrons spiraling in galactic magnetic fields.",
        "Lagrange liberation points balance two-body gravitational attraction against rotating centrifugal force.",
        "Rosseland mean opacity governs radiative energy transport through stellar interior envelopes.",
        "Core-collapse neutron stars conserve angular momentum to spin as magnetized radio pulsars.",
        "Jeans instability triggers molecular cloud collapse when self-gravity exceeds thermal pressure.",
        "Oberth maneuvers maximize kinetic energy gain by burning propellant at periapsis.",
        "Tully-Fisher relations correlate spiral galaxy intrinsic luminosity with flat rotation velocity.",
        "Eddington luminosity balances outward Thomson radiation pressure against inward stellar gravity.",
        "Precession of Mercury perihelion confirms general-relativistic spacetime curvature near the Sun.",
        " Lyman-alpha absorption forests trace neutral intergalactic hydrogen filaments along quasar sightlines.",
    ),
    "numerical_linear_algebra": (
        "Householder reflections zero subdiagonal column entries orthogonal-stably during QR factorization.",
        "Conjugate gradient iterations minimize symmetric positive-definite quadratics over Krylov subspaces.",
        "Cholesky decomposition factors symmetric positive-definite matrices into lower-triangular L L-transpose.",
        "Power iteration converges toward the dominant eigenvector at rate governed by eigenvalue gap.",
        "Singular value decomposition expresses rectangular matrices via orthogonal left and right bases.",
        "Tikhonov ridge regularization damps ill-conditioned small singular values in inverse problems.",
        "GMRES orthogonalizes Arnoldi Krylov bases using Givens rotations for nonsymmetric linear systems.",
        "Gaussian elimination with partial row pivoting bounds growth of LU multiplier magnitudes.",
        "Jacobi preconditioners rescale diagonal entries to accelerate iterative solver convergence.",
        "Lanczos tridiagonalization approximates extreme eigenvalues of large sparse symmetric matrices.",
        "Condition number kappa bounds relative solution sensitivity to right-hand-side perturbations.",
        "Strassen block recursion multiplies dense matrices in subcubic O(n to the 2.81) operations.",
        "Modified Gram-Schmidt reorthogonalizes basis vectors sequentially to curb cancellation loss.",
        "Sherman-Morrison-Woodbury formulas update inverse matrices efficiently after low-rank perturbations.",
        "Rayleigh quotient iteration achieves cubic convergence to symmetric matrix eigenpairs.",
        " Gershgorin discs bound complex matrix eigenvalues within row-sum off-diagonal circles.",
        "Incomplete LU factorizations drop fill-in entries to precondition sparse linear solvers.",
        "Eckart-Young theorem proves truncated SVD minimizes Frobenius low-rank approximation error.",
        "Bidiagonal Golub-Kahan SVD steps chase unwanted nonzero bulges with orthogonal Givens sweeps.",
        "chebyshev polynomial acceleration bounds spectral error across known eigenvalue intervals.",
    ),
}

_QWEN35_PROCESS_CACHE: dict[str, Any] | None = None


def load_real_qwen35_components(allow_synthetic_fallback: bool = False) -> dict[str, Any]:
    """Load stock `Qwen/Qwen3.5-0.8B` (`2fc0636`) tokenizer + Layer-23 SwiGLU + norms + embeddings."""
    global _QWEN35_PROCESS_CACHE
    if _QWEN35_PROCESS_CACHE is not None and _QWEN35_PROCESS_CACHE["is_real"]:
        return _QWEN35_PROCESS_CACHE

    if QWEN35_SAFETENSORS_FILE.exists():
        from safetensors import safe_open
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(str(QWEN35_LOCAL_DIR), local_files_only=True)
        with safe_open(str(QWEN35_SAFETENSORS_FILE), framework="pt", device="cpu") as f:
            emb = f.get_tensor("model.language_model.embed_tokens.weight").float()
            ln23 = f.get_tensor("model.language_model.layers.23.post_attention_layernorm.weight").float()
            wg = f.get_tensor("model.language_model.layers.23.mlp.gate_proj.weight").float()
            wu = f.get_tensor("model.language_model.layers.23.mlp.up_proj.weight").float()
            wd = f.get_tensor("model.language_model.layers.23.mlp.down_proj.weight").float()
            lnf = f.get_tensor("model.language_model.norm.weight").float()

        assert emb.shape == (248320, 1024), f"Unexpected Qwen3.5 embed shape: {emb.shape}"
        assert wg.shape == (3584, 1024) and wu.shape == (3584, 1024) and wd.shape == (1024, 3584)
        _QWEN35_PROCESS_CACHE = {
            "is_real": True,
            "tokenizer": tok,
            "embed_tokens": emb,
            "ln23_weight": ln23,
            "gate_proj": wg,
            "up_proj": wu,
            "down_proj": wd,
            "norm_weight": lnf,
        }
        return _QWEN35_PROCESS_CACHE

    if not allow_synthetic_fallback:
        raise FileNotFoundError(
            f"Provisioned Qwen/Qwen3.5-0.8B checkpoint required at {QWEN35_SAFETENSORS_FILE} "
            "(confirmation runs forbid synthetic fallback)."
        )

    # Offline CI fallback ONLY when explicitly requested in unit tests without local checkpoint
    gen = torch.Generator(device="cpu").manual_seed(7777)
    d_model, d_ff, vocab = 128, 256, 4096
    emb = (1.0 / math.sqrt(d_model)) * torch.randn((vocab, d_model), generator=gen, dtype=torch.float32)
    ln23 = 0.25 * torch.ones(d_model, dtype=torch.float32)
    wg = (1.0 / math.sqrt(d_model)) * torch.randn((d_ff, d_model), generator=gen, dtype=torch.float32)
    wu = (1.0 / math.sqrt(d_model)) * torch.randn((d_ff, d_model), generator=gen, dtype=torch.float32)
    wd = (1.0 / math.sqrt(d_ff)) * torch.randn((d_model, d_ff), generator=gen, dtype=torch.float32)
    lnf = 2.5 * torch.ones(d_model, dtype=torch.float32)

    class _HashTok:
        def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
            return [(sum(ord(c) * (idx + 1) for idx, c in enumerate(w)) % (vocab - 32)) + 32 for w in text.split()]

    return {
        "is_real": False,
        "tokenizer": _HashTok(),
        "embed_tokens": emb,
        "ln23_weight": ln23,
        "gate_proj": wg,
        "up_proj": wu,
        "down_proj": wd,
        "norm_weight": lnf,
    }


def _build_real_qwen35_swiglu_lora_task(
    seed: int,
    dtype: torch.dtype = torch.float64,
    allow_synthetic_qwen_fallback: bool = False,
) -> NeuralTargetTaskV3:
    comp = load_real_qwen35_components(allow_synthetic_fallback=allow_synthetic_qwen_fallback)
    tok = comp["tokenizer"]
    emb = comp["embed_tokens"]
    ln23 = comp["ln23_weight"]
    wg = comp["gate_proj"]
    wu = comp["up_proj"]
    wd = comp["down_proj"]
    lnf = comp["norm_weight"]
    d_ff, d_model = wg.shape

    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)

    all_domains = list(QWEN35_DOMAIN_CORPUS.keys())
    dom_perm = torch.randperm(len(all_domains), generator=gen).tolist()
    chosen_domains = [all_domains[i] for i in dom_perm[:6]]

    verb_pool = [tok.encode(w, add_special_tokens=False)[0] for w in VERBALIZER_WORDS]
    v_perm = torch.randperm(len(verb_pool), generator=gen).tolist()
    verb_ids = [verb_pool[i] for i in v_perm[:6]]

    sup_texts: list[str] = []
    sup_y: list[int] = []
    qry_texts: list[str] = []
    qry_y: list[int] = []
    for cls_i, dom_name in enumerate(chosen_domains):
        sents = QWEN35_DOMAIN_CORPUS[dom_name]
        s_perm = torch.randperm(len(sents), generator=gen).tolist()
        for j in s_perm[:10]:
            sup_texts.append(sents[j])
            sup_y.append(cls_i)
        for j in s_perm[10:20]:
            qry_texts.append(sents[j])
            qry_y.append(cls_i)

    @torch.no_grad()
    def encode_swiglu_states(texts: list[str]) -> torch.Tensor:
        ids_list = [tok.encode(t, add_special_tokens=False) for t in texts]
        x = torch.stack([emb[ids].mean(dim=0) for ids in ids_list])
        h = (1.0 + ln23) * x * torch.rsqrt(x.pow(2).mean(dim=-1, keepdim=True) + 1e-6)
        m0 = F.silu(h @ wg.T) * (h @ wu.T)
        y0 = x + m0 @ wd.T
        return torch.cat([m0, y0], dim=-1).to(dtype)

    X_sup = encode_swiglu_states(sup_texts)
    X_qry = encode_swiglu_states(qry_texts)

    r = 12
    A_down = (1.0 / math.sqrt(float(d_ff))) * torch.randn((r, d_ff + 1), generator=gen, dtype=dtype)
    A_down[:, -1] = 0.0
    B_down = torch.zeros((d_model, r + 1), dtype=dtype)

    Y_sup = torch.tensor(sup_y, dtype=torch.long)
    Y_qry = torch.tensor(qry_y, dtype=torch.long)
    flip = torch.rand(Y_sup.shape[0], generator=gen) < 0.08
    Y_sup[flip] = torch.randint(0, 6, (int(flip.sum().item()),), generator=gen)

    aux = {
        "d_ff": torch.tensor(d_ff),
        "ln_final_w": lnf.to(dtype),
        "U_verb": emb[verb_ids].to(dtype),
        "lora_alpha": torch.tensor(0.14, dtype=dtype),
        "is_real_qwen35_weights": torch.tensor(1 if comp["is_real"] else 0),
    }
    return NeuralTargetTaskV3(
        task_id=f"real_qwen35_swiglu_lora_cls-{seed}",
        family="real_qwen35_swiglu_lora_cls",
        loss_type="cross_entropy",
        arch_kind="qwen35_full_down_lora",
        activation="swiglu",
        init_layers=[A_down, B_down],
        aux_tensors=aux,
        X_sup=X_sup,
        Y_sup=Y_sup,
        X_qry=X_qry,
        Y_qry=Y_qry,
        budget=10,
    )


def build_v3_confirmation_task(
    family: str,
    seed: int,
    dtype: torch.dtype = torch.float64,
    allow_synthetic_qwen_fallback: bool = False,
) -> NeuralTargetTaskV3:
    """Build an unseen Track B2 v3 confirmation task instance."""
    assert family in V3_CONFIRMATION_FAMILIES, f"Unknown v3 confirmation family: {family}"

    if family == "real_qwen35_swiglu_lora_cls":
        return _build_real_qwen35_swiglu_lora_task(
            seed=seed,
            dtype=dtype,
            allow_synthetic_qwen_fallback=allow_synthetic_qwen_fallback,
        )

    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)

    if family == "fourier_kan_multifreq_reg":
        d_in, d_b, d_mix, d_out = 20, 16, 24, 4
        n_sup, n_qry = 56, 144
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.30, dtype=dtype)
        teacher = [
            _rand_init_matrix(gen, d_b, d_in, scale=2.3, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=2.3, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=1.7, dtype=dtype),
            _rand_init_matrix(gen, d_mix, 3 * d_b, scale=1.9, dtype=dtype),
            _rand_init_matrix(gen, d_out, d_mix, scale=1.8, dtype=dtype),
        ]
        tmp = NeuralTargetTaskV3("tmp", family, "mse", "fourier_kan_reg", "silu", teacher, {}, X_all, X_all, X_all, X_all)
        with torch.no_grad():
            raw_y = forward_target_v3(tmp, teacher, X_all)[0]
            y_all = raw_y / raw_y.std().clamp_min(1e-6)
        Y_sup = y_all[:n_sup] + 0.18 * torch.randn((n_sup, d_out), generator=gen, dtype=dtype)
        Y_qry = y_all[n_sup:]
        init_layers = [
            _rand_init_matrix(gen, d_b, d_in, scale=2.1, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=2.1, dtype=dtype),
            _rand_init_matrix(gen, d_b, d_in, scale=0.55, dtype=dtype),
            _rand_init_matrix(gen, d_mix, 3 * d_b, scale=1.6, dtype=dtype),
            _rand_init_matrix(gen, d_out, d_mix, scale=0.45, dtype=dtype),
        ]
        return NeuralTargetTaskV3(
            task_id=f"{family}-{seed}",
            family=family,
            loss_type="mse",
            arch_kind="fourier_kan_reg",
            activation="silu",
            init_layers=init_layers,
            aux_tensors={},
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=Y_qry,
            budget=10,
        )

    if family == "bilinear_gated_interaction_cls":
        d_in, d1, d2, n_cls = 22, 28, 22, 6
        n_sup, n_qry = 54, 144
        X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.25, dtype=dtype)
        teacher = [
            _rand_init_matrix(gen, d1, d_in, scale=2.0, dtype=dtype),
            _rand_init_matrix(gen, d1, d_in, scale=2.0, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=1.9, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=1.9, dtype=dtype),
            _rand_init_matrix(gen, n_cls, d2, scale=2.2, dtype=dtype),
        ]
        tmp = NeuralTargetTaskV3("tmp", family, "cross_entropy", "bilinear_gated_cls", "tanh", teacher, {}, X_all, X_all, X_all, X_all)
        with torch.no_grad():
            y_all = forward_target_v3(tmp, teacher, X_all)[0].argmax(dim=-1)
        Y_sup = y_all[:n_sup].clone()
        flip = torch.rand(n_sup, generator=gen) < 0.12
        Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)
        Y_qry = y_all[n_sup:]
        init_layers = [
            _rand_init_matrix(gen, d1, d_in, scale=1.8, dtype=dtype),
            _rand_init_matrix(gen, d1, d_in, scale=0.55, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=0.60, dtype=dtype),
            _rand_init_matrix(gen, d2, d1, scale=1.75, dtype=dtype),
            _rand_init_matrix(gen, n_cls, d2, scale=0.50, dtype=dtype),
        ]
        return NeuralTargetTaskV3(
            task_id=f"{family}-{seed}",
            family=family,
            loss_type="cross_entropy",
            arch_kind="bilinear_gated_cls",
            activation="tanh",
            init_layers=init_layers,
            aux_tensors={},
            X_sup=X_all[:n_sup],
            Y_sup=Y_sup,
            X_qry=X_all[n_sup:],
            Y_qry=Y_qry,
            budget=10,
        )

    # Family 4: layernorm_residual_gelu_cls
    d_in, d_res, n_cls = 24, 28, 6
    n_sup, n_qry = 56, 144
    X_all = _anisotropic_inputs(gen, n_sup + n_qry, d_in, log10_span=1.45, dtype=dtype)
    teacher = [
        _rand_init_matrix(gen, d_res, d_in, scale=2.0, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.8, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.8, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.8, dtype=dtype),
        _rand_init_matrix(gen, n_cls, d_res, scale=2.2, dtype=dtype),
    ]
    tmp = NeuralTargetTaskV3("tmp", family, "cross_entropy", "layernorm_res_gelu_cls", "gelu", teacher, {}, X_all, X_all, X_all, X_all)
    with torch.no_grad():
        y_all = forward_target_v3(tmp, teacher, X_all)[0].argmax(dim=-1)
    Y_sup = y_all[:n_sup].clone()
    flip = torch.rand(n_sup, generator=gen) < 0.12
    Y_sup[flip] = torch.randint(0, n_cls, (int(flip.sum().item()),), generator=gen)
    Y_qry = y_all[n_sup:]
    init_layers = [
        _rand_init_matrix(gen, d_res, d_in, scale=1.9, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=0.40, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=1.60, dtype=dtype),
        _rand_init_matrix(gen, d_res, d_res, scale=0.40, dtype=dtype),
        _rand_init_matrix(gen, n_cls, d_res, scale=0.55, dtype=dtype),
    ]
    return NeuralTargetTaskV3(
        task_id=f"{family}-{seed}",
        family=family,
        loss_type="cross_entropy",
        arch_kind="layernorm_res_gelu_cls",
        activation="gelu",
        init_layers=init_layers,
        aux_tensors={},
        X_sup=X_all[:n_sup],
        Y_sup=Y_sup,
        X_qry=X_all[n_sup:],
        Y_qry=Y_qry,
        budget=10,
    )
