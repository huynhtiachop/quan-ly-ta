import streamlit as st
import datetime

st.set_page_config(page_title="Quản Lý TA", layout="centered")

st.title("Hệ Thống Quản Lý Chuyên Cần & Nhiệm Vụ TA")

# Lấy ngày hiện tại
today = datetime.date.today()
st.caption(f"Hôm nay là: {today.strftime('%d/%m/%Y')}")

tab1, tab2 = st.tabs(["📅 Check-in Hàng Ngày", "🚩 Quản Lý Deadline Tháng"])

with tab1:
    st.subheader("Đánh giá nhiệm vụ trong ngày")
    ta_name = st.selectbox("Chọn Trợ Giảng:", ["Nguyễn Văn A", "Trần Thị B"])
    
    # 1. Chuyên cần ngày
    chuyen_can = st.radio(
        "Tình trạng đi làm hôm nay:",
        ["Đi đủ / Đúng giờ", 
         "Đi muộn / Nghỉ (Có báo trước, có SP)", 
         "Đi muộn (Không báo, không có SP)"]
    )
    
    # 2. Task hàng ngày
    st.write("Nhiệm vụ lớp học:")
    col1, col2 = st.columns(2)
    with col1:
        nhap_diem = st.checkbox("Đã nhập điểm số lớp", value=True)
    with col2:
        diem_danh = st.checkbox("Đã điểm danh học viên", value=True)

    if st.button("Lưu Check-in Ngày"):
        # Tính toán lỗi trong ngày
        loi_ngay = 0
        ghi_chu_loi = []
        
        if chuyen_can == "Đi muộn (Không báo, không có SP)":
            loi_ngay += 10
            ghi_chu_loi.append("Vi phạm chuyên cần nặng")
            
        if not nhap_diem:
            loi_ngay += 2
            ghi_chu_loi.append("Chưa nhập điểm")
            
        if not diem_danh:
            loi_ngay += 2
            ghi_chu_loi.append("Chưa điểm danh")
            
        # Đóng gói dữ liệu gửi đi
        payload_ngay = {
            "loai_form": "daily_checkin",
            "ngay": str(today),
            "tro_giang": ta_name,
            "chuyen_can": chuyen_can,
            "nhap_diem_done": nhap_diem,
            "diem_danh_done": diem_danh,
            "diem_tru_ngay": loi_ngay,
            "chi_tiet_loi": ", ".join(ghi_chu_loi) if ghi_chu_loi else "Không có lỗi"
        }

        st.success(f"Đã lưu nhật ký ngày cho {ta_name}!")
        if loi_ngay > 0:
            st.error(f"Tổng điểm trừ hôm nay: -{loi_ngay} điểm")
            
        st.write("Dữ liệu chuẩn bị gửi qua Webhook:")
        st.json(payload_ngay) # Hiển thị JSON để debug
        # Code bắn webhook sẽ đặt ở đây: requests.post(url, json=payload_ngay)


with tab2:
    st.subheader("Kiểm tra Deadline & Họp")
    ta_name_thang = st.selectbox("Chọn Trợ Giảng cần check:", ["Nguyễn Văn A", "Trần Thị B"], key="ta_thang")
    
    st.warning("Lưu ý: Báo cáo tháng (Mùng 1) | Báo giảng (Mùng 5)")
    
    # Check task tháng
    bao_cao_mung_1 = st.checkbox("Đã nộp Báo cáo tổng kết lớp (Hạn mùng 1)", value=True)
    bao_giang_mung_5 = st.checkbox("Đã hoàn thành Báo giảng (Hạn mùng 5)", value=True)
    
    # Check số buổi họp
    so_buoi_hop = st.number_input("Số buổi họp đã tham gia trong tháng", min_value=0, max_value=10, value=3)
    ly_do_vang = ""
    if so_buoi_hop < 3:
        ly_do_vang = st.text_input("Lý do vắng mặt (nếu có):", placeholder="Trùng lịch thi, ốm...")
        
    if st.button("Chốt Điểm Tháng"):
        # Logic tính toán trừ điểm nội bộ
        diem_tru = 0
        ly_do_tru = []
        
        if not bao_cao_mung_1: 
            diem_tru += 15
            ly_do_tru.append("Trễ báo cáo mùng 1")
            
        if not bao_giang_mung_5: 
            diem_tru += 10
            ly_do_tru.append("Trễ báo giảng mùng 5")
            
        if so_buoi_hop < 3 and ly_do_vang == "":
            tru_hop = (3 - so_buoi_hop) * 10
            diem_tru += tru_hop
            ly_do_tru.append(f"Vắng {3 - so_buoi_hop} buổi họp không phép")
            
        payload_thang = {
            "loai_form": "monthly_review",
            "thang": today.strftime('%m/%Y'),
            "tro_giang": ta_name_thang,
            "diem_tru_thang": diem_tru,
            "chi_tiet_loi": ", ".join(ly_do_tru) if ly_do_tru else "Hoàn thành tốt",
            "ly_do_vang_hop": ly_do_vang
        }

        if diem_tru > 0:
            st.error(f"Tổng điểm bị trừ trong kỳ chốt này: -{diem_tru} điểm")
        else:
            st.success("Hoàn thành đủ mọi deadline trong tháng!")
            
        st.write("Dữ liệu chuẩn bị gửi qua Webhook:")
        st.json(payload_thang)
