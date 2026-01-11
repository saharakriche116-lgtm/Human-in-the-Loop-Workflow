import pdfplumber
import re

def extract_invoice_data(file_path):
    extracted_data = {
        "name": "Not found",
        "email": "Not found",
        "phone": "Not found",
        "linkedin": "",
        "github": "",
        "education": "",     # NEW
        "languages": "",     # NEW
        "skills": "",
        "summary": "",       # NEW (Profile)
        "predicted_role": "Unknown"
    }

    # Keywords for categorization
    SKILLS_KEYWORDS = ["python", "java", "sql", "react", "aws", "docker", "excel", "management", "communication", "marketing", "scrum", "agile", "c++", "linux", "git"]
    EDUCATION_KEYWORDS = ["master", "bachelor", "licence", "diplôme", "phd", "doctorat", "ingénieur", "bts", "dut", "university", "école"]
    LANGUAGES_KEYWORDS = ["anglais", "français", "espagnol", "allemand", "arabe", "english", "french", "spanish", "german", "arabic", "bilingue", "toeic"]

    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            lines = []
            
            # Extract text and lines separately
            for page in pdf.pages:
                text_page = page.extract_text()
                if text_page:
                    full_text += text_page + "\n"
                    lines.extend(text_page.split('\n'))
            
            # --- 1. NAME (Heuristic: Often the 1st non-empty line in caps or Title) ---
            for line in lines[:5]: # Check the first 5 lines
                clean_line = line.strip()
                if len(clean_line) > 3 and len(clean_line) < 30 and not any(char.isdigit() for char in clean_line):
                    # If no digits and reasonable length, assume it's the name
                    extracted_data["name"] = clean_line
                    break

            # --- 2. EMAIL ---
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
            if email_match:
                extracted_data["email"] = email_match.group(0)

            # --- 3. PHONE ---
            phone_match = re.search(r'(\+33|0|\+216)[1-9]([\s\.-]?\d{2}){4}', full_text)
            if phone_match:
                extracted_data["phone"] = phone_match.group(0)

            # --- 4. LINKS (LinkedIn / GitHub) ---
            linkedin_match = re.search(r'(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', full_text)
            if linkedin_match:
                extracted_data["linkedin"] = linkedin_match.group(0)
            
            github_match = re.search(r'(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+', full_text)
            if github_match:
                extracted_data["github"] = github_match.group(0)

            # --- 5. SKILLS, EDUCATION & LANGUAGES (By keywords) ---
            found_skills = set()
            found_education = set()
            found_languages = set()
            
            text_lower = full_text.lower()

            # Skills
            for kw in SKILLS_KEYWORDS:
                if kw in text_lower:
                    found_skills.add(kw)
            
            # Education (Extract the whole line containing keywords like "Master", etc.)
            for line in lines:
                line_lower = line.lower()
                # Education
                if any(ed in line_lower for ed in EDUCATION_KEYWORDS):
                    found_education.add(line.strip())
                # Languages
                if any(lang in line_lower for lang in LANGUAGES_KEYWORDS):
                    # Filter to avoid taking very long sentences
                    if len(line) < 50: 
                        found_languages.add(line.strip())

            extracted_data["skills"] = ", ".join(list(found_skills))
            extracted_data["education"] = " | ".join(list(found_education))
            extracted_data["languages"] = ", ".join(list(found_languages))

            # --- 6. SUMMARY (First big sentence or paragraph, optional) ---
            # Simple extraction of lines between name and first "Experience" section
            # (Rudimentary, but fills the field for human correction)
            
    except Exception as e:
        print(f"PDF Extraction Error: {e}")

    return extracted_data