import json

import pdfplumber
from google.cloud import vision


def run_ocr(pdf_path):
    """PDFファイルからテキストを抽出する

    Args:
        pdf_path (_type_): PDFファイルのパス

    Returns:
        _type_: _description_
    """
    page_num = 1
    all_text = ""
    # PDFファイルを開く
    with pdfplumber.open(pdf_path) as pdf:
        # 全てのページを取得して
        for page in pdf.pages:
            # ページごとにテキストを抽出
            text = page.extract_text()
            if text:
                text_no_newline = text.replace("\n", "")
                all_text += f"[Page {page_num}]\n\n{text_no_newline}\n\n"
                page_num += 1
        #     print(text)
        # first_page = pdf.pages[0]

        # # テキストを抽出
        # text = first_page.extract_text()
        return all_text


def extract_table(pdf_path):
    """PDFファイルから表データを抽出する

    [Note]: tableデータが取得できた場合
        tables = [[[header1, header2, ...], [record1_1, record1_2, ...], [record2_1, record2_2, ...], ...]]
        の形式で返される．
        複数抽出された場合のためにこのような設計となっていると予想される．[[table1], [table2], ...]
        そのため，len(tables)が１でもtables[0]でアクセス


    Args:
        pdf_path (_type_): PDFファイルのパス

    Returns:
        _type_: _description_
    """
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        num_page = 4
        print(len(pdf.pages))
        tables = pdf.pages[num_page].extract_tables()
        print(f"Page {num_page} has {len(tables)} tables")
        # for i, table in enumerate(tables):
        #     print(f"Table {i+1}")
        #     for row in table:
        #         print(row)

        headers = tables[0][0]
        results["keys"] = headers
        # 2行目以降をレコードとして格納
        records = []
        for row in tables[0][1:]:
            record = {}
            # ヘッダーと各データのペアを作成
            for col_idx, header in enumerate(headers):
                record[header] = row[col_idx]
            records.append(record)

        results["records"] = records

        # 確認用にコンソールへ表示（任意）
        print(json.dumps(results, ensure_ascii=False, indent=2))

        return results

    # import fitz

    # # ドキュメントを開く
    # doc = fitz.open(pdf_path)

    # # ページを取得する
    # page = doc[4]

    # # ページ上にあるテーブルを検出する
    # tabs = page.find_tables()

    # # 検出されたテーブルの数を表示する
    # print(f"{len(tabs.tables)}個のテーブルが{page}上に見つかりました")

    # # 少なくとも1つのテーブルが見つかった場合
    # if tabs.tables:
    #     # 最初のテーブルの内容を表示する
    #     print(tabs[0].extract())


def async_detect_document(gcs_source_uri: str, gcs_destination_uri: str) -> None:
    """Cloud Vision APIのOCR機能を使ってPDFから文字情報を取得してJSONファイルとしてGCSに保存

    Args:
        gcs_source_uri (str): PDFのソースが保存されてるGCSのURI
        gcs_destination_uri (str): 文字情報を保存するGCSのURI
    """
    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "application/pdf"

    # How many pages should be grouped into each json output file.
    batch_size = 2

    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(gcs_destination=gcs_destination, batch_size=batch_size)

    async_request = vision.AsyncAnnotateFileRequest(features=[feature], input_config=input_config, output_config=output_config)

    operation = client.async_batch_annotate_files(requests=[async_request])

    print("Waiting for the document detection to complete.")
    operation.result(timeout=420)
