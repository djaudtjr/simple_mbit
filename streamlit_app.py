import streamlit as st
import openai
from openai import OpenAI
import json
import urllib.parse

# 페이지 설정
st.set_page_config(
    page_title="🧠 Simple MBTI 성격 테스트",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일 및 Kakao SDK
st.markdown("""
<script src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js"
        integrity="sha384-TiCUE00h649CAMonG018J2ujOgDKW/kVWlChEuu4jK2vxfAAD0eZxzCKakxg55G4" 
        crossorigin="anonymous"></script>
<script>
    // 카카오 SDK 초기화 (동적으로 키 설정)
    function initKakaoWithKey(apiKey) {
        if (typeof Kakao !== 'undefined' && apiKey && !Kakao.isInitialized()) {
            try {
                Kakao.init(apiKey);
                console.log('Kakao SDK 초기화 완료:', apiKey.substring(0, 10) + '...');
                return true;
            } catch (error) {
                console.error('Kakao SDK 초기화 실패:', error);
                return false;
            }
        }
        return false;
    }
    
    // 카카오톡 공유 함수
    function shareKakao(title, description, imageUrl, webUrl) {
        if (typeof Kakao === 'undefined') {
            alert('카카오 SDK를 불러올 수 없습니다. 다른 공유 방법을 이용해주세요.');
            return false;
        }
        
        if (!Kakao.isInitialized()) {
            alert('카카오 앱 키가 설정되지 않았습니다. 관리자에게 문의하세요.');
            return false;
        }
        
        Kakao.Share.sendDefault({
            objectType: 'feed',
            content: {
                title: title,
                description: description,
                imageUrl: imageUrl || 'https://developers.kakao.com/assets/img/about/logos/kakaolink/kakaolink_btn_medium.png',
                link: {
                    mobileWebUrl: webUrl,
                    webUrl: webUrl,
                },
            },
            buttons: [
                {
                    title: '테스트 하기',
                    link: {
                        mobileWebUrl: webUrl,
                        webUrl: webUrl,
                    },
                },
            ],
            // 카카오톡 미설치 시 카카오톡 설치 경로이동
            installTalk: true,
        });
        return true;
    }
    
    // Streamlit과 JavaScript 간의 통신을 위한 함수
    function initKakaoShare() {
        window.shareToKakao = shareKakao;
    }
    
    // DOM 로드 완료 후 초기화
    document.addEventListener('DOMContentLoaded', initKakaoShare);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initKakaoShare);
    } else {
        initKakaoShare();
    }
</script>
<style>
    .main {
        padding-top: 2rem;
    }

    .stTitle {
        text-align: center;
        color: #2E86AB;
        font-size: 3rem;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    .question-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        text-align: center;
    }

    .result-container {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 15px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        text-align: center;
    }

    .progress-bar {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        height: 20px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 15px 30px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
        margin: 10px 0;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }

    .welcome-message {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(168, 237, 234, 0.3);
        color: #2c3e50;
        font-weight: 500;
        line-height: 1.6;
    }

    .welcome-message h2 {
        color: #2c3e50;
        font-weight: bold;
        margin-bottom: 15px;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    }

    .welcome-message h3 {
        color: #34495e;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    }

    .welcome-message p {
        color: #2c3e50;
        font-size: 1.1rem;
        margin-bottom: 10px;
        text-shadow: 0.5px 0.5px 1px rgba(255,255,255,0.8);
    }

    .mbti-result {
        font-size: 3rem;
        font-weight: bold;
        color: #2E86AB;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

def generate_all_questions(client, question_count=8):
    """OpenAI API를 사용하여 지정된 개수의 MBTI 질문을 한번에 생성"""

    questions_per_dimension = question_count // 4

    prompt = f"""
    MBTI 성격 테스트를 위한 {question_count}개의 질문을 생성해주세요. 각 MBTI 차원별로 {questions_per_dimension}개씩 균형있게 배치해주세요:

    - E/I (외향성/내향성): {questions_per_dimension}개 질문
    - S/N (감각/직관): {questions_per_dimension}개 질문
    - T/F (사고/감정): {questions_per_dimension}개 질문
    - J/P (판단/인식): {questions_per_dimension}개 질문

    각 질문은 일상적이고 구체적인 상황을 제시하여 두 개의 선택지로 답할 수 있도록 만들어주세요.
    모든 질문은 서로 다른 상황과 맥락을 다루어야 하며, 중복되지 않아야 합니다.

    반드시 아래 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요:
    {{
        "questions": [
            {{
                "question": "질문 내용",
                "type": "E/I",
                "options": [
                    {{"text": "첫 번째 선택지", "type": "E"}},
                    {{"text": "두 번째 선택지", "type": "I"}}
                ]
            }}
        ]
    }}

    한국어로 작성해주세요.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 MBTI 전문가입니다. 정확하고 균형잡힌 8개의 MBTI 질문을 생성해주세요. 각 차원별로 2개씩, 총 8개의 서로 다른 질문을 만들어주세요. 반드시 올바른 JSON 형식으로만 응답하고, 다른 설명이나 텍스트는 포함하지 마세요."
                                   "질문의 어휘는 감성적인 표현으로 하고 창의적이고 다양한 생각을 하지만 구체적인 상황을 제시하여 두 개의 선택지로 답할 수 있도록 만들어주세요."
                                   "질문은 서로 다른 상황과 맥락을 다루어야 하며, 중복되지 않아야 합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8
            )

            # JSON 응답 파싱
            response_content = response.choices[0].message.content.strip()
            st.write(f"🔍 API 응답 내용: {response_content[:200]}...")  # 디버깅용

            # JSON 파싱 시도
            try:
                questions_data = json.loads(response_content)
                questions = questions_data["questions"]
                st.success(f"✅ {len(questions)}개 질문 생성 성공!")
            except json.JSONDecodeError as json_err:
                st.error(f"❌ JSON 파싱 오류: {str(json_err)}")
                st.write(f"응답 내용: {response_content}")
                continue

            # 지정된 개수의 질문이 제대로 생성되었는지 확인
            if len(questions) == question_count:
                # 각 차원별로 균등하게 있는지 확인
                type_counts = {"E/I": 0, "S/N": 0, "T/F": 0, "J/P": 0}
                for q in questions:
                    if q.get("type") in type_counts:
                        type_counts[q["type"]] += 1

                # 모든 차원이 균등하게 있으면 성공
                if all(count == questions_per_dimension for count in type_counts.values()):
                    st.success(f"🎯 균형잡힌 질문 생성 완료! {type_counts}")
                    return questions
                else:
                    st.warning(f"⚠️ 질문 분포가 불균형합니다: {type_counts}")
            else:
                st.warning(f"⚠️ {len(questions)}개 질문만 생성됨 ({question_count}개 필요)")

            # 조건에 맞지 않으면 재시도
            if attempt < max_retries - 1:
                st.info(f"🔄 재시도 중... ({attempt + 1}/{max_retries})")
                continue

        except openai.AuthenticationError as e:
            st.error("🚫 API 키가 잘못되었습니다. 올바른 키를 입력해주세요.")
            st.stop()

        except openai.OpenAIError as e:
            st.error(f"❌ OpenAI API 호출 중 오류: {str(e)}")
            if attempt < max_retries - 1:
                st.info(f"🔄 재시도 중... ({attempt + 1}/{max_retries})")
            continue

        except Exception as e:
            st.error(f"❌ 예상치 못한 오류: {str(e)}")
            if attempt < max_retries - 1:
                st.info(f"🔄 재시도 중... ({attempt + 1}/{max_retries})")
                continue
            else:
                break

    # 실패시 기본 질문 사용
    st.warning("⚠️ API 질문 생성에 실패하여 기본 질문을 사용합니다.")
    return get_default_questions(question_count)

def get_default_questions(question_count=8):
    """API 오류 시 사용할 기본 질문들"""

    base_questions = [
        {
            "question": "새로운 사람들과의 모임에서 당신은?",
            "type": "E/I",
            "options": [
                {"text": "적극적으로 다른 사람들에게 말을 걸고 대화를 시작한다", "type": "E"},
                {"text": "조용히 있다가 누군가 먼저 말을 걸어주길 기다린다", "type": "I"}
            ]
        },
        {
            "question": "주말에 에너지를 충전하는 방법은?",
            "type": "E/I",
            "options": [
                {"text": "친구들과 만나서 활발하게 대화하며 시간을 보낸다", "type": "E"},
                {"text": "혼자만의 조용한 시간을 가지며 휴식한다", "type": "I"}
            ]
        },
        {
            "question": "새로운 정보를 학습할 때 당신은?",
            "type": "S/N",
            "options": [
                {"text": "구체적인 사실과 세부사항부터 차근차근 익힌다", "type": "S"},
                {"text": "전체적인 개념과 원리를 먼저 파악하려 한다", "type": "N"}
            ]
        },
        {
            "question": "문제를 해결할 때 당신은?",
            "type": "S/N",
            "options": [
                {"text": "검증된 방법과 과거 경험을 활용한다", "type": "S"},
                {"text": "새로운 아이디어와 창의적 방법을 시도한다", "type": "N"}
            ]
        },
        {
            "question": "중요한 결정을 내릴 때 당신은?",
            "type": "T/F",
            "options": [
                {"text": "논리적 분석과 객관적 기준을 중시한다", "type": "T"},
                {"text": "관련된 사람들의 감정과 가치를 우선 고려한다", "type": "F"}
            ]
        },
        {
            "question": "팀에서 갈등이 생겼을 때 당신은?",
            "type": "T/F",
            "options": [
                {"text": "사실에 근거해 문제의 원인을 분석하고 해결방안을 찾는다", "type": "T"},
                {"text": "구성원들의 마음을 달래고 화합을 이루려 노력한다", "type": "F"}
            ]
        },
        {
            "question": "여행 계획을 세울 때 당신은?",
            "type": "J/P",
            "options": [
                {"text": "미리 상세한 일정을 짜고 예약을 완료한다", "type": "J"},
                {"text": "대략적인 계획만 세우고 현지에서 즉흥적으로 결정한다", "type": "P"}
            ]
        },
        {
            "question": "업무나 과제를 처리할 때 당신은?",
            "type": "J/P",
            "options": [
                {"text": "계획을 세워 단계별로 체계적으로 진행한다", "type": "J"},
                {"text": "상황에 따라 유연하게 순서를 바꿔가며 진행한다", "type": "P"}
            ]
        }
    ]

    # 요청된 질문 개수에 맞춰 반복하여 반환
    questions_per_dimension = question_count // 4
    result_questions = []

    for i in range(questions_per_dimension):
        for j in range(4):  # 4개 차원
            question_index = (i * 4 + j) % len(base_questions)
            result_questions.append(base_questions[question_index])

    return result_questions

# MBTI 결과 설명
MBTI_DESCRIPTIONS = {
    "ENFJ": "🌟 선천적인 리더, 타인을 이끌고 영감을 주는 사람",
    "ENFP": "🎨 열정적인 자유로운 영혼, 창의적이고 사교적인 사람",
    "ENTJ": "👑 대담한 지도자, 목표 달성을 위해 노력하는 사람",
    "ENTP": "💡 똑똑한 호기심 많은 사상가, 새로운 도전을 즐기는 사람",
    "ESFJ": "🤝 사교적이고 인기 많은 사람, 타인을 돕기 좋아하는 사람",
    "ESFP": "🎭 자유로운 연예인, 즉흥적이고 열정적인 사람",
    "ESTJ": "📋 엄격한 관리자, 질서와 규칙을 중시하는 사람",
    "ESTP": "⚡ 모험을 즐기는 사업가, 실용적이고 현실적인 사람",
    "INFJ": "🔮 신비로운 옹호자, 이상주의적이고 원칙이 뚜렷한 사람",
    "INFP": "🌸 중재자, 조화롭고 유연한 사람",
    "INTJ": "🏗️ 용의주도한 전략가, 독립적이고 결단력 있는 사람",
    "INTP": "🔬 논리적인 사색가, 지식을 추구하는 사람",
    "ISFJ": "🛡️ 용감한 수호자, 따뜻하고 헌신적인 사람",
    "ISFP": "🎨 호기심 많은 예술가, 유연하고 매력적인 사람",
    "ISTJ": "📚 현실주의자, 신뢰할 수 있고 책임감 강한 사람",
    "ISTP": "🔧 만능 재주꾼, 대담하고 실용적인 사람"
}

# 세션 상태 초기화
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "test_completed" not in st.session_state:
    st.session_state.test_completed = False
if "current_question_data" not in st.session_state:
    st.session_state.current_question_data = None
if "test_started" not in st.session_state:
    st.session_state.test_started = False
if "all_questions" not in st.session_state:
    st.session_state.all_questions = []
if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = False
if "question_count" not in st.session_state:
    st.session_state.question_count = 8
if "kakao_js_key" not in st.session_state:
    st.session_state.kakao_js_key = ""

# 메인 타이틀
st.markdown('<h1 class="stTitle">🧠 Simple MBTI 성격 테스트 🔍</h1>', unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.markdown("---")

    # 질문 개수 선택
    st.markdown("### 📊 질문 개수 설정")
    st.markdown("💡 질문 개수 설정은 기본 8개이며, 16가지 MBTI 유형을 알아가기 위한 질문 개수입니다. 더 많은 질문을 선택하실수록 보다 정확한 성격 유형 결과를 확인하실 수 있어요! 😊")
    question_options = [4, 8, 12, 16, 20]
    selected_count = st.selectbox(
        "질문 개수를 선택하세요 (4의 배수)",
        options=question_options,
        index=question_options.index(st.session_state.question_count)
    )

    if selected_count != st.session_state.question_count:
        st.session_state.question_count = selected_count
        # 질문 개수가 변경되면 테스트 초기화
        if st.session_state.test_started:
            st.session_state.test_started = False
            st.session_state.current_question = 0
            st.session_state.answers = []
            st.session_state.test_completed = False
            st.session_state.all_questions = []
            st.session_state.questions_generated = False
            st.info(f"질문 개수가 {selected_count}개로 변경되어 테스트가 초기화되었습니다.")

    # OpenAI 클라이언트 초기화 (항상 실행)
    openai_api_key = st.secrets['openai']['API_KEY']
    client = OpenAI(api_key=openai_api_key)

    st.markdown("---")
    st.markdown("### 💬 카카오톡 공유 설정")
    st.markdown("카카오톡 공유 기능을 사용하려면 카카오 JavaScript 키가 필요합니다.")
    
    # 카카오 키 입력
    kakao_key_input = st.text_input(
        "카카오 JavaScript 키 (선택사항)",
        value=st.session_state.kakao_js_key,
        type="password",
        help="카카오 개발자 콘솔에서 발급받은 JavaScript 키를 입력하세요."
    )
    
    if kakao_key_input != st.session_state.kakao_js_key:
        st.session_state.kakao_js_key = kakao_key_input
        if kakao_key_input:
            st.success("✅ 카카오 JavaScript 키가 설정되었습니다!")
            # 키가 설정되면 JavaScript에 실시간으로 적용
            st.markdown(f"""
            <script>
                if (typeof Kakao !== 'undefined' && !Kakao.isInitialized()) {{
                    try {{
                        Kakao.init('{kakao_key_input}');
                        console.log('Kakao SDK 초기화 완료');
                    }} catch (error) {{
                        console.error('Kakao SDK 초기화 실패:', error);
                    }}
                }}
            </script>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 키를 입력하지 않으면 웹 공유 방식이 사용됩니다.")
    
    # 카카오 키 발급 방법 안내
    with st.expander("🔑 카카오 JavaScript 키 발급 방법"):
        st.markdown("""
        1. **카카오 개발자 콘솔** 접속: https://developers.kakao.com
        2. **로그인** 후 "내 애플리케이션" 클릭
        3. **애플리케이션 추가하기** (앱 이름: MBTI 테스트 등)
        4. **요약 정보**에서 **JavaScript 키** 복사
        5. **플랫폼 설정**에서 **Web 플랫폼 등록**
           - `http://localhost:8501` (로컬 테스트용)
           - `https://simple-mbti.streamlit.app` (배포용)
        6. 위에서 복사한 JavaScript 키를 입력란에 붙여넣기
        
        ⚠️ **주의**: JavaScript 키는 공개되어도 상관없지만, REST API 키는 절대 공개하면 안됩니다.
        """)
    
    if st.session_state.kakao_js_key:
        st.markdown("🟢 **카카오톡 SDK 공유 모드**")
    else:
        st.markdown("🟡 **웹 공유 모드** (키 미설정)")
    

    # 테스트 시작 버튼
    if not st.session_state.test_started:
        if st.button("🚀 테스트 시작하기", use_container_width=True):
            st.session_state.test_started = True
            st.session_state.current_question = 0
            # 모든 질문을 한번에 생성
            with st.spinner(f"🤔 AI가 {st.session_state.question_count}개의 맞춤형 질문을 생성하고 있습니다..."):
                st.session_state.all_questions = generate_all_questions(client, st.session_state.question_count)
                st.session_state.questions_generated = True
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 테스트 진행상황")
    if st.session_state.test_started:
        progress = st.session_state.current_question / st.session_state.question_count
        st.progress(progress)
        st.markdown(f"**{st.session_state.current_question}/{st.session_state.question_count}** 완료")
    else:
        st.markdown("테스트 시작 대기 중...")

    st.markdown("---")
    st.markdown("### 📋 MBTI란?")
    st.markdown("""

    - **E/I**: 외향성 vs 내향성
    - **S/N**: 감각 vs 직관
    - **T/F**: 사고 vs 감정
    - **J/P**: 판단 vs 인식

    총 16가지 성격 유형으로 분류됩니다.
    """)

    if st.button("🔄 다시 시작"):
        st.session_state.current_question = 0
        st.session_state.answers = []
        st.session_state.test_completed = False
        st.session_state.current_question_data = None
        st.session_state.test_started = False
        st.session_state.all_questions = []
        st.session_state.questions_generated = False
        st.rerun()

def calculate_mbti():
    """답변을 바탕으로 MBTI 유형을 계산"""
    type_counts = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}

    for answer in st.session_state.answers:
        type_counts[answer] += 1

    mbti_type = ""
    mbti_type += "E" if type_counts["E"] >= type_counts["I"] else "I"
    mbti_type += "S" if type_counts["S"] >= type_counts["N"] else "N"
    mbti_type += "T" if type_counts["T"] >= type_counts["F"] else "F"
    mbti_type += "J" if type_counts["J"] >= type_counts["P"] else "P"

    return mbti_type

def create_share_message(mbti_result):
    """카카오톡 공유용 메시지 생성"""
    message = f"""🧠 MBTI 성격 테스트 결과 🔍

🎉 나의 MBTI 유형: {mbti_result}
{MBTI_DESCRIPTIONS[mbti_result]}

✨ AI가 생성한 맞춤형 질문으로 알아본 나의 성격!
당신도 테스트해보세요! 

#MBTI #성격테스트 #AI테스트"""
    
    return message

def create_kakao_share_url(message):
    """카카오톡 공유 URL 생성 (개선된 버전)"""
    # URL과 텍스트를 별도로 인코딩
    encoded_message = urllib.parse.quote(message, safe='')
    encoded_url = urllib.parse.quote("https://simple-mbti.streamlit.app", safe=':/?#[]@!$&\'()*+,;=')
    
    # 더 안정적인 카카오 공유 URL 구조 사용
    kakao_url = f"https://sharer.kakao.com/talk/friends/picker/link?url={encoded_url}&text={encoded_message}"
    return kakao_url

# 테스트 완료 후 결과 표시
if st.session_state.test_completed:
    mbti_result = calculate_mbti()

    st.markdown(
        f'<div class="result-container">'
        f'<h2>🎉 테스트 완료!</h2>'
        f'<div class="mbti-result">{mbti_result}</div>'
        f'<h3>{MBTI_DESCRIPTIONS[mbti_result]}</h3>'
        f'<p>당신의 성격 유형은 <strong>{mbti_result}</strong>입니다!</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # 결과 상세 설명
    st.markdown("### 📝 상세 분석")
    col1, col2, col3, col4 = st.columns(4)

    type_counts = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    for answer in st.session_state.answers:
        type_counts[answer] += 1

    with col1:
        ei_type = "외향성 (E)" if type_counts["E"] >= type_counts["I"] else "내향성 (I)"
        st.metric("에너지 방향", ei_type, f"E:{type_counts['E']} I:{type_counts['I']}")

    with col2:
        sn_type = "감각 (S)" if type_counts["S"] >= type_counts["N"] else "직관 (N)"
        st.metric("정보 수집", sn_type, f"S:{type_counts['S']} N:{type_counts['N']}")

    with col3:
        tf_type = "사고 (T)" if type_counts["T"] >= type_counts["F"] else "감정 (F)"
        st.metric("의사 결정", tf_type, f"T:{type_counts['T']} F:{type_counts['F']}")

    with col4:
        jp_type = "판단 (J)" if type_counts["J"] >= type_counts["P"] else "인식 (P)"
        st.metric("생활 양식", jp_type, f"J:{type_counts['J']} P:{type_counts['P']}")

    # 카카오톡 공유 기능
    st.markdown("### 📱 결과 공유하기")
    
    # 공유 메시지 생성
    share_message = create_share_message(mbti_result)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 카카오톡 공유 버튼 (SDK 사용)
        st.markdown("**💬 카카오톡 공유**")
        
        # JavaScript 키 설정 여부에 따른 다른 방식 제공
        # 공유용 데이터 준비
        share_title = f"🧠 MBTI 테스트 결과: {mbti_result}"
        share_description = f"{MBTI_DESCRIPTIONS[mbti_result]}\n\n✨ AI가 생성한 맞춤형 질문으로 알아본 나의 성격!"
        share_url = "https://simple-mbti.streamlit.app"
        share_image = "https://developers.kakao.com/assets/img/about/logos/kakaolink/kakaolink_btn_medium.png"
        
        # 카카오링크 API 버튼 (JavaScript 키가 있을 때 작동)
        kakao_button_id = f"kakao-share-btn-{mbti_result}"
        st.markdown(f"""
        <div style="text-align: center; margin: 10px 0;">
            <button id="{kakao_button_id}" 
                    style="background: #FEE500; color: #3C1E1E; border: none;
                           padding: 12px 20px; border-radius: 8px; font-weight: bold; 
                           font-size: 14px; cursor: pointer; transition: all 0.3s ease;"
                    onmouseover="this.style.backgroundColor='#FDD835'"
                    onmouseout="this.style.backgroundColor='#FEE500'"
                    onclick="shareToKakaoIfAvailable('{share_title}', '{share_description.replace(chr(10), " ").replace("'", chr(92)+"'")}', '{share_image}', '{share_url}')">
                💬 카카오톡으로 공유하기
            </button>
        </div>
        
        <script>
        function shareToKakaoIfAvailable(title, description, imageUrl, webUrl) {{
            // 먼저 카카오 키를 확인하고 초기화 시도
            const kakaoKey = '{st.session_state.kakao_js_key}';
            if (kakaoKey && typeof window.initKakaoWithKey === 'function') {{
                window.initKakaoWithKey(kakaoKey);
            }}
            
            // 카카오 SDK를 통한 공유 시도
            if (typeof window.shareToKakao === 'function') {{
                if (window.shareToKakao(title, description, imageUrl, webUrl)) {{
                    console.log('카카오톡 SDK 공유 성공');
                    return;
                }}
            }}
            
            // SDK가 없거나 실패한 경우 대체 방법 사용
            console.log('카카오톡 SDK 공유 실패, 웹 공유 방식 사용');
            const fallbackMessage = encodeURIComponent(`${{title}}

${{description}}

테스트 해보기: ${{webUrl}}`);
            
            const kakaoWebUrl = `https://sharer.kakao.com/talk/friends/picker/link?url=${{encodeURIComponent(webUrl)}}&text=${{fallbackMessage}}`;
            
            // 새 창에서 공유 페이지 열기
            const newWindow = window.open(kakaoWebUrl, '_blank', 'width=500,height=600');
            if (!newWindow) {{
                // 팝업이 차단된 경우 현재 창에서 열기
                window.location.href = kakaoWebUrl;
            }}
        }}
        </script>
        """, unsafe_allow_html=True)
        
        # 추가 공유 옵션들
        col1_1, col1_2 = st.columns(2)
        
        with col1_1:
            # SMS 공유
            share_text = f"MBTI 테스트 결과: {mbti_result} - {share_url}"
            sms_url = f"sms:?body={urllib.parse.quote(share_text)}"
            st.markdown(f"""
            <div style="text-align: center; margin: 5px 0;">
                <a href="{sms_url}" target="_blank" 
                   style="display: inline-block; background: #34A853; color: white; 
                          padding: 8px 12px; border-radius: 6px; text-decoration: none; 
                          font-weight: bold; font-size: 12px;">
                    📱 SMS
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        with col1_2:
            # 이메일 공유
            email_subject = urllib.parse.quote(share_title)
            email_body = urllib.parse.quote(f"{share_description}\n\n테스트 해보기: {share_url}")
            email_url = f"mailto:?subject={email_subject}&body={email_body}"
            st.markdown(f"""
            <div style="text-align: center; margin: 5px 0;">
                <a href="{email_url}" target="_blank" 
                   style="display: inline-block; background: #EA4335; color: white; 
                          padding: 8px 12px; border-radius: 6px; text-decoration: none; 
                          font-weight: bold; font-size: 12px;">
                    📧 이메일
                </a>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # 텍스트 복사 버튼
        if st.button("📋 결과 복사하기", use_container_width=True):
            st.code(share_message, language=None)
            st.success("✅ 위 텍스트를 복사해서 원하는 곳에 붙여넣으세요!")
    
    with col3:
        # URL 공유 버튼 (현재 페이지 URL)
        if st.button("🔗 링크 공유하기", use_container_width=True):
            st.code("https://simple-mbti.streamlit.app", language=None)
            st.success("✅ 위 링크를 복사해서 친구들에게 공유하세요!")

# 테스트 진행 중
elif st.session_state.test_started and st.session_state.questions_generated and st.session_state.current_question < st.session_state.question_count:
    if st.session_state.all_questions and st.session_state.current_question < len(st.session_state.all_questions):
        current_q = st.session_state.all_questions[st.session_state.current_question]

        # 환영 메시지 (첫 번째 질문일 때만)
        if st.session_state.current_question == 0:
            st.markdown(
                f'<div class="welcome-message">'
                f'<h3>🎯 AI가 생성한 {st.session_state.question_count}가지 질문으로 당신의 MBTI를 알아보세요!</h3>'
                f'<p>각 질문에 대해 더 가깝다고 느끼는 답변을 선택해주세요.</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        # 현재 질문 표시
        st.markdown(
            f'<div class="question-container">'
            f'<h2>질문 {st.session_state.current_question + 1}</h2>'
            f'<h3>{current_q["question"]}</h3>'
            f'</div>',
            unsafe_allow_html=True
        )

        # 답변 선택 버튼
        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"A. {current_q['options'][0]['text']}", key="option_a"):
                # 답변 저장
                st.session_state.answers.append(current_q['options'][0]['type'])
                st.session_state.current_question += 1

                # 테스트 완료 확인
                if st.session_state.current_question >= st.session_state.question_count:
                    st.session_state.test_completed = True
                st.rerun()

        with col2:
            if st.button(f"B. {current_q['options'][1]['text']}", key="option_b"):
                # 답변 저장
                st.session_state.answers.append(current_q['options'][1]['type'])
                st.session_state.current_question += 1

                # 테스트 완료 확인
                if st.session_state.current_question >= st.session_state.question_count:
                    st.session_state.test_completed = True
                st.rerun()

# 시작 화면
else:
    st.markdown(
        '<div class="welcome-message">'
        '<h2>🎯 AI 기반 MBTI 성격 테스트에 오신 것을 환영합니다!</h2>'
        '<p>AI가 생성하는 맞춤형 질문으로 당신의 성격 유형을 알아보세요.</p>'
        '<p>4개부터 20개까지 질문 개수를 선택할 수 있으며, 더 많은 질문일수록 정확한 결과를 얻을 수 있습니다.</p>'
        '<p>왼쪽 사이드바에서 질문 개수를 선택한 후 테스트를 시작해주세요!</p>'
        '</div>',
        unsafe_allow_html=True
    )
