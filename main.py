import os
import google.generativeai as genai
from typing import List, Dict
import json
from datetime import datetime

class GeminiChatbot:
    """Google Gemini API를 사용한 간단한 챗봇 클래스"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-lite"):
        """
        챗봇 초기화
        
        Args:
            api_key: Google AI Studio에서 발급받은 API 키
            model_name: 사용할 Gemini 모델 이름 (기본값: gemini-pro)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.chat = None
        self.history = []
        
    def start_chat(self):
        """새로운 채팅 세션 시작"""
        self.chat = self.model.start_chat(history=[])
        self.history = []
        print("💬 새로운 채팅 세션이 시작되었습니다.")
        
    def send_message(self, message: str) -> str:
        """
        메시지를 보내고 응답 받기
        
        Args:
            message: 사용자 입력 메시지
            
        Returns:
            Gemini의 응답 텍스트
        """
        if self.chat is None:
            self.start_chat()
            
        try:
            response = self.chat.send_message(message)
            
            # 대화 기록 저장
            self.history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            self.history.append({
                "role": "assistant",
                "content": response.text,
                "timestamp": datetime.now().isoformat()
            })
            
            return response.text
            
        except Exception as e:
            return f"오류 발생: {str(e)}"
    
    def get_history(self) -> List[Dict]:
        """대화 기록 반환"""
        return self.history
    
    def save_history(self, filename: str = "chat_history.json"):
        """
        대화 기록을 파일로 저장
        
        Args:
            filename: 저장할 파일명
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        print(f"✅ 대화 기록이 {filename}에 저장되었습니다.")
    
    def load_history(self, filename: str = "chat_history.json"):
        """
        저장된 대화 기록 불러오기
        
        Args:
            filename: 불러올 파일명
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
            print(f"✅ {filename}에서 대화 기록을 불러왔습니다.")
        except FileNotFoundError:
            print(f"⚠️  {filename} 파일을 찾을 수 없습니다.")
    
    def clear_history(self):
        """대화 기록 초기화"""
        self.history = []
        self.start_chat()
        print("🗑️  대화 기록이 초기화되었습니다.")


def main():
    """메인 실행 함수"""
    
    # API 키 설정 (환경 변수에서 가져오기)
    # API_KEY = os.getenv("GEMINI_API_KEY")
    API_KEY = os.getenv("GEMINI_API_KEY")  # 여기에 실제 API 키를 입력하세요
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️  API 키를 설정해주세요!")
        print("Google AI Studio에서 API 키를 발급받으세요:")
        print("https://makersuite.google.com/app/apikey")
        return
    
    # 챗봇 인스턴스 생성
    chatbot = GeminiChatbot(api_key=API_KEY)
    
    # 채팅 시작
    chatbot.start_chat()
    
    print("\n🤖 Gemini 챗봇이 준비되었습니다!")
    print("명령어:")
    print("  /history - 대화 기록 보기")
    print("  /save - 대화 기록 저장")
    print("  /load - 대화 기록 불러오기")
    print("  /clear - 대화 기록 초기화")
    print("  /exit 또는 /quit - 종료")
    print("-" * 50)
    
    while True:
        # 사용자 입력 받기
        user_input = input("\n👤 You: ").strip()
        
        # 명령어 처리
        if user_input.lower() in ['/exit', '/quit']:
            print("👋 채팅을 종료합니다. 안녕히 가세요!")
            break
            
        elif user_input.lower() == '/history':
            history = chatbot.get_history()
            if history:
                print("\n📜 대화 기록:")
                for item in history:
                    role = "👤 User" if item["role"] == "user" else "🤖 Gemini"
                    print(f"\n[{item['timestamp']}] {role}:")
                    print(f"{item['content'][:100]}..." if len(item['content']) > 100 else item['content'])
            else:
                print("대화 기록이 없습니다.")
            continue
            
        elif user_input.lower() == '/save':
            chatbot.save_history()
            continue
            
        elif user_input.lower() == '/load':
            chatbot.load_history()
            continue
            
        elif user_input.lower() == '/clear':
            chatbot.clear_history()
            continue
        
        # 빈 입력 처리
        if not user_input:
            print("⚠️  메시지를 입력해주세요.")
            continue
        
        # Gemini에게 메시지 전송 및 응답 받기
        print("\n🤖 Gemini: ", end="")
        response = chatbot.send_message(user_input)
        print(response)


# 고급 기능을 포함한 확장 버전
class AdvancedGeminiChatbot(GeminiChatbot):
    """고급 기능이 추가된 Gemini 챗봇"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-lite"):
        super().__init__(api_key, model_name)
        self.system_prompt = None
        self.temperature = 0.7
        self.max_tokens = None
        
    def set_system_prompt(self, prompt: str):
        """
        시스템 프롬프트 설정 (챗봇의 성격이나 역할 정의)
        
        Args:
            prompt: 시스템 프롬프트 텍스트
        """
        self.system_prompt = prompt
        print(f"✅ 시스템 프롬프트가 설정되었습니다.")
        
    def configure_generation(self, temperature: float = 0.7, max_tokens: int = None):
        """
        생성 파라미터 설정
        
        Args:
            temperature: 창의성 정도 (0.0 ~ 1.0)
            max_tokens: 최대 토큰 수
        """
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 새로운 설정으로 모델 재구성
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        self.model = genai.GenerativeModel(
            model_name=self.model.model_name,
            generation_config=generation_config
        )
        print(f"✅ 생성 설정이 업데이트되었습니다 (온도: {temperature}, 최대 토큰: {max_tokens})")
    
    def send_message_with_context(self, message: str, context: str = None) -> str:
        """
        컨텍스트와 함께 메시지 전송
        
        Args:
            message: 사용자 메시지
            context: 추가 컨텍스트
            
        Returns:
            Gemini의 응답
        """
        full_message = message
        
        if self.system_prompt:
            full_message = f"System: {self.system_prompt}\n\n{message}"
        
        if context:
            full_message = f"Context: {context}\n\n{full_message}"
            
        return self.send_message(full_message)


if __name__ == "__main__":
    main()