"""Tests for modules.extraction.scan_detect — garbled Vietnamese detection (#420)."""

from modules.extraction.scan_detect import is_garbled_vietnamese


_CLEAN_VN = (
    "CÔNG TY CỔ PHẦN TRẦN THÁI CAM RANH THỎA THUẬN KÝ QUỸ "
    "Số LIA02 TTKQ Ngày 20 tháng 03 năm 2018 Trong Thỏa thuận này "
    "các cụm từ dưới đây được hiểu như sau Bên A là Chủ đầu tư "
    "công ty cổ phần Trần Thái Cam Ranh địa chỉ số 12 đường Nguyễn Trãi "
    "phường Cam Phú thành phố Cam Ranh tỉnh Khánh Hòa"
)

_GARBLED_VN = (
    "CaNG TY c6 PHAN TRAN THAI CAM RANH THOA THUAN KY QUY "
    "So LIAO2 02 TTKQ Ngay 20 thang 03 nam 2018 Trang Thea thuan nay "
    "cac cum tir duoi day duoc hieu nhir sau Ben A la Chu dau tu "
    "cong ty co phan Tran Thai Cam Ranh dia chi so 12 duong Nguyen Trai "
    "phuong Cam Phu thanh pho Cam Ranh tinh Khanh Hoa"
)


def test_clean_vietnamese_not_garbled():
    assert is_garbled_vietnamese(_CLEAN_VN) is False


def test_garbled_vietnamese_detected():
    assert is_garbled_vietnamese(_GARBLED_VN) is True


def test_short_text_returns_false():
    """Text with < 100 alpha chars is too short to measure reliably."""
    assert is_garbled_vietnamese("Thea thuan nay") is False


def test_english_text_detected_as_garbled():
    """English text has 0% VN diacriticals — expected behavior for VN-only platform."""
    english = (
        "This agreement is entered into between Party A and Party B "
        "for the purpose of establishing the terms and conditions of "
        "the deposit arrangement dated March twentieth two thousand eighteen"
    )
    assert is_garbled_vietnamese(english) is True


def test_empty_string_returns_false():
    assert is_garbled_vietnamese("") is False
