"""Synthetic evaluation transcripts modelled on publicly documented
digital-arrest scam patterns (I4C/MHA advisories, news-reported cases).
All transcripts are written for this benchmark; none are real recordings.
"""

SCAM = [
    "I am calling from CBI Mumbai. A parcel in your name contains drugs. "
    "An FIR is registered against you and an arrest warrant will be issued "
    "today. This is confidential, do not tell anyone, stay on the call. "
    "To clear your name transfer the amount to an RBI safe account for "
    "verification of funds.",

    "मैं क्राइम ब्रांच से बोल रहा हूँ। आपका आधार मनी लॉन्ड्रिंग में लिंक है। "
    "यह गोपनीय मामला है, किसी को मत बताना। जांच के लिए पैसे ट्रांसफर करने होंगे तुरंत।",

    "This is TRAI. Your SIM was used in illegal items shipping and human "
    "trafficking case. You are under surveillance, keep camera on, video "
    "call for verification. Pay a refundable security deposit immediately "
    "or your account will be blocked.",

    "Sir I am from the cyber cell police. Your Aadhaar linked account is "
    "under investigation. Do not disclose this to your family. We will "
    "guide you to a safe account.",

    "This is FedEx customer care transferring you to Mumbai police. Drugs "
    "and fake passports were found in the parcel booked on your Aadhaar. "
    "You are under digital arrest. Remain on video, do not contact a lawyer. "
    "Share your screen so we can verify your net banking.",

    "Inspector calling from the crime branch. A case number has been filed "
    "against your account involved in money laundering. This is a national "
    "secret, tell no one. Break your fd and transfer the amount for audit "
    "of funds, refund after verification.",

    "I am an ED officer. Suspicious transactions in your account are linked "
    "to a criminal network. The arrest team dispatched will reach within 24 "
    "hours unless you cooperate. Stay on the call and transfer the amount "
    "to the government verification account.",

    "आपके नाम का पार्सल कस्टम्स में पकड़ा गया है, उसमें ड्रग्स हैं। एफआईआर दर्ज "
    "हो चुकी है। किसी को मत बताना, कैमरा चालू रखिए। सुरक्षित खाते में पैसे "
    "ट्रांसफर कीजिए वरना आज ही गिरफ्तारी होगी।",

    "मी मुंबई पोलीस मधून बोलतोय. तुमच्या नावावर अवैध पार्सल सापडले आहे, "
    "अटक वॉरंट निघाले आहे. कोणालाही सांगू नका. तुरंत पैसे ट्रांसफर करा.",

    "This is the income tax department with the supreme court order. Your "
    "pan and aadhaar misused for illegal shipment. Non-bailable warrant "
    "issued. Do not inform family. Install this app anydesk so the officer "
    "can verify your accounts, and keep the otp ready.",

    "Madam, customs office. A courier contains mdma booked with your identity. "
    "Under digital custody you must report every hour on video call. Any "
    "disclosure is a crime. Liquidate your mutual fund redemption and move "
    "it to the rbi account until your name is cleared.",

    "Hello, cyber crime branch. Your son is in our custody in a human "
    "trafficking case. Last warning: transfer the security deposit right now "
    "and do not tell anyone or he will be arrested today.",
]

BENIGN = [
    "Hello, this is the courier company. Your delivery is scheduled for "
    "tomorrow between 10 and 12. Please keep your phone reachable.",

    "Good morning, I am calling from your bank about your fixed deposit "
    "maturity next month. You can visit the branch anytime to renew it.",

    "Papa, I will reach home by 8. Please keep dinner ready and tell mummy "
    "I got the tickets booked.",

    "This is the electricity board. Your bill of Rs 2,340 is due on the "
    "15th. You can pay on the official website or at the office.",

    "Sir, this is the hospital front desk confirming your appointment with "
    "the cardiologist on Friday at 11 am. Please carry your old reports.",

    "Hello, I am calling from the school office. The parent teacher meeting "
    "is on Saturday morning. Kindly confirm your attendance.",

    "Namaste, your car insurance expires this month. If you wish to renew, "
    "you can do it on the official portal or at any branch at your convenience.",

    "Hi, this is the society office. The water supply will be off on Sunday "
    "for tank cleaning between 9 and 1. Please store water accordingly.",

    "Good afternoon, calling from the furniture store. Your sofa is ready "
    "for delivery. Which day of the week suits you?",

    "बेटा, कल शाम को मंदिर चलना है। समय से घर आ जाना और छाता लेते आना, बारिश हो सकती है।",

    "Hello sir, your job interview with our HR team is confirmed for Monday "
    "at 3 pm on the office address shared by email. Please carry your resume.",

    "This is your mobile operator. Your monthly plan was renewed successfully "
    "and is valid till the 28th. Thank you for being with us.",
]

AMBIGUOUS = [
    "Sir, your electricity connection will be disconnected immediately "
    "tonight unless payment is made right now.",

    "Madam, there is a parcel in your name held at the courier office "
    "due to an issue. Please call back on this number.",

    "This is your bank. Please share the otp we just sent to complete "
    "the verification.",

    "Hello, your kyc has expired. Update immediately or your account will "
    "be blocked by tonight.",

    "Sir, I am calling from the police station regarding a complaint. "
    "Please visit the station tomorrow with your documents.",

    "Your sim will be deactivated within 24 hours due to incomplete "
    "verification. Press 1 to speak to an executive.",

    "There is a legal notice issued in your name. Kindly arrange a lawyer "
    "and appear as required.",

    "आपका बिजली कनेक्शन तुरंत काटा जाएगा, अभी भुगतान करें।",
]
