#include <algorithm>
#include <array>
#include <cerrno>
#include <cinttypes>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

constexpr uint64_t kFixtureStoreBytes = 37;
constexpr uint64_t kFixtureWrtBytes = 32;
constexpr uint64_t kFixtureRawBytes = 38;
constexpr uint32_t kFixtureDictionaryWords = 3921;
constexpr uint64_t kStoreWrapperBytes = 5;
constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;
constexpr std::array<uint8_t, kStoreWrapperBytes> kExpectedWrapper{{
    0x80U, 0x00U, 0x00U, 0x00U, 0x00U,
}};
constexpr std::array<uint64_t, 7> kBoundaries{{
    0ULL, 7ULL, 14ULL, 21ULL, 25ULL, 30ULL, 38ULL,
}};

[[noreturn]] void Fail(const std::string& operation) {
  throw std::runtime_error(operation + " errno=" + std::to_string(errno));
}

uint32_t RotateRight(uint32_t value, unsigned count) {
  return (value >> count) | (value << (32U - count));
}

class Sha256 {
 public:
  void Update(const uint8_t* data, size_t size) {
    if (size > std::numeric_limits<uint64_t>::max() - total_) {
      errno = EOVERFLOW;
      Fail("SHA-256 input length");
    }
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
    if (total_ > std::numeric_limits<uint64_t>::max() / 8ULL) {
      errno = EOVERFLOW;
      Fail("SHA-256 bit length");
    }
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
    static constexpr std::array<uint32_t, 64> constants{{
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
    std::array<uint32_t, 64> words{};
    for (size_t i = 0; i < 16; ++i) {
      words[i] = (static_cast<uint32_t>(block_[i * 4]) << 24U) |
                 (static_cast<uint32_t>(block_[i * 4 + 1]) << 16U) |
                 (static_cast<uint32_t>(block_[i * 4 + 2]) << 8U) |
                 static_cast<uint32_t>(block_[i * 4 + 3]);
    }
    for (size_t i = 16; i < words.size(); ++i) {
      const uint32_t x = words[i - 15];
      const uint32_t y = words[i - 2];
      words[i] = words[i - 16] +
                 (RotateRight(x, 7) ^ RotateRight(x, 18) ^ (x >> 3U)) +
                 words[i - 7] +
                 (RotateRight(y, 17) ^ RotateRight(y, 19) ^ (y >> 10U));
    }
    uint32_t a = state_[0];
    uint32_t b = state_[1];
    uint32_t c = state_[2];
    uint32_t d = state_[3];
    uint32_t e = state_[4];
    uint32_t f = state_[5];
    uint32_t g = state_[6];
    uint32_t h = state_[7];
    for (size_t i = 0; i < words.size(); ++i) {
      const uint32_t s1 = RotateRight(e, 6) ^ RotateRight(e, 11) ^
                          RotateRight(e, 25);
      const uint32_t first = h + s1 + ((e & f) ^ ((~e) & g)) +
                             constants[i] + words[i];
      const uint32_t s0 = RotateRight(a, 2) ^ RotateRight(a, 13) ^
                          RotateRight(a, 22);
      const uint32_t second = s0 + ((a & b) ^ (a & c) ^ (b & c));
      h = g;
      g = f;
      f = e;
      e = d + first;
      d = c;
      c = b;
      b = a;
      a = first + second;
    }
    state_[0] += a;
    state_[1] += b;
    state_[2] += c;
    state_[3] += d;
    state_[4] += e;
    state_[5] += f;
    state_[6] += g;
    state_[7] += h;
  }

  std::array<uint32_t, 8> state_{{
      0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,
      0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U,
  }};
  std::array<uint8_t, 64> block_{};
  uint64_t total_ = 0;
  size_t used_ = 0;
};

std::string Hex(const std::array<uint8_t, 32>& digest) {
  std::ostringstream output;
  output << std::hex << std::setfill('0');
  for (uint8_t value : digest) output << std::setw(2) << unsigned(value);
  return output.str();
}

std::string Hex64(uint64_t value) {
  std::ostringstream output;
  output << std::hex << std::setfill('0') << std::setw(16) << value;
  return output.str();
}

std::string HashBytes(const uint8_t* data, size_t size) {
  Sha256 hash;
  hash.Update(data, size);
  return Hex(hash.Finalize());
}

uint64_t FnvByte(uint64_t hash, uint8_t value) {
  return (hash ^ value) * kFnvPrime;
}

void HashU32(Sha256* hash, uint32_t value) {
  std::array<uint8_t, 4> bytes{};
  for (unsigned i = 0; i < 4; ++i) {
    bytes[i] = static_cast<uint8_t>(value >> (8U * i));
  }
  hash->Update(bytes.data(), bytes.size());
}

void HashU64(Sha256* hash, uint64_t value) {
  std::array<uint8_t, 8> bytes{};
  for (unsigned i = 0; i < 8; ++i) {
    bytes[i] = static_cast<uint8_t>(value >> (8U * i));
  }
  hash->Update(bytes.data(), bytes.size());
}

class MappedInput {
 public:
  explicit MappedInput(const char* path) {
    struct stat before {};
    if (lstat(path, &before) != 0) Fail("lstat input");
    if (!S_ISREG(before.st_mode) || before.st_size <= 0) {
      errno = EINVAL;
      Fail("input is not a nonempty regular file");
    }
    fd_ = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd_ < 0) Fail("open input");
    struct stat after {};
    if (fstat(fd_, &after) != 0) Fail("fstat input");
    if (!S_ISREG(after.st_mode) || after.st_dev != before.st_dev ||
        after.st_ino != before.st_ino || after.st_size != before.st_size ||
        static_cast<uintmax_t>(after.st_size) >
            static_cast<uintmax_t>(std::numeric_limits<size_t>::max())) {
      errno = EINVAL;
      Fail("input identity changed");
    }
    size_ = static_cast<size_t>(after.st_size);
    void* mapped = mmap(nullptr, size_, PROT_READ, MAP_PRIVATE, fd_, 0);
    if (mapped == MAP_FAILED) Fail("mmap input");
    data_ = static_cast<const uint8_t*>(mapped);
  }

  MappedInput(const MappedInput&) = delete;
  MappedInput& operator=(const MappedInput&) = delete;

  ~MappedInput() {
    if (data_ != nullptr) munmap(const_cast<uint8_t*>(data_), size_);
    if (fd_ >= 0) close(fd_);
  }

  const uint8_t* data() const { return data_; }
  size_t size() const { return size_; }

 private:
  int fd_ = -1;
  const uint8_t* data_ = nullptr;
  size_t size_ = 0;
};

void WriteExclusive(const char* path, const std::string& contents) {
  const int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
                      0600);
  if (fd < 0) Fail("open output");
  size_t offset = 0;
  while (offset != contents.size()) {
    const ssize_t count =
        write(fd, contents.data() + offset, contents.size() - offset);
    if (count < 0 && errno == EINTR) continue;
    if (count <= 0) {
      const int saved = errno;
      close(fd);
      errno = saved;
      Fail("write output");
    }
    offset += static_cast<size_t>(count);
  }
  if (fsync(fd) != 0) {
    const int saved = errno;
    close(fd);
    errno = saved;
    Fail("fsync output");
  }
  if (close(fd) != 0) Fail("close output");
}

struct BoundaryRow {
  uint64_t raw_boundary = 0;
  uint64_t wrt_coordinate = 0;
  uint64_t raw_before = 0;
  std::string state_sha256;
};

class CoordinateDecoder {
 public:
  CoordinateDecoder(const MappedInput& raw, const MappedInput& dictionary)
      : raw_(raw.data()), raw_size_(raw.size()) {
    LoadDictionary(dictionary.data(), dictionary.size());
  }

  std::pair<uint64_t, uint64_t> Consume(uint8_t stored, uint64_t coordinate) {
    const uint64_t before = raw_position_;
    wrt_digest_ = FnvByte(wrt_digest_, stored);
    if (coordinate < 5) {
      if (coordinate == 0 && stored != 7) {
        errno = EILSEQ;
        Fail("WRT type");
      }
      if (coordinate > 0) {
        raw_length_header_ =
            (raw_length_header_ << 8U) | static_cast<uint64_t>(stored);
      }
    } else if (coordinate == 5) {
      if (stored != 7) {
        errno = EILSEQ;
        Fail("WRT enabled marker");
      }
    } else {
      DecodeStored(stored);
    }
    return {before, raw_position_};
  }

  void Finish() const {
    if (pending_escape_ || code_needed_ != 0 || code_bytes_ != 0 || code_ != 0) {
      errno = EILSEQ;
      Fail("incomplete terminal WRT code");
    }
    if (raw_length_header_ != raw_size_ || raw_position_ != raw_size_) {
      errno = EILSEQ;
      Fail("raw length identity");
    }
  }

  std::string StateDigest(uint64_t coordinate) const {
    Sha256 hash;
    static constexpr char domain[] = "HARM-FRONTEND-STATE-v1";
    hash.Update(reinterpret_cast<const uint8_t*>(domain), sizeof(domain));
    HashU64(&hash, coordinate);
    HashU64(&hash, raw_position_);
    HashU64(&hash, raw_length_header_);
    HashU64(&hash, raw_digest_);
    HashU64(&hash, wrt_digest_);
    HashU32(&hash, code_);
    HashU32(&hash, code_bytes_);
    HashU32(&hash, code_needed_);
    HashU32(&hash, dictionary_words_);
    const std::array<uint8_t, 4> flags{{
        static_cast<uint8_t>(uppercase_),
        static_cast<uint8_t>(capitalized_),
        static_cast<uint8_t>(pending_escape_),
        0U,
    }};
    hash.Update(flags.data(), flags.size());
    return Hex(hash.Finalize());
  }

  uint64_t raw_position() const { return raw_position_; }
  uint64_t raw_length_header() const { return raw_length_header_; }
  uint64_t raw_digest() const { return raw_digest_; }
  uint64_t wrt_digest() const { return wrt_digest_; }
  uint32_t dictionary_words() const { return dictionary_words_; }

 private:
  static uint8_t UndoRemap(uint8_t value) {
    if (value >= static_cast<uint8_t>('{') && value < 127) {
      value = static_cast<uint8_t>(
          value + static_cast<int>('P') - static_cast<int>('{'));
    } else if (value >= static_cast<uint8_t>('P') &&
               value < static_cast<uint8_t>('T')) {
      value = static_cast<uint8_t>(
          value - static_cast<int>('P') + static_cast<int>('{'));
    } else if ((value >= static_cast<uint8_t>(':') &&
                value <= static_cast<uint8_t>('?')) ||
               (value >= static_cast<uint8_t>('J') &&
                value <= static_cast<uint8_t>('O'))) {
      value ^= 0x70U;
    }
    if (value == static_cast<uint8_t>('X') ||
        value == static_cast<uint8_t>('`')) {
      value ^= static_cast<uint8_t>('X' ^ '`');
    }
    return value;
  }

  void LoadDictionary(const uint8_t* data, size_t size) {
    std::string word;
    uint32_t line = 0;
    for (size_t position = 0; position < size; ++position) {
      const uint8_t value = data[position];
      if (value >= static_cast<uint8_t>('a') &&
          value <= static_cast<uint8_t>('z')) {
        word.push_back(static_cast<char>(value));
        continue;
      }
      if (word.empty()) continue;
      InstallWord(line, word);
      ++line;
      word.clear();
    }
    if (!word.empty()) {
      errno = EILSEQ;
      Fail("unterminated dictionary word");
    }
    dictionary_words_ = line;
    if (dictionary_words_ != kFixtureDictionaryWords) {
      errno = EINVAL;
      Fail("fixture dictionary word count");
    }
  }

  void InstallWord(uint32_t line, const std::string& word) {
    uint32_t code = 0;
    if (line < 80) {
      code = 0x80U + line;
    } else if (line < 3920) {
      code = 0xD0U + ((line - 80) / 80);
      code += (0x80U + ((line - 80) % 80)) << 8U;
    } else if (line < 44880) {
      code = 0xF0U + (((line - 3920) / 80) / 32);
      code += (0xD0U + (((line - 3920) / 80) % 32)) << 8U;
      code += (0x80U + ((line - 3920) % 80)) << 16U;
    } else {
      errno = ERANGE;
      Fail("dictionary line bound");
    }
    reverse_[code] = word;
  }

  void Emit(uint8_t value) {
    if (raw_position_ >= raw_size_ || raw_[raw_position_] != value) {
      errno = EILSEQ;
      Fail("raw byte identity");
    }
    raw_digest_ = FnvByte(raw_digest_, value);
    ++raw_position_;
  }

  void EmitWord(uint32_t code) {
    const auto found = reverse_.find(code);
    if (found == reverse_.end()) {
      errno = EILSEQ;
      Fail("unknown dictionary code");
    }
    const std::string& word = found->second;
    for (size_t i = 0; i < word.size(); ++i) {
      uint8_t value = static_cast<uint8_t>(word[i]);
      if (i == 0 && capitalized_) {
        value = static_cast<uint8_t>(value - 'a' + 'A');
        capitalized_ = false;
      }
      if (uppercase_) value = static_cast<uint8_t>(value - 'a' + 'A');
      Emit(value);
    }
  }

  void DecodeStored(uint8_t stored) {
    const uint8_t value = UndoRemap(stored);
    if (pending_escape_) {
      uppercase_ = false;
      pending_escape_ = false;
      Emit(value);
      return;
    }
    if (code_needed_ != 0) {
      code_ += static_cast<uint32_t>(value) << (8U * code_bytes_);
      ++code_bytes_;
      --code_needed_;
      if (code_bytes_ == 2 && value > 0xCFU) ++code_needed_;
      if (code_needed_ == 0) {
        EmitWord(code_);
        code_ = 0;
        code_bytes_ = 0;
      }
      return;
    }
    if (value == 0x0CU) {
      pending_escape_ = true;
    } else if (value == 0x07U) {
      uppercase_ = true;
    } else if (value == 0x40U) {
      capitalized_ = true;
    } else if (value == 0x06U) {
      uppercase_ = false;
    } else if (value >= 0x80U) {
      code_ = value;
      code_bytes_ = 1;
      code_needed_ = value > 0xCFU ? 1U : 0U;
      if (code_needed_ == 0) {
        EmitWord(code_);
        code_ = 0;
        code_bytes_ = 0;
      }
    } else {
      uint8_t literal = value;
      const bool alphabetic =
          (literal >= static_cast<uint8_t>('a') &&
           literal <= static_cast<uint8_t>('z')) ||
          (literal >= static_cast<uint8_t>('A') &&
           literal <= static_cast<uint8_t>('Z'));
      if (!alphabetic) uppercase_ = false;
      if (capitalized_ || uppercase_) {
        literal = static_cast<uint8_t>(literal - 'a' + 'A');
      }
      if (capitalized_) capitalized_ = false;
      Emit(literal);
    }
  }

  const uint8_t* raw_ = nullptr;
  uint64_t raw_size_ = 0;
  std::unordered_map<uint32_t, std::string> reverse_{};
  uint64_t raw_length_header_ = 0;
  uint64_t raw_position_ = 0;
  uint64_t raw_digest_ = kFnvOffset;
  uint64_t wrt_digest_ = kFnvOffset;
  bool uppercase_ = false;
  bool capitalized_ = false;
  bool pending_escape_ = false;
  uint32_t code_ = 0;
  uint32_t code_bytes_ = 0;
  uint32_t code_needed_ = 0;
  uint32_t dictionary_words_ = 0;
};

void CaptureReadyBoundaries(uint64_t coordinate, const CoordinateDecoder& decoder,
                            size_t* next, std::vector<BoundaryRow>* rows) {
  while (*next < kBoundaries.size() &&
         decoder.raw_position() >= kBoundaries[*next]) {
    rows->push_back(BoundaryRow{
        kBoundaries[*next], coordinate, decoder.raw_position(),
        decoder.StateDigest(coordinate),
    });
    ++*next;
  }
}

uint64_t CoderCoordinate(uint64_t wrt_coordinate) {
  if (wrt_coordinate > std::numeric_limits<uint64_t>::max() / 8ULL) {
    errno = EOVERFLOW;
    Fail("coder coordinate");
  }
  return wrt_coordinate * 8ULL;
}

const BoundaryRow& FindBoundary(const std::vector<BoundaryRow>& rows,
                                uint64_t raw_boundary) {
  const auto found = std::find_if(
      rows.begin(), rows.end(), [raw_boundary](const BoundaryRow& row) {
        return row.raw_boundary == raw_boundary;
      });
  if (found == rows.end()) {
    errno = EINVAL;
    Fail("missing boundary");
  }
  return *found;
}

void AppendScope(std::ostringstream* output, const char* name,
                 uint64_t raw_begin, uint64_t raw_end,
                 const std::vector<BoundaryRow>& rows, bool comma) {
  const BoundaryRow& begin = FindBoundary(rows, raw_begin);
  const BoundaryRow& end = FindBoundary(rows, raw_end);
  *output << "    \"" << name << "\": {\n"
          << "      \"rawBegin\": " << raw_begin << ",\n"
          << "      \"rawEnd\": " << raw_end << ",\n"
          << "      \"wrtBegin\": " << begin.wrt_coordinate << ",\n"
          << "      \"wrtEnd\": " << end.wrt_coordinate << ",\n"
          << "      \"coderBitBegin\": "
          << CoderCoordinate(begin.wrt_coordinate) << ",\n"
          << "      \"coderBitEnd\": "
          << CoderCoordinate(end.wrt_coordinate) << "\n"
          << "    }" << (comma ? "," : "") << "\n";
}

std::string FixtureJson(const MappedInput& store, const MappedInput& raw,
                        const MappedInput& dictionary) {
  if (store.size() != kFixtureStoreBytes || raw.size() != kFixtureRawBytes) {
    errno = EINVAL;
    Fail("fixture input geometry");
  }
  if (!std::equal(kExpectedWrapper.begin(), kExpectedWrapper.end(),
                  store.data())) {
    errno = EILSEQ;
    Fail("store wrapper");
  }
  const size_t wrt_size = store.size() - kStoreWrapperBytes;
  if (wrt_size != kFixtureWrtBytes) {
    errno = EINVAL;
    Fail("fixture WRT geometry");
  }

  CoordinateDecoder decoder(raw, dictionary);
  Sha256 transcript;
  std::vector<BoundaryRow> rows;
  size_t next_boundary = 0;
  for (uint64_t coordinate = 0; coordinate < wrt_size; ++coordinate) {
    CaptureReadyBoundaries(coordinate, decoder, &next_boundary, &rows);
    const auto span = decoder.Consume(
        store.data()[kStoreWrapperBytes + static_cast<size_t>(coordinate)],
        coordinate);
    HashU64(&transcript, coordinate);
    HashU64(&transcript, span.first);
    HashU64(&transcript, span.second);
  }
  decoder.Finish();
  CaptureReadyBoundaries(wrt_size, decoder, &next_boundary, &rows);
  if (next_boundary != kBoundaries.size() || rows.size() != kBoundaries.size()) {
    errno = EINVAL;
    Fail("boundary closure");
  }

  std::ostringstream output;
  output << "{\n"
         << "  \"schema\": \"gamma.enwiki9.harm-delta-scope-coordinate-map-fixture.v1\",\n"
         << "  \"mode\": \"fixture\",\n"
         << "  \"storeBytes\": " << store.size() << ",\n"
         << "  \"storeWrapperBytes\": " << kStoreWrapperBytes << ",\n"
         << "  \"wrtBytes\": " << wrt_size << ",\n"
         << "  \"rawBytes\": " << raw.size() << ",\n"
         << "  \"dictionaryBytes\": " << dictionary.size() << ",\n"
         << "  \"dictionaryWords\": " << decoder.dictionary_words() << ",\n"
         << "  \"inputSha256\": {\n"
         << "    \"store\": \"" << HashBytes(store.data(), store.size()) << "\",\n"
         << "    \"wrt\": \""
         << HashBytes(store.data() + kStoreWrapperBytes, wrt_size) << "\",\n"
         << "    \"raw\": \"" << HashBytes(raw.data(), raw.size()) << "\",\n"
         << "    \"dictionary\": \""
         << HashBytes(dictionary.data(), dictionary.size()) << "\"\n"
         << "  },\n"
         << "  \"mappingTranscriptSha256\": \""
         << Hex(transcript.Finalize()) << "\",\n"
         << "  \"terminal\": {\n"
         << "    \"rawLengthHeader\": " << decoder.raw_length_header() << ",\n"
         << "    \"rawPosition\": " << decoder.raw_position() << ",\n"
         << "    \"rawFnv64\": \"" << Hex64(decoder.raw_digest()) << "\",\n"
         << "    \"wrtFnv64\": \"" << Hex64(decoder.wrt_digest()) << "\"\n"
         << "  },\n"
         << "  \"boundaries\": [\n";
  for (size_t i = 0; i < rows.size(); ++i) {
    const BoundaryRow& row = rows[i];
    output << "    {\"rawBoundary\": " << row.raw_boundary
           << ", \"wrtCoordinate\": " << row.wrt_coordinate
           << ", \"coderBitCoordinate\": "
           << CoderCoordinate(row.wrt_coordinate)
           << ", \"rawBefore\": " << row.raw_before
           << ", \"frontendStateSha256\": \"" << row.state_sha256
           << "\"}" << (i + 1 == rows.size() ? "" : ",") << "\n";
  }
  output << "  ],\n"
         << "  \"scopes\": {\n";
  AppendScope(&output, "opening", 0, 14, rows, true);
  AppendScope(&output, "distant", 21, 30, rows, false);
  output << "  },\n"
         << "  \"corpusAccessCount\": 0,\n"
         << "  \"activeTraceAccessCount\": 0,\n"
         << "  \"authority\": {\n"
         << "    \"archiveAuthority\": false,\n"
         << "    \"nativeIntegrationAuthority\": false,\n"
         << "    \"retainedParentGainAuthority\": false,\n"
         << "    \"corpusExecutionAuthority\": false,\n"
         << "    \"objectiveCreditBytes\": 0\n"
         << "  }\n"
         << "}\n";
  return output.str();
}

std::string ProductionJson() {
  return std::string(
      "{\n"
      "  \"schema\": \"gamma.enwiki9.harm-delta-scope-coordinate-map-production-description.v1\",\n"
      "  \"mode\": \"production-description\",\n"
      "  \"storeBytes\": 647798597,\n"
      "  \"storeWrapperBytes\": 5,\n"
      "  \"wrtBytes\": 647798592,\n"
      "  \"rawBytes\": 1000000000,\n"
      "  \"dictionaryBytes\": 411996,\n"
      "  \"inputSha256\": {\n"
      "    \"store\": \"fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9\",\n"
      "    \"raw\": \"159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc\",\n"
      "    \"dictionary\": \"4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a\"\n"
      "  },\n"
      "  \"rawBoundaries\": [0, 1000000, 500000000, 510000000, 1000000000],\n"
      "  \"rawScopes\": {\n"
      "    \"opening\": [0, 1000000],\n"
      "    \"distant\": [500000000, 510000000]\n"
      "  },\n"
      "  \"boundaryLaw\": \"minimum-causal-wrt-coordinate-with-raw-before-greater-than-or-equal-to-raw-boundary\",\n"
      "  \"coderOrder\": \"eight-msb-first-bits-per-wrt-byte\",\n"
      "  \"productionExecutionExposed\": false,\n"
      "  \"objectiveCreditBytes\": 0\n"
      "}\n");
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 6 && std::strcmp(argv[1], "--fixture") == 0) {
      MappedInput store(argv[2]);
      MappedInput raw(argv[3]);
      MappedInput dictionary(argv[4]);
      const std::string result = FixtureJson(store, raw, dictionary);
      WriteExclusive(argv[5], result);
      return 0;
    }
    if (argc == 3 && std::strcmp(argv[1], "--describe-production") == 0) {
      WriteExclusive(argv[2], ProductionJson());
      return 0;
    }
    std::fprintf(stderr,
                 "usage: %s --fixture STORE RAW DICTIONARY OUTPUT_JSON\n"
                 "       %s --describe-production OUTPUT_JSON\n",
                 argv[0], argv[0]);
    return 64;
  } catch (const std::exception& error) {
    std::fprintf(stderr, "harm-delta-scope-mapper failure: %s\n", error.what());
    return 1;
  }
}
