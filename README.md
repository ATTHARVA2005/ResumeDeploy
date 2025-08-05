# ResumeRank: Your AI-Powered Recruitment Assistant

Creator: Attharva Gupta
URL: https://resumerank-8pfn.onrender.com/
🚀 Introduction

ResumeRank is an innovative, full-stack web application designed to revolutionize the recruitment process. Leveraging the power of Artificial Intelligence, specifically Google's Gemini API, ResumeRank automates the tedious tasks of resume and job description analysis. It provides intelligent matching capabilities, helping recruiters and hiring managers find the best candidates faster, with unbiased and quantifiable results.
Say goodbye to manual resume screening and hello to efficient, data-driven hiring!

✨ Key Features

ResumeRank offers a comprehensive suite of features to streamline your recruitment workflow:

🧠 AI-Powered Resume Analysis:
* **Intelligent Extraction**: Utilizes the Google Gemini API to deeply analyze uploaded resumes (PDF, DOCX, TXT formats).
* **Structured Data Output**: Automatically extracts key information such as: Full Name, Email, Phone, LinkedIn/GitHub URLs, Total Years of Experience, Highest Education Level & Major, a comprehensive list of Extracted Skills, and detailed Work Experience entries (Title, Company, Dates, Description).
* **Accuracy & Efficiency**: Reduces human error and significantly speeds up the resume review process by providing structured insights.

📋 AI-Powered Job Description Analysis:
* **Effortless Input**: Add job descriptions either by pasting the full text or by providing a URL to a job posting. ResumeRank will automatically fetch the content from the URL, intelligently extract all critical requirements, and pre-fill the form for your review.
* **Key Data Points**: Extracts: Required Experience (Years), Required Skills, Required Certifications, Required Education Level & Major.
* **Simplified Workflow**: Eliminates the need for manual entry of individual requirements, allowing users to focus on the job details.

🎯 Intelligent Matching Algorithm:
* **Comprehensive Scoring**: Calculates a quantifiable match score between a resume and a job description based on multiple weighted criteria:
    * **Skills Alignment**: Compares extracted skills using exact, fuzzy, and semantic matching (TF-IDF cosine similarity).
    * **Experience Matching**: Evaluates if the candidate's years of experience meet the job's requirements.
    * **Certifications Matching**: Identifies alignment with required professional certifications.
    * **Education Matching**: Compares highest education level and academic major, intelligently handling specializations (e.g., "Computer Science (AI)" matches "Computer Science").
* **Customizable Ranking**: Users can adjust the weight of each criterion (Skills, Experience, Certifications, Education) to tailor match results to their specific hiring priorities.
* **Unbiased Results**: Provides objective scores to help mitigate unconscious bias in candidate selection.
* **Detailed Breakdown**: Offers insights into matched, missing, and additional skills, along with individual scores for experience, certifications, and education.

🔐 Secure User Authentication:
* **Seamless Onboarding**: Supports user registration and login with secure password hashing.
* **Admin Access**: A separate, secure login portal is available for administrators to access the admin panel.
* **Session Management**: Utilizes JWT (JSON Web Tokens) for secure user sessions.
* **Protected Access**: Ensures only authenticated users can access dashboard features and sensitive data.

📄 Resume Management:
* **Easy Upload**: Simple interface for uploading resumes in various formats.
* **Centralized Storage**: Stores parsed resume data securely.
* **View & Delete**: Allows users to view detailed extracted information for each resume and delete entries when no longer needed.
* **Search**: A search function allows for quick filtering of resumes by filename or content.

💼 Job Description Management:
* **Effortless Addition**: Add new job descriptions by simply providing a title, company, and pasting the full job text or a URL.
* **View, Edit & Delete**: Manage your job descriptions, view extracted requirements, and update them as needed (re-extracting details from the updated description).
* **Search**: A search function allows for quick filtering of job descriptions.

👨‍💻 Admin Panel:
* **User Management**: An exclusive, secure administrative panel allows for easy management of all registered users.
* **Total User Count**: The admin dashboard provides a quick overview of the total number of users in the system.
* **User List & Deletion**: Admins can view a list of all users, their names, and emails, and have the ability to delete user accounts and all associated data.

✨ Intuitive User Interface (UI/UX):
* **Modern Design**: Clean, responsive, and visually appealing interface built with Tailwind CSS.
* **Theme Toggle**: Users can switch between a light and dark theme, with their preference saved for future visits.
* **Consistent Theme**: Utilizes a harmonious color palette for a professional look.
* **Loading States**: Provides visual feedback with spinners during asynchronous operations (e.g., uploads, processing, matching).
* **Clear Status Messages**: Informative success, error, and info messages for user actions.
* **Empty States**: Friendly messages and icons guide users when lists (resumes, jobs, matches) are empty.
* **Responsive Layout**: Adapts seamlessly to various screen sizes (mobile, tablet, desktop).

🛠️ Technology Stack

ResumeRank is built with a robust and modern technology stack:
* **Backend**:
    * FastAPI: High-performance Python web framework for building the API.
    * Python: The core programming language.
    * SQLAlchemy: Python SQL toolkit and Object Relational Mapper (ORM) for database interactions.
    * PostgreSQL: (Recommended for Production) Robust and scalable relational database.
    * Uvicorn: ASGI server for running FastAPI applications.
    * Gunicorn: (For Production) WSGI HTTP server to manage Uvicorn worker processes.
    * google-generativeai: Python client library for interacting with the Gemini API.
    * pdfminer.six: For extracting text from PDF files.
    * python-docx: For extracting text from DOCX files.
    * scikit-learn: For TF-IDF vectorization in semantic skill matching.
    * fuzzywuzzy: For fuzzy string matching of skills.
    * python-Levenshtein: (Optional) C-backed implementation for faster fuzzy string comparisons.
    * aiofiles: For asynchronous file operations.
    * passlib[bcrypt]: For secure password hashing.
    * python-jose[cryptography]: For JWT (JSON Web Token) handling.
    * python-dotenv: For loading environment variables in local development.
* **Frontend**:
    * HTML5: Structure of the web pages.
    * CSS3: Styling, including custom CSS and the Tailwind CSS framework.
    * JavaScript: Client-side interactivity, API calls, and dynamic UI updates.

⚙️ Setup and Installation (Local Development)

Follow these steps to get ResumeRank running on your local machine:
1.  **Clone the Repository**:
    ```
    git clone [https://github.com/ATTHARVA2005/ResumeDeploy.git](https://github.com/ATTHARVA2005/ResumeDeploy.git)
    cd ResumeDeploy
    ```
2.  **Create a Python Virtual Environment**:
    ```
    python -m venv venv
    ```
3.  **Activate the Virtual Environment**:
    * Windows: `.\venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`
4.  **Install Dependencies**: Ensure your `requirements.txt` is up-to-date (it should contain all listed dependencies in the "Technology Stack" section).
    ```
    pip install -r requirements.txt
    ```
5.  **Set Up Environment Variables**:
    * Create a file named `.env` in the root directory of your project.
    * Add your environment variables to this file:
        ```
        GEMINI_API_KEY='YOUR_GOOGLE_GEMINI_API_KEY_HERE'
        SECRET_KEY='a_very_strong_random_secret_key_for_jwt_signing'
        DATABASE_URL='sqlite:///./resume_screening.db'
        ADMIN_EMAIL='your_admin_email@example.com'
        ADMIN_PASSWORD='your_strong_admin_password'
        ```
    * Replace the placeholder values with your actual keys and desired admin credentials.
6.  **Initialize Database**:
    * Your application uses SQLAlchemy and by default with the above `DATABASE_URL`, it will create an SQLite database file.
    * **Important**: If you have an old database file from a previous schema, you **must delete it** before running the app again to apply the latest schema changes.
7.  **Run the Application**:
    ```
    python run.py
    ```
    You should see output indicating that Uvicorn is running, typically on `http://0.0.0.0:8000`.
8.  **Access in Browser**: Open your web browser and navigate to `http://localhost:8000/`.

💡 Usage Guide

* **Register & Log In**:
    * Navigate to your application's URL.
    * Click "Go to Dashboard" or directly go to `/signup` to create a new account.
    * Log in with your new credentials.
* **Admin Login**:
    * For admin access, go to `/admin-login` and use the credentials specified in your `.env` file.
* **Upload a Resume**:
    * On the Dashboard, use the "Upload Resume" section.
    * Select a `.pdf`, `.docx`, or `.txt` resume file and click "Upload & Process".
* **Add a Job Description**:
    * On the Dashboard, use the "Add New Job Description" section.
    * Choose to either manually enter the details or provide a URL to a job posting.
    * If using a URL, click "Fetch from URL & Add Job", and the form will be pre-filled for your review.
* **Match Resumes**:
    * On the Dashboard, in the "Match Resumes" section.
    * Select a job description from the dropdown.
    * Click "Match Resumes". The system will calculate match scores for all your uploaded resumes against the selected job.
* **View Details & Manage**:
    * Navigate to "Uploaded Resumes" or "Job Descriptions" pages to see your entries.
    * Use the search bar to filter results quickly.
    * Click "View Details" to see the AI-extracted information for resumes or job requirements.
    * Use "Edit" (for jobs) or "Delete" buttons to manage your entries.
* **Admin Actions**:
    * Log in via the admin portal.
    * View the total number of users on the dashboard.
    * Navigate to the "List of Users" page to search, view, and delete user accounts.

🔗 Links

* **Hosted Tool**: https://resumerank-8pfn.onrender.com/
* **GitHub**: https://github.com/ATTHARVA2005/ResumeDeploy
* **LinkedIn**: www.linkedin.com/in/attharva-gupta-1856282a0
