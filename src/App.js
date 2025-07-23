// src/App.js (주요 로직 예시)
import React, { useState, useEffect } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { supabase } from './supabaseClient';

function App() {
  const [history, setHistory] = useState([]);
  const { transcript, listening, resetTranscript } = useSpeechRecognition();

  // 1. 과거 이력 불러오기
  useEffect(() => {
    const fetchHistory = async () => {
      const { data, error } = await supabase.from('meetings').select('*').order('created_at');
      if (error) console.error('Error fetching history:', error);
      else setHistory(data);
    };
    fetchHistory();

    // 2. 실시간 변경 감지 및 자동 업데이트
    const subscription = supabase
      .channel('meetings')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'meetings' }, (payload) => {
        // 새 데이터가 추가되면 history 상태를 업데이트하여 화면을 다시 그립니다.
        setHistory(currentHistory => [...currentHistory, payload.new]);
      })
      .subscribe();

    return () => {
      supabase.removeChannel(subscription);
    };
  }, []);

  // 3. 음성인식 텍스트 저장 함수
  const handleSaveTranscript = async () => {
    if (!transcript) return;

    // 여기에 AI 답변 생성 및 파일 저장 로직 추가 (4단계 참고)
    const aiSolution = `AI가 생성한 답변 예시: ${transcript}`; 

    const { data, error } = await supabase
      .from('meetings')
      .insert([{ transcribed_text: transcript, ai_response: aiSolution }])
      .select();

    if (error) {
      console.error('Error saving transcript:', error);
    } else {
      console.log('Saved successfully:', data);
      resetTranscript();
    }
  };

  return (
    <div>
      <h1>Meeting Assistant</h1>
      <p>Microphone: {listening ? 'on' : 'off'}</p>
      <button onClick={() => SpeechRecognition.startListening({ continuous: true })}>Start</button>
      <button onClick={SpeechRecognition.stopListening}>Stop</button>
      <button onClick={handleSaveTranscript}>Save Transcript</button>
      <p>{transcript}</p>

      <h2>History</h2>
      <table>
        <thead>
          <tr>
            <th>Transcribed Text</th>
            <th>AI Solution</th>
          </tr>
        </thead>
        <tbody>
          {history.map((item) => (
            <tr key={item.id}>
              <td>{item.transcribed_text}</td>
              <td>{item.ai_response}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;