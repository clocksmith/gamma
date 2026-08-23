#include "wiki-pda-overlay.h"

#include <algorithm>
#include <cstdlib>
#include <cstring>

namespace {

const unsigned char kTransformedLt = 'L';
const unsigned char kTransformedGt = 'N';

WikiPdaOverlay::Arm ParseArm() {
  const char* value = std::getenv("KH_WIKI_PDA_ARM");
  if (value == NULL || value[0] == 0) return WikiPdaOverlay::Arm::DIRECT;
  if (value[1] != 0) std::abort();
  switch (value[0]) {
    case 'P': return WikiPdaOverlay::Arm::PARENT;
    case 'K': return WikiPdaOverlay::Arm::BOOKKEEPING;
    case 'D': return WikiPdaOverlay::Arm::DIRECT;
    case 'R': return WikiPdaOverlay::Arm::RANDOM_PERMUTATION;
    case 'S': return WikiPdaOverlay::Arm::SHIFTED;
    default: std::abort();
  }
}

std::uint64_t NextRandom(std::uint64_t* state) {
  std::uint64_t x = *state;
  x ^= x >> 12;
  x ^= x << 25;
  x ^= x >> 27;
  *state = x;
  return x * UINT64_C(2685821657736338717);
}

}  // namespace

WikiPdaOverlay::WikiPdaOverlay()
    : arm_(ParseArm()),
      mode_(Mode::OUTSIDE),
      depth_(0),
      quote_(0),
      last_nonspace_(0),
      close_position_(0),
      next_valid_(false),
      next_truth_(0),
      next_arm_(0),
      next_bucket_(0),
      line_length_(0) {
  for (std::size_t i = 0; i < stack_.size(); ++i) ClearName(&stack_[i]);
  ClearName(&current_name_);
  random_order_.fill(0);
  correct_.fill(0);
  total_.fill(0);
  line_prefix_.fill(0);
}

bool WikiPdaOverlay::IsSpace(unsigned char byte) {
  return byte == ' ' || byte == '\t' || byte == '\r' || byte == '\n';
}

bool WikiPdaOverlay::NamesEqual(const Name& left, const Name& right) {
  return left.valid && right.valid && left.length == right.length &&
      std::memcmp(left.bytes.data(), right.bytes.data(), left.length) == 0;
}

void WikiPdaOverlay::ClearName(Name* name) {
  name->bytes.fill(0);
  name->length = 0;
  name->valid = true;
}

void WikiPdaOverlay::AppendNameByte(Name* name, unsigned char byte) {
  if (!name->valid) return;
  if (name->length >= kMaxName) {
    name->valid = false;
    return;
  }
  name->bytes[name->length++] = byte;
}

void WikiPdaOverlay::ResetParser() {
  mode_ = Mode::OUTSIDE;
  depth_ = 0;
  ClearName(&current_name_);
  quote_ = 0;
  last_nonspace_ = 0;
  close_position_ = 0;
  next_valid_ = false;
}

bool WikiPdaOverlay::TrackLine(unsigned char byte) {
  if (byte == '\n') {
    const bool marker =
        (line_length_ == 3 &&
         line_prefix_[0] == 0xDF &&
         line_prefix_[1] == 0x99 &&
         line_prefix_[2] == kTransformedGt) ||
        (line_length_ == 4 &&
         line_prefix_[0] == 0xDF &&
         line_prefix_[1] == 0x99 &&
         line_prefix_[2] == kTransformedGt &&
         line_prefix_[3] == '\r');
    line_prefix_.fill(0);
    line_length_ = 0;
    return marker;
  }
  if (line_length_ < line_prefix_.size()) line_prefix_[line_length_] = byte;
  if (line_length_ < line_prefix_.size() + 1) ++line_length_;
  return false;
}

void WikiPdaOverlay::UpdatePriorTrial(unsigned char actual) {
  if (!next_valid_) return;
  const std::size_t bucket = next_bucket_;
  if (actual == next_truth_) ++correct_[bucket];
  ++total_[bucket];
  if (total_[bucket] >= (1u << 20)) {
    correct_[bucket] = (correct_[bucket] + 1) >> 1;
    total_[bucket] = (total_[bucket] + 1) >> 1;
  }
}

void WikiPdaOverlay::BuildRandomPermutation() {
  if (depth_ == 0) return;
  const Name& top = stack_[depth_ - 1];
  for (std::size_t i = 0; i < top.length; ++i) {
    random_order_[i] = static_cast<unsigned char>(i);
  }
  std::uint64_t state = UINT64_C(1469598103934665603);
  for (std::size_t i = 0; i < top.length; ++i) {
    state ^= top.bytes[i];
    state *= UINT64_C(1099511628211);
  }
  state ^= static_cast<std::uint64_t>(depth_) << 32;
  if (state == 0) state = UINT64_C(0x9e3779b97f4a7c15);
  for (std::size_t i = top.length; i > 1; --i) {
    const std::size_t j =
        static_cast<std::size_t>(NextRandom(&state) % i);
    std::swap(random_order_[i - 1], random_order_[j]);
  }
}

void WikiPdaOverlay::PrepareNextReplay() {
  next_valid_ = false;
  if (depth_ == 0) return;
  const Name& top = stack_[depth_ - 1];
  if (!top.valid || top.length == 0 || close_position_ >= top.length) return;

  next_truth_ = top.bytes[close_position_];
  next_bucket_ = static_cast<unsigned char>(
      std::min(close_position_, kStatBuckets - 1));
  switch (arm_) {
    case Arm::RANDOM_PERMUTATION:
      next_arm_ = top.bytes[random_order_[close_position_]];
      break;
    case Arm::SHIFTED:
      next_arm_ = top.bytes[(close_position_ + 1) % top.length];
      break;
    case Arm::PARENT:
    case Arm::BOOKKEEPING:
    case Arm::DIRECT:
      next_arm_ = next_truth_;
      break;
  }
  next_valid_ = true;
}

void WikiPdaOverlay::BeginClosingReplay() {
  ClearName(&current_name_);
  close_position_ = 0;
  BuildRandomPermutation();
  PrepareNextReplay();
}

void WikiPdaOverlay::PushOpeningName() {
  if (!current_name_.valid || current_name_.length == 0) return;
  if (depth_ == kMaxDepth) {
    for (std::size_t i = 1; i < depth_; ++i) stack_[i - 1] = stack_[i];
    --depth_;
  }
  stack_[depth_++] = current_name_;
}

void WikiPdaOverlay::FinishClosingName() {
  if (!current_name_.valid || current_name_.length == 0) return;
  for (std::size_t i = depth_; i > 0; --i) {
    if (NamesEqual(stack_[i - 1], current_name_)) {
      depth_ = i - 1;
      return;
    }
  }
}

void WikiPdaOverlay::ParseByte(unsigned char byte) {
  switch (mode_) {
    case Mode::OUTSIDE:
      if (byte == kTransformedLt) mode_ = Mode::AFTER_LT;
      break;

    case Mode::AFTER_LT:
      if (byte == '/') {
        mode_ = Mode::CLOSE_NAME;
        BeginClosingReplay();
      } else if (byte == '!' || byte == '?') {
        mode_ = Mode::IGNORED_TAG;
        quote_ = 0;
      } else if (byte == kTransformedGt) {
        mode_ = Mode::OUTSIDE;
      } else if (IsSpace(byte)) {
        mode_ = Mode::OUTSIDE;
      } else {
        ClearName(&current_name_);
        AppendNameByte(&current_name_, byte);
        mode_ = Mode::OPEN_NAME;
      }
      break;

    case Mode::OPEN_NAME:
      if (byte == kTransformedGt) {
        PushOpeningName();
        mode_ = Mode::OUTSIDE;
      } else if (IsSpace(byte)) {
        last_nonspace_ = 0;
        quote_ = 0;
        mode_ = Mode::OPEN_REST;
      } else if (byte == '/') {
        last_nonspace_ = '/';
        quote_ = 0;
        mode_ = Mode::OPEN_REST;
      } else {
        AppendNameByte(&current_name_, byte);
      }
      break;

    case Mode::OPEN_REST:
      if (quote_ != 0) {
        if (byte == quote_) quote_ = 0;
      } else if (byte == '\'' || byte == '"') {
        quote_ = byte;
        last_nonspace_ = byte;
      } else if (byte == kTransformedGt) {
        if (last_nonspace_ != '/') PushOpeningName();
        mode_ = Mode::OUTSIDE;
      } else if (!IsSpace(byte)) {
        last_nonspace_ = byte;
      }
      break;

    case Mode::CLOSE_NAME:
      if (byte == kTransformedGt) {
        FinishClosingName();
        next_valid_ = false;
        mode_ = Mode::OUTSIDE;
      } else if (IsSpace(byte)) {
        next_valid_ = false;
        mode_ = Mode::CLOSE_REST;
      } else {
        AppendNameByte(&current_name_, byte);
        ++close_position_;
        PrepareNextReplay();
      }
      break;

    case Mode::CLOSE_REST:
      if (byte == kTransformedGt) {
        FinishClosingName();
        mode_ = Mode::OUTSIDE;
      }
      break;

    case Mode::IGNORED_TAG:
      if (quote_ != 0) {
        if (byte == quote_) quote_ = 0;
      } else if (byte == '\'' || byte == '"') {
        quote_ = byte;
      } else if (byte == kTransformedGt) {
        mode_ = Mode::OUTSIDE;
      }
      break;
  }
}

void WikiPdaOverlay::Observe(unsigned char byte) {
  if (arm_ == Arm::PARENT) return;
  UpdatePriorTrial(byte);
  next_valid_ = false;
  ParseByte(byte);
  if (TrackLine(byte)) ResetParser();
}

float WikiPdaOverlay::ReplayProbability() const {
  const std::size_t bucket = next_bucket_;
  float probability =
      (static_cast<float>(correct_[bucket]) + 1.0f) /
      (static_cast<float>(total_[bucket]) + 256.0f);
  const float uniform = 1.0f / 256.0f;
  if (probability < uniform) probability = uniform;
  const float maximum = 65535.0f / 65536.0f;
  if (probability > maximum) probability = maximum;
  return probability;
}

bool WikiPdaOverlay::NextPrediction(
    unsigned char* expected, float* probability) const {
  if (!next_valid_ ||
      (arm_ != Arm::DIRECT &&
       arm_ != Arm::RANDOM_PERMUTATION &&
       arm_ != Arm::SHIFTED)) {
    return false;
  }
  *expected = next_arm_;
  *probability = ReplayProbability();
  return true;
}

void WikiPdaOverlay::HashByte(
    std::uint64_t* hash, unsigned char value) const {
  *hash ^= value;
  *hash *= UINT64_C(1099511628211);
}

void WikiPdaOverlay::HashU32(
    std::uint64_t* hash, std::uint32_t value) const {
  for (int shift = 0; shift < 32; shift += 8) {
    HashByte(hash, static_cast<unsigned char>((value >> shift) & 0xFF));
  }
}

std::uint64_t WikiPdaOverlay::StateDigest() const {
  std::uint64_t hash = UINT64_C(1469598103934665603);
  HashByte(&hash, static_cast<unsigned char>(arm_));
  HashByte(&hash, static_cast<unsigned char>(mode_));
  HashByte(&hash, static_cast<unsigned char>(depth_));
  for (std::size_t i = 0; i < depth_; ++i) {
    HashByte(&hash, stack_[i].length);
    HashByte(&hash, stack_[i].valid ? 1 : 0);
    for (std::size_t j = 0; j < stack_[i].length; ++j) {
      HashByte(&hash, stack_[i].bytes[j]);
    }
  }
  HashByte(&hash, current_name_.length);
  HashByte(&hash, current_name_.valid ? 1 : 0);
  for (std::size_t i = 0; i < current_name_.length; ++i) {
    HashByte(&hash, current_name_.bytes[i]);
  }
  HashByte(&hash, quote_);
  HashByte(&hash, last_nonspace_);
  HashByte(&hash, static_cast<unsigned char>(close_position_));
  HashByte(&hash, next_valid_ ? 1 : 0);
  HashByte(&hash, next_truth_);
  HashByte(&hash, next_arm_);
  HashByte(&hash, next_bucket_);
  for (unsigned char value : random_order_) {
    HashByte(&hash, value);
  }
  for (unsigned char value : line_prefix_) {
    HashByte(&hash, value);
  }
  HashByte(&hash, line_length_);
  for (std::size_t i = 0; i < kStatBuckets; ++i) {
    HashU32(&hash, correct_[i]);
    HashU32(&hash, total_[i]);
  }
  return hash;
}
