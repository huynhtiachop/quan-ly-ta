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
        import streamlit as st
import datetime

# 1. CẤU HÌNH TRANG (Phải để ở dòng đầu tiên)
st.set_page_config(page_title="KB-LAB | Quản Lý Trợ Giảng", page_icon="🔴", layout="wide")

# 2. BƠM MÃ CSS (UI/UX DESIGN)
st.markdown("""
    <style>
    /* Nhúng font chữ Inter từ Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Áp dụng font chữ toàn cục */
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Nền chính của ứng dụng (Light Gray) */
    .stApp {
        background-color: #F5F7FA;
    }
    
    /* Giao diện Thanh Sidebar (Màu Đen/Xám đậm) */
    [data-testid="stSidebar"] {
        background-color: #1A1A1A;
        border-right: 2px solid #800000;
    }
    [data-testid="stSidebar"] * {
        color: #F5F7FA !important;
    }
    
    /* Màu chữ chính cho nội dung (Đen tiêu chuẩn) */
    h1, h2, h3, h4, h5, h6 {
        color: #2D2D2D !important;
        font-weight: 700;
    }
    p, label {
        color: #2D2D2D !important;
    }
    
    /* Nút bấm (Primary Gradient Đỏ đậm - Đỏ tươi) */
    .stButton>button {
        background: linear-gradient(135deg, #8B0000 0%, #FF0000 100%);
        color: white !important;
        border: none;
        border-radius: 8px; /* Bo góc */
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    /* Hiệu ứng khi di chuột (Hover) vào nút bấm */
    .stButton>button:hover {
        box-shadow: 0 6px 12px rgba(230, 0, 0, 0.3);
        transform: translateY(-2px);
        background: linear-gradient(135deg, #FF0000 0%, #8B0000 100%);
    }
    
    /* Tùy chỉnh các khối nhập liệu (Dropdown, Text Input, Checkbox) */
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"] {
        background-color: white !important;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        color: #2D2D2D !important;
    }
    
    /* Tạo dạng Thẻ (Card) cho các Tab nội dung */
    .stTabs [data-baseweb="tab-list"] {
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 10px 10px 0 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: white;
        padding: 20px;
        border-radius: 0 8px 8px 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)


# 3. THIẾT KẾ SIDEBAR (THANH ĐIỀU HƯỚNG BÊN TRÁI)
with st.sidebar:
    st.markdown("### 🔴 KB-LAB")
    st.caption("*Kiến tạo chuẩn mực không gian tri thức hiện đại*")
    st.markdown("---")
    
    # Tạo menu điều hướng
    menu = st.radio(
        "MENU QUẢN LÝ",
        ["🏠 Tổng quan", "👥 Quản lý Trợ giảng", "📅 Lịch trực/Lịch lớp", "📝 Đánh giá công việc", "💰 Tính lương & Thưởng", "⚙️ Cài đặt hệ thống"]
    )


# 4. NỘI DUNG CHÍNH (MAIN CONTENT)
today = datetime.date.today()

# Nếu người dùng bấm vào phần Đánh giá công việc
if menu == "📝 Đánh giá công việc":
    st.title("Phân Hệ Đánh Giá & Chuyên Cần TA")
    st.write(f"**Ngày ghi nhận:** {today.strftime('%d/%m/%Y')}")
    
    # Sử dụng Tabs như thiết kế cũ nhưng giờ giao diện đã là Card
    tab1, tab2 = st.tabs(["📅 Check-in Hàng Ngày", "🚩 Quản Lý Deadline Tháng"])

    with tab1:
        st.subheader("Đánh giá nhiệm vụ trong ngày")
        ta_name = st.selectbox("Chọn Trợ Giảng:", ["Đặng Bá Huỳnh Anh", "Nguyễn Văn A", "Trần Thị B"])
        
        chuyen_can = st.radio(
            "Tình trạng đi làm hôm nay:",
            ["Đi đủ / Đúng giờ", 
             "Đi muộn / Nghỉ (Có báo trước, có SP)", 
             "Đi muộn (Không báo, không có SP)"]
        )
        
        st.markdown("**Nhiệm vụ lớp học:**")
        col1, col2 = st.columns(2)
        with col1:
            nhap_diem = st.checkbox("Đã nhập điểm số lớp", value=True)
        with col2:
            diem_danh = st.checkbox("Đã điểm danh học viên", value=True)

        if st.button("💾 Lưu Check-in Ngày"):
            loi_ngay = 0
            if chuyen_can == "Đi muộn (Không báo, không có SP)": loi_ngay += 10
            if not nhap_diem: loi_ngay += 2
            if not diem_danh: loi_ngay += 2
            
            st.success(f"Đã lưu nhật ký ngày cho {ta_name}!")
            if loi_ngay > 0:
                st.error(f"Tổng điểm trừ hôm nay: -{loi_ngay} điểm")

    with tab2:
        st.subheader("Kiểm tra Deadline & Họp")
        ta_name_thang = st.selectbox("Chọn Trợ Giảng cần check:", ["Đặng Bá Huỳnh Anh", "Nguyễn Văn A", "Trần Thị B"], key="ta_thang")
        st.info("💡 Lưu ý: Báo cáo tháng (Mùng 1) | Báo giảng (Mùng 5)")
        
        bao_cao_mung_1 = st.checkbox("Đã nộp Báo cáo tổng kết lớp (Hạn mùng 1)", value=True)
        bao_giang_mung_5 = st.checkbox("Đã hoàn thành Báo giảng (Hạn mùng 5)", value=True)
        
        so_buoi_hop = st.number_input("Số buổi họp đã tham gia trong tháng", min_value=0, max_value=10, value=3)
        ly_do_vang = ""
        if so_buoi_hop < 3:
            ly_do_vang = st.text_input("Lý do vắng mặt (nếu có):", placeholder="Trùng lịch thi, ốm...")
            
        if st.button("📊 Chốt Điểm Tháng"):
            diem_tru = 0
            if not bao_cao_mung_1: diem_tru += 15
            if not bao_giang_mung_5: diem_tru += 10
            if so_buoi_hop < 3 and ly_do_vang == "": diem_tru += (3 - so_buoi_hop) * 10
                
            if diem_tru > 0:
                st.error(f"Tổng điểm bị trừ trong kỳ chốt này: -{diem_tru} điểm")
            else:
                st.success("Hoàn thành xuất sắc mọi deadline trong tháng!")

# Placeholder cho các mục menu khác
else:
    st.title(menu)
    st.write(f"Mô đun **{menu}** đang trong quá trình phát triển (Under Construction).")
    st.info("Vui lòng chọn mục **📝 Đánh giá công việc** ở Sidebar bên trái để trải nghiệm tính năng đã hoàn thiện.")
