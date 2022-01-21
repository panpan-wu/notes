#include <iostream>
#include <memory>
#include <string>
#include <vector>

#include "boost/json/src.hpp"

#include "decoder/init.h"
#include "decoder/torch_asr_decoder.h"
#include "frontend/wav.h"

#include "capi/decoder_capi.h"

namespace json = boost::json;
using namespace wenet;

struct AsrDecoder {
  private:
    std::unique_ptr<TorchAsrDecoder> decoder_;
    char* result_;
    int size_;
    int num_results_ = 1;
    int sentence_idx_ = 1;
  public:
    AsrDecoder(const DecoderParams* params) {
      decoder_ = CreateTorchAsrDecoder(*params);
      size_ = 4096;
      result_ = new char[size_];
      result_[0] = '\0';
    }
    ~AsrDecoder() {
      delete result_;
    }
    void SetNumResults(int num_results) {
      num_results_ = num_results;
    }
    void SetSampleRateIn(int sample_rate_in) {
      decoder_->SetSampleRateIn(sample_rate_in);
    }
    void AcceptWaveform(const char* pcm, int length) {
      int num_samples = length / sizeof(int16_t);
      std::vector<float> pcm_data(num_samples);
      const int16_t* pdata = (const int16_t*)(pcm);
      for (int i = 0; i < num_samples; i++) {
        pcm_data[i] = static_cast<float>(*pdata);
        pdata++;
      }
      decoder_->AcceptWaveform(pcm_data);
    }
    void AcceptWavefile(const char* wav_path) {
      WavReader wav_reader(wav_path);
      std::vector<float> pcm(wav_reader.data(), wav_reader.data() + wav_reader.num_sample());
      decoder_->AcceptWaveform(pcm);
      decoder_->SetInputFinished();
    }
    void SetInputFinished() {
      decoder_->SetInputFinished();
    }
    int AdvanceDecoding() {
      result_[0] = '\0';
      auto state = decoder_->AdvanceDecoding();
      if (state == DecodeState::kWaitMoreFeats) {
      } else if (state == DecodeState::kEndBatch) {
        if (decoder_->DecodedSomething()) {
          writeResult(num_results_);
        }
      } else if (state == DecodeState::kEndpoint) {
        if (decoder_->DecodedSomething()) {
          decoder_->Rescoring();
          writeResult(num_results_);
          sentence_idx_ += 1;
        }
        decoder_->ResetContinuousDecoding();
      } else if (state == DecodeState::kEndFeats) {
        if (decoder_->DecodedSomething()) {
          decoder_->Rescoring();
          writeResult(num_results_);
        }
        decoder_->Reset();
      }
      return static_cast<int>(state);
    }
    const char* Result() {
      return result_;
    }
    void Reset() {
      decoder_->Reset();
      result_[0] = '\0';
      sentence_idx_ = 1;
    }
    void LogConfig() {
      decoder_->LogConfig();
    }
  private:
    void writeResult(int n) {
      std::string res = jsonResult(n);
      int length = static_cast<int>(res.size()) + 1;
      resizeResultBuf(length);
      std::strcpy(result_, res.c_str());
    }
    std::string jsonResult(int n) {
      json::array nbest;
      for (const DecodeResult& path : decoder_->result()) {
        json::object jpath({{"sentence", path.sentence}, {"index", sentence_idx_}});
        json::array word_pieces;
        for (const WordPiece& word_piece : path.word_pieces) {
          json::object jword_piece({{"text", word_piece.word},
                                    {"start_time", word_piece.start},
                                    {"end_time", word_piece.end}});
          word_pieces.emplace_back(jword_piece);
        }
        jpath.emplace("words", word_pieces);
        nbest.emplace_back(jpath);

        if (nbest.size() == n) {
          break;
        }
      }
      return json::serialize(nbest);
    }
    void resizeResultBuf(int size) {
      if (size < size_) {
        return;
      }
      while (size_ < size) {
        size_ *= 2;
      }
      delete[] result_;
      result_ = new char[size_];
      result_[0] = '\0';
    }
};

void InitLog() {
  google::InitGoogleLogging("wenet");
}

DecoderParams* DecoderParams_New() {
  DecoderParams* params = new DecoderParams;
  return params;
}
void DecoderParams_Free(DecoderParams* params) {
  delete params;
}
void DecoderParams_Set_num_threads(DecoderParams* params, int num_threads) {
  params->num_threads = num_threads;
}
void DecoderParams_Set_model_path(DecoderParams* params, const char* model_path) {
  std::string path(model_path);
  params->model_path = path;
}
void DecoderParams_Set_num_bins(DecoderParams* params, int num_bins) {
  params->num_bins = num_bins;
}
void DecoderParams_Set_sample_rate_in(DecoderParams* params, int sample_rate_in) {
  params->sample_rate_in = sample_rate_in;
}
void DecoderParams_Set_sample_rate(DecoderParams* params, int sample_rate) {
  params->sample_rate = sample_rate;
}
void DecoderParams_Set_chunk_size(DecoderParams* params, int chunk_size) {
  params->chunk_size = chunk_size;
}
void DecoderParams_Set_num_left_chunks(DecoderParams* params, int num_left_chunks) {
  params->num_left_chunks = num_left_chunks;
}
void DecoderParams_Set_ctc_weight(DecoderParams* params, double ctc_weight) {
  params->ctc_weight = ctc_weight;
}
void DecoderParams_Set_rescoring_weight(DecoderParams* params, double rescoring_weight) {
  params->rescoring_weight = rescoring_weight;
}
void DecoderParams_Set_nbest(DecoderParams* params, int nbest) {
  params->nbest = nbest;
}
void DecoderParams_Set_max_audio_length(DecoderParams* params, int max_audio_length) {
  params->max_audio_length = max_audio_length;
}
void DecoderParams_Set_dict_path(DecoderParams* params, const char* dict_path) {
  std::string path(dict_path);
  params->dict_path = path;
}
void DecoderParams_Set_context_path(DecoderParams* params, const char* context_path) {
  std::string path(context_path);
  params->context_path = context_path;
}
void DecoderParams_Set_context_score(DecoderParams* params, double context_score) {
  params->context_score = context_score;
}
void DecoderParams_LogConfig(DecoderParams* params) {
  params->LogConfig();
}

AsrDecoder* AsrDecoder_New(const DecoderParams* params) {
  AsrDecoder* asr_decoder = new AsrDecoder(params);
  return asr_decoder;
}
void AsrDecoder_Free(AsrDecoder* decoder) {
  delete decoder;
}
void AsrDecoder_Set_num_results(AsrDecoder* decoder, int num_results) {
  decoder->SetNumResults(num_results);
}
void AsrDecoder_Set_sample_rate_in(AsrDecoder* decoder, int sample_rate_in) {
  decoder->SetSampleRateIn(sample_rate_in);
}
void AsrDecoder_AcceptWaveform(AsrDecoder* decoder, const char* pcm, int length) {
  decoder->AcceptWaveform(pcm, length);
}
void AsrDecoder_AcceptWavefile(AsrDecoder* decoder, const char* wav_path) {
  decoder->AcceptWavefile(wav_path);
}
void AsrDecoder_SetInputFinished(AsrDecoder* decoder) {
  decoder->SetInputFinished();
}
int AsrDecoder_AdvanceDecoding(AsrDecoder* decoder) {
  return decoder->AdvanceDecoding();
}
const char* AsrDecoder_Result(AsrDecoder* decoder) {
  return decoder->Result();
}
void AsrDecoder_Reset(AsrDecoder* decoder) {
  decoder->Reset();
}
void AsrDecoder_LogConfig(AsrDecoder* decoder) {
  decoder->LogConfig();
}
