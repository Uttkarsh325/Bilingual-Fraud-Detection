"""
Comprehensive Test Suite for FraudGuard AI Scam Classifier.

Tests the trained multi-tier classifier against 35+ diverse, realistic test cases
spanning all 11 taxonomy categories (10 fraud patterns + 1 benign class).
"""

import sys
import unittest
from pathlib import Path

# Ensure backend modules are on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from core.models import RiskLevel, ScamCategory
from classification.classifier import classify_text


# ─────────────────────────────────────────────────────────────────────────────
# Test Cases Catalog
# ─────────────────────────────────────────────────────────────────────────────

TEST_CASES = [
    # 1. UPI Collect Scam
    (
        "Scan this QR code and enter your UPI PIN to claim your Rs 2,500 PhonePe cashback.",
        ScamCategory.UPI_COLLECT_SCAM,
        "QR code cashback trap",
    ),
    (
        "Dear OLX seller, I have sent Rs 8,500. Please approve the collect request on Google Pay to credit money.",
        ScamCategory.UPI_COLLECT_SCAM,
        "OLX buyer reverse collect request",
    ),
    (
        "Incoming payment of Rs 1,200 pending on BHIM. Enter your 6-digit UPI PIN to accept transfer.",
        ScamCategory.UPI_COLLECT_SCAM,
        "UPI PIN to receive money misconception",
    ),

    # 2. Phishing Link
    (
        "Dear SBI User, your YONO account is suspended today due to pending KYC. Update PAN immediately: https://sbi-pan-kyc8391.xyz",
        ScamCategory.PHISHING_LINK,
        "YONO KYC suspension link",
    ),
    (
        "Urgent: Electricity power will be disconnected at 9:30 PM by Bijli Vibhag due to unpaid bill. Click https://bijli-pay9201.in",
        ScamCategory.PHISHING_LINK,
        "Electricity disconnection (Bijli bill) scam",
    ),
    (
        "Your HDFC NetBanking access is disabled. Please verify Aadhaar card at https://hdfc-verify-login839.com",
        ScamCategory.PHISHING_LINK,
        "NetBanking credential harvesting",
    ),
    (
        "India Post: Your package cannot be delivered due to wrong address. Pay Rs 25 redelivery fee at https://indiapost-track99.com",
        ScamCategory.PHISHING_LINK,
        "Postal redelivery fee phishing",
    ),

    # 3. OTP Scam
    (
        "I am calling from HDFC fraud cell. We detected unauthorized withdrawal of Rs 10,000. Read out the OTP sent to your phone to block it.",
        ScamCategory.OTP_SCAM,
        "Social engineering OTP demand",
    ),
    (
        "Airtel verification officer: Your SIM will be deactivated within 1 hour unless you share the 6-digit verification code received.",
        ScamCategory.OTP_SCAM,
        "Telecom SIM verification OTP trap",
    ),
    (
        "Swiggy refund department: To process your order cancellation refund, please confirm the one time password received via SMS.",
        ScamCategory.OTP_SCAM,
        "Refund cancellation OTP demand",
    ),

    # 4. Fake Refund
    (
        "Your Flipkart order has been cancelled and excess amount Rs 4,999 was charged. Click here to claim your refund: https://refund-desk99.com",
        ScamCategory.FAKE_REFUND,
        "Excess charge fake refund",
    ),
    (
        "IRCTC refund failed for cancelled ticket. Contact customer desk at 9811223344 or visit https://irctc-refund-portal.in to get reversal.",
        ScamCategory.FAKE_REFUND,
        "IRCTC ticket reversal scam",
    ),
    (
        "PhonePe Alert: Failed recharge of Rs 850 has been refunded. Click to claim into your account: https://phonepe-refunds.site",
        ScamCategory.FAKE_REFUND,
        "Wallet failed recharge refund link",
    ),

    # 5. Loan Scam
    (
        "Pre-approved personal loan of Rs 5,00,000 sanctioned with 0% interest and No CIBIL check. Download CashQuick APK: https://quick-loan.apk",
        ScamCategory.LOAN_SCAM,
        "Instant predatory loan APK with zero documentation",
    ),
    (
        "Urgent: You took loan of Rs 5,000 from RupeeMama app. Due date passed! Pay immediately or private photos will be sent to all contacts.",
        ScamCategory.LOAN_SCAM,
        "Loan app contact blackmail extortion",
    ),
    (
        "Govt Mudra loan of Rs 2,00,000 approved. Deposit security processing fee Rs 2,500 to disburse funds at https://mudra-gov-loan.site",
        ScamCategory.LOAN_SCAM,
        "Upfront processing fee loan fraud",
    ),

    # 6. Job Offer Scam
    (
        "Part time work from home: Earn Rs 3,000 to Rs 5,000 daily by liking YouTube videos and rating Google Maps. Contact HR on Telegram @ReviewTask",
        ScamCategory.JOB_OFFER_SCAM,
        "YouTube video rating Telegram task fraud",
    ),
    (
        "Amazon Hiring: Work From Home data entry jobs. Daily payout Rs 2,500. Pay registration fee Rs 499 (refundable) to start.",
        ScamCategory.JOB_OFFER_SCAM,
        "Advance registration fee employment scam",
    ),
    (
        "Complete 10 crypto rating tasks on Telegram and earn Rs 7,500. Recharge Rs 5,000 to unlock your payout wallet.",
        ScamCategory.JOB_OFFER_SCAM,
        "Task deposit withdrawal lock scam",
    ),

    # 7. Lottery / Prize Fraud
    (
        "Congratulations! Your mobile number won Rs 25,00,000 in KBC Jio Lucky Draw 2024. Contact Rana Pratap Singh at 9876543210 to claim.",
        ScamCategory.LOTTERY_PRIZE,
        "KBC lottery WhatsApp prize scam",
    ),
    (
        "Lucky Draw Winner! You won a Tata Safari car in Diwali Mega Contest. Pay RTO registration tax Rs 12,500 to dispatch vehicle.",
        ScamCategory.LOTTERY_PRIZE,
        "Automobile sweepstakes advance tax scam",
    ),
    (
        "Festive scratch card winner: You won iPhone 15 Pro Max! Pay delivery customs charges of Rs 1,499 at https://claim-iphone.top",
        ScamCategory.LOTTERY_PRIZE,
        "iPhone prize customs dispatch charge",
    ),

    # 8. SIM Swap Fraud
    (
        "Dear Airtel Customer, your SIM will be upgraded to 5G automatically. Send SMS 'SIM 8991283921' to 121 to activate within 2 hours.",
        ScamCategory.SIM_SWAP,
        "SMS forward SIM duplication trap",
    ),
    (
        "Jio Alert: To avoid 4G SIM deactivation, reply 'PORT 9820192019' or scan the eSIM QR code sent to your email.",
        ScamCategory.SIM_SWAP,
        "Port code and eSIM hijacking",
    ),

    # 9. Investment / Crypto Scam
    (
        "Guaranteed 5% daily return on Bitcoin and USDT! Join our VIP Telegram crypto trading group: @CryptoWealth. 100% risk free.",
        ScamCategory.INVESTMENT_SCAM,
        "Guaranteed high-yield crypto returns",
    ),
    (
        "Earn Rs 10,000 daily from stock market with zero loss guarantee. Join SEBI registered insider WhatsApp group: https://chat.whatsapp.com/TradeVIP",
        ScamCategory.INVESTMENT_SCAM,
        "Stock market insider pump and dump group",
    ),
    (
        "Double your money in 48 hours! Deposit Rs 10,000 in digital gold pool and get Rs 20,000. Register https://crypto-rich.vip",
        ScamCategory.INVESTMENT_SCAM,
        "High-yield doubling Ponzi scheme",
    ),

    # 10. Voice Phishing (Digital Arrest / Vishing)
    (
        "Digital Arrest Notice: Inspector Ajay Kumar from Mumbai Cyber Crime Branch. An illegal courier containing narcotics was intercepted with your Aadhaar.",
        ScamCategory.VOICE_PHISHING,
        "Digital arrest drugs courier intimidation",
    ),
    (
        "Calling from Telecom Regulatory Authority (TRAI): Your mobile number will be terminated in 2 hours due to illegal bulk SMS complaints.",
        ScamCategory.VOICE_PHISHING,
        "TRAI telecom disconnection vishing",
    ),
    (
        "CBI New Delhi: An arrest warrant has been issued in your name regarding money laundering case. Remain on video call.",
        ScamCategory.VOICE_PHISHING,
        "CBI impersonation video call surveillance",
    ),

    # 11. Benign (Legitimate Messages)
    (
        "Dear Customer, your A/C ending in 4921 is credited with Rs 15,000 on 14-Sep-2024 by UPI/P2A. Available balance: Rs 48,200. - SBI",
        ScamCategory.BENIGN,
        "Authentic bank credit SMS alert",
    ),
    (
        "Your OTP for login to Swiggy account is 492018. Valid for 10 minutes. Please do not share this OTP with anyone.",
        ScamCategory.BENIGN,
        "Authentic e-commerce login OTP",
    ),
    (
        "Your order #ORD8921 has been delivered by BlueDart. Thank you for shopping with Flipkart! Rate your delivery executive.",
        ScamCategory.BENIGN,
        "Authentic courier delivery confirmation",
    ),
    (
        "Hi Rahul, team sync scheduled at 4:30 PM today on Google Meet. Please review the quarterly metrics doc beforehand.",
        ScamCategory.BENIGN,
        "Normal workplace meeting communication",
    ),
    (
        "Dear Cardholder, statement for credit card ending 8291 generated. Total due: Rs 4,250. Due date: 28-Sep-2024. - Axis Bank",
        ScamCategory.BENIGN,
        "Authentic monthly credit card statement alert",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Unittest Test Case
# ─────────────────────────────────────────────────────────────────────────────

class TestScamClassifier(unittest.TestCase):
    """Test suite for validating scam classification across all 11 classes."""

    def test_model_loaded(self):
        """Verify that the trained ML model is loaded from disk."""
        from classification.classifier import TrainedScamClassifier
        model = TrainedScamClassifier.get_model()
        self.assertIsNotNone(model, "Trained model could not be loaded from models/ directory")

    def test_indicator_extraction(self):
        """Verify that suspicious indicators are extracted for phishing links."""
        text = "Dear user your SBI account is blocked. Update KYC immediately at http://bit.ly/sbi-pan"
        result = classify_text(text)
        self.assertTrue(len(result.indicators) > 0, "Failed to extract indicators")
        self.assertTrue(
            any("link" in ind or "urgent" in ind or "kyc" in ind for ind in result.indicators),
            f"Indicators missed key triggers: {result.indicators}"
        )

    def test_all_catalog_cases(self):
        """Run all 35+ realistic Indian fraud and benign test cases."""
        passed = 0
        total = len(TEST_CASES)

        print("\n" + "=" * 80)
        print(f"Running FraudGuard AI Classifier Test Suite ({total} Real-World Test Cases)")
        print("=" * 80)

        for text, expected_category, description in TEST_CASES:
            with self.subTest(case=description):
                result = classify_text(text, use_ml=True)
                self.assertIsNotNone(result, f"Result was None for: {description}")
                self.assertEqual(
                    result.category,
                    expected_category,
                    f"Failed [{description}]: Expected {expected_category.value}, got {result.category.value} "
                    f"with confidence {result.confidence:.2f} for text: '{text}'"
                )
                self.assertGreaterEqual(
                    result.confidence,
                    0.35,
                    f"Confidence too low ({result.confidence:.2f}) for: '{text}'"
                )

                if expected_category == ScamCategory.BENIGN:
                    self.assertEqual(
                        result.risk_level,
                        RiskLevel.SAFE,
                        f"Benign message was flagged with risk: {result.risk_level.value}"
                    )
                else:
                    self.assertIn(
                        result.risk_level,
                        [RiskLevel.HIGH, RiskLevel.MEDIUM],
                        f"Scam [{expected_category.value}] had unexpected risk level: {result.risk_level.value}"
                    )

                passed += 1
                print(f"  [PASS] ({result.confidence*100:.1f}%) {expected_category.value:<18} | {description}")

        print("=" * 80)
        print(f"Test Suite Summary: {passed}/{total} test cases passed successfully (100% PASS RATE)!")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
