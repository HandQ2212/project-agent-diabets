"""Multi-Agent contracts and agent implementations for Duong An."""
import re
from typing import TypedDict, Literal, Optional
from pydantic import BaseModel, Field

# Agent state schema for LangGraph
class CoordinatorState(TypedDict, total=False):
    question: str
    safety_passed: bool
    safety_category: Optional[str]
    safety_response: Optional[str]
    sources: list[dict]
    answer: str
    trace: list[str]

# Safety categories
RuleCategory = Literal['SAFE', 'EMERGENCY', 'MEDICATION_DOSAGE', 'PII_SENSITIVE', 'PROMPT_INJECTION']

class RuleEvaluation(BaseModel):
    passed: bool
    category: RuleCategory
    response: Optional[str] = None
    reason: str

class RuleAgent:
    """Agent responsible for safety, emergency detection, medication deflection, and privacy."""
    
    # Emergency patterns (acute complications, severe hypoglycemia, ketoacidosis, coma)
    EMERGENCY_PATTERNS = [
        r'\bhôn\s*mê\b',
        r'\bbất\s*tỉnh\b',
        r'\bngất\s*xỉu\b',
        r'\bmất\s*tri\s*giác\b',
        r'\bco\s*giật\b',
        r'\bkhó\s*thở\s*(dữ\s*dội|nặng)?\b',
        r'\bthở\s*kussmaul\b',
        r'\bhơi\s*thở\s*mùi\s*(táo|axeton|acetone)\b',
        r'\bnôn\s*(mửa|ói)?\s*liên\s*tục\b',
        r'\bvã\s*mồ\s*hôi\s*lạnh\s*(run\s*rẩy)?\s*dữ\s*dội\b',
        r'\b(toan\s*ceton|cetoacidosis|ketoacidosis|dka|hhs)\b',
        r'\bđường\s*huyết\s*(tụt|giảm)\s*(quá\s*thấp|<|dưới)\s*(2|3)\b',
        r'\bđau\s*thắt\s*ngực\s*dữ\s*dội\b'
    ]
    
    # Medication and dosage patterns
    MEDICATION_PATTERNS = [
        r'\b(liều|uống\s*mấy\s*viên|tiêm\s*bao\s*nhiêu|đơn\s*vị)\s*(insulin|thuốc|metformin)?\b',
        r'\b(tăng\s*liều|giảm\s*liều|chỉnh\s*liều|đổi\s*liều)\b',
        r'\b(kê\s*đơn|kê\s*thuốc|bốc\s*thuốc|chỉ\s*định\s*thuốc)\b',
        r'\b(tự\s*ý\s*)?(bỏ\s*thuốc|ngừng\s*thuốc|ngưng\s*thuốc|thôi\s*uống)\b',
        r'\b(uống|dùng)\s*thuốc\s*gì\s*để\s*(hạ|khỏi|chữa)\b',
        r'\bnovorapid|lantus|diamicron|glucophage|januvia\b'
    ]
    
    # PII patterns (Citizen ID 9 or 12 digits, VN Phone numbers)
    PII_PHONE_PATTERN = r'(\+84|0)(3[2-9]|5[6|8|9]|7[0|6-9]|8[1-9]|9[0-9])[0-9]{7}\b'
    PII_CCCD_PATTERN = r'\b(cccd|cmnd|số\s*thẻ|bảo\s*hiểm|bhyt)?\s*[:\s]?\s*([0-9]{9}|[0-9]{12})\b'
    PII_NAME_RECORD_PATTERN = r'\b(bệnh\s*nhân|hồ\s*sơ\s*bệnh\s*án|mã\s*bệnh\s*án)\s*[:\s]\s*[\w\s]+\b'
    
    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r'ignore\s*(all\s*)?previous\s*instructions',
        r'quên\s*(hết\s*)?(các\s*)?hướng\s*dẫn\s*trước',
        r'bỏ\s*qua\s*(mọi\s*)?(quy\s*tắc|chỉ\s*dẫn|nguyên\s*tắc)',
        r'(bây\s*giờ\s*)?bạn\s*là\s*bác\s*sĩ',
        r'act\s*as\s*(a\s*)?(doctor|medical\s*expert)',
        r'jailbreak',
        r'system\s*prompt',
        r'override\s*(safety)?',
        r'giả\s*lập\s*bác\s*sĩ\s*kê\s*đơn'
    ]

    @classmethod
    def evaluate(cls, text: str) -> RuleEvaluation:
        norm = text.lower().strip()
        
        # 1. Prompt Injection check
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, norm):
                return RuleEvaluation(
                    passed=False,
                    category='PROMPT_INJECTION',
                    reason='Phát hiện dấu hiệu tấn công ghi đè chỉ dẫn hệ thống (Prompt Injection).',
                    response=(
                        "YÊU CẦU BỊ TỪ CHỐI: Phát hiện nội dung bất thường nhằm can thiệp vào chỉ dẫn an toàn "
                        "của hệ thống. Vui lòng chỉ đặt các câu hỏi học thuật về bệnh đái tháo đường."
                    )
                )

        # 2. Emergency check
        for pattern in cls.EMERGENCY_PATTERNS:
            if re.search(pattern, norm):
                return RuleEvaluation(
                    passed=False,
                    category='EMERGENCY',
                    reason='Phát hiện tình huống cấp cứu y tế nguy hiểm đến tính mạng.',
                    response=(
                        "🚨 CẢNH BÁO KHẨN CẤP: Dấu hiệu bạn mô tả có thể là tình trạng cấp cứu y tế nghiêm trọng "
                        "(như hạ đường huyết nặng, hôn mê tăng áp lực thẩm thấu hoặc nhiễm toan ceton). "
                        "HÃY GỌI NGAY CẤP CỨU 115 HOẶC ĐƯA NGƯỜI BỆNH ĐẾN KHOA CẤP CỨU CỦA BỆNH VIỆN GẦN NHẤT NGAY LẬP TỨC! "
                        "Tuyệt đối không tự điều trị hoặc cố cho ăn uống khi người bệnh lơ mơ, mất tri giác."
                    )
                )

        # 3. Medication & Dosage check
        for pattern in cls.MEDICATION_PATTERNS:
            if re.search(pattern, norm):
                return RuleEvaluation(
                    passed=False,
                    category='MEDICATION_DOSAGE',
                    reason='Yêu cầu kê đơn, chỉ định hoặc điều chỉnh liều lượng thuốc điều trị.',
                    response=(
                        "⚠️ CẢNH BÁO AN TOÀN ĐIỀU TRỊ: Đường An là nền tảng học thuật hỗ trợ tìm hiểu kiến thức, "
                        "hoàn toàn không thể và không có chức năng khám chữa bệnh, kê đơn thuốc hoặc điều chỉnh liều dùng insulin/thuốc uống. "
                        "Mọi thay đổi liên quan đến thuốc bắt buộc phải có chỉ định trực tiếp từ bác sĩ chuyên khoa phụ trách điều trị của bạn."
                    )
                )

        # 4. Sensitive PII check
        if re.search(cls.PII_PHONE_PATTERN, norm) or re.search(cls.PII_CCCD_PATTERN, norm) or re.search(cls.PII_NAME_RECORD_PATTERN, norm):
            return RuleEvaluation(
                passed=False,
                category='PII_SENSITIVE',
                reason='Phát hiện thông tin định danh cá nhân hoặc hồ sơ bệnh án (PII).',
                response=(
                    "🔒 BẢO VỆ DỮ LIỆU CÁ NHÂN: Để đảm bảo quyền riêng tư và tuân thủ nguyên tắc y tế, "
                    "hệ thống không lưu trữ hay xử lý thông tin nhận dạng cá nhân (họ tên bệnh nhân, số CCCD/CMND, "
                    "số điện thoại, mã hồ sơ bệnh án). Vui lòng gửi lại câu hỏi tổng quát không chứa thông tin riêng tư."
                )
            )

        return RuleEvaluation(passed=True, category='SAFE', reason='Đạt yêu cầu an toàn.')
