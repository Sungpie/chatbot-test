import os
import sys
import json
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Optional
from datetime import datetime
import requests

# .env 파일 로드
load_dotenv()

class PlaceRecommendationBot:
    """장소 추천을 위한 JSON 응답 챗봇"""
    
    def __init__(self, api_key: str, kakao_api_key: str = None):
        """
        챗봇 초기화
        
        Args:
            api_key: Google Gemini API 키
            kakao_api_key: 카카오맵 API 키 (선택사항)
        """
        genai.configure(api_key=api_key)
        
        # JSON 응답을 위한 시스템 프롬프트
        self.system_prompt = """
        당신은 장소 추천 전문가입니다. 사용자의 요청에 따라 장소를 추천해야 합니다.
        서울시 구로구에 있는 장소들로 제한됩니다. 반드시 서울시 구로구 범위에 있는 장소들로 추천하세요.
        반드시 다음과 같은 JSON 형식으로만 응답해야 합니다:
        
        {
            "places": [
                {
                    "id": "unique_id_string",
                    "name": "장소명",
                    "description": "장소에 대한 상세 설명",
                    "address": "전체 주소",
                    "latitude": 37.123456,
                    "longitude": 126.123456
                }
            ],
            "total_count": 3,
            "query_info": {
                "location": "요청 지역",
                "type": "요청 유형"
            }
        }
        
        중요 규칙:
        1. 반드시 유효한 JSON 형식으로만 응답하세요
        2. 실제 존재하는 장소만 추천하세요
        3. 주소는 가능한 한 상세하게 제공하세요
        4. 위도(latitude)와 경도(longitude)는 실제 좌표를 제공하세요
        5. 설명은 100자 이내로 간결하게 작성하세요
        6. id는 "place_1", "place_2" 형식으로 생성하세요
        7. JSON 외의 다른 텍스트는 절대 포함하지 마세요
        """
        
        # Generation Config 설정 (JSON 모드)
        generation_config = genai.types.GenerationConfig(
            temperature=0.3,  # 더 정확한 응답을 위해 낮은 temperature
            max_output_tokens=2000,
            response_mime_type="application/json"  # JSON 응답 강제
        )
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
            system_instruction=self.system_prompt
        )
        
        self.kakao_api_key = kakao_api_key
        self.chat = None
        self.history = []
    
    def start_chat(self):
        """새로운 채팅 세션 시작"""
        self.chat = self.model.start_chat(history=[])
        print("💬 장소 추천 챗봇이 시작되었습니다.")
        print("📍 JSON 형식으로 응답합니다.")
    
    def get_coordinates_from_kakao(self, address: str) -> tuple:
        """
        카카오맵 API를 사용하여 주소로부터 좌표 획득
        
        Args:
            address: 검색할 주소
            
        Returns:
            (latitude, longitude) 튜플 또는 (None, None)
        """
        if not self.kakao_api_key:
            return None, None
        
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {self.kakao_api_key}"}
        params = {"query": address}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["documents"]:
                    doc = data["documents"][0]
                    return float(doc["y"]), float(doc["x"])  # 위도, 경도
        except Exception as e:
            print(f"카카오맵 API 오류: {e}")
        
        return None, None
    
    def recommend_places(self, user_query: str) -> Dict:
        """
        사용자 쿼리를 받아 장소 추천
        
        Args:
            user_query: 사용자의 장소 추천 요청
            
        Returns:
            JSON 형식의 추천 결과
        """
        if self.chat is None:
            self.start_chat()
        
        try:
            # Gemini에게 요청
            response = self.chat.send_message(user_query)
            
            # JSON 파싱 시도
            try:
                result = json.loads(response.text)
                
                # 카카오맵 API로 좌표 보완 (필요시)
                if self.kakao_api_key:
                    for place in result.get("places", []):
                        # 좌표가 없거나 0인 경우 카카오맵 API 사용
                        if not place.get("latitude") or not place.get("longitude"):
                            lat, lng = self.get_coordinates_from_kakao(place.get("address", ""))
                            if lat and lng:
                                place["latitude"] = lat
                                place["longitude"] = lng
                                place["coordinate_source"] = "kakao_map"
                            else:
                                place["coordinate_source"] = "not_found"
                        else:
                            place["coordinate_source"] = "gemini"
                
                # 대화 기록 저장
                self.history.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": user_query,
                    "response": result
                })
                
                return result
                
            except json.JSONDecodeError:
                # JSON 파싱 실패시 에러 메시지 반환
                return {
                    "error": "JSON 파싱 실패",
                    "raw_response": response.text,
                    "message": "응답이 올바른 JSON 형식이 아닙니다"
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "message": "추천 생성 중 오류가 발생했습니다"
            }
    
    def save_history(self, filename: str = None):
        """대화 기록 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"place_recommendations_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        print(f"✅ 추천 기록이 {filename}에 저장되었습니다.")


class PlaceRecommendationBotV2:
    """프롬프트 엔지니어링을 통한 JSON 응답 챗봇 (대안)"""
    
    def __init__(self, api_key: str, kakao_api_key: str = None):
        """
        챗봇 초기화 - 프롬프트로 JSON 출력 유도
        
        Args:
            api_key: Google Gemini API 키
            kakao_api_key: 카카오맵 API 키 (선택사항)
        """
        genai.configure(api_key=api_key)
        
        # 일반 설정 (response_mime_type 없이)
        generation_config = genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=2000
        )
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config
        )
        
        self.kakao_api_key = kakao_api_key
        self.chat = None
        self.history = []
    
    def start_chat(self):
        """새로운 채팅 세션 시작"""
        self.chat = self.model.start_chat(history=[])
        print("💬 장소 추천 챗봇 V2가 시작되었습니다.")
    
    def recommend_places(self, user_query: str) -> Dict:
        """
        프롬프트 엔지니어링으로 JSON 응답 유도
        
        Args:
            user_query: 사용자의 장소 추천 요청
            
        Returns:
            JSON 형식의 추천 결과
        """
        if self.chat is None:
            self.start_chat()
        
        # JSON 출력을 강제하는 프롬프트
        enhanced_prompt = f"""
        다음 요청에 대해 장소를 추천하고, 반드시 아래 형식의 JSON으로만 응답하세요.
        다른 설명이나 텍스트는 절대 포함하지 마세요. 오직 JSON만 출력하세요.
        
        요청: {user_query}
        
        응답 형식:
        {{
            "places": [
                {{
                    "id": "place_1",
                    "name": "장소명",
                    "description": "장소 설명 (100자 이내)",
                    "address": "전체 주소",
                    "latitude": 37.123456,
                    "longitude": 126.123456
                }}
            ],
            "total_count": 추천 개수,
            "query_info": {{
                "location": "요청 지역",
                "type": "요청 유형"
            }}
        }}
        
        규칙:
        1. 실제 존재하는 장소만 추천
        2. 위도와 경도는 실제 좌표 제공 (모르면 null)
        3. 오직 JSON만 출력, 다른 텍스트 금지
        """
        
        try:
            response = self.chat.send_message(enhanced_prompt)
            
            # 응답에서 JSON 부분만 추출
            text = response.text.strip()
            
            # 마크다운 코드 블록 제거 (```json ... ```)
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            
            # JSON 파싱
            try:
                result = json.loads(text)
                
                # 대화 기록 저장
                self.history.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": user_query,
                    "response": result
                })
                
                return result
                
            except json.JSONDecodeError as e:
                # JSON 파싱 실패시 디버깅 정보 포함
                return {
                    "error": "JSON 파싱 실패",
                    "parse_error": str(e),
                    "raw_response": text[:500],  # 처음 500자만
                    "message": "응답을 JSON으로 변환할 수 없습니다"
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "message": "추천 생성 중 오류가 발생했습니다"
            }


def main():
    """메인 실행 함수"""
    
    # 환경 변수에서 API 키 로드
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    kakao_api_key = os.getenv("KAKAO_API_KEY")  # 선택사항
    
    if not gemini_api_key or gemini_api_key == "your-api-key-here":
        print("⚠️  Gemini API 키를 설정해주세요!")
        print("📝 .env 파일에 GEMINI_API_KEY를 설정하세요")
        return
    
    print("\n🤖 장소 추천 챗봇을 시작합니다...")
    print("=" * 50)
    
    # 버전 선택
    print("\n어떤 버전을 사용하시겠습니까?")
    print("1. V1 - JSON 응답 모드 사용 (권장)")
    print("2. V2 - 프롬프트 엔지니어링 사용")
    
    choice = input("\n선택 (1 또는 2): ").strip()
    
    if choice == "1":
        bot = PlaceRecommendationBot(gemini_api_key, kakao_api_key)
    else:
        bot = PlaceRecommendationBotV2(gemini_api_key, kakao_api_key)
    
    bot.start_chat()
    
    if kakao_api_key:
        print("✅ 카카오맵 API 연동됨 (좌표 정확도 향상)")
    else:
        print("ℹ️  카카오맵 API 미연동 (Gemini 좌표만 사용)")
    
    print("\n사용 예시:")
    print('  "서울시 구로구에 있는 맛집을 세 곳 추천해줘"')
    print('  "강남역 근처 카페 5곳 알려줘"')
    print('  "부산 해운대 관광지 추천해줘"')
    print("\n명령어:")
    print("  /save - 추천 기록 저장")
    print("  /history - 추천 기록 보기")
    print("  /exit - 종료")
    print("=" * 50)
    
    while True:
        user_input = input("\n📍 질문: ").strip()
        
        if user_input.lower() == '/exit':
            print("👋 종료합니다.")
            break
        
        elif user_input.lower() == '/save':
            bot.save_history()
            continue
        
        elif user_input.lower() == '/history':
            if bot.history:
                print("\n📜 추천 기록:")
                for i, record in enumerate(bot.history, 1):
                    print(f"\n[{i}] {record['timestamp']}")
                    print(f"질문: {record['query']}")
                    print(f"추천 장소 수: {record['response'].get('total_count', 'N/A')}")
            else:
                print("기록이 없습니다.")
            continue
        
        if not user_input:
            continue
        
        # 장소 추천 실행
        print("\n🔍 추천 중...")
        result = bot.recommend_places(user_input)
        
        # 결과 출력
        print("\n📋 JSON 응답:")
        print("-" * 50)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("-" * 50)
        
        # 결과 요약 (성공시)
        if "places" in result:
            print(f"\n✅ {len(result['places'])}개 장소 추천 완료")
            for place in result['places']:
                coord_info = ""
                if place.get("latitude") and place.get("longitude"):
                    coord_info = f"📍 {place['latitude']:.6f}, {place['longitude']:.6f}"
                    if place.get("coordinate_source"):
                        coord_info += f" (출처: {place['coordinate_source']})"
                
                print(f"\n• {place['name']}")
                print(f"  {place['description']}")
                print(f"  주소: {place['address']}")
                if coord_info:
                    print(f"  {coord_info}")
        elif "error" in result:
            print(f"\n❌ 오류: {result['error']}")


if __name__ == "__main__":
    main()