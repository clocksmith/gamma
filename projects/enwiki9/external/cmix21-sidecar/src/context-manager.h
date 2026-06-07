#ifndef CONTEXT_MANAGER_H
#define CONTEXT_MANAGER_H

#include "states/nonstationary.h"
#include "states/run-map.h"
#include "contexts/context.h"
#include "contexts/bit-context.h"

#include <array>
#include <string>
#include <vector>
#include <memory>

struct ContextManager {
  ContextManager();
  const Context& AddContext(std::unique_ptr<Context> context);
  const BitContext& AddBitContext(std::unique_ptr<BitContext> bit_context);
  void UpdateContexts(int bit);
  void UpdateHistory();
  void UpdateWords();
  void UpdateRecentBytes();
  void UpdateWRTContext();
  void UpdateSidecar();
  void SidecarPush(unsigned char c);
  void SidecarPushWRT(unsigned char c);
  bool SidecarEndsWith(const char* s) const;
  bool SidecarEndsWithFold(const char* s) const;
  void SidecarRememberEntity(unsigned int h);
  void SidecarPretrainByte(unsigned char c);
  void UpdatePhda9Sidecar(unsigned char c);

  unsigned int bit_context_ = 1, wrt_state_ = 0;
  unsigned long long long_bit_context_ = 1, zero_context_ = 0, history_pos_ = 0,
      line_break_ = 0, longest_match_ = 0, auxiliary_context_ = 0,
      wrt_context_ = 0,
      sidecar_direct_=0, sidecar_direct2_=0,
      sidecar_direct3_=0, sidecar_direct4_=0,
      sidecar_ctx1_=0, sidecar_ctx2_=0, sidecar_ctx3_=0, sidecar_ctx4_=0,
      sidecar_ctx5_=0, sidecar_ctx6_=0, sidecar_ctx7_=0, sidecar_ctx8_=0,
      sidecar_schema_ctx_=0,
      sidecar_mix1_=0, sidecar_mix2_=0, sidecar_mix3_=0, sidecar_mix4_=0,
      sidecar_mix5_=0, sidecar_mix6_=0, sidecar_mix7_=0, sidecar_mix8_=0,
      ph_direct1_=0, ph_direct2_=0, ph_ctx1_=0, ph_ctx2_=0, ph_ctx3_=0,
      ph_ctx4_=0, ph_ctx5_=0, ph_ctx6_=0, ph_ctx7_=0, ph_ctx8_=0;
  unsigned int side_text_=0, side_in_tag_=0, side_template_depth_=0,
      side_template_hash_=0, side_template_arg_=0, side_link_hash_=0,
      side_link_active_=0, side_link_recency_=0, side_title_active_=0,
      side_title_hash_=0, side_category_state_=0, side_numeric_class_=0,
      side_numeric_len_=0, side_url_state_=0, side_tail_len_=0,
      side_field_=0, side_slot_=0, side_page_kind_=0, side_col_=0,
      side_col_bucket_=0, side_page_pos_=0, side_page_bucket_=0,
      side_word_hash_=0, side_word_len_=0, side_entity_hash_=0,
      side_entity_recency_=31, side_ref_active_=0, side_ref_hash_=0,
      side_wrt_state_=0, side_wrt_first_=0, side_wrt_second_=0,
      ph_line_kind_=0, ph_prev_line_kind_=0, ph_line_hash_=0,
      ph_prefix_hash_=0, ph_tail_field_=0, ph_digit_run_=0,
      ph_lang_hash_=0, ph_template_line_=0, ph_col_=0,
      ph_detect_state_=0, ph_header_len_=0, ph_header_digits_=0;
  std::array<unsigned char, 32> side_tail_{};
  std::array<unsigned int, 16> side_recent_links_{};
  std::array<unsigned int, 32> side_recent_entities_{};
  unsigned int side_pretrain_header_left_=5;
  std::string side_pretrain_word_;
  std::vector<std::string> side_wrt_words_;
  std::vector<unsigned char> history_, shared_map_;
  std::vector<unsigned long long> words_, recent_bytes_;
  std::vector<std::unique_ptr<Context>> contexts_;
  std::vector<std::unique_ptr<BitContext>> bit_contexts_;
  RunMap run_map_;
  Nonstationary nonstationary_;
};

#endif
