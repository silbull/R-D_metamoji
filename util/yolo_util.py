#!/usr/bin/env python
#
# [FILE] yolo_detect.py
#
# [DESCRIPTION]
#   ImageAIを用いた物体検出に関わるメソッドを定義する
# 0
from imageai.Detection import ObjectDetection


def yolo_detect_objects(source_image_path, output_image_path, model_file):
    """物体検出を行う

    Args:
        inputImageFile (_type_): 入力画像ファイルpath
        outputImageFile (_type_): 出力画像ファイルpath
        modelFile (_type_): YOLOモデルファイル

    Returns:
        _type_: 物体が検出された領域（JSON形式）

    NOTE: output_image_pathには検出結果を描画した画像が保存されるが，detectionsには検出結果（JSON）が格納される
    """
    detector = ObjectDetection()
    detector.setModelTypeAsYOLOv3()
    detector.setModelPath(model_file)
    detector.loadModel()

    detections = detector.detectObjectsFromImage(input_image=source_image_path, output_image_path=output_image_path)

    results = {}
    results["keys"] = ["objName", "probability", "topX", "topY", "bottomX", "bottomY"]
    detected_objects = []

    # 検出した対象物、認識精度、位置を抽出してJSONを構成する
    for each_object in detections:
        name = each_object["name"]
        prob = each_object["percentage_probability"]
        box = each_object["box_points"]
        elements = {"objName": name, "probability": prob, "topX": box[0], "topY": box[1], "bottomX": box[2], "bottomY": box[3]}
        print("Detected:", elements)
        detected_objects.append(elements)

    results["records"] = detected_objects # 検出結果のリスト
    msg = "検出できません"
    if len(detected_objects) > 0:
        msg = "送信終了"
    results["message"] = msg

    return results
