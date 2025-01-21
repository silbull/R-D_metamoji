#!/usr/bin/env python
#
# [FILE] util.py
#
# [DESCRIPTION]
#  ユーティリティ関数を定義する
#
def getNoteId(notelink):
    """eYACHO/GEMBA NoteのノートリンクからノートIDを抽出する

    Args:
        notelink (_type_): ノートリンク（例：https://mps-beta.metamoji.com/link/hsocl-4AynActJIV5e7gMQd5.mmjloc）

    Returns:
        _type_: .mmjlocから前の/までの文字列を抽出する（例：hsocl-4AynActJIV5e7gMQd5）
    """
    # スラッシュで分割する
    splitString = notelink.split("/")
    if len(splitString) < 1:
        return ""

    # 最後のスラッシュからあとの文字列を取得
    splitString = splitString[len(splitString) - 1]
    # ピリオドで分割
    splitString = splitString.split(".")
    if len(splitString) < 1:
        return ""

    return splitString[0]
