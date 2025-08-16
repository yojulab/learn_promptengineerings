import streamlit as st
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
import json
import time
import httpx
import base64

# State 정의
class ProcessingState(TypedDict):
    system_prompt: str
    user_prompt: str
    ai_models: List[str]
    mcp_servers: List[str]
    uploaded_files: List[Any]
    current_step: str
    error: Optional[str]
    processing: bool
    results: Dict[str, Any]

class DocumentProcessingGraph:
    def __init__(self):
        self.available_models = {
            "gemma3:1b": "Gemma 3 1B - 빠른 응답, 가벼운 모델",
            "qwen3:1.7b": "Qwen 3 1.7B - 균형잡힌 성능"
        }
        self.available_mcp_servers = {
            "pdf": "PDF 문서 처리",
            "excel": "Excel 스프레드시트 처리", 
            "doc": "Word 문서 처리",
            "hwp": "한글 문서 처리"
        }
        
    def create_graph(self) -> StateGraph:
        graph = StateGraph(ProcessingState)
        
        # 노드 추가
        graph.add_node("validate_input", self.validate_input)
        graph.add_node("analyze_files", self.analyze_files)
        graph.add_node("process_with_ai", self.process_with_ai)
        graph.add_node("generate_html", self.generate_html)
        graph.add_node("handle_error", self.handle_error)
        
        # 엣지 정의
        graph.set_entry_point("validate_input")
        graph.add_conditional_edges(
            "validate_input",
            self.should_process,
            {
                "process": "analyze_files",
                "error": "handle_error"
            }
        )
        graph.add_edge("analyze_files", "process_with_ai")
        graph.add_edge("process_with_ai", "generate_html")
        graph.add_edge("generate_html", END)
        graph.add_edge("handle_error", END)
        
        return graph.compile()
    
    def validate_input(self, state: ProcessingState) -> ProcessingState:
        """입력 검증"""
        state["current_step"] = "입력 검증 중..."
        state["error"] = None
        
        if not state["ai_models"]:
            state["error"] = "AI 모델을 선택해주세요."
            return state
            
        if not state["user_prompt"].strip():
            state["error"] = "User 프롬프트를 입력해주세요."
            return state
            
        if not state["uploaded_files"]:
            state["error"] = "처리할 파일을 업로드해주세요."
            return state
            
        return state
    
    def should_process(self, state: ProcessingState) -> str:
        """조건부 라우팅"""
        return "error" if state["error"] else "process"
    
    def analyze_files(self, state: ProcessingState) -> ProcessingState:
        """파일 분석 및 MCP 서버 선택"""
        state["current_step"] = "파일 분석 중..."
        
        file_info = []
        for file in state["uploaded_files"]:
            file_type = file.name.split(".")[-1].lower()
            file_info.append({
                "name": file.name,
                "type": file_type,
                "size": file.size if hasattr(file, 'size') else len(file.getvalue())
            })
        
        state["results"] = {"file_info": file_info}
        return state
    
    async def process_with_ai(self, state: ProcessingState) -> ProcessingState:
        """AI 모델로 파일 처리"""
        try:
            state["current_step"] = "AI 모델로 처리 중..."
            
            # 첫 번째 선택된 모델 사용
            selected_model = state["ai_models"][0]
            
            # 파일 정보를 프롬프트에 포함
            file_context = ""
            if state["uploaded_files"]:
                file_names = [f.name for f in state["uploaded_files"]]
                file_context = f"업로드된 파일: {', '.join(file_names)}"
            
            # 프롬프트 구성
            combined_prompt = f"""System: {state['system_prompt']}

User: {state['user_prompt']}

파일 정보: {file_context}

요청: 업로드된 파일들을 분석하고 HTML 형태로 결과를 제공해주세요."""
            
            # Ollama API 호출
            request_data = {
                "model": selected_model,
                "prompt": combined_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7
                }
            }
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json=request_data
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    ai_response = response_data.get("response", "")
                    
                    state["results"]["ai_response"] = ai_response
                    state["results"]["model_used"] = selected_model
                else:
                    state["error"] = f"AI 모델 처리 오류: {response.status_code}"
                    
        except Exception as e:
            state["error"] = f"AI 처리 중 오류: {str(e)}"
            print(f"AI 처리 오류: {e}")
            
        return state
    
    def generate_html(self, state: ProcessingState) -> ProcessingState:
        """HTML 결과 생성"""
        state["current_step"] = "HTML 결과 생성 중..."
        
        ai_response = state["results"].get("ai_response", "")
        model_used = state["results"].get("model_used", "")
        file_info = state["results"].get("file_info", [])
        
        # HTML 결과 생성
        html_content = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>🤖 AI 문서 분석 결과</h2>
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <strong>사용된 모델:</strong> {model_used}<br>
                <strong>처리된 파일 수:</strong> {len(file_info)}개
            </div>
            
            <h3>📁 파일 정보</h3>
            <ul>
                {"".join([f"<li>{file['name']} ({file['type']}) - {file['size']} bytes</li>" for file in file_info])}
            </ul>
            
            <h3>📝 AI 분석 결과</h3>
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin-top: 20px;">
                {ai_response.replace('\n', '<br>')}
            </div>
        </div>
        """
        
        state["results"]["html_content"] = html_content
        state["current_step"] = "완료"
        state["processing"] = False
        
        return state
    
    def handle_error(self, state: ProcessingState) -> ProcessingState:
        """오류 처리"""
        state["current_step"] = f"오류: {state['error']}"
        state["processing"] = False
        return state

# 사이드바: AI 모델, MCP 서버 선택
def sidebar():
    st.sidebar.header('AI 모델 & MCP 서버 선택')
    ai_models = st.sidebar.multiselect('AI 모델 선택', ['gemma3:1b', 'qwen3:1.7b'], default=['gemma3:1b', 'qwen3:1.7b'])
    mcp_servers = st.sidebar.multiselect('MCP 서버 선택', ['pdf', 'excel', 'doc', 'hwp'], default=['pdf', 'excel', 'doc', 'hwp'])
    return ai_models, mcp_servers

# 세션 상태 초기화
def init_session_state():
    if 'processing_graph' not in st.session_state:
        st.session_state.processing_graph = DocumentProcessingGraph()
    if 'graph_executor' not in st.session_state:
        st.session_state.graph_executor = st.session_state.processing_graph.create_graph()
    if 'current_results' not in st.session_state:
        st.session_state.current_results = {}

# 비동기 처리 함수
def run_async_processing(graph_executor, state_data):
    """새 스레드에서 비동기 그래프 실행"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(graph_executor.ainvoke(state_data))
    finally:
        loop.close()

# 작업영역: 프롬프트 입력, 파일 업로드, 로그
st.set_page_config(
    page_title="AI 멀티에이전트 문서 파싱/시각화",
    page_icon="🤖",
    layout="wide"
)

st.title('🤖 AI 멀티에이전트 문서 파싱/시각화')
st.caption("LangGraph와 Ollama를 활용한 AI 문서 분석 시스템")

init_session_state()
ai_models, mcp_servers = sidebar()

# 메인 컨텐츠 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader('📝 프롬프트 입력')
    system_prompt = st.text_area(
        'System 프롬프트', 
        '당신은 문서 분석 전문가입니다. 업로드된 파일을 분석하고 구조화된 정보를 제공해주세요.',
        height=100
    )
    user_prompt = st.text_area(
        'User 프롬프트', 
        '첨부된 파일들을 분석하고 주요 내용을 요약해주세요. HTML 형태로 구조화하여 제공해주세요.',
        height=100
    )

    st.subheader('📁 파일 업로드')
    uploaded_files = st.file_uploader(
        '문서 파일 업로드', 
        accept_multiple_files=True, 
        type=['pdf', 'docx', 'xlsx', 'hwp', 'txt'],
        key='file_uploader_main'
    )

    # 실행 버튼
    run_clicked = st.button('🚀 AI 분석 실행', type='primary', use_container_width=True)

    if run_clicked:
        if not ai_models:
            st.error("AI 모델을 선택해주세요.")
        elif not user_prompt.strip():
            st.error("User 프롬프트를 입력해주세요.")
        elif not uploaded_files:
            st.error("분석할 파일을 업로드해주세요.")
        else:
            # 상태 생성
            state = {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "ai_models": ai_models,
                "mcp_servers": mcp_servers,
                "uploaded_files": uploaded_files,
                "current_step": "시작",
                "error": None,
                "processing": True,
                "results": {}
            }
            
            # 진행 상황 표시
            with st.spinner("AI가 문서를 분석하고 있습니다..."):
                try:
                    # 그래프 실행자를 로컬 변수로 복사
                    graph_executor = st.session_state.graph_executor
                    
                    # 비동기 처리 실행
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_async_processing, graph_executor, state)
                        result = future.result(timeout=300)  # 5분 타임아웃
                    
                    # 결과 저장
                    if isinstance(result, dict):
                        if not result.get("error"):
                            st.session_state.current_results = result.get("results", {})
                            st.success("✅ 문서 분석이 완료되었습니다!")
                            st.rerun()
                        else:
                            st.error(f"❌ 처리 오류: {result['error']}")
                    else:
                        st.error("예상치 못한 결과 형식입니다.")
                        
                except Exception as e:
                    st.error(f"처리 중 오류 발생: {str(e)}")
                    print(f"오류 상세: {e}")
                    import traceback
                    traceback.print_exc()

with col2:
    st.subheader('📊 처리 정보')
    
    # 선택된 설정 표시
    with st.container():
        st.write("**선택된 AI 모델:**")
        if ai_models:
            for model in ai_models:
                st.write(f"• {model}")
        else:
            st.write("선택된 모델 없음")
        
        st.write("**선택된 MCP 서버:**")
        if mcp_servers:
            for server in mcp_servers:
                st.write(f"• {server}")
        else:
            st.write("선택된 서버 없음")
    
    # 파일 정보 표시
    if uploaded_files:
        st.write("**업로드된 파일:**")
        for file in uploaded_files:
            file_size = len(file.getvalue()) if hasattr(file, 'getvalue') else 0
            st.write(f"• {file.name} ({file_size:,} bytes)")

st.subheader('📋 분석 결과')

# 결과 표시
if st.session_state.current_results:
    results = st.session_state.current_results
    
    # HTML 내용이 있으면 표시
    if "html_content" in results:
        st.components.v1.html(
            results["html_content"], 
            height=600, 
            scrolling=True
        )
    
    # 원본 AI 응답도 표시 (디버깅용)
    if "ai_response" in results:
        with st.expander("🔍 원본 AI 응답 보기"):
            st.text_area(
                "AI 모델 응답:",
                results["ai_response"],
                height=200,
                disabled=True
            )
else:
    st.info("📤 파일을 업로드하고 '🚀 AI 분석 실행' 버튼을 클릭하여 분석을 시작하세요.")
