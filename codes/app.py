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


system_prompt = st.text_area('System 프롬프트', '파일 종류 따라 파싱')
user_prompt = st.text_area('User 프롬프트', '첨부 파일 tml로 파싱')

st.subheader('파일 업로드')
uploaded_files = st.file_uploader('문서 파일 업로드', accept_multiple_files=True, key='file_uploader_main')

# 실행 버튼 추가
run_clicked = st.button('실행')

if run_clicked:
    st.info('실행 버튼이 눌렸습니다.')
    # TODO: 프롬프트, 파일, 모델, MCP 서버 선택값을 처리하는 로직 연결
    st.write('선택된 AI 모델:', ai_models)
    st.write('선택된 MCP 서버:', mcp_servers)
    st.write('System 프롬프트:', system_prompt)
    st.write('User 프롬프트:', user_prompt)
    st.write('업로드된 파일:', [f.name for f in uploaded_files] if uploaded_files else '없음')

st.subheader('파싱 진행 로그')
log_placeholder = st.empty()

st.subheader('HTML 결과 캔버스')
canvas_placeholder = st.empty()

# ...에이전트 및 서비스 연동은 추후 구현...
