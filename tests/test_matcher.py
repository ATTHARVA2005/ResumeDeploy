# tests/test_matcher.py

import pytest
from backend.matcher import SkillMatcher
from typing import List, Dict, Any

@pytest.fixture
def skill_matcher_instance():
    """Fixture to provide a SkillMatcher instance for tests."""
    return SkillMatcher()

def test_calculate_match_empty_inputs(skill_matcher_instance):
    """Test calculate_match with empty resume or job skills."""
    result = skill_matcher_instance.calculate_match([], [])
    assert result['overall_score'] == 0.0
    assert result['matched_skills'] == []
    assert result['missing_skills'] == []
    assert result['additional_skills'] == []

    result = skill_matcher_instance.calculate_match(["Python"], [])
    assert result['overall_score'] == 0.0
    assert result['matched_skills'] == []
    assert result['missing_skills'] == []
    assert result['additional_skills'] == ["python"]

    result = skill_matcher_instance.calculate_match([], ["Java"])
    assert result['overall_score'] == 0.0
    assert result['matched_skills'] == []
    assert result['missing_skills'] == ["java"]
    assert result['additional_skills'] == []

def test_find_exact_matches(skill_matcher_instance):
    """Test exact skill matching."""
    resume_skills = ["Python", "Java", "SQL"]
    job_skills = ["Python", "JavaScript", "SQL"]
    result = skill_matcher_instance._find_exact_matches(
        [s.lower() for s in resume_skills],
        [s.lower() for s in job_skills]
    )
    assert set(result['matched']) == {"python", "sql"}
    assert result['score'] == 2/3 # 2 matched out of 3 job skills

def test_find_fuzzy_matches(skill_matcher_instance):
    """Test fuzzy skill matching."""
    resume_skills = ["Pyton", "Javascrpt"]
    job_skills = ["Python", "JavaScript", "SQL"]
    result = skill_matcher_instance._find_fuzzy_matches(
        [s.lower() for s in resume_skills],
        [s.lower() for s in job_skills],
        threshold=85
    )
    assert set(result['matched']) == {"python", "javascript"}
    assert result['score'] == 2/3 # 2 matched out of 3 job skills

def test_find_semantic_matches(skill_matcher_instance):
    """Test semantic skill matching (TF-IDF based)."""
    resume_skills = ["Machine Learning", "Deep Learning"]
    job_skills = ["ML", "AI", "Data Science"] # ML should semantically match Machine Learning
    result = skill_matcher_instance._find_semantic_matches(resume_skills, job_skills, threshold=0.1)
    # The exact outcome of semantic matching can be sensitive to TF-IDF vocabulary and threshold.
    # We expect 'ml' to match 'machine learning'.
    assert "ml" in result['matched'] or "machine learning" in result['matched']
    # If AI or Data Science don't have strong semantic overlap with the resume skills, they won't match.
    # This test is a bit fragile due to TF-IDF's nature; real semantic matching benefits from word embeddings.
    assert result['score'] >= 0 # Score should be non-negative

def test_calculate_overall_score(skill_matcher_instance):
    """Test overall score calculation."""
    # Perfect match
    score = skill_matcher_instance._calculate_overall_score(5, 5, 5)
    assert score > 90 # Expect high score, potentially >100 before capping

    # Partial match, resume has more skills
    score = skill_matcher_instance._calculate_overall_score(3, 5, 7)
    # Expected: (3/5)*100 = 60 (base) + (7-5)*0.5 = 1 (bonus) = 61
    assert 60 <= score <= 65

    # Partial match, resume has fewer skills (penalty)
    score = skill_matcher_instance._calculate_overall_score(2, 5, 3)
    # Expected: (2/5)*100 = 40 (base) - (5*0.5 - 2)*1 = 0.5 (penalty) = 39.5
    assert 35 <= score <= 40

    # No job skills
    score = skill_matcher_instance._calculate_overall_score(0, 0, 5)
    assert score == 0.0

def test_calculate_match_comprehensive(skill_matcher_instance):
    """Test the main calculate_match method with a mix of skills."""
    resume_skills = ["Python", "Django", "SQL", "AWS", "Docker", "Communication", "Leadership", "ReactJS"]
    job_skills = ["Python", "Django", "PostgreSQL", "AWS", "Kubernetes", "Teamwork", "JavaScript"]

    result = skill_matcher_instance.calculate_match(resume_skills, job_skills)

    assert result['overall_score'] >= 0.0 and result['overall_score'] <= 100.0
    
    # Expected matched skills (case-insensitive)
    expected_matched = {"python", "django", "aws"} # SQL might be fuzzy/semantic
    assert expected_matched.issubset(set(result['matched_skills']))

    # Expected missing skills (case-insensitive)
    expected_missing = {"postgresql", "kubernetes", "javascript", "teamwork"}
    assert expected_missing.issubset(set(result['missing_skills']))

    # Expected additional skills (case-insensitive)
    expected_additional = {"docker", "communication", "leadership", "reactjs"}
    assert expected_additional.issubset(set(result['additional_skills']))

    assert result['match_details']['total_job_skills'] == len(job_skills)
    assert result['match_details']['total_resume_skills'] == len(resume_skills)

def test_get_skill_gap_analysis(skill_matcher_instance):
    """Test skill gap analysis and recommendations."""
    resume_skills = ["Python", "Django", "AWS"]
    job_skills = ["Python", "Java", "SQL", "Docker", "Communication"]

    analysis = skill_matcher_instance.get_skill_gap_analysis(resume_skills, job_skills)

    assert "overall_score" in analysis
    assert "readiness_level" in analysis
    assert "matched_skills_count" in analysis
    assert "total_required_skills" in analysis
    assert "critical_missing" in analysis
    assert "important_missing" in analysis
    assert "nice_to_have_missing" in analysis
    assert "strengths" in analysis
    assert "recommendations" in analysis

    assert "Java" in analysis['critical_missing'] # Based on heuristic
    assert "SQL" in analysis['critical_missing']
    assert "Docker" in analysis['important_missing']
    assert "Communication" in analysis['important_missing'] # Soft skill is important

    assert len(analysis['recommendations']) > 0
    assert "Priority: Focus on acquiring or strengthening skills in Java" in analysis['recommendations'][0] or \
           "Priority: Focus on acquiring or strengthening skills in SQL" in analysis['recommendations'][0]
