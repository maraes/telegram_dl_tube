import os
import asyncio
from telethon import TelegramClient, events
import yt_dlp
from fastapi import FastAPI
import uvicorn
from threading import Thread

# Configurações do Telegram
API_ID = int(os.environ.get("API_ID", 123456))
API_HASH = os.environ.get("API_HASH", "seu_api_hash_aqui")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "seu_bot_token_do_botfather")

# Inicializa o FastAPI (Para receber o ping do UptimeRobot)
app = FastAPI()

@app.get("/healthcheck")
def health_check():
    return {"status": "online", "message": "Bot está acordado!"}

# Inicializa o Telethon
bot = TelegramClient('video_downloader_bot', API_ID, API_HASH)

def download_video(url):
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'video_%(id)s.%(ext)s',
        'max_filesize': 2000 * 1024 * 1024,
        '--cookies-from-browser',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@bot.on(events.NewMessage(pattern=r'(https?://[^\s]+)'))
async def handle_url(event):
    url = event.pattern_match.group(1)
    status_msg = await event.reply("⚡ Processando o link... Aguarde.")
    
    loop = asyncio.get_event_loop()
    try:
        file_path = await loop.run_in_executor(None, download_video, url)
        await status_msg.edit("📤 Enviando o vídeo para o Telegram...")
        
        await bot.send_file(event.chat_id, file_path, caption="Aqui está seu vídeo! 🎬")
        
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit(f"❌ Erro ao processar o vídeo: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

# Função para rodar o Servidor Web em paralelo
def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Inicia o servidor web em uma thread separada
    Thread(target=run_web_server, daemon=True).start()
    
    # Inicia o bot do Telegram principal
    print("Bot e Servidor Web iniciados!")
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()
