import streamlit as st
import datetime
import pandas as pd
import gspread
import plotly.express as px
import io

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

# Hàm xuất file Excel xịn xò
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Báo Cáo Tổng Hợp')
        # Tự động căn chỉnh độ rộng cột cho đẹp
        worksheet = writer.sheets['Báo Cáo Tổng Hợp']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 5
            worksheet.set_column(i, i, column_len)
    return output.getvalue()

# ==========================================
# 3. ĐIỀU HƯỚNG CHÍNH
# ==========================================
with st.sidebar:
    st.markdown("### 🔴 KB-LAB")
    st.caption("*Kiến tạo chuẩn mực không gian tri thức hiện đại*")
    st.markdown("---")
    menu = st.radio("MENU QUẢN LÝ", ["🏠 Tổng quan & Báo cáo", "📝 Đánh giá Hàng loạt", "👥 Quản lý Trợ giảng"])

today = datetime.date.today()
danh_sach_nhan_su, df_data = lay_danh_sach_ta(SHEET_CSV_URL)

# ------------------------------------------
# MÀN HÌNH 1: DASHBOARD CHỐT CÔNG & BÁO CÁO
# ------------------------------------------
if menu == "🏠 Tổng quan & Báo cáo":
    st.title("Bảng Điều Khiển & Xuất Báo Cáo Tháng")
    
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
            
            if not df_log_full.empty and 'Ngày' in df_log_full.columns:
                df_log_full['Ngày_DT'] = pd.to_datetime(df_log_full['Ngày'], errors='coerce')
                df_log = df_log_full[(df_log_full['Ngày_DT'].dt.month == thang_chon) & (df_log_full['Ngày_DT'].dt.year == nam_chon)]
            else:
                df_log = pd.DataFrame()

            if not df_log.empty:
                for col in ['Điểm trừ', 'Điểm cộng', 'Số ca', 'Số giờ']:
                    if col not in df_log.columns: df_log[col] = 0
                    df_log[col] = pd.to_numeric(df_log[col], errors='coerce').fillna(0)
                if 'Tên Nhân Sự' not in df_log.columns: df_log['Tên Nhân Sự'] = "Chưa cập nhật"

                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                col_kpi1.metric(f"Tổng ca làm (Tháng {thang_chon})", f"{df_log['Số ca'].sum():.1f} ca")
                col_kpi2.metric("Tổng giờ Ops", f"{df_log['Số giờ'].sum():.1f} h")
                col_kpi3.metric("Tổng Điểm Cộng", str(df_log['Điểm cộng'].sum()), "Tích cực")
                col_kpi4.metric("Tổng Điểm Trừ", str(df_log['Điểm trừ'].sum()), "Vi phạm", delta_color="inverse")
                st.markdown("---")
                
                df_ranking = df_log.groupby('Tên Nhân Sự').agg(
                    Tổng_ca=('Số ca', 'sum'), Tổng_giờ=('Số giờ', 'sum'),
                    Điểm_cộng=('Điểm cộng', 'sum'), Điểm_trừ=('Điểm trừ', 'sum')
                ).reset_index()
                df_ranking['KPI_Cuối_Tháng'] = 100 + df_ranking['Điểm_cộng'] - df_ranking['Điểm_trừ']
                df_ranking = df_ranking.sort_values(by='KPI_Cuối_Tháng', ascending=False)
                
                # Đổi tên cột cho đẹp trước khi xuất Excel
                df_export = df_ranking.rename(columns={
                    'Tổng_ca': 'Tổng Số Ca (TA)', 'Tổng_giờ': 'Tổng Số Giờ (Ops)',
                    'Điểm_cộng': 'Tổng Điểm Thưởng', 'Điểm_trừ': 'Tổng Điểm Phạt',
                    'KPI_Cuối_Tháng': 'Chỉ Số KPI (Trên 100)'
                })
                
                st.subheader("📈 Phân Tích Dữ Liệu Trực Quan")
                
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    top_5 = df_ranking.head(5).sort_values(by="KPI_Cuối_Tháng", ascending=True) 
                    fig_bar = px.bar(top_5, x="KPI_Cuối_Tháng", y="Tên Nhân Sự", orientation='h', title="Top 5 Nhân Sự Xuất Sắc Nhất", color="KPI_Cuối_Tháng", color_continuous_scale="Reds")
                    st.plotly_chart(fig_bar, use_container_width=True)
                with col_chart2:
                    df_pie = pd.DataFrame({'Phân loại': ['Điểm Thưởng', 'Điểm Phạt'], 'Điểm số': [df_log['Điểm cộng'].sum(), df_log['Điểm trừ'].sum()]})
                    fig_pie = px.pie(df_pie, names='Phân loại', values='Điểm số', hole=0.4, title="Cán cân Khen Thưởng vs Kỷ Luật", color='Phân loại', color_discrete_map={'Điểm Thưởng':'#28a745', 'Điểm Phạt':'#dc3545'})
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                st.markdown("---")
                
                col_header, col_btn = st.columns([3, 1])
                with col_header: st.subheader(f"🧮 Bảng Chốt Công & KPI (Tháng {thang_chon}/{nam_chon})")
                with col_btn:
                    # Nút xuất file Excel chuyên nghiệp
                    excel_data = to_excel(df_export)
                    st.download_button(
                        label="📥 XUẤT BÁO CÁO (EXCEL)", 
                        data=excel_data, 
                        file_name=f"Bao_Cao_Nhan_Su_Thang_{thang_chon}_{nam_chon}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )

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
            else: 
                st.info(f"Tháng {thang_chon} chưa có dữ liệu chấm công. Hãy sang mục 'Đánh giá Hàng loạt' để nhập ca làm đầu tiên!")
        except Exception as e: st.warning(f"Lỗi hệ thống: {e}")
    else: st.error("Chưa kết nối API Key.")

# ------------------------------------------
# MÀN HÌNH 2: ĐÁNH GIÁ CÔNG VIỆC HÀNG LOẠT
# ------------------------------------------
elif menu == "📝 Đánh giá Hàng loạt":
    st.title("Phân Hệ Đánh Giá & Chấm Công Hàng Loạt")
    
    col_ngay, col_trong = st.columns([1, 2])
    with col_ngay: ngay_ghi_nhan = st.date_input("🗓️ Chọn ngày ghi nhận:", today)
    doi_tuong = st.radio("Bộ phận đánh giá:", ["👥 Trợ giảng Chuyên môn (TA)", "⚙️ Trợ giảng Vận hành (Ops)"], horizontal=True)
    st.markdown("---")
    
    tab_daily, tab_deadline = st.tabs(["📅 Chấm Công & KPI Hàng Ngày", "🚩 Báo cáo Cuối Tuần / Cuối Tháng"])

    # ==========================================
    # LUỒNG 1: TRỢ GIẢNG CHUYÊN MÔN (TA)
    # ==========================================
    if doi_tuong == "👥 Trợ giảng Chuyên môn (TA)":
        with tab_daily:
            st.info("💡 **HƯỚNG DẪN:** \n1. Tích vào ô **[✅ Đi làm]**. \n2. Nhập tên lớp phụ trách (VD: M31) vào cột **[📚 Lớp dạy]**.\n3. Đánh dấu lỗi hoặc điểm cộng. Nhấp đúp vào **[🔢 Nhập Số ca]** để sửa số lượng ca nếu cần.")
            
            df_input_ta = pd.DataFrame({
                "Đi làm": [False] * len(danh_sach_nhan_su),
                "Tên Nhân Sự": danh_sach_nhan_su,
                "Lớp phụ trách": [""] * len(danh_sach_nhan_su), # Cột mới
                "Đi thay cho ai?": [""] * len(danh_sach_nhan_su),
                "Lỗi Check-in/out": [False] * len(danh_sach_nhan_su),
                "Lỗi Điểm danh": [False] * len(danh_sach_nhan_su),
                "Lỗi BTVN": [False] * len(danh_sach_nhan_su),
                "Lớp có HS nghỉ": [False] * len(danh_sach_nhan_su),
                "Ca hoàn hảo (Cộng điểm)": [False] * len(danh_sach_nhan_su),
                "Số ca": [1.0] * len(danh_sach_nhan_su)
            })

            edited_ta = st.data_editor(
                df_input_ta,
                column_config={
                    "Đi làm": st.column_config.CheckboxColumn("✅ Đi làm?", default=False),
                    "Tên Nhân Sự": st.column_config.TextColumn("👤 Họ và Tên", disabled=True), 
                    "Lớp phụ trách": st.column_config.TextColumn("📚 Lớp dạy", help="Nhập mã lớp, ví dụ: QT2N6, M31..."),
                    "Đi thay cho ai?": st.column_config.SelectboxColumn("🔄 Đi thay?", help="Bỏ trống nếu đi ca chính.", options=[""] + danh_sach_nhan_su),
                    "Lỗi Check-in/out": st.column_config.CheckboxColumn("⚠️ Lỗi Checkin (-5đ)"),
                    "Lỗi Điểm danh": st.column_config.CheckboxColumn("⚠️ Lỗi Đ.danh (-5đ)"),
                    "Lỗi BTVN": st.column_config.CheckboxColumn("⚠️ Lỗi BTVN (-5đ)"),
                    "Lớp có HS nghỉ": st.column_config.CheckboxColumn("⚠️ Có HS vắng (-2đ)"),
                    "Ca hoàn hảo (Cộng điểm)": st.column_config.CheckboxColumn("⭐ Ca Hoàn Hảo (+10đ)"),
                    "Số ca": st.column_config.NumberColumn("🔢 Số ca", min_value=0.5, step=0.5, format="%.1f")
                },
                hide_index=True, use_container_width=True
            )

            if st.button("🚀 LƯU ĐÁNH GIÁ TẤT CẢ TA"):
                danh_sach_di_lam = edited_ta[edited_ta["Đi làm"] == True]
                if danh_sach_di_lam.empty: st.warning("Vui lòng tích chọn ít nhất 1 người đi làm!")
                else:
                    rows_to_insert = []
                    for index, row in danh_sach_di_lam.iterrows():
                        diem_tru = (5 if row['Lỗi Check-in/out'] else 0) + (5 if row['Lỗi Điểm danh'] else 0) + (5 if row['Lỗi BTVN'] else 0) + (2 if row['Lớp có HS nghỉ'] else 0)
                        diem_cong = 10 if row['Ca hoàn hảo (Cộng điểm)'] else 0
                        
                        nguoi_thay_val = str(row['Đi thay cho ai?']).strip()
                        nguoi_di_thay = nguoi_thay_val if nguoi_thay_val and nguoi_thay_val != "None" else "Không"
                        lop_day = str(row['Lớp phụ trách']).strip() if row['Lớp phụ trách'] else "Chưa nhập lớp"
                        
                        # Ghi nhận dữ liệu: Có 10 cột (bao gồm cột Lớp phụ trách cuối cùng)
                        dong_moi = [str(ngay_ghi_nhan), row['Tên Nhân Sự'], "Có lỗi" if diem_tru > 0 else "Hoàn thành", nguoi_di_thay, "Ghi nhận Hàng Loạt", diem_tru, diem_cong, 0, float(row['Số ca']), lop_day]
                        rows_to_insert.append(dong_moi)

                    if gc and rows_to_insert:
                        try:
                            # Nếu sheet chưa có cột thứ 10, gspread vẫn tự động đẩy data vào cột J
                            gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_TA").append_rows(rows_to_insert)
                            st.success(f"✅ Đã lưu chấm công Hàng ngày cho {len(rows_to_insert)} TA!")
                        except Exception as e: st.error(f"Lỗi ghi dữ liệu: {e}. (Hãy chắc chắn bạn đã tạo cột 'Lớp phụ trách' ở cột thứ 10 trong Sheet Nhat_Ky_TA)")
        
        with tab_deadline:
            st.subheader("Báo cáo Tuần / Tháng (Phạt Deadline & Khen thưởng)")
            ta_dl_name = st.selectbox("Chọn nhân sự (TA):", danh_sach_nhan_su, key="ta_name_dl")
            st.markdown("**1. Vi phạm Báo cáo / Họp hành (Tính điểm trừ):**")
            vang_hop = st.number_input("Số buổi vắng họp giao ban tuần (-5đ/buổi):", min_value=0, max_value=4, value=0)
            tre_bc_lop = st.number_input("Trễ Báo cáo lớp - Hạn mùng 1 (-10đ/ngày):", min_value=0, max_value=30, value=0)
            tre_bg = st.number_input("Trễ Báo giảng - Hạn từ 1 đến 5 (-5đ/ngày):", min_value=0, max_value=30, value=0)
            tre_luong = st.number_input("Trễ Bảng lương - Hạn mùng 5 (-10đ/ngày):", min_value=0, max_value=30, value=0)
            st.markdown("**2. Khen thưởng Đặc biệt (Tính điểm cộng):**")
            thuong_feedback = st.checkbox("⭐ Phản hồi tốt từ phụ huynh/học sinh (+5đ)")
            thuong_diemcao = st.checkbox("⭐ Học sinh thi đạt điểm cao vượt kỳ vọng (+10đ)")

            if st.button("💾 LƯU BÁO CÁO TUẦN/THÁNG"):
                diem_phat_dl = (vang_hop * 5) + (tre_bc_lop * 10) + (tre_bg * 5) + (tre_luong * 10)
                diem_cong_thang = (5 if thuong_feedback else 0) + (10 if thuong_diemcao else 0)
                ghi_chu = []
                if vang_hop > 0: ghi_chu.append(f"Vắng họp: {vang_hop}b")
                if tre_bc_lop > 0: ghi_chu.append(f"Trễ BCL: {tre_bc_lop}d")
                if tre_bg > 0: ghi_chu.append(f"Trễ BG: {tre_bg}d")
                if tre_luong > 0: ghi_chu.append(f"Trễ Lương: {tre_luong}d")
                
                if diem_phat_dl > 0 or diem_cong_thang > 0:
                    if gc:
                        # Đẩy 10 cột để khớp với sheet TA hiện tại (Cột 10 để trống)
                        gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_TA").append_row([str(ngay_ghi_nhan), ta_dl_name, "Tổng kết", "Không", " | ".join(ghi_chu) if ghi_chu else "Thưởng tháng", diem_phat_dl, diem_cong_thang, 0, 0, ""])
                        st.toast(f"Đã lưu Báo cáo Phạt/Thưởng cho {ta_dl_name}!", icon="🌟")
                else: st.info("Không có chỉ số nào để lưu.")

    # ==========================================
    # LUỒNG 2: TRỢ GIẢNG VẬN HÀNH (OPS)
    # ==========================================
    else:
        try: danh_sach_ops = df_data[(df_data['Vai trò'].str.contains("Vận hành|Quản lý", na=False, case=False)) & (df_data['Họ và tên'].isin(danh_sach_nhan_su))]['Họ và tên'].tolist()
        except: danh_sach_ops = danh_sach_nhan_su
        if not danh_sach_ops: danh_sach_ops = danh_sach_nhan_su
            
        with tab_daily:
            st.info("💡 **TỰ ĐỘNG TÍNH GIỜ:** Tích chọn người đi làm. Điền Giờ Check-in & Check-out, hệ thống sẽ tự động trừ và quy đổi ra Số Giờ làm cho Kế toán.")
            
            default_in = datetime.time(17, 30)
            default_out = datetime.time(21, 30)
            
            df_input_ops = pd.DataFrame({
                "Đi làm": [False] * len(danh_sach_ops),
                "Tên Nhân Sự": danh_sach_ops,
                "Check-in": [default_in] * len(danh_sach_ops),
                "Check-out": [default_out] * len(danh_sach_ops),
                "Đi muộn (-5đ)": [False] * len(danh_sach_ops),
                "Lỗi Cơ sở VC (-2đ)": [False] * len(danh_sach_ops),
                "Lỗi Sĩ số (-5đ)": [False] * len(danh_sach_ops),
                "Lỗi Phàn nàn (-15đ)": [False] * len(danh_sach_ops),
                "Thưởng (+5đ)": [False] * len(danh_sach_ops)
            })

            edited_ops = st.data_editor(
                df_input_ops,
                column_config={
                    "Đi làm": st.column_config.CheckboxColumn("✅ Đi làm?", default=False),
                    "Tên Nhân Sự": st.column_config.TextColumn("👤 Họ và Tên", disabled=True),
                    "Check-in": st.column_config.TimeColumn("⏰ Giờ IN", format="HH:mm"),
                    "Check-out": st.column_config.TimeColumn("⏰ Giờ OUT", format="HH:mm"),
                    "Đi muộn (-5đ)": st.column_config.CheckboxColumn("⚠️ Đi muộn"),
                    "Lỗi Cơ sở VC (-2đ)": st.column_config.CheckboxColumn("⚠️ Lỗi CSVC"),
                    "Lỗi Sĩ số (-5đ)": st.column_config.CheckboxColumn("⚠️ Lỗi Sĩ số"),
                    "Lỗi Phàn nàn (-15đ)": st.column_config.CheckboxColumn("⚠️ Phàn nàn"),
                    "Thưởng (+5đ)": st.column_config.CheckboxColumn("⭐ Xử lý sự cố")
                },
                hide_index=True, use_container_width=True
            )

            if st.button("🚀 LƯU ĐÁNH GIÁ TẤT CẢ OPS"):
                danh_sach_ops_lam = edited_ops[edited_ops["Đi làm"] == True]
                if danh_sach_ops_lam.empty: st.warning("Vui lòng tích chọn ít nhất 1 Ops đi làm!")
                else:
                    rows_ops_insert = []
                    log_gio_lam = []
                    
                    for index, row in danh_sach_ops_lam.iterrows():
                        in_t = row['Check-in']
                        out_t = row['Check-out']
                        
                        dt_in = datetime.datetime.combine(today, in_t)
                        dt_out = datetime.datetime.combine(today, out_t)
                        if dt_out < dt_in: dt_out += datetime.timedelta(days=1)
                            
                        so_gio_thuc_te = round((dt_out - dt_in).total_seconds() / 3600.0, 2)
                        
                        diem_tru_ops = (5 if row['Đi muộn (-5đ)'] else 0) + (2 if row['Lỗi Cơ sở VC (-2đ)'] else 0) + (5 if row['Lỗi Sĩ số (-5đ)'] else 0) + (15 if row['Lỗi Phàn nàn (-15đ)'] else 0)
                        diem_cong_ops = 5 if row['Thưởng (+5đ)'] else 0
                        dong_ops_moi = [str(ngay_ghi_nhan), row['Tên Nhân Sự'], "Có lỗi" if diem_tru_ops > 0 else "Hoàn thành", "Ops", "Ghi nhận Hàng loạt", diem_tru_ops, diem_cong_ops, 0, so_gio_thuc_te]
                        
                        rows_ops_insert.append(dong_ops_moi)
                        log_gio_lam.append(f"{row['Tên Nhân Sự']}: {so_gio_thuc_te}h")

                    if gc and rows_ops_insert:
                        try:
                            gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_Ops").append_rows(rows_ops_insert)
                            st.success(f"✅ Đã lưu {len(rows_ops_insert)} nhân sự Ops. Chi tiết tính giờ: {', '.join(log_gio_lam)}")
                        except Exception as e: st.error(f"Lỗi ghi dữ liệu: {e}")
                    
        with tab_deadline:
            st.subheader("Cập nhật KPI Cuối tháng (Cá nhân)")
            ops_dl_name = st.selectbox("Chọn nhân sự (Ops):", danh_sach_ops, key="ops_name_dl")
            tre_luong_ops = st.number_input("Trễ Chốt lương Ops (Hạn mùng 5) [-10đ/ngày]:", min_value=0, max_value=30, value=0)
            
            if st.button("💾 Lưu Phạt Deadline Ops"):
                diem_phat_ops = tre_luong_ops * 10
                if diem_phat_ops > 0:
                    if gc:
                        gc.open_by_url(SHEET_MASTER_URL).worksheet("Nhat_Ky_Ops").append_row([str(ngay_ghi_nhan), ops_dl_name, "Tổng kết", "Ops", f"Trễ Lương: {tre_luong_ops}d", diem_phat_ops, 0, 0, 0])
                        st.toast(f"Đã trừ {diem_phat_ops} điểm deadline của {ops_dl_name}!", icon="🚨")
                else: st.info("Không có chỉ số nào để lưu.")

# ------------------------------------------
# MÀN HÌNH 3: QUẢN LÝ NHÂN SỰ
# ------------------------------------------
elif menu == "👥 Quản lý Trợ giảng":
    st.title("Hồ Sơ & Danh Bạ Nhân Sự")
    if df_data is not None:
        try: st.dataframe(df_data[['Họ và tên', 'Số điện thoại', 'Email', 'Vai trò', 'Trạng Thái']], use_container_width=True, hide_index=True)
        except: st.dataframe(df_data)
