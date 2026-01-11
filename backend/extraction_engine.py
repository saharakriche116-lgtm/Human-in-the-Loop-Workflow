import pdfplumber
import re

def extract_invoice_data(file_path):
    extracted_data = {
        "name": "Non trouvé",
        "email": "Non trouvé",
        "phone": "Non trouvé",
        "linkedin": "",
        "github": "",
        "education": "",     # NOUVEAU
        "languages": "",     # NOUVEAU
        "skills": "",
        "summary": "",       # NOUVEAU (Profil)
        "predicted_role": "Inconnu"
    }

    # Mots-clés pour catégorisation
    SKILLS_KEYWORDS = ["python", "java", "sql", "react", "aws", "docker", "excel", "management", "communication", "marketing", "scrum", "agile", "c++", "linux", "git"]
    EDUCATION_KEYWORDS = ["master", "bachelor", "licence", "diplôme", "phd", "doctorat", "ingénieur", "bts", "dut", "university", "école"]
    LANGUAGES_KEYWORDS = ["anglais", "français", "espagnol", "allemand", "arabe", "english", "french", "spanish", "german", "arabic", "bilingue", "toeic"]

    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            lines = []
            
            # On récupère le texte et les lignes séparément
            for page in pdf.pages:
                text_page = page.extract_text()
                if text_page:
                    full_text += text_page + "\n"
                    lines.extend(text_page.split('\n'))
            
            # --- 1. NOM (Heuristique : Souvent la 1ère ligne non vide en majuscules ou Titre) ---
            for line in lines[:5]: # On regarde les 5 premières lignes
                clean_line = line.strip()
                if len(clean_line) > 3 and len(clean_line) < 30 and not any(char.isdigit() for char in clean_line):
                    # Si pas de chiffre et longueur raisonnable, on suppose que c'est le nom
                    extracted_data["name"] = clean_line
                    break

            # --- 2. EMAIL ---
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
            if email_match:
                extracted_data["email"] = email_match.group(0)

            # --- 3. TÉLÉPHONE ---
            phone_match = re.search(r'(\+33|0|\+216)[1-9]([\s\.-]?\d{2}){4}', full_text)
            if phone_match:
                extracted_data["phone"] = phone_match.group(0)

            # --- 4. LIENS (LinkedIn / GitHub) ---
            linkedin_match = re.search(r'(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', full_text)
            if linkedin_match:
                extracted_data["linkedin"] = linkedin_match.group(0)
            
            github_match = re.search(r'(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+', full_text)
            if github_match:
                extracted_data["github"] = github_match.group(0)

            # --- 5. COMPÉTENCES, FORMATION & LANGUES (Par mots-clés) ---
            found_skills = set()
            found_education = set()
            found_languages = set()
            
            text_lower = full_text.lower()

            # Compétences
            for kw in SKILLS_KEYWORDS:
                if kw in text_lower:
                    found_skills.add(kw)
            
            # Formation (On extrait la ligne entière qui contient le mot clé "Master", etc.)
            for line in lines:
                line_lower = line.lower()
                # Education
                if any(ed in line_lower for ed in EDUCATION_KEYWORDS):
                    found_education.add(line.strip())
                # Langues
                if any(lang in line_lower for lang in LANGUAGES_KEYWORDS):
                    # Filtre pour éviter de prendre des phrases trop longues
                    if len(line) < 50: 
                        found_languages.add(line.strip())

            extracted_data["skills"] = ", ".join(list(found_skills))
            extracted_data["education"] = " | ".join(list(found_education))
            extracted_data["languages"] = ", ".join(list(found_languages))

            # --- 6. RÉSUMÉ (Première grosse phrase ou paragraphe, optionnel) ---
            # Simple extraction des lignes entre le nom et la première section "Experience"
            # (C'est rudimentaire, mais ça remplit le champ pour correction humaine)
            
    except Exception as e:
        print(f"Erreur extraction PDF: {e}")

    return extracted_data