import streamlit as st
import datetime
import pandas as pd
import gspread

# ==========================================
# 1. CẤU HÌNH TRANG & UI
# ==========================================
st.set_page_config(page_title="KB-LAB | Quản Lý Nhân Sự", page_icon="🔴", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; }
    
    [data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 2px solid #800000; }
    [data-testid="stSidebar"] * { color: #F5F7FA !important; }
    
    h1, h2, h3, h4, h5, h6 { color: #2D2D2D !important; font-weight: 700; }
    
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
    
    [data-testid="metric-container"] {
        background-color: white; border-radius: 12px; padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KẾT NỐI DỮ LIỆU
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

with st.sidebar:
    st.markdown("### 🔴 KB-LAB")
    st.caption("*Kiến tạo chuẩn mực không gian tri thức hiện đại*")
    st.markdown("---")
    menu = st.radio("MENU QUẢN LÝ", ["🏠 Tổng quan", "👥 Quản lý Trợ giảng", "📝 Đánh giá công việc"])

today = datetime.date.today()

# ------------------------------------------
# MÀN HÌNH 1: DASHBOARD & XẾP HẠNG
# ------------------------------------------
if menu == "🏠 Tổng quan":
    st.title("Bảng Điều Khiển & Xếp Hạng Nhân Sự")
    
    if gc:
        try:
            sh = gc.open_by_url(SHEET_MASTER_URL)
            
            ws_ta = sh.worksheet("Nhat_Ky_TA")
            df_ta = pd.DataFrame(ws_ta.get_all_records())
            ws_ops = sh.worksheet("Nhat_Ky_Ops")
            df_ops = pd.DataFrame(ws_ops.get_all_records())
            
            if not df_ta.empty: df_ta = df_ta.rename(columns={'Tên TA': 'Tên Nhân Sự'})
            if not df_ops.empty: df_ops = df_ops.rename(columns={'Tên Ops': 'Tên Nhân Sự'})
            
            df_log = pd.concat([df_ta, df_ops], ignore_index=True)
            
            if not df_log.empty:
                # Chống sập App nếu thiếu cột
                if 'Điểm cộng' not in df_log.columns: df_log['Điểm cộng'] = 0
                if 'Điểm trừ' not in df_log.columns: df_log['Điểm trừ'] = 0
                if 'Tên Nhân Sự' not in df_log.columns: df_log['Tên Nhân Sự'] = "Chưa cập nhật"

                for col in ['Điểm trừ', 'Điểm cộng']:
                    df_log[col] = pd.to_numeric(df_log[col], errors='coerce').fillna(0)

                col1, col2, col3 = st.columns(3)
                col1.metric("Tổng lượt ghi nhận", str(len(df_log)))
                col2.metric("Tổng điểm Cộng (Toàn Team)", str(df_log['Điểm cộng'].sum()), "Tích cực")
                col3.metric("Tổng điểm Trừ (Toàn Team)", str(df_log['Điểm trừ'].sum()), "Cần khắc phục", delta_color="inverse")
                st.markdown("---")
                
                # BẢNG XẾP HẠNG
                st.subheader("🏆 Bảng Xếp Hạng KPI (Quỹ chuẩn: 100đ/tháng)")
                
                df_ranking = df_log.groupby('Tên Nhân Sự').agg(
                    Số_ca_Ghi_nhận=('Ngày', 'count'),
                    Điểm_cộng=('Điểm cộng', 'sum'),
                    Điểm_trừ=('Điểm trừ', 'sum')
                ).reset_index()
                
                df_ranking['KPI_Cuối_Tháng'] = 100 + df_ranking['Điểm_cộng'] - df_ranking['Điểm_trừ']
                df_ranking = df_ranking.sort_values(by='KPI_Cuối_Tháng', ascending=False)
                
                st.dataframe(
                    df_ranking,
                    column_config={
                        "Tên Nhân Sự": st.column_config.TextColumn("👤 Tên Nhân Sự", width="medium"),
                        "Số_ca_Ghi_nhận": st.column_config.NumberColumn("📅 Tần suất"),
                        "Điểm_cộng": st.column_config.NumberColumn("⭐ Điểm Cộng"),
                        "Điểm_trừ": st.column_config.NumberColumn("⚠️ Điểm Trừ"),
                        "KPI_Cuối_Tháng": st.column_config.ProgressColumn(
                            "🔥 KPI ĐÁNH GIÁ (Trên 100)",
                            format="%f", min_value=0, max_value=130
                        ),
                    },
                    hide_index=True, use_container_width=True
                )
            else: st.info("Chưa có dữ liệu. Hãy ghi nhận ca làm đầu tiên!")
        except Exception as e: st.warning(f"Lỗi hệ thống: {e}")
    else: st.error("Chưa kết nối API Key.")

# ------------------------------------------
# MÀN HÌNH 2: ĐÁNH GIÁ CÔNG VIỆC
# ------------------------------------------
elif menu == "📝 Đánh giá công việc":
    st.title("Phân Hệ Đánh Giá KPI")
    
    col_ngay, col_trong = st.columns([1, 2])
    with col_ngay: ngay_ghi_nhan = st.date_input("🗓️ Chọn ngày ghi nhận:", today)
    
    doi_tuong = st.radio("Bộ phận đánh giá:", ["👥 Trợ giảng Chuyên môn (TA)", "⚙️ Trợ giảng Vận hành (Ops)"], horizontal=True)
    st.markdown("---")
    
    danh_sach_nhan_su, df_data = lay_danh_sach_ta(SHEET_CSV_URL)
    
    tab_daily, tab_deadline = st.tabs(["📅 Check-in Hàng Ngày", "🚩 Tổng Kết & Chấm Điểm Tháng"])

    # ==========================================
    # LUỒNG 1: TRỢ GIẢNG CHUYÊN MÔN (TA)
    # ==========================================
    if doi_tuong == "👥 Trợ giảng Chuyên môn (TA)":
        with tab_daily:
            st.subheader("Bảng Đánh Giá Task Hàng Ngày (TA)")
            ta_name = st.selectbox("Chọn nhân sự (TA):", danh_sach_nhan_su, key="ta_name_daily")
            
            nguoi_di_thay = st.selectbox("👤 Đi thay cho ai? (Bỏ trống nếu đi ca chính):", [""] + danh_sach_nhan_su)
            
            st.markdown("**1. Công việc bắt buộc (Nếu thiếu sẽ bị trừ điểm):**")
            ta_t1 = st.checkbox("✅ Điểm danh chuẩn & Chuẩn bị đủ tài liệu in ấn (Nếu thiếu/sai: -2đ)", value=True)
            ta_t2 = st.checkbox("✅ Check 100% BTVN của học sinh (Nếu bỏ sót: -5đ)", value=True)
            ta_t3 = st.checkbox("✅ Cập nhật đủ điểm & Hỗ trợ học sinh trên lớp (Nếu thiếu: -5đ)", value=True)

            st.markdown("**2. Hoạt động xuất sắc ca làm (Cộng điểm):**")
            ta_b1 = st.checkbox("⭐ Chủ động hỗ trợ GV/Ops hoặc làm thêm giờ ngoài nhiệm vụ (+5đ)")

            if st.button("💾 Lưu Check-in TA"):
                diem_tru = (0 if ta_t1 else 2) + (0 if ta_t2 else 5) + (0 if ta_t3 else 5)
                diem_cong = 5 if ta_b1 else 0
                
                if gc:
                    try:
                        ws = gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_TA")
                        dong_moi = [str(ngay_ghi_nhan), ta_name, "Ca làm việc", nguoi_di_thay if nguoi_di_thay else "Không", "Ghi nhận Daily", diem_tru, diem_cong, 0]
                        ws.append_row(dong_moi)
                        st.toast(f"Đã lưu Daily Task cho {ta_name}! (Trừ: {diem_tru} | Cộng: {diem_cong})", icon="🎉")
                    except Exception as e: st.error(f"Lỗi ghi dữ liệu: {e}")
        
        with tab_deadline:
            st.subheader("Tổng Kết Hiệu Suất Tháng (TA)")
            ta_dl_name = st.selectbox("Chọn nhân sự (TA):", danh_sach_nhan_su, key="ta_name_dl")
            
            st.markdown("**1. Vi phạm Deadline (Tính điểm trừ):**")
            tre_ph = st.number_input("Trễ Báo cáo Phụ huynh (Hạn mùng 1) [-10đ/ngày]:", min_value=0, max_value=30, value=0)
            tre_bg = st.number_input("Trễ Báo giảng (Hạn mùng 5) [-5đ/ngày]:", min_value=0, max_value=30, value=0)
            tre_luong = st.number_input("Trễ Chốt lương TA (Hạn mùng 8) [-10đ/ngày]:", min_value=0, max_value=30, value=0)
            
            st.markdown("**2. Thành tích xuất sắc trong tháng (Tính điểm cộng):**")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                thuong_feedback = st.checkbox("⭐ Nhận ý kiến/feedback rất tốt từ học sinh (+5đ)")
                thuong_diemcao = st.checkbox("⭐ Có học sinh đạt điểm cao/vượt chuẩn đầu ra (+10đ)")
            with col_m2:
                thuong_baogiang = st.checkbox("⭐ Báo giảng viết đầy đủ, nộp sớm trước hạn (+5đ)")
                thuong_idea = st.checkbox("⭐ Đóng góp idea/góp ý phát triển trung tâm (+5đ)")
            
            # Ô nhập liệu thông minh: Chỉ hiện ra khi tick chọn tính năng góp ý
            idea_text = ""
            if thuong_idea:
                idea_text = st.text_input("💡 Nhập chi tiết ý tưởng/góp ý của bạn TA này (sẽ lưu vào file báo cáo):")

            if st.button("💾 Lưu Tổng Kết Tháng TA"):
                diem_phat_dl = (tre_ph * 10) + (tre_bg * 5) + (tre_luong * 10)
                diem_cong_thang = (5 if thuong_feedback else 0) + (10 if thuong_diemcao else 0) + (5 if thuong_baogiang else 0) + (5 if thuong_idea else 0)
                
                # Tạo chuỗi ghi chú để lưu vào Excel
                ghi_chu_list = []
                if diem_phat_dl > 0: ghi_chu_list.append(f"Trễ DL: {tre_ph}d PH, {tre_bg}d BG, {tre_luong}d Lương")
                if thuong_idea and idea_text: ghi_chu_list.append(f"Idea: {idea_text}")
                
                ghi_chu_str = " | ".join(ghi_chu_list) if ghi_chu_list else "Tổng kết tháng (Không có ghi chú)"
                
                if diem_phat_dl > 0 or diem_cong_thang > 0:
                    if gc:
                        try:
                            ws = gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_TA")
                            ws.append_row([str(ngay_ghi_nhan), ta_dl_name, "Tổng kết Tháng", "Không", ghi_chu_str, diem_phat_dl, diem_cong_thang, 0])
                            st.toast(f"Đã lưu KPI tháng cho {ta_dl_name}! (Trừ: {diem_phat_dl} | Cộng: {diem_cong_thang})", icon="🌟")
                        except Exception as e: st.error(f"Lỗi: {e}")
                else: st.info("Trợ giảng này không có vi phạm deadline cũng như điểm cộng trong tháng.")

    # ==========================================
    # LUỒNG 2: TRỢ GIẢNG VẬN HÀNH (OPS)
    # ==========================================
    else:
        try: danh_sach_ops = df_data[df_data['Vai trò'].str.contains("Vận hành|Quản lý", na=False, case=False)]['Họ và tên'].tolist()
        except: danh_sach_ops = danh_sach_nhan_su
        if not danh_sach_ops: danh_sach_ops = danh_sach_nhan_su
            
        with tab_daily:
            st.subheader("Bảng Đánh Giá Task Hàng Ngày (Ops)")
            ops_name = st.selectbox("Chọn nhân sự (Ops):", danh_sach_ops, key="ops_name_daily")
            
            st.markdown("**1. Công việc bắt buộc (Nếu thiếu sẽ bị trừ điểm):**")
            ops_t1 = st.checkbox("✅ Có mặt tại trung tâm đúng giờ, trước 18h15 (Nếu đi muộn: -5đ)", value=True)
            ops_t2 = st.checkbox("✅ In ấn đủ & Đảm bảo vệ sinh sạch sẽ các phòng học (Nếu thiếu: -2đ)", value=True)
            ops_t3 = st.checkbox("✅ Kiểm soát sĩ số, gọi điện lý do vắng & Ghi danh chuẩn (Sai sót: -5đ)", value=True)
            ops_t4 = st.checkbox("✅ Xử lý phát sinh & Support học viên/lớp kịp thời (Nếu chậm trễ: -3đ)", value=True)

            st.markdown("**2. Hoạt động xuất sắc (Cộng điểm):**")
            ops_b1 = st.checkbox("⭐ Xử lý sự cố khó cực kỳ khéo léo/Được PH khen (+5đ)", value=False)

            if st.button("💾 Lưu Check-in Ops"):
                diem_tru_ops = (0 if ops_t1 else 5) + (0 if ops_t2 else 2) + (0 if ops_t3 else 5) + (0 if ops_t4 else 3)
                diem_cong_ops = 5 if ops_b1 else 0
                
                if gc:
                    try:
                        ws_ops = gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_Ops")
                        ws_ops.append_row([str(ngay_ghi_nhan), ops_name, "Có lỗi" if diem_tru_ops>0 else "Tốt", "Ops", "Ghi nhận Daily", diem_tru_ops, diem_cong_ops, 0])
                        st.toast(f"Đã lưu Daily Task Ops cho {ops_name}! (Trừ: {diem_tru_ops} | Cộng: {diem_cong_ops})", icon="🎉")
                    except Exception as e: st.error(f"Lỗi ghi dữ liệu: {e}")
                    
        with tab_deadline:
            st.subheader("Phạt Chậm Deadline Tháng (Ops)")
            ops_dl_name = st.selectbox("Chọn nhân sự (Ops):", danh_sach_ops, key="ops_name_dl")
            
            tre_luong_ops = st.number_input("Trễ Chốt lương Ops (Hạn mùng 5) [-10đ/ngày]:", min_value=0, max_value=30, value=0)
            
            if st.button("💾 Lưu Phạt Deadline Ops"):
                diem_phat_ops = tre_luong_ops * 10
                if diem_phat_ops > 0:
                    if gc:
                        ws_ops = gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_Ops")
                        ws_ops.append_row([str(ngay_ghi_nhan), ops_dl_name, "Vi phạm Deadline", "Ops", f"Trễ Lương: {tre_luong_ops}d", diem_phat_ops, 0, 0])
                        st.toast(f"Đã trừ {diem_phat_ops} điểm deadline của {ops_dl_name}!", icon="🚨")
                else: st.info("Nhân sự nộp đúng hạn, không có điểm phạt.")

# ------------------------------------------
# MÀN HÌNH 3: QUẢN LÝ NHÂN SỰ
# ------------------------------------------
elif menu == "👥 Quản lý Trợ giảng":
    st.title("Hồ Sơ & Điều Phối Nhân Sự")
    danh_sach_ta, df_data = lay_danh_sach_ta(SHEET_CSV_URL)
    
    if df_data is not None:
        try: st.dataframe(df_data[['Họ và tên', 'Số điện thoại', 'Email', 'Vai trò']], use_container_width=True, hide_index=True)
        except: st.dataframe(df_data)
