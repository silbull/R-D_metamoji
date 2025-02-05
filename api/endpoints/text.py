import base64
import os
import sys
import time

import aiofiles
from dotenv import load_dotenv

from util.redis_util import redis_table_get, redis_table_put, redis_text_get, redis_text_put
from util.text_table_util import extract_table, run_ocr
from util.util import getNoteId, is_reload_enabled

load_dotenv()

# ローカルフォルダー
local_folder = os.environ.get("LOCAL_FOLDER")
if local_folder is None:
    print("環境変数LOCAL_FOLDERが設定されていません")
    sys.exit()

# ==================================================================================================
# テキスト抽出処理
# ==================================================================================================


async def extract_text(json_data: dict):
    """eYACHO/GEMBA Noteから送信されてきたPDF情報をファイルに保存し、OCRを実行する

    Args:
        json_data (dict): クライアント（eYACHO/GEMBA Note）からのPDF情報

    Returns:
        _type_: 物体が検出された領域（JSON形式）
    """
    results = {}
    results["message"] = "不明なエラーが発生しました"

    if ("inputPDF in json_data") == False:
        results["message"] = "入力PDFが設定されていません"
        return results

    # Base64文字列をバイナリファイルに保存
    split_string = json_data["inputPDF"].split(",")  # data:application/pdf;base64, <エンコード文字列>に分割
    pdf_binary = base64.b64decode(split_string[1])  # PDFファイルのバイナリデータ(つまり、ファイルの中身)

    # ファイル拡張子を取得
    header = split_string[0].split("/")  # data:application / pdf;base64
    extension = header[1].split(";")  # pdf;base64

    # 保存するPDFファイル名を準備する
    # print(f"{json_data['_noteLink']=}")
    note_id = getNoteId(json_data["_noteLink"])
    # print(f"{note_id=}")
    filename = note_id + "-" + str(time.strftime("%Y%m%d%H%M%S")) + "." + extension[0]  # .pdf
    file_path = local_folder + "/" + filename

    # PDFファイルを保存
    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(pdf_binary)
    except OSError as e:
        print(e)
        return results

    if is_reload_enabled():
        print("[SAVED]", file_path)

    # PDFファイルからテキストを抽出する
    extracted_text = run_ocr(file_path)

    if is_reload_enabled():
        print(f"{extracted_text=}")

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    key = note_id + "-" + json_data["_pageId"]
    os.remove(file_path)

    # REDISにテキストを格納
    status = redis_text_put(key, extracted_text)

    if status is False:
        results["message"] = "テキストが抽出されませんでした"
        return results

    return {"message": "テキストが抽出されました"}

# ==================================================================================================
# テキスト返却処理
# ==================================================================================================

def get_text(json_data: dict) -> dict:
    """抽出したテキストを取得する

    Args:
        json_data (dict): eYACHO/GEMBA Noteから送信された情報

    Returns:
        dict: 抽出したテキストを含むJSON形式
    """
    if is_reload_enabled():
        print("[JSON for detected_results]", json_data)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    note_id = getNoteId(json_data["_NOTE_LINK"])
    key = note_id + "-" + json_data["_PAGE_ID"]
    results = redis_text_get(key)
    print(f"{results=}")

    return results

# ==================================================================================================
# テーブル抽出処理
# ==================================================================================================

async def extract_tables(json_data: dict):
    """eYACHO/GEMBA Noteから送信されてきたPDF情報をファイルに保存し、表ページのデータを抽出してredisに格納


    Args:
        json_data (dict): _description_
    """
    results = {}
    results["message"] = "不明なエラーが発生しました"

    # print(f"{json_data=}")

    if ("inputPDF in json_data") == False:
        results["message"] = "入力PDFが設定されていません"
        return results

    # Base64文字列をバイナリファイルに保存
    split_string = json_data["inputPDF"].split(",")  # data:application/pdf;base64, <エンコード文字列>に分割
    pdf_binary = base64.b64decode(split_string[1])

    # ファイル拡張子を取得
    header = split_string[0].split("/")  # data:application / pdf;base64
    extension = header[1].split(";")  # pdf;base64

    # 保存するPDFファイル名を準備する
    note_id = getNoteId(json_data["_noteLink"])
    filename = note_id + "-" + str(time.strftime("%Y%m%d%H%M%S")) + "." + extension[0]  # .pdf
    file_path = local_folder + "/" + filename

    # PDFファイルを保存
    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(pdf_binary)
    except OSError as e:
        print(e)
        return results

    if is_reload_enabled():
        print("[SAVED]", file_path)

    # PDFファイルから表を抽出する
    extracted_table = extract_table(file_path)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    key = note_id + "-" + json_data["_pageId"]
    os.remove(file_path)

    status = redis_table_put(key, extracted_table)

    if status is False:
        results["message"] = "テキストが抽出されませんでした"
        return results

    return {"message": "テキストが抽出されました"}

# ==================================================================================================
# テーブル返却処理
# ==================================================================================================

def get_table(json_data: dict):
    """抽出したテーブルを取得する

    Args:
        json_data (dict): _description_

    Returns:
        _type_: _description_
    """
    # if is_reload_enabled():
    # print("[JSON for detected_results]", json_data)

    # print(f"{json_data=}")

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    note_id = getNoteId(json_data["_NOTE_LINK"])
    key = note_id + "-" + json_data["_PAGE_ID"]
    results = redis_table_get(key)
    print(f"{results=}")

    return results
