// Copyright 2020 Mobvoi Inc. All Rights Reserved.
// Author: binbinzhang@mobvoi.com (Binbin Zhang)
//         di.wu@mobvoi.com (Di Wu)

#include <iomanip>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "decoder/torch_asr_decoder.h"
#include "decoder/torch_asr_model.h"
#include "frontend/feature_pipeline.h"
#include "frontend/wav.h"
#include "post_processor/post_processor.h"
#include "torch/script.h"
#include "utils/flags.h"
#include "utils/log.h"
#include "utils/string.h"
#include "utils/timer.h"
#include "utils/utils.h"

namespace wenet {

std::shared_ptr<FeaturePipelineConfig> InitFeaturePipelineConfigFromFlags() {
  auto feature_config = std::make_shared<FeaturePipelineConfig>(
      80, 16000, 8000);
  return feature_config;
}

std::shared_ptr<DecodeOptions> InitDecodeOptionsFromFlags() {
  auto decode_config = std::make_shared<DecodeOptions>();
  decode_config->chunk_size = 16;
  decode_config->num_left_chunks = 0;
  decode_config->ctc_weight = 1.0;
  decode_config->reverse_weight = 0.0;
  decode_config->rescoring_weight = 0.0;
  decode_config->ctc_wfst_search_opts.max_active = 7000;
  decode_config->ctc_wfst_search_opts.min_active = 200;
  decode_config->ctc_wfst_search_opts.beam = 16;
  decode_config->ctc_wfst_search_opts.lattice_beam = 16;
  decode_config->ctc_wfst_search_opts.acoustic_scale = 1.0;
  decode_config->ctc_wfst_search_opts.blank_skip_thresh = 0.98;
  decode_config->ctc_wfst_search_opts.nbest = 16;
  decode_config->ctc_prefix_search_opts.first_beam_size = 16;
  decode_config->ctc_prefix_search_opts.second_beam_size = 16;

  int max_audio_length_in_ms = 60 * 1000;
  decode_config->ctc_endpoint_config.rule1.min_trailing_silence = max_audio_length_in_ms;
  decode_config->ctc_endpoint_config.rule2.min_trailing_silence = max_audio_length_in_ms;
  decode_config->ctc_endpoint_config.rule3.min_utterance_length = max_audio_length_in_ms;
  return decode_config;
}

std::shared_ptr<DecodeResource> InitDecodeResourceFromFlags(std::string model_path, std::string unit_path) {
  auto resource = std::make_shared<DecodeResource>();

  LOG(INFO) << "Reading model " << model_path;
  auto model = std::make_shared<TorchAsrModel>();
  model->Read(model_path, 4);
  resource->model = model;

  std::shared_ptr<fst::Fst<fst::StdArc>> fst = nullptr;
  resource->fst = fst;

  LOG(INFO) << "Reading symbol table " << unit_path;
  auto symbol_table = std::shared_ptr<fst::SymbolTable>(
      fst::SymbolTable::ReadText(unit_path));
  resource->symbol_table = symbol_table;

  std::shared_ptr<fst::SymbolTable> unit_table = nullptr;
  unit_table = symbol_table;
  resource->unit_table = unit_table;

  PostProcessOptions post_process_opts;
  post_process_opts.language_type = kMandarinEnglish;
  post_process_opts.lowercase = 0;
  resource->post_processor =
    std::make_shared<PostProcessor>(std::move(post_process_opts));
  return resource;
}

class Asr {
  public:
    Asr(std::string model_path, std::string unit_path) {
      decode_config_ = InitDecodeOptionsFromFlags();
      feature_config_ = InitFeaturePipelineConfigFromFlags();
      decode_resource_ = InitDecodeResourceFromFlags(model_path, unit_path);
    }

    std::string Infer(std::string wav_path) {
      wenet::WavReader wav_reader(wav_path);
      auto feature_pipeline =
          std::make_shared<wenet::FeaturePipeline>(*feature_config_);
      feature_pipeline->AcceptWaveform(std::vector<float>(
          wav_reader.data(), wav_reader.data() + wav_reader.num_sample()));
      feature_pipeline->set_input_finished();
      LOG(INFO) << "num frames " << feature_pipeline->num_frames();

      wenet::TorchAsrDecoder decoder(feature_pipeline, decode_resource_,
                                     *decode_config_);

      int decode_time = 0;
      std::string final_result;
      while (true) {
        wenet::Timer timer;
        wenet::DecodeState state = decoder.Decode();
        if (state == wenet::DecodeState::kEndFeats) {
          decoder.Rescoring();
        }
        int chunk_decode_time = timer.Elapsed();
        decode_time += chunk_decode_time;
        if (decoder.DecodedSomething()) {
          LOG(INFO) << "Partial result: " << decoder.result()[0].sentence;
        }

        if (state == wenet::DecodeState::kEndpoint) {
          decoder.Rescoring();
          final_result.append(decoder.result()[0].sentence);
          decoder.ResetContinuousDecoding();
        }

        if (state == wenet::DecodeState::kEndFeats) {
          break;
        } 
      }
      if (decoder.DecodedSomething()) {
        final_result.append(decoder.result()[0].sentence);
      }
      return final_result;
    }
  private:
    std::shared_ptr<wenet::DecodeOptions> decode_config_;
    std::shared_ptr<wenet::FeaturePipelineConfig> feature_config_;
    std::shared_ptr<wenet::DecodeResource> decode_resource_;
};

} // end wenet namespace

extern "C" {

using namespace wenet;

void Asr_InitLog() {
  google::InitGoogleLogging("test_asr");
}

Asr* Asr_New(char* model_path, char* unit_path) {
  auto p_asr = new Asr(model_path, unit_path);
  return p_asr;
}

void Asr_Delete(Asr* p_asr) {
  delete p_asr;
}

void Asr_Infer(Asr* p_asr, char* wav_path, char* buf, int buf_len, int* out_len) {
  std::string sentence = p_asr -> Infer(wav_path);
  int size = sentence.size();
  *out_len = size;
  if (size > buf_len) {
    return;
  }
  for(int i = 0; i < size; i++) {
    buf[i] = sentence[i];
  }
} 

} // end extern "C"
