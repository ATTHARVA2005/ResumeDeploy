# backend/resume_parser.py

import os
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Text extraction libraries
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

class ResumeParser:
    def __init__(self):
        pass
    
    def extract_text(self, file_path: str) -> str:
        """Extracts plain text from various resume file formats."""
        file_extension = Path(file_path).suffix.lower()
        extracted_text = ""

        try:
            if file_extension == '.pdf':
                extracted_text = self._extract_from_pdf(file_path)
            elif file_extension == '.docx':
                extracted_text = self._extract_from_docx(file_path)
            elif file_extension == '.txt':
                extracted_text = self._extract_from_txt(file_path)
            else:
                print(f"Unsupported extension '{file_extension}' or attempting fallback for {file_path}. Using textract if available.")
                extracted_text = self._extract_with_textract(file_path)
        except Exception as e:
            print(f"Error during initial text extraction from {file_path} with {file_extension} parser: {e}")
            try:
                extracted_text = self._extract_with_textract(file_path)
            except Exception as textract_e:
                print(f"Textract fallback also failed for {file_path}: {textract_e}")
                extracted_text = ""

        return self._clean_text(extracted_text)

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extracts text from PDF files using pdfminer.six."""
        try:
            text = pdf_extract_text(file_path)
            return text
        except Exception as e:
            print(f"PDF extraction error for {file_path}: {e}")
            return ""
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extracts text from DOCX files using python-docx."""
        try:
            doc = Document(file_path)
            full_text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            full_text.append(cell.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"DOCX extraction error for {file_path}: {e}")
            return ""
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extracts text from TXT files."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
            return text
        except Exception as e:
            print(f"TXT extraction error for {file_path}: {e}")
            return ""
    
    def _extract_with_textract(self, file_path: str) -> str:
        """Fallback text extraction using the textract library, if available."""
        if not TEXTRACT_AVAILABLE:
            print(f"Textract is not available. Skipping extraction for {file_path}.")
            return ""
        
        try:
            text = textract.process(file_path).decode('utf-8')
            return text
        except Exception as e:
            print(f"Textract extraction error for {file_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Cleans and normalizes extracted text for better NLP processing."""
        if not text:
            return ""
        
        text = text.replace('\xa0', ' ').replace('\u2022', ' ').replace('\u2013', '-')
        text = re.sub(r'\$[0-9]+\^{.+?}\$', '', text) 
        text = re.sub(r'\"', '', text)
        text = re.sub(r',,+', ',', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r'\n{2,}', '\n', text)
        text = re.sub(r'^\s*,\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r',\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()

    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """Extracts common contact information from resume text."""
        contact_info: Dict[str, List[str]] = {
            'emails': [],
            'phones': [],
            'linkedin': [],
            'github': []
        }
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        contact_info['emails'] = list(set(re.findall(email_pattern, text, re.IGNORECASE)))
        
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        raw_phones = re.findall(phone_pattern, text)
        contact_info['phones'] = list(set([p.strip() for p in raw_phones if len(re.sub(r'\D', '', p)) >= 10]))
        
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        contact_info['linkedin'] = list(set([match.strip() for match in linkedin_matches]))
        
        github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+/?'
        github_matches = re.findall(github_pattern, text, re.IGNORECASE)
        contact_info['github'] = list(set([match.strip() for match in github_matches]))
        
        return contact_info
    
    def extract_sections(self, text: str) -> Dict[str, List[str]]:
        """Extracts different logical sections from resume text."""
        sections: Dict[str, List[str]] = {
            'personal_info': [], 'summary_objective': [], 'education': [], 'experience': [],
            'skills': [], 'projects': [], 'awards_honors': [], 'publications': [],
            'certifications': [], 'interests': [], 'references': [], 'other': []
        }
        
        lines = text.split('\n')
        current_section_key: Optional[str] = 'personal_info'
        current_content: List[str] = []
        
        section_keywords = {
            'summary_objective': ['summary', 'objective', 'profile', 'about me'],
            'education': ['education', 'academic background', 'qualifications', 'educational background',
                          'academic history', 'degrees', 'training', 'certifications and education', 'university', 'college', 'institutions'],
            'experience': ['experience', 'work experience', 'employment history', 'professional experience', 'job history', 'career history'],
            'skills': ['skills', 'technical skills', 'core competencies', 'proficiencies', 'technologies', 'abilities', 'technical expertise'],
            'projects': ['projects', 'portfolio', 'personal projects', 'key projects'],
            'awards_honors': ['awards', 'honors', 'achievements'],
            'publications': ['publications', 'research'],
            'certifications': ['certifications', 'licenses', 'certifications and licenses'],
            'interests': ['interests', 'hobbies'],
            'references': ['references']
        }
        
        header_pattern = r'^\s*(' + '|'.join(
            [re.escape(k) for sublist in section_keywords.values() for k in sublist]
        ) + r')\s*$'

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped: continue

            is_potential_header = False
            if (len(line_stripped) < 50 and line_stripped.isupper()) or re.search(header_pattern, line_stripped, re.IGNORECASE):
                for section, keywords in section_keywords.items():
                    if any(re.search(r'\b' + re.escape(keyword) + r'\b', line_stripped.lower()) for keyword in keywords):
                        if current_section_key and current_content:
                            sections[current_section_key].append('\n'.join(current_content).strip())
                        
                        current_section_key = section
                        current_content = []
                        is_potential_header = True
                        break
            
            if not is_potential_header:
                if current_section_key:
                    current_content.append(line_stripped)
                else:
                    sections['personal_info'].append(line_stripped)

        if current_section_key and current_content:
            sections[current_section_key].append('\n'.join(current_content).strip())
        
        cleaned_sections: Dict[str, List[str]] = {}
        for section_name, content_list in sections.items():
            filtered_content = [c for c in content_list if c.strip()]
            if filtered_content:
                cleaned_sections[section_name] = filtered_content
        
        return cleaned_sections

    def extract_structured_experience(self, experience_text: List[str]) -> List[Dict[str, Optional[str]]]:
        """Extracts structured work experience entries."""
        extracted_experiences: List[Dict[str, Optional[str]]] = []
        total_years_experience = 0.0

        month_abbr = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        year_pattern = r'(?:20\d{2}|19\d{2})'
        date_format = rf'(?:{month_abbr}\.?\s*)?{year_pattern}'
        date_range_pattern = rf'({date_format}\s*[\-–]\s*(?:{date_format}|Present|Current|Now))'
        
        title_company_pattern_1 = r'^\s*(.+?)\s*at\s*(.+?)\s*$'
        title_company_pattern_2 = r'^\s*(.+?)\s*,\s*(.+?)\s*$'
        company_pattern = r'\b(?:Inc|Ltd|Corp|Co|Group|LLC|LLP|GmbH|S\.?A\.?|Pvt\.?|Ltd\.?)\b'

        for block in experience_text:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            current_experience = {'title': None, 'company': None, 'start_date': None, 'end_date': None, 'description': []}
            block_temp = block
            date_match = re.search(date_range_pattern, block_temp, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1)
                dates = re.split(r'[\-–]', date_str)
                current_experience['start_date'] = dates[0].strip() if dates else None
                current_experience['end_date'] = dates[1].strip() if len(dates) > 1 else None
                block_temp = block_temp.replace(date_str, '').strip()
                lines = [line.strip() for line in block_temp.split('\n') if line.strip()]
                start_year = re.search(year_pattern, current_experience['start_date'] or '')
                if 'present' in (current_experience['end_date'] or '').lower():
                    end_year = datetime.now().year
                else:
                    end_year_match = re.search(year_pattern, current_experience['end_date'] or '')
                    end_year = int(end_year_match.group(0)) if end_year_match else None
                if start_year and end_year:
                    total_years_experience += (end_year - int(start_year.group(0)))
            
            header_lines = lines[:3]
            description_lines = lines[3:]
            for line in header_lines:
                comp_title_match = re.search(title_company_pattern_1, line, re.IGNORECASE)
                if comp_title_match:
                    current_experience['title'] = comp_title_match.group(1).strip()
                    current_experience['company'] = comp_title_match.group(2).strip()
                    continue
                comp_title_match_2 = re.search(title_company_pattern_2, line, re.IGNORECASE)
                if comp_title_match_2:
                    part1, part2 = comp_title_match_2.group(1).strip(), comp_title_match_2.group(2).strip()
                    current_experience['company'], current_experience['title'] = (part1, part2) if re.search(company_pattern, part1, re.IGNORECASE) or len(part1.split()) < 3 else (part2, part1)
                    continue
                if not date_match or date_str not in line:
                    current_experience['description'].append(line)
            current_experience['description'].extend(description_lines)
            current_experience['description'] = '\n'.join(current_experience['description']).strip() or None
            if current_experience['title'] or current_experience['company']:
                extracted_experiences.append(current_experience)
        
        return extracted_experiences, int(total_years_experience)

    def extract_structured_education(self, education_text: List[str]) -> List[Dict[str, Optional[str]]]:
        """Extracts structured educational qualification entries."""
        extracted_education: List[Dict[str, Optional[str]]] = []
        degree_pattern = r'\b(?:B\.?S\.?|M\.?S\.?c?\.?|Ph\.?D\.?|B\.?Tech|Bachelor(?:s)?(?: of \w+)?|Master(?:s)?(?: of \w+)?|Doctor(?:ate)?(?: of \w+)?|Diploma|Certificate|Degree)\b'
        major_pattern = r'(?:in|of)\s+([A-Za-z\s&,.\-]+?)(?:\s*(?:degree|major|engineering|science|arts|technology|studies|management|program)\b)?'
        institution_pattern = r'\b(?:University|Institute|College|School|Academy|Polytechnic|Vidyalaya|Mahavidyalaya)\b[\w\s,.-]+'
        year_pattern = r'(?:20\d{2}|19\d{2})'
        date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s*' + year_pattern + r'|Present|Current'
        year_of_passing_pattern = r'(?:Year of Passing|Graduation Year|Passing Year)\s*[:\-\—]?\s*(' + year_pattern + r')'

        full_education_block_text = "\n".join(education_text)
        entry_separator_pattern = re.compile(r'\n(?=\s*(?:' + degree_pattern + r'|' + year_pattern + r'|' + institution_pattern + r'|' + r'\"Qualifying Degree\"' + r'))', re.IGNORECASE)
        potential_entries = entry_separator_pattern.split(full_education_block_text)
        if len(potential_entries) <= 1 and '\n' in full_education_block_text:
            potential_entries = full_education_block_text.split('\n')
        potential_entries = [re.sub(r',,+', ',', entry.strip()) for entry in potential_entries if entry.strip() and len(entry.strip()) > 5]

        for block in potential_entries:
            current_education = {'degree': None, 'major': None, 'institution': None, 'graduation_date': None}
            block_temp = block
            grad_date_match = re.search(year_of_passing_pattern, block_temp, re.IGNORECASE)
            if grad_date_match:
                current_education['graduation_date'] = grad_date_match.group(1).strip()
                block_temp = block_temp.replace(grad_date_match.group(0), '').strip()
            else:
                date_match = re.search(date_pattern, block_temp, re.IGNORECASE)
                if date_match:
                    current_education['graduation_date'] = date_match.group(0).strip()
                    block_temp = block_temp.replace(date_match.group(0), '').strip()
            degree_match = re.search(degree_pattern, block_temp, re.IGNORECASE)
            if degree_match:
                current_education['degree'] = degree_match.group(0).strip()
                block_temp = block_temp.replace(degree_match.group(0), '').strip()
            major_match = re.search(major_pattern, block_temp, re.IGNORECASE)
            if major_match:
                current_education['major'] = major_match.group(1).strip()
                block_temp = block_temp.replace(major_match.group(0), '').strip()
            institution_match = re.search(institution_pattern, block_temp, re.IGNORECASE)
            if institution_match:
                current_education['institution'] = institution_match.group(0).strip()
            else:
                remaining_text = block_temp.strip()
                if remaining_text and len(remaining_text.split()) < 15 and any(kw in remaining_text.lower() for kw in ['university', 'institute', 'college', 'school', 'maulana abul kalam azad', 'board']):
                    current_education['institution'] = remaining_text
            if any(current_education.values()):
                for key, val in current_education.items():
                    if val:
                        current_education[key] = re.sub(r'[^\w\s\.]', '', val).strip()
                extracted_education.append(current_education)
        return extracted_education

    def parse_resume(self, raw_text: str) -> Dict[str, Any]:
        """Parses the raw text of a resume to extract structured information."""
        cleaned_text = self._clean_text(raw_text)
        sections = self.extract_sections(cleaned_text)
        contact_info = self.extract_contact_info(cleaned_text)
        
        experience_entries, total_years_experience = self.extract_structured_experience(sections.get('experience', []))
        education_entries = self.extract_structured_education(sections.get('education', []))

        parsed_data = {
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "contact_info": contact_info,
            "sections": sections,
            "extracted_skills": [],
            "experience": experience_entries,
            "total_years_experience": total_years_experience,
            "education": education_entries,
        }
        return parsed_data