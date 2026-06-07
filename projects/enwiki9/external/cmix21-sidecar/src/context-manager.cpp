#include "context-manager.h"

#include <algorithm>
#include <cstdint>
#include <cstring>

#define COLON         'J'
#define LESSTHAN      'L'
#define EQUALS        'M'
#define GREATERTHAN   'N'
#define CURLYOPENING  'P'
#define VERTICALBAR   'Q'
#define CURLYCLOSE    'R'

ContextManager::ContextManager() : history_(100000000, 0),
    shared_map_(256*8000000, 0), words_(8, 0), recent_bytes_(8, 0) {}

const Context& ContextManager::AddContext(std::unique_ptr<Context> context) {
  for (const auto& old : contexts_) {
    if (old->IsEqual(context.get())) return *old;
  }
  contexts_.push_back(std::move(context));
  return *(contexts_[contexts_.size() - 1]);
}

const BitContext& ContextManager::AddBitContext(std::unique_ptr<BitContext>
    bit_context) {
  for (const auto& old : bit_contexts_) {
    if (old->IsEqual(bit_context.get())) return *old;
  }
  bit_contexts_.push_back(std::move(bit_context));
  return *(bit_contexts_[bit_contexts_.size() - 1]);
}

void ContextManager::UpdateHistory() {
  history_[history_pos_] = bit_context_;
  ++history_pos_;
  if (history_pos_ == history_.size()) history_pos_ = 0;
}

void ContextManager::UpdateWords() {
  unsigned char c = bit_context_;
  if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c >= 0x80) {
    words_[7] = words_[7] * 997*16 + c;
  } else {
    words_[7] = 0;
  }
  if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
  if ((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == 8 || c == 6 ||
      c >= 0x80) {
    words_[0] = words_[0] * 997*16 + c;
    words_[0] &= 0xfffffff;
    words_[1] = words_[1] * 263*32 + c;
  } else {
    for (int i = 6; i >= 2; --i) {
      words_[i] = words_[i-1];
    }
    words_[1] = 0;
  }
}

void ContextManager::UpdateRecentBytes() {
  for (int i = 7; i >= 1; --i) {
    recent_bytes_[i] = recent_bytes_[i-1];
  }
  recent_bytes_[0] = bit_context_;
}

void ContextManager::UpdateWRTContext() {
  if (bit_context_ < 0x80) {
    wrt_state_ = 0;
  } else {
    if (wrt_state_ == 0) wrt_context_ = 0;
    wrt_state_ = 1;
    wrt_context_ <<= 8;
    wrt_context_ += bit_context_;
    if (wrt_context_ > 0xFFEFCF) wrt_context_ = 0;
  }
}

static unsigned char SideNorm(unsigned char c) {
  if (c == LESSTHAN) return '<';
  if (c == GREATERTHAN) return '>';
  if (c == CURLYOPENING) return '{';
  if (c == CURLYCLOSE) return '}';
  if (c == VERTICALBAR) return '|';
  if (c == COLON) return ':';
  if (c == EQUALS) return '=';
  return c;
}

static unsigned char SideLower(unsigned char c) {
  return (c >= 'A' && c <= 'Z') ? c + ('a' - 'A') : c;
}

static unsigned int SideBucket(unsigned int v) {
  unsigned int b = 0;
  while (v > 15 && b < 15) {
    v >>= 1;
    ++b;
  }
  return b;
}

static unsigned int SideClass(unsigned char c) {
  if (c >= 'A' && c <= 'Z') return 1;
  if (c >= 'a' && c <= 'z') return 2;
  if (c >= '0' && c <= '9') return 3;
  if (c == ' ' || c == '\n' || c == '\t' || c == '\r') return 4;
  if (c == '<' || c == '>' || c == '/' || c == '=' || c == '"') return 5;
  if (c == '[' || c == ']' || c == '{' || c == '}' || c == '|') return 6;
  if (c >= 128) return 7;
  return 0;
}

static unsigned int SideHashMix(unsigned int h, unsigned int v) {
  return ((h * 16777619u) ^ (v + 0x9e3779b9u)) & 65535u;
}

static unsigned int SideTimestampExpected(unsigned int pos) {
  if (pos <= 3 || (pos >= 5 && pos <= 6) || (pos >= 8 && pos <= 9) ||
      (pos >= 11 && pos <= 12) || (pos >= 14 && pos <= 15) ||
      (pos >= 17 && pos <= 18)) {
    return 1;
  }
  if (pos == 4 || pos == 7) return 2;
  if (pos == 10) return 3;
  if (pos == 13 || pos == 16) return 4;
  if (pos == 19) return 5;
  return 0;
}

static unsigned int Phda9LineKind(unsigned char c) {
  if (c >= '0' && c <= '9') return 1;
  if (c == '-') return 2;
  if (c == '[') return 3;
  if (c == '<') return 4;
  if (c == '>') return 5;
  if (c == '|') return 6;
  if (c == '{') return 7;
  if (c == '=') return 8;
  if (c == '*') return 9;
  if (c == ' ') return 10;
  if (c == '}') return 11;
  if (c == '/') return 12;
  if (c == '\n') return 13;
  if (c >= 'A' && c <= 'Z') return 14;
  if (c >= 'a' && c <= 'z') return 15;
  return 0;
}

void ContextManager::SidecarPush(unsigned char c) {
  c = SideNorm(c);
  if (side_tail_len_ < side_tail_.size()) {
    side_tail_[side_tail_len_++] = c;
  } else {
    for (unsigned int i = 1; i < side_tail_.size(); ++i) {
      side_tail_[i - 1] = side_tail_[i];
    }
    side_tail_[side_tail_.size() - 1] = c;
  }
  UpdatePhda9Sidecar(c);
}

static const char* SideWRTStructuralWord(unsigned int code) {
  switch (code) {
    case 46: return "category";
    case 47: return "image";
    case 236: return "ref";
    case 238: return "references";
    case 518: return "cite";
    case 1272: return "url";
    case 1286: return "id";
    case 1287: return "username";
    case 1295: return "contributor";
    case 1299: return "comment";
    case 1300: return "redirect";
    case 1301: return "infobox";
    case 1302: return "minor";
    case 1304: return "page";
    case 1305: return "revision";
    case 1307: return "title";
    case 1319: return "text";
    case 1357: return "timestamp";
    case 1993: return "file";
    case 2037: return "name";
    default: return nullptr;
  }
}

void ContextManager::SidecarPushWRT(unsigned char c) {
  c = SideNorm(c);

  auto push_word = [this](const char* w) {
    while (*w) SidecarPush((unsigned char)*w++);
  };
  auto push_code = [this, &push_word](unsigned int code) {
#ifdef SIDECAR_WRT_LEARN
    if (code < side_wrt_words_.size() && !side_wrt_words_[code].empty()) {
      for (unsigned char wc : side_wrt_words_[code]) SidecarPush(wc);
      return;
    }
#endif
    const char* word = SideWRTStructuralWord(code);
    if (word) push_word(word);
    else SidecarPush(0x80);
  };

  if (side_wrt_state_ == 1) {
    if (c >= 0x80 && c <= 0xcf) {
      push_code(80 + (side_wrt_first_ - 0xd0) * 80 + (c - 0x80));
    } else {
      SidecarPush(0x80);
      SidecarPush(c);
    }
    side_wrt_state_ = 0;
    return;
  }

  if (side_wrt_state_ == 2) {
    if (c >= 0xd0 && c <= 0xef) {
      side_wrt_second_ = c;
      side_wrt_state_ = 3;
      return;
    }
    SidecarPush(0x80);
    SidecarPush(c);
    side_wrt_state_ = 0;
    return;
  }

  if (side_wrt_state_ == 3) {
    if (c >= 0x80 && c <= 0xcf) {
      unsigned int group = (side_wrt_first_ - 0xf0) * 32
          + (side_wrt_second_ - 0xd0);
      push_code(3920 + group * 80 + (c - 0x80));
    } else {
      SidecarPush(0x80);
      SidecarPush(c);
    }
    side_wrt_state_ = 0;
    return;
  }

  if (c >= 0x80 && c <= 0xcf) {
    push_code(c - 0x80);
    return;
  }
  if (c >= 0xd0 && c <= 0xef) {
    side_wrt_first_ = c;
    side_wrt_state_ = 1;
    return;
  }
  if (c >= 0xf0) {
    side_wrt_first_ = c;
    side_wrt_state_ = 2;
    return;
  }

  SidecarPush(c);
}

bool ContextManager::SidecarEndsWith(const char* s) const {
  unsigned int n = std::strlen(s);
  if (n > side_tail_len_) return false;
  unsigned int off = side_tail_len_ - n;
  for (unsigned int i = 0; i < n; ++i) {
    if (side_tail_[off + i] != (unsigned char)s[i]) return false;
  }
  return true;
}

bool ContextManager::SidecarEndsWithFold(const char* s) const {
  unsigned int n = std::strlen(s);
  if (n > side_tail_len_) return false;
  unsigned int off = side_tail_len_ - n;
  for (unsigned int i = 0; i < n; ++i) {
    if (SideLower(side_tail_[off + i]) != SideLower((unsigned char)s[i])) {
      return false;
    }
  }
  return true;
}

void ContextManager::SidecarRememberEntity(unsigned int h) {
  if (h == 0) return;
  unsigned int rank = 31;
  for (unsigned int i = 0; i < side_recent_entities_.size(); ++i) {
    if (side_recent_entities_[i] == h) {
      rank = i;
      for (unsigned int j = i; j > 0; --j) {
        side_recent_entities_[j] = side_recent_entities_[j - 1];
      }
      break;
    }
  }
  side_recent_entities_[0] = h;
  side_entity_hash_ = h;
  side_entity_recency_ = rank;
}

void ContextManager::SidecarPretrainByte(unsigned char c) {
#ifdef SIDECAR_WRT_LEARN
  if (side_pretrain_header_left_ > 0) {
    --side_pretrain_header_left_;
    return;
  }
  if (c >= 'a' && c <= 'z') {
    side_pretrain_word_.push_back((char)c);
    return;
  }
  if (!side_pretrain_word_.empty()) {
    if (side_wrt_words_.size() < 44880) {
      side_wrt_words_.push_back(side_pretrain_word_);
    }
    side_pretrain_word_.clear();
  }
#else
  (void)c;
#endif
}

void ContextManager::UpdatePhda9Sidecar(unsigned char c) {
#if defined(SIDECAR_PHDA9_CONTEXT) || defined(SIDECAR_PHDA9_MODELS)
  c = SideNorm(c);
  if (ph_detect_state_ < 2) {
    if (ph_detect_state_ == 0) {
      if (c >= '0' && c <= '9') {
        ph_detect_state_ = 1;
        ph_header_len_ = 1;
        ph_header_digits_ = 1;
      }
      return;
    }
    ++ph_header_len_;
    if (c >= '0' && c <= '9') {
      if (ph_header_digits_ < 10) ++ph_header_digits_;
    } else if (c == ' ') {
    } else if (c == '\n' && ph_header_digits_ > 0 &&
        ph_header_len_ >= 8 && ph_header_len_ <= 32) {
      ph_detect_state_ = 2;
      ph_col_ = 0;
      ph_line_kind_ = 0;
      ph_prev_line_kind_ = 0;
      ph_line_hash_ = 0;
      ph_prefix_hash_ = 0;
      ph_tail_field_ = 0;
      ph_digit_run_ = 0;
      ph_lang_hash_ = 0;
      ph_template_line_ = 0;
      return;
    } else {
      ph_detect_state_ = 0;
      ph_header_len_ = 0;
      ph_header_digits_ = 0;
    }
    return;
  }

  unsigned char lc = SideLower(c);
  if (ph_col_ == 0) {
    ph_prev_line_kind_ = ph_line_kind_;
    ph_line_kind_ = Phda9LineKind(c);
    ph_line_hash_ = 0;
    ph_prefix_hash_ = 0;
    ph_tail_field_ = 0;
    ph_digit_run_ = 0;
    ph_lang_hash_ = 0;
    ph_template_line_ = (c == '{' || c == '|') ? 1 : 0;
  }
  if (c >= '0' && c <= '9') {
    if (ph_digit_run_ < 15) ++ph_digit_run_;
  } else if (c != '-') {
    ph_digit_run_ = 0;
  }
  if (ph_col_ < 48 && c != '\n') ph_prefix_hash_ = SideHashMix(ph_prefix_hash_, lc);
  if (c != '\n') ph_line_hash_ = SideHashMix(ph_line_hash_, lc);
  if (ph_line_kind_ == 3 && ph_col_ < 8 && c != '[' && c != ':') {
    ph_lang_hash_ = SideHashMix(ph_lang_hash_, lc);
  }
  if (ph_line_kind_ == 15) {
    if (SidecarEndsWithFold("id>")) ph_tail_field_ = 1;
    else if (SidecarEndsWithFold("timestamp>")) ph_tail_field_ = 2;
    else if (SidecarEndsWithFold("contributor>")) ph_tail_field_ = 3;
    else if (SidecarEndsWithFold("username>")) ph_tail_field_ = 4;
    else if (SidecarEndsWithFold("ip>")) ph_tail_field_ = 5;
    else if (SidecarEndsWithFold("revision>")) ph_tail_field_ = 6;
  }

  unsigned int ph_col_bucket = SideBucket(ph_col_);
  ph_direct1_ = ((ph_line_kind_ & 15) << 4) | (ph_digit_run_ & 15);
  ph_direct2_ = ((ph_prev_line_kind_ & 15) << 4) | (ph_tail_field_ & 15);
  ph_ctx1_ = (ph_prefix_hash_ << 8) ^ ((ph_line_kind_ & 15) << 4) ^ (ph_digit_run_ & 15);
  ph_ctx2_ = (ph_line_hash_ << 8) ^ ((ph_tail_field_ & 15) << 4) ^ (ph_prev_line_kind_ & 15);
  ph_ctx3_ = (ph_lang_hash_ << 16) ^ ((ph_line_kind_ & 15) << 8) ^ (ph_col_bucket & 15);
  ph_ctx4_ = (ph_prefix_hash_ << 16) ^ (ph_line_hash_ & 65535);
  ph_ctx5_ = ((ph_line_kind_ & 15) << 24) ^ ((ph_prev_line_kind_ & 15) << 20)
      ^ ((ph_tail_field_ & 15) << 16) ^ (ph_prefix_hash_ & 65535);
  ph_ctx6_ = (ph_line_hash_ << 12) ^ ((ph_template_line_ & 1) << 8) ^ (ph_col_bucket & 15);
  ph_ctx7_ = (ph_prefix_hash_ << 12) ^ ((ph_digit_run_ & 15) << 8) ^ (ph_tail_field_ & 15);
  ph_ctx8_ = (ph_line_hash_ << 16) ^ ((ph_line_kind_ & 15) << 12)
      ^ ((ph_lang_hash_ & 255) << 4) ^ (ph_col_bucket & 15);

  if (c == '\n') ph_col_ = 0;
  else if (ph_col_ < 4095) ++ph_col_;
#else
  (void)c;
#endif
}

void ContextManager::UpdateSidecar() {
  unsigned char c = SideNorm(bit_context_);
  SidecarPushWRT(c);

  if (c == '\n') {
    side_col_ = 0;
  } else if (side_col_ < 4095) {
    ++side_col_;
  }
  if (side_page_pos_ < 0x7fffffff) ++side_page_pos_;
  side_col_bucket_ = SideBucket(side_col_);
  side_page_bucket_ = SideBucket(side_page_pos_ >> 4);

  unsigned char lc = SideLower(c);
  if ((lc >= 'a' && lc <= 'z') || (c >= '0' && c <= '9')) {
    side_word_hash_ = (side_word_hash_ * 131 + lc) & 65535;
    if (side_word_len_ < 31) ++side_word_len_;
  } else {
    side_word_hash_ = 0;
    side_word_len_ = 0;
  }

  if (SidecarEndsWith("<page>")) {
    side_page_pos_ = 0;
    side_page_bucket_ = 0;
    side_page_kind_ = 1;
    side_field_ = 0;
    side_slot_ = 0;
    side_category_state_ = 0;
  }

  if (SidecarEndsWith("<text")) {
    side_text_ = 1;
    side_field_ = 6;
  }
  if (SidecarEndsWith("</text>")) {
    side_text_ = 0;
    side_field_ = 0;
    side_slot_ = 0;
    side_category_state_ = 0;
  }

  if (SidecarEndsWith("<title>")) {
    side_field_ = 1;
    side_title_active_ = 1;
    side_title_hash_ = 0;
  } else if (SidecarEndsWith("</title>")) {
    side_title_active_ = 0;
    side_field_ = 0;
    SidecarRememberEntity(side_title_hash_);
  } else if (side_title_active_) {
    side_title_hash_ = (side_title_hash_ * 131 + lc) & 65535;
    if (SidecarEndsWithFold("category:")) side_page_kind_ = 5;
    if (SidecarEndsWithFold("list of")) side_page_kind_ = 2;
    if (SidecarEndsWithFold("disambiguation")) side_page_kind_ = 3;
  }
  if (SidecarEndsWith("<id>")) side_field_ = 2;
  if (SidecarEndsWith("</id>")) side_field_ = 0;
  if (SidecarEndsWith("<timestamp>")) {
    side_field_ = 3;
    side_timestamp_active_ = 1;
    side_timestamp_pos_ = 0;
  } else if (SidecarEndsWith("</timestamp>")) {
    side_field_ = 0;
    side_timestamp_active_ = 0;
    side_timestamp_pos_ = 0;
  } else if (side_timestamp_active_) {
    if (c == '<') {
      side_timestamp_active_ = 0;
    } else if (side_timestamp_pos_ < 31) {
      ++side_timestamp_pos_;
    }
  }
  if (SidecarEndsWith("<username>")) side_field_ = 4;
  if (SidecarEndsWith("</username>")) side_field_ = 0;
  if (SidecarEndsWith("<comment>")) side_field_ = 5;
  if (SidecarEndsWith("</comment>")) side_field_ = 0;

  if (c == '<') side_in_tag_ = 1;
  if (c == '>') side_in_tag_ = 0;

  if (SidecarEndsWith("{{")) {
    if (side_template_depth_ < 15) ++side_template_depth_;
    side_template_hash_ = 0;
    side_template_arg_ = 0;
  } else if (SidecarEndsWith("}}")) {
    if (side_template_depth_ > 0) --side_template_depth_;
    if (side_template_depth_ == 0) {
      side_template_hash_ = 0;
      side_template_arg_ = 0;
    }
  } else if (side_template_depth_) {
    if (c == '|') {
      if (side_template_arg_ == 0) SidecarRememberEntity(side_template_hash_);
      side_template_arg_ = (side_template_arg_ + 1) & 15;
    } else if (side_template_arg_ == 0 && c > 32 && c != '{' && c != '}') {
      side_template_hash_ = (side_template_hash_ * 167 + lc) & 65535;
    }
  }

  if (SidecarEndsWithFold("[[category:")) {
    side_category_state_ = std::min(side_category_state_ + 1, 15u);
    side_slot_ = 1;
  }
  if (SidecarEndsWithFold("[[image:") || SidecarEndsWithFold("[[file:")) {
    side_slot_ = 2;
  }
  if (SidecarEndsWithFold("<ref")) {
    side_slot_ = 5;
  }
  if (side_template_depth_ && SidecarEndsWithFold("url=")) {
    side_slot_ = 7;
  }
  if (side_template_depth_ && SidecarEndsWithFold("title=")) {
    side_slot_ = 8;
  }
  if (side_text_ && SidecarEndsWithFold("#redirect")) {
    side_page_kind_ = 4;
  }
  if (SidecarEndsWith("[[")) {
    side_link_active_ = 1;
    side_link_hash_ = 0;
  } else if (side_link_active_ && c == '|') {
    SidecarRememberEntity(side_link_hash_);
    side_link_active_ = 0;
  } else if (side_link_active_ && c != ']') {
    side_link_hash_ = (side_link_hash_ * 131 + lc) & 65535;
  }
  if (side_link_active_ && SidecarEndsWith("]]")) {
    unsigned int rank = 15;
    for (unsigned int i = 0; i < side_recent_links_.size(); ++i) {
      if (side_recent_links_[i] == side_link_hash_) {
        rank = i;
        for (unsigned int j = i; j > 0; --j) {
          side_recent_links_[j] = side_recent_links_[j - 1];
        }
        break;
      }
    }
    side_recent_links_[0] = side_link_hash_;
    side_link_recency_ = rank;
    SidecarRememberEntity(side_link_hash_);
    side_link_active_ = 0;
  }

  if (!side_ref_active_ && (SidecarEndsWithFold("name=\"") ||
      SidecarEndsWithFold("name='"))) {
    side_ref_active_ = 1;
    side_ref_hash_ = 0;
    side_slot_ = 6;
  } else if (side_ref_active_) {
    if (c == '"' || c == '\'') {
      SidecarRememberEntity(side_ref_hash_);
      side_ref_active_ = 0;
    } else {
      side_ref_hash_ = (side_ref_hash_ * 131 + lc) & 65535;
    }
  }

  if (SidecarEndsWith("http://") || SidecarEndsWith("https://")) side_url_state_ = 1;
  if (side_url_state_ && (c <= 32 || c == ']' || c == '|')) side_url_state_ = 0;

  if (c >= '0' && c <= '9') {
    if (side_numeric_len_ < 15) ++side_numeric_len_;
    side_numeric_class_ = side_numeric_len_ == 4 ? 2 : (side_numeric_len_ > 4 ? 3 : 1);
  } else {
    side_numeric_len_ = 0;
    side_numeric_class_ = 0;
  }

  sidecar_direct_ = ((side_text_ & 1) << 7)
      | ((side_in_tag_ & 1) << 6)
      | ((side_template_depth_ & 3) << 4)
      | ((side_numeric_class_ & 7) << 1)
      | (side_url_state_ & 1);
  sidecar_direct2_ = ((side_category_state_ & 15) << 4)
      | (side_link_recency_ & 15);
  sidecar_direct3_ = ((side_field_ & 7) << 5)
      | ((side_slot_ & 15) << 1)
      | (side_text_ & 1);
  sidecar_direct4_ = ((side_page_kind_ & 7) << 5)
      | ((SideClass(c) & 7) << 2)
      | ((side_in_tag_ & 1) << 1)
      | (side_url_state_ & 1);
  sidecar_ctx1_ = (side_template_hash_ << 16)
      ^ (side_template_arg_ << 12)
      ^ (side_title_hash_ << 4)
      ^ (side_text_ & 1);
  sidecar_ctx2_ = (side_link_hash_ << 8)
      ^ (side_category_state_ << 4)
      ^ (side_link_recency_ & 15);
  sidecar_ctx3_ = (sidecar_direct_ << 16)
      ^ (recent_bytes_[0] << 8)
      ^ (recent_bytes_[1] & 255);
  sidecar_ctx4_ = (side_title_hash_ << 16)
      ^ (side_template_hash_ << 8)
      ^ (side_numeric_class_ << 4)
      ^ (side_url_state_ & 1);
  sidecar_ctx5_ = (side_field_ << 24)
      ^ (side_slot_ << 20)
      ^ (side_page_kind_ << 16)
      ^ (side_col_bucket_ << 8)
      ^ SideClass(c);
  sidecar_ctx6_ = (side_entity_hash_ << 8)
      ^ (side_entity_recency_ << 3)
      ^ (side_field_ & 7);
  sidecar_ctx7_ = (side_template_hash_ << 16)
      ^ (side_template_arg_ << 12)
      ^ (side_slot_ << 8)
      ^ (side_word_hash_ & 255);
  sidecar_schema_ctx_ = (side_template_hash_ << 16)
      ^ ((side_template_arg_ & 15) << 8)
      ^ (side_slot_ & 15);
  sidecar_ctx8_ = (side_page_kind_ << 20)
      ^ (side_page_bucket_ << 12)
      ^ (side_word_hash_ & 4095);
  side_timestamp_expected_ = SideTimestampExpected(side_timestamp_pos_);
  sidecar_timestamp_direct_ = ((side_timestamp_active_ & 1) << 8)
      | ((side_timestamp_pos_ & 31) << 3)
      | (side_timestamp_expected_ & 7);
  sidecar_timestamp_ctx_ = ((side_title_hash_ & 65535) << 16)
      ^ ((side_timestamp_pos_ & 31) << 8)
      ^ ((side_timestamp_expected_ & 7) << 4)
      ^ (side_page_kind_ & 7);
#ifdef SIDECAR_PHDA9_CONTEXT
  sidecar_direct3_ ^= ph_direct1_;
  sidecar_direct4_ ^= ph_direct2_;
  sidecar_ctx1_ ^= ph_ctx1_;
  sidecar_ctx2_ ^= ph_ctx2_;
  sidecar_ctx3_ ^= ph_ctx3_;
  sidecar_ctx4_ ^= ph_ctx4_;
  sidecar_ctx5_ ^= ph_ctx5_;
  sidecar_ctx6_ ^= ph_ctx6_;
  sidecar_ctx7_ ^= ph_ctx7_;
  sidecar_ctx8_ ^= ph_ctx8_;
#endif
}

void ContextManager::UpdateContexts(int bit) {
  bit_context_ += bit_context_ + bit;
  long_bit_context_ = bit_context_;
  if (bit_context_ >= 256) {
    bit_context_ -= 256;
    long_bit_context_ = 1;
    longest_match_ = 0;

    if (bit_context_ == '\n') {
      line_break_ = 0;
    } else if (line_break_ < 99) {
      ++line_break_;
    }

    UpdateHistory();
    UpdateWords();
    UpdateRecentBytes();
    UpdateWRTContext();
    UpdateSidecar();
    for (const auto& context : contexts_) {
      context->Update();
    }
  }
  sidecar_mix1_ = sidecar_direct_ * 256 + long_bit_context_;
  sidecar_mix2_ = sidecar_direct2_ * 256 + long_bit_context_;
  sidecar_mix3_ = (side_template_hash_ ^ (side_title_hash_ << 1)) * 256
      + long_bit_context_;
  sidecar_mix4_ = ((side_link_recency_ & 15) * 32 + (side_category_state_ & 15))
      * 256 + long_bit_context_;
  sidecar_mix5_ = ((side_field_ & 15) * 16 + (side_slot_ & 15))
      * 256 + long_bit_context_;
  sidecar_mix6_ = ((side_page_kind_ & 15) * 32 + (side_page_bucket_ & 31))
      * 256 + long_bit_context_;
  sidecar_mix7_ = ((side_entity_recency_ & 31) * 16 + (side_template_arg_ & 15))
      * 256 + long_bit_context_;
  sidecar_mix8_ = ((side_col_bucket_ & 15) * 8 + (side_numeric_class_ & 7))
      * 256 + long_bit_context_;
  for (const auto& context : bit_contexts_) {
    context->Update();
  }
}
