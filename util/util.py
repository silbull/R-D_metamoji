#!/usr/bin/env python
# coding: utf-8
#
# [FILE] util.py
#
# [DESCRIPTION]
#  ユーティリティ関数を定義する
#

#
# [FUNCTION] getNoteId()
#
# [DESCRIPTION]
#  eYACHO/GEMBA NoteのノートリンクからノートIDを抽出する
#
# [INPUTS]
#  notelink - ノートリンク（例：https://mps-beta.metamoji.com/link/hsocl-4AynActJIV5e7gMQd5.mmjloc）
#
# [OUTPUTS] 
#  .mmjlocから前の/までの文字列を抽出する（例：hsocl-4AynActJIV5e7gMQd5）
#  スラッシュ(/)とピリオド(.)が含まれなければ、空文字列を返す
#
# [NOTES]
#
def getNoteId(notelink):
    # スラッシュで分割する
    splitString = notelink.split('/')
    if len(splitString) < 1:
        return ""

    # 最後のスラッシュからあとの文字列を取得
    splitString = splitString[len(splitString)-1]
    # ピリオドで分割
    splitString = splitString.split('.')
    if len(splitString) < 1:
        return ""
    
    return splitString[0]
#
# HISTORY
# [1] 2024-11-14 - Initial version
#