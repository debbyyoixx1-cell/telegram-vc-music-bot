# 🎧 Telegram Voice Chat Music Bot

Pyrogram + PyTgCalls သုံးထားတဲ့ group voice chat music bot။ YouTube ကနေ သီချင်းရှာ/ဒေါင်းပြီး voice chat ထဲမှာ ဖွင့်ပေးတယ်။

## ⚠️ အရေးကြီး — Security

သင် chat ထဲမှာ ပေးလိုက်တဲ့ **Bot Token နဲ့ API_HASH ကို ချက်ချင်း ပြောင်းပါ**:
- BotFather → `/revoke` → token အသစ်ယူပါ
- token/hash တွေကို code ထဲ ဘယ်တော့မှ မထည့်ပါနဲ့။ Host ရဲ့ **Environment Variables** မှာပဲ ထည့်ပါ။

## Commands

| Command | အလုပ် |
|---|---|
| `/play <name or link>` | Voice chat ထဲ ဖွင့်မယ် |
| `/pause` `/resume` | ခဏရပ် / ပြန်ဖွင့် |
| `/skip` | နောက်သီချင်း |
| `/queue` `/now` | စာရင်း / အခုဖွင့်နေတာ |
| `/stop` | ရပ်ပြီး voice chat ကထွက် |
| `/ping` `/id` | စစ်ဆေးရန် |

## Setup (အဆင့်ဆင့်)

### 1. SESSION_STRING ထုတ်ပါ
Voice chat ထဲ ဝင်ဖို့ **bot နဲ့မရဘူး၊ user account (assistant) လိုတယ်**။ ကိုယ့်စက်မှာ:

```bash
pip install pyrogram tgcrypto
python generate_session.py
```

ထွက်လာတဲ့ string ကို `SESSION_STRING` အဖြစ်သိမ်းပါ။ အဲဒီ account ကို group ထဲ ထည့်ပေးပါ။

### 2. GitHub တင်ပါ
`bot/` folder ထဲက file တွေအားလုံးကို repo အသစ်တစ်ခုမှာ တင်ပါ (`.env` မတင်ရ)။

```bash
git init && git add . && git commit -m "music bot"
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 3. 24/7 Free Deploy — Koyeb (အကြံပြု)
1. https://koyeb.com → GitHub နဲ့ sign up
2. **Create Service → GitHub → repo ရွေး**
3. Builder: **Dockerfile**
4. Environment variables ထည့်ပါ: `API_ID`, `API_HASH`, `BOT_TOKEN`, `SESSION_STRING`, `OWNER_ID`, `LOG_CHAT_ID`
5. Instance: **Free (nano)** → Deploy

Koyeb free instance က sleep မဝင်လို့ 24/7 run နိုင်တယ်။ Health endpoint `/` ပါပြီးသား။

> Render free web service သုံးရင်လည်းရတယ် (Docker) — ဒါပေမဲ့ 15 မိနစ် idle ဆို sleep ဝင်တတ်လို့ UptimeRobot နဲ့ 5 မိနစ်တစ်ခါ `/health` ping ပေးပါ။

### 4. Group ပြင်ဆင်ချက်
- Bot ကို group ထဲထည့်ပြီး **admin** ပေးပါ (Manage voice chats + Invite users)
- Assistant account ကိုလည်း group ထဲထည့်ပါ
- Voice chat ကို အရင်ဖွင့်ထားပါ → ပြီးရင် `/play ...`

## Local run

```bash
cp .env.example .env   # တန်ဖိုးတွေဖြည့်ပါ
pip install -r requirements.txt
sudo apt install ffmpeg
python main.py
```
