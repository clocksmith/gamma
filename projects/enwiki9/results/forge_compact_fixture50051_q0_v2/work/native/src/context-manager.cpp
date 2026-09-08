#include "context-manager.h"
extern unsigned long long wrtcxt;

extern const unsigned char wrt_2b[256];
extern const unsigned char wrt_3b[256];
const unsigned char wrt_4b[256]={
 6, 0,12,15,12,15,14,14, 5, 3,14, 0,15,13, 8,13,
 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
13, 5,15,11,10,12, 6,12, 0,11,14, 1, 1,10, 9, 8,
 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9,11, 6, 1, 0, 4,
 9,10,10, 4, 5, 1, 4, 2,11, 8, 4, 1, 0,10,10, 5,
 4, 7,15, 4, 5,13, 0, 1, 4,12, 0, 1, 3, 3, 3,11,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 8, 0,11, 7,


 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2
 };
 const unsigned char wrt_5b[256]={
 10, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
 7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 3, 3, 2, 2, 1, 1,
 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
  };
#define COLON         'J' // :
#define SEMICOLON     'K' // ;
#define LESSTHAN      'L' // <
#define EQUALS        'M' // =
#define GREATERTHAN   'N' // >
#define QUESTION      'O' // ?
#define FIRSTUPPER     64 // @ - wrt first char in word is in upper case
#define SQUAREOPEN     91 // [
#define BACKSLASH      92 // '\'
#define SQUARECLOSE    93 // ]
#define CURLYOPENING  'P' // {
#define VERTICALBAR   'Q' // |
#define CURLYCLOSE    'R' // }

#ifdef ENABLE_TEMPLATE_PHASE_CONTEXT
namespace {
constexpr unsigned char kTemplatePhaseTpl = 1;
constexpr unsigned char kTemplatePhaseTable = 2;
constexpr unsigned char kTemplatePhaseLink = 3;

#ifndef TEMPLATE_PHASE_ENABLE_PIPE_TARGET
#define TEMPLATE_PHASE_ENABLE_PIPE_TARGET 1
#endif
#ifndef TEMPLATE_PHASE_ENABLE_EQUALS_TARGET
#define TEMPLATE_PHASE_ENABLE_EQUALS_TARGET 1
#endif
#ifndef TEMPLATE_PHASE_ENABLE_CLOSER_TARGET
#define TEMPLATE_PHASE_ENABLE_CLOSER_TARGET 1
#endif
#ifndef TEMPLATE_PHASE_ENABLE_NEWLINE_TARGET
#define TEMPLATE_PHASE_ENABLE_NEWLINE_TARGET 1
#endif
#ifndef TEMPLATE_PHASE_MICROCORE_MODE
#define TEMPLATE_PHASE_MICROCORE_MODE 0
#endif

bool TPIsOpenCurly(unsigned char c) {
  return c == '{' || c == CURLYOPENING;
}

bool TPIsCloseCurly(unsigned char c) {
  return c == '}' || c == CURLYCLOSE;
}

bool TPIsPipe(unsigned char c) {
  return c == '|' || c == VERTICALBAR;
}

bool TPIsEquals(unsigned char c) {
  return c == '=' || c == EQUALS;
}

bool TPIsTargetByte(unsigned char c) {
  if (TEMPLATE_PHASE_ENABLE_PIPE_TARGET && TPIsPipe(c)) return true;
  if (TEMPLATE_PHASE_ENABLE_EQUALS_TARGET && TPIsEquals(c)) return true;
  if (TEMPLATE_PHASE_ENABLE_CLOSER_TARGET && TPIsCloseCurly(c)) return true;
  if (TEMPLATE_PHASE_ENABLE_NEWLINE_TARGET && c == '\n') return true;
  return false;
}

bool TPIsOpenSquare(unsigned char c) {
  return c == '[' || c == SQUAREOPEN;
}

bool TPIsCloseSquare(unsigned char c) {
  return c == ']' || c == SQUARECLOSE;
}

bool TPIsWhitespace(unsigned char c) {
  return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

unsigned long long TPLineBucket(unsigned long long line_col) {
  if (line_col == 0) return 0;
  if (line_col <= 2) return 1;
  if (line_col <= 12) return 2;
  return 3;
}

unsigned long long TPPrevClass(unsigned char c) {
  if (TPIsWhitespace(c)) return 1;
  if (c >= '0' && c <= '9') return 2;
  if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')) return 3;
  if (TPIsPipe(c) || TPIsEquals(c) || TPIsCloseCurly(c) || c == '\n') return 4;
  return 5;
}
}
#endif

ContextManager::ContextManager() : history_(60000000, 0),
    shared_map_(256*400000, 0), words_(8, 0), recent_bytes_(8, 0) {
    hashes_ind1.resize(0x1000000, 0);
    hashes_ind2.resize(0x1000000, 0);
    hashes_ind3.resize(0x2000000, 0);
    hashes_ind4.resize(0x100, 0);
    hashes_ind5.resize(0x100, 0);
}

void ContextManager::UpdateHistory() {
  history_[history_pos_] = bit_context_;
  ++history_pos_;
  if (history_pos_ == history_.size()) history_pos_ = 0;
}

void ContextManager::UpdateWords() {
  unsigned char c = bit_context_;
  if (c==CURLYCLOSE || c==CURLYOPENING ||c==SQUARECLOSE)    b3stream= (b3stream&0xfffffff8)+3;
  else if (c==EQUALS)  b3stream=(b3stream&0xfffffff8)+4;
  n2bState=wrt_2b[c];
  b2stream=b2stream*4+n2bState;
  n3bState=wrt_3b[c];
  b3stream=b3stream*8+n3bState;
  if (o3bState!=n3bState){
      stream3bR=(stream3bR<<3)+n3bState;
      o3bState=n3bState;
  }
  if (c==10 || c==')') b3stream=b3stream<<6;
  if (c==VERTICALBAR)  b3stream=b3stream*8+wrt_3b[c];
  b2streamcxt=b2stream&0x3ff;// 2^10 bits
  b3streamcxt=b3stream&0x1ff;// 2^9 bits

  if (o2bState!=n2bState){
      stream2bR=(stream2bR<<2)+n2bState;
      o2bState=n2bState;
  }
  b4stream=b4stream*16+wrt_4b[c];
  mx18cxt=mx18cxt*16+wrt_5b[c];
  mx18=mx18cxt&0xff;

  words=words*2;

  if ((c >= 'a' && c <= 'z') || c >= 0x80) {
    words_[7] = words_[7] * 997*16 + c;
    if (recent_bytes_[0]!=12) words=words+1;

  } else {
    words_[7] = 0;
  }
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
   if (c==10  )     words=0xfffc;
   else if (c=='.')                 words= words|0xffc;
   else if (c==',')                 words=words|0xffc;
   mx5=b2stream&0xffff;//2^16 bits
   mx7=    b4stream&0xff;
   mx8=(mx8*(1 << 2)+(b3stream&0x3f))& 0x3FFF;// o1, mask 2^(7*2) , n3 should be 8 bits, use 7 for now
   mx9cxt=(mx9cxt * (1 << 4) + c) &0xff;

   mx10cxt=c;
   mx11cxt=c;
   mx12cxt=0;
   mx13cxt=0;

   mx14 = c*256+recent_bytes_[0];
   mx15 = recent_bytes_[0]*256+recent_bytes_[1];

   hashes_ind1[context1_ind] = (ind1 * (1 << 8) + c) & (0x100-1);
   context1_ind = (context1_ind * (1 << 8) + c) & (0x1000000-1);
   ind1 = hashes_ind1[context1_ind];

    hashes_ind2[context1_ind2] = (ind2 * (1 << 8) + c) & (0x100000000-1);
   context1_ind2 = (context1_ind2 * (1 << 6) + c) & (0x1000000-1);
   ind2 = hashes_ind2[context1_ind2];

  hashes_ind3[context1_ind3] = (ind3 * (1 << 5) + c) & (0x2000000-1);
  context1_ind3 = (context1_ind3 * (1 << 5) + c) &     (0x2000000-1);
  ind3 = hashes_ind3[context1_ind3];

  hashes_ind5[context1_ind5] = (ind5 * (1 << 6) + c) & (0x40000000-1);
  context1_ind5 = c;
  ind5 = hashes_ind5[context1_ind5];
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

#ifdef ENABLE_TEMPLATE_PHASE_CONTEXT
void ContextManager::UpdateTemplatePhaseContext() {
  const unsigned char c = static_cast<unsigned char>(recent_bytes_[0]);
  template_phase_active_target_ = TPIsTargetByte(c) ? 1 : 0;

  int top_tpl = -1;
  for (int i = static_cast<int>(template_phase_stack_size_) - 1; i >= 0; --i) {
    if (template_phase_stack_[i] == kTemplatePhaseTpl) {
      top_tpl = i;
      break;
    }
  }

  if (top_tpl >= 0) {
    unsigned char& line_col = template_phase_tpl_line_col_[top_tpl];
    unsigned char& sig = template_phase_tpl_sig_[top_tpl];
    unsigned char& saw_pipe = template_phase_tpl_saw_pipe_[top_tpl];
    unsigned char& saw_equals = template_phase_tpl_saw_equals_[top_tpl];

    if (c == '\n') {
      line_col = 0;
      sig = 4;
      saw_pipe = 0;
      saw_equals = 0;
    } else {
      if (line_col < 31) ++line_col;
      if (TPIsPipe(c)) {
        sig = 1;
        saw_pipe = 1;
        saw_equals = 0;
      } else if (TPIsEquals(c)) {
        sig = 2;
        if (saw_pipe) saw_equals = 1;
      } else if (TPIsCloseCurly(c)) {
        sig = 3;
      } else if (TPIsOpenCurly(c)) {
        sig = 5;
      } else if (TPIsOpenSquare(c)) {
        sig = 6;
      } else if (TPIsCloseSquare(c)) {
        sig = 7;
      }
    }
  }

  auto push_frame = [&](unsigned char frame) {
    if (template_phase_stack_size_ >= kTemplatePhaseStackCap) return;
    const unsigned long long idx = template_phase_stack_size_++;
    template_phase_stack_[idx] = frame;
    template_phase_tpl_line_col_[idx] = 0;
    template_phase_tpl_sig_[idx] = 0;
    template_phase_tpl_saw_pipe_[idx] = 0;
    template_phase_tpl_saw_equals_[idx] = 0;
    if (frame == kTemplatePhaseTpl && template_phase_tpl_depth_ < 63) {
      ++template_phase_tpl_depth_;
    }
  };

  auto pop_matching = [&](unsigned char frame) {
    if (template_phase_stack_size_ == 0) return;
    unsigned long long match = template_phase_stack_size_;
    for (int i = static_cast<int>(template_phase_stack_size_) - 1; i >= 0; --i) {
      if (template_phase_stack_[i] == frame) {
        match = static_cast<unsigned long long>(i);
        break;
      }
    }
    if (match == template_phase_stack_size_) {
      match = template_phase_stack_size_ - 1;
    }
    for (unsigned long long i = match; i < template_phase_stack_size_; ++i) {
      if (template_phase_stack_[i] == kTemplatePhaseTpl &&
          template_phase_tpl_depth_ > 0) {
        --template_phase_tpl_depth_;
      }
      template_phase_stack_[i] = 0;
      template_phase_tpl_line_col_[i] = 0;
      template_phase_tpl_sig_[i] = 0;
      template_phase_tpl_saw_pipe_[i] = 0;
      template_phase_tpl_saw_equals_[i] = 0;
    }
    template_phase_stack_size_ = match;
  };

  if (template_phase_seen_bytes_ > 0) {
    const unsigned char prev = static_cast<unsigned char>(recent_bytes_[1]);
    if (TPIsOpenCurly(prev) && TPIsOpenCurly(c)) {
      push_frame(kTemplatePhaseTpl);
    } else if (TPIsOpenCurly(prev) && TPIsPipe(c)) {
      push_frame(kTemplatePhaseTable);
    } else if (TPIsOpenSquare(prev) && TPIsOpenSquare(c)) {
      push_frame(kTemplatePhaseLink);
    } else if (TPIsCloseCurly(prev) && TPIsCloseCurly(c)) {
      pop_matching(kTemplatePhaseTpl);
    } else if (TPIsPipe(prev) && TPIsCloseCurly(c)) {
      pop_matching(kTemplatePhaseTable);
    } else if (TPIsCloseSquare(prev) && TPIsCloseSquare(c)) {
      pop_matching(kTemplatePhaseLink);
    }
  }
  ++template_phase_seen_bytes_;
  RefreshTemplatePhaseBitContexts();
}

void ContextManager::RefreshTemplatePhaseBitContexts() {
  int top_tpl = -1;
  for (int i = static_cast<int>(template_phase_stack_size_) - 1; i >= 0; --i) {
    if (template_phase_stack_[i] == kTemplatePhaseTpl) {
      top_tpl = i;
      break;
    }
  }
  if (top_tpl < 0 || template_phase_tpl_depth_ == 0) {
    template_phase_context_ = 0;
    template_phase_shape_context_ = 0;
    return;
  }
  if (!template_phase_active_target_) {
    template_phase_context_ = 0;
    template_phase_shape_context_ = 0;
    return;
  }

  const unsigned long long tpl_depth =
      template_phase_tpl_depth_ > 7 ? 7 : template_phase_tpl_depth_;
  const unsigned long long nested_depth =
      template_phase_stack_size_ > 8 ? 7 : template_phase_stack_size_ - 1;
  const unsigned long long line_bucket =
      TPLineBucket(template_phase_tpl_line_col_[top_tpl]);
  const unsigned long long sig_bucket = template_phase_tpl_sig_[top_tpl];
  const unsigned long long saw_pipe = template_phase_tpl_saw_pipe_[top_tpl] ? 1 : 0;
  const unsigned long long saw_equals =
      template_phase_tpl_saw_equals_[top_tpl] ? 1 : 0;
  const unsigned long long prev_class =
      template_phase_seen_bytes_ <= 1 ? 0 :
      TPPrevClass(static_cast<unsigned char>(recent_bytes_[1]));

#if TEMPLATE_PHASE_MICROCORE_MODE
  const unsigned long long nested_tpl_bool = template_phase_tpl_depth_ > 1 ? 1 : 0;
  unsigned long long phase = 0;
  if (saw_pipe) {
    phase = saw_equals ? 2 : 1;
  }
  const unsigned long long key =
      (((nested_tpl_bool * 3 + phase) * 4 + line_bucket) * 6 + prev_class);
  template_phase_context_ = (key << 8) + long_bit_context_;
  template_phase_shape_context_ = 0;
#else
  const unsigned long long key =
      ((((((tpl_depth * 8 + nested_depth) * 4 + line_bucket) * 9 +
          sig_bucket) * 2 + saw_pipe) * 2 + saw_equals) * 6 + prev_class);
  template_phase_context_ = (key << 8) + long_bit_context_;

  const unsigned long long shape_key =
      (((tpl_depth * 8 + nested_depth) * 4 + line_bucket) * 9 + sig_bucket);
  template_phase_shape_context_ = (shape_key << 8) + long_bit_context_;
#endif
}
#endif

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
#ifdef ENABLE_TEMPLATE_PHASE_CONTEXT
    UpdateTemplatePhaseContext();
#endif
    UpdateWRTContext();

    for (auto& context : context_hash_contexts_) {
      context.Update();
    }
    for (auto& context : sparse_contexts_) {
      context.Update();
    }
    for (auto& context : bracket_contexts_) {
      context.Update();
    }
  }
  wordscxt=(words&0x7F)*256+long_bit_context_;

  bpos=(bpos+1)&7;

  mx6=(stream2bR&0xff)*256+long_bit_context_;

  mx19cxt=    wrtcxt;
  mx9=(mx9cxt)*256+long_bit_context_;
  mx10=(mx10cxt)*256+long_bit_context_;
  mx11=(mx11cxt)*256+long_bit_context_;
  mx12=long_bit_context_;
  mx13=long_bit_context_;
  mx16=(recent_bytes_[1])*256+long_bit_context_;
  mx17=(b3stream&0x3f)*256+long_bit_context_;// 7f or 3f
  lstm_lowprob_context_=lstm_lowprob_state_*256+long_bit_context_;

      if (bpos==0)  mxx=(stream2bR&63)*8 + (b3stream&7);
    else if (bpos>3) {
        mxx=((b2stream<<2)&63)+wrt_2b[(long_bit_context_<<(8-bpos))&255]*8+(b3stream&7);
    } else
        mxx=(stream2bR&63)*8 +(b3stream&7);

#ifdef ENABLE_TEMPLATE_PHASE_CONTEXT
  RefreshTemplatePhaseBitContexts();
#endif

}
