import os
import requests
import time
import sys

# --- CONFIGURATION ---
CONTENT_FOLDER = "content/wildsnap"

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_WILDSNAP')
WEBHOOK_URL = os.getenv('WEBHOOK_WILDSNAP')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Allowed extensions
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.avi', '.mkv')

# FALLBACK CAPTION (Agar AI fail ho jaye to ye use hoga)
FALLBACK_CAPTION = "Wild vibes only. 🦁 \n#Wildlife #Nature #Animals"

# --- NEW: Pollinations AI Function ---
def generate_ai_caption():
    """
    Pollinations AI ka use karke ek single line, animal-related caption
    generate karta hai with SEO hashtags. Stars (*) allow nahi karta title mein.
    """
    # Prompt AI ko strict instructions deta hai
    prompt_text = "Generate a single, engaging caption line specifically about wild animals or nature. The starting sentence must NOT contain any stars (*) or hashtags (#). End the caption with 5-7 relevant SEO hashtags related to wildlife and nature."
    
    # URL safe encoding
    encoded_prompt = requests.utils.quote(prompt_text)
    url = f"https://text.pollinations.ai/{encoded_prompt}"

    print("🤖 AI se caption banwa raha hoon...")
    try:
        # Timeout zaroori hai taaki script latak na jaye
        response = requests.get(url, timeout=20) 
        
        if response.status_code == 200 and response.text.strip():
            caption = response.text.strip()
            
            # Extra safety: Agar AI ne galti se shuru mein * laga diya to hata do
            # Hum title part ko clean kar rahe hain, hashtags ko chhod kar.
            parts = caption.split('#', 1) # Pehle hashtag se split karo
            title_part = parts[0].replace('*', '').strip()
            
            if len(parts) > 1:
                final_caption = f"{title_part} #{parts[1]}"
            else:
                final_caption = title_part

            print(f"✨ AI Caption Generated: {final_caption}")
            return final_caption
        else:
            print(f"⚠️ AI Response Error (Status: {response.status_code}). Using fallback.")
            return FALLBACK_CAPTION
            
    except Exception as e:
        print(f"⚠️ AI Connection Failed: {e}. Using fallback.")
        return FALLBACK_CAPTION

# --- Existing Functions ---

def get_file():
    """Folder se pehli VALID media file uthata hai"""
    # Check folder exists
    if not os.path.exists(CONTENT_FOLDER):
        print(f"❌ Path nahi mila: {CONTENT_FOLDER}")
        return None
    # Check it's actually a folder
    if not os.path.isdir(CONTENT_FOLDER):
        print(f"❌ ERROR: '{CONTENT_FOLDER}' ek FILE hai, Folder nahi! Ise delete karke Folder banayein.")
        return None
    
    # Sirf valid media files filter karein
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
                    timeout=60
                )
                if r.status_code == 200 and "http" in r.text:
                    return r.text.strip()
                else:
                    print(f"⚠️ Server Response: {r.text}")
        except Exception as e:
            print(f"⚠️ Fail: {e}")
            time.sleep(5)
    return None

def main():
    # 0. Check Secrets
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Error: TELEGRAM_TOKEN or CHAT_ID is missing in Secrets!")
        sys.exit(1)

    # 1. File Uthao
    file_path = get_file()
    if not file_path:
        print("No files to process.")
        sys.exit(0)

    print(f"📂 Processing: {file_path}")

    # 2. Upload karo
    url = upload_with_retry(file_path)
    
    if url:
        print(f"✅ SUCCESS URL: {url}")

        # --- 2.1 Generate AI Caption HERE ---
        # Upload successful hone ke baad hi caption generate karein
        current_caption = generate_ai_caption()
        
        # 3. Telegram Send
        try:
            is_video = file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
            method = "sendVideo" if is_video else "sendPhoto"
            media_key = "video" if is_video else "photo"
            
            tg_resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}", 
                json={"chat_id": CHAT_ID, media_key: url, "caption": current_caption},
                timeout=30
            )
            tg_resp.raise_for_status()
            print("✅ Telegram message sent with AI caption.")
            
        except Exception as e:
            print(f"❌ Telegram Failed: {e}")
            sys.exit(1) 
        
        # 4. Webhook Send
        if WEBHOOK_URL:
            try:
                requests.post(WEBHOOK_URL, json={"content": f"{current_caption}\n{url}"}, timeout=10)
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
        sys.exit(1)

if __name__ == "__main__":
    main()
