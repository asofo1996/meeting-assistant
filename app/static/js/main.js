document.addEventListener('DOMContentLoaded', () => {
    // --- DOM 요소 가져오기 ---
    const startStopBtn = document.getElementById('startStopBtn');
    const statusDiv = document.getElementById('status');
    const transcriptDiv = document.getElementById('transcript');
    const aiResponseDiv = document.getElementById('aiResponse');
    const answerStyleSelect = document.getElementById('answerStyle');

    // --- 전역 변수 설정 ---
    let socket;
    let isRecording = false;
    let audioContext;
    let processor;
    let input;
    let globalStream;

    // --- 오디오 제약 조건 ---
    const constraints = { audio: true, video: false };

    /**
     * 상태 메시지를 UI에 업데이트하는 함수
     * @param {string} message - 표시할 메시지
     * @param {boolean} isError - 오류 메시지 여부
     */
    function updateStatus(message, isError = false) {
        statusDiv.textContent = message;
        statusDiv.className = isError ? 'error' : 'info';
    }

    /**
     * 서버와의 웹소켓 연결을 설정하고 이벤트 핸들러를 등록하는 함수
     */
    function connectSocket() {
        // 현재 위치를 기준으로 소켓에 연결합니다.
        socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

        socket.on('connect', () => {
            console.log("Socket connected!");
            updateStatus('Ready to start');
        });

        socket.on('disconnect', () => {
            console.log("Socket disconnected!");
            updateStatus('Disconnected', true);
            // 연결이 끊겼을 때 녹음 중이었다면 중지 처리
            if (isRecording) {
                stopRecording();
            }
        });

        // 중간 음성 인식 결과 수신
        socket.on('interim_transcript', (data) => {
            // 최종 결과가 표시되기 전까지 임시 결과를 보여줌
            const finalTranscriptElement = transcriptDiv.querySelector('.final');
            if (!finalTranscriptElement || finalTranscriptElement.textContent.includes('You:')) {
                 let tempP = transcriptDiv.querySelector('.interim');
                 if (!tempP) {
                     tempP = document.createElement('p');
                     tempP.className = 'interim';
                     transcriptDiv.appendChild(tempP);
                 }
                 tempP.textContent = `You: ${data.transcript}...`;
                 transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
            }
        });

        // 최종 음성 인식 결과 수신
        socket.on('final_transcript', (data) => {
            // 임시 결과를 지우고 최종 결과를 표시
            const tempP = transcriptDiv.querySelector('.interim');
            if (tempP) {
                tempP.remove();
            }
            
            const p = document.createElement('p');
            p.className = 'final';
            p.textContent = `You: ${data.transcript}`;
            transcriptDiv.appendChild(p);
            transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
        });

        // AI 응답 수신
        socket.on('ai_response', (data) => {
            const p = document.createElement('p');
            p.innerHTML = `<strong>AI:</strong> ${data.text}`;
            aiResponseDiv.appendChild(p);
            aiResponseDiv.scrollTop = aiResponseDiv.scrollHeight;
        });
    }

    /**
     * 로컬 오디오 스트림을 중지하고 관련 리소스를 해제하는 함수
     */
    function stopRecording() {
        if (!isRecording) return;

        if (globalStream) {
            globalStream.getTracks().forEach(track => track.stop());
        }
        if (audioContext && audioContext.state !== 'closed') {
            audioContext.close();
        }
        if (processor) {
            processor.disconnect();
        }
        if (input) {
            input.disconnect();
        }

        if (socket && socket.connected) {
            socket.emit('stop_session');
        }

        isRecording = false;
        startStopBtn.textContent = 'Start Listening';
        updateStatus('Stopped');
    }

    // --- 시작/중지 버튼 이벤트 리스너 ---
    startStopBtn.addEventListener('click', async () => {
        if (isRecording) {
            // 녹음 중일 경우 중지
            stopRecording();
        } else {
            // 녹음 시작
            if (!socket || !socket.connected) {
                updateStatus('Connecting...', true);
                connectSocket(); // 연결이 끊겼을 경우 재연결 시도
                return;
            }

            try {
                // 1. 마이크 권한을 얻고 오디오 스트림을 가져옴
                globalStream = await navigator.mediaDevices.getUserMedia(constraints);
                
                // 2. AudioContext 및 AudioWorklet 설정
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                await audioContext.audioWorklet.addModule('/static/js/audio-processor.js');

                // 3. 서버로 세션 시작 이벤트 전송 (MEETING_ID 포함)
                // 이 시점에서는 audioContext.sampleRate를 정확히 알 수 있음
                socket.emit('start_session', {
                    meeting_id: MEETING_ID, // meeting.html에서 정의된 전역 변수
                    answer_style_id: answerStyleSelect.value,
                    sample_rate: audioContext.sampleRate
                });

                console.log(`Session started for meeting ${MEETING_ID} with sample rate ${audioContext.sampleRate}`);
                
                // 4. 오디오 처리 노드 생성 및 연결
                input = audioContext.createMediaStreamSource(globalStream);
                processor = new AudioWorkletNode(audioContext, 'audio-processor');

                // 5. 오디오 프로세서에서 처리된 데이터를 서버로 전송
                processor.port.onmessage = (event) => {
                    const audioData = event.data;
                    if (socket && socket.connected) {
                        socket.emit('audio_stream', audioData);
                    }
                };

                input.connect(processor);
                processor.connect(audioContext.destination);

                // 6. 상태 업데이트
                isRecording = true;
                startStopBtn.textContent = 'Stop Listening';
                updateStatus('Listening...');

            } catch (error) {
                console.error('Error starting recording:', error);
                updateStatus('Error: Could not start. Check mic permissions.', true);
                // 에러 발생 시 리소스 정리
                if (globalStream) {
                    globalStream.getTracks().forEach(track => track.stop());
                }
                if (audioContext && audioContext.state !== 'closed') {
                    audioContext.close();
                }
            }
        }
    });

    // --- 초기화 ---
    // 페이지 로드 시 소켓 연결 실행
    connectSocket();
});