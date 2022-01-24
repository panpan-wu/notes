import json
from ctypes import *
from typing import List

asr = cdll.LoadLibrary("/usr/local/lib/wenet/libasr_decoder_capi.so")

# void InitLog();
asr.InitLog.argtypes = []
asr.InitLog.restype = None

# DecoderParams* DecoderParams_New();
asr.DecoderParams_New.argtypes = []
asr.DecoderParams_New.restype = c_void_p

# void DecoderParams_Free(DecoderParams* params);
asr.DecoderParams_Free.argtypes = [c_void_p]
asr.DecoderParams_Free.restype = None

# void DecoderParams_Set_num_threads(DecoderParams* params, int num_threads);
asr.DecoderParams_Set_num_threads.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_num_threads.restype = None

# void DecoderParams_Set_model_path(DecoderParams* params, const char* model_path);
asr.DecoderParams_Set_model_path.argtypes = [c_void_p, c_char_p]
asr.DecoderParams_Set_model_path.restype = None

# void DecoderParams_Set_num_bins(DecoderParams* params, int num_bins);
asr.DecoderParams_Set_num_bins.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_num_bins.restype = None

# void DecoderParams_Set_sample_rate_in(DecoderParams* params, int sample_rate_in);
asr.DecoderParams_Set_sample_rate_in.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_sample_rate_in.restype = None

# void DecoderParams_Set_sample_rate(DecoderParams* params, int sample_rate);
asr.DecoderParams_Set_sample_rate.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_sample_rate.restype = None

# void DecoderParams_Set_chunk_size(DecoderParams* params, int chunk_size);
asr.DecoderParams_Set_chunk_size.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_chunk_size.restype = None

# void DecoderParams_Set_num_left_chunks(DecoderParams* params, int num_left_chunks);
asr.DecoderParams_Set_num_left_chunks.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_num_left_chunks.restype = None

# void DecoderParams_Set_ctc_weight(DecoderParams* params, double ctc_weight);
asr.DecoderParams_Set_ctc_weight.argtypes = [c_void_p, c_double]
asr.DecoderParams_Set_ctc_weight.restype = None

# void DecoderParams_Set_rescoring_weight(DecoderParams* params, double rescoring_weight);
asr.DecoderParams_Set_rescoring_weight.argtypes = [c_void_p, c_double]
asr.DecoderParams_Set_rescoring_weight.restype = None

# void DecoderParams_Set_nbest(DecoderParams* params, int nbest);
asr.DecoderParams_Set_nbest.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_nbest.restype = None

# void DecoderParams_Set_max_audio_length(DecoderParams* params, int max_audio_length);
asr.DecoderParams_Set_max_audio_length.argtypes = [c_void_p, c_int]
asr.DecoderParams_Set_max_audio_length.restype = None

# void DecoderParams_Set_dict_path(DecoderParams* params, const char* dict_path);
asr.DecoderParams_Set_dict_path.argtypes = [c_void_p, c_char_p]
asr.DecoderParams_Set_dict_path.restype = None

# void DecoderParams_Set_context_path(DecoderParams* params, const char* context_path);
asr.DecoderParams_Set_context_path.argtypes = [c_void_p, c_char_p]
asr.DecoderParams_Set_context_path.restype = None

# void DecoderParams_Set_context_score(DecoderParams* params, double context_score);
asr.DecoderParams_Set_context_score.argtypes = [c_void_p, c_double]
asr.DecoderParams_Set_context_score.restype = None

# void DecoderParams_LogConfig(DecoderParams* params);
asr.DecoderParams_LogConfig.argtypes = [c_void_p]
asr.DecoderParams_LogConfig.restype = None


# AsrDecoder* AsrDecoder_New(const DecoderParams* params);
asr.AsrDecoder_New.argtypes = [c_void_p]
asr.AsrDecoder_New.restype = c_void_p

# void AsrDecoder_Free(AsrDecoder* decoder);
asr.AsrDecoder_Free.argtypes = [c_void_p]
asr.AsrDecoder_Free.restype = None

# void AsrDecoder_Set_num_results(AsrDecoder* decoder, int num_results);
asr.AsrDecoder_Set_num_results.argtypes = [c_void_p, c_int]
asr.AsrDecoder_Set_num_results.restype = None

# void AsrDecoder_Set_sample_rate_in(AsrDecoder* decoder, int sample_rate_in);
asr.AsrDecoder_Set_sample_rate_in.argtypes = [c_void_p, c_int]
asr.AsrDecoder_Set_sample_rate_in.restype = None

# void AsrDecoder_AcceptWaveform(AsrDecoder* decoder, const char* pcm, int length);
asr.AsrDecoder_AcceptWaveform.argtypes = [c_void_p, c_char_p, c_int]
asr.AsrDecoder_AcceptWaveform.restype = None

# void AsrDecoder_AcceptWavefile(AsrDecoder* decoder, const char* wav_path);
asr.AsrDecoder_AcceptWavefile.argtypes = [c_void_p, c_char_p]
asr.AsrDecoder_AcceptWavefile.restype = None

# void AsrDecoder_SetInputFinished(AsrDecoder* decoder);
asr.AsrDecoder_SetInputFinished.argtypes = [c_void_p]
asr.AsrDecoder_SetInputFinished.restype = None

# int AsrDecoder_AdvanceDecoding(AsrDecoder* decoder);
asr.AsrDecoder_AdvanceDecoding.argtypes = [c_void_p]
asr.AsrDecoder_AdvanceDecoding.restype = c_int

# const char* AsrDecoder_Result(AsrDecoder* decoder);
asr.AsrDecoder_Result.argtypes = [c_void_p]
asr.AsrDecoder_Result.restype = c_char_p

# void AsrDecoder_Reset(AsrDecoder* decoder);
asr.AsrDecoder_Reset.argtypes = [c_void_p]
asr.AsrDecoder_Reset.restype = None

# void AsrDecoder_LogConfig(AsrDecoder* decoder);
asr.AsrDecoder_LogConfig.argtypes = [c_void_p]
asr.AsrDecoder_LogConfig.restype = None


DefaultNumThreads = 1
DefaultSampleRate = 16000
DefaultSampleRateIn = 16000
DefaultChunkSize = 16
DefaultNumLeftChunks = 2
DefaultCtcWeight = 0.0
DefaultRescoringWeight = 0.0


class AsrDecoder:
    DecodeStateEndBatch = 0
    DecodeStateEndpoint = 1
    DecodeStateEndFeats = 2
    DecodeStateWaitMoreFeats = 3

    def __init__(
        self,
        model_path: str,
        dict_path: str,
        num_threads: int = DefaultNumThreads,
        sample_rate: int = DefaultSampleRate,
        sample_rate_in: int = DefaultSampleRateIn,
        chunk_size: int = DefaultChunkSize,
        num_left_chunks: int = DefaultNumLeftChunks,
        ctc_weight: float = DefaultCtcWeight,
        rescoring_weight: float = DefaultRescoringWeight,
    ):
        params = asr.DecoderParams_New()
        asr.DecoderParams_Set_model_path(
            params, c_char_p(model_path.encode("utf-8"))
        )
        asr.DecoderParams_Set_dict_path(
            params, c_char_p(dict_path.encode("utf-8"))
        )
        asr.DecoderParams_Set_num_threads(params, c_int(num_threads))
        asr.DecoderParams_Set_sample_rate(params, c_int(sample_rate))
        asr.DecoderParams_Set_sample_rate_in(params, c_int(sample_rate_in))
        asr.DecoderParams_Set_chunk_size(params, c_int(chunk_size))
        asr.DecoderParams_Set_num_left_chunks(params, c_int(num_left_chunks))
        asr.DecoderParams_Set_ctc_weight(params, c_double(ctc_weight))
        asr.DecoderParams_Set_rescoring_weight(
            params, c_double(rescoring_weight)
        )

        self._decoder = asr.AsrDecoder_New(params)
        asr.DecoderParams_Free(params)

    def set_num_results(self, num_results: int) -> None:
        asr.AsrDecoder_Set_num_results(self._decoder, c_int(num_results))

    def set_sample_rate_in(self, sample_rate_in: int) -> None:
        asr.AsrDecoder_Set_sample_rate_in(self._decoder, c_int(sample_rate_in))

    def accept_waveform(self, pcm: bytes) -> None:
        length = len(pcm)
        asr.AsrDecoder_AcceptWaveform(
            self._decoder, c_char_p(pcm), c_int(length)
        )

    def accept_wavefile(self, wav_path: str) -> None:
        asr.AsrDecoder_AcceptWavefile(
            self._decoder, c_char_p(wav_path.encode("utf-8"))
        )

    def set_input_finished(self) -> None:
        asr.AsrDecoder_SetInputFinished(self._decoder)

    def advance_decoding(self) -> int:
        return asr.AsrDecoder_AdvanceDecoding(self._decoder)

    def result(self) -> List[dict]:
        """
        Returns:
            list[dict]: [
                {
                    "index": int,
                    "sentence": str,
                    "words": [
                        {
                            "text": str,
                            "start_time": int,
                            "end_time": int,
                        },
                        ...
                    ]
                },
                ...
            ]
        """
        res = asr.AsrDecoder_Result(self._decoder)
        if res:
            return json.loads(res)
        return []

    def reset(self) -> None:
        asr.AsrDecoder_Reset(self._decoder)

    def free(self) -> None:
        asr.AsrDecoder_Free(self._decoder)


if __name__ == "__main__":
    import sys

    model_path = "model/127.zip"
    dict_path = "model/words.txt"
    wav_file = sys.argv[1]
    decoder = AsrDecoder(model_path, dict_path)
    decoder.set_sample_rate_in(8000)
    decoder.accept_wavefile(wav_file)
    while True:
        state = decoder.advance_decoding()
        print(state, decoder.result())
        if state == AsrDecoder.DecodeStateEndFeats:
            break
