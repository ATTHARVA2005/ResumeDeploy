# backend/skill_extractor.py

import json
import re
from typing import List, Dict, Set, Any, Optional # ADDED: Optional
from pathlib import Path

import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer

class SkillExtractor:
    def __init__(self):
        self.stop_words = set()
        self.nlp = None
        self.skills_db: Dict[str, List[str]] = {}

        self.setup_nltk()
        self.setup_spacy()
        self.load_skills_database()

        self.skills_db_lower_sets: Dict[str, Set[str]] = {
            category: {skill.lower() for skill in skills}
            for category, skills in self.skills_db.items()
        }
        self.all_known_skills_lower: Set[str] = set()
        for skills_set in self.skills_db_lower_sets.values():
            self.all_known_skills_lower.update(skills_set)
        
    def setup_nltk(self):
        """
        Downloads required NLTK data (punkt tokenizer and stopwords) if not present.
        Initializes stop_words set.
        """
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("NLTK 'punkt' tokenizer not found. Downloading...")
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            print("NLTK 'stopwords' corpus not found. Downloading...")
            nltk.download('stopwords', quiet=True)
        
        self.stop_words = set(stopwords.words('english'))
        print("NLTK setup complete.")
    
    def setup_spacy(self):
        """
        Loads the Spacy English small model ('en_core_web_sm').
        Provides instructions if the model is not found.
        """
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("Spacy 'en_core_web_sm' model loaded.")
        except OSError:
            print("\nSpacy English model 'en_core_web_sm' not found.")
            print("Please install it by running the following command in your terminal:")
            print("python -m spacy download en_core_web_sm")
            print("Skill extraction via NLP will be limited without this model.")
            self.nlp = None
    
    def load_skills_database(self):
        """
        Loads the skills database from 'data/skills_database.json'.
        If the file doesn't exist or an error occurs, it creates a default database.
        """
        skills_path = Path("data/skills_database.json")
        try:
            if skills_path.exists():
                with open(skills_path, 'r', encoding='utf-8') as file:
                    self.skills_db = json.load(file)
                print(f"Skills database loaded from {skills_path}.")
            else:
                print(f"Skills database file not found at {skills_path}. Creating default...")
                self._create_default_skills_db()
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {skills_path}. File might be corrupted. Creating default...")
            self._create_default_skills_db()
        except Exception as e:
            print(f"Unexpected error loading skills database: {e}. Creating default...")
            self._create_default_skills_db()
        
        if not self.skills_db:
            print("Warning: Skills database is empty after loading/creation. Skill extraction may be ineffective.")
            self._create_default_skills_db()

    def _create_default_skills_db(self):
        """
        Creates a default skills database and saves it to 'data/skills_database.json'.
        This is a fallback if the file is missing or corrupted.
        """
        self.skills_db = {
            "programming_languages": [
                "python", "java", "javascript", "c++", "c#", "c", "php", "ruby", "go", "rust",
                "kotlin", "swift", "typescript", "scala", "r", "matlab", "perl", "shell", "bash",
                "html", "css", "sql"
            ],
            "web_technologies": [
                "react", "angular", "vue", "node.js", "express", "django", "flask",
                "spring", "bootstrap", "jquery", "sass", "webpack", "babel", "redux", "next.js",
                "rest api", "graphql", "websocket", "ajax", "json", "xml", "html5", "css3", "tailwind css", "material-ui", "typescript"
            ],
            "databases": [
                "mysql", "postgresql", "mongodb", "sqlite", "redis", "cassandra", "oracle",
                "dynamodb", "elasticsearch", "neo4j", "firebase", "mariadb", "couchbase", "h2 database"
            ],
            "frameworks": [
                "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "opencv", "keras",
                "spring boot", "laravel", "codeigniter", "rails", "asp.net", "xamarin", "flutter",
                "apache spark", "hadoop", "kafka", "airflow", "dask", "databricks"
            ],
            "cloud_platforms": [
                "aws", "azure", "gcp", "google cloud", "heroku", "digitalocean", "vercel", "netlify",
                "cloudflare", "docker", "kubernetes", "jenkins", "gitlab", "github actions", "terraform",
                "ansible", "chef", "puppet", "azure devops", "google kubernetes engine", "amazon ec2", "s3"
            ],
            "devops_tools": [
                "git", "jira", "confluence", "slack", "trello", "postman", "figma", "photoshop",
                "illustrator", "tableau", "power bi", "excel", "word", "powerpoint", "visio",
                "jenkins", "travis ci", "circleci", "sonarqube", "nagios", "grafana", "prometheus"
            ],
            "operating_systems": [
                "linux", "windows", "macos", "unix", "ubuntu", "centos", "redhat"
            ],
            "soft_skills": [
                "leadership", "teamwork", "communication", "problem solving", "analytical thinking",
                "project management", "agile", "scrum", "collaboration", "mentoring", "training",
                "adaptability", "critical thinking", "creativity", "time management", "negotiation",
                "conflict resolution", "presentation skills", "interpersonal skills"
            ],
            "data_science_ml": [
                "machine learning", "deep learning", "data analysis", "data visualization", "statistical modeling",
                "natural language processing", "computer vision", "predictive modeling", "feature engineering",
                "model deployment", "a/b testing", "big data", "data warehousing", "etl"
            ],
            "testing_qa": [
                "unit testing", "integration testing", "end-to-end testing", "qa automation", "selenium",
                "jmeter", "load testing", "performance testing", "test plans", "test cases", "bug tracking"
            ],
            "security": [
                "cybersecurity", "network security", "data encryption", "vulnerability assessment",
                "penetration testing", "firewalls", "identity and access management", "security audits"
            ]
        }
        Path("data").mkdir(parents=True, exist_ok=True)
        try:
            with open(Path("data/skills_database.json"), 'w', encoding='utf-8') as f:
                json.dump(self.skills_db, f, indent=4)
            print("Default skills_database.json created and saved.")
        except Exception as e:
            print(f"Error saving default skills database: {e}")

        self.skills_db_lower_sets = {
            category: {skill.lower() for skill in skills}
            for category, skills in self.skills_db.items()
        }
        self.all_known_skills_lower = set()
        for skills_set in self.skills_db_lower_sets.values():
            self.all_known_skills_lower.update(skills_set)

    def extract_skills(self, text: str) -> List[str]:
        """
        Extracts skills from text using multiple approaches:
        1. Direct matching with a predefined skills database.
        2. Fuzzy matching for slight variations.
        3. NLP-based extraction using Spacy (Named Entities, Noun Chunks).
        4. Pattern-based extraction using regex.

        Args:
            text (str): The input text (e.g., resume content, job description).

        Returns:
            List[str]: A sorted list of unique, cleaned, and validated skills.
        """
        if not text or not self.all_known_skills_lower:
            return []
        
        text_lower = text.lower()
        found_skills = set()
        
        found_skills.update(self._extract_by_direct_match(text_lower))
        found_skills.update(self._find_fuzzy_matches(text_lower)) 
        
        if self.nlp:
            found_skills.update(self._extract_by_nlp(text))
        
        found_skills.update(self._extract_by_patterns(text))
        
        cleaned_and_validated_skills = self._clean_and_validate_skills(found_skills)
        
        return sorted(list(cleaned_and_validated_skills))
    
    def _extract_by_direct_match(self, text_lower: str) -> Set[str]:
        """Extracts skills by direct string matching (case-insensitive)."""
        found_skills = set()
        for skill_set in self.skills_db_lower_sets.values():
            for skill_in_db in skill_set:
                pattern = r'\b' + re.escape(skill_in_db) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(skill_in_db)
        return found_skills
    
    def _find_fuzzy_matches(self, text_lower: str, threshold: int = 85) -> Set[str]:
        """Extracts skills using fuzzy string matching (fuzzywuzzy)."""
        found_skills = set()
        words = [word for word in word_tokenize(text_lower) if word.isalnum() and word not in self.stop_words]
        
        text_ngrams = set(words)
        for i in range(len(words) - 1):
            text_ngrams.add(f"{words[i]} {words[i + 1]}")
        for i in range(len(words) - 2):
            text_ngrams.add(f"{words[i]} {words[i + 1]} {words[i + 2]}")
        
        for text_ngram in text_ngrams:
            for skill_in_db in self.all_known_skills_lower:
                if text_ngram == skill_in_db: continue
                ratio = fuzz.ratio(text_ngram, skill_in_db)
                if ratio >= threshold:
                    found_skills.add(skill_in_db)
        return found_skills
    
    def _extract_by_nlp(self, text: str) -> Set[str]:
        """Extracts skills using Spacy's Named Entity Recognition (NER) and Noun Chunks."""
        found_skills = set()
        if not self.nlp: return found_skills
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'LANGUAGE', 'GPE', 'LOC']:
                skill_candidate = ent.text.lower().strip()
                if self._is_valid_skill(skill_candidate):
                    found_skills.add(skill_candidate)
        
        for chunk in doc.noun_chunks:
            skill_candidate = chunk.text.lower().strip()
            if 2 <= len(skill_candidate.split()) <= 4:
                if self._is_valid_skill(skill_candidate):
                    found_skills.add(skill_candidate)
        return found_skills
    
    def _extract_by_patterns(self, text: str) -> Set[str]:
        """Extracts skills using predefined regex patterns."""
        found_skills = set()
        patterns = [
            r'(?:skills|technologies|proficiencies|tools|languages|frameworks|expertise|knowledge|experience)\s*[:\-\—]?\s*([a-zA-Z0-9,\s\/\-\.#+&]+)',
            r'(?:proficient|expert|experienced|skilled|familiar)\s+(?:in|with)\s+([a-zA-Z0-9,\s\/\-\.#+&]+)',
            r'\b(?:using|developed|implemented|worked with)\s+([a-zA-Z0-9,\s\/\-\.#+&]+)',
            r'\b(?:strong|solid)\s+(?:understanding|grasp)?\s*(?:of|in|with)?\s*([a-zA-Z0-9,\s\/\-\.#+&]+)'
        ]
        combined_pattern = '|'.join(f'(?:{p})' for p in patterns)
        matches = re.finditer(combined_pattern, text, re.IGNORECASE)
        
        for match in matches:
            for i in range(1, len(match.groups()) + 1):
                skill_group_text = match.group(i)
                if skill_group_text:
                    skills_candidates = re.split(r'[,;|/&]|\band\b|\bor\b', skill_group_text)
                    for skill_candidate in skills_candidates:
                        skill = skill_candidate.strip().lower()
                        if skill and len(skill) > 1 and self._is_valid_skill(skill):
                            found_skills.add(skill)
        return found_skills
    
    def _is_valid_skill(self, candidate: str) -> bool:
        """Internal helper to check if a candidate string is a valid skill."""
        candidate = candidate.strip()
        if len(candidate) < 2 or len(candidate) > 50: return False
        if candidate in self.stop_words: return False
        if re.fullmatch(r'[\d\W_]+', candidate): return False
        if candidate in self.all_known_skills_lower: return True
        for known_skill in self.all_known_skills_lower:
            if fuzz.ratio(candidate, known_skill) > 80: return True
        return False
    
    def _clean_and_validate_skills(self, skills: Set[str]) -> Set[str]:
        """Performs a final cleaning and validation pass on extracted skills."""
        cleaned_skills = set()
        non_skill_words = self.stop_words.union({
            'experience', 'knowledge', 'skills', 'tools', 'technologies', 
            'languages', 'frameworks', 'proficient', 'expert', 'skilled',
            'ability', 'abilities', 'understanding', 'familiarity', 'strong', 'solid',
            'excellent', 'good', 'basic', 'advanced', 'intermediate', 'senior', 'junior',
            'developer', 'engineer', 'analyst', 'manager', 'specialist', 'architect',
            'systems', 'software', 'data', 'web', 'mobile', 'cloud', 'security', 'network',
            'design', 'development', 'management', 'analysis', 'testing', 'operations',
            'solutions', 'platform', 'platforms', 'system', 'systems', 'application', 'applications',
            'environment', 'environments', 'concepts', 'principles', 'practices', 'methodologies',
            'methodology', 'framework', 'library', 'libraries', 'api', 'apis', 'database', 'databases',
            'server', 'servers', 'client', 'clients', 'service', 'services', 'tool', 'product', 'products',
            'solution', 'solutions', 'process', 'processes', 'workflow', 'workflows', 'project', 'projects',
            'team', 'teams', 'work', 'working', 'build', 'building', 'create', 'creating', 'implement',
            'implementing', 'designing', 'develop', 'developing', 'manage', 'managing', 'test', 'testing',
            'analyze', 'analyzing', 'optimize', 'optimizing', 'automate', 'automating', 'deploy', 'deploying',
            'troubleshoot', 'troubleshooting', 'support', 'supporting', 'maintain', 'maintaining',
            'collaborate', 'collaborating', 'communicate', 'communicating', 'present', 'presenting',
            'resolve', 'resolving', 'lead', 'leading', 'mentor', 'mentoring', 'train', 'training',
            'research', 'researching', 'document', 'documenting', 'configure', 'configuring',
            'integrate', 'integrating', 'monitor', 'monitoring', 'debug', 'debugging', 'deployments',
            'version control', 'source control', 'problem-solving', 'critical thinking', 'time management'
        })
        
        for skill in skills:
            skill = skill.strip()
            if not skill or len(skill) < 2: continue
            words_in_skill = skill.split()
            filtered_words = [word for word in words_in_skill if word not in non_skill_words]
            skill = ' '.join(filtered_words).strip()
            if not skill: continue
            if self._is_valid_skill(skill):
                cleaned_skills.add(skill)
        return cleaned_skills
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorizes a list of skills into predefined categories."""
        categorized: Dict[str, List[str]] = {category: [] for category in self.skills_db.keys()}
        categorized['other'] = []
        
        for skill in skills:
            skill_lower = skill.lower()
            found_category = False
            for category, skills_set in self.skills_db_lower_sets.items():
                if skill_lower in skills_set:
                    categorized[category].append(skill)
                    found_category = True
                    break
            if not found_category:
                categorized['other'].append(skill)
        return {k: v for k, v in categorized.items() if v or (k == 'other' and v)}
    
    def get_skill_relevance_score(self, skill: str, context: str) -> float:
        """Calculates a relevance score for a skill within a given text context."""
        if not context: return 0.0
        context_lower = context.lower()
        skill_lower = skill.lower()
        occurrences = len(re.findall(r'\b' + re.escape(skill_lower) + r'\b', context_lower))
        total_words = len(context_lower.split())
        term_frequency = occurrences / total_words if total_words > 0 else 0.0
        context_boost = 1.0
        if re.search(r'\b(?:expert|proficient|advanced|mastery)\s+(?:in|with)\s+' + re.escape(skill_lower), context_lower):
            context_boost = 2.0
        elif re.search(r'\b(?:experienced|skilled|familiar)\s+(?:in|with)?\s*' + re.escape(skill_lower), context_lower):
            context_boost = 1.5
        base_score = term_frequency * 50.0
        final_score = base_score * context_boost
        return min(final_score, 100.0)

    def extract_structured_experience(self, experience_text: List[str]) -> List[Dict[str, Optional[str]]]:
        """
        Extracts structured work experience entries from a list of experience text blocks.
        Also attempts to calculate total years of experience.
        """
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
            current_experience = {
                'title': None,
                'company': None,
                'start_date': None,
                'end_date': None,
                'description': []
            }
            
            block_temp = block 

            date_match = re.search(date_range_pattern, block_temp, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1)
                dates = re.split(r'[\-–]', date_str)
                current_experience['start_date'] = dates[0].strip() if dates else None
                current_experience['end_date'] = dates[1].strip() if len(dates) > 1 else None
                block_temp = block_temp.replace(date_str, '').strip()
                lines = [line.strip() for line in block_temp.split('\n') if line.strip()]

                start_year = None
                end_year = None
                
                start_year_match = re.search(year_pattern, current_experience['start_date'] or '')
                if start_year_match:
                    start_year = int(start_year_match.group(0))
                
                if current_experience['end_date'] and current_experience['end_date'].lower() == 'present':
                    end_year = datetime.now().year
                else:
                    end_year_match = re.search(year_pattern, current_experience['end_date'] or '')
                    if end_year_match:
                        end_year = int(end_year_match.group(0))
                
                if start_year and end_year:
                    total_years_experience += (end_year - start_year)
            
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
                    part1 = comp_title_match_2.group(1).strip()
                    part2 = comp_title_match_2.group(2).strip()
                    
                    if re.search(company_pattern, part1, re.IGNORECASE) or len(part1.split()) < 3:
                         current_experience['company'] = part1
                         current_experience['title'] = part2
                    else:
                         current_experience['title'] = part1
                         current_experience['company'] = part2
                    continue

                if not date_match or date_str not in line:
                    current_experience['description'].append(line)

            current_experience['description'].extend(description_lines)
            
            current_experience['description'] = '\n'.join(current_experience['description']).strip() if current_experience['description'] else None
            
            if current_experience['title'] or current_experience['company']:
                extracted_experiences.append(current_experience)
        
        return extracted_experiences, int(total_years_experience)

    def extract_structured_education(self, education_text: List[str]) -> List[Dict[str, Optional[str]]]:
        """
        Extracts structured educational qualification entries from a list of education text blocks.
        This version is more robust for tabular/multi-line entries.
        """
        extracted_education: List[Dict[str, Optional[str]]] = []
        
        # Define patterns locally within the method
        degree_pattern = r'\b(?:B\.?S\.?|M\.?S\.?c?\.?|Ph\.?D\.?|B\.?Tech|Bachelor(?:s)?(?: of \w+)?|Master(?:s)?(?: of \w+)?|Doctor(?:ate)?(?: of \w+)?|Diploma|Certificate|Degree|X(?:I{1,2})?th)\b'
        major_pattern = r'(?:in|of)\s+([A-Za-z\s&,.\-]+?)(?:\s*(?:degree|major|engineering|science|arts|technology|studies|management|program)\b)?'
        institution_pattern = r'\b(?:University|Institute|College|School|Academy|Polytechnic|Vidyalaya|Mahavidyalaya|Board)\b[\w\s,.-]+'
        year_pattern = r'(?:20\d{2}|19\d{2})'
        date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\.?\s*' + year_pattern + r'|Present|Current'
        year_of_passing_pattern = r'(?:Year of Passing|Graduation Year|Passing Year)\s*[:\-\—]?\s*(' + year_pattern + r')'

        full_education_block_text = "\n".join(education_text)
        
        # Split the entire education block into potential individual entries
        entry_separator_pattern = re.compile(
            r'\n(?=\s*(?:' + degree_pattern + r'|' + year_pattern + r'|' + institution_pattern + r'|' + r'\"Qualifying Degree\"' + r'))',
            re.IGNORECASE
        )
        potential_entries = entry_separator_pattern.split(full_education_block_text)
        
        if len(potential_entries) <= 1 and '\n' in full_education_block_text:
            potential_entries = full_education_block_text.split('\n')
        
        potential_entries = [re.sub(r',,+', ',', entry.strip()) for entry in potential_entries if entry.strip()]
        potential_entries = [entry for entry in potential_entries if entry and len(entry.strip()) > 5]

        combined_entries = []
        current_combined_block = []
        for i, entry_line in enumerate(potential_entries):
            is_new_entry_start = re.search(degree_pattern, entry_line, re.IGNORECASE) or \
                                 re.search(year_pattern, entry_line, re.IGNORECASE) or \
                                 re.search(institution_pattern, entry_line, re.IGNORECASE)
            
            if i > 0 and is_new_entry_start and current_combined_block:
                combined_entries.append(" ".join(current_combined_block))
                current_combined_block = [entry_line]
            else:
                current_combined_block.append(entry_line)
        if current_combined_block:
            combined_entries.append(" ".join(current_combined_block))

        for block in combined_entries:
            current_education = {
                'degree': None,
                'major': None,
                'institution': None,
                'graduation_date': None
            }
            
            block_temp = block
            
            # 1. Extract Graduation Date
            grad_date_match = re.search(year_of_passing_pattern, block_temp, re.IGNORECASE)
            if grad_date_match:
                current_education['graduation_date'] = grad_date_match.group(1).strip()
                block_temp = block_temp.replace(grad_date_match.group(0), '').strip()
            else:
                date_match = re.search(date_pattern, block_temp, re.IGNORECASE)
                if date_match:
                    current_education['graduation_date'] = date_match.group(0).strip()
                    block_temp = block_temp.replace(date_match.group(0), '').strip()

            # 2. Extract Degree
            degree_match = re.search(degree_pattern, block_temp, re.IGNORECASE)
            if degree_match:
                current_education['degree'] = degree_match.group(0).strip()
                block_temp = block_temp.replace(degree_match.group(0), '').strip()

            # 3. Extract Major (often near degree)
            major_match = re.search(major_pattern, block_temp, re.IGNORECASE)
            if major_match:
                current_education['major'] = major_match.group(1).strip()
                block_temp = block_temp.replace(major_match.group(0), '').strip()

            # 4. Extract Institution (what's left, or specific patterns)
            institution_match = re.search(institution_pattern, block_temp, re.IGNORECASE)
            if institution_match:
                current_education['institution'] = institution_match.group(0).strip()
            else:
                remaining_text = block_temp.strip()
                if remaining_text and len(remaining_text.split()) < 15 and \
                   any(kw in remaining_text.lower() for kw in ['university', 'institute', 'college', 'school', 'maulana abul kalam azad', 'board', 'council']): # Added 'council'
                    current_education['institution'] = remaining_text
            
            if current_education['degree'] or current_education['institution'] or current_education['graduation_date']:
                current_education['degree'] = re.sub(r'[^\w\s\.]', '', current_education['degree']).strip() if current_education['degree'] else None
                current_education['major'] = re.sub(r'[^\w\s]', '', current_education['major']).strip() if current_education['major'] else None
                current_education['institution'] = re.sub(r'[^\w\s\.]', '', current_education['institution']).strip() if current_education['institution'] else None

                extracted_education.append(current_education)
        
        return extracted_education

    def parse_resume(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses the raw text of a resume to extract structured information.
        Combines contact info, section extraction, and new structured experience/education.
        """
        cleaned_text = self._clean_text(raw_text)
        sections = self.extract_sections(cleaned_text)
        contact_info = self.extract_contact_info(cleaned_text)
        
        experience_entries, total_years_experience = self.extract_structured_experience(sections.get('experience', []))
        education_entries = self.extract_structured_education(sections.get('education', []))

        highest_education_level = None
        if education_entries:
            edu_levels = {
                "phd": 5, "doctorate": 5,
                "master": 4, "m.s": 4, "msc": 4,
                "bachelor": 3, "b.s": 3, "btech": 3,
                "associate": 2,
                "high school": 1,
                "diploma": 1, "certificate": 1,
                "x": 1, "xii": 1
            }
            
            max_level_val = 0
            for entry in education_entries:
                degree_text = entry.get('degree', '').lower()
                institution_text = entry.get('institution', '').lower()
                
                for level_name, level_val in edu_levels.items():
                    if level_name in degree_text:
                        if level_val > max_level_val:
                            max_level_val = level_val
                            highest_education_level = entry.get('degree')
                        break
                
                if not highest_education_level and ('x' in institution_text or 'xii' in institution_text):
                    if edu_levels.get('x', 0) > max_level_val:
                        max_level_val = edu_levels.get('x', 0)
                        highest_education_level = entry.get('degree') or entry.get('institution')

            if not highest_education_level and education_entries:
                highest_education_level = education_entries[0].get('degree') or education_entries[0].get('institution')
                if highest_education_level and len(highest_education_level.split()) > 5:
                    degree_match = re.search(r'\b(B\.?Tech|Bachelor|Master|PhD|Diploma|Certificate|X|XII)\b', highest_education_level, re.IGNORECASE)
                    if degree_match:
                        highest_education_level = degree_match.group(0)
                    else:
                        highest_education_level = None


        parsed_data = {
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "contact_info": contact_info,
            "sections": sections,
            "extracted_skills": [],
            "experience": experience_entries,
            "total_years_experience": total_years_experience,
            "education": education_entries,
            "highest_education_level": highest_education_level,
        }
        return parsed_data

