# backend/resume_parser.py

import os
import re
from pathlib import Path
from typing import List, Dict, Any

# Text extraction libraries
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

class ResumeParser:
    def __init__(self):
        pass
    
    def extract_text(self, file_path: str) -> str:
        """
        Extracts plain text from various resume file formats (.pdf, .docx, .txt).
        Includes fallback to textract for broader compatibility if available.

        Args:
            file_path (str): The path to the resume file.

        Returns:
            str: The extracted and cleaned text content of the resume, or an empty string if extraction fails.
        """
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
                # Fallback to textract for other formats or if specific parsers fail
                print(f"Unsupported extension '{file_extension}' or attempting fallback for {file_path}. Using textract if available.")
                extracted_text = self._extract_with_textract(file_path)
        except Exception as e:
            # Catch any unexpected errors during format-specific extraction
            print(f"Error during initial text extraction from {file_path} with {file_extension} parser: {e}")
            # Try textract as a final fallback if initial attempt fails
            try:
                extracted_text = self._extract_with_textract(file_path)
            except Exception as textract_e:
                print(f"Textract fallback also failed for {file_path}: {textract_e}")
                extracted_text = "" # Ensure empty string on complete failure

        return self._clean_text(extracted_text) # Always clean the text before returning

    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extracts text from PDF files using pdfminer.six.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            str: Extracted text.
        """
        try:
            # pdfminer.six's extract_text is generally robust
            text = pdf_extract_text(file_path)
            return text
        except Exception as e:
            print(f"PDF extraction error for {file_path}: {e}")
            return ""
    
    def _extract_from_docx(self, file_path: str) -> str:
        """
        Extracts text from DOCX files using python-docx.
        Includes text from paragraphs and tables.

        Args:
            file_path (str): Path to the DOCX file.

        Returns:
            str: Extracted text.
        """
        try:
            doc = Document(file_path)
            full_text = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text)
            
            # Extract text from tables
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
        """
        Extracts text from TXT files.

        Args:
            file_path (str): Path to the TXT file.

        Returns:
            str: Extracted text.
        """
        try:
            # Use 'utf-8' with error handling for broader compatibility
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
            return text
        except Exception as e:
            print(f"TXT extraction error for {file_path}: {e}")
            return ""
    
    def _extract_with_textract(self, file_path: str) -> str:
        """
        Fallback text extraction using the textract library, if available.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: Extracted text, or empty string if textract is not available or extraction fails.
        """
        if not TEXTRACT_AVAILABLE:
            print(f"Textract is not available. Skipping extraction for {file_path}.")
            return ""
        
        try:
            # textract might require external dependencies (e.g., antiword for .doc)
            # Ensure these are handled in your environment setup.
            text = textract.process(file_path).decode('utf-8')
            return text
        except Exception as e:
            print(f"Textract extraction error for {file_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Cleans and normalizes extracted text for better NLP processing.
        Removes excessive whitespace, special characters, and normalizes line breaks.

        Args:
            text (str): The raw extracted text.

        Returns:
            str: Cleaned text.
        """
        if not text:
            return ""
        
        # Replace common non-breaking spaces and similar characters
        text = text.replace('\xa0', ' ').replace('\u2022', ' ').replace('\u2013', '-')
        
        # Convert multiple newlines/tabs to single spaces
        text = re.sub(r'[\n\t\r]+', ' ', text)
        
        # Remove non-alphanumeric characters but keep common punctuation for skills/urls
        # Kept: letters, numbers, spaces, @ . - + # ( ) / :
        text = re.sub(r'[^\w\s@.\-+#()/:]', '', text)
        
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts common contact information (emails, phones, LinkedIn, GitHub) from resume text.

        Args:
            text (str): The resume's raw text.

        Returns:
            Dict[str, List[str]]: Dictionary containing lists of extracted contact details.
        """
        contact_info: Dict[str, List[str]] = {
            'emails': [],
            'phones': [],
            'linkedin': [],
            'github': []
        }
        
        # Email extraction (more robust pattern)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        contact_info['emails'] = list(set(re.findall(email_pattern, text, re.IGNORECASE)))
        
        # Phone extraction (more flexible pattern for various formats)
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        raw_phones = re.findall(phone_pattern, text)
        contact_info['phones'] = list(set([p.strip() for p in raw_phones if len(re.sub(r'\D', '', p)) >= 10]))
        
        # LinkedIn extraction
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        contact_info['linkedin'] = list(set([match.strip() for match in linkedin_matches]))
        
        # GitHub extraction
        github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+/?'
        github_matches = re.findall(github_pattern, text, re.IGNORECASE)
        contact_info['github'] = list(set([match.strip() for match in github_matches]))
        
        return contact_info
    
    def extract_sections(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts different logical sections (e.g., education, experience, skills) from resume text.
        This is a heuristic-based approach and may vary in accuracy depending on resume format.

        Args:
            text (str): The cleaned resume text.

        Returns:
            Dict[str, List[str]]: A dictionary where keys are section names and values are lists of content.
        """
        sections: Dict[str, List[str]] = {
            'personal_info': [],
            'summary_objective': [],
            'education': [],
            'experience': [],
            'skills': [],
            'projects': [],
            'awards_honors': [],
            'publications': [],
            'certifications': [],
            'interests': [],
            'references': [],
            'other': []
        }
        
        lines = text.split('\n')
        current_section_key: Optional[str] = 'personal_info'
        current_content: List[str] = []
        
        section_keywords = {
            'summary_objective': ['summary', 'objective', 'profile', 'about me'],
            'education': ['education', 'academic background', 'qualifications'],
            'experience': ['experience', 'work experience', 'employment history', 'professional experience', 'job history'],
            'skills': ['skills', 'technical skills', 'core competencies', 'proficiencies', 'technologies', 'abilities'],
            'projects': ['projects', 'portfolio', 'personal projects', 'key projects'],
            'awards_honors': ['awards', 'honors', 'achievements'],
            'publications': ['publications', 'research'],
            'certifications': ['certifications', 'licenses'],
            'interests': ['interests', 'hobbies'],
            'references': ['references']
        }
        
        header_pattern = r'^\s*(' + '|'.join(
            [re.escape(k) for sublist in section_keywords.values() for k in sublist]
        ) + r')\s*$'

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            is_potential_header = False
            if len(line_stripped) < 50 and line_stripped.isupper() or re.search(header_pattern, line_stripped, re.IGNORECASE):
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

