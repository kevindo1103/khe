/**
 * Shared enum → Vietnamese label maps.
 * Mirrored from backend enums exactly to prevent drift.
 * Source: backend/modules/extraction/schemas.py
 */

// Legacy doc_type field (DocumentListItem.doc_type) — snake_case NEVER rendered (G8)
export const DOC_TYPE_LABELS: Record<string, string> = {
  hd_nha_cung_cap:       'Nhà cung cấp',
  hd_thue_mat_bang:      'Thuê mặt bằng',
  hd_lao_dong:           'Lao động',
  hd_dan_su:             'Dân sự',
  hd_bat_dong_san:       'Bất động sản',
  hd_van_tai_logistics:  'Vận tải & Logistics',
  hd_xay_dung:           'Xây dựng',
  hd_cong_nghe_ip:       'Công nghệ & IP',
  hd_tai_chinh:          'Tài chính',
  hd_hanh_chinh:         'Hành chính',
};

// DEC-029 doc_type_group — 10 groups + "other" fallback
export const DOC_TYPE_GROUP_LABELS: Record<string, string> = {
  dan_su: 'Dân sự',
  thuong_mai: 'Thương mại',
  lao_dong: 'Lao động',
  bat_dong_san: 'Bất động sản',
  van_tai_logistics: 'Vận tải & Logistics',
  xay_dung: 'Xây dựng',
  cong_nghe_ip: 'Công nghệ & IP',
  tai_chinh: 'Tài chính',
  bao_dam: 'Bảo đảm',
  hanh_chinh: 'Hành chính',
  other: 'Khác',
};

// obligation_type — from ObligationScheduleItem schema
export const OBLIGATION_TYPE_LABELS: Record<string, string> = {
  payment: 'Thanh toán',
  delivery: 'Giao hàng',
  handover: 'Bàn giao',
  expiration: 'Hết hạn',
  renewal: 'Gia hạn',
  review: 'Rà soát',
  warranty: 'Bảo hành',
  other: 'Khác',
};

// direction — DEC-030
export const DIRECTION_LABELS: Record<string, string> = {
  'nghĩa_vụ': 'Nghĩa vụ',
  'quyền_lợi': 'Quyền lợi',
};

// CANONICAL_FIELDS — 12 universal fields (backend/modules/extraction/schemas.py)
export const CANONICAL_FIELDS: readonly string[] = [
  'doi_tac',
  'ngay_hieu_luc',
  'ngay_het_han',
  'gia_tri_hd',
  'thoi_han_hd',
  'dieu_khoan_gia_han',
  'dieu_khoan_thanh_toan',
  'doc_type_group',
  'ngay_ky',
  'tien_dat_coc',
  'thoi_han_bao_hanh',
  'thoi_han_thong_bao',
] as const;

// Field name → VN label for display
export const FIELD_LABELS: Record<string, string> = {
  doi_tac: 'Đối tác',
  ngay_hieu_luc: 'Ngày hiệu lực',
  ngay_het_han: 'Ngày hết hạn',
  gia_tri_hd: 'Giá trị HĐ',
  thoi_han_hd: 'Thời hạn HĐ',
  dieu_khoan_gia_han: 'Điều khoản gia hạn',
  dieu_khoan_thanh_toan: 'Điều khoản thanh toán',
  doc_type_group: 'Nhóm tài liệu',
  ngay_ky: 'Ngày ký',
  tien_dat_coc: 'Tiền đặt cọc',
  thoi_han_bao_hanh: 'Thời hạn bảo hành',
  thoi_han_thong_bao: 'Thời hạn báo trước',
};

export const labelFor = (map: Record<string, string>, key: string): string =>
  map[key] ?? key;
