# tests/test_skill_extractor.py

import pytest
import os
import json
from pathlib import Path

# Import the SkillExtractor class from the backend module
from backend.skill_extractor import SkillExtractor

# Define path for the skills database (should match your data/ directory)
SKILLS_DB_PATH = Path("data/skills_database.json")

@pytest.fixture(scope="module")
def skill_extractor_instance():
    """
    Fixture to provide a SkillExtractor instance for tests.
    Ensures the skills_database.json is present for testing.
    """
    # Ensure a default skills_database.json exists for testing
    if not SKILLS_DB_PATH.exists():
        print(f"\n{SKILLS_DB_PATH} not found. Creating a minimal one for tests.")
        minimal_skills = {
            "programming_languages": ["python", "java", "javascript", "c++", "go"],
            "web_technologies": ["react", "angular", "node.js", "html", "css"],
            "databases": ["sql", "mongodb", "postgresql"],
            "cloud_platforms": ["aws", "azure", "gcp"],
            "soft_skills": ["communication", "teamwork", "leadership"]
        }
        os.makedirs(SKILLS_DB_PATH.parent, exist_ok=True)
        with open(SKILLS_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(minimal_skills, f, indent=4)
    
    extractor = SkillExtractor()
    # Ensure Spacy model is loaded for tests that rely on it
    if extractor.nlp is None:
        pytest.skip("Spacy model 'en_core_web_sm' not loaded. Skipping NLP-dependent tests.")
    return extractor

def test_extract_by_direct_match(skill_extractor_instance):
    """Test direct skill matching."""
    text = "I am proficient in Python and have experience with Java."
    skills = skill_extractor_instance._extract_by_direct_match(text.lower())
    assert "python" in skills
    assert "java" in skills
    assert "javascript" not in skills # Should not match partial word

def test_extract_by_fuzzy_match(skill_extractor_instance):
    """Test fuzzy skill matching."""
    text = "I know pythn and have some experience with javascrpt."
    skills = skill_extractor_instance._extract_by_fuzzy_match(text.lower())
    assert "python" in skills
    assert "javascript" in skills
    assert "c++" not in skills # Should not match unrelated skill

def test_extract_by_nlp(skill_extractor_instance):
    """Test NLP-based skill extraction using Spacy."""
    if skill_extractor_instance.nlp is None:
        pytest.skip("Spacy model not loaded, skipping NLP test.")
    
    text = "Developed applications using Node.js and deployed on AWS. Strong in Machine Learning."
    skills = skill_extractor_instance._extract_by_nlp(text)
    assert "node.js" in skills
    assert "aws" in skills
    assert "machine learning" in skills
    assert "developed" not in skills # Should not extract verbs

def test_extract_by_patterns(skill_extractor_instance):
    """Test pattern-based skill extraction."""
    text = "Skills: Python, React, SQL. Technologies used: Docker and Kubernetes."
    skills = skill_extractor_instance._extract_by_patterns(text)
    assert "python" in skills
    assert "react" in skills
    assert "sql" in skills
    assert "docker" in skills
    assert "kubernetes" in skills
    assert "skills" not in skills # Should not extract the keyword itself

def test_extract_skills_overall(skill_extractor_instance):
    """Test the main extract_skills method combining all techniques."""
    text = """
    Resume Summary:
    Experienced Software Engineer with strong skills in Python, Django, and PostgreSQL.
    Familiar with AWS cloud platform and Agile methodologies.
    Also have knowledge of JavaScript and React.
    """
    extracted_skills = skill_extractor_instance.extract_skills(text)
    
    assert "python" in extracted_skills
    assert "django" in extracted_skills
    assert "postgresql" in extracted_skills
    assert "aws" in extracted_skills
    assert "agile" in extracted_skills
    assert "javascript" in extracted_skills
    assert "react" in extracted_skills
    assert "experienced" not in extracted_skills # Ensure non-skills are filtered

def test_categorize_skills(skill_extractor_instance):
    """Test skill categorization."""
    skills_to_categorize = ["Python", "React", "MongoDB", "Communication", "Docker", "UncategorizedSkill"]
    categorized = skill_extractor_instance.categorize_skills(skills_to_categorize)

    assert "programming_languages" in categorized
    assert "Python" in categorized["programming_languages"]

    assert "web_technologies" in categorized
    assert "React" in categorized["web_technologies"]

    assert "databases" in categorized
    assert "MongoDB" in categorized["databases"]

    assert "soft_skills" in categorized
    assert "Communication" in categorized["soft_skills"]

    assert "cloud_platforms" in categorized # Docker is often categorized under cloud/devops
    assert "Docker" in categorized["cloud_platforms"]

    assert "other" in categorized
    assert "UncategorizedSkill" in categorized["other"]

def test_get_skill_relevance_score(skill_extractor_instance):
    """Test skill relevance scoring."""
    context = "I am an expert in Python. I have used Python extensively in my projects."
    
    score_python = skill_extractor_instance.get_skill_relevance_score("Python", context)
    assert score_python > 0
    assert score_python <= 100 # Ensure score is capped

    score_java = skill_extractor_instance.get_skill_relevance_score("Java", context)
    assert score_java == 0 # Java is not in context

    context_2 = "Proficient with SQL and database management."
    score_sql = skill_extractor_instance.get_skill_relevance_score("SQL", context_2)
    assert score_sql > 0

    # Test with empty context
    score_empty_context = skill_extractor_instance.get_skill_relevance_score("Python", "")
    assert score_empty_context == 0.0
