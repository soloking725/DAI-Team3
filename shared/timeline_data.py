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
         "default_detail": "Booked at the US embassy or consulate in your home country — most posts use the State Department-contracted AIS/usvisa-info.com scheduling system, though a few use ustraveldocs.com instead.", "category": "interview",
         "form_url": "https://ais.usvisa-info.com/", "form_name": "Visa Appointment Scheduling (AIS/usvisa-info.com)",
         "static_detail_html": (
             "<p><strong>Where:</strong> the US embassy or consulate with jurisdiction over your place of residence — "
             "most applicants cannot choose a different post freely, though a few countries' posts allow it; check "
             "the specific post's website.</p>"
             "<p><strong>Rescheduling:</strong> done through the same scheduling system (AIS/usvisa-info.com or "
             "ustraveldocs.com) you booked through — look for a \"reschedule\" or \"manage appointment\" option after "
             "logging in with the same account. Most systems cap how many times you can reschedule and require a "
             "minimum notice period, so check your post's specific policy.</p>"
             "<p><strong>Country-specific quirks:</strong> appointment wait times, required extra local forms, and "
             "which scheduling system is used all vary by post — ask Vera in the chat for what's specific to your "
             "origin country, or check your embassy/consulate's own website.</p>"
         )},
        {"id": "financial_docs", "title": "Gather financial documents", "icon": "ti-cash",
         "default_detail": "Bank statements or a sponsor affidavit showing you can cover tuition and living costs.", "category": "documents",
         "static_detail_html": (
             "<p>Typical documents consular officers look for (confirm exactly what your post requires):</p>"
             "<ul>"
             "<li>Personal or parental bank statements covering at least one year of tuition and living costs</li>"
             "<li>A scholarship or assistantship award letter, if applicable</li>"
             "<li>An affidavit of support (Form I-134) if a sponsor other than you is funding the program</li>"
             "<li>Proof of the sponsor's income or assets (pay stubs, tax returns, business ownership documents)</li>"
             "<li>A letter explaining your relationship to the sponsor, if it's a relative or third party</li>"
             "</ul>"
             "<p>Documents in a language other than English are often expected to include a certified translation — "
             "check your specific post's instructions.</p>"
         )},
        {"id": "attend_interview", "title": "Attend the visa interview", "icon": "ti-users",
         "default_detail": "Bring your passport, I-20, DS-160 confirmation, and financial documents.", "category": "interview",
         "static_detail_html": (
             "<p><strong>Bring:</strong> valid passport, I-20 (signed), DS-160 confirmation page, SEVIS fee "
             "receipt, visa appointment confirmation, a passport-style photo (if not already uploaded with your "
             "DS-160), and your financial documents.</p>"
             "<p><strong>What happens:</strong> a brief in-person interview with a consular officer, usually a few "
             "minutes, covering your study plans, school choice, funding, and ties to your home country. Fingerprints "
             "are typically taken as part of the visit.</p>"
             "<p><strong>Outcome:</strong> officers may approve on the spot, place your case in administrative "
             "processing (sometimes called \"221(g)\"), which can take additional weeks, or deny the application. "
             "You'll be told which at the end of the interview.</p>"
         )},
        {"id": "after_interview", "title": "After the interview: track your passport and visa", "icon": "ti-clock",
         "default_detail": "If approved, your passport is returned with the visa stamped inside — usually by courier within a few business days, though this varies by post.", "category": "travel",
         "static_detail_html": (
             "<p>Most posts use a courier service to return your passport — you can typically track its status "
             "online using the tracking number or receipt given at your interview.</p>"
             "<p>If your case was placed in administrative processing (\"221(g)\"), there's no fixed timeline — "
             "some resolve in days, others take weeks to months. Contact the embassy or consulate directly (not "
             "USCIS) for a status check, using the instructions on the 221(g) notice you were given.</p>"
             "<p>Once you have your passport back with the visa issued, double check the visa's validity dates, "
             "number of entries, and that your name/passport number are correct before you travel.</p>"
         )},
        {"id": "visa_issued", "title": "Visa issued", "icon": "ti-plane-departure",
         "default_detail": "Once approved, you're ready to travel and begin your program.", "category": "travel"},
    ],
}

DEFAULT_VISA_TYPE = "f-1"
