import os
import requests
import time
import sys  # FIX 1: System exit codes ke liye zaroori

# --- CONFIGURATION ---
CONTENT_FOLDER = "content/wildsnap"

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_WILDSNAP')
WEBHOOK_URL = os.getenv('WEBHOOK_WILDSNAP')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

CAPTION = "🦁 Into the Wild. \n\n#WildSnap #Wildlife #NaturePhotography #AnimalPlanet #WildAnimals #NatureLovers"

# Allowed extensions filter karne ke liye (FIX 2)
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.avi', '.mkv')

def get_file():
    """Folder se pehli VALID media file uthata hai"""
    if not os.path.exists(CONTENT_FOLDER):
        print(f"❌ Folder nahi mila: {CONTENT_FOLDER}")
        return None
    
    # FIX 2: Sirf images/videos ko select karein, text files ignore karein
    files = [
        f for f in sorted(os.listdir(CONTENT_FOLDER)) 
        if not f.startswith('.') and f.lower().endswith(VALID_EXTENSIONS)
    ]
    
    if not files:
        print("⚠️ Folder khali hai ya koi valid media nahi bacha!")
        return None

    return os.path.join(CONTENT_FOLDER, files[0])

def upload_with_retry(file_path):
    """Catbox Upload with Retry Logic"""
    url = "https://catbox.moe/user/api.php"
    for attempt in range(1, 4):
        try:
            print(f"🚀 Uploading (Attempt {attempt})...")
            with open(file_path, 'rb') as f:
                r = requests.post(
                    url, 
                    data={'reqtype': 'fileupload'}, 
                    files={'fileToUpload': f}, 
                    timeout=60  # Timeout badhaya badi files ke liye
                )
                if r.status_code == 200 and "http" in r.text:
                    return r.text.strip() # Whitespace remove karein
                else:
                    print(f"⚠️ Server Response: {r.text}")
        except Exception as e:
            print(f"⚠️ Fail: {e}")
            time.sleep(5)
    return None

def main():
    # 0. Check Secrets (Debugging ke liye)
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Error: TELEGRAM_TOKEN or CHAT_ID is missing in Secrets!")
        sys.exit(1) # Action Fail karein

    # 1. File Uthao
    file_path = get_file()
    if not file_path:
        # File nahi hai to shanti se exit karein (Error nahi)
        print("No files to process.")
        sys.exit(0) 

    print(f"📂 Processing: {file_path}")

    # 2. Upload karo
    url = upload_with_retry(file_path)
    
    if url:
        print(f"✅ SUCCESS: {url}")
        
        # 3. Telegram Send
        try:
            is_video = file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
            method = "sendVideo" if is_video else "sendPhoto"
            media_key = "video" if is_video else "photo"
            
            # FIX 3: Timeout aur Error raising add kiya
            tg_resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}", 
                json={"chat_id": CHAT_ID, media_key: url, "caption": CAPTION},
                timeout=30
            )
            tg_resp.raise_for_status() # Agar Telegram ne 400/500 diya to error aayega
            print("✅ Telegram message sent.")
            
        except Exception as e:
            print(f"❌ Telegram Failed: {e}")
            # Note: Agar Telegram fail ho, to file delete nahi karni chahiye taaki retry ho sake
            sys.exit(1) 
        
        # 4. Webhook Send (Optional failure allowed)
        if WEBHOOK_URL:
            try:
                requests.post(WEBHOOK_URL, json={"content": f"{CAPTION}\n{url}"}, timeout=10)
            except Exception as e:
                print(f"⚠️ Webhook Failed: {e}")

        # 5. DELETE FILE
        try:
            os.remove(file_path)
            print("🗑️ File deleted from repo.")
        except Exception as e:
            print(f"❌ Deletion failed: {e}")

    else:
        print("❌ Upload failed after retries.")
        sys.exit(1) # FIX 1: Action ko FAIL mark karein taaki Red Cross aaye

if __name__ == "__main__":
    main()
