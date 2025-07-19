// frontend/static/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    // --- API Base URL ---
    // Make sure this matches your FastAPI backend's address
    const API_BASE_URL = 'http://localhost:8000/api';

    // --- Common Elements (conditionally checked for existence on the current page) ---
    const uploadResumeForm = document.getElementById('uploadResumeForm');
    const resumeFile = document.getElementById('resumeFile');
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadProgressBar = document.getElementById('uploadProgressBar');

    const addJobDescriptionForm = document.getElementById('addJobDescriptionForm');
    const jobTitleInput = document.getElementById('jobTitle');
    const companyNameInput = document.getElementById('companyName');
    const jobDescriptionTextInput = document.getElementById('jobDescriptionText');
    const jobStatus = document.getElementById('jobStatus');

    const jobSelect = document.getElementById('jobSelect'); // Exists only on dashboard.html
    const matchResumesBtn = document.getElementById('matchResumesBtn'); // Exists only on dashboard.html
    const matchStatus = document.getElementById('matchStatus'); // Exists only on dashboard.html
    const matchingResultsDiv = document.getElementById('matchingResults'); // Exists only on dashboard.html

    // These divs exist on multiple pages, so their population logic needs to be careful
    const resumesListDiv = document.getElementById('resumesList'); // Used on dashboard.html and uploaded_resumes.html
    const jobDescriptionsListDiv = document.getElementById('jobDescriptionsList'); // Used on dashboard.html and job_descriptions.html

    // Modals (expected on dashboard.html, uploaded_resumes.html, job_descriptions.html)
    const resumeDetailsModal = document.getElementById('resumeDetailsModal');
    const jobDetailsModal = document.getElementById('jobDetailsModal');
    const modalResumeFilename = document.getElementById('modalResumeFilename');
    const modalResumeSkills = document.getElementById('modalResumeSkills');
    const modalResumeRawText = document.getElementById('modalResumeRawText');
    const modalJobTitle = document.getElementById('modalJobTitle');
    const modalJobCompany = document.getElementById('modalJobCompany');
    const modalJobRequiredSkills = document.getElementById('modalJobRequiredSkills');
    const modalJobDescriptionText = document.getElementById('modalJobDescriptionText');

    // Close buttons for modals
    document.querySelectorAll('.close-button').forEach(button => {
        button.addEventListener('click', () => {
            if (resumeDetailsModal) resumeDetailsModal.classList.remove('modal-active');
            if (jobDetailsModal) jobDetailsModal.classList.remove('modal-active');
        });
    });

    // Close modal when clicking outside of the content
    window.addEventListener('click', (event) => {
        if (resumeDetailsModal && event.target === resumeDetailsModal) {
            resumeDetailsModal.classList.remove('modal-active');
        }
        if (jobDetailsModal && event.target === jobDetailsModal) {
            jobDetailsModal.classList.remove('modal-active');
        }
    });

    // --- Helper Functions ---

    /**
     * Displays a status message with a given color.
     * @param {HTMLElement} element - The DOM element to display the message in.
     * @param {string} message - The message to display.
     * @param {string} type - 'success', 'error', or 'info' for styling.
     */
    const showStatus = (element, message, type) => {
        if (!element) return; // Guard against element not existing on current page
        element.textContent = message;
        element.className = `mt-4 text-sm font-medium ${
            type === 'success' ? 'text-green-700' :
            type === 'error' ? 'text-red-700' :
            'text-gray-700'
        }`;
    };

    /**
     * Updates the progress bar.
     * @param {number} percentage - The percentage to set the progress bar to (0-100).
     */
    const updateProgressBar = (percentage) => {
        if (uploadProgressBar) { // Guard against element not existing on current page
            uploadProgressBar.style.width = `${percentage}%`;
            uploadProgressBar.style.setProperty('--progress-width', `${percentage}%`); // For CSS animation
        }
    };

    /**
     * Renders a list of skills as clickable tags.
     * @param {HTMLElement} container - The DOM element to append skill tags to.
     * @param {string[]} skills - An array of skill strings.
     * @param {string} type - 'matched', 'missing', 'additional' for styling.
     */
    const renderSkillTags = (container, skills, type = '') => {
        if (!container) return; // Guard against element not existing on current page
        container.innerHTML = ''; // Clear previous tags
        if (skills && skills.length > 0) {
            skills.forEach(skill => {
                const span = document.createElement('span');
                span.className = `skill-tag ${type}-skill`;
                span.textContent = skill;
                container.appendChild(span);
            });
        } else {
            container.textContent = 'N/A';
            container.className = 'text-gray-500 text-sm';
        }
    };

    // --- Fetch Data Functions ---

    /**
     * Fetches all resumes from the backend and displays them.
     * This function is called on the dashboard (dashboard.html) and uploaded_resumes.html.
     */
    const fetchAndDisplayResumes = async () => {
        if (!resumesListDiv) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/resumes`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const resumes = await response.json();
            resumesListDiv.innerHTML = ''; // Clear previous list

            if (resumes.length === 0) {
                resumesListDiv.innerHTML = '<p class="text-gray-500">No resumes uploaded yet.</p>';
                return;
            }

            resumes.forEach(resume => {
                const resumeCard = document.createElement('div');
                resumeCard.className = 'list-item flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200';
                const uploadDate = resume.upload_date ? new Date(resume.upload_date).toLocaleDateString() : 'N/A';
                const skillsPreview = resume.extracted_skills && resume.extracted_skills.length > 0
                    ? resume.extracted_skills.join(', ').substring(0, 100) + (resume.extracted_skills.join(', ').length > 100 ? '...' : '')
                    : 'No skills extracted';

                resumeCard.innerHTML = `
                    <div class="flex-grow mb-2 sm:mb-0">
                        <p class="list-item-title text-lg text-indigo-700">${resume.filename}</p>
                        <p class="list-item-details text-gray-600">Uploaded: ${uploadDate}</p>
                        <p class="list-item-details text-gray-500 text-sm mt-1">Skills: ${skillsPreview}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button data-resume-id="${resume.id}" class="view-resume-btn btn-secondary px-3 py-1 text-sm">View Details</button>
                        <button data-resume-id="${resume.id}" class="delete-resume-btn btn-secondary px-3 py-1 text-sm bg-red-100 text-red-700 hover:bg-red-200">Delete</button>
                    </div>
                `;
                resumesListDiv.appendChild(resumeCard);
            });

            document.querySelectorAll('.view-resume-btn').forEach(button => {
                button.addEventListener('click', async (event) => {
                    const resumeId = event.target.dataset.resumeId;
                    await fetchResumeDetails(resumeId);
                });
            });

            document.querySelectorAll('.delete-resume-btn').forEach(button => {
                button.addEventListener('click', async (event) => {
                    const resumeId = event.target.dataset.resumeId;
                    if (confirm('Are you sure you want to delete this resume? This action cannot be undone.')) {
                        await deleteResume(resumeId);
                    }
                });
            });

        }
        catch (error) {
            console.error('Error fetching resumes:', error);
            if (resumesListDiv) {
                resumesListDiv.innerHTML = '<p class="text-red-700">Failed to load resumes. Please try again.</p>';
            }
        }
    };

    /**
     * Fetches details for a specific resume and displays them in a modal.
     * @param {number} resumeId - The ID of the resume to fetch.
     */
    const fetchResumeDetails = async (resumeId) => {
        if (!resumeDetailsModal) return; // Guard against modal not existing on current page
        try {
            const response = await fetch(`${API_BASE_URL}/resume/${resumeId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const resume = await response.json();

            modalResumeFilename.textContent = resume.filename;
            renderSkillTags(modalResumeSkills, resume.extracted_skills);
            modalResumeRawText.textContent = resume.raw_text;
            resumeDetailsModal.classList.add('modal-active'); // Show modal
        } catch (error) {
            console.error('Error fetching resume details:', error);
            alert('Failed to load resume details. Check console for more info.');
        }
    };

    /**
     * Deletes a resume from the database.
     * @param {number} resumeId - The ID of the resume to delete.
     */
    const deleteResume = async (resumeId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/resume/${resumeId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            alert(result.message);
            const currentPage = window.location.pathname;
            if (currentPage === '/dashboard' || currentPage === '/uploaded-resumes') {
                fetchAndDisplayResumes(); // Refresh on dashboard or uploaded resumes page
            }
        } catch (error) {
            console.error('Error deleting resume:', error);
            alert('Failed to delete resume. Check console for more info.');
        }
    };

    /**
     * Fetches all job descriptions from the backend and displays them.
     * Populates the job selection dropdown on the dashboard.
     * This function is called on the dashboard (dashboard.html) and job_descriptions.html.
     */
    const fetchAndDisplayJobDescriptions = async () => {
        // This function should only proceed if 'jobDescriptionsListDiv' or 'jobSelect' is actually present.
        if (!jobDescriptionsListDiv && !jobSelect) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/job-descriptions`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const jobs = await response.json();
            
            if (jobDescriptionsListDiv) { // For the list of all jobs on dashboard.html or job_descriptions.html
                jobDescriptionsListDiv.innerHTML = '';
                if (jobs.length === 0) {
                    jobDescriptionsListDiv.innerHTML = '<p class="text-gray-500">No job descriptions added yet.</p>';
                } else {
                    jobs.forEach(job => {
                        const jobCard = document.createElement('div');
                        jobCard.className = 'list-item flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200';
                        const createdDate = job.created_date ? new Date(job.created_date).toLocaleDateString() : 'N/A';
                        const requiredSkillsPreview = job.required_skills && job.required_skills.length > 0
                            ? job.required_skills.join(', ').substring(0, 100) + (job.required_skills.join(', ').length > 100 ? '...' : '')
                            : 'No skills specified';

                        jobCard.innerHTML = `
                            <div class="flex-grow mb-2 sm:mb-0">
                                <p class="list-item-title text-lg text-indigo-700">${job.title} at ${job.company}</p>
                                <p class="list-item-details text-gray-600">Added: ${createdDate}</p>
                                <p class="list-item-details text-gray-500 text-sm mt-1">Required Skills: ${requiredSkillsPreview}</p>
                            </div>
                            <div class="flex space-x-2">
                                <button data-job-id="${job.id}" class="view-job-btn btn-secondary px-3 py-1 text-sm">View Details</button>
                                <button data-job-id="${job.id}" class="delete-job-btn btn-secondary px-3 py-1 text-sm bg-red-100 text-red-700 hover:bg-red-200">Delete</button>
                            </div>
                        `;
                        jobDescriptionsListDiv.appendChild(jobCard);
                    });
                    document.querySelectorAll('.view-job-btn').forEach(button => {
                        button.addEventListener('click', async (event) => {
                            const jobId = event.target.dataset.jobId;
                            await fetchJobDetails(jobId);
                        });
                    });
                    // Add event listeners for delete job description buttons
                    document.querySelectorAll('.delete-job-btn').forEach(button => {
                        button.addEventListener('click', async (event) => {
                            const jobId = event.target.dataset.jobId;
                            if (confirm('Are you sure you want to delete this job description? This action cannot be undone.')) {
                                await deleteJobDescription(jobId);
                            }
                        });
                    });
                }
            }

            if (jobSelect) { // For the job selection dropdown on dashboard.html
                jobSelect.innerHTML = '<option value="">-- Select a Job --</option>';
                jobs.forEach(job => {
                    const option = document.createElement('option');
                    option.value = job.id;
                    option.textContent = `${job.title} at ${job.company}`;
                    jobSelect.appendChild(option);
                });
            }

        } catch (error) {
            console.error('Error fetching job descriptions:', error);
            if (jobDescriptionsListDiv) {
                jobDescriptionsListDiv.innerHTML = '<p class="text-red-700">Failed to load job descriptions. Please try again.</p>';
            }
            if (jobSelect) {
                jobSelect.innerHTML = '<option value="">-- Failed to load jobs --</option>';
            }
        }
    };

    /**
     * Fetches details for a specific job description and displays them in a modal.
     * @param {number} jobId - The ID of the job description to fetch.
     */
    const fetchJobDetails = async (jobId) => {
        if (!jobDetailsModal) return; // Guard
        try {
            const response = await fetch(`${API_BASE_URL}/job-description/${jobId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const job = await response.json();

            modalJobTitle.textContent = job.title;
            modalJobCompany.textContent = job.company;
            renderSkillTags(modalJobRequiredSkills, job.required_skills);
            modalJobDescriptionText.textContent = job.description;
            jobDetailsModal.classList.add('modal-active'); // Show modal
        } catch (error) {
            console.error('Error fetching job details:', error);
            alert('Failed to load job details. Check console for more info.');
        }
    };

    /**
     * Deletes a job description from the database.
     * @param {number} jobId - The ID of the job description to delete.
     */
    const deleteJobDescription = async (jobId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/job-description/${jobId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            alert(result.message);
            const currentPage = window.location.pathname;
            if (currentPage === '/dashboard' || currentPage === '/job-descriptions-page') {
                fetchAndDisplayJobDescriptions(); // Refresh on dashboard or job descriptions page
            }
        } catch (error) {
            console.error('Error deleting job description:', error);
            alert('Failed to delete job description. Check console for more info.');
        }
    };

    // --- Event Listeners ---

    // Resume Upload Form Submission (only on dashboard.html)
    if (uploadResumeForm) {
        uploadResumeForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            showStatus(uploadStatus, 'Uploading and processing...', 'info');
            updateProgressBar(0);

            const file = resumeFile.files[0];
            if (!file) {
                showStatus(uploadStatus, 'Please select a file.', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch(`${API_BASE_URL}/upload-resume`, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                showStatus(uploadStatus, `Success: ${result.filename} uploaded. Skills extracted: ${result.extracted_skills.length}`, 'success');
                updateProgressBar(100);
                uploadResumeForm.reset();
                const currentPage = window.location.pathname;
                if (currentPage === '/dashboard') {
                    fetchAndDisplayResumes(); // Optionally refresh resumes on dashboard if needed
                }
            } catch (error) {
                console.error('Error uploading resume:', error);
                showStatus(uploadStatus, `Error: ${error.message}`, 'error');
                updateProgressBar(0);
            }
        });
    }

    // Add Job Description Form Submission (only on add_job.html)
    if (addJobDescriptionForm) {
        addJobDescriptionForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            showStatus(jobStatus, 'Adding job description...', 'info');

            const jobData = {
                title: jobTitleInput.value,
                company: companyNameInput.value,
                description: jobDescriptionTextInput.value
            };

            try {
                const response = await fetch(`${API_BASE_URL}/job-description`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(jobData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                showStatus(jobStatus, `Success: Job "${result.title}" added. Skills extracted: ${result.required_skills.length}`, 'success');
                addJobDescriptionForm.reset();
            } catch (error) {
                console.error('Error adding job description:', error);
                showStatus(jobStatus, `Error: ${error.message}`, 'error');
            }
        });
    }

    // Match Resumes Button Click (only on dashboard.html)
    if (matchResumesBtn) {
        matchResumesBtn.addEventListener('click', async () => {
            const selectedJobId = jobSelect.value;
            if (!selectedJobId) {
                showStatus(matchStatus, 'Please select a job description first.', 'error');
                return;
            }

            showStatus(matchStatus, 'Matching resumes...', 'info');
            if (matchingResultsDiv) {
                matchingResultsDiv.innerHTML = '<p class="text-gray-500">Loading matching results...</p>';
            }

            const formData = new FormData();
            formData.append('job_id', selectedJobId);

            try {
                const response = await fetch(`${API_BASE_URL}/match-resumes`, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const results = await response.json();
                showStatus(matchStatus, `Matching complete. Found ${results.length} results.`, 'success');
                renderMatchingResults(results);

            } catch (error) {
                console.error('Error matching resumes:', error);
                showStatus(matchStatus, `Error: ${error.message}`, 'error');
                if (matchingResultsDiv) {
                    matchingResultsDiv.innerHTML = '<p class="text-red-700">Failed to load matching results. Please try again.</p>';
                }
            }
        });
    }

    /**
     * Renders the matching results in the UI.
     * @param {Array} results - Array of resume matching results.
     */
    const renderMatchingResults = (results) => {
        if (!matchingResultsDiv) return;
        matchingResultsDiv.innerHTML = '';

        if (results.length === 0) {
            matchingResultsDiv.innerHTML = '<p class="text-gray-500">No matching resumes found for the selected job.</p>';
            return;
        }

        results.forEach(result => {
            const resultCard = document.createElement('div');
            resultCard.className = 'card p-6 mb-4 border border-gray-200 shadow-sm';
            resultCard.innerHTML = `
                <h3 class="text-xl font-semibold text-indigo-800 mb-2">${result.filename}</h3>
                <div class="flex items-center mb-4">
                    <div class="score-bar-container flex-grow">
                        <div class="score-bar" style="width: ${result.overall_score}%;"></div>
                    </div>
                    <span class="score-text">${result.overall_score}% Match</span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <p class="font-semibold text-gray-700 mb-1">Matched Skills (${result.matched_skills.length}):</p>
                        <div class="flex flex-wrap gap-2" id="matchedSkills-${result.resume_id}-${result.job_id}"></div>
                    </div>
                    <div>
                        <p class="font-semibold text-gray-700 mb-1">Missing Skills (${result.missing_skills.length}):</p>
                        <div class="flex flex-wrap gap-2" id="missingSkills-${result.resume_id}-${result.job_id}"></div>
                    </div>
                </div>
            `;
            matchingResultsDiv.appendChild(resultCard);

            renderSkillTags(document.getElementById(`matchedSkills-${result.resume_id}-${result.job_id}`), result.matched_skills, 'matched');
            renderSkillTags(document.getElementById(`missingSkills-${result.resume_id}-${result.job_id}`), result.missing_skills, 'missing');
        });
    };

    // --- Initial Load Logic ---
    const currentPage = window.location.pathname;

    // Check if on the new landing page
    if (currentPage === '/' || currentPage === '/index.html') {
        // No data fetching needed for the landing page
    }
    // Check if on the dashboard page
    else if (currentPage === '/dashboard') {
        // Dashboard needs job descriptions for the dropdown and list
        fetchAndDisplayJobDescriptions();
        // It also needs resumes for the upload section's list (if you put it back)
        // For now, it only has the upload form and match section
    }
    // Check if on the Add Job page
    else if (currentPage === '/add-job' || currentPage === '/add_job.html') {
        // No initial data fetching for lists on this page
    }
    // Check if on the Uploaded Resumes page
    else if (currentPage === '/uploaded-resumes') {
        fetchAndDisplayResumes(); // Fetch and display resumes for this dedicated page
    }
    // Check if on the Job Descriptions page
    else if (currentPage === '/job-descriptions-page') {
        fetchAndDisplayJobDescriptions(); // Fetch and display job descriptions for this dedicated page
    }
});
