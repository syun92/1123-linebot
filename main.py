# 0J04029 制作実習Ⅱ第3期
from flask import Flask, request, abort
from pyowm.owm import OWM
from pyowm.utils import formatting
from pyowm.utils.config import get_default_config
import datetime, os, uvicorn
from linebot import LineBotApi, WebhookHandler
from linebot.v3.messaging import TextMessage
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage


app = Flask(__name__)

# PyOWMのコンフィグ設定
config_dict = get_default_config()
config_dict["language"] = "ja"  # 取得データの言語設定

# PyOWMライブラリの初期化
owm = OWM(os.getenv("API_KEY_OWM", config_dict))
mgr = owm.weather_manager()

# 英語から日本語への天気状態の対応表
weather_status_mapping = {
    "Clear": "晴れ",
    "Clouds": "曇り",
    "Rain": "雨",
    "Snow": "雪",
    "Thunderstorm": "雷雨",
    "Mist": "霧",
    # 天気状態に対する対応をここに追記
}


# 天気状態を日本語に変換する関数
def convert_japanese(weather_status):
    if weather_status in weather_status_mapping:
        return weather_status_mapping[weather_status]
    else:
        return weather_status


# チャンネルアクセストークン
line_bot_api = LineBotApi(os.getenv("API_KEY_LINEBOT_ACCESS"))

# シークレット
handler = WebhookHandler(os.getenv("API_KEY_LINEBOT_SECRET"))

"""
lini-bot-sdk-pythonのサンプルコードを使っています
ここから
"""


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


"""
lini-bot-sdk-pythonのサンプルコードを使っています
ここまで
"""


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # メッセージを小文字に変換し処理しやすくする
    user_message = event.message.text.lower()
    if user_message in ["西宮", "三田", "神戸", "大阪"]:
        if user_message == "西宮":
            observation = mgr.weather_at_place("Nishinomiya-hama,JP")
        elif user_message == "三田":
            observation = mgr.weather_at_place("Sandachō,JP")
        elif user_message == "神戸":
            observation = mgr.weather_at_place("Kobe,JP")
        elif user_message == "大阪":
            observation = mgr.weather_at_place("Osaka,JP")
        w = observation.weather
        # 日本時間に変換
        ref_time = datetime.datetime.fromtimestamp(w.reference_time()).astimezone(
            datetime.timezone(datetime.timedelta(hours=9))
        )
        # 日本時間に変換された天気を変数に入れる
        time_text = "気象データの計測日次時間: {}".format(formatting.to_date(ref_time))
        # 天気情報を日本語に変換するために関数で使う変数に入れる
        weather_status = w.status
        # convert_japanese関数を使って日本語に変換したものを変数に入れる
        weather_status_jp = convert_japanese(weather_status)
        weather_text = "天気: {}".format(weather_status_jp)
        detail_text = "天気詳細: {}".format(w.detailed_status)
        # 変数に気温情報を入れる
        temperature_data = w.temperature("celsius")
        # 各気温情報を日本語で出力するために一度変数に入れる
        temperature_text = "気温(℃): {:.2f}".format(temperature_data["temp"])
        temp_max_text = "最高気温(℃): {:.2f}".format(temperature_data["temp_max"])
        temp_min_text = "最低気温(℃): {:.2f}".format(temperature_data["temp_min"])
        feels_like_text = "体感気温(℃): {:.2f}".format(temperature_data["feels_like"])
        # 複数メッセージを入力するための出力
        line_bot_api.reply_message(
            event.reply_token,
            # 一度に5つまでしか送れない
            [
                TextSendMessage(time_text),
                TextSendMessage(weather_text),
                # TextSendMessage(detail_text),
                TextSendMessage(temperature_text),
                TextSendMessage(temp_max_text),
                TextSendMessage(temp_min_text),
                # TextSendMessage(feels_like_text),
            ],
        )

    else:
        reply_text = "大阪、神戸、三田、西宮の内知りたい天気を入力してください。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
