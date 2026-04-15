# LINE 韓幣轉台幣機器人

這是一個用 Python 製作的 LINE Bot。把 Bot 加進指定群組後，成員只要輸入韓幣金額，例如 `10000 krw`，機器人就會用 Flex Message 卡片回覆換算後的台幣金額。

## 功能

- 驗證 LINE Webhook 簽章
- 只允許指定群組使用
- 將 `KRW` 即時換算成 `TWD`
- 使用 Flex Message 卡片呈現結果
- 支援簡單輸入格式，例如 `10000 krw`、`krw 25000`

## 專案檔案

- `app.py`: LINE Webhook、Flex Message 與匯率換算主程式
- `core.py`: 訊息解析與簽章驗證邏輯
- `test_app.py`: 基本單元測試
- `.env.example`: 環境變數範例
- `requirements.txt`: 套件需求

## 安裝

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 環境變數

至少要設定以下內容:

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `ALLOWED_GROUP_ID`

`ALLOWED_GROUP_ID` 用來限制只有指定 LINE 群組可以使用這個換匯工具。

## 啟動

```powershell
$env:LINE_CHANNEL_ACCESS_TOKEN="你的 access token"
$env:LINE_CHANNEL_SECRET="你的 channel secret"
$env:ALLOWED_GROUP_ID="你的 group id"
py app.py
```

Webhook URL:

```text
https://你的網域/callback
```

本機開發可以先用 ngrok 或 Cloudflare Tunnel 暴露出 HTTPS 網址，再貼到 LINE Developers Console。

## LINE 群組中的呈現方式

群組成員輸入:

```text
10000 krw
krw 25000
```

Bot 會回覆一張 Flex Message 卡片，內容包含:

- 韓幣金額
- 換算後的台幣金額
- 即時參考匯率
- 匯率更新時間
- 兩個快速換算按鈕

輸入格式不正確時，Bot 會回覆文字提示，並附上快捷輸入按鈕。

## 如何拿到指定群組的 `groupId`

先把 Bot 加入目標群組，然後暫時不要填 `ALLOWED_GROUP_ID`。當群組有人傳訊息給 Bot 時，LINE Webhook 的 `source.groupId` 就會出現在事件資料裡。拿到正確的 `groupId` 後，再填回環境變數即可。

## 測試

```powershell
py -m unittest
```

## 建議部署

- Render
- Railway
- Zeabur
- 自己的 Windows / Linux VPS

## 部署到 Render

1. 把這個專案上傳到 GitHub
2. 登入 [Render](https://render.com/)
3. 選 `New +`
4. 選 `Blueprint`
5. 連接你的 GitHub repository
6. Render 會讀到專案裡的 `render.yaml`
7. 建立完成後，到 Render 的環境變數頁面補上：

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `ALLOWED_GROUP_ID`

如果你還沒先鎖定群組，`ALLOWED_GROUP_ID` 可以先留空，等抓到 groupId 後再補。

## Render 上線後要做的事

部署成功後，你會拿到一個公開網址，例如：

```text
https://line-krw-twd-bot.onrender.com
```

把 LINE 的 `Webhook URL` 設成：

```text
https://line-krw-twd-bot.onrender.com/callback
```

接著回到 LINE Developers Console：

1. 貼上 `Webhook URL`
2. 啟用 Webhook
3. 驗證成功後，把 Bot 加進 LINE 群組

## 第一次綁定群組的建議流程

1. 先部署 Render
2. 先不要填 `ALLOWED_GROUP_ID`
3. 把 Bot 加進目標群組
4. 在群組輸入一次 `10000 krw`
5. 等你確認 Bot 已正常回應後，再決定要不要加上群組白名單限制

如果你要，我下一步可以直接幫你整理成「Render 從 GitHub 建立服務」的超短操作清單。
