// Observer successor only: the included, measured codec and model law are immutable.
// Archives retain v1 framing. Observation files are diagnostics, not codec inputs.
#define main midas_open_unobserved_main_v1
#include "midas_open_codec_v1.cpp"
#undef main
#include "../programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_population.hpp"

#include <array>
#include <span>

namespace {
constexpr std::size_t observer_file_limit = 32 * 1024 * 1024;
constexpr std::size_t snapshot_raw_limit = 129;
constexpr const char* observer_error = "midas_open_boundary_observer_v1: ";

// Anonymous, already-unlinked files stream during prediction. A process stop
// cannot leave a named probability/state trace mistaken for a complete result.
class ObserverStream {
 public:
  explicit ObserverStream(const fs::path& parent) {
    auto pattern = (parent / ".midas-observer-stream-XXXXXX").string();
    fd_ = ::mkstemp(pattern.data());
    require(fd_ >= 0, "cannot create private observer stream");
    if (::unlink(pattern.c_str()) != 0) {
      ::close(fd_); fd_ = -1;
      throw std::runtime_error("cannot unlink private observer stream");
    }
    require(::fcntl(fd_, F_SETFD, FD_CLOEXEC) == 0, "cannot protect observer descriptor");
  }
  ObserverStream(const ObserverStream&) = delete;
  ~ObserverStream() { if (fd_ >= 0) ::close(fd_); }
  void write(std::span<const std::uint8_t> bytes) {
    require(bytes.size() <= observer_file_limit - bytes_, "observer file exceeds byte ceiling");
    std::size_t offset = 0;
    while (offset < bytes.size()) {
      const auto n = ::write(fd_, bytes.data() + offset, bytes.size() - offset);
      if (n < 0 && errno == EINTR) continue;
      require(n > 0, "observer stream write failed"); offset += n;
    }
    bytes_ += bytes.size();
  }
  void text(const std::string& value) {
    write(std::span(reinterpret_cast<const std::uint8_t*>(value.data()), value.size()));
  }
  void publish(const fs::path& path) {
    require(::fsync(fd_) == 0 && ::lseek(fd_, 0, SEEK_SET) == 0, "observer stream sync failed");
    File target(::open(path.c_str(), O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600));
    std::array<std::uint8_t, 65536> buffer{};
    std::size_t copied = 0;
    while (copied < bytes_) {
      const auto n = ::read(fd_, buffer.data(), std::min(buffer.size(), bytes_ - copied));
      if (n < 0 && errno == EINTR) continue;
      require(n > 0, "observer stream copy read failed");
      std::size_t offset = 0;
      while (offset < std::size_t(n)) {
        const auto m = ::write(target.descriptor, buffer.data() + offset, n - offset);
        if (m < 0 && errno == EINTR) continue;
        require(m > 0, "observer stream copy write failed"); offset += m;
      }
      copied += n;
    }
    require(::fsync(target.descriptor) == 0, "observer output sync failed");
    const auto fd = target.descriptor; target.descriptor = -1;
    require(::close(fd) == 0, "observer output close failed");
  }
  std::size_t size() const { return bytes_; }
 private:
  int fd_ = -1;
  std::size_t bytes_ = 0;
};

struct StatePart { std::string name; std::size_t offset, bytes; };
// Parse only the versioned serialization produced by the unchanged classes.
// Ranges point into the complete snapshot; no state field is manufactured here.
class StateCursor {
 public:
  StateCursor(const Bytes& bytes, std::size_t begin, std::size_t size)
      : data_(bytes), position(begin), end_(begin + size) {
    require(begin <= bytes.size() && size <= bytes.size() - begin, "observer state range exceeds snapshot");
  }
  void skip(std::size_t count) {
    require(count <= end_ - position, "observer state range truncated"); position += count;
  }
  std::uint64_t integer(unsigned width) {
    require(width <= 8 && width <= end_ - position, "observer integer truncated");
    std::uint64_t value = 0;
    for (unsigned i = 0; i < width; ++i) value |= std::uint64_t(data_[position++]) << (8 * i);
    return value;
  }
  StatePart blob(const std::string& name) {
    const auto count = integer(8), begin = position; skip(count); return {name, begin, count};
  }
  void vector(unsigned width) {
    const auto count = integer(8);
    require(count <= (end_ - position) / width, "observer vector truncated"); skip(count * width);
  }
  void magic(const char* expected) {
    require(end_ - position >= 5 && std::memcmp(data_.data() + position, expected, 5) == 0,
            "observer serialization version differs"); skip(5);
  }
  void finish() const { require(position == end_, "observer serialization has unparsed bytes"); }
  const Bytes& data_;
  std::size_t position;
 private:
  std::size_t end_;
};

std::vector<StatePart> state_parts(const Bytes& state, const Predictor& model) {
  std::vector<StatePart> parts{{"complete_state", 0, state.size()}};
  StateCursor envelope(state, 0, state.size()); envelope.magic("GMST\1");
  for (const auto name : {"complete_predictor", "parent_identity_projection", "normalized_coder", "reference_model_projection"})
    parts.push_back(envelope.blob(name));
  envelope.finish();
  StateCursor predictor(state, parts[1].offset, parts[1].bytes); predictor.magic("MBIT\1");
  const auto schedule = predictor.blob("scheduler"), prefix = predictor.blob("byte_prefix");
  predictor.finish(); parts.push_back(schedule); parts.push_back(prefix);
  StateCursor scheduler(state, schedule.offset, schedule.bytes); scheduler.magic("MSCH\1");
  scheduler.skip(1 + 8 + 8 + 1 + 256 * 4);
  parts.push_back(scheduler.blob("decoded_prefix"));
  parts.push_back(scheduler.blob("sequence_origin"));
  const auto backend = scheduler.blob("backend_model");
  // The scheduler digest above also includes arm, update counters and K shadow.
  parts.push_back({"scheduler_update_counters", scheduler.position, 16}); scheduler.skip(16);
  parts.push_back(scheduler.blob("discarded_shadow")); scheduler.finish();
  StateCursor native(state, backend.offset, backend.bytes); native.magic("OPFI\1");
  native.skip(4 + 8 + 1 + 3); const auto prefix_bytes = native.integer(1); native.skip(prefix_bytes);
  parts.push_back({"model_header_prefix", backend.offset, native.position - backend.offset});
  const auto cache_begin = native.position; native.skip(256 * 4);
  parts.push_back({"model_probability_cache", cache_begin, native.position - cache_begin});
  const auto memory_begin = native.position;
  for (std::size_t i = 0; i < Model::geometry().layers; ++i) native.vector(2);
  parts.push_back({"recurrent_memory", memory_begin, native.position - memory_begin});
  const auto parameters_begin = native.position;
  const auto parameters = model.schedule().model().parameter_states();
  for (const auto& parameter : parameters) {
    const auto begin = native.position; native.skip(parameter.second.size());
    require(std::equal(parameter.second.begin(), parameter.second.end(), state.begin() + begin),
            "observer parameter range differs from named model snapshot");
  }
  parts.push_back({"parameters", parameters_begin, native.position - parameters_begin});
  const auto optimizer_begin = native.position; native.skip(8);
  for (std::size_t i = 0; i < parameters.size(); ++i) {
    native.vector(2); native.vector(2); native.vector(4);
  }
  parts.push_back({"optimizer_moments_and_compensation", optimizer_begin, native.position - optimizer_begin});
  parts.push_back(native.blob("incremental_cache")); native.finish();
  return parts;
}

class BoundaryObserver {
 public:
  BoundaryObserver(const fs::path& parent, std::size_t raw_bytes, unsigned arm, bool snapshots)
      : probabilities(parent), boundaries(parent), states(parent), snapshots_(snapshots) {
    require(!snapshots || raw_bytes <= snapshot_raw_limit, "exact boundary snapshots require at most 129 raw bytes");
    Bytes header{'M','O','P','R','O','B','0','1'}; put(header, raw_bytes, 8);
    put(header, Model::model_tag, 4); put(header, arm, 1); probabilities.write(header);
    Bytes snapshot_header{'M','O','S','N','A','P','0','1'}; put(snapshot_header, snapshots, 1);
    states.write(snapshot_header);
  }
  void probability(std::uint16_t value) {
    // Called after predict(), before encoder truth access / decoder.decode().
    require(value > 0, "observer encountered zero Q16 probability");
    buffer_.push_back(value & 255); buffer_.push_back(value >> 8); ++bits_;
    if (buffer_.size() == 65536) flush();
  }
  void boundary(const char* kind, unsigned tag, const Predictor& model, const Bytes& coder) {
    require(model.bit_position() == bits_, "observer probability clock differs from model");
    const auto state = complete_state(model, coder); const auto parts = state_parts(state, model);
    std::ostringstream row;
    row << "{\"kind\":\"" << kind << "\",\"bit_position\":" << bits_
        << ",\"model_updates\":" << model.schedule().model().updates()
        << ",\"parent_updates\":" << model.schedule().parent_updates()
        << ",\"midpoint_updates\":" << model.schedule().midpoint_updates()
        << ",\"shadow_updates\":" << model.schedule().shadow_updates() << ",\"parts\":[";
    bool first = true;
    for (const auto& part : parts) {
      if (!first) row << ',';
      first = false;
      row << "{\"name\":\"" << part.name << "\",\"offset\":" << part.offset << ",\"bytes\":" << part.bytes
          << ",\"sha256\":\"" << gamma_enwiki9::nncp::Sha256Hex(
               std::span(state.data() + part.offset, part.bytes)) << "\"}";
    }
    row << "]}\n"; boundaries.text(row.str());
    if (snapshots_) {
      Bytes header; put(header, tag, 1); put(header, bits_, 8); put(header, state.size(), 8);
      states.write(header); states.write(state);
    }
    ++records_;
  }
  void flush() { probabilities.write(buffer_); buffer_.clear(); }
  std::uint64_t records() const { return records_; }
  ObserverStream probabilities, boundaries, states;
 private:
  bool snapshots_;
  Bytes buffer_;
  std::uint64_t bits_ = 0, records_ = 0;
};

class ObservedBundle {
 public:
  explicit ObservedBundle(const fs::path& destination) : destination_(destination) {
    check_destination(destination);
    auto pattern = (destination.parent_path() / ".midas-observed-XXXXXX").string();
    const auto name = ::mkdtemp(pattern.data()); require(name != nullptr, "cannot create observed output staging");
    staging_ = name;
  }
  ~ObservedBundle() {
    if (staging_.empty()) return;
    for (const auto name : {"data", "state.bin", "summary.json", "probabilities.bin", "boundaries.jsonl", "snapshots.bin"})
      ::unlink((staging_ / name).c_str());
    ::rmdir(staging_.c_str());
  }
  void publish(const Bytes& output, const Bytes& state, const std::string& summary, BoundaryObserver& observer) {
    // All streams and ordinary outputs use the same checked sync/close path.
    for (const auto& item : std::array<std::pair<const char*, const Bytes*>, 2>{{{"data", &output}, {"state.bin", &state}}}) {
      ObserverStream stream(destination_.parent_path()); stream.write(*item.second); stream.publish(staging_ / item.first);
    }
    ObserverStream summary_stream(destination_.parent_path()); summary_stream.text(summary);
    summary_stream.publish(staging_ / "summary.json");
    observer.probabilities.publish(staging_ / "probabilities.bin");
    observer.boundaries.publish(staging_ / "boundaries.jsonl");
    observer.states.publish(staging_ / "snapshots.bin");
    File directory(::open(staging_.c_str(), O_RDONLY | O_DIRECTORY | O_CLOEXEC));
    require(::fsync(directory.descriptor) == 0, "observed directory sync failed");
    require(::syscall(SYS_renameat2, AT_FDCWD, staging_.c_str(), AT_FDCWD, destination_.c_str(),
                      1U /* RENAME_NOREPLACE */) == 0, "observed output publication refused");
    staging_.clear();
  }
 private:
  fs::path destination_, staging_;
};
}  // namespace

int main(int argc, char** argv) {
  try {
    require(argc == 7, "usage: midas-boundary-observer encode/decode P/K/F/S MAX_RAW_BYTES INPUT NEW_OUTPUT_DIRECTORY digest/snapshots");
    const std::string operation = argv[1], observation = argv[6];
    require(operation == "encode" || operation == "decode", "operation must be encode or decode");
    require(observation == "digest" || observation == "snapshots", "observation must be digest or snapshots");
    const auto arm = parse_arm(argv[2]); const auto limit = raw_limit(argv[3]);
    const auto archive_limit = 32 * limit + 64;
    set_bound(RLIMIT_AS, memory_limit); set_bound(RLIMIT_CPU, 120); set_bound(RLIMIT_FSIZE, observer_file_limit);
    const auto destination = fs::absolute(argv[5]); check_destination(destination);
    const auto start = std::chrono::steady_clock::now(); const auto cpu = std::clock();
    const auto input = read_input(argv[4], operation == "encode" ? limit : archive_limit);
    const auto archive_arm = arm == Arm::F ? 1 : arm == Arm::S ? 2 : 0;
    // Unframe before allocating observers so rejected headers cannot publish diagnostics.
    const auto raw_bytes = operation == "encode" ? input.size() : unframe(input, Model::model_tag, limit, archive_limit).raw_bytes;
    BoundaryObserver observer(destination.parent_path(), raw_bytes, archive_arm, observation == "snapshots");
    Predictor model(Model{}, arm); Bytes raw, output, state;
    if (operation == "encode") {
      raw = input; Encoder coder;
      observer.boundary("initial", 0, model, coder.comparison_state());
      for (auto byte : raw) for (int shift = 7; shift >= 0; --shift) {
        const auto probability = model.predict(); observer.probability(probability);
        const auto truth = std::uint16_t((byte >> shift) & 1U);
        coder.encode(truth, probability); model.observe(truth);
        if (model.bit_position() % 256 == 0) observer.boundary("boundary", 1, model, coder.comparison_state());
      }
      output = frame(raw, coder.finish(), Model::model_tag, archive_arm);
      require(output.size() <= archive_limit, "encoded archive exceeds operational ceiling");
      observer.boundary("final", 2, model, coder.comparison_state());
      state = complete_state(model, coder.comparison_state());
    } else {
      const auto framed = unframe(input, Model::model_tag, limit, archive_limit);
      require(framed.arm == archive_arm, "archive arm differs from decoder law");
      Decoder coder(framed.payload); raw.reserve(framed.raw_bytes);
      observer.boundary("initial", 0, model, coder.comparison_state());
      for (std::size_t i = 0; i < framed.raw_bytes; ++i) {
        unsigned byte = 0;
        for (unsigned bit = 0; bit != 8; ++bit) {
          const auto probability = model.predict(); observer.probability(probability);
          const auto truth = coder.decode(probability); model.observe(truth); byte = (byte << 1) | truth;
          if (model.bit_position() % 256 == 0) observer.boundary("boundary", 1, model, coder.comparison_state());
        }
        raw.push_back(static_cast<std::uint8_t>(byte));
      }
      coder.finish(); verify_inverse(framed, raw);
      observer.boundary("final", 2, model, coder.comparison_state());
      output = raw; state = complete_state(model, coder.comparison_state());
    }
    observer.flush();
    struct rusage usage{}; require(::getrusage(RUSAGE_SELF, &usage) == 0, "resource observation failed");
    std::ostringstream summary; summary.precision(12);
    summary << "{\"schema\":\"midas_open_boundary_observer_v1\",\"operation\":\"" << operation
            << "\",\"arm\":\"" << argv[2] << "\",\"frontend\":\"raw_identity_v1\",\"raw_bytes\":" << raw.size()
            << ",\"archive_bytes\":" << (operation == "encode" ? output.size() : input.size())
            << ",\"state_bytes\":" << state.size() << ",\"max_raw_bytes\":" << limit
            << ",\"probability_records\":" << raw.size() * 8 << ",\"boundary_records\":" << observer.records()
            << ",\"probability_bytes\":" << observer.probabilities.size() << ",\"boundary_bytes\":" << observer.boundaries.size()
            << ",\"snapshot_bytes\":" << observer.states.size() << ",\"exact_snapshots\":" << (observation == "snapshots" ? "true" : "false")
            << ",\"model_updates\":" << model.schedule().model().updates() << ",\"process_peak_rss_kib\":" << usage.ru_maxrss
            << ",\"observed_codec_cpu_seconds\":" << double(std::clock() - cpu) / CLOCKS_PER_SEC
            << ",\"observed_codec_wall_seconds\":" << std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count()
            << ",\"timing_scope\":\"whole codec including observer; excludes final publication; shared-host diagnostic\""
            << ",\"resource_qualified\":false,\"complete_package_bytes\":null,\"objective_credit_bytes\":0}\n";
    ObservedBundle bundle(destination); bundle.publish(output, state, summary.str(), observer);
    std::cout << summary.str(); require(bool(std::cout), "observer stdout publication failed");
    return 0;
  } catch (const std::exception& error) {
    std::cerr << observer_error << error.what() << '\n'; return 1;
  }
}
