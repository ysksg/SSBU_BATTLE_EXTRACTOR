# 使い方

## ffmpegをインストール
* サイトからffmpegのexeをダウンロード
* 任意のフォルダに保存
* ダウンロードしたexeのPATHを通す

## Pythonのインストール
* Python3系をインストール
  https://www.python.org/downloads/

## Pythonライブラリのインストール
* コマンドプロンプト起動
* 以下コマンド実行
  > pip3 install opencv-python tqdm

## 実行方法
* python ssbu.py <抽出したい動画ファイル>
  * python ssbu.py -h とすると押すとヘルプ出るよ

## どういう仕組み？
* 指定した時間秒ごとに動画のフレームを抽出
* 抽出したフレームが、指定した「試合開始テンプレ画像」と「試合終了テンプレ画像」に合致するとその間を動画化
* 元動画をffmpegでエンコード。GPUエンコードでYouTubeの推奨設定済み(10Mbps)
* 詳細はウンコード参照

