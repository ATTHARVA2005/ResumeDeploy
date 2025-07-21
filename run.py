# run.py

import uvicorn
import os
import sys
import json
from pathlib import Path

print("App running on http://localhost:8000/")

# Add the project root directory to the Python path
# This ensures that 'backend' can be imported as a top-level package by uvicorn
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure necessary directories exist
def setup_directories():
    """Create necessary directories for the application."""
    directories = [
        "uploads",  # For resume uploads
        "data",     # For skills_database.json and sample_job_descriptions.json
        "frontend/static/css",
        "frontend/static/js",
        "tests"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("All necessary directories ensured.")

# Ensure skills_database.json exists with default content if not present
def ensure_skills_database():
    """Ensures skills_database.json exists, creating it with default content if not."""
    skills_path = Path("data/skills_database.json")
    if not skills_path.exists():
        print("skills_database.json not found. Creating with default content...")
        default_skills = {
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
        with open(skills_path, 'w', encoding='utf-8') as f: # Added encoding
            json.dump(default_skills, f, indent=4)
        print("Default skills_database.json created.")

# Ensure sample_job_descriptions.json exists with default content if not present
def ensure_sample_job_descriptions():
    """Ensures sample_job_descriptions.json exists, creating it with default content if not."""
    jobs_path = Path("data/sample_job_descriptions.json")
    if not jobs_path.exists():
        print("sample_job_descriptions.json not found. Creating with default content...")
        default_jobs = [
            {
                "title": "Senior Software Engineer",
                "company": "InnovateX Corp.",
                "description": "InnovateX Corp. is seeking a highly skilled Senior Software Engineer with expertise in Python, Django, and PostgreSQL. The ideal candidate will have strong experience with AWS, Docker, and CI/CD pipelines. Responsibilities include designing, developing, and deploying scalable web applications, mentoring junior developers, and contributing to architectural decisions. Excellent problem-solving and communication skills are a must. Experience with React or Angular is a plus."
            },
            {
                "title": "Data Scientist",
                "company": "Analytics Hub",
                "description": "Analytics Hub is looking for a passionate Data Scientist to join our growing team. You will be responsible for collecting, analyzing, and interpreting large datasets. Required skills include Python (Pandas, NumPy, Scikit-learn), R, SQL, and strong statistical modeling abilities. Experience with machine learning algorithms, data visualization tools (Tableau, Power BI), and cloud platforms (GCP, Azure) is highly desirable. Strong communication and presentation skills are essential for explaining complex findings to stakeholders."
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudBurst Solutions",
                "description": "CloudBurst Solutions is hiring a talented DevOps Engineer to build and maintain our automated infrastructure. Key requirements include extensive experience with Linux, Docker, Kubernetes, and Jenkins. Proficiency in scripting (Bash, Python) and familiarity with configuration management tools like Ansible or Terraform is crucial. Experience with AWS or Azure cloud environments, monitoring tools (Prometheus, Grafana), and Git is expected. Agile methodology experience is a plus."
            },
            {
                "title": "Frontend Developer (React)",
                "company": "Creative UI Labs",
                "description": "Creative UI Labs seeks a skilled Frontend Developer with a strong focus on React.js. Candidates must be proficient in JavaScript, HTML, CSS, and modern frontend frameworks. Experience with Redux, Webpack, and responsive design is required. Familiarity with RESTful APIs, Git, and UI/UX principles is beneficial. Excellent teamwork and problem-solving skills are highly valued."
            }
        ]
        with open(jobs_path, 'w', encoding='utf-8') as f: # Added encoding
            json.dump(default_jobs, f, indent=4)
        print("Default sample_job_descriptions.json created.")


if __name__ == "__main__":
    # Perform initial setup
    setup_directories()
    ensure_skills_database()
    ensure_sample_job_descriptions()

    # Run the FastAPI application
    # IMPORTANT CHANGE: Specify the app as 'backend.main:app'
    # This tells uvicorn that 'main' is inside the 'backend' package.
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
    # Removed app_dir="backend" as it's redundant/can conflict when using full module path
