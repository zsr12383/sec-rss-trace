from bs4 import Comment
import re


def html_body_extractor(doc):
    for element in doc(['script', 'style', 'head', 'meta', 'title', 'link', 'noscript']):
        element.decompose()

    # 주석 제거
    for comment in doc.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 숨겨진 요소 제거 (예: display: none)
    for hidden in doc.find_all(style=lambda value: value and 'display: none' in value):
        hidden.decompose()

    # 추가로 제거할 태그들 (예: 네비게이션, 푸터, 사이드바 등)
    for element in doc(['nav', 'footer', 'aside']):
        element.decompose()

    # 텍스트 추출
    body = doc.body

    # 만약 body 태그가 없을 경우 대비
    if not body:
        body = doc

    text = body.get_text(separator='\n', strip=True)

    # 불필요한 공백 제거
    text = re.sub(r'\n\s*\n', '\n', text)
    return text
