import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from main import PlaceRecommendationBot # 기존 main.py에서 클래스를 가져옵니다.

# .env 파일 로드
load_dotenv()

# Flask 앱 생성
app = Flask(__name__)

# Gemini API 키 확인
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key or gemini_api_key == "your-api-key-here":
    raise ValueError("Gemini API 키를 .env 파일에 설정해주세요!")

# 챗봇 인스턴스 생성 (카카오 API 키는 선택사항)
kakao_api_key = os.getenv("KAKAO_API_KEY")
bot = PlaceRecommendationBot(api_key=gemini_api_key, kakao_api_key=kakao_api_key)


# --- 백엔드와의 소통을 위한 핵심 로직 ---
@app.route('/api/recommend', methods=['POST'])
def recommend():
    # 1. 백엔드로부터 정해진 형식의 JSON 데이터를 받습니다.
    backend_request_data = request.get_json()

    # 필수 값들이 있는지 확인합니다.
    if not all(key in backend_request_data for key in ["place", "mood", "purpose"]):
        return jsonify({
            "statusCode": 400, # Bad Request
            "message": "요청 형식이 잘못되었습니다. 'place', 'mood', 'purpose'를 모두 포함해야 합니다.",
            "data": None
        }), 400

    # 2. 받은 데이터로 Gemini에게 보낼 자연어 질문을 생성합니다. (매우 중요!)
    place = backend_request_data.get("place")
    mood = backend_request_data.get("mood")
    purpose = backend_request_data.get("purpose")
    
    # 예시: "서울시 구로구에서 조용한 분위기의 데이트 목적에 맞는 장소를 추천해줘"
    user_query = f"{place}에서 {mood} 분위기의 {purpose} 목적에 맞는 장소를 추천해줘"
    print(f"Gemini에게 보낼 질문: {user_query}")

    # 3. 기존에 만들어둔 챗봇의 핵심 기능을 호출하여 장소를 추천받습니다.
    gemini_response = bot.recommend_places(user_query)

    # 4. Gemini의 응답을 백엔드가 원하는 최종 형식으로 '포장'합니다.
    if "error" in gemini_response:
        # Gemini API 호출 중 에러가 발생했을 경우
        final_response = {
            "statusCode": 500, # Internal Server Error
            "message": gemini_response.get("message", "장소 추천 중 오류가 발생했습니다."),
            "data": gemini_response # 에러의 상세 내용을 data에 포함
        }
        return jsonify(final_response), 500
    else:
        # 성공적으로 추천 받았을 경우
        final_response = {
            "statusCode": 200, # OK
            "message": "장소 추천에 성공했습니다.",
            "data": gemini_response # Gemini가 준 결과(places, total_count 등)를 data 필드에 넣습니다.
        }
        return jsonify(final_response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))