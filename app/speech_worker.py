# app/speech_worker.py

import queue
from google.cloud import speech
from flask_socketio import SocketIO
from flask import current_app

class SpeechWorker:
    """Google Speech-to-Text API 스트리밍을 관리하는 클래스"""

    def __init__(self, socketio: SocketIO, sid: str, language_code: str, sample_rate: int = 16000):
        self.socketio = socketio
        self.sid = sid
        self.language_code = language_code
        self.sample_rate = sample_rate
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate,
            language_code=self.language_code,
            enable_automatic_punctuation=True,
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True
        )
        self._buffer = queue.Queue()
        self.closed = False

    def _generator(self):
        """버퍼에서 오디오 청크를 가져와 API로 보낼 요청을 생성합니다."""
        while not self.closed:
            chunk = self._buffer.get()
            if chunk is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    def process(self):
        """API로부터 응답을 받고 실시간으로 클라이언트에 전송합니다."""
        try:
            requests = self._generator()
            responses = self.client.streaming_recognize(
                config=self.streaming_config,
                requests=requests
            )
            self._listen_for_responses(responses)
        except Exception as e:
            current_app.logger.error(f"Speech worker error for {self.sid}: {e}")

    def _listen_for_responses(self, responses):
        """응답을 분석하여 최종 또는 중간 결과를 클라이언트로 보냅니다."""
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            if result.is_final:
                current_app.logger.info(f"Final transcript for {self.sid}: {transcript}")
                self.socketio.emit('final_transcript', {'transcript': transcript}, to=self.sid)
            else:
                self.socketio.emit('interim_transcript', {'transcript': transcript}, to=self.sid)

    def add_audio_chunk(self, chunk):
        """메인 스레드에서 오디오 데이터를 버퍼에 추가합니다."""
        if not self.closed:
            self._buffer.put(chunk)

    def close(self):
        """스트림을 안전하게 종료합니다."""
        if not self.closed:
            current_app.logger.info(f"Closing speech worker for {self.sid}")
            self.closed = True
            self._buffer.put(None)