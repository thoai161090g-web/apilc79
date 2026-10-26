import requests
from flask import Flask, jsonify, Response
import threading
import time
import datetime
import json

app = Flask(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/lite-sessions?cp=R&cl=R&pf=web&at=3959701241b686f12e01bfe9c3a319b8"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Lưu lịch sử dự đoán (tối đa 50 phiên)
LICH_SU_DU_DOAN = []
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
    # Bảng tra tổng điểm
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
    if len(history) < 15: return "TÀI", 50
    
    recent = history[:15][::-1]
    results = [h["resultTruyenThong"] for h in recent]
    points = [h["point"] for h in recent]
    dices = [h["dices"] for h in recent]
    
    last_res = "TÀI" if results[-1] == "TAI" else "XỈU"
    last_point = points[-1]
    last_dices = dices[-1]
    
    do_tin_cay = 65 # Mặc định

    if results[-3:] == ["XIU", "XIU", "XIU"]: return "TÀI", 65
    if results[-3:] == ["TAI", "TAI", "TAI"]: return "XỈU", 65
    if results[-4:] in [["XIU", "TAI", "XIU", "TAI"], ["TAI", "XIU", "TAI", "XIU"]]: return last_res, 60
    if set(points[-3:]).issubset({7, 9, 10}) and len(set(results[-3:])) > 1: return ("TÀI" if last_res == "XỈU" else "XỈU"), 75
    if str(points[-2]) + str(points[-1]) in ["1011", "1110", "89", "98"]: return ("TÀI" if last_res == "XỈU" else "XỈU"), 80
    if len(set(points[-5:-1])) == 1 and points[-1] != points[-2]: return ("TÀI" if last_res == "XỈU" else "XỈU"), 61
    count_tai = results[-5:].count("TAI")
    if count_tai in [3, 4] and count_tai - results[-5:].count("XIU") > 0: return "XỈU", 86

    du_doan_bang = kiem_tra_diem(last_point, last_dices, last_res)
    if du_doan_bang == "BỎ": return last_res, 50
    return du_doan_bang, 70

def bot_chay_ngam():
    global LICH_SU_DU_DOAN
    last_id = None
    
    while IS_RUNNING:
        current_hour = datetime.datetime.now().hour
        if 0 <= current_hour < 5:
            time.sleep(60)
            continue

        history = get_history()
        if history:
            current_id = history[0]["id"]
            
            # Cập nhật kết quả cho phiên trước đó trong lịch sử
            for item in LICH_SU_DU_DOAN:
                if item["phien"] == str(current_id) and item["ket_qua"] == "running...":
                    actual_res = history[0]["resultTruyenThong"]
                    item["ket_qua"] = "TÀI" if actual_res == "TAI" else "XỈU"
                    item["xac_minh"] = "✅" if item["du_doan"] == item["ket_qua"] else "❌"

            if current_id != last_id:
                last_id = current_id
                du_doan, tin_cay = phan_tich_cau(history)
                
                phien_moi = {
                    "phien": str(current_id + 1),
                    "du_doan": du_doan,
                    "do_tin_cay": f"{tin_cay}%",
                    "ket_qua": "running...",
                    "xac_minh": "Chờ..."
                }
                LICH_SU_DU_DOAN.insert(0, phien_moi)
                
                # Chỉ giữ 50 phiên
                if len(LICH_SU_DU_DOAN) > 50: LICH_SU_DU_DOAN.pop()
                
        time.sleep(10)

@app.route('/')
def home():
    return "API LC79 đang chạy. Xem /api hoặc /thongke"

@app.route('/api')
def api_json():
    history = get_history()
    if not history:
        return jsonify({"error": "Không lấy được dữ liệu từ API gốc"})

    # Lấy phiên vừa xong (gần nhất) và dự đoán phiên tới
    current_id = history[0]["id"]
    actual_res = history[0]["resultTruyenThong"]
    point = history[0]["point"]
    dices = history[0]["dices"]
    
    du_doan, tin_cay = phan_tich_cau(history)
    
    data = {
        "phien_truoc": {
            "phien": current_id,
            "ket_qua": "TÀI" if actual_res == "TAI" else "XỈU",
            "xuc_xac": dices,
            "tong_diem": point
        },
        "phien_nay": {
            "phien": current_id + 1,
            "du_doan": du_doan,
            "do_tin_cay": f"{tin_cay}%"
        }
    }
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/json; charset=utf-8')

@app.route('/thongke')
def thongke_json():
    # Gọi API để cập nhật trạng thái mới nhất trước khi trả kết quả
    history = get_history()
    if history:
        current_id = history[0]["id"]
        for item in LICH_SU_DU_DOAN:
            if item["phien"] == str(current_id) and item["ket_qua"] == "running...":
                actual_res = history[0]["resultTruyenThong"]
                item["ket_qua"] = "TÀI" if actual_res == "TAI" else "XỈU"
                item["xac_minh"] = "✅" if item["du_doan"] == item["ket_qua"] else "❌"

    thang = sum(1 for item in LICH_SU_DU_DOAN if item["xac_minh"] == "✅")
    thua = sum(1 for item in LICH_SU_DU_DOAN if item["xac_minh"] == "❌")
    ti_le = round((thang / (thang + thua) * 100), 1) if (thang + thua) > 0 else 0.0

    data = {
        "thong_ke_50_phien": {
            "Thang": thang,
            "Thua": thua,
            "Ti_le": f"{ti_le}%"
        },
        "lich_su": LICH_SU_DU_DOAN
    }
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/json; charset=utf-8')

if __name__ == "__main__":
    threading.Thread(target=bot_chay_ngam, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
