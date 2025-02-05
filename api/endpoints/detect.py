import base64
import os
import sys
import time

import aiofiles
from dotenv import load_dotenv
from ultralytics import SAM, YOLO

from util.redis_util import redis_box_get, redis_iamge_get, redis_image_put
from util.util import getNoteId, is_reload_enabled
from util.yolo_util import yolo_detect_objects

load_dotenv()

# ローカルフォルダー
local_folder = os.environ.get("LOCAL_FOLDER")
if local_folder is None:
    print("環境変数LOCAL_FOLDERが設定されていません")
    sys.exit()

# YOLOモデルファイル
yolo_model_file = os.environ.get("YOLO_MODEL_FILE")
sam_model_file = os.environ.get("SAM_MODEL_FILE")

# ==================================================================================================
# 物体検出処理
# ==================================================================================================


def detect_objects(json_data: dict):
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

    # Base64文字列をdecodeし中身を取り出す
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

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページID(ページで固有)から生成する
    key = note_id + "-" + json_data["_pageId"]
    if is_reload_enabled():
        print("[DETECTED]", detected)
        print("[REDIS KEY]", key)
    os.remove(file_path)

    if len(detected["records"]) < 1:
        results["message"] = "何も検出されませんでした"
        return results

    # 生成した画像と認識結果を登録する
    status = redis_image_put(key, annotated_image_path, detected)
    os.remove(annotated_image_path)

    if status is False:
        results["message"] = "検出結果がありません"
        return results

    return detected


# ==================================================================================================
# 物体検出結果取得処理
# ==================================================================================================
def get_detected_boxes(json_data: dict) -> dict:
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
    results = redis_box_get(key)

    return results


# ==================================================================================================
# 物体検出画像取得処理
# ==================================================================================================
def get_detected_image(json_data: dict):
    if is_reload_enabled():
        print("[JSON for detected_results]", json_data)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    noteId = getNoteId(json_data["_NOTE_LINK"])
    key = noteId + "-" + json_data["_PAGE_ID"]
    results = redis_iamge_get(key)  # 画像データを取得する

    print("[REDIS IMAGE]", results)
    print(type(results))

    return results


# ==================================================================================================
# 物体セグメンテーション処理
# ==================================================================================================
async def segment_anything(json_data: dict):
    """eYACHO/GEMBA Noteから送信されてきた画像情報をファイルに保存し、SAMを実行する

    Args:
        json_data (dict): クライアント（eYACHO/GEMBA Note）からの画像情報
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
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(img_binary)
    except OSError as e:
        print(e)
        return results

    if is_reload_enabled():
        print("[SAVED]", file_path)

    # SAMを実行する
    annotated_image_path = local_folder + "/segmented-" + filename
    model = SAM(sam_model_file)
    sam_results = model.predict(file_path, save=False)
    for result in sam_results:
        # print(result.verbose())
        result.save(annotated_image_path, boxes=False, labels=False)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページID(ページで固有)から生成する
    key = note_id + "-" + json_data["_pageId"]
    if is_reload_enabled():
        print("[REDIS KEY]", key)
    os.remove(file_path)

    # 生成した画像と認識結果を登録する
    status = redis_image_put(key, annotated_image_path, results)
    os.remove(annotated_image_path)

    if status is False:
        results["message"] = "セグメンテーション結果がありません"
        return results
    else:
        results["message"] = "セグメンテーションが完了しました"

    return results


# ==================================================================================================
# 物体セグメンテーション結果取得処理
# ==================================================================================================
def get_segmented_image(json_data: dict):
    if is_reload_enabled():
        print("[JSON for detected_results]", json_data)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    noteId = getNoteId(json_data["_NOTE_LINK"])
    key = noteId + "-" + json_data["_PAGE_ID"]
    results = redis_iamge_get(key)  # 画像データを取得する

    if is_reload_enabled():
        print("[REDIS IMAGE]", results)
        print(type(results))

    return results
