#include <algorithm>
#include <array>
#include <cerrno>
#include <cinttypes>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <sys/stat.h>
#include <unistd.h>

namespace {

constexpr uint64_t kStoreBytes = 647798597ULL;
constexpr uint64_t kHeaderBytes = 5ULL;
constexpr uint64_t kStreamBytes = 647798592ULL;
constexpr uint64_t kKeyBytes = 16ULL;
constexpr uint64_t kMinimumAge = 100000000ULL;
constexpr uint64_t kRingBytes = 100000000ULL;
constexpr uint64_t kTableEntries = 16777216ULL;
constexpr uint64_t kTableMask = kTableEntries - 1ULL;
constexpr uint64_t kHashBase = 0x9e3779b185ebca87ULL;
constexpr uint64_t kHashBasePower16 = 0x6fe6ef9fbd3b9581ULL;
constexpr uint64_t kRandomSeedM = 0xd1b54a32d192ed03ULL;
constexpr uint64_t kRandomSeedA = 0x94d049bb133111ebULL;
constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;
constexpr size_t kBufferBytes = 8ULL * 1024ULL * 1024ULL;
constexpr uint64_t kSemanticStateBytes =
    2ULL * kTableEntries * 8ULL + kRingBytes;

constexpr std::array<uint8_t, kHeaderBytes> kExpectedHeader{{
    0x80U, 0x00U, 0x00U, 0x00U, 0x00U,
}};
constexpr std::array<uint8_t, 32> kExpectedSha{{
    0xfeU, 0x6aU, 0xb5U, 0xb9U, 0x6aU, 0xd7U, 0xbfU, 0x2bU,
    0x6fU, 0x7bU, 0xd9U, 0xf7U, 0xcdU, 0x3bU, 0x32U, 0x12U,
    0xffU, 0xc7U, 0x32U, 0x0aU, 0xe2U, 0x90U, 0xe0U, 0x98U,
    0xf6U, 0x8eU, 0x97U, 0xb5U, 0x32U, 0x95U, 0xceU, 0xb9U,
}};
constexpr std::array<std::array<uint64_t, 2>, 6> kBuckets{{
    {{100000001ULL, 134217728ULL}},
    {{134217729ULL, 201326592ULL}},
    {{201326593ULL, 268435456ULL}},
    {{268435457ULL, 402653184ULL}},
    {{402653185ULL, 536870912ULL}},
    {{536870913ULL, 647798591ULL}},
}};

[[noreturn]] void Fail(const char* operation) {
  std::fprintf(stderr, "horizon-dualclock failure operation=%s errno=%d\n",
               operation, errno);
  std::exit(1);
}

uint32_t Ror(uint32_t value, unsigned int count) {
  return (value >> count) | (value << (32U - count));
}

class Sha256 {
 public:
  void Update(const uint8_t* data, size_t size) {
    total_ += static_cast<uint64_t>(size);
    while (size != 0) {
      const size_t take = std::min(size, block_.size() - used_);
      std::memcpy(block_.data() + used_, data, take);
      used_ += take;
      data += take;
      size -= take;
      if (used_ == block_.size()) {
        Transform();
        used_ = 0;
      }
    }
  }

  std::array<uint8_t, 32> Finalize() {
    const uint64_t bits = total_ * 8ULL;
    const uint8_t marker = 0x80U;
    const uint8_t zero = 0;
    Update(&marker, 1);
    while (used_ != 56) Update(&zero, 1);
    std::array<uint8_t, 8> length{};
    for (size_t i = 0; i < length.size(); ++i) {
      length[7 - i] = static_cast<uint8_t>(bits >> (i * 8U));
    }
    Update(length.data(), length.size());
    std::array<uint8_t, 32> digest{};
    for (size_t i = 0; i < state_.size(); ++i) {
      for (size_t j = 0; j < 4; ++j) {
        digest[i * 4 + j] =
            static_cast<uint8_t>(state_[i] >> ((3U - j) * 8U));
      }
    }
    return digest;
  }

 private:
  void Transform() {
    static constexpr std::array<uint32_t, 64> k{{
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,
        0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,
        0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,
        0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,
        0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,
        0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,
        0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,
        0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,
        0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U,
    }};
    std::array<uint32_t, 64> w{};
    for (size_t i = 0; i < 16; ++i) {
      w[i] = (static_cast<uint32_t>(block_[i * 4]) << 24U) |
          (static_cast<uint32_t>(block_[i * 4 + 1]) << 16U) |
          (static_cast<uint32_t>(block_[i * 4 + 2]) << 8U) |
          static_cast<uint32_t>(block_[i * 4 + 3]);
    }
    for (size_t i = 16; i < w.size(); ++i) {
      const uint32_t x = w[i - 15];
      const uint32_t y = w[i - 2];
      w[i] = w[i - 16] + (Ror(x, 7) ^ Ror(x, 18) ^ (x >> 3U)) +
          w[i - 7] + (Ror(y, 17) ^ Ror(y, 19) ^ (y >> 10U));
    }
    uint32_t a=state_[0], b=state_[1], c=state_[2], d=state_[3];
    uint32_t e=state_[4], f=state_[5], g=state_[6], h=state_[7];
    for (size_t i = 0; i < w.size(); ++i) {
      const uint32_t s1 = Ror(e, 6) ^ Ror(e, 11) ^ Ror(e, 25);
      const uint32_t t1 = h + s1 + ((e & f) ^ ((~e) & g)) + k[i] + w[i];
      const uint32_t s0 = Ror(a, 2) ^ Ror(a, 13) ^ Ror(a, 22);
      const uint32_t t2 = s0 + ((a & b) ^ (a & c) ^ (b & c));
      h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    state_[0]+=a; state_[1]+=b; state_[2]+=c; state_[3]+=d;
    state_[4]+=e; state_[5]+=f; state_[6]+=g; state_[7]+=h;
  }

  std::array<uint32_t, 8> state_{{
      0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,
      0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U,
  }};
  std::array<uint8_t, 64> block_{};
  uint64_t total_ = 0;
  size_t used_ = 0;
};

uint64_t FnvByte(uint64_t h, uint8_t value) {
  return (h ^ value) * kFnvPrime;
}
uint64_t FnvU32(uint64_t h, uint32_t value) {
  for (unsigned int s = 0; s < 32; s += 8) {
    h = FnvByte(h, static_cast<uint8_t>(value >> s));
  }
  return h;
}
uint64_t FnvU64(uint64_t h, uint64_t value) {
  for (unsigned int s = 0; s < 64; s += 8) {
    h = FnvByte(h, static_cast<uint8_t>(value >> s));
  }
  return h;
}
uint64_t SplitMix64(uint64_t value) {
  value += 0x9e3779b97f4a7c15ULL;
  value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
  value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
  return value ^ (value >> 31);
}

struct Record {
  uint32_t tag = 0;
  uint32_t continuation_plus_one = 0;
};
static_assert(sizeof(Record) == 8, "record must be eight bytes");

struct Counts {
  uint64_t active=0, d=0, s=0, r=0, n=0;
  uint64_t kt_correct=0, kt_incorrect=0;
  double kt_truth_bits=0.0;
};
struct Arm {
  uint64_t empty=0, tag_mismatch=0, invalid=0, verify_fail=0, suppressed=0;
  uint64_t active=0, d=0, s=0, r=0, n=0;
  std::array<Counts, 3> thirds{};
  std::array<Counts, 6> buckets{};
  uint64_t opportunity_hash=kFnvOffset;
};
struct Measurements {
  uint64_t stream=0, positions=0, lookups_m=0, lookups_a=0;
  uint64_t replaces_m=0, installs_a=0, preserves_a=0;
  uint64_t ring_writes=0, hash_rolls=0, past_reads=0, past_bytes=0;
  uint64_t advice_failures=0;
  Arm m{}, a{};
  uint64_t tm=kFnvOffset, tkm=kFnvOffset, ta=kFnvOffset, tka=kFnvOffset;
  uint64_t shared=kFnvOffset, shared_k=kFnvOffset;
};
struct Candidate { bool active=false; uint64_t coordinate=0; uint8_t donor=0; };

class Scanner {
 public:
  explicit Scanner(int input) : input_(input) {}

  void Observe(uint8_t truth, uint64_t i) {
    if (i != measurements_.stream) Fail("nonsequential truth");
    if (i < kKeyBytes) {
      rolling_hash_ = rolling_hash_ * kHashBase + truth;
      context_[i] = truth;
      ring_[i % kRingBytes] = truth;
      ++measurements_.ring_writes;
      ++measurements_.stream;
      return;
    }
    ++measurements_.positions;
    ++measurements_.lookups_m;
    ++measurements_.lookups_a;
    const uint32_t index = static_cast<uint32_t>(rolling_hash_ & kTableMask);
    const uint32_t tag = static_cast<uint32_t>(rolling_hash_ >> 32);
    const Record old_m = recent_[index];
    const Record old_a = anchor_[index];
    const Candidate cm = Evaluate(old_m, tag, i, &measurements_.m);
    const Candidate ca = Evaluate(old_a, tag, i, &measurements_.a);
    if (cm.active) Score('M', i, cm, truth, &measurements_.m);
    if (ca.active) Score('A', i, ca, truth, &measurements_.a);

    const uint8_t outgoing = context_[0];
    for (size_t j = 1; j < context_.size(); ++j) context_[j - 1] = context_[j];
    context_.back() = truth;
    const Record new_m{tag, static_cast<uint32_t>(i + 1ULL)};
    recent_[index] = new_m;
    ++measurements_.replaces_m;
    Record new_a = old_a;
    if (old_a.continuation_plus_one == 0 || old_a.tag != tag) {
      new_a = Record{tag, static_cast<uint32_t>(i + 1ULL)};
      anchor_[index] = new_a;
      ++measurements_.installs_a;
    } else {
      ++measurements_.preserves_a;
    }
    Advance(i, index, old_m, new_m, truth, &measurements_.tm, &measurements_.tkm);
    Advance(i, index, old_a, new_a, truth, &measurements_.ta, &measurements_.tka);
    AdvanceShared(i, outgoing, truth);
    ring_[i % kRingBytes] = truth;
    ++measurements_.ring_writes;
    rolling_hash_ = rolling_hash_ * kHashBase -
        static_cast<uint64_t>(outgoing) * kHashBasePower16 + truth;
    ++measurements_.hash_rolls;
    ++measurements_.stream;
  }

  void Finish() {
    if (measurements_.stream != kStreamBytes) Fail("short stream");
    uint64_t recomputed = 0;
    for (uint8_t value : context_) recomputed = recomputed * kHashBase + value;
    hash_recompute_pass_ = recomputed == rolling_hash_;
    recent_hash_ = HashTable(recent_);
    anchor_hash_ = HashTable(anchor_);
    ring_hash_ = kFnvOffset;
    for (uint8_t value : ring_) ring_hash_ = FnvByte(ring_hash_, value);
  }

  const Measurements& measurements() const { return measurements_; }
  uint64_t rolling_hash() const { return rolling_hash_; }
  uint64_t recent_hash() const { return recent_hash_; }
  uint64_t anchor_hash() const { return anchor_hash_; }
  uint64_t ring_hash() const { return ring_hash_; }
  bool hash_recompute_pass() const { return hash_recompute_pass_; }

 private:
  Candidate Evaluate(const Record& record, uint32_t tag, uint64_t current,
                     Arm* arm) {
    if (record.continuation_plus_one == 0) { ++arm->empty; return {}; }
    if (record.tag != tag) { ++arm->tag_mismatch; return {}; }
    const uint64_t candidate =
        static_cast<uint64_t>(record.continuation_plus_one) - 1ULL;
    if (candidate < kKeyBytes || candidate >= current) {
      ++arm->invalid; return {};
    }
    if (current - candidate <= kMinimumAge) { ++arm->suppressed; return {}; }
    std::array<uint8_t, 17> history{};
    PastBytes(candidate - kKeyBytes, history.size(), current, history.data());
    for (size_t i = 0; i < kKeyBytes; ++i) {
      if (history[i] != context_[i]) { ++arm->verify_fail; return {}; }
    }
    return Candidate{true, candidate, history[kKeyBytes]};
  }

  void PastBytes(uint64_t begin, size_t size, uint64_t current, uint8_t* out) {
    if (size == 0 || begin >= current || begin > current - size) {
      errno = ERANGE; Fail("past causal bound");
    }
    size_t done = 0;
    while (done < size) {
      const ssize_t count = pread(input_, out + done, size - done,
          static_cast<off_t>(kHeaderBytes + begin + done));
      if (count < 0 && errno == EINTR) continue;
      if (count <= 0) Fail("past read");
      done += static_cast<size_t>(count);
    }
    ++measurements_.past_reads;
    measurements_.past_bytes += size;
    const long page = sysconf(_SC_PAGESIZE);
    if (page > 0) {
      const uint64_t page_size = static_cast<uint64_t>(page);
      const uint64_t stored = kHeaderBytes + begin;
      const uint64_t low = stored - stored % page_size;
      const uint64_t high = ((stored + size + page_size - 1) / page_size) * page_size;
      if (posix_fadvise(input_, static_cast<off_t>(low),
          static_cast<off_t>(high - low), POSIX_FADV_DONTNEED) != 0) {
        ++measurements_.advice_failures;
      }
    } else {
      ++measurements_.advice_failures;
    }
  }

  static size_t Third(uint64_t i) {
    return std::min<size_t>(2, static_cast<size_t>((i * 3ULL) / kStreamBytes));
  }
  static size_t Bucket(uint64_t distance) {
    for (size_t i = 0; i < kBuckets.size(); ++i) {
      if (distance >= kBuckets[i][0] && distance <= kBuckets[i][1]) return i;
    }
    errno = ERANGE; Fail("distance bucket");
  }
  static void Count(Counts* c, bool d, bool s, bool r, bool n, bool kt) {
    ++c->active; c->d += d; c->s += s; c->r += r; c->n += n;
    if (kt) {
      const double total = static_cast<double>(c->kt_correct + c->kt_incorrect);
      const double q = (static_cast<double>(c->kt_correct) + 0.5) / (total + 1.0);
      const double p = d ? q : (1.0 - q) / 255.0;
      c->kt_truth_bits += -std::log2(p);
      c->kt_correct += d;
      c->kt_incorrect += !d;
    }
  }
  void Score(char id, uint64_t current, const Candidate& candidate,
             uint8_t truth, Arm* arm) {
    const uint8_t shifted = ring_[candidate.coordinate % kRingBytes];
    const uint64_t seed = id == 'M' ? kRandomSeedM : kRandomSeedA;
    const uint8_t random = static_cast<uint8_t>(
        SplitMix64(rolling_hash_ ^ (current << 1U) ^ seed) >> 56U);
    const uint8_t negated = static_cast<uint8_t>(candidate.donor ^ 0xffU);
    const bool d = candidate.donor == truth;
    const bool s = shifted == truth;
    const bool r = random == truth;
    const bool n = negated == truth;
    ++arm->active; arm->d += d; arm->s += s; arm->r += r; arm->n += n;
    Count(&arm->thirds[Third(current)], d, s, r, n, true);
    Count(&arm->buckets[Bucket(current - candidate.coordinate)], d, s, r, n, false);
    uint64_t& h = arm->opportunity_hash;
    h=FnvByte(h,static_cast<uint8_t>(id)); h=FnvU64(h,current);
    h=FnvU64(h,rolling_hash_); h=FnvU64(h,candidate.coordinate);
    h=FnvByte(h,candidate.donor); h=FnvByte(h,shifted); h=FnvByte(h,random);
    h=FnvByte(h,negated); h=FnvByte(h,truth);
  }
  void Advance(uint64_t i, uint32_t index, const Record& old,
               const Record& next, uint8_t truth, uint64_t* t, uint64_t* k) {
    auto step = [&](uint64_t h) {
      h=FnvU64(h,i); h=FnvU64(h,rolling_hash_); h=FnvU32(h,index);
      h=FnvU32(h,old.tag); h=FnvU32(h,old.continuation_plus_one);
      h=FnvU32(h,next.tag); h=FnvU32(h,next.continuation_plus_one);
      return FnvByte(h,truth);
    };
    *t=step(*t); *k=step(*k);
  }
  void AdvanceShared(uint64_t i, uint8_t outgoing, uint8_t truth) {
    auto step = [&](uint64_t h) {
      h=FnvU64(h,i); h=FnvU64(h,rolling_hash_); h=FnvByte(h,outgoing);
      return FnvByte(h,truth);
    };
    measurements_.shared=step(measurements_.shared);
    measurements_.shared_k=step(measurements_.shared_k);
  }
  static uint64_t HashTable(const std::array<Record,kTableEntries>& table) {
    uint64_t h=kFnvOffset;
    for (const Record& record : table) {
      h=FnvU32(h,record.tag); h=FnvU32(h,record.continuation_plus_one);
    }
    return h;
  }

  int input_;
  std::array<Record,kTableEntries> recent_{};
  std::array<Record,kTableEntries> anchor_{};
  std::array<uint8_t,kRingBytes> ring_{};
  std::array<uint8_t,kKeyBytes> context_{};
  Measurements measurements_{};
  uint64_t rolling_hash_=0, recent_hash_=0, anchor_hash_=0, ring_hash_=0;
  bool hash_recompute_pass_=false;
};

int64_t Margin(const Counts& c) {
  return static_cast<int64_t>(c.d) -
      static_cast<int64_t>(std::max({c.s,c.r,c.n}));
}
double KtGain(const Counts& c) {
  return 8.0 * static_cast<double>(c.active) - c.kt_truth_bits;
}
bool CountsPass(const Counts& c, bool kt) {
  return c.d<=c.active && c.s<=c.active && c.r<=c.active && c.n<=c.active &&
      (!kt || c.kt_correct+c.kt_incorrect==c.active);
}
struct Derived {
  int64_t min_margin=std::numeric_limits<int64_t>::max();
  uint64_t positive_buckets=0;
  double truth_bits=0.0, gain_bits=0.0;
  double min_third_gain=std::numeric_limits<double>::infinity();
  bool partitions=false;
};
Derived Derive(const Arm& arm) {
  Derived d{};
  uint64_t ta=0,td=0,ts=0,tr=0,tn=0,ba=0,bd=0,bs=0,br=0,bn=0;
  bool bounded=true;
  for (const Counts& c : arm.thirds) {
    d.min_margin=std::min(d.min_margin,Margin(c));
    d.truth_bits+=c.kt_truth_bits;
    d.min_third_gain=std::min(d.min_third_gain,KtGain(c));
    ta+=c.active; td+=c.d; ts+=c.s; tr+=c.r; tn+=c.n;
    bounded=bounded && CountsPass(c,true);
  }
  d.gain_bits=8.0*static_cast<double>(arm.active)-d.truth_bits;
  for (const Counts& c : arm.buckets) {
    if (c.active!=0 && Margin(c)>0) ++d.positive_buckets;
    ba+=c.active; bd+=c.d; bs+=c.s; br+=c.r; bn+=c.n;
    bounded=bounded && CountsPass(c,false);
  }
  d.partitions=bounded && ta==arm.active && ba==arm.active &&
      td==arm.d && ts==arm.s && tr==arm.r && tn==arm.n &&
      bd==arm.d && bs==arm.s && br==arm.r && bn==arm.n;
  return d;
}
void WriteCounts(FILE* out, const Counts& c, bool kt) {
  std::fprintf(out,"{\"active\":%" PRIu64 ",\"D\":%" PRIu64
      ",\"S\":%" PRIu64 ",\"R\":%" PRIu64 ",\"N\":%" PRIu64,
      c.active,c.d,c.s,c.r,c.n);
  if (kt) std::fprintf(out,",\"kt_correct\":%" PRIu64
      ",\"kt_incorrect\":%" PRIu64 ",\"kt_truth_bits\":%.9f"
      ",\"kt_gain_bits\":%.9f",c.kt_correct,c.kt_incorrect,
      c.kt_truth_bits,KtGain(c));
  std::fputc('}',out);
}
void WriteArm(FILE* out, const Arm& arm, const Derived& d) {
  std::fprintf(out,"{\"table_empty\":%" PRIu64
      ",\"table_tag_mismatches\":%" PRIu64
      ",\"invalid_continuations\":%" PRIu64
      ",\"context_verification_failures\":%" PRIu64
      ",\"distance_suppressed\":%" PRIu64
      ",\"active_bytes\":%" PRIu64
      ",\"treatment_correct_bytes\":%" PRIu64
      ",\"alias_correct_bytes\":%" PRIu64
      ",\"random_correct_bytes\":%" PRIu64
      ",\"negated_correct_bytes\":%" PRIu64,
      arm.empty,arm.tag_mismatch,arm.invalid,arm.verify_fail,arm.suppressed,
      arm.active,arm.d,arm.s,arm.r,arm.n);
  std::fprintf(out,",\"correct_by_third\":[");
  for (size_t i=0;i<arm.thirds.size();++i) { if(i) std::fputc(',',out); WriteCounts(out,arm.thirds[i],true); }
  std::fprintf(out,"],\"correct_by_distance_bucket\":[");
  for (size_t i=0;i<arm.buckets.size();++i) { if(i) std::fputc(',',out); WriteCounts(out,arm.buckets[i],false); }
  std::fprintf(out,"],\"minimum_third_control_margin_bytes\":%" PRId64
      ",\"positive_distance_bucket_count\":%" PRIu64
      ",\"causal_kt_truth_bits\":%.9f,\"causal_kt_gain_bits\":%.9f"
      ",\"minimum_third_kt_gain_bits\":%.9f,\"partition_pass\":%s"
      ",\"opportunity_fnv1a64\":\"%016" PRIx64 "\"}",
      d.min_margin,d.positive_buckets,d.truth_bits,d.gain_bits,d.min_third_gain,
      d.partitions?"true":"false",arm.opportunity_hash);
}

void WriteReceipt(const char* path, const Scanner& scanner) {
  const int fd=open(path,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW,0600);
  if(fd<0) Fail("create output");
  FILE* out=fdopen(fd,"wb"); if(out==nullptr){close(fd);Fail("fdopen");}
  const Measurements& m=scanner.measurements();
  const Derived dm=Derive(m.m), da=Derive(m.a);
  const uint64_t pm=m.m.empty+m.m.tag_mismatch+m.m.invalid+m.m.verify_fail+m.m.suppressed+m.m.active;
  const uint64_t pa=m.a.empty+m.a.tag_mismatch+m.a.invalid+m.a.verify_fail+m.a.suppressed+m.a.active;
  const bool identity=m.tm==m.tkm && m.ta==m.tka && m.shared==m.shared_k;
  const bool causal=scanner.hash_recompute_pass() && identity && dm.partitions && da.partitions &&
      m.stream==kStreamBytes && m.positions==kStreamBytes-kKeyBytes &&
      m.lookups_m==m.positions && m.lookups_a==m.positions &&
      m.replaces_m==m.positions && m.installs_a+m.preserves_a==m.positions &&
      m.ring_writes==kStreamBytes && m.hash_rolls==m.positions &&
      pm==m.lookups_m && pa==m.lookups_a && m.past_bytes==m.past_reads*17ULL;
  std::fprintf(out,"{\n  \"schema\": \"gamma.enwiki9.endpoint428-horizon-dualclock-scan.v1\",\n"
      "  \"candidate_id\": \"endpoint428_horizon_dualclock_source_census_q0_v2\",\n"
      "  \"store_bytes\": %" PRIu64 ",\n"
      "  \"store_sha256\": \"fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9\",\n"
      "  \"storage_header_bytes\": %" PRIu64 ",\n"
      "  \"stream_bytes\": %" PRIu64 ",\n"
      "  \"positions_scored\": %" PRIu64 ",\n"
      "  \"minimum_candidate_age_bytes\": %" PRIu64 ",\n"
      "  \"distance_buckets\": [[100000001,134217728],[134217729,201326592],[201326593,268435456],[268435457,402653184],[402653185,536870912],[536870913,647798591]],\n"
      "  \"arms\": {\"M\":",kStoreBytes,kHeaderBytes,m.stream,m.positions,kMinimumAge);
  WriteArm(out,m.m,dm); std::fprintf(out,",\"A\":"); WriteArm(out,m.a,da);
  std::fprintf(out,"},\n  \"table_lookups_m\": %" PRIu64 ",\n"
      "  \"table_lookups_a\": %" PRIu64 ",\n"
      "  \"table_replacements_m\": %" PRIu64 ",\n"
      "  \"table_installs_a\": %" PRIu64 ",\n"
      "  \"table_preserves_a\": %" PRIu64 ",\n"
      "  \"ring_writes\": %" PRIu64 ",\n  \"hash_rolls\": %" PRIu64 ",\n"
      "  \"past_reads\": %" PRIu64 ",\n  \"past_bytes_read\": %" PRIu64 ",\n"
      "  \"past_read_advice_failures\": %" PRIu64 ",\n"
      "  \"final_rolling_hash\": \"%016" PRIx64 "\",\n"
      "  \"terminal_hash_recompute_pass\": %s,\n"
      "  \"recent_table_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"anchor_table_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"ring_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"transition_m_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"transition_km_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"transition_a_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"transition_ka_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"shared_transition_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"shared_transition_k_fnv1a64\": \"%016" PRIx64 "\",\n"
      "  \"treatment_k_state_identity_pass\": %s,\n"
      "  \"control_outcomes_feed_state\": false,\n"
      "  \"causal_and_verification_pass\": %s,\n"
      "  \"semantic_state_bytes\": %" PRIu64 ",\n"
      "  \"archive_authority\": false,\n  \"score_credit_bytes\": 0\n}\n",
      m.lookups_m,m.lookups_a,m.replaces_m,m.installs_a,m.preserves_a,
      m.ring_writes,m.hash_rolls,m.past_reads,m.past_bytes,m.advice_failures,
      scanner.rolling_hash(),scanner.hash_recompute_pass()?"true":"false",
      scanner.recent_hash(),scanner.anchor_hash(),scanner.ring_hash(),
      m.tm,m.tkm,m.ta,m.tka,m.shared,m.shared_k,identity?"true":"false",
      causal?"true":"false",kSemanticStateBytes);
  if(std::fflush(out)!=0 || fsync(fd)!=0){std::fclose(out);Fail("flush");}
  if(std::fclose(out)!=0) Fail("close output");
}

void VerifyStore(int input) {
  if(lseek(input,0,SEEK_SET)!=0) Fail("seek identity");
  Sha256 sha; std::array<uint8_t,kBufferBytes> buffer{}; uint64_t total=0;
  for(;;){
    const ssize_t count=read(input,buffer.data(),buffer.size());
    if(count<0 && errno==EINTR) continue;
    if(count<0) Fail("read identity");
    if(count==0) break;
    sha.Update(buffer.data(),static_cast<size_t>(count)); total+=static_cast<uint64_t>(count);
  }
  if(total!=kStoreBytes || sha.Finalize()!=kExpectedSha){errno=EINVAL;Fail("store sha256");}
  std::array<uint8_t,kHeaderBytes> header{};
  if(pread(input,header.data(),header.size(),0)!=static_cast<ssize_t>(header.size()) ||
      header!=kExpectedHeader){errno=EINVAL;Fail("store wrapper");}
  (void)posix_fadvise(input,0,0,POSIX_FADV_DONTNEED);
}

}  // namespace

int main(int argc,char** argv) {
  if(argc!=3){std::fprintf(stderr,"usage: %s ENDPOINT_STORE OUTPUT_JSON\n",argv[0]);return 64;}
  struct stat metadata={};
  if(lstat(argv[1],&metadata)!=0 || !S_ISREG(metadata.st_mode) || metadata.st_nlink!=1 ||
      static_cast<uint64_t>(metadata.st_size)!=kStoreBytes){errno=EINVAL;Fail("input geometry");}
  const int input=open(argv[1],O_RDONLY|O_CLOEXEC|O_NOFOLLOW); if(input<0) Fail("open input");
  VerifyStore(input);
  if(lseek(input,static_cast<off_t>(kHeaderBytes),SEEK_SET)!=static_cast<off_t>(kHeaderBytes)) Fail("seek WRT");
  const int advice=posix_fadvise(input,static_cast<off_t>(kHeaderBytes),
      static_cast<off_t>(kStreamBytes),POSIX_FADV_SEQUENTIAL);
  if(advice!=0){errno=advice;Fail("sequential advice");}
  static Scanner scanner(input); static std::array<uint8_t,kBufferBytes> buffer{};
  uint64_t offset=0;
  while(offset<kStreamBytes){
    const size_t wanted=static_cast<size_t>(std::min<uint64_t>(buffer.size(),kStreamBytes-offset));
    const ssize_t count=read(input,buffer.data(),wanted);
    if(count<0 && errno==EINTR) continue;
    if(count<0) Fail("read WRT");
    if(count==0) Fail("short WRT");
    for(ssize_t i=0;i<count;++i) scanner.Observe(buffer[static_cast<size_t>(i)],offset++);
    const uint64_t begin=kHeaderBytes+offset-static_cast<uint64_t>(count);
    (void)posix_fadvise(input,static_cast<off_t>(begin),count,POSIX_FADV_DONTNEED);
  }
  scanner.Finish(); if(close(input)!=0) Fail("close input"); WriteReceipt(argv[2],scanner);
  return 0;
}
