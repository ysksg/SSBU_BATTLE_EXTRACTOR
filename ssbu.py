import argparse
import cv2
import subprocess
import sys
from argparse import ArgumentParser

# Installation
# $ pip3 install opencv-python

parser = argparse.ArgumentParser()
parser.add_argument('input_movie', help='元動画ファイル')
parser.add_argument('-st', '--start_template', type=str,
                    default='./template/start.png',
                    help='試合開始時を示すテンプレ画像')
parser.add_argument('-et', '--end_template', type=str,
                    default='./template/end.png',
                    help='試合終了時を示すテンプレ画像')
parser.add_argument('-c', '--codec', type=str,
                    default="-movflags +faststart -c:a aac -profile:a aac_low -ac 2 -ar 48000"
                    "-c:v h264_nvenc -vf yadif=0:-1:1 -profile:v high -bf 2 -g 30"
                    "-coder 1 -b:v 10M -b:a 384k -pix_fmt yuv420p",
                    help='抽出後の動画エンコードオプション。デフォルトはGPUエンコード & YouTubeの推奨設定済み(10Mbps)')
parser.add_argument('-i', '--interval', type=float,
                    default=1,
                    help='テンプレ画像との判定時間間隔(小さいほど高精度)')
parser.add_argument('-t', '--threshold', type=float,
                    default=0.7,
                    help='テンプレ画像との合致率閾値(1が完全一致, 0が完全不一致)')
parser.add_argument('-m', '--min_time', type=int,
                    default=120,
                    help='最小試合時間(大きくするほど処理高速、0に近いほど厳密な判定処理)')

args = parser.parse_args()

VIDEO_FILE = args.input_movie
START_TEMPLATE = args.start_template
END_TEMPLATE = args.end_template
ENC_OPTION = args.codec
MATCH_INTERVAL = args.interval
MIN_BATTLE_TIME = args.min_time
THRESHOLD = args.threshold

start_template = cv2.imread(START_TEMPLATE, 0)
end_template = cv2.imread(END_TEMPLATE, 0)


def match(img, tmp):
    grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 比較用にグレー画像を作る
    result = cv2.matchTemplate(grayimg, tmp, cv2.TM_CCOEFF_NORMED)

    # 0-1 1に近いほど似てる
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val


def save_match_frame(img, tmp, savefilename):
    # 検出結果から検出領域の位置を取得
    grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 比較用にグレー画像を作る
    result = cv2.matchTemplate(grayimg, tmp, cv2.TM_CCOEFF_NORMED)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    top_left = max_loc
    w, h = tmp.shape[::-1]
    bottom_right = (top_left[0] + w, top_left[1] + h)

    print(max_val, min_val)

    # 検出領域を四角で囲んで保存
    if(max_val >= THRESHOLD):
        cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 2)
        cv2.imwrite(savefilename, img)


def save_match_video(originfilename, start_time, end_time, savefilename):
    cmd = "ffmpeg -ss " + str(start_time) + " -i " + originfilename + \
        " -ss 0 -t " + str(end_time - start_time + 1) + " " + \
        ENC_OPTION + " " + savefilename
    subprocess.call(cmd, shell=True)


video = cv2.VideoCapture(VIDEO_FILE)

frame_count = int(video.get(7))  # 総フレーム数
frame_rate = int(video.get(5))  # フレームレート

battles = []

stime = 0
etime = 0
for i in range(int((frame_count / frame_rate)/MATCH_INTERVAL)):  # 指定した間隔秒(frame数)ごとに画像判定
    # 現在秒と試合開始時間との差が最小試合時間よりも小さい場合は、処理をスキップ
    if (stime > 0) & (i*MATCH_INTERVAL - stime < MIN_BATTLE_TIME):
        continue

    video.set(cv2.CAP_PROP_POS_FRAMES, frame_rate * MATCH_INTERVAL * i)
    _, frame = video.read()  # 動画をフレームに読み込み

    m1 = match(frame, start_template)

    if m1 >= THRESHOLD:  # 試合開始フレームに合致
        # save_match_frame(frame, start_template, "test" +
        #                  str(i*MATCH_INTERVAL) + ".png")

        if etime > stime:
            battles.append({"start": stime, "end": etime})
            print("[Found!] start: " + str(stime) + ", end: " + str(etime))

        stime = i * MATCH_INTERVAL
        continue

    m2 = match(frame, end_template)

    if m2 >= THRESHOLD:  # 試合終了フレームに合致 複数回合致する場合あり
        # save_match_frame(frame, end_template, "test" +
        #                  str(i*MATCH_INTERVAL) + ".png")
        etime = i*MATCH_INTERVAL

if etime > stime:
    battles.append({"start": stime, "end": etime})
    print("[Found!] start: " + str(stime) + ", end: " + str(etime))

for b in battles:
    save_match_video(
        VIDEO_FILE,                                         # 元動画ファイル
        b["start"],                                         # クリップ開始位置
        b["end"],                                           # クリップ終了位置
        VIDEO_FILE + "_battle_" + str(b["start"]) + ".mp4"    # 抽出後動画ファイル名
    )
