# backend/skill_extractor.py

import json
import re
from typing import List, Dict, Set, Any
from pathlib import Path

import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from fuzzywuzzy import fuzz # Correctly imported and used
from sklearn.feature_extraction.text import TfidfVectorizer # Correctly imported and used

class SkillExtractor:
    def __init__(self):
        self.stop_words = set() # Initialize here, populated by setup_nltk
        self.nlp = None         # Initialize here, populated by setup_spacy
        self.skills_db: Dict[str, List[str]] = {} # Initialize with type hint

        self.setup_nltk()
        self.setup_spacy()
        self.load_skills_database()

        # Pre-process skills_db for faster lookups (convert to lowercased sets)
        self.skills_db_lower_sets: Dict[str, Set[str]] = {
            category: {skill.lower() for skill in skills}
            for category, skills in self.skills_db.items()
        }
        # Create a flat set of all known skills (lowercased) for quick lookups
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
            nltk.download('punkt', quiet=True) # quiet=True to suppress verbose output
        
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
                self._create_default_skills_db() # Call private method
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {skills_path}. File might be corrupted. Creating default...")
            self._create_default_skills_db()
        except Exception as e:
            print(f"Unexpected error loading skills database: {e}. Creating default...")
            self._create_default_skills_db()
        
        if not self.skills_db: # Fallback if default creation also fails or is empty
            print("Warning: Skills database is empty after loading/creation. Skill extraction may be ineffective.")
            self._create_default_skills_db() # Ensure it's not empty

    def _create_default_skills_db(self):
        """
        Creates a default skills database and saves it to 'data/skills_database.json'.
        This is a fallback if the file is missing or corrupted.
        """
        self.skills_db = {
            "programming_languages": [
                "python", "java", "javascript", "c++", "c#", "c", "php", "ruby", "go", "rust",
                "kotlin", "swift", "typescript", "scala", "r", "matlab", "perl", "shell", "bash",
                "html", "css", "sql" # Added SQL here as it's often a language
            ],
            "web_technologies": [
                "react", "angular", "vue", "node.js", "express", "django", "flask",
                "spring", "bootstrap", "jquery", "sass", "webpack", "babel", "redux", "next.js",
                "rest api", "graphql", "websocket", "ajax", "json", "xml", "html5", "css3",
                "tailwind css", "material-ui", "typescript" # TS can be here too
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
            "devops_tools": [ # Renamed from "tools" for better clarity
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
        # Ensure the data directory exists before writing
        Path("data").mkdir(parents=True, exist_ok=True)
        try:
            with open(Path("data/skills_database.json"), 'w', encoding='utf-8') as f:
                json.dump(self.skills_db, f, indent=4)
            print("Default skills_database.json created and saved.")
        except Exception as e:
            print(f"Error saving default skills database: {e}")

        # Re-initialize the lowercased sets after creating/loading new skills_db
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
        
        # Method 1: Direct matching with skills database
        found_skills.update(self._extract_by_direct_match(text_lower))
        
        # Method 2: Fuzzy matching for slight variations
        found_skills.update(self._extract_by_fuzzy_match(text_lower))
        
        # Method 3: NLP-based extraction using Spacy
        if self.nlp: # Only run if Spacy model was loaded successfully
            found_skills.update(self._extract_by_nlp(text)) # Pass original text to NLP
        
        # Method 4: Pattern-based extraction (can find skills not in DB but structured)
        found_skills.update(self._extract_by_patterns(text)) # Pass original text to patterns
        
        # Final cleaning and validation of all found skills
        cleaned_and_validated_skills = self._clean_and_validate_skills(found_skills)
        
        return sorted(list(cleaned_and_validated_skills))
    
    def _extract_by_direct_match(self, text_lower: str) -> Set[str]:
        """
        Extracts skills by direct string matching (case-insensitive) against the skills database.
        Ensures whole word matches using regex boundaries.

        Args:
            text_lower (str): The lowercased input text.

        Returns:
            Set[str]: A set of directly matched skills (lowercased).
        """
        found_skills = set()
        
        # Iterate through the pre-processed lowercased skill sets for efficiency
        for skill_set in self.skills_db_lower_sets.values():
            for skill_in_db in skill_set:
                # Use regex to ensure it's a whole word match, not just a substring
                # e.g., 'java' should not match 'javascript'
                pattern = r'\b' + re.escape(skill_in_db) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(skill_in_db)
        
        return found_skills
    
    def _extract_by_fuzzy_match(self, text_lower: str, threshold: int = 85) -> Set[str]:
        """
        Extracts skills using fuzzy string matching (fuzzywuzzy) against the skills database.
        Tokenizes text into words and n-grams for better matching.

        Args:
            text_lower (str): The lowercased input text.
            threshold (int): Minimum fuzzy ratio to consider a match (0-100).

        Returns:
            Set[str]: A set of fuzzily matched skills (lowercased).
        """
        found_skills = set()
        # Tokenize and generate n-grams from the input text
        words = [word for word in word_tokenize(text_lower) if word.isalnum() and word not in self.stop_words]
        
        # Create bigrams and trigrams for better matching
        text_ngrams = set()
        text_ngrams.update(words) # Add unigrams
        
        # Bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i + 1]}"
            text_ngrams.add(bigram)
        
        # Trigrams
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i + 1]} {words[i + 2]}"
            text_ngrams.add(trigram)
        
        # Compare extracted n-grams against all known skills in the database
        for text_ngram in text_ngrams:
            for skill_in_db in self.all_known_skills_lower:
                # Avoid re-matching exact matches if direct match already covered them
                if text_ngram == skill_in_db:
                    found_skills.add(skill_in_db)
                    continue

                ratio = fuzz.ratio(text_ngram, skill_in_db)
                if ratio >= threshold:
                    found_skills.add(skill_in_db)
        
        return found_skills
    
    def _extract_by_nlp(self, text: str) -> Set[str]:
        """
        Extracts skills using Spacy's Named Entity Recognition (NER) and Noun Chunks.
        Filters candidates against the known skills database.

        Args:
            text (str): The original input text (Spacy prefers original casing).

        Returns:
            Set[str]: A set of skills identified by NLP (lowercased).
        """
        found_skills = set()
        
        if not self.nlp:
            return found_skills
        
        doc = self.nlp(text)
        
        # Extract named entities that might represent skills
        for ent in doc.ents:
            # Common labels for tech/product/language skills
            if ent.label_ in ['ORG', 'PRODUCT', 'LANGUAGE', 'GPE', 'LOC']: # GPE/LOC for locations like 'London' if used as a skill context
                skill_candidate = ent.text.lower().strip()
                # Validate the candidate against our known skills
                if self._is_valid_skill(skill_candidate):
                    found_skills.add(skill_candidate)
        
        # Extract noun phrases that could be skills (e.g., "data analysis", "cloud computing")
        for chunk in doc.noun_chunks:
            skill_candidate = chunk.text.lower().strip()
            # Filter out very long phrases or short, common words
            if 2 <= len(skill_candidate.split()) <= 4: # Limit length for noun chunks
                if self._is_valid_skill(skill_candidate):
                    found_skills.add(skill_candidate)
        
        return found_skills
    
    def _extract_by_patterns(self, text: str) -> Set[str]:
        """
        Extracts skills using predefined regex patterns to capture skills listed in specific contexts
        (e.g., "Skills: Python, Java", "Proficient in AWS").

        Args:
            text (str): The original input text.

        Returns:
            Set[str]: A set of skills identified by regex patterns (lowercased).
        """
        found_skills = set()
        
        # Patterns to capture skills following common prefixes or within sections
        patterns = [
            r'(?:skills|technologies|proficiencies|tools|languages|frameworks|expertise|knowledge|experience)\s*[:\-\—]?\s*([a-zA-Z0-9,\s\/\-\.#+&]+)',
            r'(?:proficient|expert|experienced|skilled|familiar)\s+(?:in|with)\s+([a-zA-Z0-9,\s\/\-\.#+&]+)',
            r'\b(?:using|developed|implemented|worked with)\s+([a-zA-Z0-9,\s\/\-\.#+&]+)',
            r'\b(?:strong|solid)\s+(?:understanding|grasp)?\s*(?:of|in|with)?\s*([a-zA-Z0-9,\s\/\-\.#+&]+)'
        ]
        
        # Combine all patterns into a single regex for efficiency
        combined_pattern = '|'.join(f'(?:{p})' for p in patterns)
        
        # Find all matches for the combined pattern
        matches = re.finditer(combined_pattern, text, re.IGNORECASE)
        
        for match in matches:
            # Iterate through all capturing groups to find the one that matched
            for i in range(1, len(match.groups()) + 1):
                skill_group_text = match.group(i)
                if skill_group_text:
                    # Split by common delimiters (comma, semicolon, pipe, slash, ampersand)
                    # and handle "and" / "or" as delimiters
                    skills_candidates = re.split(r'[,;|/&]|\band\b|\bor\b', skill_group_text)
                    for skill_candidate in skills_candidates:
                        skill = skill_candidate.strip().lower()
                        # Validate and add to found skills
                        if skill and len(skill) > 1 and self._is_valid_skill(skill):
                            found_skills.add(skill)
        
        return found_skills
    
    def _is_valid_skill(self, candidate: str) -> bool:
        """
        Internal helper to check if a candidate string is a valid skill.
        Checks length, stop words, and fuzzy matches against the skills database.

        Args:
            candidate (str): The skill candidate string (should be lowercased).

        Returns:
            bool: True if it's considered a valid skill, False otherwise.
        """
        candidate = candidate.strip()
        
        # Basic length validation
        if len(candidate) < 2 or len(candidate) > 50:
            return False
        
        # Check if it's a common stop word (e.g., 'the', 'is')
        if candidate in self.stop_words:
            return False
        
        # Check if it's a number or purely punctuation
        if re.fullmatch(r'[\d\W_]+', candidate):
            return False # e.g., "123", "---", "..."

        # Check if it's in our skills database (direct or fuzzy match)
        # Using the pre-processed all_known_skills_lower set for efficiency
        if candidate in self.all_known_skills_lower:
            return True
        
        # Fallback to fuzzy matching if not an exact match in the flat set
        for known_skill in self.all_known_skills_lower:
            if fuzz.ratio(candidate, known_skill) > 80: # Using a threshold of 80 for fuzzy match
                return True
        
        return False
    
    def _clean_and_validate_skills(self, skills: Set[str]) -> Set[str]:
        """
        Performs a final cleaning and validation pass on the extracted skills.
        Removes common non-skill words, normalizes whitespace, and filters.

        Args:
            skills (Set[str]): A set of raw extracted skill strings (lowercased).

        Returns:
            Set[str]: A set of cleaned and validated skills.
        """
        cleaned_skills = set()
        
        # Define common words that are often extracted but are not skills
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
            
            # Skip if empty or very short after stripping
            if not skill or len(skill) < 2:
                continue
            
            # Remove common non-skill words (e.g., "experience in")
            # This is a more aggressive filter for extracted phrases
            words_in_skill = skill.split()
            filtered_words = [word for word in words_in_skill if word not in non_skill_words]
            skill = ' '.join(filtered_words).strip()

            if not skill: # If skill became empty after filtering
                continue

            # Final check against the comprehensive _is_valid_skill
            if self._is_valid_skill(skill):
                cleaned_skills.add(skill)
        
        return cleaned_skills
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorizes a list of skills into predefined categories based on the skills database.

        Args:
            skills (List[str]): A list of skills to categorize.

        Returns:
            Dict[str, List[str]]: A dictionary where keys are categories and values are lists of skills
                                  belonging to that category. Includes an 'other' category for uncategorized skills.
        """
        categorized: Dict[str, List[str]] = {category: [] for category in self.skills_db.keys()}
        categorized['other'] = [] # Ensure 'other' category exists
        
        for skill in skills:
            skill_lower = skill.lower()
            found_category = False
            for category, skills_set in self.skills_db_lower_sets.items():
                if skill_lower in skills_set:
                    categorized[category].append(skill) # Append original skill casing
                    found_category = True
                    break
            
            if not found_category:
                categorized['other'].append(skill)
        
        # Remove categories that ended up empty (except 'other' if it has content)
        return {k: v for k, v in categorized.items() if v or (k == 'other' and v)}
    
    def get_skill_relevance_score(self, skill: str, context: str) -> float:
        """
        Calculates a relevance score for a skill within a given text context.
        Considers frequency and contextual keywords.

        Args:
            skill (str): The skill to score.
            context (str): The text context (e.g., a resume section, job description).

        Returns:
            float: A relevance score between 0.0 and 100.0.
        """
        if not context:
            return 0.0
        
        context_lower = context.lower()
        skill_lower = skill.lower()
        
        # Count occurrences of the skill in the context
        # Use regex for whole word match to avoid partial matches (e.g., 'java' in 'javascript')
        occurrences = len(re.findall(r'\b' + re.escape(skill_lower) + r'\b', context_lower))
        
        # Calculate Term Frequency (TF)
        total_words = len(context_lower.split())
        term_frequency = occurrences / total_words if total_words > 0 else 0.0
        
        # Boost score based on strong contextual keywords (e.g., "expert in", "proficient with")
        context_boost = 1.0
        if re.search(r'\b(?:expert|proficient|advanced|mastery)\s+(?:in|with)\s+' + re.escape(skill_lower), context_lower):
            context_boost = 2.0 # Higher boost for strong indicators
        elif re.search(r'\b(?:experienced|skilled|familiar)\s+(?:in|with)?\s*' + re.escape(skill_lower), context_lower):
            context_boost = 1.5
        
        # A simple linear scaling to 100, capped at 100
        # The base score is TF * a multiplier, then boosted
        base_score = term_frequency * 50.0 # Arbitrary multiplier to scale TF
        final_score = base_score * context_boost
        
        return min(final_score, 100.0)

