"""Run the Flask Meeting Assistant.

This file used to contain a Streamlit implementation. To avoid confusing
`ModuleNotFoundError` messages when running `python app.py`, it now simply
launches the Flask app defined in ``run.py``.
"""

from run import app, socketio

# OpenAI API 키 설정
# Streamlit Cloud의 Secrets 또는 로컬 환경 변수에서 키를 가져옵니다.
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    google_sheet_creds_dict = st.secrets["GOOGLE_SHEET_CREDS"]
except (FileNotFoundError, KeyError):
    # 로컬 테스트를 위해 직접 키를 입력할 수 있습니다.
    openai.api_key = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
    # 로컬 테스트용 Google Sheets 자격 증명 (secret/credentials.json 파일 내용)
    # 이 부분은 배포 시에는 Streamlit Secrets로 관리해야 합니다.
    google_sheet_creds_dict = {} 

# Google Sheets 인증
try:
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_sheet_creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("미팅GPT")
except Exception as e:
    st.error(f"Google Sheets 인증에 실패했습니다: {e}")
    spreadsheet = None


# --- 2. 핵심 함수 정의 ---

@st.cache_data
def transcribe_audio(audio_bytes):
    """오디오 바이트를 텍스트로 변환하는 함수"""
    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,  # 오디오 레코더의 기본 샘플링 레이트
            language_code="ko-KR",
            enable_automatic_punctuation=True,
        )
        response = client.recognize(config=config, audio=audio)
        return "".join([result.alternatives[0].transcript for result in response.results])
    except Exception as e:
        st.error(f"음성 인식 중 오류 발생: {e}")
        return None

@st.cache_data
def get_gpt_suggestion(text, style_prompt):
    """텍스트를 기반으로 GPT 답변을 생성하는 함수"""
    try:
        system_message = f"You are a helpful meeting assistant. Based on the user's speech, provide a concise, actionable, and helpful response or suggestion to advance the meeting. {style_prompt}. Please respond in Korean."
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"GPT 답변 생성 중 오류 발생: {e}")
        return "AI 답변을 생성할 수 없습니다."

def add_to_sheet(worksheet, data):
    """데이터를 구글 시트에 추가하는 함수"""
    try:
        # 데이터프레임으로 변환하여 추가
        df = pd.DataFrame([data])
        # 헤더 없이 데이터만 추가
        worksheet.append_rows(df.values.tolist(), value_input_option='USER_ENTERED')
    except Exception as e:
        st.error(f"시트 저장 중 오류 발생: {e}")

# --- 3. Streamlit UI 구성 ---

st.title("🚀 실시간 미팅 어시스턴트")
st.markdown("---")

# 세션 상태 초기화 (데이터를 페이지 리로드 간에 유지하기 위함)
if 'meeting_data' not in st.session_state:
    st.session_state.meeting_data = []
if 'current_sheet' not in st.session_state:
    st.session_state.current_sheet = None
if 'meeting_started' not in st.session_state:
    st.session_state.meeting_started = False


# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ 미팅 설정")
    
    if not st.session_state.meeting_started:
        meeting_title = st.text_input("미팅 제목", f"미팅_{datetime.now().strftime('%Y%m%d_%H%M')}")
        
        if st.button("새 미팅 시작", type="primary"):
            if spreadsheet:
                try:
                    # 새 워크시트 생성
                    new_sheet = spreadsheet.add_worksheet(title=meeting_title, rows="100", cols="4")
                    # 헤더 추가
                    new_sheet.append_row(["타임스탬프", "고객 발언", "AI 추천 답변", "답변 스타일"])
                    st.session_state.current_sheet = new_sheet
                    st.session_state.meeting_started = True
                    st.session_state.meeting_data = [] # 이전 데이터 초기화
                    st.rerun() # 페이지 새로고침
                except gspread.exceptions.WorksheetExists:
                    st.warning("같은 이름의 미팅이 이미 존재합니다. 다른 제목을 사용해주세요.")
                except Exception as e:
                    st.error(f"시트 생성 중 오류 발생: {e}")
            else:
                st.error("Google Sheets에 연결할 수 없어 미팅을 시작할 수 없습니다.")
    else:
        st.success(f"'{st.session_state.current_sheet.title}' 미팅 진행 중...")
        if st.button("미팅 종료"):
            st.session_state.meeting_started = False
            st.session_state.current_sheet = None
            st.session_state.meeting_data = []
            st.rerun()

    st.markdown("---")
    st.header("🎨 답변 스타일")
    answer_style = st.selectbox(
        "스타일 선택",
        ["기본 (간결하고 명확하게)", "친절한 영업사원", "공격적인 협상가", "꼼꼼한 분석가"],
        key="answer_style_select"
    )
    style_prompt = st.text_area(
        "AI 프롬프트 (직접 수정 가능)",
        {
            "기본 (간결하고 명확하게)": "Be concise and clear.",
            "친절한 영업사원": "Respond in a very friendly, positive, and persuasive tone, focusing on building a good relationship.",
            "공격적인 협상가": "Respond with a strong, assertive, and challenging tone, aiming to get the best possible deal.",
            "꼼꼼한 분석가": "Respond with a detailed, data-driven, and analytical tone, asking clarifying questions and pointing out potential issues."
        }[answer_style],
        height=150
    )


# --- 메인 화면 ---
if st.session_state.meeting_started:
    st.subheader("🎤 음성 녹음 및 변환")
    
    # 오디오 레코더 UI
    audio_bytes = st_audiorecorder(
        start_prompt="▶️ 녹음 시작",
        stop_prompt="⏹️ 녹음 중지",
        pause_prompt="",
        key="audio_recorder"
    )

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        with st.spinner("음성을 텍스트로 변환 중..."):
            transcript_text = transcribe_audio(audio_bytes)

        if transcript_text:
            st.success("음성 변환 완료!")
            
            with st.spinner("AI가 최적의 답변을 생성 중..."):
                gpt_response = get_gpt_suggestion(transcript_text, style_prompt)

            # 결과 데이터 구성
            new_data = {
                "타임스탬프": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "고객 발언": transcript_text,
                "AI 추천 답변": gpt_response,
                "답변 스타일": answer_style
            }
            
            # 세션 상태에 데이터 추가 및 시트에 저장
            st.session_state.meeting_data.insert(0, new_data)
            if st.session_state.current_sheet:
                add_to_sheet(st.session_state.current_sheet, new_data)

    st.markdown("---")

    # 데이터 표시
    st.subheader("📋 실시간 회의록")
    if st.session_state.meeting_data:
        # 데이터프레임으로 변환하여 표시
        df = pd.DataFrame(st.session_state.meeting_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("녹음된 내용이 없습니다. '녹음 시작' 버튼을 눌러 미팅을 기록하세요.")

else:
    st.info("왼쪽 사이드바에서 '새 미팅 시작' 버튼을 눌러주세요.")
