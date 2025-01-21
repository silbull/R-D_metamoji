import pdfplumber


def extract_text(pdf_path):
    # PDFファイルを開く
    with pdfplumber.open(pdf_path) as pdf:
        # 最初のページを取得
        first_page = pdf.pages[1]

        # テキストを抽出
        text = first_page.extract_text()
        return text
