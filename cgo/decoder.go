package decoder

/*
#cgo CFLAGS: -I/usr/local/include/wenet
#cgo LDFLAGS: -L/usr/local/lib/wenet -Wl,-rpath=/usr/local/lib/wenet -lasr_decoder_capi

#include "decoder_capi.h"
#include <stdlib.h>
*/
import "C"
import (
	"encoding/json"
	"sync"
	"unsafe"
)

func init() {
	C.InitLog()
}

type AsrDecoderPool struct {
	lock     sync.Mutex
	decoders []*AsrDecoder
	size     int
	opts     []func(*C.DecoderParams)
}

func NewAsrDecoderPool(size int, opts ...func(*C.DecoderParams)) *AsrDecoderPool {
	pool := &AsrDecoderPool{
		size: size,
		opts: opts,
	}
	for i := 0; i <= size; i++ {
		decoder := NewAsrDecoder(opts...)
		pool.decoders = append(pool.decoders, decoder)
	}
	return pool
}

func (p *AsrDecoderPool) Get() *AsrDecoder {
	p.lock.Lock()
	defer p.lock.Unlock()

	l := len(p.decoders)
	if l > 0 {
		decoder := p.decoders[l-1]
		p.decoders = p.decoders[:l-1]
		return decoder
	}
	return NewAsrDecoder(p.opts...)
}

func (p *AsrDecoderPool) Put(decoder *AsrDecoder) {
	p.lock.Lock()
	defer p.lock.Unlock()

	decoder.Reset()
	l := len(p.decoders)
	if l < p.size {
		p.decoders = append(p.decoders, decoder)
	} else {
		decoder.Free()
	}
}

type DecodeState int

const (
	DecodeStateEndBatch DecodeState = iota
	DecodeStateEndpoint
	DecodeStateEndFeats
	DecodeStateWaitMoreFeats
)

type AsrDecoder struct {
	decoder *C.AsrDecoder
}

func NewAsrDecoder(opts ...func(*C.DecoderParams)) *AsrDecoder {
	params := C.DecoderParams_New()
	defer C.DecoderParams_Free(params)
	for _, opt := range opts {
		opt(params)
	}
	asr_decoder := C.AsrDecoder_New(params)
	a := &AsrDecoder{
		decoder: asr_decoder,
	}
	return a
}

func (a *AsrDecoder) Free() {
	C.AsrDecoder_Free(a.decoder)
}

func NumThreads(n int) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		C.DecoderParams_Set_num_threads(a, C.int(n))
	}
}

func ModelPath(model_path string) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		path := C.CString(model_path)
		defer C.free(unsafe.Pointer(path))
		C.DecoderParams_Set_model_path(a, path)
	}
}

func DictPath(dict_path string) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		path := C.CString(dict_path)
		defer C.free(unsafe.Pointer(path))
		C.DecoderParams_Set_dict_path(a, path)
	}
}

func SampleRateIn(n int) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		C.DecoderParams_Set_sample_rate_in(a, C.int(n))
	}
}

func SampleRate(n int) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		C.DecoderParams_Set_sample_rate(a, C.int(n))
	}
}

func ChunkSize(n int) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		C.DecoderParams_Set_chunk_size(a, C.int(n))
	}
}

func NumLeftChunks(n int) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		C.DecoderParams_Set_num_left_chunks(a, C.int(n))
	}
}

func CtcWeight(n float64) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		C.DecoderParams_Set_ctc_weight(a, C.double(n))
	}
}

func RescoringWeight(n float64) func(*C.DecoderParams) {
	return func(a *C.DecoderParams) {
		C.DecoderParams_Set_rescoring_weight(a, C.double(n))
	}
}

func (a *AsrDecoder) SetSampleRateIn(sample_rate_in int) {
	C.AsrDecoder_Set_sample_rate_in(a.decoder, C.int(sample_rate_in))
}

func (a *AsrDecoder) SetNumResults(num_results int) {
	C.AsrDecoder_Set_num_results(a.decoder, C.int(num_results))
}

func (a *AsrDecoder) AcceptWaveform(pcm []byte) {
	c_size := C.int(len(pcm))
	c_pcm := (*C.char)(unsafe.Pointer(&pcm[0]))
	C.AsrDecoder_AcceptWaveform(a.decoder, c_pcm, c_size)
}

func (a *AsrDecoder) AcceptWavefile(wav_path string) {
	c_wav_path := C.CString(wav_path)
	defer C.free(unsafe.Pointer(c_wav_path))
	C.AsrDecoder_AcceptWavefile(a.decoder, c_wav_path)
}

func (a *AsrDecoder) SetInputFinished() {
	C.AsrDecoder_SetInputFinished(a.decoder)
}

func (a *AsrDecoder) AdvanceDecoding() DecodeState {
	return DecodeState(C.AsrDecoder_AdvanceDecoding(a.decoder))
}

func (a *AsrDecoder) Results() ([]AsrResult, error) {
	result := C.AsrDecoder_Result(a.decoder)
	s := C.GoString(result)
	if s == "" {
		return nil, nil
	}
	var asr_result []AsrResult
	err := json.Unmarshal([]byte(s), &asr_result)
	if err != nil {
		return nil, err
	}
	return asr_result, nil
}

func (a *AsrDecoder) Reset() {
	C.AsrDecoder_Reset(a.decoder)
}

func (a *AsrDecoder) LogConfig() {
	C.AsrDecoder_LogConfig(a.decoder)
}

type AsrResult struct {
	Index    int       `json:"index"`
	Sentence string    `json:"sentence"`
	Words    []AsrWord `json:"words,omitempty"`
}

type AsrWord struct {
	Text      string `json:"text"`
	StartTime int    `json:"start_time"`
	EndTime   int    `json:"end_time"`
}
