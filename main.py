import os
import asyncio
from telethon import TelegramClient, events
import yt_dlp

# Configurações das APIs do Telegram (Obtenha em my.telegram.org)
API_ID = int(os.environ.get("API_ID", 123456))  # Insira seu API ID ou use var de ambiente
API_HASH = os.environ.get("API_HASH", "seu_api_hash_aqui")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "seu_bot_token_do_botfather")

bot = TelegramClient('video_downloader_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def download_video(url):
    """Baixa o vídeo usando yt-dlp e retorna o nome do arquivo criado."""
    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # Garante formato MP4 compatível com Telegram
        'outtmpl': 'video_%(id)s.%(ext)s', # Nome temporário do arquivo
        'max_filesize': 2000 * 1024 * 1024, # Limite do Telegram (2GB)
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@bot.on(events.NewMessage(pattern=r'(https?://[^\s]+)'))
async def handle_url(event):
    url = event.pattern_match.group(1)
    status_msg = await event.reply("⚡ Processando o link... Aguarde.")
    
    # Executa o download em uma thread separada para não travar o bot
    loop = asyncio.get_event_loop()
    try:
        file_path = await loop.run_in_executor(None, download_video, url)
        
        await status_msg.edit("📤 Enviando o vídeo para o Telegram...")
        # Envia o arquivo baixado
        await bot.send_file(event.chat_id, file_path, caption="Aqui está seu vídeo! 🎬")
        
        # Deleta o vídeo do servidor para não estourar o espaço em disco
        if os.path.exists(file_path):
            os.remove(file_path)
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit(f"❌ Erro ao processar o vídeo: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

print("Bot iniciado com sucesso!")
bot.run_until_disconnected()