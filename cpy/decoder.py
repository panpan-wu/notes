import ctypes

lib = ctypes.cdll.LoadLibrary('./libasr_decoder.so')

lib.Asr_InitLog.argtypes = []
lib.Asr_InitLog.restype = None

lib.Asr_New.argtypes = [
    ctypes.c_char_p,  # char* model_path
    ctypes.c_char_p,  # char* unit_path
]
lib.Asr_New.restype = ctypes.c_void_p

lib.Asr_Delete.argtypes = [ctypes.c_void_p]
lib.Asr_Delete.restype = None

lib.Asr_Infer.argtypes = [
    ctypes.c_void_p,  # Asr*
    ctypes.c_char_p,  # char* wav_path
    ctypes.c_char_p,  # char* buf
    ctypes.c_int,  # int buf_len
    ctypes.POINTER(ctypes.c_int),  # int* out_len
]
lib.Asr_Infer.restype = ctypes.c_void_p

class Asr:
    def __init__(self, model_path, unit_path):
        self._asr = lib.Asr_New(
            ctypes.c_char_p(model_path.encode("utf-8")),
            ctypes.c_char_p(unit_path.encode("utf-8")),
        )

    def infer(self, wav_path):
        buf_len = 100
        buf = ctypes.create_string_buffer(buf_len)
        out_len = ctypes.c_int(0)
        lib.Asr_Infer(
            self._asr,
            ctypes.c_char_p(wav_path.encode("utf-8")),
            buf,
            ctypes.c_int(buf_len),
            ctypes.byref(out_len)
        )
        print("out_len:", out_len)
        sentence = buf.raw[:out_len.value]
        print("sentence:", sentence.decode("utf-8"))

    def __del__(self):
        lib.Asr_Delete(self._asr)


def main():
    lib.Asr_InitLog()
    model_path = "exp/conformer/127.zip"
    unit_path = "exp/conformer/words.txt"
    wav_path = "/mydata/data/outbound_call/2144/2021-10-31/68465302_1.wav"
    asr = Asr(model_path, unit_path)
    asr.infer(wav_path)


if __name__ == "__main__":
    main()
