document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration ---
    const API_BASE_URL = 'https://resumerank-1c6v.onrender.com/api';
    const token = localStorage.getItem('user_token');
    const currentPage = window.location.pathname;
    const protectedPages = ['/dashboard', '/uploaded-resumes', '/job-descriptions-page'];

    // --- Page Protection ---
    // If we're on a protected page and there's no token, redirect to login
    if (!token && protectedPages.some(page => currentPage.startsWith(page))) {
        window.location.href = '/login';
        return; // Stop all script execution if not logged in
    }

    // --- Universal Helper Functions ---
    const showStatus = (element, message, type) => {
        if (element) {
            element.textContent = message;
            element.className = `mt-4 text-sm font-medium text-center ${type === 'success' ? 'text-green-700' : type === 'error' ? 'text-red-700' : 'text-gray-700'}`;
        }
    };

    const getAuthHeaders = () => token ? { 'Authorization': `Bearer ${token}` } : {};
    const fetchWithAuth = (url, options = {}) => fetch(url, { ...options, headers: { ...getAuthHeaders(), ...options.headers } });

    const renderSkillTags = (container, items, type = '') => {
        if (!container) return;
        container.innerHTML = '';
        if (items && items.length > 0) {
            items.forEach(item => {
                const span = document.createElement('span');
                span.className = `skill-tag ${type}-skill`;
                span.textContent = item;
                container.appendChild(span);
            });
        } else {
            container.textContent = 'N/A';
        }
    };

    const renderExperienceEntries = (container, experiences) => {
        if (!container) return;
        container.innerHTML = '';
        if (experiences && experiences.length > 0) {
            experiences.forEach(exp => {
                const div = document.createElement('div');
                div.innerHTML = `<p class="font-semibold">${exp.title || 'N/A'} at ${exp.company || 'N/A'}</p><p class="text-xs text-gray-600">${exp.start_date || ''} - ${exp.end_date || 'Present'}</p>`;
                container.appendChild(div);
            });
        } else {
            container.textContent = 'No experience extracted.';
        }
    };

    const renderEducationEntries = (container, educationEntries) => {
        if (!container) return;
        container.innerHTML = '';
        if (educationEntries && educationEntries.length > 0) {
            educationEntries.forEach(edu => {
                const div = document.createElement('div');
                div.innerHTML = `<p class="font-semibold">${edu.degree || 'N/A'} in ${edu.major || 'N/A'}</p><p class="text-xs text-gray-600">${edu.institution || 'N/A'}</p>`;
                container.appendChild(div);
            });
        } else {
            container.textContent = 'No education extracted.';
        }
    };
    
    // --- AUTHENTICATION PAGES LOGIC ---
    if (currentPage.includes('/login')) {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const statusEl = document.getElementById('loginStatus');
                showStatus(statusEl, 'Signing in...', 'info');
                try {
                    const response = await fetch(`${API_BASE_URL}/login`, { method: 'POST', body: new FormData(loginForm) });
                    if (!response.ok) throw new Error((await response.json()).detail);
                    const data = await response.json();
                    localStorage.setItem('user_token', data.access_token);
                    window.location.href = '/dashboard';
                } catch (error) {
                    showStatus(statusEl, `Error: ${error.message}`, 'error');
                }
            });
        }
    } else if (currentPage.includes('/signup')) {
        const signupForm = document.getElementById('signupForm');
        if (signupForm) {
            signupForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const statusEl = document.getElementById('signupStatus');
                const userData = { email: e.target.email.value, password: e.target.password.value };
                showStatus(statusEl, 'Creating account...', 'info');
                try {
                    const response = await fetch(`${API_BASE_URL}/register`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(userData),
                    });
                    if (!response.ok) throw new Error((await response.json()).detail);
                    showStatus(statusEl, 'Account created! Redirecting to login...', 'success');
                    setTimeout(() => window.location.href = '/login', 1500);
                } catch (error) {
                    showStatus(statusEl, `Error: ${error.message}`, 'error');
                }
            });
        }
    }
    // --- MAIN APPLICATION LOGIC (for protected pages) ---
    else if (protectedPages.some(page => currentPage.startsWith(page))) {
        // --- Universal Elements & Functions for Protected Pages ---
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                localStorage.removeItem('user_token');
                window.location.href = '/login';
            });
        }

        const fetchAndDisplayJobs = async () => {
            const jobDescriptionsListDiv = document.getElementById('jobDescriptionsList');
            const jobSelect = document.getElementById('jobSelect');
            if (!jobDescriptionsListDiv && !jobSelect) return;
            try {
                const response = await fetchWithAuth(`${API_BASE_URL}/job-descriptions`);
                if (!response.ok) throw new Error('Failed to fetch jobs');
                const jobs = await response.json();
                if (jobDescriptionsListDiv) {
                    jobDescriptionsListDiv.innerHTML = jobs.length === 0 ? '<p class="text-gray-500">No jobs added yet.</p>' : '';
                    jobs.forEach(job => {
                        const el = document.createElement('div');
                        el.className = 'list-item';
                        el.innerHTML = `
                            <div><p class="list-item-title">${job.title} at ${job.company}</p><p class="list-item-details">Added: ${new Date(job.created_date).toLocaleDateString()}</p></div>
                            <div class="flex space-x-2"><button data-job-id="${job.id}" class="view-job-btn btn-secondary">Details</button><button data-job-id="${job.id}" class="edit-job-btn btn-secondary">Edit</button><button data-job-id="${job.id}" class="delete-job-btn btn-secondary bg-red-100 text-red-700">Delete</button></div>`;
                        jobDescriptionsListDiv.appendChild(el);
                    });
                }
                if (jobSelect) {
                    jobSelect.innerHTML = '<option value="">-- Select a Job --</option>';
                    jobs.forEach(job => jobSelect.innerHTML += `<option value="${job.id}">${job.title} at ${job.company}</option>`);
                }
            } catch (error) {
                if (jobDescriptionsListDiv) jobDescriptionsListDiv.innerHTML = '<p class="text-red-700">Could not load jobs.</p>';
            }
        };

        const fetchAndDisplayResumes = async () => {
            const resumesListDiv = document.getElementById('resumesList');
            if (!resumesListDiv) return;
            try {
                const response = await fetchWithAuth(`${API_BASE_URL}/resumes`);
                if (!response.ok) throw new Error('Failed to fetch resumes');
                const resumes = await response.json();
                resumesListDiv.innerHTML = resumes.length === 0 ? '<p class="text-gray-500">No resumes uploaded yet.</p>' : '';
                resumes.forEach(resume => {
                    const el = document.createElement('div');
                    el.className = 'list-item';
                    el.innerHTML = `
                        <div><p class="list-item-title">${resume.filename}</p><p class="list-item-details">Uploaded: ${new Date(resume.upload_date).toLocaleDateString()}</p></div>
                        <div class="flex space-x-2"><button data-resume-id="${resume.id}" class="view-resume-btn btn-secondary">Details</button><button data-resume-id="${resume.id}" class="delete-resume-btn btn-secondary bg-red-100 text-red-700">Delete</button></div>`;
                    resumesListDiv.appendChild(el);
                });
            } catch (error) {
                resumesListDiv.innerHTML = '<p class="text-red-700">Could not load resumes.</p>';
            }
        };
        
        // --- Attach Event Listeners based on current page ---

        // DASHBOARD
        if (currentPage.includes('/dashboard')) {
            const uploadResumeForm = document.getElementById('uploadResumeForm');
            const addJobDescriptionForm = document.getElementById('addJobDescriptionForm');
            const matchResumesBtn = document.getElementById('matchResumesBtn');
            fetchAndDisplayJobs(); // Load jobs into dropdown

            uploadResumeForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const statusEl = document.getElementById('uploadStatus');
                showStatus(statusEl, 'Uploading...', 'info');
                try {
                    const response = await fetchWithAuth(`${API_BASE_URL}/upload-resume`, { method: 'POST', body: new FormData(uploadResumeForm) });
                    if (!response.ok) throw new Error((await response.json()).detail);
                    showStatus(statusEl, 'Upload successful!', 'success');
                    uploadResumeForm.reset();
                } catch (error) {
                    showStatus(statusEl, `Error: ${error.message}`, 'error');
                }
            });

            addJobDescriptionForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const statusEl = document.getElementById('jobStatus');
                const jobData = { title: e.target.title.value, company: e.target.company.value, description: e.target.description.value, required_experience_years: e.target.required_experience_years.value ? parseInt(e.target.required_experience_years.value) : null, required_certifications: e.target.required_certifications.value.split(',').map(s => s.trim()).filter(Boolean) };
                showStatus(statusEl, 'Adding job...', 'info');
                try {
                    const response = await fetchWithAuth(`${API_BASE_URL}/job-description`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(jobData) });
                    if (!response.ok) throw new Error((await response.json()).detail);
                    showStatus(statusEl, 'Job added successfully!', 'success');
                    addJobDescriptionForm.reset();
                    fetchAndDisplayJobs();
                } catch (error) {
                    showStatus(statusEl, `Error: ${error.message}`, 'error');
                }
            });

            matchResumesBtn.addEventListener('click', async () => { /* Match logic here */ });
        }
        
        // UPLOADED RESUMES PAGE
        if (currentPage.includes('/uploaded-resumes')) {
            fetchAndDisplayResumes();
        }

        // JOB DESCRIPTIONS PAGE
        if (currentPage.includes('/job-descriptions-page')) {
            fetchAndDisplayJobs();
            const editJobDescriptionForm = document.getElementById('editJobDescriptionForm');
            if(editJobDescriptionForm) {
                editJobDescriptionForm.addEventListener('submit', async (e) => { /* Edit form logic */ });
            }
        }
        
        // --- Universal Delegated Click Handler for Lists & Modals ---
        document.body.addEventListener('click', async (e) => {
            const target = e.target;
            const resumeDetailsModal = document.getElementById('resumeDetailsModal');
            const jobDetailsModal = document.getElementById('jobDetailsModal');
            const jobEditModal = document.getElementById('jobEditModal');

            // Handle Resume Buttons
            if (target.matches('.view-resume-btn')) {
                const resumeId = target.dataset.resumeId;
                const response = await fetchWithAuth(`${API_BASE_URL}/resume/${resumeId}`);
                if (!response.ok) { alert('Could not load resume details.'); return; }
                const resume = await response.json();
                
                resumeDetailsModal.querySelector('#modalResumeFilename').textContent = resume.filename;
                // ... populate rest of resume modal
                resumeDetailsModal.classList.add('modal-active');
            }
            if (target.matches('.delete-resume-btn')) {
                if (confirm('Are you sure?')) {
                    await fetchWithAuth(`${API_BASE_URL}/resume/${target.dataset.resumeId}`, { method: 'DELETE' });
                    fetchAndDisplayResumes();
                }
            }

            // Handle Job Buttons
            if (target.matches('.view-job-btn')) {
                const jobId = target.dataset.jobId;
                const response = await fetchWithAuth(`${API_BASE_URL}/job-description/${jobId}`);
                if (!response.ok) { alert('Could not load job details.'); return; }
                const job = await response.json();
                
                jobDetailsModal.querySelector('#modalJobTitle').textContent = job.title;
                // ... populate rest of job details modal
                jobDetailsModal.classList.add('modal-active');
            }
             if (target.matches('.edit-job-btn')) {
                const jobId = target.dataset.jobId;
                const response = await fetchWithAuth(`${API_BASE_URL}/job-description/${jobId}`);
                if (!response.ok) { alert('Could not load details for editing.'); return; }
                const job = await response.json();
                
                const form = document.getElementById('editJobDescriptionForm');
                form.querySelector('#editJobId').value = job.id;
                // ... populate rest of edit form
                jobEditModal.classList.add('modal-active');
            }
            if (target.matches('.delete-job-btn')) {
                if (confirm('Are you sure?')) {
                    await fetchWithAuth(`${API_BASE_URL}/job-description/${target.dataset.jobId}`, { method: 'DELETE' });
                    fetchAndDisplayJobs();
                }
            }

            // Handle Modal Closing
            if (target.matches('.close-button') || target.matches('.modal')) {
                document.querySelectorAll('.modal').forEach(modal => modal.classList.remove('modal-active'));
            }
        });
    }
});