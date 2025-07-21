document.addEventListener('DOMContentLoaded', () => {
    const startStopBtn = document.getElementById('start-stop-btn');
    const statusDiv = document.getElementById('status');
    const chatLog = document.getElementById('chat-log');
    const answerStyleSelect = document.getElementById('answer-style-select');

    let socket;
    let audioContext;
    let processor;
    let isRecording = false;

    // 네임스페이스 없이 소켓 연결
    socket = io();

    socket.on('connect', () => {
        console.log('Socket connected!');
    });

    socket.on('disconnect', () => {
        console.log('Socket disconnected!');
    });

    // 서버로부터 AI 응답을 받았을 때
    socket.on('ai_response', (data) => {
        addChatMessage('ai', data.text);
    });

    // 서버로부터 중간 음성 인식 결과를 받았을 때
    socket.on('interim_transcript', (data) => {
        updateLastCustomerMessage(data.transcript);
    });
    
    // 서버로부터 최종 음성 인식 결과를 받았을 때
    socket.on('final_transcript', (data) => {
        updateLastCustomerMessage(data.transcript, true);
    });

    // 채팅 메시지를 화면에 추가하는 함수
    function addChatMessage(sender, text) {
        const messageWrapper = document.createElement('div');
        const messageBubble = document.createElement('div');
        const messageParagraph = document.createElement('p');
        
        messageParagraph.innerHTML = text; // innerHTML을 사용하여 HTML 태그(예: <br>)를 렌더링

        if (sender === 'customer') {
            messageWrapper.className = 'flex items-end gap-3 customer-message-wrapper';
            messageBubble.className = 'bg-blue-600 text-white p-4 rounded-lg rounded-bl-none max-w-xl';
        } else { // AI
            messageWrapper.className = 'flex items-end justify-end gap-3';
            messageBubble.className = 'bg-gray-600 text-white p-4 rounded-lg rounded-br-none max-w-xl';
        }

        messageBubble.appendChild(messageParagraph);
        messageWrapper.appendChild(messageBubble);
        chatLog.appendChild(messageWrapper);
        
        // 스크롤을 맨 아래로 이동
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // 고객의 마지막 메시지를 업데이트하는 함수
    function updateLastCustomerMessage(transcript, isFinal = false) {
        let lastMessageWrapper = chatLog.querySelector('.customer-message-wrapper:last-of-type');
        
        if (!lastMessageWrapper || isFinal) {
            // 마지막 메시지가 없거나, 최종 결과물이면 새 메시지 추가
            addChatMessage('customer', transcript);
        } else {
            // 중간 결과물이면 마지막 메시지 내용 업데이트
            lastMessageWrapper.querySelector('p').textContent = transcript;
        }
        chatLog.scrollTop = chatLog.scrollHeight;
    }


    startStopBtn.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                // 오디오 컨텍스트 및 스트림 시작
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const source = audioContext.createMediaStreamSource(stream);

                await audioContext.audioWorklet.addModule('/static/js/audio-processor.js');
                processor = new AudioWorkletNode(audioContext, 'audio-processor');
                source.connect(processor);
                processor.connect(audioContext.destination);

                processor.port.onmessage = (event) => {
                    const audioData = event.data;
                    socket.emit('audio_stream', audioData);
                };

                // 녹음 시작 상태로 UI 업데이트
                isRecording = true;
                startStopBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-square"><rect width="18" height="18" x="3" y="3" rx="2"/></svg>
                    <span>Stop Meeting</span>`;
                startStopBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
                startStopBtn.classList.add('bg-red-600', 'hover:bg-red-700');
                statusDiv.textContent = 'Recording...';
                statusDiv.classList.add('text-red-400');
                
                socket.emit('start_session', { 
                    answer_style_id: answerStyleSelect.value,
                    sample_rate: audioContext.sampleRate
                });
                console.log('Recording started');

            } catch (error) {
                console.error('Error starting recording:', error);
                alert('Could not start recording. Please check microphone permissions.');
            }
        } else {
            // 녹음 중지
            if (processor) processor.port.postMessage({ command: 'stop' });
            if (audioContext) await audioContext.close();

            isRecording = false;
            startStopBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-mic"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
                <span>Start Meeting</span>`;
            startStopBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
            startStopBtn.classList.add('bg-green-600', 'hover:bg-green-700');
            statusDiv.textContent = 'Meeting Ended';
            statusDiv.classList.remove('text-red-400');
            
            socket.emit('stop_session');
            console.log('Recording stopped');
        }
    });

    // 답변 스타일 변경 시 서버에 알림
    answerStyleSelect.addEventListener('change', () => {
        if (isRecording) {
            socket.emit('change_style', { answer_style_id: answerStyleSelect.value });
            console.log('Answer style changed to:', answerStyleSelect.value);
        }
    });
});