#ifndef DECODER_CAPI_H_
#define DECODER_CAPI_H_

#ifdef __cplusplus
#include "decoder/init.h"
struct AsrDecoder;
using namespace wenet;
#else
typedef struct DecoderParams DecoderParams;
typedef struct AsrDecoder AsrDecoder;
#endif

#ifdef __cplusplus
extern "C" {
#endif

void InitLog();

DecoderParams* DecoderParams_New();
void DecoderParams_Free(DecoderParams* params);
void DecoderParams_Set_num_threads(DecoderParams* params, int num_threads);
void DecoderParams_Set_model_path(DecoderParams* params, const char* model_path);
void DecoderParams_Set_num_bins(DecoderParams* params, int num_bins);
void DecoderParams_Set_sample_rate_in(DecoderParams* params, int sample_rate_in);
void DecoderParams_Set_sample_rate(DecoderParams* params, int sample_rate);
void DecoderParams_Set_chunk_size(DecoderParams* params, int chunk_size);
void DecoderParams_Set_num_left_chunks(DecoderParams* params, int num_left_chunks);
void DecoderParams_Set_ctc_weight(DecoderParams* params, double ctc_weight);
void DecoderParams_Set_rescoring_weight(DecoderParams* params, double rescoring_weight);
void DecoderParams_Set_nbest(DecoderParams* params, int nbest);
void DecoderParams_Set_max_audio_length(DecoderParams* params, int max_audio_length);
void DecoderParams_Set_dict_path(DecoderParams* params, const char* dict_path);
void DecoderParams_Set_context_path(DecoderParams* params, const char* context_path);
void DecoderParams_Set_context_score(DecoderParams* params, double context_score);
void DecoderParams_LogConfig(DecoderParams* params);

AsrDecoder* AsrDecoder_New(const DecoderParams* params);
void AsrDecoder_Free(AsrDecoder* decoder);
void AsrDecoder_Set_num_results(AsrDecoder* decoder, int num_results);
void AsrDecoder_Set_sample_rate_in(AsrDecoder* decoder, int sample_rate_in);
void AsrDecoder_AcceptWaveform(AsrDecoder* decoder, const char* pcm, int length);
void AsrDecoder_AcceptWavefile(AsrDecoder* decoder, const char* wav_path);
void AsrDecoder_SetInputFinished(AsrDecoder* decoder);
int AsrDecoder_AdvanceDecoding(AsrDecoder* decoder);
const char* AsrDecoder_Result(AsrDecoder* decoder);
void AsrDecoder_Reset(AsrDecoder* decoder);
void AsrDecoder_LogConfig(AsrDecoder* decoder);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // DECODER_CAPI_H_
