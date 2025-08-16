import streamlit as st

# 사이드바: AI 모델, MCP 서버 선택
def sidebar():
    st.sidebar.header('AI 모델 & MCP 서버 선택')
    ai_models = st.sidebar.multiselect('AI 모델 선택', ['gemma3:1b', 'qwen3:1.7b'], default=['gemma3:1b', 'qwen3:1.7b'])
    mcp_servers = st.sidebar.multiselect('MCP 서버 선택', ['pdf', 'excel', 'doc', 'hwp'], default=['pdf', 'excel', 'doc', 'hwp'])
    return ai_models, mcp_servers

# 작업영역: 프롬프트 입력, 파일 업로드, 로그
st.title('AI 멀티에이전트 문서 파싱/시각화')
ai_models, mcp_servers = sidebar()

st.subheader('프롬프트 입력')
system_prompt = st.text_area('System 프롬프트')
user_prompt = st.text_area('User 프롬프트')

st.subheader('파일 업로드')
uploaded_files = st.file_uploader('문서 파일 업로드', accept_multiple_files=True)

st.subheader('파싱 진행 로그')
log_placeholder = st.empty()

st.subheader('HTML 결과 캔버스')
canvas_placeholder = st.empty()

# ...에이전트 및 서비스 연동은 추후 구현...
