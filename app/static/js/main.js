// 전역 변수 설정
let socket;
let audioContext;
let isRecording = false;

// HTML 문서에서 필요한 요소들을 미리 찾아 변수에 저장합니다.
const startBtn = document.getElementById('start-record-btn');
const stopBtn = document.getElementById('stop-record-btn');
const statusText = document.getElementById('status-text');
const transcriptSheet = document.getElementById('transcript-sheet');
const styleSelect = document.getElementById('style-select');

// (중요) WebSocket 대신 Polling 연결 방식을 강제하여 App Engine과의 호환성을 높입니다.
socket = io({ transports: ['polling'] });

// 서버와 성공적으로 연결되었을 때 실행되는 이벤트 리스너입니다.
socket.on('connect', () => {
    console.log('진단 1: 서버에 성공적으로 연결되었습니다.');
});

// 실시간으로 음성 변환 텍스트를 받았을 때 처리하는 부분입니다.
let currentTranscriptRow = null;
socket.on('transcript_update', (data) => {
    // 새로운 텍스트를 표시할 행이 없으면 새로 만듭니다.
    if (!currentTranscriptRow) {
        createNewRow();
    }
    
    const transcriptCell = currentTranscriptRow.querySelector('.transcript-cell');
    transcriptCell.textContent = data.transcript;

    // 문장이 완성되면 (is_final=true), 다음 텍스트는 새 줄에 표시되도록 합니다.
    if (data.is_final) {
        transcriptCell.classList.remove('interim');
        currentTranscriptRow = null;
    } else {
        transcriptCell.classList.add('interim');
    }
});

// 문장이 완성되고 AI 추천 답변까지 도착했을 때 처리하는 부분입니다.
socket.on('final_result', (data) => {
    const rows = transcriptSheet.querySelectorAll('.sheet-row');
    // 완성된 문장을 찾아 해당 행의 AI 답변 칸을 채웁니다.
    for (let i = rows.length - 1; i >= 0; i--) {
        const row = rows[i];
        const textCell = row.querySelector('.transcript-cell');
        if (textCell && textCell.textContent.trim() === data.text.trim() && !row.dataset.id) {
            row.dataset.id = data.transcript_id;
            const gptCell = row.querySelector('.gpt-cell');
            if (gptCell) gptCell.textContent = data.gpt_response;
            break;
        }
    }
});

// '녹음 시작' 버튼 클릭 이벤트
startBtn.addEventListener('click', async () => {
    if (isRecording || !socket.connected) return;
    console.log('진단 2: 녹음 시작 버튼이 클릭되었습니다.');

    try {
        // 사용자의 마이크에 접근하여 오디오 스트림을 가져옵니다.
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('진단 3: 마이크 접근에 성공했습니다. 스트림이 생성되었습니다.');
        
        // 오디오 처리를 위한 AudioContext를 생성합니다.
        audioContext = new AudioContext();
        // 별도의 스레드에서 오디오를 처리할 audio-processor.js 파일을 로드합니다.
        await audioContext.audioWorklet.addModule('/static/js/audio-processor.js');
        console.log('진단 4: 오디오 워크릿 모듈을 성공적으로 로드했습니다.');
        
        const source = audioContext.createMediaStreamSource(stream);
        const workletNode = new AudioWorkletNode(audioContext, 'resampling-processor');

        // 오디오 워크릿이 처리한 음성 데이터를 서버로 전송합니다.
        workletNode.port.onmessage = (event) => {
            console.log('진단 5: 오디오 청크를 성공적으로 처리하여 서버로 전송합니다.');
            socket.emit('audio_stream', { 'data': event.data });
        };
        
        source.connect(workletNode);
        workletNode.connect(audioContext.destination);

        isRecording = true;
        updateButtonState();
        statusText.textContent = translations[window.getSavedLanguage()].status_recording;

        // 서버에 녹음 시작을 알립니다.
        socket.emit('start_transcription', {
            meeting_id: MEETING_ID,
            language: LANGUAGE_CODE,
            style_id: styleSelect.value
        });

    } catch (error) {
        console.error('진단 실패: 녹음 시작 중 오류가 발생했습니다.', error);
        statusText.textContent = translations[window.getSavedLanguage()].status_error;
    }
});

// '녹음 중지' 버튼 클릭 이벤트
stopBtn.addEventListener('click', () => {
    if (!isRecording) return;
    isRecording = false;
    updateButtonState();
    statusText.textContent = translations[window.getSavedLanguage()].status_stopping;
    
    // 서버에 녹음 중지를 알립니다.
    socket.emit('stop_transcription', {});

    // 오디오 처리를 깨끗하게 종료합니다.
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close().then(() => {
            statusText.textContent = translations[window.getSavedLanguage()].status_stopped;
        });
    }
});

// 답변 스타일 변경 이벤트
styleSelect.addEventListener('change', () => {
    if (isRecording) {
        socket.emit('change_style', { style_id: styleSelect.value });
    }
});

socket.on('style_changed_ack', (data) => {
    console.log(data.message);
});

// 버튼 활성화/비활성화 상태를 업데이트하는 함수
function updateButtonState() {
    startBtn.disabled = isRecording;
    stopBtn.disabled = !isRecording;
}

// 시트에 새로운 행을 추가하는 함수
function createNewRow() {
    const row = document.createElement('div');
    row.className = 'sheet-row';
    
    const cell1 = document.createElement('div');
    cell1.className = 'sheet-cell transcript-cell';
    cell1.textContent = '...';

    const cell2 = document.createElement('div');
    cell2.className = 'sheet-cell gpt-cell';
    cell2.textContent = '...';
    
    row.appendChild(cell1);
    row.appendChild(cell2);
    
    transcriptSheet.appendChild(row);
    // 새 행이 추가되면 자동으로 스크롤을 맨 아래로 내립니다.
    transcriptSheet.scrollTop = transcriptSheet.scrollHeight;
    currentTranscriptRow = row;
}
