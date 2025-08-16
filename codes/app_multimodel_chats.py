import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from dataclasses import dataclass
import json
import time
import httpx
import requests

# State 정의
from typing import TypedDict

class ChatState(TypedDict):
    messages: List[Dict[str, str]]
    model_name: str
    system_prompt: str
    current_step: str
    error: Optional[str]
    processing: bool

class MultiModelChatGraph:
    def __init__(self):
        self.available_models = {
            "gemma3:1b": "Gemma 3 1B - 빠른 응답, 가벼운 모델",
            "qwen3:1.7b": "Qwen 3 1.7B - 균형잡힌 성능"
        }
        
    def create_graph(self) -> StateGraph:
        # StateGraph 생성
        graph = StateGraph(ChatState)
        
        # 노드 추가
        graph.add_node("validate_input", self.validate_input)
        graph.add_node("process_message", self.process_message)
        graph.add_node("generate_response", self.generate_response)
        graph.add_node("handle_error", self.handle_error)
        
        # 엣지 정의
        graph.set_entry_point("validate_input")
        graph.add_conditional_edges(
            "validate_input",
            self.should_process,
            {
                "process": "process_message",
                "error": "handle_error"
            }
        )
        graph.add_edge("process_message", "generate_response")
        graph.add_edge("generate_response", END)
        graph.add_edge("handle_error", END)
        
        return graph.compile()
    
    def validate_input(self, state: ChatState) -> ChatState:
        """입력 검증"""
        state["current_step"] = "입력 검증 중..."
        
        if not state["messages"]:
            state["error"] = "메시지가 없습니다."
            return state
            
        if not state["model_name"]:
            state["error"] = "모델이 선택되지 않았습니다."
            return state
            
        if state["model_name"] not in self.available_models:
            state["error"] = f"지원하지 않는 모델입니다: {state['model_name']}"
            return state
            
        state["error"] = None
        return state
    
    def should_process(self, state: ChatState) -> str:
        """조건부 라우팅"""
        return "error" if state["error"] else "process"
    
    def process_message(self, state: ChatState) -> ChatState:
        """메시지 전처리"""
        state["current_step"] = "메시지 처리 중..."
        state["processing"] = True
        return state
    
    async def generate_response(self, state: ChatState) -> ChatState:
        """응답 생성 - 개선된 오류 처리 및 재시도 로직"""
        try:
            state["current_step"] = f"{state['model_name']} 모델로 응답 생성 중..."
            
            # 최신 사용자 메시지만 처리
            user_message = state["messages"][-1]["content"]
            
            # 프롬프트 길이 제한 (너무 긴 프롬프트는 오류 원인이 될 수 있음)
            if len(user_message) > 2000:
                user_message = user_message[:2000] + "..."
            
            # 프롬프트 구성 (system과 user 분리, 더 간단한 형태)
            if state["system_prompt"] and len(state["system_prompt"].strip()) > 0:
                combined_prompt = f"{state['system_prompt']}\n\n{user_message}"
            else:
                combined_prompt = user_message
            
            # HTTP 요청 데이터 구성 (최소한의 옵션으로 안정성 향상)
            request_data = {
                "model": state["model_name"],
                "prompt": combined_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7
                }
            }
            
            print(f"🔧 요청 데이터: 모델={state['model_name']}, 프롬프트 길이={len(combined_prompt)}")
            
            # 먼저 모델 상태 확인
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    models_response = await client.get("http://localhost:11434/api/tags")
                    if models_response.status_code == 200:
                        models_data = models_response.json()
                        model_names = [model.get("name", "") for model in models_data.get("models", [])]
                        if state["model_name"] not in model_names:
                            print(f"⚠️ 모델 {state['model_name']}이 로드되지 않았습니다. 사용 가능한 모델: {model_names}")
                        else:
                            print(f"✅ 모델 {state['model_name']} 확인됨")
                    else:
                        print(f"⚠️ 모델 목록 조회 실패: {models_response.status_code}")
            except Exception as e:
                print(f"⚠️ 모델 상태 확인 실패: {e}")
            
            # Ollama API 직접 호출 (타임아웃 증가 및 재시도 로직)
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # 첫 번째 시도가 실패하면 간단한 프롬프트로 테스트
                    if attempt == 1:
                        print("🔄 간단한 프롬프트로 재시도...")
                        request_data["prompt"] = "Hello"
                        request_data["options"] = {"temperature": 0.1}
                    
                    async with httpx.AsyncClient(timeout=90.0) as client:  # 타임아웃 더 증가
                        response = await client.post(
                            "http://localhost:11434/api/generate",
                            json=request_data
                        )
                        
                        # 상태 코드 확인
                        if response.status_code == 200:
                            response_data = response.json()
                            break
                        elif response.status_code == 500:
                            if attempt < max_retries - 1:
                                print(f"⚠️ 서버 오류 (시도 {attempt + 1}/{max_retries}), 재시도...")
                                await asyncio.sleep(2)  # 2초 대기 후 재시도
                                continue
                            else:
                                raise httpx.HTTPStatusError(f"서버 오류: {response.status_code}", request=response.request, response=response)
                        else:
                            response.raise_for_status()
                            
                except httpx.TimeoutException:
                    if attempt < max_retries - 1:
                        print(f"⏰ 타임아웃 (시도 {attempt + 1}/{max_retries}), 재시도...")
                        await asyncio.sleep(3)  # 3초 대기 후 재시도
                        continue
                    else:
                        raise
            
            # 응답 텍스트 추출
            ai_response = response_data.get("response", "")
            
            # 빈 응답 처리
            if not ai_response or ai_response.strip() == "":
                ai_response = "죄송합니다. 응답을 생성하지 못했습니다."
            
            # 응답을 메시지 히스토리에 추가
            state["messages"].append({
                "role": "assistant",
                "content": ai_response.strip(),
                "model": state["model_name"]
            })
            
            state["current_step"] = "완료"
            state["processing"] = False
            
            # 디버깅용 로그
            print(f"✅ 응답 생성 완료: {ai_response[:100]}...")
            
        except httpx.TimeoutException:
            state["error"] = "요청 시간 초과 - Ollama 서버가 응답하지 않습니다."
            state["current_step"] = "시간 초과"
            state["processing"] = False
            print("⏰ 타임아웃 오류")
        except httpx.RequestError as e:
            state["error"] = f"연결 오류: Ollama 서버에 연결할 수 없습니다. ({str(e)})"
            state["current_step"] = "연결 오류"
            state["processing"] = False
            print(f"🔌 연결 오류: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                state["error"] = "서버 내부 오류 - 모델이 로드되지 않았거나 프롬프트에 문제가 있을 수 있습니다."
            else:
                state["error"] = f"HTTP 오류: {e.response.status_code}"
            state["current_step"] = "서버 오류"
            state["processing"] = False
            print(f"🚫 HTTP 오류: {e.response.status_code}")
        except Exception as e:
            state["error"] = f"예상치 못한 오류: {str(e)}"
            state["current_step"] = "오류 발생"
            state["processing"] = False
            print(f"💥 예상치 못한 오류: {e}")
        
        return state
    
    def handle_error(self, state: ChatState) -> ChatState:
        """오류 처리"""
        state["current_step"] = f"오류: {state['error']}"
        state["processing"] = False
        return state

def init_session_state():
    """세션 상태 초기화"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chat_graph' not in st.session_state:
        st.session_state.chat_graph = MultiModelChatGraph()
    if 'graph_executor' not in st.session_state:
        st.session_state.graph_executor = st.session_state.chat_graph.create_graph()

def main():
    st.set_page_config(
        page_title="LangGraph Multi-Model Chat",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    st.title("🤖 LangGraph Multi-Model Chat")
    st.caption("LangGraph와 Streamlit을 활용한 다중 모델 채팅 애플리케이션")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 모델 선택
        st.subheader("🔧 모델 선택")
        available_models = st.session_state.chat_graph.available_models
        
        selected_model = st.selectbox(
            "사용할 모델을 선택하세요:",
            options=list(available_models.keys()),
            format_func=lambda x: f"{x} - {available_models[x]}",
            key="selected_model"
        )
        
        st.info(f"선택된 모델: **{selected_model}**")
        
        # 프롬프트 설정
        st.subheader("📝 프롬프트 설정")
        
        # System 메시지
        system_prompt = st.text_area(
            "System 메시지:",
            value="당신은 도움이 되는 AI 어시스턴트입니다. 친절하고 정확한 답변을 제공해주세요.",
            height=100,
            help="모델의 전반적인 행동을 지정합니다."
        )
        
        # 디버깅 모드 추가
        debug_mode = st.checkbox("🐛 디버그 모드", help="원본 응답을 확인할 수 있습니다.")
        
        # 설정 저장
        if st.button("🔄 설정 새로고침", type="secondary"):
            st.rerun()
        
        # 대화 기록 삭제
        if st.button("🗑️ 대화 기록 삭제", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        
        # 서버 상태 확인
        st.subheader("🔌 서버 상태")
        if st.button("🔍 Ollama 서버 확인", type="secondary"):
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    models_data = response.json()
                    model_names = [model.get("name", "") for model in models_data.get("models", [])]
                    st.success(f"✅ 서버 정상 - 로드된 모델: {', '.join(model_names)}")
                else:
                    st.error(f"❌ 서버 오류: {response.status_code}")
            except Exception as e:
                st.error(f"❌ 연결 실패: {str(e)}")
        
        # 모델 정보
        st.subheader("ℹ️ 모델 정보")
        st.json({
            "사용 가능한 모델": list(available_models.keys()),
            "현재 선택된 모델": selected_model,
            "총 대화 수": len(st.session_state.messages)
        })
    
    # 사용자 입력을 상단으로 이동
    st.subheader("💬 대화")
    user_input = st.chat_input("메시지를 입력하세요...")
    
    # 메인 작업 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 대화 기록 표시
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(message["content"])
                elif message["role"] == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(message["content"])
                        if "model" in message:
                            st.caption(f"Model: {message['model']}")
                        
                        # 디버그 모드에서 원본 응답 표시
                        if debug_mode and i == len(st.session_state.messages) - 1:
                            with st.expander("🔍 디버그 정보"):
                                st.text("이 정보는 마지막 응답에 대한 디버그 정보입니다.")
        
        # 사용자 입력 처리
        if user_input:
            # 사용자 메시지 추가
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 진행 상황 표시
            with st.spinner("응답 생성 중..."):
                # 상태 생성 (TypedDict 형태로)
                state = {
                    "messages": st.session_state.messages.copy(),
                    "model_name": selected_model,
                    "system_prompt": system_prompt,
                    "current_step": "시작",
                    "error": None,
                    "processing": True
                }
                
                # 그래프 실행 (graph_executor를 직접 전달)
                try:
                    # Streamlit에서 async 함수 실행하기 위한 간단한 방법
                    import concurrent.futures
                    
                    # 그래프 실행자를 로컬 변수로 복사 (스레드 간 공유 불가 해결)
                    graph_executor = st.session_state.graph_executor
                    
                    def run_async_in_thread(executor, state_data):
                        # 새 스레드에서 새로운 이벤트 루프 생성
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(executor.ainvoke(state_data))
                        finally:
                            loop.close()
                    
                    # ThreadPoolExecutor를 사용하여 async 함수 실행
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_async_in_thread, graph_executor, state)
                        result = future.result(timeout=350)  # 7분 타임아웃
                    
                    # 결과를 세션에 저장 (딕셔너리 접근 방식)
                    if isinstance(result, dict):
                        if not result.get("error"):
                            if "messages" in result and len(result["messages"]) > len(st.session_state.messages):
                                st.session_state.messages = result["messages"]
                                print(f"✅ UI 업데이트: {len(result['messages'])}개 메시지")
                            else:
                                print("⚠️ 메시지 업데이트 없음")
                                print(f"🔍 결과 메시지 수: {len(result.get('messages', []))}, 세션 메시지 수: {len(st.session_state.messages)}")
                        else:
                            st.error(f"오류: {result['error']}")
                            print(f"❌ 오류 발생: {result['error']}")
                    else:
                        print(f"🔍 결과 상태: {type(result)}, {result}")
                
                except Exception as e:
                    st.error(f"처리 중 오류 발생: {str(e)}")
                    print(f"💥 처리 오류: {e}")
                    import traceback
                    traceback.print_exc()
            
            st.rerun()
    
    with col2:
        st.subheader("📊 작업 상태")
        
        # 진행 상태 표시
        status_container = st.container()
        
        with status_container:
            if st.session_state.messages:
                last_message = st.session_state.messages[-1]
                
                if last_message["role"] == "user":
                    st.info("🔄 처리 대기 중...")
                    st.progress(0)
                else:
                    st.success("✅ 완료")
                    st.progress(100)
            else:
                st.info("💬 대화를 시작해보세요!")
        
        # 실시간 통계
        st.subheader("📈 통계")
        
        total_messages = len(st.session_state.messages)
        user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
        assistant_messages = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("전체 메시지", total_messages)
            st.metric("사용자 메시지", user_messages)
        
        with col_stat2:
            st.metric("AI 응답", assistant_messages)
            if assistant_messages > 0:
                avg_length = sum(len(msg["content"]) for msg in st.session_state.messages if msg["role"] == "assistant") / assistant_messages
                st.metric("평균 응답 길이", f"{avg_length:.0f}자")
        
        # 최근 활동
        st.subheader("🕒 최근 활동")
        if st.session_state.messages:
            recent_messages = st.session_state.messages[-3:]
            for msg in recent_messages:
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                st.text(f"{role_icon} {content_preview}")
        else:
            st.text("아직 대화가 없습니다.")

if __name__ == "__main__":
    main()