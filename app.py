import streamlit as st
import datetime
import pandas as pd
import gspread

# ==========================================
# 1. CẤU HÌNH TRANG & UI
# ==========================================
st.set_page_config(page_title="KB-LAB | Quản Lý Nhân Sự", page_icon="🔴", layout="wide")

# Nâng cấp CSS: Thêm hiệu ứng bo góc mượt mà và bóng đổ (Shadow)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; }
    
    /* Thiết kế thanh Sidebar */
    [data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 2px solid #800000; }
    [data-testid="stSidebar"] * { color: #F5F7FA !important; }
    
    h1, h2, h3, h4, h5, h6 { color: #2D2D2D !important; font-weight: 700; }
    
    /* Thiết kế nút bấm chuẩn SaaS */
    .stButton>button {
        background: linear-gradient(135deg, #8B0000 0%, #FF0000 100%);
        color: white !important; border: none; border-radius: 8px; 
        padding: 10px 24px; font-weight: 600; width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background: linear-gradient(135deg, #FF0000 0%, #8B0000 100%);
        box-shadow: 0 6px 12px rgba(230, 0, 0, 0.3); transform: translateY(-2px);
    }
    
    /* Hiệu ứng nổi cho các ô Metric (Thống kê) */
    [data-testid="metric-container"] {
        background-color: white; border-radius: 12px; padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;
    }
    
    /* Thiết kế ô nhập liệu */
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"] {
        background-color: white !important; border-radius: 8px; 
        border: 1px solid #E2E8F0; color: #2D2D2D !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KẾT NỐI DỮ LIỆU GOOGLE SHEETS
# ==========================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSVb3rLLnxyEcojV3neR2SWmZViC4GMRy-uRrDhb6d4o84UaE5C_Po9NQZDc-Hduc1ZQVAaRAUYxDR5/pub?output=csv"
SHEET_MASTER_URL = "https://docs.google.com/spreadsheets/d/1KV7lcDuBMG1i0u4IEaBuBRNkhAxlWxEJgLBSkgpWtyI/edit"

@st.cache_resource
def init_gspread():
    try:
        credentials = dict(st.secrets["gcp_service_account"])
        return gspread.service_account_from_dict(credentials)
    except: return None

gc = init_gspread()

@st.cache_data(ttl=10)
def lay_danh_sach_ta(url):
    try:
        df = pd.read_csv(url)
        df_active = df[df['Trạng Thái'] == 'Đang làm việc']
        return df_active['Họ và tên'].tolist(), df_active
    except: return ["Lỗi dữ liệu"], None

# ==========================================
# 3. THANH ĐIỀU HƯỚNG BÊN TRÁI
# ==========================================
with st.sidebar:
    st.markdown("### 🔴 KB-LAB")
    st.caption("*Kiến tạo chuẩn mực không gian tri thức hiện đại*")
    st.markdown("---")
    menu = st.radio("MENU QUẢN LÝ", ["🏠 Tổng quan", "👥 Quản lý Trợ giảng", "📝 Đánh giá công việc"])

# ------------------------------------------
# MÀN HÌNH 1: DASHBOARD TỰ ĐỘNG CẬP NHẬT
# ------------------------------------------
if menu == "🏠 Tổng quan":
    st.title("Bảng Điều Khiển (Dashboard)")
    
    if gc:
        try:
            sh = gc.open_by_url(SHEET_MASTER_URL)
            ws_ta = sh.worksheet("Nhat_Ky_TA")
            data_ta = ws_ta.get_all_records()
            df_log = pd.DataFrame(data_ta)
            
            if not df_log.empty:
                st.write("Thống kê hiệu suất và chuyên cần dựa trên dữ liệu thực tế.")
                
                tong_luot_diem_danh = len(df_log)
                di_muon = len(df_log[df_log['Trạng thái'].str.contains('muộn', na=False, case=False)])
                ty_le_muon = round((di_muon / tong_luot_diem_danh) * 100, 1) if tong_luot_diem_danh > 0 else 0
                tong_diem_tru = df_log['Điểm trừ'].sum() if 'Điểm trừ' in df_log.columns else 0

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Tổng lượt Check-in", str(tong_luot_diem_danh))
                col2.metric("Tỷ lệ đi muộn", f"{ty_le_muon}%", "Cần chú ý" if ty_le_muon > 10 else "Tốt", delta_color="inverse")
                col3.metric("Tổng điểm trừ hệ thống", str(tong_diem_tru))
                col4.metric("Trạng thái", "Đang đồng bộ", "Realtime")
                st.markdown("---")
                
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.subheader("Biểu đồ Điểm trừ theo Nhân sự")
                    try:
                        df_chart_ta = df_log.groupby('Tên TA')['Điểm trừ'].sum().reset_index()
                        df_chart_ta = df_chart_ta.set_index('Tên TA')
                        st.bar_chart(df_chart_ta)
                    except: st.write("Chưa đủ dữ liệu để vẽ biểu đồ điểm trừ.")
                    
                with col_chart2:
                    st.subheader("Thống kê tình trạng chuyên cần")
                    try:
                        df_chuyen_can = df_log['Trạng thái'].value_counts().reset_index()
                        df_chuyen_can.columns = ['Trạng thái', 'Số lượng']
                        df_chuyen_can = df_chuyen_can.set_index('Trạng thái')
                        st.bar_chart(df_chuyen_can)
                    except: st.write("Chưa đủ dữ liệu để vẽ biểu đồ chuyên cần.")
            else:
                st.info("Bảng nhật ký đang trống. Hãy qua mục 'Đánh giá công việc' để ghi nhận ca làm đầu tiên!")
                
        except Exception as e:
            st.warning("Chưa kết nối được trang tính Nhat_Ky_TA. Hãy chắc chắn bạn đã tạo Sheet này và có dòng tiêu đề.")
    else:
        st.error("Chưa cấu hình API Key Google Sheets trong mục Secrets của Streamlit.")

# ------------------------------------------
# MÀN HÌNH 2: ĐÁNH GIÁ CÔNG VIỆC (CÓ CHỌN NGÀY & TOAST)
# ------------------------------------------
elif menu == "📝 Đánh giá công việc":
    st.title("Phân Hệ Đánh Giá Nhân Sự")
    
    # --- TÍNH NĂNG MỚI: CHỌN NGÀY LINH HOẠT ---
    col_ngay, col_trong = st.columns([1, 2])
    with col_ngay:
        ngay_ghi_nhan = st.date_input("🗓️ Chọn ngày ghi nhận ca làm:", datetime.date.today())
    
    doi_tuong = st.radio("Lựa chọn vị trí:", ["👥 Đội ngũ Trợ giảng (TA)", "⚙️ Đội ngũ Vận hành lớp (Ops)"], horizontal=True)
    st.markdown("---")
    
    danh_sach_nhan_su, df_data = lay_danh_sach_ta(SHEET_CSV_URL)

    # ==== ĐÁNH GIÁ TRỢ GIẢNG ====
    if doi_tuong == "👥 Đội ngũ Trợ giảng (TA)":
        st.subheader("Đánh giá nhiệm vụ TA")
        ta_name = st.selectbox("Chọn nhân sự (TA):", danh_sach_nhan_su)
        
        chuyen_can = st.radio("Tình trạng đi làm ca này:", ["Đi đủ / Đúng giờ", "Đi muộn / Nghỉ (Có báo trước, có SP)", "Đi muộn (Không báo, không có SP)"])
        nguoi_di_thay = None
        if chuyen_can == "Đi muộn / Nghỉ (Có báo trước, có SP)":
            danh_sach_sp = [ta for ta in danh_sach_nhan_su if ta != ta_name]
            nguoi_di_thay = st.selectbox("👤 Chọn người đi thay (SP):", danh_sach_sp)
        
        st.markdown("**Nhiệm vụ lớp học:**")
        col1, col2 = st.columns(2)
        with col1: nhap_diem = st.checkbox("Đã nhập điểm số lớp", value=True)
        with col2: diem_danh = st.checkbox("Đã điểm danh học viên", value=True)

        if st.button("💾 Lưu Check-in TA"):
            loi_ngay = 0
            if chuyen_can == "Đi muộn (Không báo, không có SP)": loi_ngay += 10
            if not nhap_diem: loi_ngay += 2
            if not diem_danh: loi_ngay += 2
            
            if gc:
                try:
                    sh = gc.open_by_url(SHEET_MASTER_URL)
                    ws = sh.worksheet("Nhat_Ky_TA")
                    # Sử dụng ngay_ghi_nhan thay vì today
                    dong_moi = [str(ngay_ghi_nhan), ta_name, chuyen_can, nguoi_di_thay if nguoi_di_thay else "Không", "Có lỗi" if loi_ngay > 0 else "Hoàn thành", loi_ngay]
                    ws.append_row(dong_moi)
                    
                    # Hiển thị Toast mượt mà
                    st.toast(f"Đã lưu thành công dữ liệu ngày {ngay_ghi_nhan.strftime('%d/%m')} cho {ta_name}!", icon="🎉")
                    
                    if nguoi_di_thay: st.info(f"🔄 Ca làm việc này tính cho SP: {nguoi_di_thay}")
                    if loi_ngay > 0: st.error(f"📉 Tổng điểm trừ ca này: -{loi_ngay} điểm")
                except Exception as e:
                    st.error(f"❌ Lỗi ghi dữ liệu vào Nhat_Ky_TA. Chi tiết: {e}")
            else:
                st.error("Chưa kết nối API Google Sheets.")

    # ==== ĐÁNH GIÁ VẬN HÀNH LỚP ====
    else:
        st.subheader("Check-list Vận Hành Lớp")
        try:
            danh_sach_ops = df_data[df_data['Vai trò'].str.contains("Vận hành|Quản lý", na=False, case=False)]['Họ và tên'].tolist()
            if not danh_sach_ops: danh_sach_ops = danh_sach_nhan_su 
        except: danh_sach_ops = danh_sach_nhan_su 
            
        ops_name = st.selectbox("Chọn nhân sự Vận hành:", danh_sach_ops)
        
        st.markdown("**1. Công tác chuẩn bị (Trước giờ học):**")
        col_op1, col_op2 = st.columns(2)
        with col_op1: setup_phong = st.checkbox("Setup phòng ốc hoàn tất", value=True)
        with col_op2: in_an = st.checkbox("Đã in ấn đủ tài liệu", value=True)
        
        co_su_co = st.radio("Lớp học hôm nay có phát sinh sự cố không?", ["Không có sự cố", "Có sự cố (Đã xử lý tốt)", "Có sự cố (Chưa xử lý được/Phàn nàn)"])
        bao_cao_lop = st.checkbox("Cập nhật nhật ký lớp học & Sĩ số", value=True)

        if st.button("💾 Lưu Check-in Vận Hành"):
            diem_tru_ops = 0
            if not setup_phong: diem_tru_ops += 5
            if not in_an: diem_tru_ops += 5
            if co_su_co == "Có sự cố (Chưa xử lý được/Phàn nàn)": diem_tru_ops += 15
            if not bao_cao_lop: diem_tru_ops += 10
            
            if gc:
                try:
                    sh = gc.open_by_url(SHEET_MASTER_URL)
                    ws_ops = sh.worksheet("Nhat_Ky_Ops")
                    # Sử dụng ngay_ghi_nhan thay vì today
                    dong_ops_moi = [str(ngay_ghi_nhan), ops_name, "Xong" if setup_phong and in_an else "Thiếu sót", co_su_co, "Xong" if bao_cao_lop else "Chưa", diem_tru_ops]
                    ws_ops.append_row(dong_ops_moi)
                    
                    # Hiển thị Toast mượt mà
                    st.toast(f"Đã lưu kết quả Ops ngày {ngay_ghi_nhan.strftime('%d/%m')} cho {ops_name}!", icon="🎉")
                    
                    if diem_tru_ops > 0: st.error(f"📉 Điểm trừ vận hành ca này: -{diem_tru_ops} điểm")
                except Exception as e:
                    st.error(f"❌ Lỗi ghi dữ liệu. Bạn đã tạo sheet 'Nhat_Ky_Ops' chưa? Chi tiết: {e}")

# ------------------------------------------
# MÀN HÌNH 3: QUẢN LÝ NHÂN SỰ
# ------------------------------------------
elif menu == "👥 Quản lý Trợ giảng":
    st.title("Hồ Sơ & Điều Phối Nhân Sự")
    danh_sach_ta, df_data = lay_danh_sach_ta(SHEET_CSV_URL)
    
    if df_data is not None:
        try:
            bang_hien_thi = df_data[['Họ và tên', 'Số điện thoại', 'Email', 'Vai trò']]
            st.dataframe(bang_hien_thi, use_container_width=True, hide_index=True)
        except KeyError: st.dataframe(df_data) 
    else: st.warning("Chưa tải được danh sách từ Google Sheets.")
