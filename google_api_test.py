import os
import pytest

speech = pytest.importorskip('google.cloud.speech')

# .env 파일이나 다른 설정 없이, 직접 자격 증명 파일을 지정합니다.
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_credentials.json'

def transcribe_file(speech_file):
    """지정된 오디오 파일을 텍스트로 변환합니다."""
    client = speech.SpeechClient()

    print("1. Google Speech 클라이언트 생성 완료.")

    try:
        with open(speech_file, "rb") as audio_file:
            content = audio_file.read()
        
        print(f"2. '{speech_file}' 파일 읽기 완료.")

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="ko-KR",
        )

        print("3. Google에 텍스트 변환 요청 전송 시작...")
        
        # 스트리밍이 아닌, 간단한 단일 요청을 보냅니다.
        response = client.recognize(config=config, audio=audio)
        
        print("4. Google로부터 응답 수신 완료!")

        for result in response.results:
            print("-" * 20)
            print(f"변환된 텍스트: {result.alternatives[0].transcript}")
            print(f"정확도: {result.alternatives[0].confidence:.2f}")
            print("-" * 20)

    except Exception as e:
        print("\n" + "="*20)
        print("!!! 테스트 중 심각한 오류가 발생했습니다 !!!")
        print(f"오류 종류: {type(e).__name__}")
        print(f"오류 메시지: {e}")
        print("="*20)

if __name__ == "__main__":
    transcribe_file("test_audio.wav")
