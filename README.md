# ResumeRank: Your AI-Powered Recruitment Assistant

**Creator:** Attharva Gupta
**URL:** https://resumerank-8pfn.onrender.com/

---

## 🚀 Introduction

ResumeRank is an innovative, full-stack web application designed to revolutionize the recruitment process. Leveraging the power of Artificial Intelligence, specifically Google's Gemini API, ResumeRank automates the tedious tasks of resume and job description analysis. It provides intelligent matching capabilities, helping recruiters and hiring managers find the best candidates faster, with unbiased and quantifiable results.

Say goodbye to manual resume screening and hello to efficient, data-driven hiring!

---

## ✨ Key Features

ResumeRank offers a comprehensive suite of features to streamline your recruitment workflow:

1.  **🧠 AI-Powered Resume Analysis:**
    * **Intelligent Extraction:** Utilizes the Google Gemini API to deeply analyze uploaded resumes (PDF, DOCX, TXT formats).
    * **Structured Data Output:** Automatically extracts key information such as:
        * Full Name, Email, Phone, LinkedIn/GitHub URLs
        * Total Years of Experience
        * Highest Education Level & Major
        * A comprehensive list of Extracted Skills
        * Detailed Work Experience entries (Title, Company, Dates, Description)
    * **Accuracy & Efficiency:** Reduces human error and significantly speeds up the resume review process by providing structured insights.

2.  **📋 AI-Powered Job Description Analysis:**
    * **Automated Requirement Extraction:** Simply paste the full job description text, and ResumeRank (powered by Gemini) will intelligently extract all critical requirements.
    * **Key Data Points:** Extracts:
        * Required Experience (Years)
        * Required Skills
        * Required Certifications
        * Required Education Level & Major
    * **Simplified Input:** Eliminates the need for manual entry of individual requirements, allowing users to focus on the job details.

3.  **🎯 Intelligent Matching Algorithm:**
    * **Comprehensive Scoring:** Calculates a quantifiable match score between a resume and a job description based on multiple weighted criteria:
        * **Skills Alignment:** Compares extracted skills using exact, fuzzy, and semantic matching (TF-IDF cosine similarity).
        * **Experience Matching:** Evaluates if the candidate's years of experience meet the job's requirements.
        * **Certifications Matching:** Identifies alignment with required professional certifications.
        * **Education Matching:** Compares highest education level and academic major, intelligently handling specializations (e.g., "Computer Science (AI)" matches "Computer Science").
    * **Unbiased Results:** Provides objective scores to help mitigate unconscious bias in candidate selection.
    * **Detailed Breakdown:** Offers insights into matched, missing, and additional skills, along with individual scores for experience, certifications, and education.

4.  **🔐 Secure User Authentication:**
    * **Seamless Onboarding:** Supports user registration and login with secure password hashing.
    * **Session Management:** Utilizes JWT (JSON Web Tokens) for secure user sessions.
    * **Protected Access:** Ensures only authenticated users can access dashboard features and sensitive data.

5.  **📄 Resume Management:**
    * **Easy Upload:** Simple interface for uploading resumes in various formats.
    * **Centralized Storage:** Stores parsed resume data securely.
    * **View & Delete:** Allows users to view detailed extracted information for each resume and delete entries when no longer needed.

6.  **💼 Job Description Management:**
    * **Effortless Addition:** Add new job descriptions by simply providing a title, company, and pasting the full job text.
    * **View, Edit & Delete:** Manage your job descriptions, view extracted requirements, and update them as needed (re-extracting details from the updated description).

7.  **✨ Intuitive User Interface (UI/UX):**
    * **Modern Design:** Clean, responsive, and visually appealing interface built with Tailwind CSS.
    * **Consistent Theme:** Utilizes a harmonious color palette for a professional look.
    * **Loading States:** Provides visual feedback with spinners during asynchronous operations (e.g., uploads, processing, matching).
    * **Clear Status Messages:** Informative success, error, and info messages for user actions.
    * **Empty States:** Friendly messages and icons guide users when lists (resumes, jobs, matches) are empty.
    * **Responsive Layout:** Adapts seamlessly to various screen sizes (mobile, tablet, desktop).

---

## 🛠️ Technology Stack

ResumeRank is built with a robust and modern technology stack:

* **Backend:**
    * **FastAPI:** High-performance Python web framework for building the API.
    * **Python:** The core programming language.
    * **SQLAlchemy:** Python SQL toolkit and Object Relational Mapper (ORM) for database interactions.
    * **PostgreSQL:** (Recommended for Production) Robust and scalable relational database.
    * **Uvicorn:** ASGI server for running FastAPI applications.
    * **Gunicorn:** (For Production) WSGI HTTP server to manage Uvicorn worker processes.
    * **`google-generativeai`:** Python client library for interacting with the Gemini API.
    * **`pdfminer.six`:** For extracting text from PDF files.
    * **`python-docx`:** For extracting text from DOCX files.
    * **`scikit-learn`:** For TF-IDF vectorization in semantic skill matching.
    * **`fuzzywuzzy`:** For fuzzy string matching of skills.
    * **`python-Levenshtein`:** (Optional) C-backed implementation for faster fuzzy string comparisons.
    * **`aiofiles`:** For asynchronous file operations.
    * **`passlib[bcrypt]`:** For secure password hashing.
    * **`python-jose[cryptography]`:** For JWT (JSON Web Token) handling.
    * **`python-dotenv`:** For loading environment variables in local development.

* **Frontend:**
    * **HTML5:** Structure of the web pages.
    * **CSS3:** Styling, including custom CSS and the Tailwind CSS framework.
    * **JavaScript:** Client-side interactivity, API calls, and dynamic UI updates.

---

## ⚙️ Setup and Installation (Local Development)

Follow these steps to get ResumeRank running on your local machine:

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd ResumeRank # Or your project's root directory name
    ```

2.  **Create a Python Virtual Environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **Windows:** `.\venv\Scripts\activate`
    * **macOS/Linux:** `source venv/bin/activate`

4.  **Install Dependencies:**
    Ensure your `requirements.txt` is up-to-date (it should contain all listed dependencies in the "Technology Stack" section).
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up Environment Variables:**
    * Create a file named `.env` in the root directory of your project (same level as `run.py`).
    * Add your Gemini API Key and a strong secret key for JWT:
        ```dotenv
        GEMINI_API_KEY='YOUR_GOOGLE_GEMINI_API_KEY_HERE'
        SECRET_KEY='a_very_strong_random_secret_key_for_jwt_signing'
        # DATABASE_URL='sqlite:///./resume_screening.db' # Optional: Default is SQLite, no need to set unless you want to be explicit
        ```
    * Replace `YOUR_GOOGLE_GEMINI_API_KEY_HERE` and `a_very_strong_random_secret_key_for_jwt_signing` with your actual keys.

6.  **Initialize Database:**
    Your application uses SQLAlchemy, and by default, it will create an SQLite database file (`resume_screening.db`) in your project root.
    * **Important:** If you've run the app before and made database schema changes (e.g., adding/removing columns for education fields), you **must delete** any existing `resume_screening.db` file before running the app again to ensure the new schema is applied.

7.  **Run the Application:**
    ```bash
    python run.py
    ```
    You should see output indicating that Uvicorn is running, typically on `http://0.0.0.0:8000`.

8.  **Access in Browser:**
    Open your web browser and navigate to `http://localhost:8000/`.

---

## 💡 Usage Guide

1.  **Register & Log In:**
    * Navigate to your application's URL.
    * Click "Go to Dashboard" or directly go to `/signup` to create a new account.
    * Log in with your new credentials.

2.  **Upload a Resume:**
    * On the Dashboard, use the "Upload Resume" section.
    * Select a `.pdf`, `.docx`, or `.txt` resume file.
    * Click "Upload & Process". The AI will extract details.

3.  **Add a Job Description:**
    * On the Dashboard, use the "Add New Job Description" section.
    * Enter the Job Title and Company Name.
    * **Paste the full job description text** into the provided textarea.
    * Click "Add Job & Extract Requirements". The AI will extract all necessary requirements.

4.  **Match Resumes:**
    * On the Dashboard, in the "Match Resumes" section.
    * Select a job description from the dropdown.
    * Click "Match Resumes". The system will calculate match scores for all your uploaded resumes against the selected job.

5.  **View Details & Manage:**
    * Navigate to "Uploaded Resumes" or "Job Descriptions" pages to see your entries.
    * Click "View Details" to see the AI-extracted information for resumes or job requirements.
    * Use "Edit" (for jobs) or "Delete" buttons to manage your entries.

---

## 🔗 Links
  * **Hosted Tool:** https://resumerank-8pfn.onrender.com/
  * **Githhub:** https://github.com/ATTHARVA2005/ResumeDeploy
  * **LinkedIn:** www.linkedin.com/in/attharva-gupta-1856282a0
## 📈 Future Enhancements (Ideas)

* **Batch Resume Upload & Processing:** Allow multiple resumes to be uploaded simultaneously.
* **Advanced Filtering & Sorting:** Implement more sophisticated options for filtering and sorting resumes and job descriptions.
* **Match Report Generation:** Generate downloadable PDF or CSV reports of match results.
* **User Profiles:** Enhance user profiles with more details and settings.
* **Notification System:** Implement notifications for successful uploads, matches, etc.
* **AI-Powered Feedback:** Provide AI-generated feedback on resumes or job descriptions.
