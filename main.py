import requests
from flask import Flask
import threading
import time

app = Flask(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/lite-sessions?cp=R&cl=R&pf=web&at=3959701241b686f12e01bfe9c3a319b8"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

KET_QUA_DU_DOAN = {"phien": "...", "du_doan": "...", "do_tin_cay": 0, "ly_do": "..."}

def get_history():
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json().get("list", [])
        return []
    except:
        return []

def kiem_tra_diem(du_doan, diem, xuc_xac, cua_truoc):
    # 1. Xỉu 3 (111)
    if diem == 3: return "XIU", 80 if xuc_xac == [1,1,1] else 0
    
    # 2. Xỉu 4, Xỉu 5
    if diem in [4, 5]: return "XIU", 70
    
    # 3. Xỉu 6
    if diem == 6: 
        return ("TAI", 70) if sorted(xuc_xac) in [[1,2,3], [1,1,4]] else ("XIU", 70)
    
    # 4. Xỉu 7
    if diem == 7:
        return ("TAI", 89) if sorted(xuc_xac) in [[1,2,4], [1,3,3]] else ("XIU", 70)
        
    # 5. Xỉu 8
    if diem == 8:
        return ("TAI", 70) if sorted(xuc_xac) in [[1,3,4], [2,2,4], [2,3,3]] else ("XIU", 70)
        
    # 6. Xỉu 9
    if diem == 9:
        return ("TAI", 70) if sorted(xuc_xac) in [[1,2,6], [1,3,5], [1,4,4], [3,3,3]] else ("XIU", 70)
        
    # 7. Xỉu 10
    if diem == 10:
        return ("TAI", 70) if sorted(xuc_xac) in [[1,3,6], [1,4,5], [2,4,4], [3,4,3]] else ("XIU", 70)

    # 8. Tài 11
    if diem == 11:
        return ("TAI", 70) if sorted(xuc_xac) in [[2,3,6], [3,4,4]] else ("XIU", 70)

    # 9. Tài 12
    if diem == 12:
        s = sorted(xuc_xac)
        if s in [[1,5,6], [2,5,5], [3,3,6], [3,4,5]]: return "TAI", 70
        if s in [[2,4,6], [4,4,4]]: return "XIU", 99 # Auto Xỉu
        return "TAI", 70 # Các trường hợp còn lại (651, 552...)

    # 10. Tài 13
    if diem == 13:
        return ("TAI", 70) if sorted(xuc_xac) in [[3,4,6], [3,5,5], [4,4,5]] else ("XIU", 70)

    # 11. Tài 14
    if diem == 14:
        return ("TAI", 70) if sorted(xuc_xac) in [[3,5,6], [4,5,5]] else ("XIU", 70)

    # 12. Tài 15
    if diem == 15:
        return ("TAI", 70) if sorted(xuc_xac) in [[4,5,6], [5,5,5]] else ("XIU", 70)

    # 13. Tài 16
    if diem == 16:
        return ("XIU", 70) if sorted(xuc_xac) in [[5,5,6], [4,6,6]] else ("TAI", 70)

    # 14. Tài 17
    if diem == 17: return "TAI", 70

    # 15. Tài 18
    if diem == 18: return "BỎ", 0
    
    return cua_truoc, 50 # Mặc định

def phan_tich_cau(history):
    if len(history) < 15: return "Chưa đủ dữ liệu", 0, "Không đủ data"
    
    recent = history[:15][::-1]
    results = [h["resultTruyenThong"] for h in recent]
    points = [h["point"] for h in recent]
    dices = [h["dices"] for h in recent]
    
    last_res = results[-1]
    last_point = points[-1]
    last_dices = dices[-1]

    # --- 1. Áp bảng tra tổng điểm trước ---
    du_doan_bang, tin_cay = kiem_tra_diem("", last_point, last_dices, last_res)
    
    # --- 2. Áp các mẹo cầu (Nếu trùng khớp thì ghi đè hoặc tăng độ tin cậy) ---
    ly_do = f"Bảng tra Tổng {last_point}"
    
    # Mẹo 6: 3 trắng/3 đen -> Bẻ nhẹ
    if results[-3:] == ["XIU", "XIU", "XIU"]:
        du_doan_bang, tin_cay, ly_do = "TAI", 65, "Bẻ cầu 3 Xỉu liên tiếp"
    elif results[-3:] == ["TAI", "TAI", "TAI"]:
        du_doan_bang, tin_cay, ly_do = "XIU", 65, "Bẻ cầu 3 Tài liên tiếp"
        
    # Mẹo 3: Cầu 1-1 so le
    elif results[-4:] in [["XIU", "TAI", "XIU", "TAI"], ["TAI", "XIU", "TAI", "XIU"]]:
        du_doan_bang, tin_cay, ly_do = results[-1], 60, "Bám cầu so le 1-1"
        
    # Mẹo 2: Lặp 10,11 hoặc 8,9 -> Auto bẻ
    elif str(points[-2]) + str(points[-1]) in ["1011", "1110", "89", "98"]:
        du_doan_bang, tin_cay, ly_do = ("XIU" if last_res == "TAI" else "TAI"), 80, "Auto bẻ cầu lặp 10-11 hoặc 8-9"

    # Mẹo 1: Cầu 3 trắng đen + cặp 9-10-7 (T-X-T có 9,10,7)
    elif set(points[-3:]).issubset({7, 9, 10}) and len(set(results[-3:])) > 1:
        du_doan_bang, tin_cay, ly_do = ("XIU" if last_res == "TAI" else "TAI"), 75, "Auto bẻ cầu 3 trắng đen (9-10-7)"

    # Mẹo 5: Bệt + con mới ra (Đang bệt 11-12-13-14-12-11 tự nhiên ra con khác)
    elif len(set(points[-5:-1])) == 1 and points[-1] != points[-2]:
        du_doan_bang, tin_cay, ly_do = ("XIU" if last_res == "TAI" else "TAI"), 61, "Bẻ nhẹ do cầu bệt xuất hiện con mới"

    # Mẹo 7: Đa số 5-4-3
    count_tai = results[-5:].count("TAI")
    if count_tai in [3, 4] and count_tai - results[-5:].count("XIU") > 0:
        du_doan_bang, tin_cay, ly_do = "XIU", 86, "Đa số 5-4-3 (Đứt nhịp)"

    return du_doan_bang, tin_cay, ly_do

def bot_chay_ngam():
    global KET_QUA_DU_DOAN
    last_id = None
    while True:
        # Bỏ qua khung giờ 12h đêm - 5h sáng (Mẹo 11)
        current_hour = int(time.strftime("%H"))
        if 0 <= current_hour < 5:
            time.sleep(60)
            continue

        history = get_history()
        if history:
            current_id = history[0]["id"]
            if current_id != last_id:
                last_id = current_id
                du_doan, tin_cay, ly_do = phan_tich_cau(history)
                
                KET_QUA_DU_DOAN = {
                    "phien": str(current_id + 1),
                    "du_doan": du_doan,
                    "do_tin_cay": tin_cay,
                    "ly_do": ly_do
                }
                print(f"[{time.strftime('%H:%M:%S')}] Phiên {KET_QUA_DU_DOAN['phien']} -> {du_doan} ({tin_cay}%) | {ly_do}")
        time.sleep(15)

@app.route('/')
def home():
    if KET_QUA_DU_DOAN["phien"] == "...":
        return "Bot đang khởi động..."
    
    # Định dạng trả về đúng yêu cầu
    text_response = (
        f"Phiên này {KET_QUA_DU_DOAN['phien']} dự đoán {KET_QUA_DU_DOAN['du_doan']} "
        f"(Độ tin cậy {KET_QUA_DU_DOAN['do_tin_cay']}%)\n"
        f"Lý do: {KET_QUA_DU_DOAN['ly_do']}"
    )
    return text_response

if __name__ == "__main__":
    threading.Thread(target=bot_chay_ngam, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
