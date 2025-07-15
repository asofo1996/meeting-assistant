import openai
from flask import current_app

def get_gpt_suggestion(text, style_prompt, language):
    try:
        language_map = {
            'en-US': 'English',
            'es-ES': 'Spanish',
            'ko-KR': 'Korean'
        }
        target_language = language_map.get(language, 'English')

        # 시스템 메시지를 통해 GPT의 역할과 언어를 명확히 지정
        system_message = f"You are a helpful meeting assistant. The user is in a business meeting. Based on their speech, provide a concise, actionable, and helpful response or suggestion to advance the meeting. {style_prompt}. Please respond in {target_language}."

        response = openai.chat.completions.create(
            model="gpt-4o",  # 최신 모델 사용 권장
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        suggestion = response.choices[0].message.content.strip()
        return suggestion
    except Exception as e:
        current_app.logger.error(f"Error getting GPT suggestion: {e}")
        error_messages = {
            'en-US': "AI response could not be generated.",
            'es-ES': "No se pudo generar la respuesta de la IA.",
            'ko-KR': "AI 답변을 생성할 수 없습니다."
        }
        return error_messages[language]
