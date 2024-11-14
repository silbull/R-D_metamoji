#!/usr/bin/env python
# coding: utf-8
#
# [FILE] yolo_detect.py
#
# [DESCRIPTION]
#   ImageAIを用いた物体検出に関わるメソッドを定義する
#
from imageai.Detection import ObjectDetection

#
# [FUNCTION] yoloDetectObjects()
#
# [DESCRIPTION]
#  YOLOモデルを用いて物体を検出する
#
# [INPUTS]
#  inputImageFile - 入力画像ファイル名
#  outputImageFile - 出力画像ファイル名
#  modelFile - YOLOモデルファイル名
#
# [OUTPUTS]
#  {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
#   'records': [
#       {'objName':<Detected Name>, 
#        'probability':<Percentage>, 
#        'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
#       ...],
#   'message': <コメント>}
#
# [NOTES]
#
def yoloDetectObjects(inputImageFile, outputImageFile, modelFile):
    detector = ObjectDetection()
    detector.setModelTypeAsYOLOv3()
    detector.setModelPath(modelFile)
    detector.loadModel()

    detections = detector.detectObjectsFromImage(input_image=inputImageFile, output_image_path=outputImageFile)

    results = {}
    results['keys'] = ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY']
    list = []
    
    # 検出した対象物、認識精度、位置を抽出してJSONを構成する
    for eachObject in detections:
        name = eachObject["name"]
        prob = eachObject["percentage_probability"]
        box  = eachObject["box_points"]
        elements = {'objName': name, 'probability': prob, 'topX': box[0], 'topY': box[1], 'bottomX': box[2], 'bottomY': box[3]}
        print("Detected:", elements)
        list.append(elements)

    results['records'] = list
    msg = "検出できません"
    if len(list) > 0:
        msg = "送信終了"
    results['message'] = msg

    return results

#
# HISTORY
# [1] 2024-11-14 - Initial version
#