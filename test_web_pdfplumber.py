import pdfplumber

# PDFファイルのパスを指定
pdf_path = "miyawaki_paper_MIRU2024.pdf"

# PDFファイルを開く
with pdfplumber.open(pdf_path) as pdf:
    # 最初のページを取得
    first_page = pdf.pages[0]

    # テキストを抽出
    text = first_page.extract_text()
    print(text)
