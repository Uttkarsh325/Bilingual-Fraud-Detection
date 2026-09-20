"""
Dataset Builder for FraudGuard AI — Multilingual Financial Fraud Detection.

This module compiles a diverse, high-quality, heavily expanded dataset of Indian
financial fraud patterns across all 11 taxonomy categories (10 fraud types + 1 benign class).
It guarantees:
  1. Balanced representation across all 11 categories (target ~1,000+ unique samples per class).
  2. Realistic contemporary Indian context (UPI, VPA, YONO, KYC, Bijli bill, Digital Arrest,
     eSIM swap, Telegram task jobs, fake loan apps).
  3. Trilingual representation: English (en-IN), Hinglish (hi-Latn), and Hindi in Devanagari (hi-IN).
  4. Stratified Train (70%), Validation (15%), and Test (15%) splits.
  5. Strict deduplication to prevent data leakage between train, val, and test sets.
"""

import os
import random
import re
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Output paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SPLITS_DIR = DATA_DIR / "splits"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Parameter Pools for Hyper-Realistic Synthetic Variation
# ─────────────────────────────────────────────────────────────────────────────

BANKS = [
    "SBI", "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank",
    "Punjab National Bank", "PNB", "Bank of Baroda", "BOB", "Canara Bank",
    "Kotak Mahindra Bank", "Union Bank of India", "IndusInd Bank", "Yes Bank", "IDFC FIRST Bank"
]

UPI_APPS = ["PhonePe", "Google Pay", "GPay", "Paytm", "BHIM UPI", "CRED", "Amazon Pay", "MobiKwik"]

NAMES = [
    "Ramesh Kumar", "Priya Sharma", "Rahul Verma", "Inspector Ajay Kumar", "Rana Pratap Singh",
    "Vikram Malhotra", "Sneha Patel", "Amit Shah", "Rajesh Gupta", "Anita Rao",
    "Sunil Joshi", "Deepak Verma", "Pooja Mishra", "Kavita Reddy", "Arun Nair",
    "Sanjay Singhania", "Neha Deshmukh", "Manoj Tiwari", "Alok Pandey", "Suresh Raina",
    "DCP Mahesh Sharma", "Sub-Inspector Sandeep", "Advocate Alok Verma"
]

CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Kolkata", "Chennai", "Pune",
    "Ahmedabad", "Jaipur", "Lucknow", "Patna", "Indore", "Bhopal", "Chandigarh", "Surat"
]

DATES_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

AMOUNTS = [
    199, 299, 499, 750, 999, 1200, 1499, 2000, 2450, 3200, 4500, 4999,
    6500, 8500, 10000, 12500, 15000, 18000, 20000, 25000, 35000, 45000,
    50000, 75000, 85000, 100000, 250000, 500000, 2500000
]

VPAS = ["ybl", "okaxis", "okhdfcbank", "oksbi", "paytm", "apl", "icici", "barodampay"]

PREFIXES_EN = [
    "", "URGENT: ", "ALERT: ", "NOTICE: ", "IMPORTANT: ", "WARNING: ",
    "Action Required: ", "Final Reminder: ", "Priority: ", "Immediate Attention: "
]

PREFIXES_HI_LATN = [
    "", "Zaroori Suchna: ", "Dhyan Dein: ", "Alert: ", "Urgent Notice: ",
    "Chetawani: ", "Aakhri Chetawani: ", "Savdhan Rahe: ", "Important Update: "
]

PREFIXES_HI_IN = [
    "", "सावधान: ", "अंतिम चेतावनी: ", "तत्काल सूचना: ", "महत्वपूर्ण सूचना: ",
    "सतर्कता अलर्ट: ", "आवश्यक सूचना: ", "अंतिम रिमाइंडर: "
]


# ─────────────────────────────────────────────────────────────────────────────
# Raw Bilingual Templates across all 11 Categories
# Each entry is a tuple: (template_text, language_code)
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATES: dict[str, list[tuple[str, str]]] = {
    # ─────────────────────────────────────────────────────────────────────────
    # 1. UPI COLLECT SCAM
    # ─────────────────────────────────────────────────────────────────────────
    "upi_collect_scam": [
        # English
        ("Dear Customer, you received a cashback of Rs {amt}. Click to approve collect request in {app}: upi://pay?pa=cb{id}@{vpa}&am={amt}", "en-IN"),
        ("Your refund of Rs {amt} is pending. Scan this QR code and enter your UPI PIN to credit your bank account immediately.", "en-IN"),
        ("Payment of Rs {amt} received from OLX buyer {name}. Please approve the collect request on {app} to accept money into your account.", "en-IN"),
        ("Congratulations! You won Rs {amt} scratch card reward on {app}. Scan QR code to transfer prize directly to {bank}.", "en-IN"),
        ("Dear User, an incoming UPI transfer of Rs {amt} from {name} is waiting. Enter your 6-digit PIN on this collect request to receive.", "en-IN"),
        ("Amazon cashback of Rs {amt} credited. Open {app} and click 'Approve Payment' to deposit into {bank} account.", "en-IN"),
        ("Flipkart refund failed for order #{id}. Please scan this attached QR code and input UPI PIN to initiate instant refund of Rs {amt}.", "en-IN"),
        ("Sent you Rs {amt} by mistake instead of Rs 500 on {app}. Please approve reverse collect request or refund back immediately.", "en-IN"),
        ("Scan QR code with any UPI App ({app}) to receive your pending payment of Rs {amt} from Army Officer {name}.", "en-IN"),
        ("Customer care update: Your pending reward of Rs {amt} is ready. Click the collect link upi://pay?pa=win{id}@{vpa} and enter PIN to claim.", "en-IN"),
        ("Approve the pending UPI collect request of Rs {amt} on {app} app to unlock your merchant credit limit #{id}.", "en-IN"),
        ("Electricity bill excess payment refund of Rs {amt} for consumer {id}. Scan QR code on your mobile banking app to claim refund.", "en-IN"),
        ("OLX item #{id} sold! Buyer {name} has sent payment via QR. Open {app}, select 'Scan QR', enter UPI PIN to deposit Rs {amt}.", "en-IN"),
        ("Dear merchant, daily settlement of Rs {amt} is pending. Click to approve collect request: upi://pay?pa=settle{id}@{vpa}", "en-IN"),
        ("Your cashback voucher of Rs {amt} on Cred is ready. Scan QR code and confirm with your UPI PIN to claim directly into {bank}.", "en-IN"),
        ("Urgent: An instant payment request of Rs {amt} from buyer {name} requires your PIN authorization to accept money into {bank}.", "en-IN"),
        ("To receive Rs {amt} prize money into your {bank} account, authorize incoming collect notification in {app} within 10 mins.", "en-IN"),
        ("Payment settlement: Click upi://pay?pa=refund{id}@{vpa}&am={amt} and enter secret 4-digit PIN to receive fund directly.", "en-IN"),
        ("Zomato gold cashback Rs {amt} is waiting for user #{id}. Open {app}, accept collect request and verify your PIN to claim.", "en-IN"),
        ("Your friend {name} sent you Rs {amt} via {app}. Tap the collect pop-up and input UPI PIN to deposit into account ending {id}.", "en-IN"),
        ("Govt DBT subsidy Rs {amt} release request received for beneficiary #{id}. Authorize collect request on {app} by confirming UPI PIN.", "en-IN"),
        ("Quick transfer: Scan QR on screen, enter your security PIN and Rs {amt} will be credited to {bank} instantly. Ref #{id}.", "en-IN"),
        ("Meesho seller payout of Rs {amt} pending approval for invoice #{id}. Click collect link and enter PIN to finalize deposit.", "en-IN"),
        ("Swiggy refund of Rs {amt} needs bank confirmation. Authorize collect mandate in {app} using MPIN to account #{id}.", "en-IN"),
        ("Notice: Rs {amt} transfer failed. Scan this dynamic QR code and enter UPI PIN to re-credit to your {bank} account.", "en-IN"),
        # Hinglish
        ("Aapko Rs {amt} ka cashback mila hai. {app} me collect request approve karein aur UPI PIN enter karein account #{id} me lene ke liye.", "hi-Latn"),
        ("OLX buyer {name} ne advance payment bheja hai. QR code scan karke UPI PIN dalein taaki paise aapke {bank} account me aayein.", "hi-Latn"),
        ("{app} par collect request accept karein aur 6-digit PIN enter karein Rs {amt} receive karne ke liye. Ref #{id}.", "hi-Latn"),
        ("Cashback lene ke liye QR scan karein aur apna security PIN dalein, turant {bank} me Rs {amt} deposit hoga.", "hi-Latn"),
        ("Galti se aapke account me Rs {amt} send ho gaya hai. Reverse collect request approve karke return karein. Contact {name}.", "hi-Latn"),
        ("{app} scratch card me aapne Rs {amt} jeeta hai. Link par click karein aur UPI PIN daal kar claim karein.", "hi-Latn"),
        ("Army officer {name} ne furniture khareedne ke liye QR code bheja hai. Scan karke PIN enter karein paise lene ke liye.", "hi-Latn"),
        ("Flipkart refund Rs {amt} pending hai order #{id} ka. {app} open karein aur collect request par PIN daal kar receive karein.", "hi-Latn"),
        ("Merchant settlement Rs {amt} lene ke liye collect mandate par apna UPI PIN verify karein {bank} me deposit ke liye.", "hi-Latn"),
        ("Bijli bill ka extra payment refund Rs {amt} lene ke liye QR code scan karein aur MPIN confirm karein.", "hi-Latn"),
        ("{app} par Rs {amt} ka coupon mila hai, collect notification approve karke apna bank PIN submit karein.", "hi-Latn"),
        ("Buyer {name} ne Rs {amt} bhej diya hai. Receive karne ke liye {app} me collect request ko accept karein aur PIN dalein.", "hi-Latn"),
        ("Dear user, {app} par cashback aaya hai Rs {amt}, turant collect request par PIN daal kar {bank} account me transfer karein.", "hi-Latn"),
        ("Aapke account me Rs {amt} transfer pending hai ref #{id}, accept karne ke liye UPI PIN enter karna compulsory hai.", "hi-Latn"),
        ("Swiggy failed payment refund: Collect link upi://pay?pa=claim{id}@{vpa}&am={amt} par click karein aur PIN dalein.", "hi-Latn"),
        # Devanagari Hindi
        ("बधाई हो! आपको {app} पर ₹{amt} का कैशबैक मिला है। प्राप्त करने के लिए QR कोड स्कैन करें और UPI पिन दर्ज करें। संदर्भ #{id}।", "hi-IN"),
        ("आपके खाते में ₹{amt} का रिफंड भेजा गया है। पैसे प्राप्त करने के लिए {app} पर कलेक्ट रिक्वेस्ट स्वीकार करें और पिन डालें।", "hi-IN"),
        ("OLX खरीदार {name} ने ₹{amt} का भुगतान भेजा है। पैसे खाते में जमा करने के लिए {app} पर QR स्कैन करें और UPI PIN डालें।", "hi-IN"),
        ("पेटीएम स्क्रैच कार्ड में आपने ₹{amt} जीते हैं। पुरस्कार राशि {bank} में सीधे प्राप्त करने के लिए पिन दर्ज करें।", "hi-IN"),
        ("गलती से आपके खाते में ₹{amt} ट्रांसफर हो गए हैं। कृपया रिवर्स कलेक्ट रिक्वेस्ट स्वीकार करके पैसे वापस करें। प्रेषक: {name}।", "hi-IN"),
        ("सेना अधिकारी {name} द्वारा भेजा गया अग्रिम भुगतान स्वीकार करने के लिए QR कोड स्कैन करें और अपना 6-अंकीय पिन डालें।", "hi-IN"),
        ("बिजली बिल अतिरिक्त भुगतान का ₹{amt} रिफंड पाने के लिए {app} में कलेक्ट लिंक खोलें और पिन सत्यापित करें। बिल #{id}।", "hi-IN"),
        ("अमेज़न कैशबैक ₹{amt} तैयार है। {bank} खाते में जमा करने के लिए 'भुगतान स्वीकार करें' पर क्लिक कर पिन दर्ज करें।", "hi-IN"),
        ("ग्राहक सूचना: ₹{amt} का भुगतान प्राप्त करने के लिए अपने {app} ऐप पर कलेक्ट अनुरोध को पिन डालकर तुरंत अनुमति दें।", "hi-IN"),
        ("फ्लिपकार्ट रिफंड: बैंक खाते में राशि ₹{amt} तुरंत जमा करने के लिए संलग्न QR कोड स्कैन करके अपना गुप्त पिन दर्ज करें।", "hi-IN"),
        ("दैनिक मर्चेंट सेटलमेंट ₹{amt} पेंडिंग है। बैंक में पाने के लिए कलेक्ट रिक्वेस्ट पर क्लिक करें और UPI PIN डालें।", "hi-IN"),
        ("खाते में ₹{amt} प्राप्त करने के लिए {app} खोलें और कलेक्ट अधिसूचना पर अपना MPIN दर्ज करें।", "hi-IN"),
        ("आपका ₹{amt} का रिवॉर्ड तैयार है। लिंक upi://pay?pa=rew{id}@{vpa}&am={amt} पर क्लिक करके पिन डालकर क्लेम करें।", "hi-IN"),
        ("सरकारी योजना के तहत ₹{amt} की सब्सिडी लेने के लिए BHIM ऐप में कलेक्ट रिक्वेस्ट पर UPI पिन सत्यापित करें। लाभार्थी #{id}।", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 2. PHISHING LINK
    # ─────────────────────────────────────────────────────────────────────────
    "phishing_link": [
        # English
        ("Dear {bank} User, your NetBanking account #{id} will be blocked today due to expired KYC. Update PAN immediately at https://{bank_slug}-pan-kyc{id}.xyz", "en-IN"),
        ("Urgent Notice: Electricity power to consumer #{id} will be disconnected tonight at 9:30 PM by Bijli Vibhag due to unpaid bill of Rs {amt}. Click https://bijli-pay{id}.in", "en-IN"),
        ("{bank} Alert: Your NetBanking access is disabled. Please verify your Aadhaar card and PAN at https://{bank_slug}-verify-login{id}.com", "en-IN"),
        ("Your {bank} Credit Card points worth Rs {amt} are expiring today. Redeem cash directly at https://{bank_slug}-points-redeem{id}.top", "en-IN"),
        ("Income Tax Refund of Rs {amt} approved for PAN ending {id}. Confirm bank account details within 24 hours at https://incometax-efiling-refund{id}.online", "en-IN"),
        ("PNB Alert: Dear Customer #{id}, your account is suspended due to non-submission of KYC. Re-activate by clicking https://pnb-rekyc{id}.site", "en-IN"),
        ("Paytm KYC Notice: Your wallet will be deactivated within 12 hours. Update Aadhaar and PAN at https://paytm-kyc-desk{id}.live", "en-IN"),
        ("Dear consumer, your electricity bill no {id} for Rs {amt} is overdue. Pay immediately at https://state-power-discom{id}.com to avoid immediate line cut.", "en-IN"),
        ("Bank of Baroda: Important! Update mobile number on account #{id} and PAN card to avoid debit card deactivation at https://bob-kyc-update{id}.in", "en-IN"),
        ("Your Netflix subscription for account {id} has expired and payment failed. Update card details to continue watching: https://netflix-update-billing{id}.co", "en-IN"),
        ("Speed Post: Your package #IN{id} cannot be delivered to {city} due to incomplete address. Update details and pay Rs 25 fee at https://indiapost-parcel-tracking{id}.com", "en-IN"),
        ("Airtel Alert: Your SIM card KYC is incomplete for {id}. It will be disconnected in 24 hours. Update KYC at https://airtel-5g-kyc{id}.net", "en-IN"),
        ("Axis Bank: Dear customer, temporary block placed on card ending {id}. Verify recent transaction of Rs {amt} at https://axis-security-alert{id}.info", "en-IN"),
        ("EPFO Alert: Claim of Rs {amt} approved for UAN #{id}. Verify credentials to disburse funds at https://epfo-claim-status{id}.org", "en-IN"),
        ("Jio Notice: Complete your e-KYC update for number ending {id} to continue enjoying unlimited 5G services: https://jio-5g-upgrade{id}.top", "en-IN"),
        ("SBI YONO notice: Your account login suspended. Submit mandatory identity verification for customer #{id} at https://sbi-yono-portal{id}.xyz", "en-IN"),
        ("Courier delivery hold: Indian Customs package #{id} awaiting delivery tax clearance of Rs 48 at {city}. Pay at https://delhivery-customs{id}.site", "en-IN"),
        ("HDFC Bank Alert: Mandatory PAN-Aadhaar seeding required for customer #{id}. Update now at https://hdfc-aadhaar-link{id}.live", "en-IN"),
        ("BSNL 4G to 5G migration pending for number {id}. Complete mandatory KYC before midnight at https://bsnl-5g-verification{id}.in", "en-IN"),
        ("Vehicle Challan Alert: Traffic penalty of Rs {amt} pending against vehicle in {city}. Clear challan at https://echallan-parivahan-pay{id}.top", "en-IN"),
        ("Gas Agency Notice: Subsidized LPG cylinder booking suspended for consumer #{id}. Re-verify consumer connection at https://iocl-indane-update{id}.online", "en-IN"),
        ("Voter ID link with Aadhaar mandatory for EPIC #{id}. Avoid deletion from electoral roll by updating at https://nvsp-voter-link{id}.info", "en-IN"),
        ("Google Account Security: Suspicious login from Russia detected for user #{id}. Secure your account now at https://myaccount-google-security{id}.site", "en-IN"),
        ("Claim your free Rs 500 mobile recharge sponsored by Govt for mobile #{id} at https://pm-free-recharge-yojana{id}.xyz", "en-IN"),
        ("Fastag Account Suspended for vehicle #{id}: Insufficient KYC. Update vehicle RC and Aadhaar at https://fastag-nhai-verify{id}.com", "en-IN"),
        # Hinglish
        ("Dear {bank} customer, aapka YONO account #{id} block hone wala hai. Turant PAN update karein https://{bank_slug}-kyc{id}.xyz", "hi-Latn"),
        ("Bijli Vibhag Notice: Consumer #{id} ki bijli aaj raat 9:30 baje kaat di jayegi unpaid bill Rs {amt} ke karan. Pay karein https://bijli-bill{id}.in", "hi-Latn"),
        ("Aapka {bank} account freeze ho chuka hai KYC expire hone par. Click karke activate karein https://{bank_slug}-activate{id}.com", "hi-Latn"),
        ("Credit card points worth Rs {amt} expire ho rahe hain. Cash me convert karne ke liye link open karein https://card-reward{id}.site", "hi-Latn"),
        ("Speed Post parcel #{id} address incomplete hai {city} me. Rs 25 charge dekar address sahi karein https://indiapost-parcel{id}.online", "hi-Latn"),
        ("Airtel SIM band ho jayega 24 ghante me number {id} ka. 5G e-KYC update karne ke liye visit karein https://airtel-kyc-desk{id}.net", "hi-Latn"),
        ("Dear consumer #{id}, aapka light connection cut hone se bachane ke liye turant bill Rs {amt} bharein https://discom-bill-pay{id}.com", "hi-Latn"),
        ("Traffic Police {city}: Aapki gadi ka Rs {amt} challan baki hai. Court notice se bachne ke liye pay karein https://parivahan-fine{id}.top", "hi-Latn"),
        ("Income tax refund Rs {amt} approved ho chuka hai PAN #{id} ka. Account me lene ke liye form fill karein https://tax-refund-gov{id}.site", "hi-Latn"),
        ("Fastag tag #{id} blacklist ho chuka hai. Dobara chalu karne ke liye KYC complete karein https://fastag-rekyc{id}.live", "hi-Latn"),
        ("Paytm wallet inactive ho gaya hai user #{id} ka. PAN card link karke activate karein https://paytm-wallet-kyc{id}.in", "hi-Latn"),
        ("Jio 5G welcome offer claim karne ke liye number {id} par KYC details submit karein https://jio-5g-claim{id}.info", "hi-Latn"),
        ("{bank} account ending {id} me mobile number update karne ke liye form bharein https://bank-mobile-update{id}.com", "hi-Latn"),
        ("LPG gas subsidy consumer #{id} ke account me lene ke liye Aadhaar verify karein https://lpg-subsidy-portal{id}.online", "hi-Latn"),
        ("SBI NetBanking disabled for CIF #{id}: Password reset aur security verification karein https://sbi-secure-portal{id}.xyz", "hi-Latn"),
        # Devanagari Hindi
        ("प्रिय ग्राहक, आपका {bank} खाता #{id} आज रात बंद कर दिया जाएगा क्योंकि KYC समाप्त हो चुका है। तुरंत अपडेट करें: https://{bank_slug}-pan-kyc{id}.xyz", "hi-IN"),
        ("बिजली विभाग: उपभोक्ता #{id}, आपका ₹{amt} का पिछला बिल जमा न होने के कारण आज रात 9:30 बजे बिजली काट दी जाएगी। तुरंत भुगतान करें: https://bijli-pay{id}.in", "hi-IN"),
        ("इंडिया पोस्ट: आपका स्पीड पोस्ट पार्सल #IN{id} गलत पते के कारण रोका गया है। पता अपडेट करें और ₹25 शुल्क भरें: https://indiapost-update{id}.com", "hi-IN"),
        ("आयकर विभाग: ₹{amt} का टैक्स रिफंड स्वीकृत हुआ है। 24 घंटे के अंदर बैंक विवरण सत्यापित करें: https://incometax-refund{id}.online", "hi-IN"),
        ("क्रेडिट कार्ड पॉइंट्स: आपके कार्ड ending {id} के ₹{amt} के रिवॉर्ड पॉइंट्स आज समाप्त हो रहे हैं। नकद में बदलने के लिए लिंक खोलें: https://card-points{id}.top", "hi-IN"),
        ("एयरटेल सूचना: मोबाइल #{id} की KYC अधूरी है। 24 घंटे में सिम बंद होने से बचाने के लिए यहां सत्यापित करें: https://airtel-kyc{id}.net", "hi-IN"),
        ("ई-चालान सूचना: {city} में आपके वाहन का ₹{amt} का चालान लंबित है। कानूनी कार्रवाई से बचने हेतु भुगतान करें: https://echallan-pay{id}.live", "hi-IN"),
        ("फास्टैग अलर्ट: वाहन #{id} का फास्टैग खाता निष्क्रिय कर दिया गया है। पुनः सक्रिय करने के लिए KYC करें: https://fastag-verify{id}.site", "hi-IN"),
        ("गैस सब्सिडी: उपभोक्ता #{id} अपने बैंक खाते में एलपीजी सब्सिडी प्राप्त करने के लिए आधार कार्ड तुरंत लिंक करें: https://lpg-kyc{id}.org", "hi-IN"),
        ("पीएनबी अलर्ट: खाता #{id} निलंबित कर दिया गया है। पुनः सक्रिय करने के लिए नेटबैंकिंग लॉगिन करें: https://pnb-rekyc{id}.info", "hi-IN"),
        ("राशन कार्ड नवीनीकरण: कार्ड #{id} पर मुफ्त राशन योजना जारी रखने हेतु परिवार के सदस्यों का सत्यापन करें: https://ration-card-kyc{id}.in", "hi-IN"),
        ("जियो अलर्ट: नंबर {id} पर 5जी सेवा जारी रखने के लिए तुरंत ई-केवाईसी पूरा करें: https://jio-5g-upgrade{id}.top", "hi-IN"),
        ("भारतीय स्टेट बैंक: प्रिय ग्राहक #{id}, आपकी नेटबैंकिंग बंद कर दी गई है। तुरंत पैन लिंक करें: https://sbi-kyc-form{id}.online", "hi-IN"),
        ("पेटीएम वॉलेट सूचना: 12 घंटे में वॉलेट #{id} बंद हो जाएगा। आधार कार्ड अपडेट करने के लिए यहां क्लिक करें: https://paytm-kyc{id}.xyz", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 3. OTP SCAM
    # ─────────────────────────────────────────────────────────────────────────
    "otp_scam": [
        # English
        ("Hello sir, I am {name} from {bank} fraud prevention department. We detected an unauthorized transaction of Rs {amt}. Please share the 6-digit OTP sent to your phone to cancel it.", "en-IN"),
        ("{bank} Customer Care: To prevent unauthorized withdrawal of Rs {amt} from card ending {id}, tell the verification OTP received on your mobile.", "en-IN"),
        ("Airtel verification officer {name} here. Your SIM card #{id} will be blocked unless you confirm the 4-digit verification code received just now.", "en-IN"),
        ("Delivery agent outside: Sir I am {name} here with your Amazon parcel #{id}. Please share the delivery OTP to complete handover.", "en-IN"),
        ("Paytm representative: Your cashback of Rs {amt} is approved for order #{id}. To disburse, share the one-time password sent by our server.", "en-IN"),
        ("Dear customer, to upgrade your {bank} debit card limit to Rs 5 Lakhs on account #{id}, please verify the authorization code sent to your registered mobile number.", "en-IN"),
        ("Calling from Police Cyber Cell {city}: Your {bank} account #{id} was used in suspicious activity. Read out the verification code to avoid account seizure.", "en-IN"),
        ("Swiggy support: We are processing your cancellation refund of Rs {amt} for order #{id}. Please share the OTP sent by SMS to approve the transfer.", "en-IN"),
        ("{bank} security team: We have blocked a transaction of Rs {amt} at merchant #{id}. To confirm you did NOT make it, tell us the OTP.", "en-IN"),
        ("Electricity department {city}: To confirm your meter payment of Rs {amt} for connection #{id}, provide the 6-digit verification code sent to your phone.", "en-IN"),
        ("IRCTC agent {name}: Your train ticket refund of Rs {amt} for PNR #{id} is ready. Share OTP received on mobile to credit amount into your account.", "en-IN"),
        ("Canara Bank: NetBanking password reset initiated for user #{id}. If not done by you, immediately share the OTP with support officer on call.", "en-IN"),
        ("HDFC Credit Card Dept: To waive your annual card fee of Rs 2,500 on card ending {id}, please tell executive {name} the 6-digit OTP received via SMS.", "en-IN"),
        ("EPFO Helpdesk: To credit your PF withdrawal claim of Rs {amt} for UAN #{id}, disclose the Aadhaar authentication OTP.", "en-IN"),
        ("Amazon Pay Support: Unauthorized order placed for iPhone worth Rs {amt} on account #{id}. Share OTP to initiate instant cancellation.", "en-IN"),
        ("Zomato executive {name}: Sir, to process your food refund of Rs {amt} for order #{id}, give me the 4-digit code sent on SMS.", "en-IN"),
        ("Telecom Regulatory Authority: To prevent your number ending {id} disconnection, confirm the 6-digit security code immediately.", "en-IN"),
        ("PhonePe technical desk: Your wallet balance of Rs {amt} is on hold for transaction #{id}. Tell the validation code to unfreeze your funds.", "en-IN"),
        ("UIDAI Aadhaar Helpline: Verification call regarding biometric lock on Aadhaar ending {id}. Please tell the 6-digit OTP sent to your phone.", "en-IN"),
        ("Flipkart Delivery Desk: Delivery attempted for parcel #{id}. Share the 6-digit OTP to reschedule package delivery in {city}.", "en-IN"),
        ("Income Tax Helpdesk: To deposit tax refund of Rs {amt} for assessment #{id}, read the one-time passcode received from NSDL.", "en-IN"),
        ("Courier Tracking Desk: Parcel #{id} held at {city} customs. Tell the verification OTP to dispatch to your address.", "en-IN"),
        ("Google Pay Verification: To claim bonus Rs {amt} on scratch card #{id}, share the SMS passcode with customer care executive.", "en-IN"),
        ("Credit Card Reward Desk: Converting reward points into cash Rs {amt} for card ending {id}. Kindly confirm the one-time password.", "en-IN"),
        # Hinglish
        ("Namaste sir, main {name} {bank} fraud department se bol raha hoon. Rs {amt} ka fraud rokne ke liye turant mobile par aaya OTP batayein. Ref #{id}.", "hi-Latn"),
        ("Airtel head office se call hai. Aapka SIM ending {id} 2 ghante me band ho jayega, verify karne ke liye abhi aaya OTP share karein.", "hi-Latn"),
        ("Amazon delivery boy {name} bol raha hoon, parcel #{id} dispatch ho raha hai, confirm karne ke liye OTP bata dijiye sir.", "hi-Latn"),
        ("Paytm customer care: Aapka Rs {amt} ka cashback account me transfer karne ke liye mobile par aaya OTP confirm karein.", "hi-Latn"),
        ("Credit card limit badhane ke liye {bank} se call hai card ending {id} par. SMS me aaya hua 6-digit verification code batayein.", "hi-Latn"),
        ("Police cyber cell {city} se bol rahe hain, aapke account #{id} se illegal transaction hua hai. Block karne ke liye OTP share karein.", "hi-Latn"),
        ("Swiggy refund initiate ho gaya hai order #{id} ka. Aapke number par 4-digit code aaya hoga, wo batayein taaki paisa account me aaye.", "hi-Latn"),
        ("Bijli vibhag {city}: Bill payment Rs {amt} confirm karne ke liye SMS ka OTP executive {name} ko batayein.", "hi-Latn"),
        ("IRCTC ticket cancel refund Rs {amt} lene ke liye PNR #{id} par aaya hua One Time Password share karein.", "hi-Latn"),
        ("HDFC annual fee zero karne ke liye bank officer {name} ko phone par aaya OTP bata dijiye card ending {id} ka.", "hi-Latn"),
        ("Aapka {bank} NetBanking password hack ho gaya hai user #{id}, turant stop karne ke liye aaya hua verification OTP share karein.", "hi-Latn"),
        ("Flipkart support: Return parcel #{id} cancel ho gaya hai, Rs {amt} refund lene ke liye SMS code bataiye.", "hi-Latn"),
        ("PF claim pass ho gaya hai Rs {amt} UAN #{id} ka. Account me transfer ke liye Aadhaar OTP verify karwayein phone par.", "hi-Latn"),
        ("GPay cashback Rs {amt} release karne ke liye scratch card #{id} ka secret OTP batayein sir.", "hi-Latn"),
        # Devanagari Hindi
        ("नमस्ते सर, मैं {name} {bank} के धोखाधड़ी रोकथाम विभाग से बोल रहा हूँ। आपके खाते #{id} से संदिग्ध लेनदेन ₹{amt} रोकने के लिए प्राप्त 6 अंकों का OTP बताएं।", "hi-IN"),
        ("एयरटेल वेरिफिकेशन: यदि आप अपना सिम #{id} ब्लॉक होने से बचाना चाहते हैं तो तुरंत मोबाइल पर आया 4 अंकों का कोड साझा करें।", "hi-IN"),
        ("अमेज़न डिलीवरी: सर, पार्सल #{id} लेकर {name} आया हूँ। कृपया डिलीवरी पूरी करने के लिए अपने फोन पर आया OTP बताएं।", "hi-IN"),
        ("पेटीएम प्रतिनिधि: आपका ₹{amt} का कैशबैक स्वीकृत हो गया है। खाते #{id} में भेजने के लिए मोबाइल पर भेजा गया वन-टाइम पासवर्ड बताएं।", "hi-IN"),
        ("क्रेडिट कार्ड विभाग: अपने कार्ड ending {id} की लिमिट ₹5 लाख तक बढ़ाने के लिए पंजीकृत मोबाइल पर आया सत्यापन कोड सत्यापित करें।", "hi-IN"),
        ("साइबर सेल {city} पुलिस अधिकारी: आपके बैंक खाते #{id} से अवैध लेनदेन देखा गया है। खाता सीज होने से बचाने के लिए प्राप्त OTP तुरंत बताएं।", "hi-IN"),
        ("स्विगी सपोर्ट: ऑर्डर #{id} के रिफंड ₹{amt} के लिए आपके नंबर पर 4 अंकों का कोड भेजा गया है, कृपया उसे साझा करें।", "hi-IN"),
        ("{bank} सुरक्षा शाखा: ₹{amt} के गलत लेनदेन को रोकने के लिए अभी प्राप्त हुआ 6 अंकों का कोड बताएं। संदर्भ #{id}।", "hi-IN"),
        ("बिजली बिल सत्यापन {city}: उपभोक्ता #{id} का मीटर कनेक्शन चालू रखने के लिए आपके मोबाइल पर आया सत्यापन कोड हमारे अधिकारी को दें।", "hi-IN"),
        ("आईआरसीटीसी रिफंड: रेल टिकट PNR #{id} का रिफंड ₹{amt} खाते में जमा करने के लिए एसएमएस द्वारा प्राप्त गुप्त कोड बताएं।", "hi-IN"),
        ("ईपीएफओ सहायता केंद्र: पीएफ निकासी राशि ₹{amt} जारी करने के लिए UAN #{id} पर आया आधार प्रमाणीकरण ओटीपी दर्ज करवाएं।", "hi-IN"),
        ("फ्लिपकार्ट सहायता: ऑर्डर #{id} रद्द करने और ₹{amt} तुरंत खाते में वापस पाने के लिए फोन पर आया पासवर्ड बताएं।", "hi-IN"),
        ("फोनपे तकनीकी विभाग: आपके वॉलेट की रोक हटाने के लिए लेनदेन #{id} पर एसएमएस द्वारा प्राप्त 6 अंकों का कोड तुरंत प्रदान करें।", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 4. FAKE REFUND
    # ─────────────────────────────────────────────────────────────────────────
    "fake_refund": [
        # English
        ("Dear User, your order #{id} on Flipkart has been cancelled. An excess amount of Rs {amt} was debited. Click here to claim your refund: https://refund-desk{id}.com", "en-IN"),
        ("Refund Notice: We accidentally charged your credit card ending {id} Rs {amt} twice for your airline ticket to {city}. Contact customer desk at 98{id} to process reversal.", "en-IN"),
        ("Amazon customer: Your return request for order #{id} has been processed. To receive Rs {amt} in your {bank} account, accept the reverse transaction.", "en-IN"),
        ("Your IRCTC tatkal booking failed for PNR #{id} but money Rs {amt} was deducted. Call 97{id} or click https://irctc-refund-portal{id}.in to claim refund.", "en-IN"),
        ("PhonePe Alert: Failed recharge of Rs {amt} on mobile #{id} has been refunded. Click to claim into your account: https://phonepe-refunds{id}.site", "en-IN"),
        ("Dear customer, excess electricity billing of Rs {amt} detected in consumer account #{id} at {city}. Apply for rebate credit at https://bijli-rebate{id}.com", "en-IN"),
        ("Paytm Mall: Cash on Delivery refund of Rs {amt} for order #{id} is waiting. Enter your UPI ID and accept refund request in app.", "en-IN"),
        ("Courier service: Delivery charges Rs {amt} for package #{id} overpaid in {city}. Please install AnyDesk or TeamViewer to verify your account for refund.", "en-IN"),
        ("Google Pay notice: Payment to merchant #{id} failed. Reversal of Rs {amt} ready. Open {app} and click claim refund button.", "en-IN"),
        ("Dear traveler, MakeMyTrip hotel cancellation refund of Rs {amt} for booking #{id} approved. Verify banking credentials to disburse funds into {bank}.", "en-IN"),
        ("Swiggy Helpdesk: Double deduction of Rs {amt} detected on food order #{id}. Call 91{id} to authorize instant money reversal.", "en-IN"),
        ("Zomato refund desk: Order #{id} cancelled. To get refund Rs {amt} credited, install QuickSupport app and share device ID with agent {name}.", "en-IN"),
        ("BookMyShow refund: Movie tickets for booking #{id} cancelled. Click https://bms-refunds{id}.top to receive Rs {amt} back to UPI.", "en-IN"),
        ("IndiGo flight refund of Rs {amt} for PNR #{id} is pending bank clearance. Provide debit card CVV to authenticate fund transfer.", "en-IN"),
        ("Uber driver trip overcharge Rs {amt} in {city}. Claim fare refund voucher for ride #{id} at https://uber-fare-adjustment{id}.online", "en-IN"),
        ("College examination fee for student #{id} deducted twice. Fill refund mandate form at https://univ-exam-fee-refund{id}.site for Rs {amt}", "en-IN"),
        ("Myntra return accepted: Refund Rs {amt} on hold for order #{id}. Share screen via AnyDesk with agent {name} to approve payment transfer.", "en-IN"),
        ("Fastag toll duplicate deduction of Rs {amt} at {city} toll plaza for vehicle #{id}. Click https://toll-refund-desk{id}.in to credit toll balance.", "en-IN"),
        ("Hospital lab test fee refund Rs {amt} approved for bill #{id}. Send your Google Pay UPI ID to customer helpline 98{id}", "en-IN"),
        ("Broadband security deposit refund of Rs {amt} for account #{id} is ready. Accept reverse collect request in {app} to receive.", "en-IN"),
        # Hinglish
        ("Aapka Flipkart order #{id} cancel ho gaya tha, Rs {amt} ka refund lene ke liye link par click karein https://refund-desk{id}.com", "hi-Latn"),
        ("IRCTC tatkal ticket fail hua tha PNR #{id} ka lekin paisa kat gaya. Rs {amt} refund lene ke liye customer care 98{id} par call karein.", "hi-Latn"),
        ("Amazon return parcel #{id} ka Rs {amt} refund pending hai. Account verify karne ke liye AnyDesk install karein.", "hi-Latn"),
        ("PhonePe failed recharge refund: Mobile #{id} par kata Rs {amt} wapas lene ke liye app me reverse collect request ko accept karein.", "hi-Latn"),
        ("Bijli bill me Rs {amt} extra charge ho gaya tha consumer #{id} par. Rebate wapas lene ke liye portal open karein https://bijli-rebate{id}.in", "hi-Latn"),
        ("Swiggy order #{id} par double payment ho gaya tha. Customer care se Rs {amt} refund lene ke liye TeamViewer download karke connect karein.", "hi-Latn"),
        ("Paytm payment fail hua tha merchant #{id} ko. Rs {amt} reversal claim karne ke liye UPI PIN enter karein.", "hi-Latn"),
        ("Zomato food refund Rs {amt} lene ke liye executive {name} ko screen share karke bank app open karke dikhayein.", "hi-Latn"),
        ("MakeMyTrip hotel booking #{id} cancel refund Rs {amt} lene ke liye card details verify karein https://mmt-refunds{id}.online", "hi-Latn"),
        ("Courier service charge extra cut gaya tha parcel #{id} ka. {app} par aayi refund request accept karke paise credit karwayein.", "hi-Latn"),
        ("Uber trip #{id} me extra paise kate the {city} me. Fare refund Rs {amt} lene ke liye link par click karein https://uber-refund{id}.top", "hi-Latn"),
        ("Myntra order #{id} refund hold par hai, phone me AnyDesk app dal kar 9-digit code support officer {name} ko batayein.", "hi-Latn"),
        # Devanagari Hindi
        ("प्रिय ग्राहक, फ्लिपकार्ट पर आपका ऑर्डर #{id} रद्द हो गया है। ₹{amt} का रिफंड पाने के लिए इस लिंक पर क्लिक करें: https://refund-desk{id}.com", "hi-IN"),
        ("आईआरसीटीसी टिकट PNR #{id} विफल होने पर काटा गया ₹{amt} वापस पाने के लिए तुरंत हमारे कस्टमर केयर नंबर 98{id} पर संपर्क करें।", "hi-IN"),
        ("अमेज़न रिटर्न: आपके उत्पाद #{id} का रिफंड ₹{amt} जारी करने के लिए ग्राहक सेवा अधिकारी {name} से संपर्क करें और स्क्रीन शेयर करें।", "hi-IN"),
        ("फोनपे अलर्ट: मोबाइल #{id} के विफल रिचार्ज का ₹{amt} रिफंड तैयार है। खाते में प्राप्त करने के लिए लिंक पर क्लिक करें: https://phonepe-refund{id}.site", "hi-IN"),
        ("बिजली विभाग {city}: उपभोक्ता #{id} के पिछले बिल में ₹{amt} अधिक काट लिया गया था। अतिरिक्त राशि वापस पाने के लिए फॉर्म भरें: https://bijli-rebate{id}.in", "hi-IN"),
        ("स्विगी सपोर्ट: ऑर्डर #{id} का दोहरा भुगतान ₹{amt} वापस लेने के लिए दिए गए हेल्पलाइन नंबर 91{id} पर बात करें।", "hi-IN"),
        ("पेटीएम मॉल: रद्द किए गए सामान #{id} का ₹{amt} रिफंड लंबित है। अपने {bank} खाते में प्राप्त करने हेतु विवरण सत्यापित करें।", "hi-IN"),
        ("जोमैटो रिफंड: ऑर्डर #{id} के लिए आपके खाते में ₹{amt} भेजने के लिए AnyDesk ऐप इंस्टॉल करके अधिकारी को कोड बताएं।", "hi-IN"),
        ("फास्टैग टोल प्लाजा पर वाहन #{id} से दो बार काटा गया ₹{amt} वापस पाने के लिए राष्ट्रीय राजमार्ग रिफंड पोर्टल पर आवेदन करें।", "hi-IN"),
        ("मेकमाइंसट्रिप टिकट रद्दीकरण रिफंड ₹{amt} प्राप्त करने हेतु अपना डेबिट कार्ड नंबर और सीवीवी दर्ज करें बुकिंग #{id} के लिए।", "hi-IN"),
        ("कूरियर ओवरचार्ज रिफंड: पार्सल #{id} की अधिक ली गई डिलीवरी राशि ₹{amt} वापस पाने के लिए {app} पर रिवर्स रिक्वेस्ट स्वीकार करें।", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 5. LOAN SCAM
    # ─────────────────────────────────────────────────────────────────────────
    "loan_scam": [
        # English
        ("Congratulations! Pre-approved personal loan of Rs {amt} sanctioned with 0% interest and No CIBIL check for applicant #{id}. Download CashQuick APK: https://quick-loan{id}.apk", "en-IN"),
        ("Instant Loan Alert: Get Rs {amt} in 5 minutes directly in {bank} account. No documentation required. Click https://fast-money-credit{id}.in to apply.", "en-IN"),
        ("Dear customer #{id}, your loan of Rs {amt} is approved. Pay processing fee of Rs 1,500 to disburse full amount into your account immediately.", "en-IN"),
        ("Urgent: You borrowed Rs {amt} from RupeeMama loan app. Due date passed for file #{id}! Pay immediately or we will send your private photos to all contacts in {city}.", "en-IN"),
        ("Pre-approved Mudra loan of Rs {amt} from Govt of India for application #{id}. Deposit security fee Rs 2,000 to release funds at https://mudra-gov-loan{id}.site", "en-IN"),
        ("Get instant gold loan without pledge. Rs {amt} credited to {bank} in 10 mins. Install QuickRupee app now: https://rupee-instant{id}.xyz?id={id}", "en-IN"),
        ("Notice from Legal Recovery Team: Non-payment of loan app balance Rs {amt} for case #{id}. Police FIR being registered in {city}. Contact 91{id} to settle.", "en-IN"),
        ("Congratulations! Based on your PAN ending {id}, you are eligible for pre-approved loan of Rs {amt}. Click https://easyloan-india{id}.top", "en-IN"),
        ("Emergency Cash Loan! Need money fast? Get up to Rs {amt} today. Only Aadhaar card needed. WhatsApp your documents to 98{id}", "en-IN"),
        ("Loan approval letter attached: Sanctioned Rs {amt} for applicant {name}. Please transfer GST and documentation charges Rs 3,500 to account #{id} to release.", "en-IN"),
        ("Instant student loan of Rs {amt} approved for roll #{id} with zero collateral. Pay file opening fee Rs 999 at https://student-loan-hub{id}.site", "en-IN"),
        ("Final Warning: Defaulter notice #{id} issued. Transfer loan EMI of Rs {amt} within 2 hours or recovery agents will visit your home in {city}.", "en-IN"),
        ("Aadhaar Instant Loan: Borrow Rs {amt} at 1% interest rate per annum. Download APK file directly for profile #{id}: https://aadhaar-credit-loan{id}.apk", "en-IN"),
        ("Pre-sanctioned business loan of Rs {amt} approved under MSME scheme for file #{id}. Deposit insurance bond Rs 4,500 to receive cheque.", "en-IN"),
        ("Repay Rs {amt} today for loan #{id} to clear file or your morphed images will be circulated on Facebook and WhatsApp contact list.", "en-IN"),
        ("Bajaj Finance Limited: Instant personal loan of Rs {amt} credited for customer #{id}. Download loan agreement app: https://bajaj-fast-credit{id}.com", "en-IN"),
        ("Zero interest festival loan of Rs {amt} for citizens in {city}. Apply now using Aadhaar #{id}: https://festival-easy-loan{id}.online", "en-IN"),
        ("Legal Court Notice: Section 138 cheque bounce case initiated for unpaid loan balance Rs {amt} on file #{id}. Call lawyer {name} at 98{id} to settle.", "en-IN"),
        ("Quick Cash App: Pre-approved limit Rs {amt} ready to withdraw for account #{id}. Install app and grant contact permissions to disburse.", "en-IN"),
        ("Govt PM Svanidhi Loan: Rs {amt} loan approved for applicant #{id}. Transfer NOC certificate fee Rs 1,800 to government treasury officer {name}.", "en-IN"),
        # Hinglish
        ("Badhai ho! Pre-approved personal loan Rs {amt} bina CIBIL score ke approve ho gaya hai customer #{id} ka. App download karein https://quick-loan{id}.apk", "hi-Latn"),
        ("Aapka Rs {amt} ka loan sanction ho chuka hai file #{id} par. Amount lene ke liye Rs 1500 processing charge pehle jama karein.", "hi-Latn"),
        ("Warning: Loan app ka due payment Rs {amt} abhi bharein file #{id} ka warna aapki morphed photos family aur WhatsApp contacts ko bhejenge {city} me.", "hi-Latn"),
        ("PM Mudra loan Rs {amt} approve ho gaya hai applicant #{id} ka. Loan sanction letter release karne ke liye Rs 2,500 file charge transfer karein.", "hi-Latn"),
        ("Sirf Aadhaar aur PAN card par 5 minute me loan Rs {amt} seedhe {bank} me. Link par click karke apply karein https://easy-cash{id}.in", "hi-Latn"),
        ("Recovery agent notice: Loan file #{id} ka baki paisa Rs {amt} 1 ghante me pay karein warna police complaint darj hogi {city} me.", "hi-Latn"),
        ("Emergency loan chahiye? Bina kisi guarantee ke Rs {amt} lein. WhatsApp par documents bhejein officer {name} ko 98{id}", "hi-Latn"),
        ("Bajaj Finserv se Rs {amt} ka loan approve hua hai customer #{id}. Disbursement ke liye GST tax Rs 3,200 account me dalein.", "hi-Latn"),
        ("Loan defaulter alert: Court se non-bailable warrant issue ho raha hai unpaid EMI Rs {amt} ke liye file #{id}. Call karein 98{id}", "hi-Latn"),
        ("Instant loan app download karein aur 10 minute me Rs {amt} payein: https://fast-rupee-loan{id}.apk", "hi-Latn"),
        ("Aapke PAN card ending {id} par Rs {amt} pre-approved credit limit mili hai, withdraw karne ke liye link kholein https://credit-fast{id}.site", "hi-Latn"),
        ("Final warning loan #{id}: Shaam tak Rs {amt} settle karein warna aapke photo social media par post kar diye jayenge.", "hi-Latn"),
        # Devanagari Hindi
        ("बधाई हो! आपको बिना किसी सिबिल स्कोर या कागजी कार्रवाई के ₹{amt} का तत्काल व्यक्तिगत ऋण स्वीकृत किया गया है। फाइल #{id}। ऐप डाउनलोड करें: https://quick-loan{id}.apk", "hi-IN"),
        ("प्रधानमंत्री मुद्रा योजना: आवेदक #{id} को ₹{amt} का लोन मिला है। फाइल चार्ज और जीएसटी के रूप में ₹2,500 जमा करें ताकि राशि आपके {bank} खाते में भेजी जा सके।", "hi-IN"),
        ("अंतिम चेतावनी: लोन ऐप की बकाया राशि ₹{amt} तुरंत चुकाएं ऋण संख्या #{id} की, अन्यथा आपकी निजी तस्वीरें सभी संपर्कों को भेज दी जाएंगी।", "hi-IN"),
        ("कानूनी नोटिस: ऋण राशि ₹{amt} का भुगतान न करने पर {city} में आपके विरुद्ध पुलिस में गैर-जमानती वारंट जारी हो रहा है। समझौता करने के लिए कॉल करें।", "hi-IN"),
        ("केवल आधार कार्ड पर 5 मिनट में ₹{amt} का लोन सीधे अपने {bank} खाते में प्राप्त करें। संदर्भ #{id}। आज ही आवेदन करें: https://instant-loan{id}.in", "hi-IN"),
        ("ऋण स्वीकृति पत्र: आवेदक {name} का ₹{amt} का ऋण पास हो गया है। एनओसी शुल्क ₹1,800 का भुगतान करके चेक प्राप्त करें।", "hi-IN"),
        ("आपातकालीन नकद ऋण: 0% ब्याज दर पर ₹{amt} तक का ऋण तुरंत प्राप्त करें। {city} के ग्राहक तुरंत संपर्क करें: 98{id}", "hi-IN"),
        ("बजाज फाइनेंस लोन: दिवाली ऑफर के तहत खाता #{id} पर ₹{amt} का प्री-अप्रूव्ड लोन स्वीकृत। दस्तावेज शुल्क ट्रांसफर करके राशि प्राप्त करें।", "hi-IN"),
        ("रिकवरी टीम सूचना: यदि 2 घंटे में लोन संख्या #{id} की किश्त ₹{amt} जमा नहीं की गई तो रिकवरी एजेंट आपके {city} आवास पर पहुंचेंगे।", "hi-IN"),
        ("विद्यार्थी ऋण: छात्र #{id} को बिना किसी गारंटी के पढ़ाई के लिए ₹{amt} का लोन। फॉर्म भरने के लिए यहां जाएं: https://student-credit{id}.site", "hi-IN"),
        ("तत्काल गोल्ड लोन: बिना सोना गिरवी रखे ₹{amt} सीधे बैंक में पाएं। ऐप इंस्टॉल करें: https://gold-loan-app{id}.apk", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 6. JOB OFFER SCAM
    # ─────────────────────────────────────────────────────────────────────────
    "job_offer_scam": [
        # English
        ("Part time job opportunity: Earn Rs 2,500 to Rs {amt} daily from home by liking YouTube videos and rating Google Maps. Contact HR {name} on Telegram @EarnDaily{id}", "en-IN"),
        ("Amazon Hiring: Work From Home data entry jobs in {city}. Daily payout Rs 3,000. No experience needed. Join our official WhatsApp group #{id}: https://chat.whatsapp.com/Job{id}", "en-IN"),
        ("Earn passive income! Subscribe to 5 YouTube channels and get Rs 150 per channel. Deposit Rs 1,000 VIP fee to withdraw your earnings of Rs {amt}.", "en-IN"),
        ("Hotel review work from home job: Earn Rs 800 per hotel review on TripAdvisor in {city}. 15 tasks daily. Register today on Telegram: @ReviewJob{id}", "en-IN"),
        ("Flipkart product rating assistant needed for hub #{id}. Daily income Rs 4,000. Pay registration fee Rs 499 (refundable) to receive starter kit.", "en-IN"),
        ("Global movie rating platform: Watch 3 movie trailers and get paid Rs 1,200. Register on our portal for applicant #{id}: https://task-earnings{id}.com", "en-IN"),
        ("Part-time freelance recruiter job: 2 hours work daily, earn up to Rs {amt} per month. Message HR manager {name} on WhatsApp at 98{id}", "en-IN"),
        ("Congratulations! Your resume #{id} was shortlisted for Data Analyst (Remote). Pay Rs 1,200 for onboarding exam fee at https://career-test{id}.in", "en-IN"),
        ("Telegram task job: Complete 10 crypto rating tasks, earn Rs {amt}. To unlock task 11, recharge your account with Rs 5,000.", "en-IN"),
        ("International translation project #{id}: Translate 5 English pages to Hindi, earn Rs {amt}. Deposit refundable security money to start.", "en-IN"),
        ("Google Maps Local Guide project in {city}: Give 5-star ratings to clinics and shops. Rs 200 per rating. Contact Telegram mentor @TaskGuide{id}", "en-IN"),
        ("Work from home SMS sending job: Send 100 SMS daily from your mobile #{id} and earn Rs 3,500. Pay software activation fee Rs 750.", "en-IN"),
        ("Instagram influencer agency hiring: Like and comment on fashion posts. Daily payout Rs 2,000. WhatsApp your resume to {name} at 97{id}", "en-IN"),
        ("TCS Off-Campus Remote Selection: Sanctioned salary Rs {amt}/month for candidate #{id}. Pay laptop security deposit Rs 4,500 to dispatch joining letter.", "en-IN"),
        ("Proofreading work: Earn Rs 50 per page. 100 pages provided per week. Deposit Rs 1,500 material security fee for project #{id} to start.", "en-IN"),
        ("Netflix subtitle testing job: Watch web series and find typos. Rs 4,000 per episode. Register candidate #{id} now: https://netflix-careers{id}.site", "en-IN"),
        ("Earn Rs {amt} weekly by doing simple copy paste tasks on mobile. Instant withdrawal. Join Telegram group @CopyPasteWork{id}", "en-IN"),
        ("Railway Recruitment Board: Candidate #{id} selected for Junior Clerk post. Transfer document verification fee Rs 2,800 to HR officer {name}.", "en-IN"),
        ("Crypto rating assistant: Rate 5 exchange coins, get Rs {amt}. To withdraw funds, deposit tier-2 VIP upgrade charge Rs 6,000.", "en-IN"),
        ("Survey filling job: Fill 10 customer feedback forms and receive Rs 1,500 directly in {app}. Sign up at https://easy-survey{id}.online", "en-IN"),
        # Hinglish
        ("Part time work from home: Daily YouTube videos like karein aur Google Maps review karke Rs 2,500 se Rs {amt} kamayein. Contact on Telegram @WorkDaily{id}", "hi-Latn"),
        ("Amazon WFH hiring in {city}: Ghar baithe data entry job. Daily payout Rs 3,000. Registration fee Rs 499 refundable hai. Join group #{id}.", "hi-Latn"),
        ("Ghar baithe kamayein! YouTube channel subscribe karne par Rs 150 per channel. Payout Rs {amt} nikalne ke liye Rs 1,000 VIP recharge karein.", "hi-Latn"),
        ("Telegram task job: 10 hotel reviews likhein aur Rs {amt} kamayein. Withdraw karne ke liye security deposit Rs 3,000 jama karein account #{id} me.", "hi-Latn"),
        ("Flipkart product rating job: Roz 2 ghante mobile par kaam karein aur Rs {amt} mahina kamayein. WhatsApp HR {name} at 98{id}", "hi-Latn"),
        ("Resume #{id} shortlist hua hai remote back office job ke liye. Joining letter lene ke liye onboarding exam fee Rs 1,200 pay karein.", "hi-Latn"),
        ("Instagram par reels like karke roz Rs 2,000 kamayein. Free registration nahi hai, starter package Rs 650 ka hai ID #{id}.", "hi-Latn"),
        ("Crypto task complete karne ke baad Rs {amt} account me locked hain. Unlock karne ke liye tier-3 VIP fee Rs 5,000 transfer karein.", "hi-Latn"),
        ("Mobile typing job: 50 page type karein aur Rs {amt} payein project #{id} me. Kaam shuru karne ke liye security money transfer karein.", "hi-Latn"),
        ("Google rating task in {city}: Shop rating dene par Rs 200 har rating ka. Join karein Telegram channel @DailyRating{id}", "hi-Latn"),
        ("TCS me work from home job mili hai candidate #{id}. Company laptop lene ke liye courier charges Rs 3,500 pay karein.", "hi-Latn"),
        ("Copy paste job: Mobile se 2 ghante kaam karein aur daily Rs 1,500 apne {app} wallet me receive karein. Ref #{id}.", "hi-Latn"),
        # Devanagari Hindi
        ("घर बैठे पार्ट टाइम काम: यूट्यूब वीडियो लाइक करके और {city} में गूगल मैप्स रिव्यू देकर रोजाना ₹2,500 से ₹{amt} कमाएं। संपर्क: @WorkDaily{id}", "hi-IN"),
        ("अमेज़न में घर से काम: डाटा एंट्री जॉब। दैनिक वेतन ₹3,000। कोई अनुभव जरूरी नहीं। हमारे व्हाट्सएप ग्रुप #{id} से जुड़ें: 98{id}", "hi-IN"),
        ("होटल रिव्यू कार्य: ट्रिपएडवाइजर पर प्रति होटल रिव्यू ₹800 कमाएं। काम शुरू करने के लिए वीआईपी पंजीकरण शुल्क ₹999 जमा करें। आईडी #{id}।", "hi-IN"),
        ("फ्लिपकार्ट रेटिंग सहायक: घर बैठे उत्पाद रेटिंग का काम करके ₹{amt} प्रति माह कमाएं। प्रारंभिक सुरक्षा राशि ₹499 रिफंडेबल है।", "hi-IN"),
        ("बधाई हो! आपका बायोडाटा #{id} डेटा एनालिस्ट पद के लिए चुना गया है। जॉइनिंग किट के लिए ₹1,200 का सत्यापन शुल्क जमा करें।", "hi-IN"),
        ("टेलीग्राम टास्क कार्य: 10 कार्य पूरे करें और ₹{amt} प्राप्त करें। कमाई निकालने के लिए अपने खाते #{id} में ₹3,000 का रिचार्ज करें।", "hi-IN"),
        ("अंतरराष्ट्रीय अनुवाद कार्य #{id}: अंग्रेजी से हिंदी में अनुवाद करके ₹{amt} कमाएं। सामग्री सुरक्षा राशि जमा करके काम शुरू करें।", "hi-IN"),
        ("इंस्टाग्राम रील लाइक जॉब: प्रतिदिन 2 घंटे काम करके ₹2,000 सीधे अपने {bank} खाते में पाएं। तुरंत संपर्क करें HR {name}।", "hi-IN"),
        ("टीसीएस वर्क फ्रॉम होम: अभ्यर्थी #{id} का चयन हो गया है। लैपटॉप और आईडी कार्ड कूरियर शुल्क ₹4,500 जमा करें।", "hi-IN"),
        ("टाइपिंग जॉब: मोबाइल पर प्रति पेज ₹100 कमाएं। सॉफ्टवेयर एक्टिवेशन फीस ₹750 का भुगतान करके आज ही काम शुरू करें। प्रोजेक्ट #{id}।", "hi-IN"),
        ("क्रिप्टो रेटिंग जॉब: कार्य पूरा होने पर कमाई ₹{amt} निकालने हेतु खाता #{id} अपग्रेड शुल्क ₹4,000 ट्रांसफर करें।", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 7. LOTTERY PRIZE
    # ─────────────────────────────────────────────────────────────────────────
    "lottery_prize": [
        # English
        ("Congratulations!! Your mobile number ending {id} has won Rs {amt} in KBC Jio Lucky Draw 2024. Contact KBC Manager {name} at 98{id} to claim.", "en-IN"),
        ("Lucky Draw Winner! You won a brand new Tata Safari car in Diwali Mega Contest for coupon #{id}. Pay RTO registration tax Rs 12,500 in {city} to dispatch vehicle.", "en-IN"),
        ("Dear Customer #{id}, you are selected for Amazon Prime Annual Lucky Prize of Rs {amt}. WhatsApp your {bank} passbook to 91{id} to receive cheque.", "en-IN"),
        ("Notice: You won Rs 25,00,000 in WhatsApp International Lottery for ticket #{id}. To claim prize money, contact London office via WhatsApp at +44{id}", "en-IN"),
        ("Congratulations! iPhone 15 Pro Max won in festive scratch contest #{id}! Pay delivery customs charges of Rs 1,499 at https://claim-iphone{id}.top", "en-IN"),
        ("Shoppers Stop Lucky Customer award: Winner #{id} won gold voucher worth Rs {amt}. Call manager {name} at 93{id} within 2 hours to redeem before expiry.", "en-IN"),
        ("Government Lottery Bureau: Your ticket number #{id} has won second prize of Rs {amt}. Send processing fee Rs 5,000 to officer {name} to claim.", "en-IN"),
        ("Surprise Gift! You have won an international flight ticket to Dubai + Rs {amt} spending cash for booking #{id}. Claim voucher at https://free-dubai-trip{id}.xyz", "en-IN"),
        ("Flipkart 10th Anniversary Lucky Winner #{id}: Claim cash prize Rs {amt} by verifying your Aadhaar and paying TDS tax at https://fk-lucky{id}.live", "en-IN"),
        ("Maruti Suzuki lucky draw: Congratulations on winning Baleno car for ticket #{id}. Contact regional dispatch officer in {city} at 96{id} with prize code #{id}.", "en-IN"),
        ("Coca-Cola Golden Can Contest: Coupon #{id} won cash reward of Rs {amt}. Contact clearance manager {name} at 98{id} with winning coupon code.", "en-IN"),
        ("Hero Motocorp festive reward: You won a Splendor Plus bike! Deposit insurance registration fee Rs 8,500 to ship bike to your address in {city}.", "en-IN"),
        ("Paytm Mega Jackpot Winner #{id}: Cash prize of Rs {amt} waiting in your name. Pay 1% govt TDS tax Rs 2,500 to release funds to {bank}.", "en-IN"),
        ("Google Pay Scratch Card Grand Prize: You won Rs {amt} on card #{id}. Click https://gpay-festive-jackpot{id}.site to deposit in bank account.", "en-IN"),
        ("Samsung Mega Contest: Winner #{id} of Galaxy S24 Ultra smartphone! Clear courier and GST charges Rs 1,999 at https://claim-samsung{id}.online", "en-IN"),
        ("Big Bazaar Shopping Bonanza: Customer #{id} won 10 gram gold coin! Call store manager {name} at 97{id} to collect your prize in {city}.", "en-IN"),
        ("Mahindra Thar Lucky Draw 2024: Your coupon #{id} won! Pay road tax Rs 18,000 to initiate transport from {city} showroom.", "en-IN"),
        ("International Charity Foundation: Selected for financial grant of Rs {amt} for applicant #{id}. Deposit file opening charges Rs 4,500 to wire funds.", "en-IN"),
        ("Tanishq Jewellery festive scratch card #{id}: Diamond necklace winner. Call helpline 91{id} to verify identity.", "en-IN"),
        ("Jio 8th Anniversary Contest: Claim cash prize Rs {amt} for number ending {id}. Send Aadhaar card and processing fee to claim department.", "en-IN"),
        # Hinglish
        ("Badhai ho!! Aapka mobile number ending {id} KBC Jio Lucky Draw me Rs {amt} jeet chuka hai. KBC Manager {name} se call karein 98{id}", "hi-Latn"),
        ("Lucky Draw Winner! Diwali contest coupon #{id} me aapne brand new Scorpio car jeeti hai. Gadi dispatch karne ke liye RTO tax Rs 12,500 pay karein {city} me.", "hi-Latn"),
        ("Amazon Lucky Customer award: Customer #{id} ne Rs {amt} ka cash prize jeeta hai. Bank passbook WhatsApp karein 91{id} par cheque lene ke liye.", "hi-Latn"),
        ("WhatsApp International Lottery me ticket #{id} par Rs 25 Lakh jeeta hai. London head office se contact karein +44{id} par claim karne ke liye.", "hi-Latn"),
        ("Badhai ho! Festive contest #{id} me iPhone 15 jeeta hai. Delivery customs charges Rs 1,499 link par pay karein https://claim-gift{id}.site", "hi-Latn"),
        ("Flipkart lucky draw: Rs {amt} ka cash prize lene ke liye winner #{id} 1% TDS tax Rs 2,500 pehle jama karein {bank} account me.", "hi-Latn"),
        ("Maruti Suzuki lucky draw: Congratulations on winning Baleno car coupon #{id}. RTO registration fee transfer karein car {city} me deliver karwane ke liye.", "hi-Latn"),
        ("Coca Cola lucky contest me aapka number #{id} select hua hai Rs {amt} ke liye. Manager {name} ko call karein claim karne ke liye.", "hi-Latn"),
        ("Hero bike lucky winner #{id}! Splendor bike dispatch karne ke liye insurance charge Rs 8,500 jama karein.", "hi-Latn"),
        ("Paytm jackpot me Rs {amt} jeet gaye hain customer #{id}. Cash account me transfer karne ke liye processing fee pay karein https://paytm-gift{id}.online", "hi-Latn"),
        ("Samsung Galaxy S24 jeetne par badhai ticket #{id}. Parcel release karwane ke liye GST charges Rs 1,999 submit karein.", "hi-Latn"),
        ("Mahindra Thar lucky draw me coupon #{id} ka naam nikla hai. {city} showroom se gadi dispatch karne ke liye tax transfer karein.", "hi-Latn"),
        # Devanagari Hindi
        ("बधाई हो!! आपके मोबाइल नंबर ending {id} ने केबीसी जियो लकी ड्रा में ₹{amt} जीते हैं। पुरस्कार राशि प्राप्त करने के लिए मैनेजर {name} से संपर्क करें: 98{id}", "hi-IN"),
        ("लकी ड्रा विजेता! आपने कूपन #{id} पर दिवाली मेगा प्रतियोगिता में नई टाटा सफारी कार जीती है। {city} में डिलीवरी हेतु आरटीओ टैक्स ₹12,500 जमा करें।", "hi-IN"),
        ("अमेज़न प्राइम वार्षिक लकी ड्रा: ग्राहक #{id} ₹{amt} के नकद पुरस्कार के लिए चुने गए हैं। चेक प्राप्त करने के लिए अपनी {bank} पासबुक व्हाट्सएप करें: 91{id}", "hi-IN"),
        ("व्हाट्सएप अंतरराष्ट्रीय लॉटरी: टिकट #{id} पर आपने ₹25,00,000 का मेगा जैकपॉट जीता है। इनाम का दावा करने के लिए लंदन कार्यालय से संपर्क करें।", "hi-IN"),
        ("बधाई हो! आपने कूपन #{id} पर iPhone 15 Pro Max जीता है! पार्सल सीमा शुल्क ₹1,499 का भुगतान करें: https://claim-iphone{id}.top", "hi-IN"),
        ("फ्लिपकार्ट 10वीं वर्षगांठ: विजेता #{id} ने ₹{amt} का नकद पुरस्कार जीता है। सरकारी टीडीएस टैक्स ₹2,500 जमा करके राशि बैंक में ट्रांसफर करवाएं।", "hi-IN"),
        ("मारुति सुजुकी लकी ड्रा: कूपन #{id} पर बलेनो कार जीतने पर बधाई। वाहन {city} में भेजने के लिए रोड टैक्स तुरंत ट्रांसफर करें।", "hi-IN"),
        ("हीरो मोटोकॉर्प लकी विनर #{id}: आपने स्प्लेंडर प्लस बाइक जीती है! शोरूम से डिलीवरी हेतु बीमा शुल्क ₹8,500 जमा करें।", "hi-IN"),
        ("पेटीएम जैकपॉट: ग्राहक #{id} के नाम पर ₹{amt} का इनाम निकला है। फाइल चार्ज ₹2,000 जमा करके अपने {bank} खाते में सीधे ट्रांसफर लें।", "hi-IN"),
        ("सैमसंग मेगा प्रतियोगिता: कूपन #{id} गैलेक्सी स्मार्टफोन विजेता! कूरियर और जीएसटी शुल्क ₹1,999 का भुगतान करके पार्सल डिस्पैच करवाएं।", "hi-IN"),
        ("महिंद्रा थार लकी कूपन: आपका कूपन नंबर #{id} प्रथम पुरस्कार के लिए चुना गया है। {city} में रजिस्ट्रेशन राशि जमा करके गाड़ी क्लेम करें।", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 8. SIM SWAP FRAUD
    # ─────────────────────────────────────────────────────────────────────────
    "sim_swap": [
        # English
        ("Dear Airtel Customer #{id}, your SIM card will be upgraded to 5G Ultra automatically. Send SMS 'SIM {id}' to 121 to activate within 2 hours.", "en-IN"),
        ("Jio Alert for number {id}: To avoid 4G SIM deactivation, share the 20-digit SIM number printed on your SIM card or scan the eSIM QR sent on your email.", "en-IN"),
        ("Vodafone-Idea Notice: 4G SIM service closing in {city}. Reply 'PORT 98{id}' to upgrade to high-speed 5G or service will be cut for mobile #{id}.", "en-IN"),
        ("Dear user, your duplicate eSIM request #ES{id} has been submitted for phone {id}. If you did not request this, call 198 immediately or SIM will disconnect.", "en-IN"),
        ("BSNL Alert: Your mobile KYC verification failed for number #{id}. Your number will be permanently disconnected unless you verify 5G SIM with executive {name}.", "en-IN"),
        ("Airtel 5G Welcome Offer for {id}: Free 50GB data + 5G SIM card replacement. Forward the 1900 porting confirmation code to our executive {name}.", "en-IN"),
        ("Telecom Regulatory Notice: Upgrade to mandatory 5G biometric SIM card today for number #{id}. Share the activation OTP received from telecom operator.", "en-IN"),
        ("Jio e-SIM setup for mobile #{id}: Scan the attached barcode on another phone and accept profile download to complete SIM upgrade.", "en-IN"),
        ("Customer notice: Your SIM replacement request for number ending {id} is in progress in {city}. SMS 'YES' to 121 to confirm physical swap.", "en-IN"),
        ("VI 5G Upgrade: To prevent mobile outgoing call block on number #{id}, share your 19-digit ICCID number with telecom agent {name}.", "en-IN"),
        ("Telecom department advisory for {city}: Unverified SIM card #{id} detected. Send 'UPG {id}' to 59059 within 1 hour to retain mobile number.", "en-IN"),
        ("Airtel eSIM conversion initiated for subscriber #{id}. Forward the confirmation SMS received from 121 to continue network connectivity.", "en-IN"),
        ("Warning: Your phone number ending {id} is being transferred to a new SIM card. If unauthorized, dial 198 and press 3 immediately.", "en-IN"),
        ("Jio True 5G Activation for number #{id}: Send SMS 'SIMREQ {id}' to 199 to claim free unlimited 5G data package in {city}.", "en-IN"),
        ("Important: Telecom identity re-verification pending for connection #{id}. Share the 4-digit port validation code with support officer {name}.", "en-IN"),
        ("BSNL 5G SIM Doorstep Delivery in {city}: Confirm your eSIM barcode profile for account #{id} to activate high-speed connection.", "en-IN"),
        # Hinglish
        ("Dear Airtel customer, aapka 4G SIM ending {id} band hone wala hai. 5G me upgrade karne ke liye SMS karein 'SIM {id}' to 121 turant.", "hi-Latn"),
        ("Jio Alert for number {id}: 4G SIM deactivation se bachne ke liye SIM ke piche likha 20-digit number share karein ya eSIM QR scan karein.", "hi-Latn"),
        ("Vodafone-Idea {city}: Aapke area me 4G band ho raha hai. High speed 5G ke liye reply karein 'PORT 98{id}' 1900 par mobile #{id} se.", "hi-Latn"),
        ("Aapka duplicate eSIM request #ES{id} mila hai number {id} par. Agar aapne nahi kiya to turant call karein warna SIM 2 ghante me band ho jayega.", "hi-Latn"),
        ("Airtel 5G offer for {id}: Free 50GB data pane ke liye 1900 se aaya hua porting confirmation SMS executive {name} ko forward karein.", "hi-Latn"),
        ("Telecom KYC update for number #{id}: SIM card block hone se bachane ke liye telecom company se aaya hua activation OTP batayein.", "hi-Latn"),
        ("Jio eSIM setup mobile #{id}: Email par aaya barcode doosre phone se scan karein taaki aapka network 5G me switch ho sake.", "hi-Latn"),
        ("VI customer in {city}: SIM swap request approve karne ke liye 121 par 'CONFIRM {id}' bhej kar executive {name} ko batayein.", "hi-Latn"),
        ("Aapka number ending {id} nayi SIM par transfer kiya ja raha hai. Agar aapne nahi kiya to turant 198 par call karein.", "hi-Latn"),
        ("BSNL 5G SIM activation for #{id}: Number chalu rakhne ke liye 59059 par 'UPG {id}' send karein turant.", "hi-Latn"),
        ("SIM card KYC fail ho gaya hai number {id} ka. 24 ghante me number band hoga agar executive ko verification code nahi diya.", "hi-Latn"),
        # Devanagari Hindi
        ("प्रिय एयरटेल ग्राहक #{id}, आपका सिम कार्ड स्वतः 5G में अपग्रेड किया जाएगा। 2 घंटे में सक्रिय करने के लिए 121 पर 'SIM {id}' लिखकर भेजें।", "hi-IN"),
        ("जियो चेतावनी नंबर {id}: सिम ब्लॉक होने से बचाने के लिए अपने सिम कार्ड पर छपा 20-अंकीय नंबर साझा करें अथवा ईमेल पर आया eSIM QR कोड स्कैन करें।", "hi-IN"),
        ("वोडाफोन-आइडिया {city}: आपके क्षेत्र में 4G सेवाएं बंद की जा रही हैं। हाई-स्पीड 5G पर अपग्रेड करने हेतु 1900 पर 'PORT 98{id}' भेजें मोबाइल #{id} से।", "hi-IN"),
        ("प्रिय उपभोक्ता #{id}, आपके नंबर के लिए डुप्लीकेट ई-सिम #ES{id} का अनुरोध प्राप्त हुआ है। यदि आपने यह नहीं किया है, तो तुरंत 198 पर कॉल करें।", "hi-IN"),
        ("एयरटेल 5G स्वागत ऑफर नंबर {id}: 50GB मुफ्त डेटा पाने के लिए 1900 से आया पोर्टिंग पुष्टिकरण कोड हमारे अधिकारी {name} को फॉरवर्ड करें।", "hi-IN"),
        ("दूरसंचार विभाग नोटिस: सिम कार्ड #{id} का बायोमेट्रिक सत्यापन लंबित है। सिम बंद होने से बचाने के लिए प्राप्त एक्टिवेशन ओटीपी साझा करें।", "hi-IN"),
        ("जियो ई-सिम सेटअप मोबाइल #{id}: दूसरे फोन पर ईमेल से आया बारकोड स्कैन करें और प्रोफाइल डाउनलोड स्वीकार करके सिम अपग्रेड पूरा करें।", "hi-IN"),
        ("महत्वपूर्ण: आपके नंबर ending {id} को नए सिम कार्ड पर ट्रांसफर किया जा रहा है। यदि यह अनधिकृत है, तो तुरंत 198 डायल करें।", "hi-IN"),
        ("बीएसएनएल 5G एक्टिवेशन {city}: अपना नंबर #{id} चालू रखने के लिए 1 घंटे के अंदर 59059 पर 'UPG {id}' लिखकर भेजें।", "hi-IN"),
        ("टेलीकॉम अलर्ट: आपकी सिम कार्ड #{id} की केवाईसी अधूरी है। 24 घंटे में नंबर बंद होने से बचाने हेतु अधिकारी {name} से सत्यापन कराएं।", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 9. INVESTMENT / CRYPTO SCAM
    # ─────────────────────────────────────────────────────────────────────────
    "investment_scam": [
        # English
        ("Guaranteed 5% daily return on Bitcoin and USDT! Join our VIP Telegram trading channel: @CryptoWealth{id}. 100% risk free with mentor {name}.", "en-IN"),
        ("Earn Rs {amt} daily from stock market with zero loss guarantee in {city}. SEBI registered analyst tips. Join WhatsApp group: https://chat.whatsapp.com/Trade{id}", "en-IN"),
        ("Double your money in 7 days! Invest in our government certified renewable energy green bond for project #{id}. Minimum investment Rs 5,000.", "en-IN"),
        ("High yield arbitrage platform: Deposit Rs {amt} and get Rs {amt_double} back in 48 hours directly into {bank} account. Sign up https://crypto-rich{id}.vip", "en-IN"),
        ("Institutional pre-IPO allotment: Buy Tata Technologies shares at 50% discount before market listing. Limited quota for applicant #{id}: https://pre-ipo-shares{id}.in", "en-IN"),
        ("Forex automatic trading bot: 300% monthly profit guaranteed. Invest Rs {amt} today in account #{id}. Managed by top Wall Street traders.", "en-IN"),
        ("Gold trading scheme in {city}: Deposit money in digital gold pool #{id} and earn 2% interest per day. Withdraw anytime. Register: https://gold-growth{id}.top", "en-IN"),
        ("Private equity syndicate: High net worth investment opportunity with guaranteed 25% quarterly dividends on ticket #{id}. Minimum ticket Rs 25,000.", "en-IN"),
        ("VIP stock pump group: Buy recommended penny stock #{id} at 9:15 AM tomorrow for guaranteed 20% upper circuit profit. Join group now with trader {name}.", "en-IN"),
        ("Binary options signals with 98% accuracy. Earn Rs {amt} per hour trading currency pairs. WhatsApp mentor {name} at 99{id}", "en-IN"),
        ("Bumper return! Invest Rs {amt} in solar energy project #{id} and get daily return Rs 600. Direct payout in {bank} account.", "en-IN"),
        ("Join Angel One VIP premium group. Guaranteed 100% jackpot call tomorrow morning for member #{id}. Register: https://angel-vip-trade{id}.site", "en-IN"),
        ("Exclusive AI trading algorithm generates 15% weekly compounding profit on Binance for user #{id}. Deposit USDT to start automated trades.", "en-IN"),
        ("Government approved infrastructure fund: Invest Rs {amt} in scheme #{id} and receive guaranteed monthly pension of Rs 15,000 for lifetime.", "en-IN"),
        ("Stock market insider leaked tips: Buy breakout options contracts with 500% ROI guarantee on strike #{id}. Join secret channel: @MarketJackpot{id}", "en-IN"),
        ("Crowdfunding real estate platform: Buy fractional commercial property in {city} for Rs 10,000 and earn 30% annualized rental returns on unit #{id}.", "en-IN"),
        ("Crypto staking pool: Stake Ethereum in pool #{id} and earn 1.5% daily rewards with instant liquidity withdrawal. Visit https://eth-stake-pool{id}.org", "en-IN"),
        ("Hedge fund private pool #{id}: Guaranteed capital protection with 50% annual return. Minimum investment Rs {amt}.", "en-IN"),
        ("Day trading masterclass + VIP signals: Recover all your past trading losses within 14 days in {city}. WhatsApp our trader {name} at 98{id}", "en-IN"),
        ("Automated copy trading: Copy trades of billionaire investor {name} and make Rs {amt} every single day without effort on account #{id}.", "en-IN"),
        # Hinglish
        ("Guaranteed 5% daily return on Bitcoin and USDT! Hamara VIP Telegram trading channel join karein: @CryptoWealth{id}. 100% loss free with mentor {name}.", "hi-Latn"),
        ("Stock market me zero loss guarantee ke sath rozana Rs {amt} kamayein {city} me. SEBI registered analyst tips WhatsApp group join karein: link #{id}.", "hi-Latn"),
        ("7 din me paisa double! Government certified solar project #{id} me invest karein. Minimum investment Rs 5,000.", "hi-Latn"),
        ("Deposit karein Rs {amt} aur payein Rs {amt_double} 48 ghante me direct {bank} account me. Register karein https://crypto-rich{id}.vip", "hi-Latn"),
        ("Pre-IPO shares 50% discount par khareedein NSE listing se pehle for client #{id}. Limited quota: https://pre-ipo-deal{id}.in", "hi-Latn"),
        ("Forex trading bot se 300% monthly profit pakka account #{id} par. Aaj hi Rs {amt} invest karein aur ghar baithe daily profit kamayein.", "hi-Latn"),
        ("Digital gold pool scheme: Rozana 2% interest kamayein pool #{id} me, jab chahein withdraw karein. Register karein https://gold-grow{id}.top", "hi-Latn"),
        ("Kal subah 9:15 baje 20% upper circuit lagne wala penny stock buy karein. VIP insider group join karein @StockJackpot{id} with {name}.", "hi-Latn"),
        ("Share market me saara loss recover karein 10 din me {city} me. Guaranteed jackpot calls ke liye WhatsApp karein {name} ko 98{id}", "hi-Latn"),
        ("Solar plant project #{id} me Rs {amt} lagayein aur rozana Rs 700 {bank} me receive karein. Lifetime profit guaranteed.", "hi-Latn"),
        ("Binance USDT trading robot for account #{id}: 15% weekly profit automated system. Paisa lagayein aur tension free kamayein.", "hi-Latn"),
        ("Crypto staking platform par 2% daily return payein pool #{id} me. Minimum investment sirf Rs 1,000. Signup karein link par.", "hi-Latn"),
        # Devanagari Hindi
        ("क्रिप्टो और बिटकॉइन में दैनिक 5% गारंटीड मुनाफा! हमारे वीआईपी टेलीग्राम चैनल से जुड़ें: @CryptoWealth{id}। मेंटॉर {name} के साथ 100% जोखिम मुक्त।", "hi-IN"),
        ("शेयर बाजार में रोजाना ₹{amt} कमाएं बिना किसी नुकसान की गारंटी के {city} में। हमारे सेबी पंजीकृत विश्लेषक के ग्रुप से जुड़ें: #{id}।", "hi-IN"),
        ("7 दिनों में पैसा दोगुना! सरकार द्वारा मान्यता प्राप्त ग्रीन एनर्जी बॉन्ड #{id} में निवेश करें। न्यूनतम निवेश ₹5,000।", "hi-IN"),
        ("उच्च लाभ आर्बिट्रेज प्लेटफॉर्म: ₹{amt} जमा करें और 48 घंटे में ₹{amt_double} सीधे {bank} खाते में पाएं: https://crypto-rich{id}.vip?ref={id}", "hi-IN"),
        ("संस्थागत प्री-आईपीओ शेयर 50% छूट पर खरीदें खाता #{id} पर। बाजार में लिस्टिंग से पहले भारी मुनाफा कमाने का मौका।", "hi-IN"),
        ("फॉरेक्स ऑटोमैटिक ट्रेडिंग बॉट: 300% मासिक लाभ की पूर्ण गारंटी। आज ही खाता #{id} में ₹{amt} का निवेश करें।", "hi-IN"),
        ("डिजिटल गोल्ड ट्रेडिंग योजना {city}: गोल्ड पूल #{id} में पैसा जमा करें और प्रति दिन 2% ब्याज अर्जित करें। कभी भी निकासी करें।", "hi-IN"),
        ("पेनी स्टॉक जैकपॉट कॉल: कल सुबह 20% अपर सर्किट लगने वाले शेयर की इनसाइडर जानकारी पाने के लिए टेलीग्राम चैनल @StockJackpot{id} से जुड़ें।", "hi-IN"),
        ("सोलर ऊर्जा परियोजना #{id} में ₹{amt} निवेश करें और दैनिक ₹700 की निश्चित आय सीधे खाते में प्राप्त करें।", "hi-IN"),
        ("शेयर बाजार में पुराना सारा घाटा 14 दिनों में पूरा करें। विशेषज्ञ {name} के वीआईपी प्रीमियम ग्रुप में तुरंत पंजीकरण करें: #{id}।", "hi-IN"),
        ("क्रिप्टो स्टेकिंग पूल #{id}: एथेरियम और यूएसडीटी स्टेक करें और 1.5% दैनिक रिटर्न प्राप्त करें। पंजीकरण करें: https://eth-pool{id}.org", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 10. VOICE PHISHING / DIGITAL ARREST
    # ─────────────────────────────────────────────────────────────────────────
    "voice_phishing": [
        # English
        ("Digital Arrest Notice: This is Inspector {name} from {city} Cyber Crime Branch. An illegal parcel #{id} containing narcotics was intercepted with your Aadhaar.", "en-IN"),
        ("CBI Headquarters New Delhi: An arrest warrant #{id} has been issued against you regarding money laundering case. Transfer Rs {amt} clearance bond immediately. Do not disconnect call.", "en-IN"),
        ("Calling from Telecom Department (TRAI) {city}: All mobile numbers linked to Aadhaar #{id} will be terminated within 2 hours due to illegal bulk SMS complaints.", "en-IN"),
        ("Customs Officer {name} at {city} Airport: A DHL courier parcel #{id} booked to Cambodia under your name contains 5 fake passports and contraband.", "en-IN"),
        ("Supreme Court of India Enforcement Directorate: Case #{id} filed. You are under continuous digital surveillance. Stay on video call until statement is recorded.", "en-IN"),
        ("Crime Branch Cyber Cell {city}: A complaint of financial fraud of Rs 85 Lakhs has been lodged against your {bank} account #{id}. Transfer bail bond Rs 50,000 to verify funds.", "en-IN"),
        ("Police Control Room 112: Your son {name} has been detained in hit-and-run case #{id} in {city}. Transfer Rs 30,000 immediately to settle case before media arrives.", "en-IN"),
        ("Income Tax Enforcement Wing: Tax evasion case #{id} detected. Digital arrest warrant issued by officer {name}. Remain on Skype call or police team will arrive at residence in {city}.", "en-IN"),
        ("Narcotics Control Bureau (NCB): 150 grams MDMA seized in courier #{id} addressed to you in {city}. Pay clearance deposit of Rs {amt} to verify your innocence.", "en-IN"),
        ("Indian Army Cantonment Procurement Officer {name}: Calling regarding order #{id} in {city}. We will transfer advance via army digital portal, stay on call.", "en-IN"),
        ("Cyber Crime Inspector {name}: Aadhaar number #{id} linked to illegal transactions in {bank}. Report on WhatsApp video call immediately.", "en-IN"),
        ("DCP {name} Cyber Crime Cell: Non-bailable warrant #{id} issued by Magistrate in {city}. Join emergency interrogation session via Skype now.", "en-IN"),
        ("FedEx Customs Desk: Package #FX{id} sent from {city} to Taiwan flagged for wildlife contraband. Police case transferred to Crime Branch officer {name}.", "en-IN"),
        ("National Investigation Agency (NIA): Anti-national transactions detected from your account #{id}. Keep camera turned on for confidential interrogation with officer {name}.", "en-IN"),
        ("Traffic Police Inspector {name}: Your vehicle #{id} was involved in a fatal accident in {city}. Pay Rs 25,000 on {app} right now to avoid immediate arrest.", "en-IN"),
        ("Reserve Bank of India Vigilance: Your {bank} accounts are being frozen under PMLA Act file #{id}. Transfer funds of Rs {amt} to RBI safety escrow account for verification.", "en-IN"),
        ("Delhi Police Special Cell: FIR #{id} registered against you for cyber extortion. Join official video room immediately with officer {name}.", "en-IN"),
        ("Postal Department Legal Cell {city}: Seized parcel #{id} contains 16 ATM cards and fake PAN. CBI team dispatched to your location.", "en-IN"),
        ("High Court Legal Notice: Contempt of court proceedings initiated for case #{id}. Pay fine of Rs {amt} before 5 PM to dismiss warrant.", "en-IN"),
        ("Maharashtra Anti-Terrorism Squad (ATS): Suspicious international wire transfer traced to your {bank} account #{id}. Cooperate in digital interrogation with officer {name}.", "en-IN"),
        # Hinglish
        ("Digital Arrest Warning: Main Inspector {name}, {city} Cyber Crime Branch se bol raha hoon. Aapke Aadhaar #{id} par parcel me narcotics baramad hui hai.", "hi-Latn"),
        ("CBI Headquarters New Delhi se call hai. Money laundering case #{id} me aapke khilaf arrest warrant jari hua hai, phone cut mat karna.", "hi-Latn"),
        ("TRAI Telecom Department {city}: Aapke Aadhaar #{id} par 9 illegal SIM chal rahe hain jinse fraud SMS bheje gaye. Sabhi number 2 ghante me band honge.", "hi-Latn"),
        ("Customs Officer {name} {city} Airport: Aapke naam se booked DHL parcel #{id} me fake passport aur MDMA drugs mili hai. Skype par video call connect karein.", "hi-Latn"),
        ("Police Control Room: Aapka beta {name} accident me pakda gaya hai {city} me. Case settle karne ke liye turant Rs 30,000 bhejein media aane se pehle.", "hi-Latn"),
        ("Crime Branch Cyber Cell: Aapke {bank} account #{id} se Rs 85 Lakhs ka illegal transaction hua hai. Verification ke liye bail bond Rs 50,000 transfer karein.", "hi-Latn"),
        ("Income Tax raid officer {name}: Aapke ghar police team bheji ja rahi hai tax evasion case #{id} me. Bachne ke liye Skype video interrogation par aayein.", "hi-Latn"),
        ("Narcotics Control Bureau: 150 gram MDMA parcel #{id} me aapka Aadhaar linked hai {city} me. Nirdosh saabit karne ke liye security deposit Rs {amt} bharein.", "hi-Latn"),
        ("Inspector {name}: Aapke account #{id} par non-bailable warrant nikla hai. WhatsApp video call par aakar apna statement darj karwayein.", "hi-Latn"),
        ("FedEx courier office {city}: Parcel #{id} me 5 illegal ATM card mile hain. Case cyber crime police ko hand over kiya ja raha hai.", "hi-Latn"),
        ("RBI Vigilance Team: Money laundering ke shak me aapke sabhi accounts freeze kiye ja rahe hain file #{id}. Safe account me Rs {amt} move karein.", "hi-Latn"),
        ("DCP {name} Crime Branch: Supreme Court ke order par aap digital surveillance me hain case #{id}. Camera off kiya to seedha arrest kiya jayega.", "hi-Latn"),
        # Devanagari Hindi
        ("डिजिटल अरेस्ट नोटिस: मैं {city} साइबर क्राइम सेल से इंस्पेक्टर {name} बोल रहा हूँ। आपके आधार #{id} से बुक पार्सल में नशीले पदार्थ पकड़े गए हैं।", "hi-IN"),
        ("सीबीआई मुख्यालय नई दिल्ली: मनी लॉन्ड्रिंग मामले #{id} में आपके नाम गैर-जमानती गिरफ्तारी वारंट जारी हुआ है। कॉल न काटें और तुरंत स्काइप पर आएं।", "hi-IN"),
        ("दूरसंचार विभाग (TRAI) {city}: आपके पहचान पत्र #{id} पर पंजीकृत सभी मोबाइल नंबर अवैध गतिविधियों के कारण अगले 2 घंटे में बंद कर दिए जाएंगे।", "hi-IN"),
        ("कस्टम विभाग {city} हवाई अड्डा: आपके नाम से भेजे जा रहे पार्सल #{id} में 5 फर्जी पासपोर्ट और मादक पदार्थ मिले हैं। तुरंत वीडियो कॉल पर बयान दें अधिकारी {name} को।", "hi-IN"),
        ("पुलिस नियंत्रण कक्ष {city}: आपका बेटा दुर्घटना मामले में हिरासत में लिया गया है। मामला रफा-दफा करने के लिए तुरंत ₹30,000 ट्रांसफर करें एफआईआर #{id} दर्ज होने से पहले।", "hi-IN"),
        ("क्राइम ब्रांच साइबर सेल: आपके {bank} खाते #{id} में ₹85 लाख के वित्तीय घोटाले की शिकायत दर्ज है। अपनी निर्दोषता साबित करने हेतु सुरक्षा राशि जमा करें।", "hi-IN"),
        ("नारकोटिक्स कंट्रोल ब्यूरो (NCB): आपके पार्सल #{id} से 150 ग्राम एमडीएमए ड्रग्स जब्त की गई है। गिरफ्तारी से बचने हेतु सत्यापन राशि ₹{amt} ट्रांसफर करें।", "hi-IN"),
        ("आयकर अन्वेषण विंग: कर चोरी का मामला #{id} दर्ज। गैर-जमानती डिजिटल अरेस्ट वारंट जारी। जांच पूरी होने तक स्काइप वीडियो कॉल चालू रखें इंस्पेक्टर {name} के साथ।", "hi-IN"),
        ("फेडएक्स कूरियर सुरक्षा विंग {city}: आपके आधार नंबर #{id} से जुड़े पार्सल में गैरकानूनी सामग्री पाई गई है। मामला सीबीआई को सौंप दिया गया है।", "hi-IN"),
        ("उच्चतम न्यायालय प्रवर्तन निदेशालय: आप 24 घंटे की डिजिटल निगरानी में हैं केस #{id} के तहत। कॉल काटने पर स्थानीय पुलिस आपके घर पहुंचेगी।", "hi-IN"),
        ("भारतीय रिज़र्व बैंक सतर्कता प्रकोष्ठ: आपके {bank} खाते #{id} संदिग्ध पाए गए हैं। धनराशि की सुरक्षा के लिए आरबीआई सत्यापन खाते में ₹{amt} ट्रांसफर करें।", "hi-IN"),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # 11. BENIGN (Legitimate Transactional & Everyday Messages)
    # ─────────────────────────────────────────────────────────────────────────
    "benign": [
        # English
        ("Dear Customer, your {bank} A/C ending in {id} is credited with Rs {amt} on {date} by UPI/P2A from {name}. Available balance: Rs {bal}.", "en-IN"),
        ("Your {bank} A/C {id} has been debited with Rs {amt} on {date} at Amazon India in {city}. Available balance: Rs {bal}. If not done by you, call 1800-{bank_slug}.", "en-IN"),
        ("Your OTP for login to Swiggy account is {otp}. Valid for 10 minutes for order #{id}. Please do not share this OTP with anyone, including delivery partners.", "en-IN"),
        ("Dear user, OTP for transaction of Rs {amt} on IRCTC using card ending {id} is {otp}. Never share OTP with anyone. - {bank}", "en-IN"),
        ("Your order #ORD{id} has been delivered by BlueDart in {city}. Thank you for shopping with Flipkart! Rate your delivery executive {name}.", "en-IN"),
        ("Zomato: Your food order from Haldiram is out for delivery in {city}. Delivery partner {name} is on his way for order #{id}. Track live in app.", "en-IN"),
        ("Dear Customer, electricity bill for consumer no {id} of Rs {amt} in {city} is due on {date}. Pay online through official portal bspscl.co.in", "en-IN"),
        ("Hi Mom, I reached the hostel in {city} safely. Will call you in the evening after classes finish. Love from {name}.", "en-IN"),
        ("Your monthly e-statement for {bank} Savings Account ending in {id} for month of August is ready. Password is your DOB.", "en-IN"),
        ("Dear Cardholder, statement for {bank} credit card ending {id} has been generated. Total amount due: Rs {amt}. Due date: {date}.", "en-IN"),
        ("Jio: 1.5GB daily high speed data quota exhausted for mobile {id}. Data speed reset at midnight. Recharge extra data via MyJio.", "en-IN"),
        ("Uber: Your trip of Rs {amt} in {city} with driver {name} has ended. Hope you had a pleasant ride! Receipt #{id} sent to email.", "en-IN"),
        ("Dear Customer, your Fixed Deposit #{id} of Rs {amt} with {bank} will mature on {date}. Visit {city} branch or internet banking to renew.", "en-IN"),
        ("Your Airtel broadband bill for account {id} in {city} is generated. Total due: Rs {amt}. Pay via Airtel Thanks app to avoid interruption.", "en-IN"),
        ("Dear SBI user, your request for Cheque Book dispatch for account #{id} has been accepted. Tracking no #CK{id}. Will arrive in 3 working days.", "en-IN"),
        ("Transaction successful: Rs {amt} paid to Mother Dairy in {city} via {app} on {date}. Ref: UPI/{id}.", "en-IN"),
        ("Dear Student #{id}, college fees payment receipt of Rs {amt} for semester {sem} has been generated. Download from student portal.", "en-IN"),
        ("Hi {name}, team sync scheduled at 4:30 PM today on Google Meet. Please review the quarterly metrics doc for project #{id} beforehand.", "en-IN"),
        ("Good morning sir, submitting the project documentation #{id} and code repository link for your review. Thanks, {name}.", "en-IN"),
        ("Let us catch up at the {city} library around 5 PM to discuss the machine learning assignment #{id}.", "en-IN"),
        ("Happy birthday {name}! Wishing you a fantastic year ahead filled with joy and success. See you in {city} soon.", "en-IN"),
        ("Salary credit: Rs {amt} has been credited to your salary account {id} for month of September. - {bank}", "en-IN"),
        ("IndiGo flight 6E-{id} from {city} to Mumbai is on time. Web check-in is now open. Boarding gate will open at 14:15 on {date}.", "en-IN"),
        ("BookMyShow: Booking confirmed for movie at PVR Cinema in {city}. Audi {sem}, Seats F12-F13. Booking ID #{id}. Show on {date}.", "en-IN"),
        ("Mutual fund SIP installment of Rs {amt} towards Nippon India Growth Fund executed successfully on {date} for folio #{id}.", "en-IN"),
        ("Delhi Metro Smart Card #{id} recharge of Rs {amt} successful. Tap your card at AVM machine to update balance.", "en-IN"),
        ("Bescom Electricity: Payment of Rs {amt} received for Account {id} on {date} in {city}. Thank you for timely payment.", "en-IN"),
        ("Aadhaar authentication successful for transaction of Rs {amt} at {bank} ATM in {city}. If not done by you, lock biometrics via mAadhaar.", "en-IN"),
        ("Apollo Pharmacy: Your medicine order #MED{id} is ready for pickup at Sector 14 branch in {city}.", "en-IN"),
        ("Blinkit: Order #{id} delivered in 8 minutes in {city}! Enjoy your fresh groceries. For feedback, rate us on app.", "en-IN"),
        # Hinglish
        ("Dear Customer, aapke {bank} account #{id} me Rs {amt} credit ho gaye hain on {date}. Available balance: Rs {bal}. Shukriya.", "hi-Latn"),
        ("Aapka {bank} account ending {id} se Rs {amt} debit ho gaya hai grocery store par in {city}. Agar aapne nahi kiya to customer care call karein.", "hi-Latn"),
        ("Swiggy: Haldiram se aapka order #{id} out for delivery hai. Delivery partner {name} raste me hai, live track karein.", "hi-Latn"),
        ("Aapka Swiggy order #{id} deliver ho gaya hai. Rate your delivery agent {name} in Swiggy app. Enjoy your meal in {city}!", "hi-Latn"),
        ("Mom main room par safely pahunch gaya hoon {city} me. Khana kha kar thodi der me phone karta hoon. - {name}", "hi-Latn"),
        ("Bhai project #{id} ki presentation ready hai. Google Drive link share kar di hai group me, dekh lena. - {name}", "hi-Latn"),
        ("Airtel data alert: Mobile #{id} ka 100% daily data khatam ho gaya hai. Speed 64Kbps ho gayi hai. 1GB add-on karein.", "hi-Latn"),
        ("Uber auto ride #{id} in {city} complete ho gayi. Driver {name} ko cash Rs {amt} pay karein ya UPI se pay karein.", "hi-Latn"),
        ("Zomato order #{id} deliver ho gaya. Khana kaisa laga? Review share karein app par.", "hi-Latn"),
        ("Happy Diwali {name}! Bhagwan kare ye saal aapke parivar ke liye dhero khushiya aur tarakki lekar aaye.", "hi-Latn"),
        ("Kal exam ke baad sab log {city} canteen me milenge notes discuss karne ke liye semester {sem} ke.", "hi-Latn"),
        ("Train ticket #{id} confirm ho gaya hai RAC se seat number 45 coach B2 mila hai on {date}.", "hi-Latn"),
        ("Flipkart delivery boy {name} bahar khada hai {city} me, parcel #{id} receive kar lo please.", "hi-Latn"),
        ("Electricity bill #{id} online pay kar diya hai {app} se Rs {amt}, receipt download kar li hai.", "hi-Latn"),
        ("Bhai kal subah 7 baje gym chalna hai in {city}, time par ready rehna. - {name}", "hi-Latn"),
        # Devanagari Hindi
        ("प्रिय ग्राहक, आपके {bank} खाते #{id} में दिनांक {date} को ₹{amt} जमा किए गए हैं। शेष राशि: ₹{bal}।", "hi-IN"),
        ("आपके खाते #{id} से ₹{amt} का भुगतान सफल रहा {city} में। शेष राशि: ₹{bal}। यदि यह लेनदेन आपने नहीं किया है, तो तुरंत बैंक को सूचित करें।", "hi-IN"),
        ("स्विगी लॉगिन हेतु आपका वन-टाइम पासवर्ड (OTP) {otp} है ऑर्डर #{id} के लिए। यह 10 मिनट के लिए मान्य है। किसी के साथ साझा न करें।", "hi-IN"),
        ("प्रिय उपभोक्ता, बिजली बिल संख्या {id} राशि ₹{amt} का भुगतान {city} में सफलतापूर्वक प्राप्त हुआ दिनांक {date} को। धन्यवाद।", "hi-IN"),
        ("नमस्ते माँ, मैं सुरक्षित छात्रावास {city} पहुँच गया हूँ। कक्षाएं समाप्त होने के बाद शाम को बात करता हूँ। - {name}", "hi-IN"),
        ("जोमैटो: आपका भोजन तैयार है और डिलीवरी पार्टनर {name} आपके पते के लिए निकल चुका है ऑर्डर #{id} लेकर।", "hi-IN"),
        ("फ्लिपकार्ट: आपका पार्सल #ORD{id} {city} में सफलतापूर्वक डिलीवर कर दिया गया है। खरीदारी के लिए धन्यवाद!", "hi-IN"),
        ("भारतीय स्टेट बैंक: आपकी चेक बुक आपके {city} पते पर भेज दी गई है। ट्रैकिंग संख्या #CK{id} है।", "hi-IN"),
        ("जन्मदिन की हार्दिक शुभकामनाएं {name}! ईश्वर आपको उत्तम स्वास्थ्य, दीर्घायु और सफलता प्रदान करें।", "hi-IN"),
        ("प्रिय छात्र #{id}, आगामी सेमेस्टर {sem} की परीक्षा समय सारणी कॉलेज पोर्टल पर अपलोड कर दी गई है। कृपया जांच लें।", "hi-IN"),
        ("उबर: {city} में आपकी ₹{amt} की यात्रा समाप्त हुई। ड्राइवर {name} को रेटिंग दें और रसीद #{id} ईमेल पर देखें।", "hi-IN"),
        ("आईआरसीटीसी: आपकी गाड़ी संख्या 12301 राजधानी एक्सप्रेस PNR #{id} समय पर है दिनांक {date} को। शुभ यात्रा!", "hi-IN"),
        ("म्युचुअल फंड: आपकी ₹{amt} की मासिक एसआईपी सफलतापूर्वक निष्पादित हो गई है फोलियो #{id} के लिए। एनएवी आवंटित कर दी गई है।", "hi-IN"),
        ("आधार प्रमाणीकरण: {city} में आपके आधार #{id} का उपयोग करके बैंक लेनदेन ₹{amt} सफलतापूर्वक पूरा किया गया।", "hi-IN"),
    ]
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper to Synthesize Realistic Variants with Rich Parameter Diversity
# ─────────────────────────────────────────────────────────────────────────────

def generate_variants(category: str, template: str, lang: str, count: int = 25) -> list[dict]:
    """Generates distinct, varied instances of a template with randomized parameters and varied prefixes."""
    variants = []
    seen = set()

    # Select appropriate prefixes based on language
    if lang == "hi-IN":
        prefix_pool = PREFIXES_HI_IN
    elif lang == "hi-Latn":
        prefix_pool = PREFIXES_HI_LATN
    else:
        prefix_pool = PREFIXES_EN

    # Iterate with enough attempts to achieve desired variant count
    for _ in range(count * 8):
        if len(variants) >= count:
            break

        prefix = random.choice(prefix_pool)
        amt_val = random.choice(AMOUNTS)
        amt_str = f"{amt_val:,}"
        amt_double_str = f"{(amt_val * 2):,}"
        uid_str = str(random.randint(1000, 99999))
        otp_str = str(random.randint(100000, 999999))
        day = random.randint(1, 28)
        month = random.choice(DATES_MONTHS)
        year = random.choice([2024, 2025])
        date_str = f"{day:02d}-{month}-{year}"
        bal_val = random.randint(1200, 450000)
        bal_str = f"{bal_val:,}"
        bank_choice = random.choice(BANKS)
        bank_slug = bank_choice.lower().replace(" ", "")[:8]
        app_choice = random.choice(UPI_APPS)
        name_choice = random.choice(NAMES)
        city_choice = random.choice(CITIES)
        vpa_choice = random.choice(VPAS)
        sem_choice = str(random.choice([3, 4, 5, 6, 7, 8]))

        text = prefix + template
        text = text.replace("{amt}", amt_str)
        text = text.replace("{amt_double}", amt_double_str)
        text = text.replace("{id}", uid_str)
        text = text.replace("{otp}", otp_str)
        text = text.replace("{date}", date_str)
        text = text.replace("{bal}", bal_str)
        text = text.replace("{bank}", bank_choice)
        text = text.replace("{bank_slug}", bank_slug)
        text = text.replace("{app}", app_choice)
        text = text.replace("{name}", name_choice)
        text = text.replace("{city}", city_choice)
        text = text.replace("{vpa}", vpa_choice)
        text = text.replace("{sem}", sem_choice)

        cleaned = " ".join(text.split())
        if cleaned not in seen:
            seen.add(cleaned)
            variants.append({
                "text": cleaned,
                "category": category,
                "language": lang,
            })

    return variants


def build_full_dataset() -> pd.DataFrame:
    """Builds the complete multi-class dataset across all taxonomy categories."""
    records = []

    # Load taxonomy risk mapping
    taxonomy_df = pd.read_csv(DATA_DIR / "taxonomy.csv")
    risk_map = dict(zip(taxonomy_df["category"], taxonomy_df["risk_level"]))

    for category, template_list in TEMPLATES.items():
        risk_level = risk_map.get(category, "high" if category != "benign" else "safe")
        seen_texts = set()

        for template_text, lang in template_list:
            # Generate 25 diverse variants per template
            variants = generate_variants(category, template_text, lang, count=25)
            for var in variants:
                cleaned = var["text"]
                if cleaned not in seen_texts:
                    seen_texts.add(cleaned)
                    records.append({
                        "text": cleaned,
                        "category": category,
                        "risk_level": risk_level,
                        "language": var["language"],
                        "source_type": "curated_scam" if category != "benign" else "authentic_transaction",
                    })

    df = pd.DataFrame(records)
    # Deduplicate strictly on text
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)
    return df


def split_and_save_dataset(df: pd.DataFrame):
    """
    Performs stratified Train (70%), Validation (15%), and Test (15%) splits.
    Saves CSVs to data/splits/ and data/processed/ directories.
    """
    # First split: Train (70%) vs Temp (30%)
    train_df, temp_df = train_test_split(
        df,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=df["category"],
    )

    # Second split: Val (15%) and Test (15%) from Temp
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temp_df["category"],
    )

    # Save full processed dataset
    full_path = PROCESSED_DIR / "full_dataset.csv"
    df.to_csv(full_path, index=False)

    # Save splits
    train_path = SPLITS_DIR / "train.csv"
    val_path = SPLITS_DIR / "val.csv"
    test_path = SPLITS_DIR / "test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print("\n" + "=" * 65)
    print("FraudGuard AI — Heavily Expanded Dataset Generation Summary")
    print("=" * 65)
    print(f"Total Unique Samples:     {len(df)}")
    print(f"Train Set (70%):          {len(train_df)} samples")
    print(f"Validation Set (15%):     {len(val_df)} samples")
    print(f"Held-out Test Set (15%):  {len(test_df)} samples")
    print(f"Saved to:                 {SPLITS_DIR}")
    print("=" * 65)
    print("\nLanguage Distribution in Full Dataset:")
    print(df["language"].value_counts())
    print("\nPer-Category Distribution in Full Dataset:")
    print(df["category"].value_counts())
    print("\nPer-Category Distribution in Test Set:")
    print(test_df["category"].value_counts())
    print("=" * 65 + "\n")


if __name__ == "__main__":
    df = build_full_dataset()
    split_and_save_dataset(df)
