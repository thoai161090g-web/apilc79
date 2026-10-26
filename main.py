import requests
from flask import Flask
import threading
import time

app = Flask(__name__)

# --- CẤU HÌNH API CỦA MÀY ---
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/lite-sessions?cp=R&cl=R&pf=web&at=3959701241b686f12e01bfe9c3a319b8"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def get_history():
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json().get("list", [])
        return []
    except:
        return []

def phan_tich_cau(history):
    if len(history) < 10: return "Chưa đủ dữ liệu", 0
    
    # Đảo ngược list để tính từ cũ đến mới
    recent = history[:15][::-1]
    results = [h["resultTruyenThong"] for h in recent]
    points = [h["point"] for h in recent]
    
    last_res = results[-1]
    last_point = points[-1]

    # --- ÁP DỤNG MẸO CỦA MÀY ---
    
    # Mẹo 1: Cầu bệt 3 con (3 trắng/3 đen) -> Bẻ nhẹ
    if results[-3:] == ["XIU", "XIU", "XIU"]:
        return "TAI", 65
    if results[-3:] == ["TAI", "TAI", "TAI"]:
        return "XIU", 65
        
    # Mẹo 2: Cầu 1-1 (so le) -> Đi theo nhịp đảo
    if results[-4:] == ["XIU", "TAI", "XIU", "TAI"]:
        return "XIU", 60
    if results[-4:] == ["TAI", "XIU", "TAI", "XIU"]:
        return "TAI", 60

    # Mẹo 3: Đa số 5-4-3
    count_tai = results[-5:].count("TAI")
    count_xiu = results[-5:].count("XIU")
    if count_tai == 3 and count_xiu == 2: return "XIU", 55
    if count_xiu == 3 and count_tai == 2: return "TAI", 55

    # Mẹo 4: Bám điểm (Phiên trước ra Xỉu 8,9,10 -> Bẻ Tài. Ra Tài 11,12 -> Bẻ Xỉu)
    if last_res == "XIU" and last_point in [8, 9, 10]:
        return "TAI", 70
    if last_res == "TAI" and last_point in [11, 12]:
        return "XIU", 70

    # Mặc định theo cầu
    return last_res, 50

# --- VÒNG LẶP CHẠY NGẦM ---
def bot_chay_ngam():
    last_id = None
    while True:
        history = get_history()
        if history:
            current_id = history[0]["id"]
            # Chỉ phân tích khi có phiên mới
            if current_id != last_id:
                last_id = current_id
                last_info = history[0]
                du_doan, tin_cay = phan_tich_cau(history)
                
                print("="*40)
                print(f"Phiên vừa xong: #{last_info['id']} | {last_info['resultTruyenThong']} | Tổng: {last_info['point']}")
                print(f"👉 DỰ ĐOÁN PHIÊN {current_id + 1}: {du_doan} ({tin_cay}%)")
                print("="*40)
        time.sleep(15) # Cứ 15s check API 1 lần

@app.route('/')
def home():
    return "Bot đang chạy ngầm phân tích cầu..."

# Khởi chạy bot ngầm cùng lúc với web server
threading.Thread(target=bot_chay_ngam, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)