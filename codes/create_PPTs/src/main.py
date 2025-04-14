from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import os
import markdown
import re

class PPTCreator:
    def __init__(self):
        self.prs = Presentation()
        self.output_dir = "codes/create_PPTs/output"
        
    def create_title_slide(self, title, subtitle=None):
        """제목 슬라이드 생성"""
        layout = self.prs.slide_layouts[0]
        slide = self.prs.slides.add_slide(layout)
        
        title_placeholder = slide.shapes.title
        subtitle_placeholder = slide.placeholders[1]
        
        title_placeholder.text = title
        if subtitle:
            subtitle_placeholder.text = subtitle
            
    def create_content_slide(self, title, content):
        """내용 슬라이드 생성"""
        layout = self.prs.slide_layouts[1]
        slide = self.prs.slides.add_slide(layout)
        
        title_placeholder = slide.shapes.title
        content_placeholder = slide.placeholders[1]
        
        title_placeholder.text = title
        content_placeholder.text = content
        
    def add_image_slide(self, title, image_path):
        """이미지 슬라이드 생성"""
        layout = self.prs.slide_layouts[5]
        slide = self.prs.slides.add_slide(layout)
        
        title_placeholder = slide.shapes.title
        title_placeholder.text = title
        
        # 이미지 추가
        left = Inches(2)
        top = Inches(2)
        if os.path.exists(image_path):
            slide.shapes.add_picture(image_path, left, top)
    
    def create_section_slide(self, title):
        """섹션 구분 슬라이드 생성"""
        layout = self.prs.slide_layouts[2]  # 섹션 헤더용 레이아웃
        slide = self.prs.slides.add_slide(layout)
        
        title_placeholder = slide.shapes.title
        title_placeholder.text = title
        
        # 섹션 슬라이드 스타일링
        title_placeholder.text_frame.paragraphs[0].font.size = Pt(44)
        title_placeholder.text_frame.paragraphs[0].font.bold = True
            
    def save(self, filename):
        """프레젠테이션 저장"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        output_path = os.path.join(self.output_dir, filename)
        self.prs.save(output_path)
        print(f"프레젠테이션이 저장되었습니다: {output_path}")

def parse_markdown_content(md_file):
    """마크다운 파일을 파싱하여 슬라이드 컨텐츠 추출"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 섹션 분리
    sections = re.split(r'\n## ', content)
    main_title = sections[0].strip('# \n')
    sections = [s.strip() for s in sections[1:]]
    
    slides = []
    # 메인 타이틀 슬라이드
    slides.append(('title', main_title, None))
    
    for section in sections:
        lines = section.split('\n')
        section_title = lines[0]
        
        # 섹션 타이틀 슬라이드
        slides.append(('section', section_title, None))
        
        # 서브섹션 처리
        current_subsection = ""
        current_content = []
        
        for line in lines[1:]:
            if line.startswith('### '):
                # 이전 서브섹션 저장
                if current_subsection and current_content:
                    content_text = '\n'.join(current_content)
                    slides.append(('content', current_subsection, content_text))
                
                current_subsection = line.strip('### ')
                current_content = []
            elif line.strip().startswith('- '):
                current_content.append(line.strip())
        
        # 마지막 서브섹션 저장
        if current_subsection and current_content:
            content_text = '\n'.join(current_content)
            slides.append(('content', current_subsection, content_text))
    
    return slides

def main():
    # 마크다운 파일 경로
    md_file = "codes/create_PPTs/data/ai_course_content.md"
    
    # PPT 생성기 인스턴스 생성
    creator = PPTCreator()
    
    # 마크다운 파싱
    slides = parse_markdown_content(md_file)
    
    # 슬라이드 생성
    for slide_type, title, content in slides:
        if slide_type == 'title':
            creator.create_title_slide(title, "AI 전문가 과정")
        elif slide_type == 'section':
            creator.create_section_slide(title)
        elif slide_type == 'content':
            creator.create_content_slide(title, content)
    
    # 저장
    creator.save("AI_Course.pptx")

if __name__ == "__main__":
    main() 