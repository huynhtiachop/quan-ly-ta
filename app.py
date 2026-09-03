import streamlit as st
import datetime
import pandas as pd
import gspread
import plotly.express as px

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
        if 'Trạng Thái' in df.columns:
            df['Trạng Thái'] = df['Trạng Thái'].astype(str).str.strip()
        cac_trang_thai_active = ['Đang làm việc', 'Đang thử việc']
        df_active = df[df['Trạng Thái'].isin(cac_trang_thai_active)]
        return df_active['Họ và tên'].tolist(), df
    except: return ["Lỗi dữ liệu"], None

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# ==========================================
# 3. ĐIỀU HƯỚNG CHÍNH
# ==========================================
with st.sidebar:
    st.markdown("### 🔴 KB-LAB")
    st.caption("*Kiến tạo chuẩn mực không gian tri thức hiện đại*")
    st.markdown("---")
    menu = st.radio("MENU QUẢN LÝ", ["🏠 Tổng quan", "👥 Quản lý Trợ giảng", "📝 Đánh giá công việc"])

today = datetime.date.today()
danh_sach_nhan_su, df_data = lay_danh_sach_ta(SHEET_CSV_URL)

# ------------------------------------------
# MÀN HÌNH 1: DASHBOARD CHỐT CÔNG
# ------------------------------------------
if menu == "🏠 Tổng quan":
    st.title("Bảng Điều Khiển & Phân Tích Dữ Liệu")
    
    st.markdown("### 🗓️ Lọc dữ liệu theo kỳ lương")
    col_thang, col_nam, col_trong = st.columns([1, 1, 2])
    with col_thang: thang_chon = st.selectbox("Chọn Tháng", list(range(1, 13)), index=today.month - 1)
    with col_nam: nam_chon = st.selectbox("Chọn Năm", [today.year - 1, today.year, today.year + 1], index=1)
    st.markdown("---")
    
    if gc:
        try:
            sh = gc.open_by_url(SHEET_MASTER_URL)
            ws_ta = sh.worksheet("Nhat_Ky_TA")
            df_ta = pd.DataFrame(ws_ta.get_all_records())
            ws_ops = sh.worksheet("Nhat_Ky_Ops")
            df_ops = pd.DataFrame(ws_ops.get_all_records())
            
            if not df_ta.empty: 
                df_ta = df_ta.rename(columns={'Tên TA': 'Tên Nhân Sự'})
                if 'Số ca' not in df_ta.columns: df_ta['Số ca'] = 0
                df_ta['Số giờ'] = 0 
                
            if not df_ops.empty: 
                df_ops = df_ops.rename(columns={'Tên Ops': 'Tên Nhân Sự'})
                if 'Số giờ' not in df_ops.columns: df_ops['Số giờ'] = 0
                df_ops['Số ca'] = 0 
            
            df_log_full = pd.concat([df_ta, df_ops], ignore_index=True)
            
            if not df_log_full.empty:
                if 'Ngày' in df_log_full.columns:
                    df_log_full['Ngày_DT'] = pd.to_datetime(df_log_full['Ngày'], errors='coerce')
                    df_log = df_log_full[(df_log_full['Ngày_DT'].dt.month == thang_chon) & (df_log_full['Ngày_DT'].dt.year == nam_chon)]
                else: df_log = pd.DataFrame()

                if not df_log.empty:
                    if 'Điểm cộng' not in df_log.columns: df_log['Điểm cộng'] = 0
                    if 'Điểm trừ' not in df_log.columns: df_log['Điểm trừ'] = 0
                    if 'Tên Nhân Sự' not in df_log.columns: df_log['Tên Nhân Sự'] = "Chưa cập nhật"

                    for col in ['Điểm trừ', 'Điểm cộng', 'Số ca', 'Số giờ']:
                        df_log[col] = pd.to_numeric(df_log[col], errors='coerce').fillna(0)

                    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                    col_kpi1.metric(f"Tổng ca làm (Tháng {thang_chon})", str(df_log['Số ca'].sum()) + " ca")
                    col_kpi2.metric("Tổng giờ Ops", f"{round(df_log['Số giờ'].sum(), 1)} h")
                    col_kpi3.metric("Tổng Điểm Cộng", str(df_log['Điểm cộng'].sum()), "Tích cực")
                    col_kpi4.metric("Tổng Điểm Trừ", str(df_log['Điểm trừ'].sum()), "Vi phạm", delta_color="inverse")
                    st.markdown("---")
                    
                    df_ranking = df_log.groupby('Tên Nhân Sự').agg(
                        Tổng_ca=('Số ca', 'sum'),
                        Tổng_giờ=('Số giờ', 'sum'),
                        Điểm_cộng=('Điểm cộng', 'sum'),
                        Điểm_trừ=('Điểm trừ', 'sum')
                    ).reset_index()
                    df_ranking['KPI_Cuối_Tháng'] = 100 + df_ranking['Điểm_cộng'] - df_ranking['Điểm_trừ']
                    df_ranking = df_ranking.sort_values(by='KPI_Cuối_Tháng', ascending=False)
                    
                    st.subheader("📈 Phân Tích Dữ Liệu Trực Quan")
                    df_trend = df_log.groupby(df_log['Ngày_DT'].dt.date).agg({'Số ca': 'sum', 'Số giờ': 'sum'}).reset_index()
                    fig_trend = px.area(df_trend, x="Ngày_DT", y=["Số ca", "Số giờ"], title="Lưu lượng công việc (Ca/Giờ) theo thời gian", labels={"Ngày_DT": "Ngày", "value": "Số lượng", "variable": "Loại công việc"}, color_discrete_sequence=['#ff4b4b', '#1f77b4'])
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        top_5 = df_ranking.head(5).sort_values(by="KPI_Cuối_Tháng", ascending=True) 
                        fig_bar = px.bar(top_5, x="KPI_Cuối_Tháng", y="Tên Nhân Sự", orientation='h', title="Top 5 Nhân Sự Xuất Sắc", color="KPI_Cuối_Tháng", color_continuous_scale="Reds")
                        st.plotly_chart(fig_bar, use_container_width=True)
                    with col_chart2:
                        df_pie = pd.DataFrame({'Phân loại': ['Điểm Thưởng', 'Điểm Phạt'], 'Điểm số': [df_log['Điểm cộng'].sum(), df_log['Điểm trừ'].sum()]})
                        fig_pie = px.pie(df_pie, names='Phân loại', values='Điểm số', hole=0.4, title="Cán cân Khen Thưởng vs Kỷ Luật", color='Phân loại', color_discrete_map={'Điểm Thưởng':'#28a745', 'Điểm Phạt':'#dc3545'})
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    st.markdown("---")
                    
                    col_header, col_btn = st.columns([3, 1])
                    with col_header: st.subheader(f"🧮 Bảng Tính Công Chi Tiết (Tháng {thang_chon}/{nam_chon})")
                    with col_btn:
                        csv = convert_df(df_ranking)
                        st.download_button(label="📥 Tải Bảng Lương (Excel/CSV)", data=csv, file_name=f"ChotCong_Thang{thang_chon}_{nam_chon}.csv", mime="text/csv")

                    st.dataframe(
                        df_ranking,
                        column_config={
                            "Tên Nhân Sự": st.column_config.TextColumn("👤 Tên Nhân Sự", width="medium"),
                            "Tổng_ca": st.column_config.NumberColumn("🔢 Tổng Ca (TA)", format="%.1f ca"),
                            "Tổng_giờ": st.column_config.NumberColumn("⏱️ Tổng Giờ (Ops)", format="%.2f h"),
                            "Điểm_cộng": st.column_config.NumberColumn("⭐ Cộng"),
                            "Điểm_trừ": st.column_config.NumberColumn("⚠️ Trừ"),
                            "KPI_Cuối_Tháng": st.column_config.ProgressColumn("🔥 ĐIỂM KPI TỔNG", format="%f", min_value=0, max_value=150),
                        }, hide_index=True, use_container_width=True
                    )
                else: st.info(f"Chưa có dữ liệu chấm công nào trong Tháng {thang_chon}/{nam_chon}.")
            else: st.info("Chưa có dữ liệu. Hãy ghi nhận ca làm đầu tiên ở mục Đánh giá công việc!")
        except Exception as e: st.warning(f"Lỗi hệ thống đọc dữ liệu: {e}")
    else: st.error("Chưa kết nối API Key.")

# ------------------------------------------
# MÀN HÌNH 2: ĐÁNH GIÁ CÔNG VIỆC & IMPORT
# ------------------------------------------
elif menu == "📝 Đánh giá công việc":
    st.title("Phân Hệ Đánh Giá & Chấm Công")
    
    col_ngay, col_trong = st.columns([1, 2])
    with col_ngay: ngay_ghi_nhan = st.date_input("🗓️ Chọn ngày ghi nhận:", today)
    doi_tuong = st.radio("Bộ phận đánh giá:", ["👥 Trợ giảng Chuyên môn (TA)", "⚙️ Trợ giảng Vận hành (Ops)"], horizontal=True)
    st.markdown("---")
    
    # THÊM TAB IMPORT DỮ LIỆU
    tab_daily, tab_deadline, tab_import = st.tabs(["📅 Chấm Công Hàng Loạt", "🚩 Tổng Kết Phạt Tháng", "⬆️ Nhập Liệu Từ Excel (Import)"])

    # --- TAB IMPORT EXCEL ---
    with tab_import:
        st.subheader("⬆️ Tải lên dữ liệu từ File Excel")
        st.info("Tính năng này giúp bạn import file lịch sử (như file Tổng Hợp Tháng 8) vào hệ thống chỉ bằng 1 nút bấm.")
        
        uploaded_file = st.file_uploader("Kéo thả file Excel vào đây (Định dạng .xlsx)", type=["xlsx"])
        
        if uploaded_file is not None:
            try:
                # Đọc dữ liệu từ file Excel tải lên
                df_import = pd.read_excel(uploaded_file)
                st.write("🔍 **Xem trước dữ liệu tải lên:**")
                st.dataframe(df_import.head(10))
                
                # Cấu hình map cột dữ liệu
                st.markdown("### ⚙️ Ghép nối cột dữ liệu (Mapping)")
                col_name_excel = st.selectbox("Chọn cột chứa TÊN NHÂN SỰ:", df_import.columns)
                
                if doi_tuong == "👥 Trợ giảng Chuyên môn (TA)":
                    col_value_excel = st.selectbox("Chọn cột chứa SỐ CA (Buổi):", df_import.columns)
                    if st.button("🚀 XÁC NHẬN ĐẨY LÊN HỆ THỐNG (TA)", type="primary"):
                        rows_to_insert = []
                        for _, row in df_import.iterrows():
                            # Mảng đẩy vào Sheet Nhat_Ky_TA
                            dong_moi = [str(ngay_ghi_nhan), str(row[col_name_excel]).strip(), "Hoàn thành", "Không", "Import từ Excel", 0, 0, 0, float(row[col_value_excel])]
                            rows_to_insert.append(dong_moi)

                        if gc and rows_to_insert:
                            gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_TA").append_rows(rows_to_insert)
                            st.success(f"✅ Đã import thành công {len(rows_to_insert)} nhân sự vào bảng Trợ giảng Chuyên môn!")
                            
                else: # Đẩy vào Ops
                    col_value_excel = st.selectbox("Chọn cột chứa SỐ GIỜ (Tiếng):", df_import.columns)
                    if st.button("🚀 XÁC NHẬN ĐẨY LÊN HỆ THỐNG (Ops)", type="primary"):
                        rows_to_insert = []
                        for _, row in df_import.iterrows():
                            # Mảng đẩy vào Sheet Nhat_Ky_Ops
                            dong_moi = [str(ngay_ghi_nhan), str(row[col_name_excel]).strip(), "Hoàn thành", "Ops", "Import từ Excel", 0, 0, 0, float(row[col_value_excel])]
                            rows_to_insert.append(dong_moi)

                        if gc and rows_to_insert:
                            gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_Ops").append_rows(rows_to_insert)
                            st.success(f"✅ Đã import thành công {len(rows_to_insert)} nhân sự vào bảng Vận hành Ops!")

            except Exception as e:
                st.error(f"❌ Có lỗi khi đọc file Excel: {e}")

    # ==========================================
    # LUỒNG 1: TRỢ GIẢNG CHUYÊN MÔN (TA) - BẢNG BULK
    # ==========================================
    if doi_tuong == "👥 Trợ giảng Chuyên môn (TA)":
        with tab_daily:
            st.info("💡 Hướng dẫn: Tích vào ô **[Làm ca này?]** cho những bạn có đi làm. Bấm LƯU 1 LẦN duy nhất ở cuối bảng.")
            df_input_ta = pd.DataFrame({
                "Làm ca này?": [False] * len(danh_sach_nhan_su),
                "Tên Nhân Sự": danh_sach_nhan_su,
                "Đi muộn (-10đ)": [False] * len(danh_sach_nhan_su),
                "Thiếu tài liệu (-2đ)": [False] * len(danh_sach_nhan_su),
                "Thiếu BTVN (-5đ)": [False] * len(danh_sach_nhan_su),
                "Thiếu Điểm (-5đ)": [False] * len(danh_sach_nhan_su),
                "Thưởng Hỗ trợ (+5đ)": [False] * len(danh_sach_nhan_su),
                "Số ca": [1.0] * len(danh_sach_nhan_su)
            })

            edited_ta = st.data_editor(
                df_input_ta,
                column_config={
                    "Làm ca này?": st.column_config.CheckboxColumn("✅ Tham gia ca?", default=False),
                    "Tên Nhân Sự": st.column_config.TextColumn("👤 Họ và Tên", disabled=True), 
                    "Đi muộn (-10đ)": st.column_config.CheckboxColumn("⚠️ Đi muộn"),
                    "Thiếu tài liệu (-2đ)": st.column_config.CheckboxColumn("⚠️ Lỗi In ấn"),
                    "Thiếu BTVN (-5đ)": st.column_config.CheckboxColumn("⚠️ Lỗi BTVN"),
                    "Thiếu Điểm (-5đ)": st.column_config.CheckboxColumn("⚠️ Lỗi Nhập Điểm"),
                    "Thưởng Hỗ trợ (+5đ)": st.column_config.CheckboxColumn("⭐ Support Tốt"),
                    "Số ca": st.column_config.NumberColumn("🔢 Ca làm", min_value=0.5, step=0.5, format="%.1f")
                },
                hide_index=True, use_container_width=True
            )

            if st.button("🚀 LƯU ĐÁNH GIÁ TẤT CẢ TA"):
                danh_sach_di_lam = edited_ta[edited_ta["Làm ca này?"] == True]
                if danh_sach_di_lam.empty: st.warning("Bạn chưa tích chọn nhân sự nào đi làm trong ca này!")
                else:
                    rows_to_insert = []
                    for index, row in danh_sach_di_lam.iterrows():
                        diem_tru = (10 if row['Đi muộn (-10đ)'] else 0) + (2 if row['Thiếu tài liệu (-2đ)'] else 0) + (5 if row['Thiếu BTVN (-5đ)'] else 0) + (5 if row['Thiếu Điểm (-5đ)'] else 0)
                        diem_cong = 5 if row['Thưởng Hỗ trợ (+5đ)'] else 0
                        dong_moi = [str(ngay_ghi_nhan), row['Tên Nhân Sự'], "Có lỗi" if diem_tru > 0 else "Hoàn thành", "Không", "Bulk Check-in", diem_tru, diem_cong, 0, row['Số ca']]
                        rows_to_insert.append(dong_moi)

                    if gc and rows_to_insert:
                        try:
                            gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_TA").append_rows(rows_to_insert)
                            st.success(f"✅ Đã lưu thành công chấm công cho {len(rows_to_insert)} nhân sự TA!")
                        except Exception as e: st.error(f"Lỗi kết nối ghi dữ liệu: {e}")
        
        with tab_deadline:
            st.subheader("Cập nhật Phạt/Thưởng Tháng (Cá nhân)")
            ta_dl_name = st.selectbox("Chọn nhân sự (TA):", danh_sach_nhan_su, key="ta_name_dl")
            st.markdown("**1. Vi phạm Deadline (Tính điểm trừ):**")
            tre_ph = st.number_input("Trễ Báo cáo Phụ huynh (Hạn mùng 1) [-10đ/ngày]:", min_value=0, max_value=30, value=0)
            tre_bg = st.number_input("Trễ Báo giảng (Hạn mùng 5) [-5đ/ngày]:", min_value=0, max_value=30, value=0)
            tre_luong = st.number_input("Trễ Chốt lương TA (Hạn mùng 8) [-10đ/ngày]:", min_value=0, max_value=30, value=0)
            st.markdown("**2. Thành tích xuất sắc (Tính điểm cộng):**")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                thuong_feedback = st.checkbox("⭐ Nhận feedback rất tốt từ học sinh (+5đ)")
                thuong_diemcao = st.checkbox("⭐ Học sinh đạt điểm cao/vượt đầu ra (+10đ)")
            with col_m2:
                thuong_baogiang = st.checkbox("⭐ Báo giảng đầy đủ, sớm trước hạn (+5đ)")
                thuong_idea = st.checkbox("⭐ Đóng góp idea phát triển trung tâm (+5đ)")
            idea_text = st.text_input("💡 Nhập chi tiết ý tưởng của bạn TA này:") if thuong_idea else ""

            if st.button("💾 Lưu Phạt/Thưởng Tháng"):
                diem_phat_dl = (tre_ph * 10) + (tre_bg * 5) + (tre_luong * 10)
                diem_cong_thang = (5 if thuong_feedback else 0) + (10 if thuong_diemcao else 0) + (5 if thuong_baogiang else 0) + (5 if thuong_idea else 0)
                ghi_chu = []
                if diem_phat_dl > 0: ghi_chu.append(f"Trễ DL: {tre_ph}d PH, {tre_bg}d BG, {tre_luong}d Lương")
                if thuong_idea and idea_text: ghi_chu.append(f"Idea: {idea_text}")
                
                if diem_phat_dl > 0 or diem_cong_thang > 0:
                    if gc:
                        gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_TA").append_row([str(ngay_ghi_nhan), ta_dl_name, "Tổng kết Tháng", "Không", " | ".join(ghi_chu) if ghi_chu else "Tổng kết", diem_phat_dl, diem_cong_thang, 0, 0])
                        st.toast(f"Đã lưu KPI tháng cho {ta_dl_name}!", icon="🌟")
                else: st.info("Chưa có vi phạm hay điểm cộng nào được nhập.")

    # ==========================================
    # LUỒNG 2: TRỢ GIẢNG VẬN HÀNH (OPS) - BẢNG BULK
    # ==========================================
    else:
        try: danh_sach_ops = df_data[(df_data['Vai trò'].str.contains("Vận hành|Quản lý", na=False, case=False)) & (df_data['Họ và tên'].isin(danh_sach_nhan_su))]['Họ và tên'].tolist()
        except: danh_sach_ops = danh_sach_nhan_su
        if not danh_sach_ops: danh_sach_ops = danh_sach_nhan_su
            
        with tab_daily:
            st.info("💡 Hướng dẫn: Tích vào ô **[Làm ca này?]** cho Ops đi làm. Bấm LƯU 1 LẦN ở cuối bảng.")
            df_input_ops = pd.DataFrame({
                "Làm ca này?": [False] * len(danh_sach_ops),
                "Tên Nhân Sự": danh_sach_ops,
                "Đi muộn (-5đ)": [False] * len(danh_sach_ops),
                "Lỗi Cơ sở VC (-2đ)": [False] * len(danh_sach_ops),
                "Lỗi Sĩ số (-5đ)": [False] * len(danh_sach_ops),
                "Lỗi Phàn nàn (-15đ)": [False] * len(danh_sach_ops),
                "Thưởng (+5đ)": [False] * len(danh_sach_ops),
                "Số giờ làm": [4.0] * len(danh_sach_ops)
            })

            edited_ops = st.data_editor(
                df_input_ops,
                column_config={
                    "Làm ca này?": st.column_config.CheckboxColumn("✅ Tham gia ca?", default=False),
                    "Tên Nhân Sự": st.column_config.TextColumn("👤 Họ và Tên", disabled=True),
                    "Đi muộn (-5đ)": st.column_config.CheckboxColumn("⚠️ Đi muộn"),
                    "Lỗi Cơ sở VC (-2đ)": st.column_config.CheckboxColumn("⚠️ Lỗi CSVC/In ấn"),
                    "Lỗi Sĩ số (-5đ)": st.column_config.CheckboxColumn("⚠️ Lỗi Sĩ số"),
                    "Lỗi Phàn nàn (-15đ)": st.column_config.CheckboxColumn("⚠️ Bị phàn nàn"),
                    "Thưởng (+5đ)": st.column_config.CheckboxColumn("⭐ Xử lý sự cố xuất sắc"),
                    "Số giờ làm": st.column_config.NumberColumn("⏱️ Tổng Giờ", min_value=0.5, step=0.5, format="%.1f")
                },
                hide_index=True, use_container_width=True
            )

            if st.button("🚀 LƯU ĐÁNH GIÁ TẤT CẢ OPS"):
                danh_sach_ops_lam = edited_ops[edited_ops["Làm ca này?"] == True]
                if danh_sach_ops_lam.empty: st.warning("Bạn chưa tích chọn nhân sự Ops nào đi làm!")
                else:
                    rows_ops_insert = []
                    for index, row in danh_sach_ops_lam.iterrows():
                        diem_tru_ops = (5 if row['Đi muộn (-5đ)'] else 0) + (2 if row['Lỗi Cơ sở VC (-2đ)'] else 0) + (5 if row['Lỗi Sĩ số (-5đ)'] else 0) + (15 if row['Lỗi Phàn nàn (-15đ)'] else 0)
                        diem_cong_ops = 5 if row['Thưởng (+5đ)'] else 0
                        dong_ops_moi = [str(ngay_ghi_nhan), row['Tên Nhân Sự'], "Có lỗi" if diem_tru_ops > 0 else "Hoàn thành", "Ops", "Bulk Check-in", diem_tru_ops, diem_cong_ops, 0, row['Số giờ làm']]
                        rows_ops_insert.append(dong_ops_moi)

                    if gc and rows_ops_insert:
                        try:
                            gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_Ops").append_rows(rows_ops_insert)
                            st.success(f"✅ Đã lưu thành công chấm công cho {len(rows_ops_insert)} nhân sự Ops!")
                        except Exception as e: st.error(f"Lỗi ghi dữ liệu: {e}")
                    
        with tab_deadline:
            st.subheader("Phạt Chậm Deadline Tháng (Ops)")
            ops_dl_name = st.selectbox("Chọn nhân sự (Ops):", danh_sach_ops, key="ops_name_dl")
            tre_luong_ops = st.number_input("Trễ Chốt lương Ops (Hạn mùng 5) [-10đ/ngày]:", min_value=0, max_value=30, value=0)
            
            if st.button("💾 Lưu Phạt Deadline Ops"):
                diem_phat_ops = tre_luong_ops * 10
                if diem_phat_ops > 0:
                    if gc:
                        gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_Ops").append_row([str(ngay_ghi_nhan), ops_dl_name, "Vi phạm Deadline", "Ops", f"Trễ Lương: {tre_luong_ops}d", diem_phat_ops, 0, 0, 0])
                        st.toast(f"Đã trừ {diem_phat_ops} điểm deadline của {ops_dl_name}!", icon="🚨")
                else: st.info("Nhân sự nộp đúng hạn, không có điểm phạt.")

# ------------------------------------------
# MÀN HÌNH 3: QUẢN LÝ NHÂN SỰ
# ------------------------------------------
elif menu == "👥 Quản lý Trợ giảng":
    st.title("Hồ Sơ & Danh Bạ Nhân Sự")
    if df_data is not None:
        try: st.dataframe(df_data[['Họ và tên', 'Số điện thoại', 'Email', 'Vai trò', 'Trạng Thái']], use_container_width=True, hide_index=True)
        except: st.dataframe(df_data)
