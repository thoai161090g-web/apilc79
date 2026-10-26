import requests
from flask import Flask, jsonify
import threading
import time

app = Flask(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/lite-sessions?cp=R&cl=R&pf=web&at=3959701241b686f12e01bfe9c3a319b8"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Biến lưu trữ kết quả dự đoán mới nhất
KET_QUA_DU_DOAN = {"phien": "...", "du_doan": "...", "do_tin_cay": 0}

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
    
    recent = history[:15][::-1]
    results = [h["resultTruyenThong"] for h in recent]
    points = [h["point"] for h in recent]
    
    last_res = results[-1]
    last_point = points[-1]

    if results[-3:] == ["XIU", "XIU", "XIU"]: return "TAI", 65
    if results[-3:] == ["TAI", "TAI", "TAI"]: return "XIU", 65
    if results[-4:] == ["XIU", "TAI", "XIU", "TAI"]: return "XIU", 60
    if results[-4:] == ["TAI", "XIU", "TAI", "XIU"]: return "TAI", 60

    count_tai = results[-5:].count("TAI")
    count_xiu = results[-5:].count("XIU")
    if count_tai == 3 and count_xiu == 2: return "XIU", 55
    if count_xiu == 3 and count_tai == 2: return "TAI", 55

    if last_res == "XIU" and last_point in [8, 9, 10]: return "TAI", 70
    if last_res == "TAI" and last_point in [11, 12]: return "XIU", 70

    return last_res, 50

def bot_chay_ngam():
    global KET_QUA_DU_DOAN
    last_id = None
    while True:
        history = get_history()
        if history:
            current_id = history[0]["id"]
            if current_id != last_id:
                last_id = current_id
                du_doan, tin_cay = phan_tich_cau(history)
                
                # Cập nhật kết quả vào biến toàn cục
                KET_QUA_DU_DOAN = {
                    "phien": str(current_id + 1),
                    "du_doan": du_doan,
                    "do_tin_cay": tin_cay
                }
                print(f"Đã cập nhật dự đoán: {KET_QUA_DU_DOAN}")
        time.sleep(15)

@app.route('/')
def home():
    # Trả về kết quả dự đoán dạng text thuần giống yêu cầu của mày
    if KET_QUA_DU_DOAN["phien"] == "...":
        return "Bot đang khởi động và lấy dữ liệu, vui lòng đợi..."
    
    text_response = f"Phiên này {KET_QUA_DU_DOAN['phien']} dự đoán {KET_QUA_DU_DOAN['du_doan']} (Độ tin cậy {KET_QUA_DU_DOAN['do_tin_cay']}%)"
    return text_response

# Chạy luồng ngầm
threading.Thread(target=bot_chay_ngam, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
