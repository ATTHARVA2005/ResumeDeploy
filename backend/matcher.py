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
        # Define a simple hierarchy for education levels
        self.education_hierarchy = {
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
                        resume_highest_education_level: Optional[str] = None,
                        resume_major: Optional[str] = None,
                        job_required_education_level: Optional[str] = None,
                        job_required_major: Optional[str] = None,
                        # NEW: Add weights parameter
                        weights: Optional[Dict[str, float]] = None
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
            resume_skills, # Using resume_skills as a proxy for certifications mentioned in resume
            job_required_certifications
        )

        # --- 4. Education Matching ---
        education_score = self._calculate_education_score(
            resume_highest_education_level=resume_highest_education_level,
            resume_major=resume_major,
            job_required_education_level=job_required_education_level,
            job_required_major=job_required_major
        )

        # --- 5. Combine Overall Score ---
        # Use custom weights if provided, otherwise fall back to defaults
        # Ensure weights sum to 1.0 (handled by Pydantic validation if using models.MatchWeights)
        effective_weights = {
            "skills": 0.60,
            "experience": 0.20,
            "certifications": 0.10,
            "education": 0.10
        }
        if weights:
            # Normalise custom weights if they don't sum to 1, though Pydantic model should enforce this.
            # This is a fallback for direct calls or if validation is skipped.
            total_custom_weight = sum(weights.values())
            if not math.isclose(total_custom_weight, 0.0) and not math.isclose(total_custom_weight, 1.0):
                effective_weights = {k: v / total_custom_weight for k, v in weights.items()}
            elif math.isclose(total_custom_weight, 1.0):
                effective_weights = weights


        overall_score = (
            (skill_overall_score * effective_weights["skills"]) +
            (experience_score * effective_weights["experience"]) +
            (certifications_score * effective_weights["certifications"]) +
            (education_score * effective_weights["education"])
        )

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
                'education_score': round(education_score, 2),
                'resume_exp_years': resume_experience_years,
                'job_req_exp_years': job_required_experience_years,
                'job_req_certs': job_required_certifications,
                'resume_highest_edu': resume_highest_education_level,
                'resume_major': resume_major,
                'job_req_edu': job_required_education_level,
                'job_req_major': job_required_major,
                'applied_weights': effective_weights # NEW: Show which weights were applied
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
                if job_skill == resume_skill: continue # Skip exact matches handled by _find_exact_matches
                similarity = fuzz.ratio(job_skill, resume_skill)
                if similarity >= threshold:
                    matched_skills.add(job_skill)
                    break # Found a fuzzy match for this job_skill, move to next
        return {'matched': list(matched_skills), 'score': len(matched_skills) / len(job_skills_lower) if job_skills_lower else 0.0}
    
    def _find_semantic_matches(self, resume_skills: List[str], job_skills: List[str], threshold: float = 0.3) -> Dict[str, Any]:
        """Find semantic matches using TF-IDF and cosine similarity."""
        if not resume_skills or not job_skills:
            return {'matched': [], 'score': 0.0}
        
        try:
            all_unique_skills = list(set(resume_skills + job_skills))
            if not all_unique_skills: return {'matched': [], 'score': 0.0}

            # If the vectorizer has not been fitted, fit it with all skills from both resume and job
            # This ensures consistent vector space for similarity calculation
            # Note: For production, pre-fitting TFIDF on a large corpus of skills is more robust
            # For dynamic fitting, ensure it happens only once per match operation or batch.
            # Here, it's safer to re-fit if skills vary wildly.
            self.tfidf_vectorizer.fit(all_unique_skills)
            
            job_skill_vectors = self.tfidf_vectorizer.transform(job_skills)
            resume_skill_vectors = self.tfidf_vectorizer.transform(resume_skills)

            matched_skills = set()
            for i, job_skill_vec in enumerate(job_skill_vectors):
                # Skip if job skill vector is all zeros (e.g., common stop word or very short skill)
                if job_skill_vec.nnz == 0: continue

                # Calculate cosine similarity between current job skill and all resume skills
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
        # Bonus for having more skills than required (up to 5 points)
        skill_abundance_bonus = min((total_resume_skills - total_job_skills) * 0.5, 5.0) if total_resume_skills > total_job_skills else 0.0
        # Penalty for matching less than 50% of required skills
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
            return 100.0 # If job requires 0 experience, always a perfect match
        if resume_exp_years >= job_req_exp_years:
            return 100.0 # If resume meets or exceeds requirement, perfect match
        else:
            score = (resume_exp_years / job_req_exp_years) * 100
            return max(0.0, min(100.0, score))

    def _calculate_certifications_score(self, 
                                        resume_skills: List[str], # Can contain certs if Gemini extracts them as skills
                                        job_required_certifications: Optional[List[str]]) -> float:
        """Calculates a score based on matching certifications."""
        if not job_required_certifications:
            return 100.0 # No certifications required, so perfect score
        if not resume_skills:
            return 0.0 # Certifications required but resume has no skills/certs listed

        resume_skills_lower = {s.lower() for s in resume_skills}
        job_certs_lower = {c.lower() for c in job_required_certifications}

        if not job_certs_lower:
            return 100.0 # Should be caught by first check, but for safety
        
        matched_certs = resume_skills_lower.intersection(job_certs_lower)
        score = (len(matched_certs) / len(job_certs_lower)) * 100
        return max(0.0, min(100.0, score))

    def _calculate_education_score(self,
                                   resume_highest_education_level: Optional[str],
                                   resume_major: Optional[str],
                                   job_required_education_level: Optional[str],
                                   job_required_major: Optional[str]) -> float:
        """
        Calculates a score based on matching education level and major.
        If job requires no specific education, it's a 100% match.
        """
        score = 0.0
        
        resume_edu_level_norm = (resume_highest_education_level or "none").lower().replace(" ", "")
        job_req_edu_level_norm = (job_required_education_level or "none").lower().replace(" ", "")

        resume_major_norm = (resume_major or "").lower().strip()
        job_req_major_norm = (job_required_major or "").lower().strip()

        # Score based on education level hierarchy
        resume_level_val = self.education_hierarchy.get(resume_edu_level_norm, 0)
        job_req_level_val = self.education_hierarchy.get(job_req_edu_level_norm, 0)

        # Explicitly handle cases where job requires no education
        if job_req_level_val == 0:
            edu_level_score = 100.0 # If job requires 0 education, it's a perfect match for level
        elif resume_level_val >= job_req_level_val:
            edu_level_score = 100.0 # Resume meets or exceeds required level
        elif resume_level_val > 0 and resume_level_val < job_req_level_val:
            # Partial credit for having some education but not meeting the level
            edu_level_score = (resume_level_val / job_req_level_val) * 80.0 # Give partial credit, max 80% for not fully meeting.
        else: # resume_level_val == 0 and job_req_level_val > 0
            edu_level_score = 0.0 # Job requires education, but resume has none listed

        # Score based on major match (if a major is specified by the job)
        major_match_score = 0.0
        if job_req_major_norm and job_req_major_norm.lower() != 'none': # Only consider major if job actually specified one
            if resume_major_norm and resume_major_norm.lower() != 'none':
                # Use partial ratio for flexibility
                if fuzz.partial_ratio(job_req_major_norm, resume_major_norm) > 80:
                    major_match_score = 100.0
                elif job_req_major_norm in resume_major_norm: # Also check for exact substring match
                    major_match_score = 100.0
            # If resume has no major but job requires one, major_match_score remains 0.0
            
            # Combine major match with education level score.
            # Give higher weight to education level than major unless major is a perfect match.
            # Adjust these weights as needed. For simplicity, let's keep it direct.
            # If a major is required, it becomes a factor.
            # If major is required but resume has none, it will pull score down.
            # If resume has major but job doesn't require, it doesn't add to score, unless it matches default "None" to "None"
            
            # For combining: A simple average or weighted average works.
            # Let's say edu level is 70% of score, major is 30% if major is required.
            score = (edu_level_score * 0.7) + (major_match_score * 0.3)
        else:
            # If no major is required by job, the score is solely based on education level
            score = edu_level_score
        
        return max(0.0, min(100.0, score))