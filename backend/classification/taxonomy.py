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
    # Devanagari (Hindi) trigger words for the same scam patterns, so rule-based
    # matching and indicator extraction also work on हिन्दी messages.
    keywords_hi: list[str] = field(default_factory=list)
    description: str = ""


def _combined_keywords(defn: ScamDefinition) -> list[str]:
    """All trigger words for a definition (English + Devanagari Hindi)."""
    return [*defn.keywords, *defn.keywords_hi]


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
        keywords_hi=[
            "कलेक्ट अनुरोध", "भुगतान अनुरोध", "क्यूआर कोड", "स्कैन करें",
            "भुगतान स्वीकार", "लंबित कलेक्ट", "यूपीआई पिन", "पिन दर्ज",
            "कलेक्ट रिक्वेस्ट", "भुगतान प्राप्त करने के लिए",
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
        keywords_hi=[
            "केवाईसी अपडेट", "केवाईसी सत्यापित", "केवाईसी समाप्त",
            "खाता ब्लॉक", "खाता निलंबित", "पुनः सत्यापित", "लिंक",
            "पोर्टल", "यहां क्लिक करें", "तुरंत अपडेट करें", "सत्यापित करें",
            "समाप्त हो", "निलंबित कर दिया", "रीवेरिफाई", "री-वेरिफाई",
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
        keywords_hi=[
            "बैंक अधिकारी", "आरबीआई अधिकारी", "कानूनी कार्रवाई", "पुलिस",
            "सीबीआई", "गिरफ्तारी वारंट", "वीडियो कॉल पर", "बैंक से बोल रहा",
            "धोखाधड़ी रोकथाम विभाग", "अरेस्ट वारंट", "कस्टम विभाग",
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
        keywords_hi=[
            "ओटीपी", "वन-टाइम पासवर्ड", "ओटीपी बताएं", "कोड बताएं",
            "सत्यापन कोड", "अंकों कोड", "कोड साझा करें", "कोड सत्यापित",
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
        keywords_hi=[
            "रिफंड", "कैशबैक", "वापसी", "धन वापस", "लंबित रिफंड",
            "रिफंड विफल", "रिफंड प्रक्रिया", "रिफंड शुरू",
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
        keywords_hi=[
            "सिम अपग्रेड", "सिम ब्लॉक", "नंबर पोर्ट", "नई सिम",
            "सिम कार्ड", "सिम बंद", "नंबर बंद", "पोर्ट करने के लिए",
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
        keywords_hi=[
            "निवेश", "गारंटीड रिटर्न", "पैसा दोगुना", "क्रिप्टो", "बिटकॉइन",
            "शेयर बाजार", "मुनाफा", "जोखिम मुक्त", "टेलीग्राम ग्रुप",
            "ट्रेडिंग ऐप", "वर्चुअल ट्रेडिंग", "स्टॉक निवेश",
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
        keywords_hi=[
            "लॉटरी", "इनाम", "विजेता", "बधाई", "लकी ड्रॉ",
            "जीते हैं", "पुरस्कार", "गिफ्ट कार्ड", "अमेज़न उपहार",
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
        keywords_hi=[
            "घर बैठे", "पार्ट टाइम जॉब", "रोज कमाई", "दैनिक कमाई",
            "ऑनलाइन जॉब", "टाइपिंग जॉब", "डेटा एंट्री", "रजिस्ट्रेशन फीस",
            "अग्रिम भुगतान", "कमाएं", "अभी जुड़ें",
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
        keywords_hi=[
            "इंस्टेंट लोन", "प्री-अप्रूव्ड लोन", "लोन मंजूर",
            "प्रोसेसिंग फीस", "लोन ऐप", "कम ब्याज लोन",
            "लोन शुल्क", "लोन स्वीकृत", "ऋण स्वीकृत",
        ],
        description="Fraudulent loan apps or offers with hidden charges.",
    ),
    ScamDefinition(
        category="benign",
        label="Legitimate / Normal Message",
        risk_level="safe",
        keywords=[
            "debited", "credited", "available balance", "statement",
            "order delivered", "swiggy", "zomato", "irctc", "meeting",
            "delivered", "balance is rs", "paid to",
        ],
        keywords_hi=[
            "डेबिट हो", "क्रेडिट हो", "उपलब्ध शेष", "शेष राशि",
            "ऑर्डर डिलीवर", "सफलतापूर्वक", "भुगतान प्राप्त", "रसीद",
        ],
        description="Authentic transactional, personal, or non-fraudulent messages.",
    ),
]

# Lookup maps
CATEGORY_TO_DEF: dict[str, ScamDefinition] = {s.category: s for s in SCAM_TAXONOMY}
ALL_CATEGORIES: list[str] = [s.category for s in SCAM_TAXONOMY] + ["unknown"]
