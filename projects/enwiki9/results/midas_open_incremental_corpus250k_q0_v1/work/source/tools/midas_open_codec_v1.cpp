// Bounded standalone open MIDAS codec. New driver; retained model law unchanged.
// This executable does not authorize a corpus experiment or claim qualification.
#ifdef GAMMA_MIDAS_REFERENCE
#include "../lib/midas_open_profile_fixture.hpp"
#else
#include "../lib/midas_open_profile_incremental_fixture.hpp"
#endif

#include <cerrno>
#include <charconv>
#include <chrono>
#include <cstring>
#include <ctime>
#include <fcntl.h>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

using namespace gamma_enwiki9::midas_codec;
namespace fs = std::filesystem;
#ifdef GAMMA_MIDAS_REFERENCE
using Model = OpenProfileFixture;
#else
using Model = OpenProfileIncrementalFixture;
#endif
using Predictor = MidpointBitPredictor<Model>;

namespace {
constexpr std::size_t maximum_raw_limit = 250000;
constexpr std::size_t memory_limit = 512 * 1024 * 1024;

struct File {
  int descriptor = -1;
  explicit File(int fd) : descriptor(fd) { require(fd >= 0, "file open failed"); }
  File(const File&) = delete;
  ~File() { if (descriptor >= 0) ::close(descriptor); }
};

bool same_file(const struct stat& a, const struct stat& b) {
  return a.st_dev == b.st_dev && a.st_ino == b.st_ino && a.st_size == b.st_size &&
         a.st_mtim.tv_sec == b.st_mtim.tv_sec && a.st_mtim.tv_nsec == b.st_mtim.tv_nsec &&
         a.st_ctim.tv_sec == b.st_ctim.tv_sec && a.st_ctim.tv_nsec == b.st_ctim.tv_nsec;
}
Bytes read_input(const fs::path& path, std::size_t limit) {
  File file(::open(path.c_str(), O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC));
  struct stat before{}, after{}, current{};
  require(::fstat(file.descriptor, &before) == 0 && S_ISREG(before.st_mode), "input must be a regular file");
  require(before.st_size >= 0 && std::uint64_t(before.st_size) <= limit, "input byte limit exceeded");
  Bytes bytes(static_cast<std::size_t>(before.st_size));
  std::size_t offset = 0;
  while (offset < bytes.size()) {
    const auto count = ::read(file.descriptor, bytes.data() + offset, bytes.size() - offset);
    if (count < 0 && errno == EINTR) continue;
    require(count > 0, "input changed or read failed"); offset += count;
  }
  std::uint8_t extra;
  require(::read(file.descriptor, &extra, 1) == 0 && ::fstat(file.descriptor, &after) == 0 &&
          ::lstat(path.c_str(), &current) == 0 && same_file(before, after) && same_file(after, current),
          "input changed while read");
  return bytes;
}

void write_file(const fs::path& path, const Bytes& bytes) {
  File file(::open(path.c_str(), O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600));
  std::size_t offset = 0;
  while (offset < bytes.size()) {
    const auto count = ::write(file.descriptor, bytes.data() + offset, bytes.size() - offset);
    if (count < 0 && errno == EINTR) continue;
    require(count > 0, "output write failed"); offset += count;
  }
  require(::fsync(file.descriptor) == 0, "output sync failed");
}

// Stage all files together; publish the directory once, without replacing any
// existing file, directory or symlink. Failed inverses never publish output.
void check_destination(const fs::path& destination) {
  require(!destination.filename().empty() && destination.filename() != "." && destination.filename() != "..",
          "output requires a new named directory");
  struct stat existing{};
  require(::lstat(destination.c_str(), &existing) != 0 && errno == ENOENT, "output already exists or cannot be inspected");
}

class OutputBundle {
 public:
  explicit OutputBundle(const fs::path& destination) : destination_(destination) {
    check_destination(destination);
    auto pattern = (destination.parent_path() / ".midas-codec-XXXXXX").string();
    char* name = ::mkdtemp(pattern.data()); require(name != nullptr, "cannot create output staging directory");
    staging_ = name;
  }
  ~OutputBundle() {
    if (staging_.empty()) return;
    // Only these three private, known files can be created by this driver.
    for (const auto name : {"data", "state.bin", "summary.json"}) ::unlink((staging_ / name).c_str());
    ::rmdir(staging_.c_str());
  }
  void publish(const Bytes& output, const Bytes& state, const std::string& summary) {
    write_file(staging_ / "data", output);
    write_file(staging_ / "state.bin", state);
    write_file(staging_ / "summary.json", Bytes(summary.begin(), summary.end()));
    File directory(::open(staging_.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC));
    require(::fsync(directory.descriptor) == 0, "staging directory sync failed");
    require(::syscall(SYS_renameat2, AT_FDCWD, staging_.c_str(), AT_FDCWD, destination_.c_str(),
                      1U /* RENAME_NOREPLACE */) == 0, "output publication refused");
    staging_.clear();
  }
 private:
  fs::path destination_, staging_;
};

std::size_t raw_limit(const char* text) {
  std::size_t result = 0;
  const auto end = text + std::strlen(text);
  const auto parsed = std::from_chars(text, end, result);
  require(parsed.ec == std::errc{} && parsed.ptr == end && result > 0 && result <= maximum_raw_limit,
          "raw limit must be an explicit integer in 1..250000");
  return result;
}
Arm parse_arm(const std::string& name) {
  require(name.size() == 1, "arm must be P/K/F/S");
  const auto index = std::string("PKFS").find(name);
  require(index != std::string::npos, "arm must be P/K/F/S");
  return static_cast<Arm>(index);
}
void set_bound(int resource, rlim_t bound) {
  struct rlimit existing{};
  require(::getrlimit(resource, &existing) == 0, "cannot inspect resource limit");
  const auto ceiling = std::min(bound, existing.rlim_max);
  const struct rlimit limit{std::min(ceiling, existing.rlim_cur), ceiling};
  require(::setrlimit(resource, &limit) == 0, "cannot set resource limit");
}
Bytes complete_state(const Predictor& model, const Bytes& coder) {
  Bytes out{'G','M','S','T',1};
  // Common predictor/coder state only. Decoder code/input cursor are role-local;
  // they are already checked by finite decoding and are not made falsely equal.
  const auto full = model.serialize(), parent = model.parent_identity_state();
#ifdef GAMMA_MIDAS_REFERENCE
  const auto reference = model.schedule().model().serialize();
#else
  const auto reference = model.schedule().model().reference_state();
#endif
  for (const auto* part : {&full, &parent, &coder, &reference}) {
    put(out, part->size(), 8); out.insert(out.end(), part->begin(), part->end());
  }
  return out;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    require(argc == 6, "usage: midas-open-codec encode/decode P/K/F/S MAX_RAW_BYTES INPUT NEW_OUTPUT_DIRECTORY");
    const std::string operation = argv[1];
    require(operation == "encode" || operation == "decode", "operation must be encode or decode");
    const auto arm = parse_arm(argv[2]); const auto limit = raw_limit(argv[3]);
    // Explicit operational ceiling, not a proved archive-size bound or a prize
    // resource certificate. Larger populations require a separately frozen driver.
    const auto archive_limit = 32 * limit + 64;
    set_bound(RLIMIT_AS, memory_limit); set_bound(RLIMIT_CPU, 120); set_bound(RLIMIT_FSIZE, 32 * 1024 * 1024);
    const auto destination = fs::absolute(argv[5]);
    check_destination(destination);
    const auto start = std::chrono::steady_clock::now(); const auto cpu = std::clock();
    const auto input = read_input(argv[4], operation == "encode" ? limit : archive_limit);
    Predictor model(Model{}, arm);
    Bytes raw, output, state;
    const auto archive_arm = arm == Arm::F ? 1 : arm == Arm::S ? 2 : 0;
    if (operation == "encode") {
      raw = input; Encoder coder;
      for (auto byte : raw) for (int shift = 7; shift >= 0; --shift) {
        const auto probability = model.predict(), truth = std::uint16_t((byte >> shift) & 1U);
        coder.encode(truth, probability); model.observe(truth);
      }
      output = frame(raw, coder.finish(), Model::model_tag, archive_arm);
      require(output.size() <= archive_limit, "encoded archive exceeds operational ceiling");
      state = complete_state(model, coder.comparison_state());
    } else {
      const auto framed = unframe(input, Model::model_tag, limit, archive_limit);
      require(framed.arm == archive_arm, "archive arm differs from decoder law");
      Decoder coder(framed.payload); raw.reserve(framed.raw_bytes);
      for (std::size_t i = 0; i < framed.raw_bytes; ++i) {
        unsigned byte = 0;
        for (unsigned bit = 0; bit != 8; ++bit) {
          const auto truth = coder.decode(model.predict()); model.observe(truth); byte = (byte << 1) | truth;
        }
        raw.push_back(static_cast<std::uint8_t>(byte));
      }
      coder.finish(); verify_inverse(framed, raw);
      output = raw; state = complete_state(model, coder.comparison_state());
    }
    struct rusage usage{}; require(::getrusage(RUSAGE_SELF, &usage) == 0, "resource observation failed");
    std::ostringstream summary;
    summary.precision(12);
    summary << "{\"schema\":\"midas_open_codec_operation_v1\",\"operation\":\"" << operation
            << "\",\"arm\":\"" << argv[2] << "\",\"frontend\":\"raw_identity_v1\",\"raw_bytes\":" << raw.size()
            << ",\"archive_bytes\":" << (operation == "encode" ? output.size() : input.size())
            << ",\"state_bytes\":" << state.size() << ",\"max_raw_bytes\":" << limit
            << ",\"model_updates\":" << model.schedule().model().updates()
            << ",\"process_peak_rss_kib\":" << usage.ru_maxrss
            << ",\"codec_cpu_seconds\":" << double(std::clock() - cpu) / CLOCKS_PER_SEC
            << ",\"codec_wall_seconds\":" << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count()
            << ",\"publication_included_in_codec_timing\":false,\"resource_qualified\":false,\"objective_credit_bytes\":0}\n";
    // Do not allocate staging during prediction/training: resource stops before
    // publication leave neither a result nor a private staging directory.
    OutputBundle bundle(destination);
    bundle.publish(output, state, summary.str());
    std::cout << summary.str();
    return 0;
  } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
