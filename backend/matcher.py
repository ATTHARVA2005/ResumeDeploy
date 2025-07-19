# backend/matcher.py

from typing import List, Dict, Set, Any
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import numpy as np

class SkillMatcher:
    def __init__(self):
        # Initialize TF-IDF Vectorizer with common settings
        # lowercase=True: Converts all text to lowercase.
        # stop_words='english': Removes common English stop words (e.g., 'the', 'is').
        # ngram_range=(1, 2): Considers individual words (unigrams) and two-word phrases (bigrams).
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def calculate_match(self, resume_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
        """
        Calculate a comprehensive match between resume skills and job required skills.
        Combines exact, fuzzy, and semantic matching for a robust score.

        Args:
            resume_skills (List[str]): List of skills extracted from the resume.
            job_skills (List[str]): List of required skills from the job description.

        Returns:
            Dict[str, Any]: A dictionary containing overall_score, matched_skills,
                            missing_skills, additional_skills, and match_details.
        """
        # Handle edge cases where either list is empty
        if not resume_skills or not job_skills:
            return {
                'overall_score': 0.0,
                'matched_skills': [],
                'missing_skills': job_skills if job_skills else [], # If job_skills is empty, missing is empty
                'additional_skills': resume_skills if resume_skills else [], # If resume_skills is empty, additional is empty
                'match_details': {}
            }
        
        # Convert all skills to lowercase for consistent comparison across all methods
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]
        
        # Use sets for efficient membership testing and combining results
        all_matched_skills_set = set()
        
        # 1. Exact Matches: Prioritize direct matches
        exact_matched = self._find_exact_matches(resume_skills_lower, job_skills_lower)
        all_matched_skills_set.update(exact_matched['matched'])
        
        # 2. Fuzzy Matches: Capture variations (e.g., 'js' vs 'javascript')
        # Only consider skills not already found by exact match to avoid redundant processing
        remaining_job_skills_for_fuzzy = [s for s in job_skills_lower if s not in all_matched_skills_set]
        fuzzy_matched = self._find_fuzzy_matches(resume_skills_lower, remaining_job_skills_for_fuzzy)
        all_matched_skills_set.update(fuzzy_matched['matched'])
        
        # 3. Semantic Matches: Capture conceptual similarities (e.g., 'ML' vs 'Machine Learning')
        # Only consider skills not already found by exact or fuzzy match
        remaining_job_skills_for_semantic = [s for s in job_skills_lower if s not in all_matched_skills_set]
        semantic_matched = self._find_semantic_matches(resume_skills, remaining_job_skills_for_semantic)
        all_matched_skills_set.update(semantic_matched['matched'])
        
        # Convert the set of matched skills back to a list for the final output
        final_matched_skills = list(all_matched_skills_set)
        
        # Calculate overall score based on the combined matched skills
        overall_score = self._calculate_overall_score(
            len(final_matched_skills), 
            len(job_skills), # Total required job skills
            len(resume_skills) # Total skills in resume
        )
        
        # Determine missing skills (job skills not found in any match type)
        missing_skills = [skill for skill in job_skills_lower if skill not in all_matched_skills_set]
        
        # Determine additional skills (resume skills not required by the job)
        # Filter out any resume skills that are also job skills (even if not 'matched' by our logic)
        additional_skills = [skill for skill in resume_skills_lower if skill not in job_skills_lower]
        
        return {
            'overall_score': round(overall_score, 2), # Round for cleaner output
            'matched_skills': final_matched_skills,
            'missing_skills': missing_skills,
            'additional_skills': additional_skills,
            'match_details': {
                'exact_matches_count': len(exact_matched['matched']),
                'fuzzy_matches_count': len(fuzzy_matched['matched']),
                'semantic_matches_count': len(semantic_matched['matched']),
                'total_job_skills': len(job_skills),
                'total_resume_skills': len(resume_skills)
            }
        }
    
    def _find_exact_matches(self, resume_skills_lower: List[str], job_skills_lower: List[str]) -> Dict[str, Any]:
        """
        Find exact string matches between skills (case-insensitive due to lowercasing).
        
        Args:
            resume_skills_lower (List[str]): Lowercased skills from resume.
            job_skills_lower (List[str]): Lowercased skills from job description.
            
        Returns:
            Dict: 'matched' (list of exactly matched skills), 'score' (ratio of matched to total job skills).
        """
        resume_set = set(resume_skills_lower)
        job_set = set(job_skills_lower)
        
        matched = resume_set.intersection(job_set)
        
        return {
            'matched': list(matched),
            'score': len(matched) / len(job_set) if job_set else 0.0
        }
    
    def _find_fuzzy_matches(self, resume_skills_lower: List[str], job_skills_lower: List[str], threshold: int = 85) -> Dict[str, Any]:
        """
        Find fuzzy matches between skills using fuzzywuzzy.
        
        Args:
            resume_skills_lower (List[str]): Lowercased skills from resume.
            job_skills_lower (List[str]): Lowercased skills from job description.
            threshold (int): Minimum fuzzy ratio to consider a match (0-100).
            
        Returns:
            Dict: 'matched' (list of fuzzily matched job skills), 'score'.
        """
        matched_skills = set()
        
        for job_skill in job_skills_lower:
            for resume_skill in resume_skills_lower:
                # Calculate fuzzy similarity
                similarity = fuzz.ratio(job_skill, resume_skill)
                if similarity >= threshold:
                    matched_skills.add(job_skill) # Add the job skill that was matched
                    break # Move to the next job skill once a match is found
        
        return {
            'matched': list(matched_skills),
            'score': len(matched_skills) / len(job_skills_lower) if job_skills_lower else 0.0
        }
    
    def _find_semantic_matches(self, resume_skills: List[str], job_skills: List[str], threshold: float = 0.3) -> Dict[str, Any]:
        """
        Find semantic matches using TF-IDF vectorization and cosine similarity.
        This captures conceptual similarity beyond exact or fuzzy string matches.
        
        Args:
            resume_skills (List[str]): Skills from resume (original case, TF-IDF handles lowercasing).
            job_skills (List[str]): Skills from job description (original case).
            threshold (float): Minimum cosine similarity to consider a semantic match.
            
        Returns:
            Dict: 'matched' (list of semantically matched job skills), 'score'.
        """
        if not resume_skills or not job_skills:
            return {'matched': [], 'score': 0.0}
        
        try:
            # Combine all skills for consistent TF-IDF vectorization
            # This ensures the vocabulary is built from both sets of skills
            all_skills_text = [" ".join(resume_skills), " ".join(job_skills)]
            
            # Fit and transform the combined text to get TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_skills_text)
            
            # Extract vectors for resume and job skills
            # Each row in tfidf_matrix now represents the combined text of all skills from resume/job
            # To get similarity between individual skills, we need to vectorize each skill separately
            # A more robust semantic matching would involve pre-trained word embeddings (e.g., Word2Vec, BERT)
            # but for TF-IDF, comparing the overall skill sets is more typical.
            
            # Let's refine this to compare individual job skills against the entire resume skill set
            # This is a common approach for TF-IDF based semantic matching in this context.
            
            job_skill_vectors = self.tfidf_vectorizer.transform(job_skills)
            resume_skill_vectors = self.tfidf_vectorizer.transform(resume_skills)

            matched_skills = set()
            # Compare each job skill vector against all resume skill vectors
            for i, job_skill_vec in enumerate(job_skill_vectors):
                # Calculate cosine similarity between current job skill vector and all resume skill vectors
                similarities = cosine_similarity(job_skill_vec, resume_skill_vectors)
                
                # Find the maximum similarity for this job skill
                max_similarity = np.max(similarities)
                
                if max_similarity >= threshold:
                    matched_skills.add(job_skills[i].lower()) # Add the original job skill (lowercased)
            
            return {
                'matched': list(matched_skills),
                'score': len(matched_skills) / len(job_skills) if job_skills else 0.0
            }
        
        except ValueError as ve:
            # This can happen if tfidf_vectorizer.fit_transform receives empty documents
            print(f"ValueError in semantic matching (likely empty skills after preprocessing): {ve}")
            return {'matched': [], 'score': 0.0}
        except Exception as e:
            print(f"Unexpected error in semantic matching: {e}")
            return {'matched': [], 'score': 0.0}
    
    def _calculate_overall_score(self, matched_count: int, total_job_skills: int, total_resume_skills: int) -> float:
        """
        Calculate the overall matching score based on matched skills,
        total required job skills, and total resume skills.
        
        Args:
            matched_count (int): Number of skills matched.
            total_job_skills (int): Total number of skills required by the job.
            total_resume_skills (int): Total number of skills listed in the resume.
            
        Returns:
            float: The calculated overall score (0-100).
        """
        if total_job_skills == 0:
            return 0.0 # Cannot calculate score if no job skills are required
        
        # Base score: percentage of job skills that were matched
        base_score = (matched_count / total_job_skills) * 100
        
        # Introduce a small bonus for having more skills in the resume than required,
        # indicating a broader skillset, but cap it.
        skill_abundance_bonus = 0.0
        if total_resume_skills > total_job_skills:
            # For every skill beyond the required, add a small bonus, up to a max
            skill_abundance_bonus = min((total_resume_skills - total_job_skills) * 0.5, 5.0) # Max 5% bonus

        # Introduce a penalty for significantly missing critical skills (if applicable, though not explicitly prioritized here)
        # For simplicity, a general penalty if matched skills are very low compared to required
        missing_penalty = 0.0
        if matched_count < (total_job_skills * 0.5): # If less than 50% matched
            missing_penalty = (total_job_skills * 0.5 - matched_count) * 1.0 # Larger penalty for each missing skill below threshold

        final_score = base_score + skill_abundance_bonus - missing_penalty
        
        # Ensure the final score is within the valid range [0, 100]
        return max(0.0, min(100.0, final_score))
    
    # The rank_resumes method is typically handled in main.py after getting all match results.
    # Keeping it here for completeness if you decide to use it internally.
    def rank_resumes(self, resumes_data: List[Dict[str, Any]], job_skills: List[str]) -> List[Dict[str, Any]]:
        """
        Rank multiple resumes against job requirements based on their match scores.
        
        Args:
            resumes_data (List[Dict]): List of resume dictionaries (with 'id', 'filename', 'extracted_skills').
            job_skills (List[str]): List of required skills from the job description.
            
        Returns:
            List[Dict]: List of scored resume dictionaries, sorted by overall_score descending.
        """
        scored_resumes = []
        
        for resume in resumes_data:
            # Ensure extracted_skills is a list; handle cases where it might be None or not a list
            resume_extracted_skills = resume.get('extracted_skills', [])
            if not isinstance(resume_extracted_skills, list):
                # Attempt to parse if it's a JSON string, or default to empty list
                try:
                    resume_extracted_skills = json.loads(resume_extracted_skills)
                except (json.JSONDecodeError, TypeError):
                    resume_extracted_skills = []

            match_result = self.calculate_match(resume_extracted_skills, job_skills)
            
            scored_resume = {
                'resume_id': resume['id'],
                'filename': resume['filename'],
                'overall_score': match_result['overall_score'],
                'matched_skills': match_result['matched_skills'],
                'missing_skills': match_result['missing_skills'],
                'additional_skills': match_result['additional_skills'],
                'match_details': match_result['match_details']
            }
            
            scored_resumes.append(scored_resume)
        
        # Sort by score (highest first)
        scored_resumes.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return scored_resumes
    
    def get_skill_gap_analysis(self, resume_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
        """
        Analyze skill gaps and provide recommendations based on the match.
        
        Args:
            resume_skills (List[str]): Skills extracted from the resume.
            job_skills (List[str]): Required skills from the job description.
            
        Returns:
            Dict: Analysis including overall score, readiness level, counts, strengths, and recommendations.
        """
        match_result = self.calculate_match(resume_skills, job_skills)
        
        # Categorize missing skills by a simple heuristic for recommendation generation
        # In a real-world scenario, this might involve skill importance from job description or a skill ontology
        critical_missing = []
        important_missing = []
        nice_to_have = []
        
        # This part could be enhanced by using your skills_database categories
        # For simplicity, we'll keep the keyword-based heuristic for now.
        for skill in match_result['missing_skills']:
            if any(keyword in skill.lower() for keyword in ['python', 'java', 'sql', 'javascript', 'aws', 'docker', 'kubernetes']):
                critical_missing.append(skill)
            elif any(keyword in skill.lower() for keyword in ['git', 'agile', 'api', 'database', 'cloud', 'frontend', 'backend']):
                important_missing.append(skill)
            else:
                nice_to_have.append(skill)
        
        # Determine readiness level based on overall score
        readiness_level = "Not Ready"
        if match_result['overall_score'] >= 80:
            readiness_level = "Excellent Match"
        elif match_result['overall_score'] >= 60:
            readiness_level = "Good Match"
        elif match_result['overall_score'] >= 40:
            readiness_level = "Fair Match"
        elif match_result['overall_score'] >= 20:
            readiness_level = "Partial Match"
        
        return {
            'overall_score': match_result['overall_score'],
            'readiness_level': readiness_level,
            'matched_skills_count': len(match_result['matched_skills']),
            'total_required_skills': len(job_skills),
            'critical_missing': critical_missing,
            'important_missing': important_missing,
            'nice_to_have_missing': nice_to_have,
            'strengths': match_result['additional_skills'][:5],  # Top 5 additional skills
            'recommendations': self._generate_recommendations(critical_missing, important_missing)
        }
    
    def _generate_recommendations(self, critical_missing: List[str], important_missing: List[str]) -> List[str]:
        """
        Generate actionable recommendations based on identified missing skills.
        
        Args:
            critical_missing (List[str]): Skills deemed critical and missing.
            important_missing (List[str]): Skills deemed important and missing.
            
        Returns:
            List[str]: A list of recommendation strings.
        """
        recommendations = []
        
        if critical_missing:
            recommendations.append(f"Priority: Focus on acquiring or strengthening skills in {', '.join(critical_missing[:3])} as these are crucial for the role.")
        
        if important_missing:
            recommendations.append(f"Consider developing skills in {', '.join(important_missing[:3])} to significantly improve your profile's alignment.")
        
        if not critical_missing and not important_missing:
            recommendations.append("Excellent skill alignment! Your profile strongly matches the requirements. Focus on gaining practical experience with your existing skills.")
        
        recommendations.append("Tailor your resume and cover letter to prominently feature your matched skills and experiences relevant to this job description.")
        recommendations.append("For any missing skills, consider online courses, certifications, or personal projects to build proficiency.")
        
        return recommendations

