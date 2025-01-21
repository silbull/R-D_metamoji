import base64
import os
import subprocess
import sys
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from extract_text import extract_text
from util.redis_util import redis_text_get, redis_text_put, redisBoxGet, redisImageGet, redisImagePut
from util.util import getNoteId
from yolo_detect import yolo_detect_objects


def start_redis_with_docker():
    # Docker コマンドで Redis コンテナを起動
    command = ["docker", "run", "--rm", "-d", "--name", "redis-server", "-p", "6379:6379", "redis:latest"]
    subprocess.run(command, check=False)
    print("Redis server started with Docker")


# .envファイルの内容を読み込見込む
load_dotenv()

# ローカルフォルダー
local_folder = os.environ.get("LOCAL_FOLDER")
if local_folder is None:
    print("環境変数LOCAL_FOLDERが設定されていません")
    sys.exit()

# YOLOモデルファイル
yolo_model_file = os.environ.get("YOLO_MODEL_FILE")
if yolo_model_file is None:
    print("環境変数YOLO_MODEL_FILEが設定されていません")
    sys.exit()
else:
    print("[MODEL FILE]", yolo_model_file)

app = FastAPI()
app.mount(path="/static", app=StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
start_redis_with_docker()


def is_reload_enabled():
    """実行するコマンドに--reloadが含まれるか判定する

    Note:
        Trueの場合はデバッグ実行とみなし、JSONデータをコンソール上に表示する

    Returns:
        bool: True: 含まれる False: 含まれない
    """
    return "--reload" in sys.argv


@app.get("/", response_class=HTMLResponse)
async def top_page(request: Request):
    """トップページを開く

    Args:
        request (Request): リクエスト

    Returns:
        _type_: テンプレートレスポンスを返す
    """

    return templates.TemplateResponse("top.html", {"request": request, "title": "YOLO REST Server"})


@app.post("/rest/extract_text")
def post_extract_text(json_data: dict):
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
    pdf_binary = base64.b64decode(split_string[1])

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
        with open(file_path, "wb") as f:
            f.write(pdf_binary)
    except OSError as e:
        print(e)
        return results

    if is_reload_enabled():
        print("[SAVED]", file_path)

    # PDFファイルからテキストを抽出する
    extracted_text = extract_text(file_path)

    print(f"{extracted_text=}")

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    key = note_id + "-" + json_data["_pageId"]
    os.remove(file_path)

    status = redis_text_put(key, extracted_text)

    if status is False:
        results["message"] = "テキストが抽出されませんでした"
        return results

    return {"message": "テキストが抽出されました"}


@app.post("/rest/get_text")
def get_text(json_data: dict):
    """抽出したテキストを取得する

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
    results = redis_text_get(key)
    print(f"{results=}")

    return results


@app.post("/rest/detect_objects")
def post_detect_objects(json_data: dict):
    """eYACHO/GEMBA Noteから送信されてきた画像情報をファイルに保存し、YOLOの物体検出を実行する

    Args:
        json_data (dict): クライアント（eYACHO/GEMBA Note）からの画像情報

    Returns:
        _type_: 物体が検出された領域（JSON形式）
    """
    results = {}
    results["message"] = "不明なエラーが発生しました"

    if ("inputImage" in json_data) is False:
        results["message"] = "入力画像が設定されていません"
        return results

    # Base64文字列をバイナリファイルに保存
    split_string = json_data["inputImage"].split(",")
    print("[SPLIT]", split_string)
    img_binary = base64.b64decode(split_string[1])

    # ファイル拡張子を取得
    split_string = split_string[0].split("/")  # data:image/jpeg;base64
    extension = split_string[1].split(";")  # jpeg;base64

    # 保存する画像ファイル名を準備する
    note_id = getNoteId(json_data["_noteLink"])
    filename = note_id + "-" + str(time.strftime("%Y%m%d%H%M%S")) + "." + extension[0]
    file_path = local_folder + "/" + filename

    # 画像ファイルを保存
    try:
        with open(file_path, "wb") as f:
            f.write(img_binary)
    except OSError as e:
        print(e)
        return results

    if is_reload_enabled():
        print("[SAVED]", file_path)

    # 物体を検出する
    annotated_image_path = local_folder + "/detected-" + filename
    detected = yolo_detect_objects(file_path, annotated_image_path, yolo_model_file)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    key = note_id + "-" + json_data["_pageId"]
    if is_reload_enabled():
        print("[DETECTED]", detected)
        print("[REDIS KEY]", key)
    os.remove(file_path)

    if len(detected["records"]) < 1:
        results["message"] = "何も検出されませんでした"
        return results

    # 生成した画像と認識結果を登録する
    status = redisImagePut(key, annotated_image_path, detected)
    os.remove(annotated_image_path)

    if status is False:
        results["message"] = "検出結果がありません"
        return results

    return detected


@app.post("/rest/detected_boxes")
def postDetectedBoxes(json_data: dict) -> dict:
    """検出された物体の名称と認識領域を取得する

    Args:
        json_data (dict): クライアント（eYACHO/GEMBA Note）からの情報

    Returns:
        dict: 物体が検出された領域（JSON形式）

    [NOTES]
    eYACHO/GEMBA Noteのボタンアクション「アグリゲーションで更新」や「アグリゲーション結果を反映」から実行する
    """
    if is_reload_enabled():
        print("[JSON for detected_results]", json_data)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    noteId = getNoteId(json_data["_NOTE_LINK"])
    key = noteId + "-" + json_data["_PAGE_ID"]
    results = redisBoxGet(key)

    return results


#
# HISTORY
# [1] 2024-11-14 - Initial version
#

#
# POST Method
# End Point: /rest/detected_image
#
# [DESCRIPTION]
#  /rest/detect_objectsで生成された検出画像を取得する。
#
# [INPUTS]
#   request - bodyにクライアント（eYACHO/GEMBA Note）からの情報が格納されている
#    {..., "_NOTE_LINK": <ノートリンク>, "_PAGE_ID": <ページID>, ...}
#
# [OUTPUTS]
#  認識結果画像（JSON形式）：
#  {'keys': ['outputImage'],
#   'records': [{'outputImage':<String of image>}],
#   'message': <コメント>}
#
# [NOTES]
#   eYACHO/GEMBA Noteのボタンコマンド「アグリゲーション結果を反映」で実行する
#


@app.post("/rest/detected_image")
def postDetectedImage(json_data: dict):
    if is_reload_enabled():
        print("[JSON for detected_results]", json_data)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    noteId = getNoteId(json_data["_NOTE_LINK"])
    key = noteId + "-" + json_data["_PAGE_ID"]
    results = redisImageGet(key)  # 画像データを取得する

    print("[REDIS IMAGE]", results)
    print(type(results))

    return results
