import copy
import json
import logging
from typing import List

from starlette.websockets import WebSocket

from .asr_decoder import AsrDecoder

logging.basicConfig(level=logging.DEBUG)


# client event
StartTranscription = "StartTranscription"
StopTranscription = "StopTranscription"

# server event
TranscriptionStarted = "TranscriptionStarted"
TranscriptionResultChanged = "TranscriptionResultChanged"
SentenceEnd = "SentenceEnd"
TranscriptionCompleted = "TranscriptionCompleted"

# client msg
start_msg = {
    "header": {
        "event_name": StartTranscription,
    },
    "payload": {
        "sample_rate": 8000,  # 8000 或 16000，默认是 16000
    },
}
stop_msg = {
    "header": {
        "event_name": StopTranscription,
    }
}

# server msg
transcription_started = {
    "header": {
        "status": 200,
        "status_message": "ok",
        "event_name": "TranscriptionStarted",
    }
}

transcription_result_changed = {
    "header": {
        "status": 200,
        "status_message": "ok",
        "event_name": "TranscriptionResultChanged",
    },
    "payload": {"index": 1, "result": "不", "words": []},
}

sentence_end = {
    "header": {
        "status": 200,
        "status_message": "ok",
        "event_name": "SentenceEnd",
    },
    "payload": {
        "index": 1,
        "result": "不嗯不能做",
        "words": [
            {"text": "不", "start_time": 0, "end_time": 5160},
            {"text": "嗯", "start_time": 5160, "end_time": 8600},
            {"text": "不", "start_time": 8600, "end_time": 8880},
            {"text": "能", "start_time": 8880, "end_time": 9120},
            {"text": "做", "start_time": 9120, "end_time": 10120},
        ],
    },
}

transcription_completed = {
    "header": {
        "status": 200,
        "status_message": "ok",
        "event_name": "TranscriptionCompleted",
    }
}


class ParameterError(Exception):
    pass


class ConnClosedError(Exception):
    pass


async def handle_ws(ws: WebSocket) -> None:
    decoder = AsrDecoder(
        "model/127.zip",
        "model/words.txt",
        sample_rate_in=8000,
        num_threads=1,
    )
    while True:
        decoder.reset()
        try:
            await handle_task(ws, decoder)
        except ConnClosedError:
            break
        except Exception:
            logging.error("ws error", exc_info=True)
            break
    decoder.free()


async def handle_task(ws: WebSocket, decoder: AsrDecoder) -> None:
    state = "init"
    while True:
        msg = await ws.receive()
        if msg["type"] == "websocket.disconnect":
            raise ConnClosedError("ws conn closed")
        if state == "init":
            state = "start"
            msg = msg["text"]
            msg_dict = json.loads(msg)
            if msg_dict["header"]["event_name"] != StartTranscription:
                raise ParameterError("start msg is expected")
            await ws.send_text(
                json.dumps(transcription_started, ensure_ascii=False)
            )
        elif state == "start":
            state = "wav"
            if not msg.get("bytes"):
                raise ParameterError("raw pcm data is expected")
            msg = msg["bytes"]
            decoder.accept_waveform(msg)
            while True:
                decode_state = decoder.advance_decoding()
                result = decoder.result()
                if result:
                    server_msg = copy.deepcopy(transcription_result_changed)
                    server_msg["payload"] = msg_to_payload(result)
                    await ws.send_text(
                        json.dumps(server_msg, ensure_ascii=False)
                    )
                if decode_state == 3:
                    break
        elif state == "wav":
            if msg.get("bytes"):
                state = "wav"
                msg = msg["bytes"]
                decoder.accept_waveform(msg)
                while True:
                    decode_state = decoder.advance_decoding()
                    result = decoder.result()
                    if result:
                        server_msg = copy.deepcopy(
                            transcription_result_changed
                        )
                        server_msg["payload"] = msg_to_payload(result)
                        await ws.send_text(
                            json.dumps(server_msg, ensure_ascii=False)
                        )
                    if decode_state == 3:
                        break
            else:
                state = "stop"
                decoder.set_input_finished()
                while True:
                    decode_state = decoder.advance_decoding()
                    result = decoder.result()
                    if result:
                        server_msg = copy.deepcopy(
                            transcription_result_changed
                        )
                        server_msg["payload"] = msg_to_payload(result)
                        await ws.send_text(
                            json.dumps(server_msg, ensure_ascii=False)
                        )
                    if decode_state == 3:
                        server_msg = transcription_completed
                        await ws.send_text(
                            json.dumps(server_msg, ensure_ascii=False)
                        )
                        return


def msg_to_payload(msg_lst: List[dict]) -> dict:
    msg_dict = msg_lst[0]
    payload = {
        "index": msg_dict["index"],
        "text": msg_dict["sentence"],
        "words": msg_dict.get("words", []),
    }
    return payload


async def app(scope, receive, send):
    websocket = WebSocket(scope=scope, receive=receive, send=send)
    await websocket.accept()
    try:
        await handle_ws(websocket)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
