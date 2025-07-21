# backend/matcher.py

from typing import List, Dict, Set, Any, Optional
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import numpy as np

class SkillMatcher:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def calculate_match(self, 
                        resume_skills: List[str], 
                        job_skills: List[str],
                        resume_experience_years: Optional[int] = None,
                        job_required_experience_years: Optional[int] = None,
                        job_required_certifications: Optional[List[str]] = None
                       ) -> Dict[str, Any]:
        """
        Calculate a comprehensive match between resume and job requirements.
        Includes skills, experience, and certifications.
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

        # --- 4. Combine Overall Score ---
        # Assign weights to different match aspects
        WEIGHT_SKILLS = 0.70 # Increased weight
        WEIGHT_EXPERIENCE = 0.20
        WEIGHT_CERTIFICATIONS = 0.10

        # Normalize weights to sum to 1
        total_weight = WEIGHT_SKILLS + WEIGHT_EXPERIENCE + WEIGHT_CERTIFICATIONS
        
        overall_score = (
            (skill_overall_score * WEIGHT_SKILLS) +
            (experience_score * WEIGHT_EXPERIENCE) +
            (certifications_score * WEIGHT_CERTIFICATIONS)
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
                'resume_exp_years': resume_experience_years,
                'job_req_exp_years': job_required_experience_years,
                'job_req_certs': job_required_certifications
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
                                        resume_skills: List[str], 
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