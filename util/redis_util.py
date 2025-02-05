#!/usr/bin/env python
#
# [FILE] redis_util.py
#
# [DESCRIPTION]
#  REDISに関わるメソッドを定義する
#
import base64
import json
import os
import sys

import redis
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

# REDISホスト名を取得
redis_host = os.environ.get("REDIS_HOST")
if redis_host is None:
    print("環境変数REDIS_HOSTが設定されていません")
    sys.exit()

# REDISポート番号を取得
redis_port = os.environ.get("REDIS_PORT")
if redis_port is None:
    print("環境変数REDIS_PORTが設定されていません")
    sys.exit()

# REDISキーの有効期限を取得
redis_duration = os.environ.get("REDIS_EXPIRE")
if redis_duration is None:
    print("環境変数REDIS_EXPIREが設定されていません")
    redis_duration = 60
else:
    redis_duration = int(redis_duration)

# REDISに接続する
r_client = redis.Redis(host=redis_host, port=redis_port, db=0)
print("Connected REDIS")

# ==================================================================================================
# 表データ系のREDIS処理
# ==================================================================================================


def redis_table_put(key, table) -> bool:
    """テーブルデータをREDISに格納する

    Args:
        key (_type_): REDISに格納するときのキー
        table (_type_): テーブルデータ（JSON形式）

    Returns:
        bool: True - REDISへの格納が成功、False - 失敗
    """
    Status = True
    # REDISにテーブルを格納
    try:
        r_client.hset(key, "table", json.dumps(table, ensure_ascii=False, indent=2))
        r_client.expire(key, redis_duration)  # 有効期限を設定する
    except Exception as e:
        print(e)
        Status = False

    return Status


def redis_table_get(key) -> dict:
    """REDISからテーブルデータを取得する

    Args:
        key (_type_): REDISに格納されたキー

    Returns:
        dict: テーブルデータ（JSON形式）
    """
    json_string = r_client.hget(key, "table")
    if json_string is None:
        return {"message": "テーブルはありません"}

    table = json.loads(json_string)

    table["message"] = "表を読み込みました"
    return table


# ==================================================================================================
# 物体検出系のREDIS処理
# ==================================================================================================


def redis_iamge_get(key) -> dict:
    """物体を検出した画像データを取得する

    Args:
        key (_type_): REDISに格納されたキー

    Returns:
        dict: 認識結果画像（JSON形式）
        {'keys': ['outputImage'],
         'records': [{'outputImage':<String of image>}],
         'message': <コメント>}
    """
    results = {}
    results["message"] = "検出画像はありません"

    # REDISから画像を取得する
    image_string = r_client.hget(key, "image")
    if image_string is None:
        return results

    results = {}
    results["keys"] = ["outputImage"]
    output_image_list = []
    element = {"outputImage": image_string}
    output_image_list.append(element)
    results["records"] = output_image_list
    results["message"] = None

    return results


def redis_box_get(key):
    """物体検出結果を取得する

     Args:
         key (_type_): REDISに格納されたキー

     Returns:
         _type_: 物体が検出された領域（JSON形式）

          {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
    'records': [
        {'objName':<Detected Name>,
         'probability':<Percentage>,
         'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156},
        ...],
    'message': <コメント>}
    """

    init_val = {}
    init_val["message"] = "検出結果がありません"

    # REDISから物体検出情報を取得する
    json_string = r_client.hget(key, "boxes")
    if json_string is None:
        return init_val

    # 文字列をJSON構造に変換する
    boxes = json.loads(json_string)
    return boxes


def redis_image_put(key, output_image_file, detected_boxes) -> bool:
    """検出された画像データと検出結果をREDISに格納する

    NOTE: REDISへは、ハッシュとしてimageキーとboxesキーを有効期限付きで格納する

    Args:
        key (_type_): REDISに格納するときのキー
        output_image_file (_type_): 出力画像ファイル名
        detected_boxes (_type_): 物体が検出された領域（JSON形式）
        {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
            'records': [
                {'objName':<Detected Name>,
                'probability':<Percentage>,
                'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156},
                ...],
            'message': <コメント>}

    Returns:
        _type_: True - REDISへの格納が成功、False - 失敗
    """
    Status = True
    # Base64文字列に変換する
    with open(output_image_file, "rb") as image_file:
        data = base64.b64encode(image_file.read())

    img_text = "data:image/jpeg;base64," + data.decode("utf-8")

    # REDISにハッシュとして格納
    try:
        r_client.hset(key, "image", img_text)
        r_client.hset(key, "boxes", json.dumps(detected_boxes))
        r_client.expire(key, redis_duration)  # 有効期限を設定する
    except Exception as e:
        print(e)
        Status = False

    return Status


# ==================================================================================================
# テキスト抽出系のREDIS処理
# ==================================================================================================


def redis_text_put(key, text) -> bool:
    """抽出したテキストをREDISに格納する

    Args:
        key (_type_): REDISに格納するときのキー
        text (_type_): 抽出したテキスト

    Returns:
        bool: True - REDISへの格納が成功、False - 失敗
    """
    Status = True
    # REDISにテキストを格納
    try:
        r_client.hset(key, "text", text)
        r_client.expire(key, redis_duration)  # 有効期限を設定する
    except Exception as e:
        print(e)
        Status = False

    return Status


def redis_text_get(key) -> dict:
    """抽出したテキストを取得する

    Args:
        key (_type_): REDISに格納されたキー

    Returns:
        dict: 抽出したテキストを含むJSON形式
    """
    # REDISからテキストを取得する
    text = r_client.hget(key, "text")
    if text is None:
        return {"outputText": "テキストはありません"}

    # この形式がeyachoのAPIのレスポンスとなる
    # keysには，eYaChoで定義したタグのプロパティ名（自分が出力箇所にリンクさせたタグ）を入れる
    # recordsには，先ほどのkeysとその出力箇所に入れたい値をdict形式で入れる
    result = {}
    result["keys"] = ["outputText"]
    result["records"] = [{"outputText": text.decode("utf-8")}]
    result["message"] = None

    # print("Extracted Text:", text)

    return result
