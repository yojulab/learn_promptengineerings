import pdfplumber
import pandas as pd
import os

def convert_pdf_to_excel(pdf_path, output_path):
    try:
        # PDF 파일 열기
        print("PDF 파일 읽는 중...")
        with pdfplumber.open(pdf_path) as pdf:
            # 모든 페이지의 텍스트 추출
            all_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # 줄 단위로 분리하고 빈 줄 제거
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    all_text.extend(lines)
        
        # DataFrame 생성
        df = pd.DataFrame(all_text, columns=['Content'])
        
        # 엑셀 파일로 저장
        print("엑셀 파일 생성 중...")
        df.to_excel(output_path, index=False)
        
        print(f"변환 완료! 엑셀 파일이 저장되었습니다: {output_path}")
        return True
    
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    # 현재 디렉토리의 절대 경로
    current_dir = "/apps/learn_promptengineerings/codes/pdf_to_excels"
    
    # PDF 파일 경로
    pdf_file = "빅데이터 기반 컴퓨터비전(CV)데이터사이언스과정_커리큘럼.pdf"
    pdf_path = os.path.join(current_dir, pdf_file)
    
    # 출력 엑셀 파일 경로
    output_file = "curriculum.xlsx"
    output_path = os.path.join(current_dir, output_file)
    
    # PDF를 엑셀로 변환
    convert_pdf_to_excel(pdf_path, output_path) 