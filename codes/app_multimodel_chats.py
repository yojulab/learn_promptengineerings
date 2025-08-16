import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from dataclasses import dataclass
import json
import time

# State 정의
@dataclass
class ChatState:
    messages: List[Dict[str, str]]
    model_name: str
    system_prompt: str
    current_step: str
    error: Optional[str] = None
    processing: bool = False

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
        state.current_step = "입력 검증 중..."
        
        if not state.messages:
            state.error = "메시지가 없습니다."
            return state
            
        if not state.model_name:
            state.error = "모델이 선택되지 않았습니다."
            return state
            
        if state.model_name not in self.available_models:
            state.error = f"지원하지 않는 모델입니다: {state.model_name}"
            return state
            
        state.error = None
        return state
    
    def should_process(self, state: ChatState) -> str:
        """조건부 라우팅"""
        return "error" if state.error else "process"
    
    def process_message(self, state: ChatState) -> ChatState:
        """메시지 전처리"""
        state.current_step = "메시지 처리 중..."
        state.processing = True
        return state
    
    def generate_response(self, state: ChatState) -> ChatState:
        """응답 생성"""
        try:
            state.current_step = f"{state.model_name} 모델로 응답 생성 중..."
            
            # Ollama 모델 초기화
            llm = Ollama(
                model=state.model_name,
                base_url="http://localhost:11434"
            )
            
            # 메시지 구성
            messages = []
            if state.system_prompt:
                messages.append(SystemMessage(content=state.system_prompt))
            
            # 대화 히스토리 추가
            for msg in state.messages:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            # 최신 사용자 메시지만 처리
            user_message = state.messages[-1]["content"]
            
            # 프롬프트 구성
            full_prompt = ""
            if state.system_prompt:
                full_prompt += f"System: {state.system_prompt}\n\n"
            full_prompt += f"Human: {user_message}\n\nAssistant:"
            
            # 응답 생성
            response = llm.invoke(full_prompt)
            
            # 응답을 메시지 히스토리에 추가
            state.messages.append({
                "role": "assistant",
                "content": response,
                "model": state.model_name
            })
            
            state.current_step = "완료"
            state.processing = False
            
        except Exception as e:
            state.error = f"응답 생성 중 오류 발생: {str(e)}"
            state.current_step = "오류 발생"
            state.processing = False
        
        return state
    
    def handle_error(self, state: ChatState) -> ChatState:
        """오류 처리"""
        state.current_step = f"오류: {state.error}"
        state.processing = False
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
        
        # 설정 저장
        if st.button("🔄 설정 새로고침", type="secondary"):
            st.rerun()
        
        # 대화 기록 삭제
        if st.button("🗑️ 대화 기록 삭제", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        
        # 모델 정보
        st.subheader("ℹ️ 모델 정보")
        st.json({
            "사용 가능한 모델": list(available_models.keys()),
            "현재 선택된 모델": selected_model,
            "총 대화 수": len(st.session_state.messages)
        })
    
    # 메인 작업 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 대화")
        
        # 대화 기록 표시
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                elif message["role"] == "assistant":
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        if "model" in message:
                            st.caption(f"Model: {message['model']}")
        
        # 사용자 입력
        user_input = st.chat_input("메시지를 입력하세요...")
        
        if user_input:
            # 사용자 메시지 추가
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 상태 생성
            state = ChatState(
                messages=st.session_state.messages.copy(),
                model_name=selected_model,
                system_prompt=system_prompt,
                current_step="시작",
                processing=True
            )
            
            # 그래프 실행
            try:
                result = st.session_state.graph_executor.invoke(state)
                
                # 결과를 세션에 저장
                if not result.error and len(result.messages) > len(st.session_state.messages):
                    st.session_state.messages = result.messages
                
            except Exception as e:
                st.error(f"처리 중 오류 발생: {str(e)}")
            
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