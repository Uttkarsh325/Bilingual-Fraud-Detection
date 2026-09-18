"""
Scam taxonomy — category definitions, keyword indicators, and risk mappings.
Used by both the rule-based classifier and the ML classifier as ground truth.
"""
from dataclasses import dataclass, field


@dataclass
class ScamDefinition:
    category: str
    label: str
    risk_level: str                    # high | medium | low
    keywords: list[str] = field(default_factory=list)
    description: str = ""


SCAM_TAXONOMY: list[ScamDefinition] = [
    ScamDefinition(
        category="upi_collect_scam",
        label="UPI Collect Scam",
        risk_level="high",
        keywords=[
            "collect request", "pay request", "upi request", "qr code",
            "scan qr", "approve payment", "pending collect", "upi collect",
            "bhim", "gpay collect", "phonepay collect",
        ],
        description="Fraudulent UPI collect/payment requests or QR codes.",
    ),
    ScamDefinition(
        category="phishing_link",
        label="Phishing Link",
        risk_level="high",
        keywords=[
            "click here", "verify kyc", "update kyc", "kyc expired",
            "account blocked", "re-verify", "link", "http", "bit.ly",
            "tinyurl", "reward link", "claim prize", "cashback link",
        ],
        description="Malicious links masquerading as bank/UPI/govt portals.",
    ),
    ScamDefinition(
        category="voice_phishing",
        label="Voice Phishing (Vishing)",
        risk_level="high",
        keywords=[
            "bank officer", "rbi officer", "trai", "disconnect number",
            "legal action", "police", "cbi", "arrest warrant",
            "calling from bank", "customer care", "verify your account",
        ],
        description="Phone calls impersonating bank/RBI/government officials.",
    ),
    ScamDefinition(
        category="otp_scam",
        label="OTP Fraud",
        risk_level="high",
        keywords=[
            "otp", "one time password", "share otp", "tell otp",
            "enter otp", "verification code", "sms code",
        ],
        description="Social engineering to extract OTP from the victim.",
    ),
    ScamDefinition(
        category="fake_refund",
        label="Fake Refund Scam",
        risk_level="high",
        keywords=[
            "refund", "cashback", "money back", "pending refund",
            "process refund", "refund failed", "refund initiated",
        ],
        description="Fake refund offers used to steal account credentials.",
    ),
    ScamDefinition(
        category="sim_swap",
        label="SIM Swap Fraud",
        risk_level="high",
        keywords=[
            "sim swap", "sim upgrade", "port number", "sim blocked",
            "new sim", "mnp", "mobile number portability",
        ],
        description="SIM card duplication to take over mobile banking.",
    ),
    ScamDefinition(
        category="investment_scam",
        label="Investment / Crypto Scam",
        risk_level="high",
        keywords=[
            "invest", "guaranteed return", "double money", "crypto",
            "bitcoin", "trading app", "high return", "risk free",
            "join our group", "telegram trading", "forex",
        ],
        description="Fraudulent investment schemes promising unrealistic returns.",
    ),
    ScamDefinition(
        category="lottery_prize",
        label="Lottery / Prize Fraud",
        risk_level="medium",
        keywords=[
            "lottery", "prize", "winner", "congratulations", "lucky draw",
            "won", "reward", "gift card", "amazon gift", "iphone won",
        ],
        description="Fake lottery/prize notifications to steal money or data.",
    ),
    ScamDefinition(
        category="job_offer_scam",
        label="Fake Job Offer",
        risk_level="medium",
        keywords=[
            "work from home", "part time job", "earn per day",
            "daily earning", "online job", "typing job", "data entry",
            "join now", "registration fee", "advance payment",
        ],
        description="Fake job offers requiring upfront payment.",
    ),
    ScamDefinition(
        category="loan_scam",
        label="Fake Loan Scam",
        risk_level="medium",
        keywords=[
            "instant loan", "pre-approved loan", "loan approved",
            "processing fee", "loan app", "low interest loan",
            "no documents", "same day loan",
        ],
        description="Fraudulent loan apps or offers with hidden charges.",
    ),
]

# Lookup maps
CATEGORY_TO_DEF: dict[str, ScamDefinition] = {s.category: s for s in SCAM_TAXONOMY}
ALL_CATEGORIES: list[str] = [s.category for s in SCAM_TAXONOMY] + ["unknown"]
