# Gemini Chatbot

Google Gemini API를 사용한 Python 챗봇입니다.

## 설치 방법

1. 저장소 클론

```bash
git clone https://github.com/yourusername/gemini-chatbot.git
```

2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

4. 환경 변수 설정

```bash
cp .env.example .env
```

그 다음 `.env` 파일을 열어 실제 API 키를 입력하세요.

5. API 키 발급

- [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키 발급
- `.env` 파일에 발급받은 키 입력

## 사용 방법

```bash
python chatbot.py
```

## 주의사항

- `.env` 파일은 절대 Git에 커밋하지 마세요
- API 키는 안전하게 관리하세요
