#ifndef GAMMA_FX2_CLOSING_REPLAY_V1_HPP
#define GAMMA_FX2_CLOSING_REPLAY_V1_HPP
#include <array>
#include <cstdint>
#include <vector>

namespace gamma_closing {
// Recognizes bounded stored WRT spellings, not XML validity. Names remain in
// their original stored coordinates; no dictionary or future truth is queried.
class Replay {
 public:
  bool predict(uint8_t& value) const {
    if (mode_ != Close || !replay_ || !depth_ || position_ >= stack_[depth_-1].size)
      return false;
    value = stack_[depth_-1].bytes[position_];
    return true;
  }
  void observe(uint8_t stored) {
    ++count_;
    const uint8_t c = unswap(stored);
    // Escaped bytes may spell apparent markup. Conservatively forget both
    // the pending tag and stack, and consume the escaped byte without parsing.
    if (escaped_) { escaped_ = false; return; }
    if (c == 12) { reset(); escaped_ = true; return; }
    switch (mode_) {
      case Outside:
        if (c == '<') { clear_name(); mode_ = AfterLt; }
        break;
      case AfterLt:
        if (c == '/') { mode_ = Close; position_ = 0; replay_ = depth_ != 0; }
        else if (is_name(c)) { mode_ = Open; append(stored); }
        else { reset(); mode_ = Ignore; }
        break;
      case Open:
        if (is_name(c)) append(stored);
        else if (c == '>') finish_open();
        else if (space(c) || c == '/') { mode_ = Attributes; slash_ = c == '/'; }
        else reset();
        break;
      case Attributes:
        if (quote_) { if (c == quote_) quote_ = 0; }
        else if (c == '\'' || c == '"') { quote_ = c; slash_ = false; }
        else if (c == '>') finish_open();
        else if (c == '<') reset();
        else if (!space(c)) slash_ = c == '/';
        break;
      case Close:
        if (is_name(c)) {
          uint8_t expected = 0;
          if (!predict(expected) || expected != stored) replay_ = false;
          if (position_ < 255) ++position_;
          append(stored);
        } else if (c == '>') finish_close();
        else if (space(c)) { replay_ = false; mode_ = CloseRest; }
        else reset();
        break;
      case CloseRest:
        if (c == '>') finish_close();
        else if (!space(c)) reset();
        break;
      case Ignore:
        if (c == '>') mode_ = Outside;
        break;
    }
  }
  std::vector<uint8_t> state() const {
    std::vector<uint8_t> out{'C','L','R','1',uint8_t(mode_),depth_,position_,quote_,
                             uint8_t(slash_),uint8_t(replay_),uint8_t(escaped_),name_.size};
    for (unsigned i=0;i<8;++i) out.push_back(uint8_t(count_ >> (8*i)));
    out.insert(out.end(),name_.bytes.begin(),name_.bytes.end());
    for (const auto& n:stack_) {
      out.push_back(n.size); out.insert(out.end(),n.bytes.begin(),n.bytes.end());
    }
    return out;
  }
 private:
  enum Mode : uint8_t { Outside, AfterLt, Open, Attributes, Close, CloseRest, Ignore };
  struct Name { uint8_t size=0; std::array<uint8_t,64> bytes{}; };
  static uint8_t unswap(uint8_t c) {
    if(c>='{' && c<127)c-=43; else if(c>='P' && c<'T')c+=43;
    else if((c>=':' && c<='?')||(c>='J' && c<='O'))c^=0x70;
    if(c=='X'||c=='`')c^='X'^'`';
    return c;
  }
  static bool space(uint8_t c) { return c==' '||c=='\t'||c=='\r'||c=='\n'; }
  static bool is_name(uint8_t c) {
    return c>=128 || (c>='a'&&c<='z') || (c>='A'&&c<='Z') ||
      (c>='0'&&c<='9') || c=='_' || c==':' || c=='-' || c=='.' ||
      c==7 || c==6 || c==64;
  }
  void clear_name() { name_=Name{}; position_=0; quote_=0; slash_=false; replay_=false; }
  void reset() {
    mode_=Outside; depth_=0; clear_name();
    for(auto& n:stack_)n=Name{};
  }
  void append(uint8_t c) {
    if(name_.size==64) { reset(); mode_=Ignore; return; }
    name_.bytes[name_.size++]=c;
  }
  void finish_open() {
    if(!name_.size || (!slash_ && depth_==16)) { reset(); return; }
    if(!slash_)stack_[depth_++]=name_;
    clear_name(); mode_=Outside;
  }
  void finish_close() {
    bool same=depth_ && name_.size==stack_[depth_-1].size;
    if(same)for(unsigned i=0;i<name_.size;++i)
      same = same && name_.bytes[i]==stack_[depth_-1].bytes[i];
    if(!same) { reset(); return; }
    stack_[--depth_]=Name{}; clear_name(); mode_=Outside;
  }
  Mode mode_=Outside;
  uint8_t depth_=0,position_=0,quote_=0;
  bool slash_=false,replay_=false,escaped_=false;
  uint64_t count_=0;
  Name name_;
  std::array<Name,16> stack_{};
};
}
#endif
