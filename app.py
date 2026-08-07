import streamlit as st
import datetime
import pandas as pd

# ==========================================
# 1. CẤU HÌNH TRANG (BẮT BUỘC Ở DÒNG ĐẦU TIÊN)
# ==========================================
st.set_page_config(page_title="KB-LAB | Quản Lý Trợ Giảng", page_icon="🔴", layout="wide")

# ==========================================
# 2. BƠM MÃ CSS (UI/UX DESIGN: KB-LAB)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; }
    
    [data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 2px solid #800000; }
    [data-testid="stSidebar"] * { color: #F5F7FA !important; }
    
    h1, h2, h3, h4, h5, h6 { color: #2D2D2D !important; font-weight: 700; }
    p, label { color: #2D2D2D !important; }
    
    .stButton>button {
        background: linear-gradient(135deg, #8B0000 0%, #FF0000 100%);
        color: white !important; border: none; border-radius: 8px; 
        padding: 10px 24px; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease; width: 100%;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 12px rgba(230, 0, 0, 0.3); transform: translateY(-2px);
        background: linear-gradient(135deg, #FF0000 0%, #8B0000 100%);
    }
    
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"] {
        background-color: white !important; border-radius: 8px; border: 1px solid #E2E8F0; color: #2D2D2D !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 8px 8px 0 0; padding: 10px 10px 0 10px; }
    .stTabs [data-baseweb="tab-panel"] { background-color: white; padding: 20px; border-radius: 0 8px 8px 8px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. KẾT NỐI DỮ LIỆU REALTIME (GOOGLE SHEETS)
# ==========================================
# ⚠️ THAY ĐƯỜNG LINK NÀY BẰNG LINK CSV CỦA BẠN
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSVb3rLLnxyEcojV3neR2SWmZViC4GMRy-uRrDhb6d4o84UaE5C_Po9NQZDc-Hduc1ZQVAaRAUYxDR5/pub?output=csv"

@st.cache_data(ttl=10)
def lay_danh_sach_ta(url):
    try:
        df = pd.read_csv(url)
        df_active = df[df['Trạng Thái'] == 'Đang làm việc']
        return df_active['Họ và tên'].tolist(), df_active
    except Exception as e:
        return ["Lỗi/Chưa có link dữ liệu"], None

# ==========================================
# 4. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("### 🔴 KB-LAB")
    st.caption("*Kiến tạo chuẩn mực không gian tri thức hiện đại*")
    st.markdown("---")
    menu = st.radio(
        "MENU QUẢN LÝ",
        ["🏠 Tổng quan", "👥 Quản lý Trợ giảng", "📅 Lịch trực/Lịch lớp", "📝 Đánh giá công việc", "💰 Tính lương & Thưởng", "⚙️ Cài đặt hệ thống"]
    )

# ==========================================
# 5. NỘI DUNG CHÍNH (MAIN CONTENT)
# ==========================================
today = datetime.date.today()

# ------------------------------------------
# MÀN HÌNH 1: DASHBOARD TỔNG QUAN
# ------------------------------------------
if menu == "🏠 Tổng quan":
    st.title("Bảng Điều Khiển (Dashboard)")
    st.write("Thống kê hiệu suất và chuyên cần của đội ngũ trong tháng này.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng số nhân sự", "15", "+2")
    col2.metric("Tỷ lệ đi muộn", "5%", "-2%")
    col3.metric("Hoàn thành báo cáo", "90%", "Tăng")
    col4.metric("Điểm đánh giá TB", "4.8/5", "Ổn định")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Top Nhân Sự Xuất Sắc Tháng")
        data_ta = pd.DataFrame({
            'Họ và tên': ['Huỳnh Anh', 'Nguyễn Văn A', 'Trần Thị B', 'Lê Văn C'],
            'Điểm': [95, 88, 85, 70]
        }).set_index('Họ và tên')
        st.bar_chart(data_ta)
        
    with col_chart2:
        st.subheader("Tần suất lỗi vi phạm")
        data_loi = pd.DataFrame({
            'Loại lỗi': ['Đi muộn', 'Quên điểm danh', 'Trễ báo giảng', 'Vắng họp'],
            'Số lượng': [12, 5, 8, 2]
        }).set_index('Loại lỗi')
        st.line_chart(data_loi)

# ------------------------------------------
# MÀN HÌNH 2: ĐÁNH GIÁ CÔNG VIỆC
# ------------------------------------------
elif menu == "📝 Đánh giá công việc":
    st.title("Phân Hệ Đánh Giá & Chuyên Cần")
    st.write(f"**Ngày ghi nhận:** {today.strftime('%d/%m/%Y')}")
    
    tab1, tab2 = st.tabs(["📅 Check-in Hàng Ngày", "🚩 Quản Lý Deadline Tháng"])

    # Lấy dữ liệu Realtime từ hàm đã viết ở trên
    danh_sach_ta, df_data = lay_danh_sach_ta(SHEET_CSV_URL)

    with tab1:
        st.subheader("Đánh giá nhiệm vụ trong ngày")
        ta_name = st.selectbox("Chọn nhân sự:", danh_sach_ta, key="checkin_ngay")
        
        # Hiển thị SĐT và Vai trò (nếu kết nối được Google Sheets)
        if df_data is not None and ta_name != "Lỗi/Chưa có link dữ liệu":
            try:
                thong_tin = df_data[df_data['Họ và tên'] == ta_name].iloc[0]
                st.caption(f"📞 SĐT: {thong_tin.get('Số điện thoại', 'N/A')} | 🏷️ Vai trò: {thong_tin.get('Vai trò', 'N/A')}")
            except:
                pass

        chuyen_can = st.radio(
            "Tình trạng đi làm hôm nay:",
            ["Đi đủ / Đúng giờ", "Đi muộn / Nghỉ (Có báo trước, có SP)", "Đi muộn (Không báo, không có SP)"]
        )
        
        st.markdown("**Nhiệm vụ lớp học:**")
        col1, col2 = st.columns(2)
        with col1: nhap_diem = st.checkbox("Đã nhập điểm số lớp", value=True)
        with col2: diem_danh = st.checkbox("Đã điểm danh học viên", value=True)

        if st.button("💾 Lưu Check-in Ngày"):
            loi_ngay = 0
            if chuyen_can == "Đi muộn (Không báo, không có SP)": loi_ngay += 10
            if not nhap_diem: loi_ngay += 2
            if not diem_danh: loi_ngay += 2
            
            st.success(f"Đã lưu nhật ký ngày cho {ta_name}!")
            if loi_ngay > 0: st.error(f"Tổng điểm trừ hôm nay: -{loi_ngay} điểm")

    with tab2:
        st.subheader("Kiểm tra Deadline & Họp")
        ta_name_thang = st.selectbox("Chọn nhân sự:", danh_sach_ta, key="checkin_thang")
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

# ------------------------------------------
# MÀN HÌNH 3: CÁC MỤC ĐANG PHÁT TRIỂN
# ------------------------------------------
else:
    st.title(menu)
    st.write(f"Mô đun **{menu}** đang trong quá trình phát triển (Under Construction).")
    st.info("Vui lòng chọn mục **📝 Đánh giá công việc** ở Sidebar bên trái để trải nghiệm tính năng đã hoàn thiện.")
        # Vẽ biểu đồ đường
        st.line_chart(data_loi)
