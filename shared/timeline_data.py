"""
Canonical timeline step templates, one per supported visa type.

This is the source of truth for which steps exist and in what order.
shared/timeline.py may annotate a step's detail text using retrieved,
confidence-gated context, but it never adds, removes, or reorders steps
beyond what's defined here.
"""

TIMELINE_TEMPLATES = {
    "f-1": [
        {"id": "i20", "title": "Receive your I-20 from the university", "icon": "ti-file-text",
         "default_detail": "Issued by your school's international student office once you accept admission.", "category": "school"},
        {"id": "sevis_fee", "title": "Pay the SEVIS I-901 fee", "icon": "ti-cash",
         "default_detail": "Paid online at fmjfee.com using the SEVIS ID from your I-20.", "category": "fees",
         "form_url": "https://www.fmjfee.com/", "form_name": "SEVIS I-901 Fee Payment"},
        {"id": "ds160", "title": "Complete the DS-160 form", "icon": "ti-file-text",
         "default_detail": "The online nonimmigrant visa application, submitted before your interview.", "category": "forms",
         "form_url": "https://ceac.state.gov/genniv/", "form_name": "DS-160 (online application)"},
        {"id": "schedule_interview", "title": "Schedule the visa interview", "icon": "ti-calendar-event",
         "default_detail": "Booked at the US embassy or consulate in your home country.", "category": "interview"},
        {"id": "financial_docs", "title": "Gather financial documents", "icon": "ti-cash",
         "default_detail": "Bank statements or a sponsor affidavit showing you can cover tuition and living costs.", "category": "documents"},
        {"id": "attend_interview", "title": "Attend the visa interview", "icon": "ti-users",
         "default_detail": "Bring your passport, I-20, DS-160 confirmation, and financial documents.", "category": "interview"},
        {"id": "visa_issued", "title": "Visa issued", "icon": "ti-plane-departure",
         "default_detail": "Once approved, you're ready to travel and begin your program.", "category": "travel"},
    ],
    "j-1": [
        {"id": "ds2019", "title": "Receive your DS-2019 from the program sponsor", "icon": "ti-file-text",
         "default_detail": "Issued by your exchange program sponsor once you're accepted.", "category": "school"},
        {"id": "sevis_fee", "title": "Pay the SEVIS I-901 fee", "icon": "ti-cash",
         "default_detail": "Paid online at fmjfee.com using the SEVIS ID from your DS-2019.", "category": "fees",
         "form_url": "https://www.fmjfee.com/", "form_name": "SEVIS I-901 Fee Payment"},
        {"id": "ds160", "title": "Complete the DS-160 form", "icon": "ti-file-text",
         "default_detail": "The online nonimmigrant visa application, submitted before your interview.", "category": "forms",
         "form_url": "https://ceac.state.gov/genniv/", "form_name": "DS-160 (online application)"},
        {"id": "schedule_interview", "title": "Schedule the visa interview", "icon": "ti-calendar-event",
         "default_detail": "Booked at the US embassy or consulate in your home country.", "category": "interview"},
        {"id": "financial_docs", "title": "Gather financial documents", "icon": "ti-cash",
         "default_detail": "Proof of funding from your program sponsor or personal/family resources.", "category": "documents"},
        {"id": "attend_interview", "title": "Attend the visa interview", "icon": "ti-users",
         "default_detail": "Bring your passport, DS-2019, DS-160 confirmation, and financial documents.", "category": "interview"},
        {"id": "visa_issued", "title": "Visa issued", "icon": "ti-plane-departure",
         "default_detail": "Once approved, you're ready to travel and begin your exchange program.", "category": "travel"},
    ],
    "m-1": [
        {"id": "i20", "title": "Receive your I-20 from the vocational school", "icon": "ti-file-text",
         "default_detail": "Issued by your school's international student office once you're accepted.", "category": "school"},
        {"id": "sevis_fee", "title": "Pay the SEVIS I-901 fee", "icon": "ti-cash",
         "default_detail": "Paid online at fmjfee.com using the SEVIS ID from your I-20.", "category": "fees",
         "form_url": "https://www.fmjfee.com/", "form_name": "SEVIS I-901 Fee Payment"},
        {"id": "ds160", "title": "Complete the DS-160 form", "icon": "ti-file-text",
         "default_detail": "The online nonimmigrant visa application, submitted before your interview.", "category": "forms",
         "form_url": "https://ceac.state.gov/genniv/", "form_name": "DS-160 (online application)"},
        {"id": "schedule_interview", "title": "Schedule the visa interview", "icon": "ti-calendar-event",
         "default_detail": "Booked at the US embassy or consulate in your home country.", "category": "interview"},
        {"id": "financial_docs", "title": "Gather financial documents", "icon": "ti-cash",
         "default_detail": "Bank statements or a sponsor affidavit showing you can cover full program costs.", "category": "documents"},
        {"id": "attend_interview", "title": "Attend the visa interview", "icon": "ti-users",
         "default_detail": "Bring your passport, I-20, DS-160 confirmation, and financial documents.", "category": "interview"},
        {"id": "visa_issued", "title": "Visa issued", "icon": "ti-plane-departure",
         "default_detail": "Once approved, you're ready to travel and begin your program.", "category": "travel"},
    ],
}

DEFAULT_VISA_TYPE = "f-1"
