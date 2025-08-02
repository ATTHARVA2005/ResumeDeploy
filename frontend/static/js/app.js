// frontend/static/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = window.location.origin;

    // --- Utility Functions ---
    const showMessage = (element, message, type = 'info', showSpinner = false) => {
        if (!element) return;
        element.innerHTML = showSpinner ? `<span class="spinner"></span> ${message}` : message;
        element.className = `mt-4 text-sm font-medium status-message-container ${
            type === 'success' ? 'status-message-success' :
            type === 'error' ? 'status-message-error' :
            'status-message-info'
        }`;
        element.style.display = 'flex';
    };

    const clearMessage = (element) => {
        if (!element) return;
        element.innerHTML = '';
        element.className = '';
        element.style.display = 'hidden';
    };

    const toggleButtonState = (button, isLoading) => {
        if (!button) return;
        if (isLoading) {
            button.disabled = true;
            button.innerHTML = `<span class="spinner"></span> Processing...`;
        } else {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
            } else {
                button.innerHTML = 'Submit';
            }
        }
    };

    const getToken = () => localStorage.getItem('accessToken');
    const setToken = (token) => localStorage.setItem('accessToken', token);
    const removeToken = () => localStorage.removeItem('accessToken');

    const isAuthenticated = () => !!getToken();

    const redirectToDashboard = () => {
        if (isAuthenticated()) {
            window.location.href = '/dashboard';
        }
    };

    const redirectToLogin = () => {
        window.location.href = '/login';
    };

    const redirectToAdminLogin = () => {
        window.location.href = '/admin-login';
    };

    const renderSkillTags = (skills, typeClass) => {
        if (!skills || skills.length === 0 || (Array.isArray(skills) && skills.every(s => !s || s.toLowerCase() === 'none'))) {
            return '<span class="text-gray-500">None specified.</span>';
        }
        return skills.filter(s => s && s.toLowerCase() !== 'none').map(skill => `<span class="skill-tag ${typeClass}">${skill}</span>`).join('');
    };

    const renderExperienceEntries = (experience) => {
        if (!experience || experience.length === 0) {
            return '<p class="text-gray-500">No experience details found.</p>';
        }
        return experience.map(entry => `
            <div>
                <p class="font-semibold">${entry.title || 'N/A'} at ${entry.company || 'N/A'}</p>
                <p class="text-xs text-gray-500">${entry.start_date || 'N/A'} - ${entry.end_date || 'N/A'}</p>
                ${entry.description ? `<p class="text-xs text-gray-700 mt-1 whitespace-pre-wrap">${entry.description}</p>` : ''}
            </div>
        `).join('<hr class="my-2 border-gray-200">');
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // --- Modals Logic ---
    const setupModal = (modalId, closeButtonSelector) => {
        const modal = document.getElementById(modalId);
        if (!modal) {
            return null;
        }
        const closeButton = modal.querySelector(closeButtonSelector);

        if (closeButton) {
            closeButton.onclick = () => {
                modal.classList.remove('modal-active');
            };
        }
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.classList.remove('modal-active');
            }
        });
        return modal;
    };

    const jobDetailsModal = setupModal('jobDetailsModal', '.close-button');
    const resumeDetailsModal = setupModal('resumeDetailsModal', '.close-button');
    const jobEditModal = setupModal('jobEditModal', '.close-button[data-modal-id="jobEditModal"]');

    const showJobDetailsModal = (job) => {
        if (!jobDetailsModal) return;
        document.getElementById('modalJobTitle').textContent = job.title;
        document.getElementById('modalJobCompany').textContent = job.company;
        document.getElementById('modalJobDescriptionText').textContent = job.description;
        document.getElementById('modalJobRequiredExperience').textContent = job.required_experience_years !== null && job.required_experience_years !== 0 ? `${job.required_experience_years} years` : 'N/A';
        
        document.getElementById('modalJobRequiredSkills').innerHTML = renderSkillTags(job.required_skills, 'matched-skill');
        document.getElementById('modalJobRequiredCertifications').innerHTML = renderSkillTags(job.required_certifications, 'additional-skill');

        document.getElementById('modalJobRequiredEducation').textContent = job.required_education_level && job.required_education_level.toLowerCase() !== 'none' ? job.required_education_level : 'N/A';
        document.getElementById('modalJobRequiredMajor').textContent = job.required_major && job.required_major.toLowerCase() !== 'none' ? job.required_major : 'N/A';

        jobDetailsModal.classList.add('modal-active');
    };

    const showResumeDetailsModal = (resume) => {
        if (!resumeDetailsModal) return;
        document.getElementById('modalResumeFilename').textContent = resume.filename;
        document.getElementById('modalResumeRawText').textContent = resume.raw_text;
        document.getElementById('modalResumeTotalYearsExperience').textContent = `${resume.total_years_experience || 0} years`;
        
        document.getElementById('modalResumeHighestEducationLevel').textContent = resume.highest_education_level && resume.highest_education_level.toLowerCase() !== 'none' ? resume.highest_education_level : 'N/A';
        document.getElementById('modalResumeMajor').textContent = resume.major && resume.major.toLowerCase() !== 'none' ? resume.major : 'N/A';

        document.getElementById('modalResumeSkills').innerHTML = renderSkillTags(resume.extracted_skills, 'matched-skill');
        document.getElementById('modalResumeExperience').innerHTML = renderExperienceEntries(resume.experience);
        
        resumeDetailsModal.classList.add('modal-active');
    };


    // --- API Calls ---

    const authFetch = async (url, options = {}) => {
        const token = getToken();
        if (!token) {
            console.error('No authentication token found. Redirecting to login.');
            if (url.includes('/admin/')) {
                redirectToAdminLogin();
            } else {
                redirectToLogin();
            }
            throw new Error('No authentication token found.');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        const response = await fetch(url, { ...options, headers });

        if (response.status === 401 || response.status === 403) {
            console.error('Authentication failed or token expired. Clearing token and redirecting.');
            removeToken();
            if (url.includes('/admin/')) {
                alert('Admin session expired or unauthorized. Please log in as admin again.');
                redirectToAdminLogin();
            } else {
                redirectToLogin();
            }
            throw new Error('Authentication failed or token expired.');
        }
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
        }
        return response.json();
    };

    // --- Authentication Logic ---
    const loginForm = document.getElementById('loginForm');
    const loginStatus = document.getElementById('loginStatus');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = e.target.email.value;
            const password = e.target.password.value;
            clearMessage(loginStatus);
            toggleButtonState(loginForm.querySelector('button[type="submit"]'), true);

            try {
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);

                const response = await fetch(`${API_BASE_URL}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData.toString()
                });

                if (response.ok) {
                    const data = await response.json();
                    setToken(data.access_token);
                    showMessage(loginStatus, 'Login successful! Redirecting to dashboard...', 'success', true);
                    setTimeout(redirectToDashboard, 1000);
                } else {
                    const errorData = await response.json();
                    showMessage(loginStatus, errorData.detail || 'Login failed. Please check your credentials.', 'error');
                }
            } catch (error) {
                showMessage(loginStatus, `Network error: ${error.message}`, 'error');
            } finally {
                toggleButtonState(loginForm.querySelector('button[type="submit"]'), false);
            }
        });
    }

    // Admin Login Logic
    const adminLoginForm = document.getElementById('adminLoginForm');
    const adminLoginStatus = document.getElementById('adminLoginStatus');
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = e.target.email.value;
            const password = e.target.password.value;
            clearMessage(adminLoginStatus);
            toggleButtonState(adminLoginForm.querySelector('button[type="submit"]'), true);

            try {
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);

                const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData.toString()
                });

                if (response.ok) {
                    const data = await response.json();
                    setToken(data.access_token);
                    showMessage(adminLoginStatus, 'Admin login successful! Redirecting to admin panel...', 'success', true);
                    setTimeout(() => { window.location.href = '/admin-panel'; }, 1000);
                } else {
                    const errorData = await response.json();
                    if (response.status === 403) {
                        showMessage(adminLoginStatus, `${errorData.detail} <a href="/login" class="font-medium text-indigo-600 hover:text-indigo-500">User Login</a>`, 'error');
                    } else {
                        showMessage(adminLoginStatus, errorData.detail || 'Admin login failed. Please check your credentials.', 'error');
                    }
                }
            } catch (error) {
                showMessage(adminLoginStatus, `Network error: ${error.message}`, 'error');
            } finally {
                toggleButtonState(adminLoginForm.querySelector('button[type="submit"]'), false);
            }
        });
    }


    const signupForm = document.getElementById('signupForm');
    const signupStatus = document.getElementById('signupStatus');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = e.target.name.value;
            const email = e.target.email.value;
            const password = e.target.password.value;
            clearMessage(signupStatus);
            toggleButtonState(signupForm.querySelector('button[type="submit"]'), true);

            try {
                const response = await fetch(`${API_BASE_URL}/api/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, name })
                });

                if (response.ok) {
                    showMessage(signupStatus, 'Account created successfully! Please login.', 'success');
                    e.target.reset();
                    setTimeout(redirectToLogin, 1500);
                } else {
                    const errorData = await response.json();
                    showMessage(signupStatus, errorData.detail || 'Signup failed', 'error');
                }
            } catch (error) {
                showMessage(signupStatus, `Network error: ${error.message}`, 'error');
            } finally {
                toggleButtonState(signupForm.querySelector('button[type="submit"]'), false);
            }
        });
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            removeToken();
            window.location.href = '/'; 
        });
    }

    // --- Resume Upload Logic (Dashboard Page) ---
    const uploadResumeForm = document.getElementById('uploadResumeForm');
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadButton = uploadResumeForm ? uploadResumeForm.querySelector('button[type="submit"]') : null;
    if (uploadResumeForm) {
        if (uploadButton) uploadButton.dataset.originalText = uploadButton.innerHTML;

        uploadResumeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('resumeFile');
            clearMessage(uploadStatus);

            if (!fileInput.files.length) {
                showMessage(uploadStatus, 'Please select a file to upload.', 'error');
                return;
            }

            const file = fileInput.files[0];

            let validationMessage = '';
            const allowedExtensions = ['.pdf', '.docx', '.txt'];
            const maxFileSize = 10 * 1024 * 1024; // 10MB

            const fileExt = file.name.slice((file.name.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
            if (!allowedExtensions.includes(`.${fileExt}`)) {
                validationMessage = `File type '.${fileExt}' not allowed. Allowed types: ${allowedExtensions.join(', ')}.`;
            } else if (file.size > maxFileSize) {
                validationMessage = `File too large. Maximum size: ${formatFileSize(maxFileSize)}. Provided: ${formatFileSize(file.size)}.`;
            }

            if (validationMessage) {
                showMessage(uploadStatus, validationMessage, 'error');
                return;
            }

            toggleButtonState(uploadButton, true);
            showMessage(uploadStatus, 'Uploading and processing resume...', 'info', true);

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await authFetch(`${API_BASE_URL}/api/upload-resume`, {
                    method: 'POST',
                    body: formData,
                });

                showMessage(uploadStatus, response.message, 'success');
                e.target.reset();
                if (window.location.pathname === '/uploaded-resumes') {
                    loadResumes();
                } else if (window.location.pathname === '/dashboard') {
                    loadJobDescriptionsForSelect();
                }
            } catch (error) {
                showMessage(uploadStatus, `Error uploading resume: ${error.message}`, 'error');
            } finally {
                toggleButtonState(uploadButton, false);
            }
        });
    }

    // --- Add Job Description Logic (Dashboard Page) ---
    const addJobDescriptionForm = document.getElementById('addJobDescriptionForm');
    const jobTitleInput = document.getElementById('jobTitle');
    const companyNameInput = document.getElementById('companyName');
    const jobDescriptionTextInput = document.getElementById('jobDescriptionText');
    const jobStatus = document.getElementById('jobStatus');
    const addJobButton = addJobDescriptionForm ? addJobDescriptionForm.querySelector('button[type="submit"]') : null;
    
    const addJobDescriptionUrlForm = document.getElementById('addJobDescriptionUrlForm');
    const jobUrlInput = document.getElementById('jobUrl');
    const jobUrlStatus = document.getElementById('jobUrlStatus');
    const jobUrlButton = addJobDescriptionUrlForm ? addJobDescriptionUrlForm.querySelector('button[type="submit"]') : null;
    const toggleJobInputMode = document.getElementById('toggleJobInputMode');

    if (toggleJobInputMode && addJobDescriptionForm && addJobDescriptionUrlForm) {
        toggleJobInputMode.addEventListener('change', () => {
            if (toggleJobInputMode.checked) {
                addJobDescriptionForm.style.display = 'none';
                addJobDescriptionUrlForm.style.display = 'block';
                clearMessage(jobStatus);
                jobUrlInput.focus();
            } else {
                addJobDescriptionForm.style.display = 'block';
                addJobDescriptionUrlForm.style.display = 'none';
                clearMessage(jobUrlStatus);
                jobTitleInput.focus();
            }
        });
    }

    if (addJobDescriptionForm) {
        if (addJobButton) addJobButton.dataset.originalText = addJobButton.innerHTML;

        addJobDescriptionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const jobTitle = jobTitleInput.value;
            const companyName = companyNameInput.value;
            const jobDescriptionText = jobDescriptionTextInput.value;
            clearMessage(jobStatus);

            toggleButtonState(addJobButton, true);
            showMessage(jobStatus, 'Adding job and extracting requirements...', 'info', true);

            const jobData = {
                title: jobTitle,
                company: companyName,
                description: jobDescriptionText,
            };

            try {
                const response = await authFetch(`${API_BASE_URL}/api/job-description`, {
                    method: 'POST',
                    body: JSON.stringify(jobData)
                });

                showMessage(jobStatus, response.message, 'success');
                e.target.reset();
                loadJobDescriptionsForSelect();
                if (window.location.pathname === '/job-descriptions-page') {
                    loadJobDescriptions();
                }

            } catch (error) {
                showMessage(jobStatus, `Error adding job description: ${error.message}`, 'error');
            } finally {
                toggleButtonState(addJobButton, false);
            }
        });
    }

    if (addJobDescriptionUrlForm) {
        if (jobUrlButton) jobUrlButton.dataset.originalText = jobUrlButton.innerHTML;

        addJobDescriptionUrlForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const jobUrl = jobUrlInput.value;
            clearMessage(jobUrlStatus);

            toggleButtonState(jobUrlButton, true);
            showMessage(jobUrlStatus, 'Fetching job description from URL and processing...', 'info', true);

            try {
                const extractedData = await authFetch(`${API_BASE_URL}/api/extract-job-from-url`, {
                    method: 'POST',
                    body: JSON.stringify({ url: jobUrl })
                });

                jobTitleInput.value = extractedData.title;
                companyNameInput.value = extractedData.company;
                jobDescriptionTextInput.value = extractedData.description;

                toggleJobInputMode.checked = false;
                addJobDescriptionForm.style.display = 'block';
                addJobDescriptionUrlForm.style.display = 'none';
                clearMessage(jobUrlStatus);
                showMessage(jobStatus, 'Job details extracted and pre-filled. Please review and click "Add Job" to save.', 'success');
                jobTitleInput.focus();
                
                e.target.reset();

            } catch (error) {
                showMessage(jobUrlStatus, `Error fetching job from URL: ${error.message}`, 'error');
            } finally {
                toggleButtonState(jobUrlButton, false);
            }
        });
    }


    // --- Load Resumes List (Uploaded Resumes Page) ---
    const resumesListDiv = document.getElementById('resumesList');
    const resumesEmptyState = document.getElementById('resumesEmptyState');
    
    // NEW: Function to filter resumes by search input
    const filterResumes = () => {
        const searchTerm = document.getElementById('resumeSearchInput').value.toLowerCase();
        document.querySelectorAll('#resumesList .list-item').forEach(item => {
            const textContent = item.textContent.toLowerCase();
            if (textContent.includes(searchTerm)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    };

    const loadResumes = async () => {
        if (!resumesListDiv) return;

        if (resumesEmptyState) resumesEmptyState.classList.add('hidden');
        resumesListDiv.innerHTML = '<p class="text-gray-500"><span class="spinner"></span> Loading resumes...</p>';

        try {
            const resumes = await authFetch(`${API_BASE_URL}/api/resumes`);
            resumesListDiv.innerHTML = '';

            if (resumes.length === 0) {
                if (resumesEmptyState) resumesEmptyState.classList.remove('hidden');
                return;
            }

            resumes.forEach(resume => {
                const resumeItem = document.createElement('div');
                resumeItem.className = 'list-item flex flex-col sm:flex-row mb-4';
                resumeItem.innerHTML = `
                    <div class="flex-grow">
                        <h3 class="list-item-title">${resume.filename}</h3>
                        <p class="list-item-details">Uploaded: ${new Date(resume.upload_date).toLocaleDateString()}</p>
                        <p class="list-item-details">Experience: ${resume.total_years_experience || 0} years</p>
                        <p class="list-item-details">Education: ${resume.highest_education_level && resume.highest_education_level.toLowerCase() !== 'none' ? resume.highest_education_level : 'N/A'} ${resume.major && resume.major.toLowerCase() !== 'none' ? `(${resume.major})` : ''}</p>
                    </div>
                    <div class="flex space-x-2 mt-4 sm:mt-0">
                        <button class="btn-secondary view-resume-btn" data-id="${resume.id}">View Details</button>
                        <button class="btn-secondary delete-resume-btn" data-id="${resume.id}">Delete</button>
                    </div>
                `;
                resumesListDiv.appendChild(resumeItem);
            });

            document.querySelectorAll('.view-resume-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const resumeId = e.target.dataset.id;
                    try {
                        const resume = await authFetch(`${API_BASE_URL}/api/resume/${resumeId}`);
                        showResumeDetailsModal(resume);
                    } catch (error) {
                        alert(`Error fetching resume details: ${error.message}`);
                    }
                });
            });

            document.querySelectorAll('.delete-resume-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    if (!confirm('Are you sure you want to delete this resume?')) {
                        return;
                    }
                    const resumeId = e.target.dataset.id;
                    try {
                        const response = await authFetch(`${API_BASE_URL}/api/resume/${resumeId}`, { method: 'DELETE' });
                        alert(response.message);
                        loadResumes();
                    } catch (error) {
                        alert(`Error deleting resume: ${error.message}`);
                    }
                });
            });
            
            // NEW: Attach listener to the search input
            const resumeSearchInput = document.getElementById('resumeSearchInput');
            if (resumeSearchInput) {
                resumeSearchInput.addEventListener('input', filterResumes);
            }

        } catch (error) {
            resumesListDiv.innerHTML = `<p class="text-red-600">Failed to load resumes: ${error.message}</p>`;
        }
    };

    // --- Load Job Descriptions List (Job Descriptions Page) ---
    const jobDescriptionsListDiv = document.getElementById('jobDescriptionsList');
    const jobsEmptyState = document.getElementById('jobsEmptyState');

    // NEW: Function to filter jobs by search input
    const filterJobs = () => {
        const jobSearchInput = document.getElementById('jobSearchInput');
        if (!jobSearchInput) return;
        const searchTerm = jobSearchInput.value.toLowerCase();
        document.querySelectorAll('#jobDescriptionsList .list-item').forEach(item => {
            const textContent = item.textContent.toLowerCase();
            if (textContent.includes(searchTerm)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    };

    const loadJobDescriptions = async () => {
        if (!jobDescriptionsListDiv) return;

        if (jobsEmptyState) jobsEmptyState.classList.add('hidden');
        jobDescriptionsListDiv.innerHTML = '<p class="text-gray-500"><span class="spinner"></span> Loading job descriptions...</p>';
        try {
            const jobs = await authFetch(`${API_BASE_URL}/api/job-descriptions`);
            jobDescriptionsListDiv.innerHTML = '';

            if (jobs.length === 0) {
                if (jobsEmptyState) jobsEmptyState.classList.remove('hidden');
                return;
            }

            jobs.forEach(job => {
                const jobItem = document.createElement('div');
                jobItem.className = 'list-item flex flex-col sm:flex-row mb-4';
                jobItem.innerHTML = `
                    <div class="flex-grow">
                        <h3 class="list-item-title">${job.title}</h3>
                        <p class="list-item-details">Company: ${job.company}</p>
                        <p class="list-item-details">Added: ${new Date(job.created_date).toLocaleDateString()}</p>
                        <p class="list-item-details">Req. Exp: ${job.required_experience_years !== null && job.required_experience_years !== 0 ? `${job.required_experience_years} years` : 'N/A'}</p>
                        <p class="list-item-details">Req. Edu: ${job.required_education_level && job.required_education_level.toLowerCase() !== 'none' ? job.required_education_level : 'N/A'} ${job.required_major && job.required_major.toLowerCase() !== 'none' ? `(${job.major})` : ''}</p>
                    </div>
                    <div class="flex space-x-2 mt-4 sm:mt-0">
                        <button class="btn-secondary view-job-btn" data-id="${job.id}">View Details</button>
                        <button class="btn-secondary edit-job-btn" data-id="${job.id}">Edit</button>
                        <button class="btn-secondary delete-job-btn" data-id="${job.id}">Delete</button>
                    </div>
                `;
                jobDescriptionsListDiv.appendChild(jobItem);
            });

            document.querySelectorAll('.view-job-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const jobId = e.target.dataset.id;
                    try {
                        const job = await authFetch(`${API_BASE_URL}/api/job-description/${jobId}`);
                        showJobDetailsModal(job);
                    }
                    catch (error) {
                        alert(`Error fetching job details: ${error.message}`);
                    }
                });
            });

            document.querySelectorAll('.edit-job-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const jobId = e.target.dataset.id;
                    try {
                        const job = await authFetch(`${API_BASE_URL}/api/job-description/${jobId}`);
                        const editJobIdElem = document.getElementById('editJobId');
                        const editJobTitleElem = document.getElementById('editJobTitle');
                        const editCompanyNameElem = document.getElementById('editCompanyName');
                        const editJobDescriptionTextElem = document.getElementById('editJobDescriptionText');

                        if (editJobIdElem) editJobIdElem.value = job.id;
                        if (editJobTitleElem) editJobTitleElem.value = job.title;
                        if (editCompanyNameElem) editCompanyNameElem.value = job.company;
                        if (editJobDescriptionTextElem) editJobDescriptionTextElem.value = job.description;

                        if (jobEditModal) jobEditModal.classList.add('modal-active');
                    } catch (error) {
                        alert(`Error fetching job for edit: ${error.message}`);
                    }
                });
            });

            document.querySelectorAll('.delete-job-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    if (!confirm('Are you sure you want to delete this job description?')) {
                        return;
                    }
                    const jobId = e.target.dataset.id;
                    try {
                        const response = await authFetch(`${API_BASE_URL}/api/job-description/${jobId}`, { method: 'DELETE' });
                        alert(response.message);
                        loadJobDescriptions();
                    } catch (error) {
                        alert(`Error deleting job description: ${error.message}`);
                    }
                });
            });
            
            // NEW: Attach listener to the search input
            const jobSearchInput = document.getElementById('jobSearchInput');
            if (jobSearchInput) {
                jobSearchInput.addEventListener('input', filterJobs);
            }

        } catch (error) {
            jobDescriptionsListDiv.innerHTML = `<p class="text-red-600">Failed to load job descriptions: ${error.message}</p>`;
        }
    };

    // --- Edit Job Description Logic ---
    const editJobDescriptionForm = document.getElementById('editJobDescriptionForm');
    const editJobStatus = document.getElementById('editJobStatus');
    const editJobButton = editJobDescriptionForm ? editJobDescriptionForm.querySelector('button[type="submit"]') : null;
    if (editJobDescriptionForm) {
        if (editJobButton) editJobButton.dataset.originalText = editJobButton.innerHTML;

        editJobDescriptionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const jobId = document.getElementById('editJobId').value;
            const jobTitle = document.getElementById('editJobTitle').value;
            const companyName = document.getElementById('editCompanyName').value;
            const jobDescriptionText = document.getElementById('editJobDescriptionText').value;
            clearMessage(editJobStatus);

            toggleButtonState(editJobButton, true);
            showMessage(editJobStatus, 'Saving changes and re-extracting requirements...', 'info', true);

            const updatedJobData = {
                title: jobTitle,
                company: companyName,
                description: jobDescriptionText,
            };

            try {
                const response = await authFetch(`${API_BASE_URL}/api/job-description/${jobId}`, {
                    method: 'PUT',
                    body: JSON.stringify(updatedJobData)
                });
                showMessage(editJobStatus, 'Job description updated successfully!', 'success');
                if (jobEditModal) jobEditModal.classList.remove('modal-active');
                loadJobDescriptions();
                loadJobDescriptionsForSelect();
            } catch (error) {
                showMessage(editJobStatus, `Error updating job description: ${error.message}`, 'error');
            } finally {
                toggleButtonState(editJobButton, false);
            }
        });
    }

    // --- Match Resumes Logic (Dashboard Page) ---
    const jobSelect = document.getElementById('jobSelect');
    const matchResumesBtn = document.getElementById('matchResumesBtn');
    const matchingResultsDiv = document.getElementById('matchingResults');
    const matchStatus = document.getElementById('matchStatus');
    const matchEmptyState = document.getElementById('matchEmptyState');
    const matchButton = matchResumesBtn;
    
    // Weight Adjustment Logic
    const weightElements = {
        skills: {
            slider: document.getElementById('weightSkills'),
            text: document.getElementById('weightSkillsText'),
            display: document.getElementById('weightSkillsValue')
        },
        experience: {
            slider: document.getElementById('weightExperience'),
            text: document.getElementById('weightExperienceText'),
            display: document.getElementById('weightExperienceValue')
        },
        certifications: {
            slider: document.getElementById('weightCertifications'),
            text: document.getElementById('weightCertificationsText'),
            display: document.getElementById('weightCertificationsValue')
        },
        education: {
            slider: document.getElementById('weightEducation'),
            text: document.getElementById('weightEducationText'),
            display: document.getElementById('weightEducationValue')
        }
    };
    const weightWarning = document.getElementById('weightWarning');

    const updateWeightDisplays = (key, sourceElement) => {
        let value;
        if (sourceElement === weightElements[key].slider) {
            value = parseInt(weightElements[key].slider.value, 10);
            if (weightElements[key].text) {
                weightElements[key].text.value = value;
            }
        } else if (sourceElement === weightElements[key].text) {
            value = parseInt(weightElements[key].text.value, 10);
            if (isNaN(value) || value < 0 || value > 100) {
                value = Math.max(0, Math.min(100, isNaN(value) ? 0 : value));
                weightElements[key].text.value = value;
            }
            if (weightElements[key].slider) {
                weightElements[key].slider.value = value;
            }
        } else {
            value = parseInt(weightElements[key].slider.value, 10);
            if (weightElements[key].text) {
                weightElements[key].text.value = value;
            }
        }
        if (weightElements[key].display) {
            weightElements[key].display.textContent = `${value}%`;
        }
        checkTotalWeights();
    };

    const checkTotalWeights = () => {
        let total = 0;
        for (const key in weightElements) {
            if (weightElements[key].text) {
                total += parseInt(weightElements[key].text.value, 10) || 0;
            } else if (weightElements[key].slider) {
                total += parseInt(weightElements[key].slider.value, 10) || 0;
            }
        }
        if (weightWarning) {
            if (total !== 100) {
                weightWarning.style.display = 'block';
                weightWarning.textContent = `Total weights must sum to 100%. Current: ${total}%. Please adjust.`;
                return false;
            } else {
                weightWarning.style.display = 'none';
                return true;
            }
        }
        return true;
    };

    const setupWeightListeners = () => {
        for (const key in weightElements) {
            if (weightElements[key].slider) {
                updateWeightDisplays(key);
                weightElements[key].slider.addEventListener('input', (e) => updateWeightDisplays(key, e.target));
            }
            if (weightElements[key].text) {
                weightElements[key].text.addEventListener('input', (e) => updateWeightDisplays(key, e.target));
                weightElements[key].text.addEventListener('blur', (e) => {
                    let val = parseInt(e.target.value, 10);
                    if (isNaN(val) || val < 0 || val > 100) {
                        val = Math.max(0, Math.min(100, isNaN(val) ? 0 : val));
                        e.target.value = val;
                    }
                    updateWeightDisplays(key, e.target);
                });
            }
        }
        checkTotalWeights();
    };

    const loadJobDescriptionsForSelect = async () => {
        if (!jobSelect) return;
        jobSelect.innerHTML = '<option value="">-- Loading Jobs --</option>';
        try {
            const allJobs = await authFetch(`${API_BASE_URL}/api/job-descriptions`);
            jobSelect.innerHTML = '<option value="">-- Select a Job --</option>';
            if (allJobs.length > 0) {
                allJobs.forEach(job => {
                    const option = document.createElement('option');
                    option.value = job.id;
                    option.textContent = `${job.title} at ${job.company}`;
                    jobSelect.appendChild(option);
                });
            } else {
                jobSelect.innerHTML = '<option value="">-- No Jobs Available --</option>';
            }
        } catch (error) {
            jobSelect.innerHTML = '<option value="">-- Error Loading Jobs --</option>';
            console.error('Error loading jobs for select:', error.message);
        }
    };

    if (matchResumesBtn) {
        if (matchButton) matchButton.dataset.originalText = matchButton.innerHTML;

        if (window.location.pathname === '/dashboard') {
            setupWeightListeners();
        }

        matchResumesBtn.addEventListener('click', async () => {
            const selectedJobId = jobSelect.value;
            clearMessage(matchStatus);
            matchingResultsDiv.innerHTML = '';
            if (matchEmptyState) matchEmptyState.classList.add('hidden');

            if (!selectedJobId) {
                showMessage(matchStatus, 'Please select a job description first.', 'error');
                if (matchEmptyState) matchEmptyState.classList.remove('hidden');
                return;
            }

            if (!checkTotalWeights()) {
                showMessage(matchStatus, 'Please adjust weights; they must sum to 100%.', 'error');
                return;
            }

            toggleButtonState(matchButton, true);
            showMessage(matchStatus, 'Matching resumes...', 'info', true);

            const formData = new FormData();
            formData.append('job_id', selectedJobId);

            const currentWeights = {};
            for (const key in weightElements) {
                if (weightElements[key].text) {
                    currentWeights[key] = parseFloat(weightElements[key].text.value) / 100;
                } else if (weightElements[key].slider) {
                    currentWeights[key] = parseFloat(weightElements[key].slider.value) / 100;
                }
            }
            formData.append('weights', JSON.stringify(currentWeights));

            try {
                const response = await authFetch(`${API_BASE_URL}/api/match-resumes`, {
                    method: 'POST',
                    body: formData,
                });

                clearMessage(matchStatus);

                if (response.length === 0) {
                    matchingResultsDiv.innerHTML = '<p class="text-gray-500">No resumes to match or no matches found.</p>';
                    if (matchEmptyState) matchEmptyState.classList.remove('hidden');
                    return;
                }

                response.forEach(result => {
                    const resultCard = document.createElement('div');
                    resultCard.className = 'card p-4 mb-4';
                    
                    let scoreBarGradient;
                    if (result.overall_score >= 80) {
                        scoreBarGradient = 'linear-gradient(to right, #22c55e, #16a34a)';
                    } else if (result.overall_score >= 50) {
                        scoreBarGradient = 'linear-gradient(to right, #facc15, #eab308)';
                    } else {
                        scoreBarGradient = 'linear-gradient(to right, #ef4444, #dc2626)';
                    }

                    const appliedWeights = result.match_details.applied_weights || { skills: 0.6, experience: 0.2, certifications: 0.1, education: 0.1 };

                    resultCard.innerHTML = `
                        <div class="flex items-center justify-between mb-2">
                            <h4 class="text-lg font-semibold text-gray-800">${result.filename}</h4>
                            <div class="score-text" style="color: ${result.overall_score >= 80 ? '#15803d' : (result.overall_score >= 50 ? '#b45309' : '#b91c1c')}">${result.overall_score}% Match</div>
                        </div>
                        <div class="score-bar-container">
                            <div class="score-bar" style="width: ${result.overall_score}%; background-image: ${scoreBarGradient};"></div>
                        </div>
                        <div class="mt-4">
                            <p class="font-medium text-gray-700 mb-1">Matched Skills:</p>
                            <div class="flex flex-wrap gap-2 mb-2">${renderSkillTags(result.matched_skills, 'matched-skill')}</div>
                            <p class="font-medium text-gray-700 mb-1">Missing Skills:</p>
                            <div class="flex flex-wrap gap-2 mb-2">${renderSkillTags(result.missing_skills, 'missing-skill')}</div>
                            <p class="font-medium text-gray-700 mb-1">Additional Skills:</p>
                            <div class="flex flex-wrap gap-2">${renderSkillTags(result.additional_skills, 'additional-skill')}</div>
                        </div>
                        <div class="mt-4 text-sm text-gray-600">
                            <p class="font-bold text-gray-700">Match Details:</p>
                            <p>Experience Score: ${result.match_details.experience_score}% (Resume: ${result.match_details.resume_exp_years || 0} yrs, Job Req: ${result.match_details.job_req_exp_years || 0} yrs)</p>
                            <p>Certifications Score: ${result.match_details.certifications_score}%</p>
                            <p>Education Score: ${result.match_details.education_score}% (Resume: ${result.match_details.resume_highest_edu && result.match_details.resume_highest_edu.toLowerCase() !== 'none' ? result.match_details.resume_highest_edu : 'N/A'} ${result.match_details.resume_major && result.match_details.resume_major.toLowerCase() !== 'none' ? `(${result.match_details.resume_major})` : ''}, Job Req: ${result.match_details.job_req_edu && result.match_details.job_req_edu.toLowerCase() !== 'none' ? result.match_details.job_req_edu : 'N/A'} ${result.match_details.job_req_major && result.match_details.job_req_major.toLowerCase() !== 'none' ? `(${result.match_details.job_req_major})` : ''})</p>
                            
                            <p class="mt-2 font-bold text-gray-700">Applied Weights:</p>
                            <p>Skills: ${Math.round(appliedWeights.skills * 100)}%, Experience: ${Math.round(appliedWeights.experience * 100)}%, Certifications: ${Math.round(appliedWeights.certifications * 100)}%, Education: ${Math.round(appliedWeights.education * 100)}%</p>
                        </div>
                    `;
                    matchingResultsDiv.appendChild(resultCard);
                });

            } catch (error) {
                showMessage(matchStatus, `Error matching resumes: ${error.message}`, 'error');
                if (matchEmptyState) matchEmptyState.classList.remove('hidden');
            } finally {
                toggleButtonState(matchButton, false);
            }
        });
    }

    // --- Admin Panel Specific Logic ---
    const totalUsersCountElem = document.getElementById('totalUsersCount');
    const usersTableBody = document.getElementById('usersTableBody');
    const usersEmptyState = document.getElementById('usersEmptyState');

    // NEW: Function to filter users by search input
    const filterUsers = () => {
        const userSearchInput = document.getElementById('userSearchInput');
        if (!userSearchInput) return;
        const searchTerm = userSearchInput.value.toLowerCase();
        document.querySelectorAll('#usersTableBody tr').forEach(row => {
            const textContent = row.textContent.toLowerCase();
            if (textContent.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    };

    const loadAdminDashboardData = async () => {
        if (!totalUsersCountElem) return;

        try {
            const users = await authFetch(`${API_BASE_URL}/api/admin/users`);
            totalUsersCountElem.textContent = users.length;
        } catch (error) {
            totalUsersCountElem.textContent = 'Error';
            console.error('Error fetching total users:', error);
        }
    };

    const loadUsersList = async () => {
        if (!usersTableBody) return;

        if (usersEmptyState) usersEmptyState.classList.add('hidden');
        usersTableBody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-gray-500"><span class="spinner"></span> Loading users...</td></tr>';

        try {
            const users = await authFetch(`${API_BASE_URL}/api/admin/users`);
            usersTableBody.innerHTML = '';

            if (users.length === 0) {
                if (usersEmptyState) usersEmptyState.classList.remove('hidden');
                return;
            }

            users.forEach(user => {
                const row = usersTableBody.insertRow();
                row.className = 'hover:bg-gray-50';
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${user.name || 'N/A'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${user.email}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${user.id}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button class="btn-secondary delete-user-btn" data-user-id="${user.id}" data-user-email="${user.email}">Delete</button>
                    </td>
                `;
            });

            document.querySelectorAll('.delete-user-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const userId = e.target.dataset.userId;
                    const userEmail = e.target.dataset.userEmail;
                    if (confirm(`Are you sure you want to delete user ${userEmail} (ID: ${userId})? This action cannot be undone and will delete all associated data.`)) {
                        try {
                            const response = await authFetch(`${API_BASE_URL}/api/admin/users/${userId}`, { method: 'DELETE' });
                            alert(response.message);
                            loadUsersList();
                            loadAdminDashboardData();
                        } catch (error) {
                            alert(`Error deleting user: ${error.message}`);
                            console.error('Error deleting user:', error);
                        }
                    }
                });
            });
            
            // NEW: Attach listener to the search input
            const userSearchInput = document.getElementById('userSearchInput');
            if (userSearchInput) {
                userSearchInput.addEventListener('input', filterUsers);
            }

        } catch (error) {
            usersTableBody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-red-600">Failed to load users: ${error.message}</td></tr>`;
        }
    };


    // --- Theme Toggle Logic ---
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    
    // Function to set the theme
    const setTheme = (theme) => {
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light');
        }
    };
    
    // Check for saved theme preference on page load
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    // Toggle theme on button click
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.body.classList.contains('dark-mode') ? 'light' : 'dark';
            setTheme(currentTheme);
        });
    }

    // --- Initialization based on current page ---
    const currentPage = window.location.pathname;

    if (currentPage === '/dashboard') {
        if (!isAuthenticated()) {
            redirectToLogin();
            return;
        }
        loadJobDescriptionsForSelect();
    } else if (currentPage === '/uploaded-resumes') {
        if (!isAuthenticated()) {
            redirectToLogin();
            return;
        }
        loadResumes();
    } else if (currentPage === '/job-descriptions-page') {
        if (!isAuthenticated()) {
            redirectToLogin();
            return;
        }
        loadJobDescriptions();
    } else if (currentPage === '/admin-panel') {
        if (!isAuthenticated()) {
            redirectToAdminLogin();
            return;
        }
        loadAdminDashboardData();
    } else if (currentPage === '/admin-panel/users') {
        if (!isAuthenticated()) {
            redirectToAdminLogin();
            return;
        }
        loadUsersList();
    } else if (currentPage === '/' || currentPage === '/login' || currentPage === '/signup' || currentPage === '/admin-login') {
        if (isAuthenticated()) {
            redirectToDashboard(); 
        }
    }
});