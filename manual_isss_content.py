import json
import os

# ─────────────────────────────────────────────
# ISSS CONTENT (flat structure: url, title, content)
# ─────────────────────────────────────────────
isss_content = [
    {
        "url": "https://isss.gsu.edu/employment/cpt/",
        "title": "Curricular Practical Training (CPT)",
        "content": """
Curricular Practical Training (CPT)

What is CPT?
Curricular Practical Training (CPT) is a type of employment authorization that allows F-1 students to work off-campus in a position that is directly related to their major area of study.

CPT Eligibility Requirements:
- Must be enrolled full-time for at least one academic year (two semesters or three quarters)
- Job must be directly related to your major
- Must be required by your academic program or earn academic credit
- Must have job offer before applying
- Cannot begin work until CPT is authorized

Types of CPT:
1. Part-time CPT: 20 hours or less per week (can be used while school is in session)
2. Full-time CPT: More than 20 hours per week (typically during breaks)

Important: If you use 12 months or more of full-time CPT, you will NOT be eligible for OPT.

How to Apply:
1. Get a job offer related to your major
2. Meet with your academic advisor
3. Submit CPT application to ISSS
4. Wait for ISSS authorization
5. Receive updated I-20 with CPT authorization

Processing Time: 5-7 business days

Questions? Contact ISSS at isss@gsu.edu
        """
    },
    {
        "url": "https://isss.gsu.edu/employment/opt/",
        "title": "Optional Practical Training (OPT)",
        "content": """
Optional Practical Training (OPT)

What is OPT?
Optional Practical Training (OPT) is temporary employment authorization that allows F-1 students to work in the United States in their field of study.

Types of OPT:
1. Pre-completion OPT: Work before completing your degree (part-time during school, full-time during breaks)
2. Post-completion OPT: Work after completing your degree (full-time, 12 months)
3. STEM Extension: Additional 24 months for STEM degree holders (total 36 months)

Eligibility Requirements:
- Must be enrolled full-time for at least one academic year
- Must be in valid F-1 status
- Must apply before completing degree or within 60 days after completion
- Job must be directly related to major area of study
- Must work at least 20 hours per week (or face unemployment limits)

Application Timeline:
- Apply 90 days before graduation but no later than 60 days after completion
- USCIS processing: 3-5 months typically
- Cannot work until you receive EAD card

Application Steps:
1. Attend OPT workshop at ISSS
2. Request OPT recommendation from ISSS
3. Receive I-20 with OPT recommendation
4. File Form I-765 with USCIS
5. Pay $410 filing fee to USCIS
6. Wait for EAD card approval
7. Begin working

Required Documents:
- Form I-765 (Application for Employment Authorization)
- I-20 with OPT recommendation from ISSS
- Copy of I-94
- Copy of all previous EADs (if applicable)
- Copy of passport identification page
- Two passport photos
- Personal check or money order for $410 payable to U.S. Department of Homeland Security

Important Rules:
- Cannot work before receiving EAD card
- Must report all employment to ISSS
- Can have up to 90 days of unemployment (150 days for STEM)
- Must maintain valid F-1 status

Contact: isss@gsu.edu
        """
    },
    {
        "url": "https://isss.gsu.edu/employment/",
        "title": "F-1 Employment Options",
        "content": """
Employment for F-1 Students

F-1 students have several employment options:

On-Campus Employment:
- No special authorization required
- Work up to 20 hours per week during school term
- Work full-time during official breaks
- Must maintain full-time enrollment

Off-Campus Employment:
Requires special authorization through one of these programs:

1. Curricular Practical Training (CPT)
   - Must be related to major
   - After one academic year
   - Can be part-time or full-time

2. Optional Practical Training (OPT)
   - Pre-completion or post-completion
   - 12 months standard (36 months for STEM)
   - Requires USCIS authorization

3. Severe Economic Hardship
   - For unexpected financial difficulties
   - Rarely granted
   - Must prove hardship

Important Rules:
- Working without authorization violates F-1 status
- Violations can lead to deportation
- Always get approval BEFORE starting work
- Keep copies of all employment authorization documents

For questions, contact ISSS at isss@gsu.edu
        """
    },
    {
        "url": "https://isss.gsu.edu/travel/",
        "title": "Travel for F-1 Students",
        "content": """
Travel Information for F-1 Students

Documents Required for Re-entry:
- Valid passport (valid for at least 6 months)
- Valid F-1 visa stamp (unless from visa-exempt country)
- Valid I-20 with travel signature (must be signed within past 12 months)
- Proof of enrollment (unofficial transcript or enrollment letter)

Travel Signature:
Your I-20 must have a travel signature from ISSS to re-enter the U.S.
- Travel signatures are valid for 12 months
- Get signature before leaving U.S.
- Can request signature via email to isss@gsu.edu

Important Information:

During OPT:
- Must have valid EAD card
- Must have job offer letter or proof of employment
- I-20 must be endorsed for travel within past 6 months

Canada and Mexico Travel:
- F-1 visa stamp can be expired for trips under 30 days (automatic visa revalidation)
- Must not apply for new visa while away
- Must return to U.S. directly from Canada or Mexico

Tips:
- Check passport expiration before booking travel
- Get travel signature at least 1 week before departure
- Keep employment documents with you
- Check visa requirements for destination country

Questions? Email isss@gsu.edu
        """
    },
    {
        "url": "https://isss.gsu.edu/current-students/",
        "title": "Current F-1 Students",
        "content": """
Information for Current F-1 Students

Maintaining Your F-1 Status:

Full-Time Enrollment:
- Undergraduate: 12 credits minimum per semester
- Graduate: 9 credits minimum per semester
- Must register for classes every semester (except approved breaks)

Reporting Requirements:
- Report address changes within 10 days
- Report program changes to ISSS
- Keep passport valid (at least 6 months)
- Maintain valid I-20

Employment:
- On-campus: Up to 20 hours/week during semester, full-time during breaks
- Off-campus: Requires CPT or OPT authorization
- Never work without authorization

Travel:
- Get I-20 travel signature before leaving U.S.
- Signature valid for 12 months

Important Deadlines:
- OPT applications: 90 days before to 60 days after graduation
- Travel signatures: At least 1 week before departure

Contact: isss@gsu.edu
        """
    },
    {
        "url": "https://isss.gsu.edu/",
        "title": "International Student and Scholar Services - GSU",
        "content": """
International Student and Scholar Services (ISSS)

Welcome to Georgia State University!

ISSS assists international students with:
- Immigration advising
- Visa and travel guidance
- Employment authorization
- Cultural adjustment

Contact Information:
Email: isss@gsu.edu
Phone: (404) 413-2070
Location: Student Success Center, Suite 100, 25-27 Auburn Ave NE, Atlanta, GA 30303

Office Hours:
Monday - Friday: 8:30 AM - 5:15 PM EST

Services:
- I-20 processing
- OPT and CPT authorization
- Travel signatures
- Immigration workshops

Important Reminders for F-1 Students:
- Maintain full-time enrollment
- Report address changes within 10 days
- Get work authorization before starting employment

For urgent matters, email isss@gsu.edu
        """
    }
]

# ─────────────────────────────────────────────
# INCOMING CONTENT (normalized to same flat structure)
# ─────────────────────────────────────────────
incoming_content = [
    {
        "url": "https://isss.gsu.edu/incoming-students/step-1-admissions/",
        "title": "Step 1: Admissions - I-20 Request Process",
        "content": """
Step 1: Admissions - I-20 Request

Organization: International Student & Scholar Services (ISSS), Georgia State University (GSU)
Website: https://isss.gsu.edu

After Academic Admission:
You will receive an email from ISSS with instructions to log in to iStart to submit your I-20 request.
iStart portal: https://sunapsisprd.gsu.edu/istart/controllers/start/StartEngine.cfm

Important Notes:
- An international admissions hold is placed on all newly admitted students
- Students CANNOT register for classes until the hold is removed by ISSS
- Submit financial documentation as early as possible
- ISSS will only review COMPLETE submissions — all required e-forms must be submitted
- Incomplete submissions will NOT be reviewed
- I-20 is issued to the student email address once complete
- Processing time: Allow 10 business days after complete submission

Required Documents for I-20 Request:
- Passport identification page (ALL applicants)
- Current F-1/J-1 visa or change of status approval notice, I-20/DS-2019, and I-94
  (required if currently in the U.S. in F-1 or J-1 status)
- Current visa and I-94
  (required if currently in the U.S. on a non-F-1 visa)
- Passport identification page of dependents (spouse and/or children)
  (required if dependents will accompany you)

Admissions Portals by Student Type:
- Undergraduate: https://admissions.gsu.edu/bachelors-degree/apply/international-students/
- Graduate: https://graduate.gsu.edu/how-to-apply/apply/steps-international-students/
- Perimeter College: https://perimeter.gsu.edu/admissions/international/
- J-1 Exchange Students: https://isss.gsu.edu/incoming-students/step-1-admissions/j-1-exchange-students/
        """
    },
    {
        "url": "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/",
        "title": "Step 2: Pre-Arrival Checklist",
        "content": """
Step 2: Pre-Arrival

System Used: iStart — complete the Pre-Arrival Checklist under 'Georgia State Main Campus'
iStart portal: https://sunapsisprd.gsu.edu/istart/controllers/start/StartEngine.cfm
Estimated time to complete: 45 minutes to 1 hour

Start @ State:
Visit https://start.gsu.edu to complete online orientation modules.
WARNING: First-year undergraduate F-1 students should NOT register for New Student Orientation at the end of Start @ State.

Academic Advising by Student Type:
- Undergraduate First-Year: After receiving I-20, attend a virtual academic advising session and register for classes from home country. Must attend International Student Orientation before classes start.
- Undergraduate Transfer or Transition (PC to Atlanta): After receiving I-20, schedule an appointment with academic advisor. Register independently once registration appointment opens.
- Graduate Students: After receiving I-20, consult academic department for first-semester course info. Register independently once registration appointment opens.

Documents to Prepare (PDF format only):
- Passport photo page
- Visa document
- I-94 (only available after arrival in the U.S.)

Pre-Arrival Checklist Covers:
- Confirming enrollment and applying for visa
- Uploading immigration documents
- Check-in, orientation, and arrival information
- Housing options (short-term and long-term)
- Transportation and airport pickup request
- Special disability assistance request

Technical Support:
If you have issues, email isss@gsu.edu with your full name, Panther ID number, and description of the problem.

Warning: Failure to complete pre-arrival e-forms before Check-in and Orientation will cause delays in starting class and settling in Atlanta.
        """
    },
    {
        "url": "https://isss.gsu.edu/incoming-students/step-3-arrival-and-orientation/",
        "title": "Step 3: Arrival and Orientation",
        "content": """
Step 3: Arrival and Orientation

Required for ALL international students:
- International Student Check-in
- International Student Orientation

Orientation Components:
1. International Student Check-in: Required check-in for all international students upon arrival.
2. International Student Orientation: Online course covering immigration status, benefits, policies, procedures, life in the U.S., and campus programs.
3. Arrival Confirmation: Virtual check-in with ISSS to confirm arrival to the U.S. Government and protect immigration status.
4. Mandatory Academic Advising Session: Required for First-Year International Students only.

Registration: Students receive orientation registration info via iStart. ISSS communicates further details closer to semester start.
Orientation info: https://isss.gsu.edu/international-check-in-and-orientation/
        """
    },
    {
        "url": "https://isss.gsu.edu/",
        "title": "ISSS Contact Information and Office Locations",
        "content": """
ISSS Contact Information

Atlanta Campus:
- Email: isss@gsu.edu
- Phone: 404-413-2070
- Location: Student Success Center, Suite 100, 25-27 Auburn Ave NE, Atlanta, GA 30303
- Mailing Address: ISSS, Georgia State University, 25 Auburn Ave NE, Suite 100, P.O. Box 3987, Atlanta, GA 30302-3987, USA
  (Use physical address for express mail)

Perimeter College Campus:
- Email: issspc@gsu.edu
- Phone: 678-891-3235
- Location: Building CN 2230 (Student Center), 555 N. Indian Creek Dr., Clarkston, GA 30021

Office Hours: Monday through Friday, 8:30 AM - 5:15 PM EST

Students Served:
- F-1 International Students (undergraduate and graduate)
- J-1 Exchange Students
- Fulbright, Muskie, and Externally Sponsored Students
- Transfer Students to GSU
- International Employees and Visiting Scholars (H-1B, O-1, TN, J-1 Scholars)
- Dependents (J-2, F-2)

Critical Rules:
- Students CANNOT register for classes until the international admissions hold is removed by ISSS
- Submit financial documentation as early as possible to allow time for visa application processing
- ISSS will only review COMPLETE submissions — all required e-forms must be submitted
- Failure to complete pre-arrival e-forms before Check-in and Orientation will cause delays in starting class
- I-94 can only be uploaded AFTER arrival in the U.S.
- First-year undergraduate F-1 students should NOT register for New Student Orientation at the end of Start @ State
        """
    }
]


def save_manual_content(filepath, content):
    """Save manually entered content"""
    os.makedirs('data/raw_docs', exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)

    total_chars = sum(len(doc.get('content', json.dumps(doc))) for doc in content)

    print(f"✅ Saved {len(content)} documents to {filepath}")
    print(f"   Pages: {len(content)}")
    print(f"   Total characters: {total_chars:,}")


if __name__ == "__main__":
    print("=" * 60)
    print("CREATING MANUAL ISSS CONTENT")
    print("=" * 60)

    save_manual_content('data/raw_docs/isss_content.json', isss_content)
    save_manual_content('data/raw_docs/incoming_content.json', incoming_content)

    print("\n✅ Knowledge base ready!")