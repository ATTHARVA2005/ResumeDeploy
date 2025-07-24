# backend/matcher.py

from typing import List, Dict, Set, Any, Optional
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import numpy as np
import re # Added regex module for major normalization

class SkillMatcher:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2)
        )
        # Define a simple hierarchy for education levels
        self.education_hierarchy = { # Added for education matching
            "phd": 5, "doctorate": 5,
            "master": 4, "m.s": 4, "msc": 4,
            "bachelor": 3, "b.s": 3, "btech": 3,
            "associate": 2, "diploma": 1, "high school": 1, "none": 0
        }
    
    def calculate_match(self, 
                        resume_skills: List[str], 
                        job_skills: List[str],
                        resume_experience_years: Optional[int] = None,
                        job_required_experience_years: Optional[int] = None,
                        job_required_certifications: Optional[List[str]] = None,
                        resume_highest_education_level: Optional[str] = None, # Added for education matching
                        resume_major: Optional[str] = None, # Added for education matching
                        job_required_education_level: Optional[str] = None, # Added for education matching
                        job_required_major: Optional[str] = None # Added for education matching
                       ) -> Dict[str, Any]:
        """
        Calculate a comprehensive match between resume and job requirements.
        Includes skills, experience, certifications, and education.
        """
        # --- 1. Skill Matching ---
        if not resume_skills or not job_skills:
            skill_overall_score = 0.0
            final_matched_skills = []
            missing_skills = job_skills if job_skills else []
            additional_skills = resume_skills if resume_skills else []
            skill_match_details = {
                'exact_matches_count': 0, 'fuzzy_matches_count': 0, 'semantic_matches_count': 0,
                'total_job_skills': len(job_skills), 'total_resume_skills': len(resume_skills)
            }
        else:
            resume_skills_lower = [skill.lower() for skill in resume_skills]
            job_skills_lower = [skill.lower() for skill in job_skills]
            
            all_matched_skills_set = set()
            
            exact_matched = self._find_exact_matches(resume_skills_lower, job_skills_lower)
            all_matched_skills_set.update(exact_matched['matched'])
            
            remaining_job_skills_for_fuzzy = [s for s in job_skills_lower if s not in all_matched_skills_set]
            fuzzy_matched = self._find_fuzzy_matches(resume_skills_lower, remaining_job_skills_for_fuzzy)
            all_matched_skills_set.update(fuzzy_matched['matched'])
            
            remaining_job_skills_for_semantic = [s for s in job_skills_lower if s not in all_matched_skills_set]
            semantic_matched = self._find_semantic_matches(resume_skills, remaining_job_skills_for_semantic)
            all_matched_skills_set.update(semantic_matched['matched'])
            
            final_matched_skills = list(all_matched_skills_set)
            missing_skills = [skill for skill in job_skills_lower if skill not in all_matched_skills_set]
            additional_skills = [skill for skill in resume_skills_lower if skill not in job_skills_lower]

            skill_overall_score = self._calculate_skill_score(
                len(final_matched_skills), 
                len(job_skills),
                len(resume_skills)
            )
            skill_match_details = {
                'exact_matches_count': len(exact_matched['matched']),
                'fuzzy_matches_count': len(fuzzy_matched['matched']),
                'semantic_matches_count': len(semantic_matched['matched']),
                'total_job_skills': len(job_skills),
                'total_resume_skills': len(resume_skills)
            }
        
        # --- 2. Experience Matching ---
        experience_score = self._calculate_experience_score(
            resume_experience_years, 
            job_required_experience_years
        )

        # --- 3. Certifications Matching ---
        certifications_score = self._calculate_certifications_score(
            resume_skills,
            job_required_certifications
        )

        # --- 4. Education Matching (NEW) ---
        education_score = self._calculate_education_score( # Call to new method
            resume_highest_education_level=resume_highest_education_level,
            resume_major=resume_major,
            job_required_education_level=job_required_education_level,
            job_required_major=job_required_major
        )

        # --- 5. Combine Overall Score ---
        # Assign weights to different match aspects
        WEIGHT_SKILLS = 0.60 # Adjusted weight
        WEIGHT_EXPERIENCE = 0.20
        WEIGHT_CERTIFICATIONS = 0.10
        WEIGHT_EDUCATION = 0.10 # New weight for education

        # Normalize weights to sum to 1
        total_weight = WEIGHT_SKILLS + WEIGHT_EXPERIENCE + WEIGHT_CERTIFICATIONS + WEIGHT_EDUCATION
        
        overall_score = (
            (skill_overall_score * WEIGHT_SKILLS) +
            (experience_score * WEIGHT_EXPERIENCE) +
            (certifications_score * WEIGHT_CERTIFICATIONS) +
            (education_score * WEIGHT_EDUCATION) # Add education score
        ) / total_weight

        overall_score = max(0.0, min(100.0, overall_score))

        return {
            'overall_score': round(overall_score, 2),
            'matched_skills': final_matched_skills,
            'missing_skills': missing_skills,
            'additional_skills': additional_skills,
            'match_details': {
                **skill_match_details,
                'experience_score': round(experience_score, 2),
                'certifications_score': round(certifications_score, 2),
                'education_score': round(education_score, 2), # Add education score to details
                'resume_exp_years': resume_experience_years,
                'job_req_exp_years': job_required_experience_years,
                'job_req_certs': job_required_certifications,
                'resume_highest_edu': resume_highest_education_level, # Add edu details
                'resume_major': resume_major, # Add edu details
                'job_req_edu': job_required_education_level, # Add edu details
                'job_req_major': job_required_major # Add edu details
            }
        }
    
    def _find_exact_matches(self, resume_skills_lower: List[str], job_skills_lower: List[str]) -> Dict[str, Any]:
        """Find exact string matches between skills (case-insensitive)."""
        resume_set = set(resume_skills_lower)
        job_set = set(job_skills_lower)
        matched = resume_set.intersection(job_set)
        return {'matched': list(matched), 'score': len(matched) / len(job_set) if job_set else 0.0}
    
    def _find_fuzzy_matches(self, resume_skills_lower: List[str], job_skills_lower: List[str], threshold: int = 85) -> Dict[str, Any]:
        """Find fuzzy matches between skills using fuzzywuzzy."""
        matched_skills = set()
        for job_skill in job_skills_lower:
            for resume_skill in resume_skills_lower:
                if job_skill == resume_skill: continue
                similarity = fuzz.ratio(job_skill, resume_skill)
                if similarity >= threshold:
                    matched_skills.add(job_skill)
                    break
        return {'matched': list(matched_skills), 'score': len(matched_skills) / len(job_skills_lower) if job_skills_lower else 0.0}
    
    def _find_semantic_matches(self, resume_skills: List[str], job_skills: List[str], threshold: float = 0.3) -> Dict[str, Any]:
        """Find semantic matches using TF-IDF and cosine similarity."""
        if not resume_skills or not job_skills:
            return {'matched': [], 'score': 0.0}
        
        try:
            all_unique_skills = list(set(resume_skills + job_skills))
            if not all_unique_skills: return {'matched': [], 'score': 0.0}

            self.tfidf_vectorizer.fit(all_unique_skills)
            
            job_skill_vectors = self.tfidf_vectorizer.transform(job_skills)
            resume_skill_vectors = self.tfidf_vectorizer.transform(resume_skills)

            matched_skills = set()
            for i, job_skill_vec in enumerate(job_skill_vectors):
                if job_skill_vec.nnz == 0: continue

                similarities = cosine_similarity(job_skill_vec, resume_skill_vectors)
                
                if similarities.size > 0:
                    max_similarity = np.max(similarities)
                    if max_similarity >= threshold:
                        matched_skills.add(job_skills[i].lower())
            
            return {'matched': list(matched_skills), 'score': len(matched_skills) / len(job_skills) if job_skills else 0.0}
        
        except ValueError as ve:
            print(f"ValueError in semantic matching: {ve}")
            return {'matched': [], 'score': 0.0}
        except Exception as e:
            print(f"Unexpected error in semantic matching: {e}")
            return {'matched': [], 'score': 0.0}
    
    def _calculate_skill_score(self, matched_count: int, total_job_skills: int, total_resume_skills: int) -> float:
        """Calculate skill-specific matching score."""
        if total_job_skills == 0:
            return 0.0
        
        base_score = (matched_count / total_job_skills) * 100
        skill_abundance_bonus = min((total_resume_skills - total_job_skills) * 0.5, 5.0) if total_resume_skills > total_job_skills else 0.0
        missing_penalty = (total_job_skills * 0.5 - matched_count) * 1.0 if matched_count < (total_job_skills * 0.5) else 0.0

        final_score = base_score + skill_abundance_bonus - missing_penalty
        return max(0.0, min(100.0, final_score))

    def _calculate_experience_score(self, 
                                    resume_exp_years: Optional[int], 
                                    job_req_exp_years: Optional[int]) -> float:
        """Calculates a score based on matching experience years."""
        resume_exp_years = resume_exp_years if resume_exp_years is not None else 0
        job_req_exp_years = job_req_exp_years if job_req_exp_years is not None else 0

        if job_req_exp_years == 0:
            return 100.0
        if resume_exp_years >= job_req_exp_years:
            return 100.0
        else:
            score = (resume_exp_years / job_req_exp_years) * 100
            return max(0.0, min(100.0, score))

    def _calculate_certifications_score(self, 
                                        resume_skills: List[str], # Can contain certs if Gemini extracts them as skills
                                        job_required_certifications: Optional[List[str]]) -> float:
        """Calculates a score based on matching certifications."""
        if not job_required_certifications:
            return 100.0
        if not resume_skills:
            return 0.0

        resume_skills_lower = {s.lower() for s in resume_skills}
        job_certs_lower = {c.lower() for c in job_required_certifications}

        if not job_certs_lower:
            return 100.0
        
        matched_certs = resume_skills_lower.intersection(job_certs_lower)
        score = (len(matched_certs) / len(job_certs_lower)) * 100
        return max(0.0, min(100.0, score))

    def _calculate_education_score(self, # New method for education matching
                                   resume_highest_education_level: Optional[str],
                                   resume_major: Optional[str],
                                   job_required_education_level: Optional[str],
                                   job_required_major: Optional[str]) -> float:
        """
        Calculates a score based on matching education level and major,
        ignoring specializations in parentheses for major comparison.
        """
        score = 0.0
        
        resume_edu_level_norm = (resume_highest_education_level or "none").lower().replace(" ", "")
        job_req_edu_level_norm = (job_required_education_level or "none").lower().replace(" ", "")

        # NEW: Normalize majors by removing text in parentheses
        def normalize_major(major_str: Optional[str]) -> str:
            if not major_str:
                return ""
            # Remove text in parentheses
            cleaned_major = re.sub(r'\s*\(.*?\)\s*', '', major_str).strip()
            # Handle common abbreviations or variations if necessary (e.g., "CS" vs "Computer Science")
            if cleaned_major.lower() == "cs": return "computer science"
            if cleaned_major.lower() == "ee": return "electrical engineering"
            return cleaned_major.lower()

        resume_major_normalized = normalize_major(resume_major) # Apply normalization
        job_req_major_normalized = normalize_major(job_required_major) # Apply normalization

        # Score based on education level hierarchy
        resume_level_val = self.education_hierarchy.get(resume_edu_level_norm, 0)
        job_req_level_val = self.education_hierarchy.get(job_req_edu_level_norm, 0)

        if job_req_level_val == 0: # No specific education level required by job
            score += 50.0 # Base score for having any education
            if resume_level_val > 0:
                score += 50.0 # Bonus for actually having education if not strictly required
        elif resume_level_val >= job_req_level_val:
            score += 100.0 # Resume meets or exceeds required level
        elif resume_level_val > 0 and resume_level_val < job_req_level_val:
            # Partial credit for having some education but not meeting the level
            score += (resume_level_val / job_req_level_val) * 70.0
        
        # Adjust score based on major match (if a major is specified by the job)
        if job_req_major_normalized: # Use normalized major here
            major_match_score = 0.0
            # Check for direct or fuzzy match on normalized majors
            if resume_major_normalized == job_req_major_normalized:
                major_match_score = 100.0
            elif fuzz.ratio(job_req_major_normalized, resume_major_normalized) > 85: # High fuzzy match
                major_match_score = 90.0
            elif fuzz.partial_ratio(job_req_major_normalized, resume_major_normalized) > 90: # Partial match for broader terms
                major_match_score = 80.0
            elif job_req_major_normalized in resume_major_normalized or resume_major_normalized in job_req_major_normalized: # Catch cases like "Computer Science" being part of "Applied Computer Science"
                major_match_score = 70.0

            # Combine major match with education level score. For example, 70% level, 30% major.
            score = (score * 0.7) + (major_match_score * 0.3)
        
        return max(0.0, min(100.0, score))