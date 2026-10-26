import requests
from flask import Flask, jsonify, Response
import threading
import time
import datetime
import json

app = Flask(__name__)

# Token API của mày
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/lite-sessions?cp=R&cl=R&pf=web&at=3959701241b686f12e01bfe9c3a319b8"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Lưu trữ lịch sử
FAKE_DB = []
IS_RUNNING = True

def get_history():
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json().get("list", [])
        return []
    except:
        return []

def kiem_tra_diem(diem, xuc_xac, cua_truoc):
    # Bảng tra của mày
    if diem == 3: return "XỈU"
    if diem in [4, 5]: return "XỈU"
    if diem == 6: return ("TÀI") if sorted(xuc_xac) in [[1,2,3], [1,1,4]] else ("XỈU")
    if diem == 7: return ("TÀI") if sorted(xuc_xac) in [[1,2,4], [1,3,3]] else ("XỈU")
    if diem == 8: return ("TÀI") if sorted(xuc_xac) in [[1,3,4], [2,2,4], [2,3,3]] else ("XỈU")
    if diem == 9: return ("TÀI") if sorted(xuc_xac) in [[1,2,6], [1,3,5], [1,4,4], [3,3,3]] else ("XỈU")
    if diem == 10: return ("TÀI") if sorted(xuc_xac) in [[1,3,6], [1,4,5], [2,4,4], [3,4,3]] else ("XỈU")
    if diem == 11: return ("TÀI") if sorted(xuc_xac) in [[2,3,6], [3,4,4]] else ("XỈU")
    if diem == 12:
        s = sorted(xuc_xac)
        if s in [[1,5,6], [2,5,5], [3,3,6], [3,4,5]]: return "TÀI"
        if s in [[2,4,6], [4,4,4]]: return "XỈU"
        return "TÀI"
    if diem == 13: return ("TÀI") if sorted(xuc_xac) in [[3,4,6], [3,5,5], [4,4,5]] else ("XỈU")
    if diem == 14: return ("TÀI") if sorted(xuc_xac) in [[3,5,6], [4,5,5]] else ("XỈU")
    if diem == 15: return ("TÀI") if sorted(xuc_xac) in [[4,5,6], [5,5,5]] else ("XỈU")
    if diem == 16: return ("XỈU") if sorted(xuc_xac) in [[5,5,6], [4,6,6]] else ("TÀI")
    if diem == 17: return "TÀI"
    if diem == 18: return "BỎ"
    return cua_truoc

def phan_tich_cau(history):
    if len(history) < 15: return "TÀI"
    
    recent = history[:15][::-1]
    results = [h["resultTruyenThong"] for h in recent]
    points = [h["point"] for h in recent]
    dices = [h["dices"] for h in recent]
    
    last_res = "TÀI" if results[-1] == "TAI" else "XỈU"
    last_point = points[-1]
    last_dices = dices[-1]

    # Mẹo cầu
    if results[-3:] == ["XIU", "XIU", "XIU"]: return "TÀI"
    if results[-3:] == ["TAI", "TAI", "TAI"]: return "XỈU"
    if results[-4:] in [["XIU", "TAI", "XIU", "TAI"], ["TAI", "XIU", "TAI", "XIU"]]: return last_res
    if set(points[-3:]).issubset({7, 9, 10}) and len(set(results[-3:])) > 1: return "TÀI" if last_res == "XỈU" else "XỈU"
    if str(points[-2]) + str(points[-1]) in ["1011", "1110", "89", "98"]: return "TÀI" if last_res == "XỈU" else "XỈU"
    if len(set(points[-5:-1])) == 1 and points[-1] != points[-2]: return "TÀI" if last_res == "XỈU" else "XỈU"
    count_tai = results[-5:].count("TAI")
    if count_tai in [3, 4] and count_tai - results[-5:].count("XIU") > 0: return "XỈU"

    du_doan = kiem_tra_diem(last_point, last_dices, last_res)
    if du_doan == "BỎ": return last_res
    return du_doan

def bot_chay_ngam():
    global FAKE_DB
    last_id = None
    
    while IS_RUNNING:
        current_hour = datetime.datetime.now().hour
        if 0 <= current_hour < 5:
            time.sleep(60)
            continue

        history = get_history()
        if history:
            current_id = history[0]["id"]
            
            # Cập nhật kết quả thực tế cho phiên trước đó
            for item in FAKE_DB:
                if item["phien"] == str(current_id) and item["ket_qua"] == "running...":
                    actual_res = history[0]["resultTruyenThong"]
                    item["ket_qua"] = "TÀI" if actual_res == "TAI" else "XỈU"
                    item["xac_minh"] = "Đúng" if item["du_doan"] == item["ket_qua"] else "Sai"

            # Thêm phiên mới
            if current_id != last_id:
                last_id = current_id
                du_doan = phan_tich_cau(history)
                
                phien_moi = {
                    "game": "LC79 MD5",
                    "phien": str(current_id + 1),
                    "thoi_gian": datetime.datetime.now().strftime("%H:%M:%S"),
                    "du_doan": du_doan,
                    "ket_qua": "running...",
                    "xac_minh": "Chờ..."
                }
                FAKE_DB.insert(0, phien_moi)
                if len(FAKE_DB) > 30: FAKE_DB.pop()
                
        time.sleep(10) # Quét API mỗi 10s

@app.route('/')
def home():
    return "API đang chạy. Mở /api để xem kết quả."

@app.route('/api')
def api_json():
    thang = sum(1 for item in FAKE_DB if item["xac_minh"] == "Đúng")
    thua = sum(1 for item in FAKE_DB if item["xac_minh"] == "Sai")
    ti_le = round((thang / (thang + thua) * 100), 1) if (thang + thua) > 0 else 0.0
    
    # Trả về đúng cấu trúc yêu cầu, ép hiển thị tiếng Việt có dấu chuẩn
    data = {
        "game": "LC79 MD5",
        "typeStat": {
            "Thắng": thang,
            "Thua": thua,
            "Tỉ lệ": f"{ti_le}%"
        },
        "list": FAKE_DB
    }
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/json')

if __name__ == "__main__":
    threading.Thread(target=bot_chay_ngam, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
