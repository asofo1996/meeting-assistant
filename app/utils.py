# app/utils.py

import os
import openai

def get_gpt_suggestion(transcript, style_prompt, language="en"):
    """GPT-3.5-turbo를 사용하여 응답을 생성합니다."""
    
    # [⭐️핵심 수정⭐️] OpenAI API 키도 환경변수에서 직접 읽어옵니다.
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # 이 함수는 앱 실행 중에 호출되므로, 오류가 발생해도 서버가 멈추지는 않습니다.
        return "Error: OPENAI_API_KEY is not configured."
        
    openai.api_key = api_key

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": style_prompt},
                {"role": "user", "content": f"Based on the following transcript, provide a response in {language}. Transcript: {transcript}"}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return f"Sorry, I encountered an error: {e}"