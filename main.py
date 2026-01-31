import os
import requests
import time

# --- CONFIGURATION ---
# Folder jahan animals ki images/videos hongi
CONTENT_FOLDER = "content/wildsnap"

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_WILDSNAP')
WEBHOOK_URL = os.getenv('WEBHOOK_WILDSNAP')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# SEO Caption
CAPTION = "🦁 Into the Wild. \n\n#WildSnap #Wildlife #NaturePhotography #AnimalPlanet #WildAnimals #NatureLovers"

def get_file():
    """Folder se pehli file uthata hai"""
    if not os.path.exists(CONTENT_FOLDER):
        print(f"❌ Folder nahi mila: {CONTENT_FOLDER}")
        return None
    
    # Hidden files ignore karein
    files = [f for f in sorted(os.listdir(CONTENT_FOLDER)) if not f.startswith('.')]
    
    if not files:
        print("⚠️ Folder khali hai! Koi content nahi bacha.")
        return None

    return os.path.join(CONTENT_FOLDER, files[0])

def upload_with_retry(file_path):
    """Catbox Upload with Retry Logic"""
    url = "https://catbox.moe/user/api.php"
    for attempt in range(1, 4):
        try:
            print(f"🚀 Uploading (Attempt {attempt})...")
            with open(file_path, 'rb') as f:
                r = requests.post(url, data={'reqtype': 'fileupload'}, files={'fileToUpload': f}, timeout=30 * attempt)
                if "http" in r.text: return r.text
        except Exception as e:
            print(f"⚠️ Fail: {e}")
            time.sleep(5)
    return None

def main():
    # 1. File Uthao
    file_path = get_file()
    if not file_path: return

    print(f"📂 Processing: {file_path}")

    # 2. Upload karo
    url = upload_with_retry(file_path)
    
    if url:
        print(f"✅ SUCCESS: {url}")
        
        # 3. Telegram Send (Photo vs Video check)
        if TELEGRAM_TOKEN and CHAT_ID:
            is_video = file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
            method = "sendVideo" if is_video else "sendPhoto"
            media_key = "video" if is_video else "photo"
            
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}", 
                         json={"chat_id": CHAT_ID, media_key: url, "caption": CAPTION})
        
        # 4. Webhook Send
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"content": f"{CAPTION}\n{url}"})

        # 5. DELETE FILE (Important)
        try:
            os.remove(file_path)
            print("🗑️ File deleted from repo.")
        except Exception as e:
            print(f"❌ Deletion failed: {e}")

    else:
        print("❌ Upload failed.")

if __name__ == "__main__":
    main()
