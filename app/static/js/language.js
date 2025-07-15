document.addEventListener('DOMContentLoaded', () => {
  const languageSelector = document.getElementById('language-select');

  const setLanguage = (lang) => {
    // 1. data-key 속성을 가진 모든 HTML 요소를 찾습니다.
    const elements = document.querySelectorAll('[data-key]');
    
    // 2. 각 요소를 순회하며 텍스트를 선택된 언어의 번역문으로 교체합니다.
    elements.forEach(element => {
      const key = element.getAttribute('data-key');
      const translation = translations[lang][key];
      
      if (translation) {
        // 플레이스홀더와 일반 텍스트를 구분하여 처리합니다.
        if (element.placeholder !== undefined) {
          element.placeholder = translation;
        } else {
          element.textContent = translation;
        }
      }
    });

    // 3. 사용자의 언어 선택을 브라우저에 저장하여 다음에 방문할 때도 기억하게 합니다.
    localStorage.setItem('language', lang);
    if(languageSelector) {
        languageSelector.value = lang;
    }
  };

  if (languageSelector) {
    // 4. 언어 선택 드롭다운에 이벤트 리스너를 추가합니다.
    languageSelector.addEventListener('change', (event) => {
      setLanguage(event.target.value);
    });
  }

  // 5. 페이지가 로드될 때, 저장된 언어 설정을 불러오거나 기본값(영어)으로 설정합니다.
  const savedLang = localStorage.getItem('language') || 'en';
  setLanguage(savedLang);

  // 전역적으로 사용할 수 있도록 함수를 window 객체에 할당 (필요 시)
  window.setLanguage = setLanguage;
  window.getSavedLanguage = () => localStorage.getItem('language') || 'en';
});

// index.html의 새 미팅 생성 버튼 로직 수정
const newMeetingBtn = document.getElementById('new-meeting-btn');
if (newMeetingBtn) {
    newMeetingBtn.addEventListener('click', () => {
        // 백엔드에 보낼 언어 코드는 Google STT가 요구하는 형식이어야 함
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
            window.location.href = `/meeting/${data.meeting_id}`;
        })
        .catch(error => console.error('Error:', error));
    });
}
