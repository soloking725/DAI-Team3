"""
Static content ingestion for student visa RAG database.

Populates ChromaDB with accurate, sourced information about F-1, J-1, and M-1
student visas. Content is derived from official US government sources and
structured for effective semantic retrieval.

Usage:
    python ingest_static.py
"""

import os
import datetime
from sentence_transformers import SentenceTransformer
import chromadb

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "student_visa_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def store_in_chroma(chunks, metadata_template):
    """Store chunks in ChromaDB with metadata."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # Remove old chunks for this specific document (URL + title combo)
    try:
        existing = collection.get(where={"doc_key": metadata_template["doc_key"]})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    for i, chunk in enumerate(chunks):
        doc_id = f"{metadata_template['doc_key']}_{i}"
        meta = metadata_template.copy()
        meta["source_url"] = metadata_template["url"]
        meta["chunk_index"] = i
        meta["section"] = f"Chunk {i + 1}"
        meta["scraped_at"] = datetime.datetime.now().isoformat()

        # visa_type is stored as a "F-1|J-1"-style string (see metadata_template
        # below) since Chroma metadata values must be scalar. Derive per-type
        # boolean flags from it so shared/retrieval.py can apply a real where
        # filter instead of just concatenating visa_type into the query.
        visa_types = [v.strip().lower() for v in meta.get("visa_type", "").split("|") if v.strip()]
        for vt in ("f-1", "j-1", "m-1", "h-1b"):
            meta[f"is_{vt.replace('-', '')}"] = vt in visa_types
        meta.setdefault("country", "US")  # destination-side content is about entering the US
        meta.setdefault("origin_country", "")  # set for content specific to a country of origin
        meta.setdefault("category", "")  # e.g. "extenuating_circumstances"

        collection.upsert(
            ids=[doc_id],
            documents=[chunk],
            metadatas=[meta],
        )


# -------------------------------------------------------
# Static content (sourced from official government pages)
# -------------------------------------------------------

# Each entry has: text, url, title, agency, visa_type tags
STATIC_DOCUMENTS = [
    # ---- F-1 Student Visa ----
    {
        "text": """F-1 Student Visa Overview

The F-1 nonimmigrant visa category allows students to study at a US college, university, seminary, conservatory, academic high school, elementary school, or other educational institution, including language training programs. The F-1 visa is classified under section 101(a)(15)(F) of the Immigration and Nationality Act. It is the most common visa for international students pursuing academic degrees in the United States.

To qualify for an F-1 visa, a student must be enrolled in a program that requires full-time study in English or have enrolled in sufficient English courses to acquire proficiency. The student must be able to show evidence of acceptance by a Student and Exchange Visitor Program (SEVP)-approved school. The student must demonstrate sufficient funds to cover tuition and living expenses without engaging in unauthorized employment. The student must maintain a valid foreign residence that they intend to occupy upon temporary stay in the US.

Source: US Department of State, travel.state.gov""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "State Department - F-1 Student Visa",
        "agency": "State Department",
        "visa_type": ["F-1"],
    },
    {
        "text": """F-1 Visa Application Documents

The following documents are required for an F-1 visa application and interview:

Form I-20, Certificate of Eligibility for Nonimmigrant Student Status, issued by an SEVP-approved school. This form confirms the student has been accepted and has met financial requirements.

Valid passport that must be valid for at least 6 months beyond the intended period of stay in the US. If the passport expires within 6 months, the student should renew it before applying.

Form DS-160 confirmation page. The DS-160 is the Online Nonimmigrant Visa Application, completed at ceac.state.gov. The confirmation page with barcode must be printed and brought to the interview.

Visa application fee (MRV fee) receipt. The Machine Readable Visa application fee is currently $185 and is non-refundable. Payment is made before scheduling the interview appointment.

SEVIS I-901 fee payment receipt. The Student and Exchange Visitor Information System fee is $350 for F-1 students. Payment is made online at fmjfee.gov before the visa interview.

One photograph meeting US visa requirements. The photo must be 2x2 inches (5x5 cm) with a white background, taken within the last 6 months.

Financial evidence demonstrating ability to cover tuition and living expenses. This may include bank statements, scholarship award letters, sponsor letters, or evidence of personal or family assets.

Academic transcripts, diplomas, and standardized test scores such as TOEFL, IELTS, GRE, or SAT scores. These demonstrate academic preparation for the program.

Admission letter from the SEVP-approved US educational institution confirming acceptance into the program.

Source: US Department of State, travel.state.gov""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "State Department - F-1 Required Documents",
        "agency": "State Department",
        "visa_type": ["F-1"],
    },
    {
        "text": """F-1 Visa Application Fees

The F-1 visa application involves the following fees:

MRV Visa Application Fee: $185. This is the Machine Readable Visa application fee. It is non-refundable and must be paid before scheduling the visa interview appointment. The fee is paid through the US Department of State payment system.

SEVIS I-901 Fee: $350 for F-1 students. The Student and Exchange Visitor Information System fee supports the SEVP program that tracks international students. Payment is made online at fmjfee.gov using the I-20 form SEVIS ID number. This fee must be paid before the visa interview.

Reciprocity Fee: Some countries have a reciprocity fee in addition to the MRV fee. The amount varies by country and visa type. Students should check the US embassy or consulate website for their specific country to determine if a reciprocity fee applies.

Fee amounts are subject to change by the US government. Applicants should verify current fees at travel.state.gov before applying.

Source: US Department of State, travel.state.gov""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "State Department - F-1 Fees",
        "agency": "State Department",
        "visa_type": ["F-1"],
    },
    {
        "text": """F-1 Visa Application Process Step by Step

The F-1 visa application process follows these steps:

Step 1: Apply to and receive admission from a SEVP-approved US educational institution. The school must be certified by the Student and Exchange Visitor Program to enroll nonimmigrant students.

Step 2: Receive Form I-20 from the school after accepting admission and providing financial documentation. The school issues the I-20, Certificate of Eligibility for Nonimmigrant Student Status, which confirms the student meets financial and academic requirements.

Step 3: Pay the SEVIS I-901 fee online at fmjfee.gov. Use the SEVIS ID number from the I-20 form. Keep the payment receipt for the visa interview.

Step 4: Complete the online DS-160 visa application at ceac.state.gov. Answer all questions accurately. Upload a compliant photograph. Print the DS-160 confirmation page with barcode.

Step 5: Pay the MRV visa application fee of $185. Payment methods vary by country. Keep the receipt.

Step 6: Schedule a visa interview appointment at the nearest US embassy or consulate. Appointment availability varies by location and season. Summer months typically have longer wait times.

Step 7: Attend the visa interview with all required documents including I-20, passport, DS-160 confirmation page, fee receipts, financial evidence, and academic records.

Step 8: If approved, receive the visa stamp in the passport. Some applicants may be subject to administrative processing under INA Section 221(g), which requires additional documentation or waiting period.

Step 9: Enter the US within 30 days of the program start date listed on the I-20 form. The student cannot begin studies before this date.

Source: US Department of State, travel.state.gov""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "State Department - F-1 Application Process",
        "agency": "State Department",
        "visa_type": ["F-1"],
    },
    {
        "text": """F-1 Student Work Authorization

F-1 students have limited work authorization under the following categories:

On-campus employment: F-1 students may work on the campus of their school up to 20 hours per week during active school sessions. During official school breaks, holidays, and vacations, students may work full time. No additional authorization beyond valid F-1 status is required for on-campus employment. Students must obtain a job offer from the campus employer.

CPT (Curricular Practical Training): CPT is work authorization for off-campus employment that is directly related to the student's major field of study. CPT is an integral part of the established curriculum. The student must receive recommendation from their Designated School Official (DSO) before beginning work. CPT does not require USCIS approval. The school authorizes CPT by updating the student's SEVIS record.

OPT (Optional Practical Training): OPT is temporary employment directly related to the student's major area of study. OPT requires approval from USCIS via Form I-765, Application for Employment Authorization. Students may apply for up to 12 months of OPT after completing their degree program. STEM degree holders may be eligible for a 24-month OPT extension, allowing a total of up to 36 months of OPT employment. Students must apply for OPT before completing their studies but cannot begin working until the Employment Authorization Document (EAD) is received.

Unauthorized employment violates F-1 status and may result in deportation and future visa ineligibility.

Source: USCIS, uscis.gov; SEVP, studyinthestates.dhs.gov""",
        "url": "https://studyinthestates.dhs.gov/f-students",
        "title": "SEVP - F-1 Work Authorization",
        "agency": "SEVP",
        "visa_type": ["F-1"],
    },
    {
        "text": """F-1 Visa Common Refusal Reasons

The most common reasons for F-1 visa refusal include:

Failure to demonstrate sufficient financial resources to cover tuition and living expenses for the first year of study. The consular officer must be satisfied that the student has access to adequate funds without resorting to unauthorized employment.

Failure to establish strong nonimmigrant intent under INA Section 214(b). The applicant must convince the consular officer that they intend to return to their home country after completing studies. Evidence of ties to the home country such as family, property, employment prospects, or enrollment in a continuing program may be considered. INA Section 214(b) is the most common basis for F-1 visa refusal.

Invalid or expired Form I-20. The I-20 must be properly signed by the school official and the student, and must not be expired.

Incomplete or inconsistent documentation. Missing required documents or discrepancies between documents can lead to refusal.

Failure to prove intent to return home after studies are completed. This overlaps with INA Section 214(b) requirements.

Previous violations of US immigration law. Prior overstays, unauthorized employment, or other status violations may affect eligibility.

Inadequate English proficiency without enrollment in English language training programs. The student must demonstrate ability to pursue academic studies or be enrolled in sufficient English coursework.

Source: US Department of State, travel.state.gov; INA Section 214(b)""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "State Department - F-1 Refusal Reasons",
        "agency": "State Department",
        "visa_type": ["F-1"],
    },
    # ---- J-1 Exchange Visitor ----
    {
        "text": """J-1 Exchange Visitor Visa Overview

The J-1 exchange visitor visa is designed for participants in programs approved by the US Department of State. The J-1 visa promotes cultural exchange through work and study-based activities in the United States. J-1 students are sponsored by designated exchange visitor programs that issue the DS-2019 form, Certificate of Eligibility for Exchange Visitor Status.

J-1 categories relevant to students include:

Student category: Enrolled in academic study programs at US institutions. Similar to F-1 but operates under the exchange visitor framework with a program sponsor rather than a direct school relationship.

Research Scholar category: Researchers, postdoctoral scholars, and professors visiting the US to teach, lecture, or conduct research at US institutions.

Summer Work Travel category: Short-term employment during summer vacation for students enrolled in foreign post-secondary institutions. Allows participants to experience American culture while earning supplemental income.

Trainee category: Recent graduates and working professionals seeking supervised training in their professional field at US organizations.

The J-1 visa is classified under section 101(a)(15)(J) of the Immigration and Nationality Act.

Source: US Department of State, exchanges.state.gov""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html",
        "title": "State Department - J-1 Exchange Visitor",
        "agency": "State Department",
        "visa_type": ["J-1"],
    },
    {
        "text": """J-1 Visa Application Documents

The following documents are required for a J-1 visa application and interview:

Form DS-2019, Certificate of Eligibility for Exchange Visitor Status, issued by the designated exchange program sponsor. This form replaces the I-20 used for F-1 visas. The sponsor issues the DS-2019 after placing the participant in an approved program.

Valid passport that must be valid for at least 6 months beyond the intended period of stay in the US.

Form DS-160 confirmation page. The Online Nonimmigrant Visa Application completed at ceac.state.gov. Print the confirmation page with barcode.

Visa application fee (MRV fee) receipt. Currently $185, non-refundable.

SEVIS I-901 fee payment receipt. The Student and Exchange Visitor Information System fee for J-1 students is $220. Payment is made online at fmjfee.gov before the visa interview.

One photograph meeting US visa requirements. 2x2 inches with white background, taken within the last 6 months.

Financial evidence demonstrating ability to cover all expenses as stated on the DS-2019 form. This includes tuition, living expenses, and health insurance requirements.

Program invitation letter or evidence of acceptance into the exchange visitor program.

Academic and professional documents supporting the exchange program, such as transcripts, diplomas, CV, or research proposals.

Source: US Department of State, travel.state.gov""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html",
        "title": "State Department - J-1 Documents",
        "agency": "State Department",
        "visa_type": ["J-1"],
    },
    {
        "text": """J-1 Visa Fees and Two-Year Home Residency Requirement

J-1 visa application fees:

MRV Visa Application Fee: $185. Non-refundable, paid before interview appointment.

SEVIS I-901 Fee: $220 for J-1 exchange visitors. Amount may vary by program category. Paid online at fmjfee.gov before the visa interview.

Reciprocity Fee: Varies by country. Check the US embassy or consulate website for country-specific fees.

Two-Year Home Country Physical Presence Requirement under INA Section 212(e):

Some J-1 exchange visitors are subject to the two-year home country physical presence requirement. This means they must return to their home country for two years before being eligible for certain US immigrant visas or changing status to H-1B or other immigrant categories.

This requirement typically applies if:

The exchange visitor's government or an externally funded program provided a grant, scholarship, or funding for the exchange program.

The field of study or research is on the US Department of State's Exchange Visitor Skills List for the participant's country. This list identifies fields where the home country has a shortage of trained professionals.

The exchange visitor is coming to the US for graduate medical training or research.

J-1 visitors subject to the two-year requirement may apply for a waiver under certain conditions, including no-objection statements from their home government, exceptional hardship to a US citizen spouse or child, or persecution claims.

Source: US Department of State, exchanges.state.gov; INA Section 212(e)""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html",
        "title": "State Department - J-1 Fees and Requirements",
        "agency": "State Department",
        "visa_type": ["J-1"],
    },
    # ---- M-1 Vocational Student ----
    {
        "text": """M-1 Vocational Student Visa Overview

The M-1 visa is for nonimmigrant students pursuing a vocational or technical program in the United States that is primarily practical or technical rather than academic in nature. M-1 students attend SEVP-approved vocational or technical institutions.

Vocational programs include trade school, technical school, mechanical or auto repair, culinary arts, cosmetology, and other nonacademic practical training programs. Unlike the F-1 visa, which covers academic study at colleges and universities, the M-1 visa is specifically for vocational and technical education.

M-1 students are classified under section 101(a)(15)(M) of the Immigration and Nationality Act.

Key differences from F-1 visa:

Program length: M-1 status is generally limited to 1 year of study, with possible extensions not exceeding 3 years total. Extensions are granted only for additional vocational training at the same or higher level. F-1 has no such fixed maximum limit.

Transfers: M-1 students may only transfer to another vocational program at the same level or higher level of study. Transferring to a lower-level program requires restarting the program completion timeline.

Work authorization: M-1 students are not authorized to work during their program of study. After completing studies, they may be eligible for practical training on a temporary basis, limited to 1 month per every 15 months of study completed.

Dependents: M-2 dependents may attend academic or language school but may not engage in employment.

No OPT: M-1 students are not eligible for Optional Practical Training (OPT). Only post-completion practical training is available.

Source: USCIS, uscis.gov; SEVP, studyinthestates.dhs.gov""",
        "url": "https://www.uscis.gov/m-vocational-student",
        "title": "USCIS - M-1 Vocational Student",
        "agency": "USCIS",
        "visa_type": ["M-1"],
    },
    {
        "text": """M-1 Visa Application Documents and Fees

M-1 visa application documents:

Form I-20, Certificate of Eligibility for Nonimmigrant Student Status, issued by an SEVP-approved vocational or technical school. This confirms the student has been accepted into a qualifying vocational program.

Valid passport valid for at least 6 months beyond the intended period of stay.

Form DS-160 confirmation page from the online Nonimmigrant Visa Application at ceac.state.gov.

MRV visa application fee receipt.

SEVIS I-901 fee payment receipt.

One photograph meeting US visa requirements (2x2 inches, white background).

Financial evidence demonstrating ability to cover tuition and living expenses for the duration of the vocational program.

Admission letter from the SEVP-approved vocational school.

M-1 visa fees:

MRV Visa Application Fee: $185. Non-refundable, paid before interview appointment.

SEVIS I-901 Fee: $220 for M-1 students. Paid online at fmjfee.gov before the visa interview.

Reciprocity Fee: Varies by country. Check travel.state.gov for country-specific fees.

M-1 visa application process:

Apply to and receive admission from a SEVP-approved vocational or technical school. Receive Form I-20 from the school. Pay the SEVIS I-901 fee. Complete the DS-160 online. Pay the MRV fee. Schedule and attend the visa interview. If approved, enter the US within 30 days of the program start date.

Source: USCIS, uscis.gov; State Department, travel.state.gov""",
        "url": "https://www.uscis.gov/m-vocational-student",
        "title": "USCIS - M-1 Documents and Fees",
        "agency": "USCIS",
        "visa_type": ["M-1"],
    },
    # ---- Post-Arrival Information ----
    {
        "text": """Post-Arrival Steps for Student Visa Holders

After arriving in the US on a student visa, the following steps are important:

Report to Your School (SEVP/DSO Reporting):

F-1 and M-1 students must report to their Designated School Official (DSO) to activate their SEVIS record. J-1 students must report to their program sponsor or Responsible Officer (RO).

F-1 and M-1 students should report to their DSO within the first week of arriving, or by the date specified in the I-20. The DSO updates SEVIS with the student's arrival information and address.

J-1 students should report to their program sponsor or RO within 30 days of arrival to verify the SEVIS record and address.

Students must keep their address updated with their DSO or RO at all times. Address changes must be reported within 10 days.

Carry the I-20 or DS-2019 form and passport at all times as proof of immigration status.

Source: SEVP, studyinthestates.dhs.gov""",
        "url": "https://studyinthestates.dhs.gov/f-students",
        "title": "SEVP - Post-Arrival Reporting",
        "agency": "SEVP",
        "visa_type": ["post-visa"],
    },
    {
        "text": """Social Security Number (SSN) for International Students

F-1 students with on-campus work authorization, Curricular Practical Training (CPT), or Optional Practical Training (OPT) approval can apply for a Social Security Number through the Social Security Administration (SSA). J-1 students with work authorization may also apply. M-1 students are generally not eligible for an SSN during their program.

To apply for an SSN:

Complete Form SS-5, Application for a Social Security Card. This form is available at local SSA offices or online at ssa.gov.

Bring required documents to the SSA office in person: valid passport with US student visa, I-94 arrival record, and I-20 or DS-2019 form.

F-1 students must bring a job offer letter from the university or an approved Employment Authorization Document (EAD) for CPT or OPT. The SSA requires proof of work authorization before issuing an SSN.

Visit a local Social Security Administration office in person. SSN applications cannot be submitted online for non-US citizens.

SSN cards are typically mailed within 7 to 14 business days after the in-person application.

Note: An SSN is not required for opening a bank account or obtaining a state ID in many cases. Some institutions accept alternative documentation.

Source: Social Security Administration, ssa.gov""",
        "url": "https://www.ssa.gov/foreign/immigrant/apply.html",
        "title": "SSA - SSN for International Students",
        "agency": "SSA",
        "visa_type": ["post-visa"],
    },
    {
        "text": """Tax Obligations for International Students

Student visa holders in the US are generally required to file federal and state tax returns, even if no US income was earned. International students are classified as nonresident aliens for tax purposes during their first 5 calendar years in the US.

Key tax obligations:

File Form 1040-NR, the Nonresident Alien Individual US Income Tax Return. After 5 calendar years, the substantial presence test may classify the student as a resident alien for tax purposes, requiring Form 1040 instead.

Report all US-source income, including on-campus wages, research and teaching assistantships, and the portion of scholarships that exceeds tuition and fees. Scholarships used solely for tuition and required fees may be tax-exempt.

Use a Social Security Number (SSN) or apply for an Individual Taxpayer Identification Number (ITIN) via Form W-7 if the student does not have an SSN and has a tax filing obligation. ITINs are issued by the IRS for tax purposes only.

File state tax returns where applicable. State tax requirements vary by state of residence and employment.

Treaty benefits: If the student's home country has an income tax treaty with the US, the student may be eligible for exemptions or reductions on certain types of income. File Form 1040-NR with appropriate treaty claims.

Federal and state tax returns are generally due by April 15 of the following year. Extensions may be requested using Form 4868.

The IRS provides Special Instructions for Tax Forms for Nonresident Aliens, available at irs.gov.

Source: Internal Revenue Service, irs.gov""",
        "url": "https://www.irs.gov/individuals/international-taxes/nonresident-alien-individuals",
        "title": "IRS - Nonresident Alien Tax Information",
        "agency": "IRS",
        "visa_type": ["post-visa"],
    },
    {
        "text": """Opening a Bank Account as an International Student

Requirements for opening a bank account vary by financial institution. International students generally need the following documents:

Valid passport with a current US student visa (F-1, J-1, or M-1).

Form I-20 or DS-2019 as proof of student status and immigration documentation.

I-94 arrival record, available online at i94.cbp.dhs.gov. Print the record from the website.

Social Security Number (SSN) or Individual Taxpayer Identification Number (ITIN). Some banks accept alternative documentation such as the I-20 and passport if the student does not yet have an SSN.

Proof of US address, such as a utility bill, lease agreement, or school acceptance letter with a US address.

Initial deposit, which varies by bank and account type. Some banks have no minimum initial deposit requirement.

Some banks offer specific programs for international students with reduced fees and lower minimum balances. Consider choosing a bank with branches near the campus for convenience.

Note: Credit cards for international students without a US credit history may require a secured card or a cosigner. Building US credit history takes time.

Source: Federal Reserve consumer information""",
        "url": "https://www.uscis.gov/international-students-academics",
        "title": "USCIS - International Students Bank Accounts",
        "agency": "USCIS",
        "visa_type": ["post-visa"],
    },
    {
        "text": """State ID and Driver's License for International Students

Each US state has its own requirements for issuing identification cards and driver's licenses to student visa holders. The following documents are generally required:

Valid visa and I-94 arrival record as proof of legal presence in the US.

Form I-20 or DS-2019 as proof of current student status.

Proof of state residency, which may include a utility bill, lease agreement, bank statement showing a US address, or school enrollment verification letter.

Social Security Number or proof of SSN application denial letter. Some states accept alternative documentation if an SSN is not available.

Valid passport.

Written knowledge test and vision test for driver's license applicants.

State-specific application fee.

Contact the state's Department of Motor Vehicles (DMV) or equivalent agency for specific requirements. Some states accept the I-20 form as proof of state residency.

Real ID Act compliance: As of May 7, 2025, a Real ID-compliant license or alternative federally accepted documentation is required to board domestic flights and enter certain federal facilities. International students should verify their state ID meets Real ID requirements.

Source: US Department of State, DMV guidelines; Real ID Act""",
        "url": "https://www.uscis.gov/international-students-academics",
        "title": "USCIS - State ID for International Students",
        "agency": "USCIS",
        "visa_type": ["post-visa"],
    },
    # ---- General Visa Information ----
    {
        "text": """DS-160 Online Nonimmigrant Visa Application

The DS-160 form is the Online Nonimmigrant Visa Application required for all nonimmigrant visa categories, including F-1, J-1, and M-1 student visas. The form is completed electronically at ceac.state.gov.

Completing the DS-160:

Access the DS-160 form at ceac.state.gov. Select the appropriate US embassy or consulate where the visa interview will take place.

Answer all questions accurately and completely. Incomplete or inaccurate information may result in visa delay or refusal.

Upload a photograph that meets US visa requirements: 2x2 inches (5x5 cm), white background, taken within the last 6 months, frontal view with neutral expression.

After completing the form, print the DS-160 confirmation page with the barcode. This page must be brought to the visa interview. Do not email or fax the confirmation page.

The DS-160 application is valid for 30 days from the date of initial completion. If the application is not submitted within 30 days, it expires and must be restarted.

Keep the DS-160 application ID number for reference. If changes are needed after submission, a new DS-160 must be completed.

Source: US Department of State, ceac.state.gov""",
        "url": "https://ceac.state.gov",
        "title": "State Department - DS-160 Application",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
    {
        "text": """US Student Visa Processing Times and Appointment Wait Times

Visa processing times for F-1, J-1, and M-1 student visas vary significantly by US embassy or consulate location and by season.

Typical processing timeline:

After the visa interview, most student visa applications are processed within a few business days. If the application is approved, the passport with the visa stamp is returned through the courier service specified during the application.

Administrative processing under INA Section 221(g) may extend processing time. This additional processing can take several weeks to several months. Reasons include the need for additional documentation, security checks, or specialized review of the applicant's field of study.

Appointment wait times vary by embassy and season:

Summer months (May through August) typically see the highest demand for student visa interviews, resulting in longer appointment wait times.

Some embassies offer expedited or emergency appointments for students with program start dates approaching. Eligibility for expedited appointments varies by embassy.

Check current appointment availability and wait times at the US embassy or consulate website for your specific location. The US Department of State publishes current visa wait times at travel.state.gov.

Processing times published by USCIS relate to form processing (such as OPT applications on Form I-765), not visa issuance at consulates. For consulate processing times, refer to the specific embassy website.

Source: US Department of State, travel.state.gov; USCIS, egov.uscis.gov/processing-times""",
        "url": "https://egov.uscis.gov/processing-times/",
        "title": "USCIS - Processing Times",
        "agency": "USCIS",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
    {
        "text": """SEVP and School Requirements for Student Visas

The Student and Exchange Visitor Program (SEVP) administers the Student and Exchange Visitor Information System (SEVIS), a database that tracks F-1, J-1, and M-1 nonimmigrant students and their dependents.

SEVP-approved schools:

Only schools certified by SEVP can issue Form I-20 to nonimmigrant students. Students should verify their school is SEVP-certified at studyinthestates.dhs.gov.

Designated School Official (DSO):

The DSO is a school employee responsible for maintaining student records in SEVIS. The DSO issues the I-20, authorizes on-campus employment, recommends CPT, and endorses travel documents. Students must maintain regular contact with their DSO.

SEVIS requirements for F-1 students:

Maintain full-time enrollment as defined by the school. Usually this means at least 12 credit hours per semester for undergraduate students and 9 credit hours for graduate students.

Report address changes to the DSO within 10 days.

Obtain DSO travel endorsement before re-entering the US after international travel.

Request a new I-20 for program extensions, school transfers, or reduced course load authorization.

Failure to maintain SEVIS compliance may result in termination of the SEVIS record, loss of status, and requirement to leave the US.

Source: SEVP, studyinthestates.dhs.gov""",
        "url": "https://studyinthestates.dhs.gov",
        "title": "SEVP - Student Requirements",
        "agency": "SEVP",
        "visa_type": ["F-1", "M-1"],
    },

    # ---- Extenuating circumstances ----
    {
        "text": """Section 214(b) Visa Refusals and Reapplying

Section 214(b) of the Immigration and Nationality Act requires every nonimmigrant visa applicant to overcome a legal presumption that they intend to immigrate permanently. A consular officer must refuse a visa under 214(b) if the applicant has not, in that officer's judgment, demonstrated sufficiently strong ties to their home country (such as employment, family, property, or other commitments) that would compel their return after a temporary stay.

A 214(b) refusal is not permanent and there is no formal appeal process. An applicant may reapply at any time by submitting a new DS-160 and paying a new MRV application fee. Consular officers recommend addressing whatever evidence was missing in the prior interview, such as clearer proof of funding, stronger ties to the home country, or a more complete academic/professional plan, before reapplying.

A prior 214(b) refusal does not need to be disclosed as a "denial" in the same way as a fraud or criminal-related ineligibility, but the DS-160 does ask about prior refusals and this should be answered accurately.

Source: US Department of State, travel.state.gov (Visa Denials)""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/visa-denials.html",
        "title": "State Department - Visa Denials (Section 214(b))",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "category": "extenuating_circumstances",
    },
    {
        "text": """SEVIS Record Termination and Reinstatement

A student's SEVIS record can be terminated by a Designated School Official (DSO) or SEVP for reasons including failure to maintain a full course of study, unauthorized employment, failure to report an address change, or failure to depart after the program end date. A terminated SEVIS record means the student is out of F-1 or M-1 status.

Under 8 CFR 214.2(f)(16), a student whose SEVIS record was terminated (or who otherwise fell out of status) may apply for reinstatement by filing Form I-539, Application to Extend/Change Nonimmigrant Status, with USCIS. Reinstatement generally requires showing that the violation resulted from circumstances beyond the student's control (or that failure to reinstate would result in extreme hardship), that the student is currently pursuing a full course of study, and that the student has not been out of status for more than 5 months at the time of filing (with limited exceptions).

While a reinstatement application is pending, the student should continue full-time enrollment. If reinstatement is denied, there is no appeal, but a motion to reopen/reconsider may be available depending on the circumstances.

Source: USCIS, 8 CFR 214.2(f)(16); SEVP Policy Guidance""",
        "url": "https://www.uscis.gov/i-539",
        "title": "USCIS - Reinstatement to Student Status (Form I-539)",
        "agency": "USCIS",
        "visa_type": ["F-1", "M-1"],
        "category": "extenuating_circumstances",
    },
    {
        "text": """Financial Hardship: Documentation and Employment Options

Applicants who cannot show the full cost of tuition and living expenses through personal or family funds may submit a sponsor's Affidavit of Support-style letter along with the sponsor's bank statements, or a scholarship/assistantship award letter from the school, as part of their financial evidence.

For F-1 students already enrolled who experience financial hardship that arose after arriving in the US due to unforeseen circumstances beyond their control, federal regulation (8 CFR 214.2(f)(9)(ii)(C)) allows a DSO to authorize off-campus employment for "severe economic hardship." This requires the student to have been in F-1 status for at least one full academic year, to file Form I-765 with USCIS for an Employment Authorization Document, and to show the hardship was caused by circumstances beyond the student's control (e.g., loss of financial aid or on-campus employment through no fault of the student, substantial currency devaluation, unexpected changes in a sponsor's finances, or excessive medical expenses).

Students should discuss financial hardship with their school's DSO before making any changes, since unauthorized employment while on F-1/M-1/J-1 status can result in SEVIS termination.

Source: USCIS, 8 CFR 214.2(f)(9)(ii)(C); Form I-765 instructions""",
        "url": "https://www.uscis.gov/i-765",
        "title": "USCIS - Off-Campus Employment for Severe Economic Hardship (F-1)",
        "agency": "USCIS",
        "visa_type": ["F-1"],
        "category": "extenuating_circumstances",
    },
    {
        "text": """Medical or Family Emergencies During the Visa Process

Most US embassies and consulates offer an emergency or expedited appointment request option for applicants who need to travel urgently due to a medical emergency, a death or serious illness in the family, or another compelling humanitarian reason. This request is typically made through the same online appointment system used to schedule the standard interview, by selecting the emergency/expedite option and explaining the reason; approval and available slots vary by post and are not guaranteed.

If a medical or family emergency happens after a visa has already been refused or while a case is otherwise pending, applicants should contact the specific embassy or consulate handling their case directly, since procedures and response times differ by location.

Source: US Department of State, travel.state.gov (Visa Appointment Wait Times / Contact a US Embassy or Consulate)""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/wait-times.html",
        "title": "State Department - Expedited/Emergency Appointment Requests",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "category": "extenuating_circumstances",
    },
    {
        "text": """Delayed I-20, DS-2019, or Other Required Documents

If a Form I-20 or DS-2019 arrives later than expected, students should first confirm with their school's international student office (DSO or program sponsor) that SEVIS registration has been completed, since the visa interview and DS-160 both depend on the SEVIS ID found on that document. A late I-20/DS-2019 does not by itself extend a visa appointment; students should reschedule their interview date if the required documents will not be ready in time, since arriving without them can result in the interview being unsuccessful.

If a program start date is close and required documents are delayed, contacting the school's DSO about a possible program start date deferral (which requires an updated I-20/DS-2019) is generally preferable to attempting an interview without complete documentation.

Source: SEVP, studyinthestates.dhs.gov; US Department of State, travel.state.gov""",
        "url": "https://studyinthestates.dhs.gov",
        "title": "SEVP - Program Start Date and Document Timing",
        "agency": "SEVP",
        "visa_type": ["F-1", "J-1", "M-1"],
        "category": "extenuating_circumstances",
    },

    # ---- Visa interview preparation ----
    {
        "text": """Preparing for the Student Visa Interview

Consular officers use the interview to assess whether an applicant qualifies for a student visa, focusing on a few consistent topic areas rather than a fixed script. Applicants should be ready to speak clearly and specifically about: their study plans and why they chose their particular school and program; how they will pay for tuition and living expenses, including who is providing the funds and their relationship to the applicant; and their ties to their home country, such as family, career plans, or property, that support an intent to return after completing the program.

Applicants should bring their passport, Form I-20 or DS-2019, DS-160 confirmation page, SEVIS fee receipt, and financial documents, and should be prepared to answer questions about the specific contents of those documents (such as the exact program length or the source of sponsorship funds) rather than only general statements.

Interviews are typically short, and consular officers make decisions based on the interview and documentation provided that day; there is no fixed list of questions guaranteed to be asked, and preparation should focus on being able to explain one's own plans and documents accurately and specifically.

Source: EducationUSA (US Department of State network for international student advising); US Department of State, travel.state.gov""",
        "url": "https://educationusa.state.gov/foreign-students/apply-us-visa",
        "title": "EducationUSA - Applying for a US Student Visa",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "category": "interview_prep",
    },
    {
        "text": """Additional Scrutiny for M-1 Vocational Student Interviews

M-1 vocational student visa applicants often face additional scrutiny compared to F-1 academic applicants, since vocational programs are more frequently associated with cases where consular officers have found weak ties to the home country or unclear post-program intent. M-1 applicants should be prepared to explain in detail how the specific vocational program connects to their career plans at home, and should bring complete documentation of program costs, since M-1 students (unlike F-1) must show funds for the entire course of study up front rather than just the first year.

Source: US Department of State, travel.state.gov; SEVP, studyinthestates.dhs.gov""",
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/student-visa.html",
        "title": "State Department - M-1 Vocational Student Visa Interview Considerations",
        "agency": "State Department",
        "visa_type": ["M-1"],
        "category": "interview_prep",
    },

    # ---- Origin-country specific guidance (embassy/consulate locations) ----
    {
        "text": """Applying for a US Student Visa from India

Indian applicants for F-1, J-1, or M-1 visas apply through the US Embassy in New Delhi or the US Consulates General in Mumbai, Chennai, Hyderabad, or Kolkata. Applicants should schedule their interview at the embassy or consulate with jurisdiction over their place of residence in India, though in practice applicants may sometimes apply at any post; check the specific post's website for its jurisdiction policy before booking.

As with any country, reciprocity fees (an additional fee some nationalities pay based on what their home country charges US citizens for similar visas) can apply on top of the standard MRV fee — check the State Department's visa reciprocity table for India before paying, since this amount is set per visa class and can change.

If a prior visa was refused under Section 214(b), Indian applicants reapply the same way as any other applicant: a new DS-160 and a new MRV fee, ideally with stronger evidence of ties to India and financial support.

Source: US Embassy New Delhi and Consulates General in India, travel.state.gov""",
        "url": "https://in.usembassy.gov/visas/",
        "title": "US Mission India - Visa Services",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "India",
    },
    {
        "text": """Applying for a US Student Visa from China

Chinese applicants for F-1, J-1, or M-1 visas apply through the US Embassy in Beijing or the US Consulates General in Shanghai, Guangzhou, Shenyang, or Wuhan. As with India, applicants generally apply at the post with consular jurisdiction over their place of residence in mainland China; check the specific post's website for current jurisdiction and appointment availability, since wait times can vary significantly by post and season (appointment demand is typically highest in the summer months before the fall semester).

Reciprocity fees for Chinese nationals can apply on top of the standard MRV fee for certain visa classes — check the State Department's visa reciprocity table for China, since these amounts and validity periods are set per visa class and can change.

Source: US Embassy Beijing and Consulates General in China, travel.state.gov""",
        "url": "https://china.usembassy-china.org.cn/visas/",
        "title": "US Mission China - Visa Services",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "China",
    },
    {
        "text": """Applying for a US Student Visa from Nigeria

Nigerian applicants for F-1, J-1, or M-1 visas apply through the US Embassy in Abuja or the US Consulate General in Lagos. Jurisdiction is generally based on state of residence within Nigeria; check the specific post's website for the current jurisdiction breakdown and appointment wait times before booking.

Reciprocity fees for Nigerian nationals can apply on top of the standard MRV fee for certain visa classes — check the State Department's visa reciprocity table for Nigeria, since amounts and visa validity periods are set per visa class and can change.

Source: US Mission Nigeria, travel.state.gov""",
        "url": "https://ng.usembassy.gov/visas/",
        "title": "US Mission Nigeria - Visa Services",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Nigeria",
    },
    {
        "text": """Applying for a US Student Visa from Brazil

Brazilian applicants for F-1, J-1, or M-1 visas apply through the US Embassy in Brasilia or the US Consulates General in Rio de Janeiro, Sao Paulo, Recife, or Porto Alegre. Applicants generally apply at the post with consular jurisdiction over their state of residence in Brazil; check the specific post's website for the current jurisdiction map and appointment availability.

Reciprocity fees for Brazilian nationals can apply on top of the standard MRV fee for certain visa classes — check the State Department's visa reciprocity table for Brazil, since amounts and visa validity periods are set per visa class and can change.

Source: US Mission Brazil, travel.state.gov""",
        "url": "https://br.usembassy.gov/visas/",
        "title": "US Mission Brazil - Visa Services",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Brazil",
    },
    {
        "text": """Applying for a US Student Visa from South Korea

South Korean applicants for F-1, J-1, or M-1 visas apply through the US Embassy in Seoul or the US Consulate in Busan. Check the specific post's website for current jurisdiction and appointment wait times, since demand can rise sharply ahead of the US fall (August/September) semester start.

Reciprocity fees for South Korean nationals can apply on top of the standard MRV fee for certain visa classes — check the State Department's visa reciprocity table for South Korea, since amounts and visa validity periods are set per visa class and can change.

Source: US Embassy Seoul and US Consulate Busan, travel.state.gov""",
        "url": "https://kr.usembassy.gov/visas/",
        "title": "US Mission South Korea - Visa Services",
        "agency": "State Department",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "South Korea",
    },
]


# -------------------------------------------------------
# Main ingestion
# -------------------------------------------------------

def run_static_ingestion():
    """Load static content into ChromaDB."""
    print("=" * 60)
    print("Static Content Ingestion - Student Visa RAG Database")
    print("=" * 60)

    print(f"\nLoading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"ChromaDB path: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Clear existing collection for clean re-ingest
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' ready.\n")

    total_chunks = 0

    for doc in STATIC_DOCUMENTS:
        text = doc["text"]
        url = doc["url"]
        print(f"Processing: {doc['title']}")
        print(f"  URL: {url}")
        print(f"  Agency: {doc['agency']}")
        print(f"  Visa types: {', '.join(doc['visa_type'])}")

        chunks = chunk_text(text)
        print(f"  Text length: {len(text)} chars")
        print(f"  Chunks created: {len(chunks)}")

        metadata_template = {
            "doc_key": f"{url}_{doc['title']}",
            "url": url,
            "title": doc["title"],
            "agency": doc["agency"],
            "visa_type": "|".join(doc["visa_type"]),
            "last_updated": datetime.datetime.now().isoformat(),
        }
        if doc.get("origin_country"):
            metadata_template["origin_country"] = doc["origin_country"]
        if doc.get("category"):
            metadata_template["category"] = doc["category"]

        store_in_chroma(chunks, metadata_template)
        total_chunks += len(chunks)
        print(f"  Stored in ChromaDB.\n")

    print("=" * 60)
    print(f"Ingestion complete.")
    print(f"  Total documents processed: {len(STATIC_DOCUMENTS)}")
    print(f"  Total chunks stored: {total_chunks}")
    print(f"  ChromaDB collection size: {collection.count()}")
    print("=" * 60)


if __name__ == "__main__":
    run_static_ingestion()
