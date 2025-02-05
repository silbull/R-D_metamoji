# api/routers/routers.py  # noqa: INP001

from fastapi import APIRouter

from api.endpoints.detect import detect_objects, get_detected_boxes, get_detected_image, get_segmented_image, segment_anything
from api.endpoints.text import extract_tables, extract_text, get_table, get_text

text_router = APIRouter()  # prefix="/text", tags=["text"])
object_detection_router = APIRouter()  # prefix="/detect", tags=["detect"])


# テキスト抽出のエンドポイント
@text_router.post("/rest/extract_text")
async def post_extract_text(json_data: dict):
    return await extract_text(json_data)


# テキスト取得のエンドポイント
@text_router.post("/rest/get_text")
async def post_get_text(json_data: dict):
    return get_text(json_data)


# 表データ抽出のエンドポイント
@text_router.post("/rest/extract_table")
async def post_extract_table(json_data: dict):
    return await extract_tables(json_data)

# 表データ取得のエンドポイント
@text_router.post("/rest/get_table")
async def post_get_table(json_data: dict):
    return get_table(json_data)


# 物体検出のエンドポイント
@object_detection_router.post("/rest/detect_objects")
async def post_detect_objects(json_data: dict):
    return detect_objects(json_data)


# 物体検出領域結果取得のエンドポイント
@object_detection_router.post("/rest/detected_boxes")
async def post_get_detected_boxes(json_data: dict):
    return get_detected_boxes(json_data)

# 物体検出画像取得のエンドポイント
@object_detection_router.post("/rest/detected_image")
async def post_get_detected_image(json_data: dict):
    return get_detected_image(json_data)

# 物体セグメンテーション(SAM)実行のエンドポイント
@object_detection_router.post("/rest/segment_anything")
async def post_segment_anything(json_data: dict):
    return await segment_anything(json_data)

# 物体セグメンテーション結果取得のエンドポイント
@object_detection_router.post("/rest/get_segmented_image")
async def post_get_segmented_image(json_data: dict):
    return get_segmented_image(json_data)
