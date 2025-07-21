document.addEventListener('DOMContentLoaded', () => {
  const languageSelector = document.getElementById('language-select');

  // 언어 설정 함수
  const setLanguage = (lang) => {
    // data-key 속성을 가진 모든 HTML 요소를 찾습니다.
    const elements = document.querySelectorAll('[data-key]');
    
    elements.forEach(element => {
      const key = element.getAttribute('data-key');
      // translations 객체는 translations.js 파일에 정의되어 있습니다.
      const translation = translations[lang]?.[key];
      
      if (translation) {
        if (element.placeholder !== undefined) {
          element.placeholder = translation;
        } else {
          element.textContent = translation;
        }
      }
    });

    // 사용자의 언어 선택을 브라우저에 저장
    localStorage.setItem('language', lang);
    if(languageSelector) {
        languageSelector.value = lang;
    }
  };

  if (languageSelector) {
    languageSelector.addEventListener('change', (event) => {
      setLanguage(event.target.value);
    });
  }

  // 저장된 언어 설정을 불러오거나 기본값(영어)으로 설정
  const savedLang = localStorage.getItem('language') || 'en';
  setLanguage(savedLang);

  // 전역 함수로 할당
  window.setLanguage = setLanguage;
  window.getSavedLanguage = () => localStorage.getItem('language') || 'en';

  // --- 문제 해결 부분 ---
  // 새 미팅 생성 버튼 로직을 DOMContentLoaded 안으로 이동
  const newMeetingBtn = document.getElementById('new-meeting-btn');
  if (newMeetingBtn) {
      newMeetingBtn.addEventListener('click', () => {
          const selectedLanguage = localStorage.getItem('language') || 'en';
          const languageCodeMap = {
              en: 'en-US',
              es: 'es-ES',
              ko: 'ko-KR'
          };
          const backendLanguageCode = languageCodeMap[selectedLanguage];

          fetch('/api/meeting/create', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ language: backendLanguageCode })
          })
          .then(response => response.json())
          .then(data => {
              if (data.meeting_id) {
                  window.location.href = `/meeting/${data.meeting_id}`;
              } else {
                  console.error('Failed to create meeting:', data);
                  alert('Error: Could not create a new meeting.');
              }
          })
          .catch(error => {
              console.error('Error:', error);
              alert('An error occurred while creating the meeting.');
          });
      });
  }
});
