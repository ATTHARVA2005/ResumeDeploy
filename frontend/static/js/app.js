document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration & Page Protection ---
    const API_BASE_URL = window.location.origin.includes('localhost') ? 'http://localhost:8000/api' : `${window.location.origin}/api`;
    const token = localStorage.getItem('user_token');
    const currentPage = window.location.pathname;
    
    const protectedPages = ['/dashboard', '/uploaded-resumes', '/job-descriptions-page'];
    if (!token && protectedPages.some(page => currentPage.includes(page))) {
        window.location.href = '/login';
        return; 
    }

    // --- Element Selectors ---
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const logoutBtn = document.getElementById('logoutBtn');
    
    const uploadResumeForm = document.getElementById('uploadResumeForm');
    const addJobDescriptionForm = document.getElementById('addJobDescriptionForm');
    const matchResumesBtn = document.getElementById('matchResumesBtn');
    
    const resumesListDiv = document.getElementById('resumesList');
    const jobDescriptionsListDiv = document.getElementById('jobDescriptionsList');
    const matchingResultsDiv = document.getElementById('matchingResults');

    const resumeDetailsModal = document.getElementById('resumeDetailsModal');
    const jobDetailsModal = document.getElementById('jobDetailsModal');
    const jobEditModal = document.getElementById('jobEditModal');
    const editJobDescriptionForm = document.getElementById('editJobDescriptionForm');


    // --- Helper Functions ---
    const showStatus = (element, message, type) => {
        if (!element) return;
        element.textContent = message;
        element.className = `mt-4 text-sm font-medium text-center ${type === 'success' ? 'text-green-700' : type === 'error' ? 'text-red-700' : 'text-gray-700'}`;
    };

    const getAuthHeaders = () => {
        const token = localStorage.getItem('user_token');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    };

    const fetchWithAuth = (url, options = {}) => {
        return fetch(url, {
            ...options,
            headers: { ...getAuthHeaders(), ...options.headers },
        });
    };
    
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

    // --- Data Fetching and Rendering ---
    const fetchAndDisplayResumes = async () => {
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
                    <div>
                        <p class="list-item-title">${resume.filename}</p>
                        <p class="list-item-details">Uploaded: ${new Date(resume.upload_date).toLocaleDateString()}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button data-resume-id="${resume.id}" class="view-resume-btn btn-secondary">Details</button>
                        <button data-resume-id="${resume.id}" class="delete-resume-btn btn-secondary bg-red-100 text-red-700">Delete</button>
                    </div>`;
                resumesListDiv.appendChild(el);
            });
        } catch (error) {
            resumesListDiv.innerHTML = '<p class="text-red-700">Could not load resumes.</p>';
        }
    };

    const fetchAndDisplayJobDescriptions = async () => {
        if (!jobDescriptionsListDiv && !document.getElementById('jobSelect')) return;
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
                        <div>
                            <p class="list-item-title">${job.title} at ${job.company}</p>
                            <p class="list-item-details">Added: ${new Date(job.created_date).toLocaleDateString()}</p>
                        </div>
                        <div class="flex space-x-2">
                            <button data-job-id="${job.id}" class="view-job-btn btn-secondary">Details</button>
                            <button data-job-id="${job.id}" class="edit-job-btn btn-secondary">Edit</button>
                            <button data-job-id="${job.id}" class="delete-job-btn btn-secondary bg-red-100 text-red-700">Delete</button>
                        </div>`;
                    jobDescriptionsListDiv.appendChild(el);
                });
            }
            const jobSelect = document.getElementById('jobSelect');
            if (jobSelect) {
                jobSelect.innerHTML = '<option value="">-- Select a Job --</option>';
                jobs.forEach(job => jobSelect.innerHTML += `<option value="${job.id}">${job.title} at ${job.company}</option>`);
            }
        } catch (error) {
             if (jobDescriptionsListDiv) jobDescriptionsListDiv.innerHTML = '<p class="text-red-700">Could not load jobs.</p>';
        }
    };
    
    const renderMatchingResults = (results) => {
        if (!matchingResultsDiv) return;
        matchingResultsDiv.innerHTML = '';
        if (results.length === 0) {
            matchingResultsDiv.innerHTML = '<p class="text-gray-500">No matching resumes found.</p>';
            return;
        }
        results.forEach(result => {
            const resultCard = document.createElement('div');
            resultCard.className = 'card p-6 mb-4 border border-gray-200 shadow-sm';
            resultCard.innerHTML = `
                <h3 class="text-xl font-semibold text-indigo-800 mb-2">${result.filename}</h3>
                <div class="flex items-center mb-4">
                    <div class="score-bar-container flex-grow"><div class="score-bar" style="width: ${result.overall_score}%;"></div></div>
                    <span class="score-text">${result.overall_score}% Match</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div><p class="font-semibold">Experience Match: <span class="font-normal text-indigo-600">${result.match_details.experience_score}%</span></p></div>
                    <div><p class="font-semibold">Certifications Match: <span class="font-normal text-indigo-600">${result.match_details.certifications_score}%</span></p></div>
                    <div class="col-span-full"><p class="font-semibold">Matched Skills (${result.matched_skills.length}):</p><div class="flex flex-wrap gap-2" id="matched-${result.resume_id}"></div></div>
                    <div class="col-span-full"><p class="font-semibold">Missing Skills (${result.missing_skills.length}):</p><div class="flex flex-wrap gap-2" id="missing-${result.resume_id}"></div></div>
                </div>
            `;
            matchingResultsDiv.appendChild(resultCard);
            renderSkillTags(document.getElementById(`matched-${result.resume_id}`), result.matched_skills, 'matched');
            renderSkillTags(document.getElementById(`missing-${result.resume_id}`), result.missing_skills, 'missing');
        });
    };

    // --- Authentication Event Handlers ---
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

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const statusEl = document.getElementById('loginStatus');
            const formData = new FormData();
            formData.append('username', e.target.username.value);
            formData.append('password', e.target.password.value);
            showStatus(statusEl, 'Signing in...', 'info');
            try {
                const response = await fetch(`${API_BASE_URL}/login`, { method: 'POST', body: formData });
                if (!response.ok) throw new Error((await response.json()).detail);
                const data = await response.json();
                localStorage.setItem('user_token', data.access_token);
                window.location.href = '/dashboard';
            } catch (error) {
                showStatus(statusEl, `Error: ${error.message}`, 'error');
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('user_token');
            window.location.href = '/login';
        });
    }

    // --- Main Dashboard Form & Button Handlers ---
    if (uploadResumeForm) {
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
    }
    
    if (addJobDescriptionForm) {
        addJobDescriptionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const statusEl = document.getElementById('jobStatus');
            const jobData = {
                title: e.target.title.value, 
                company: e.target.company.value, 
                description: e.target.description.value,
                required_experience_years: e.target.required_experience_years.value ? parseInt(e.target.required_experience_years.value) : null,
                required_certifications: e.target.required_certifications.value.split(',').map(s => s.trim()).filter(Boolean)
            };
            showStatus(statusEl, 'Adding job...', 'info');
            try {
                const response = await fetchWithAuth(`${API_BASE_URL}/job-description`, { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify(jobData) 
                });
                if (!response.ok) throw new Error((await response.json()).detail);
                showStatus(statusEl, 'Job added successfully!', 'success');
                addJobDescriptionForm.reset();
                fetchAndDisplayJobDescriptions();
            } catch (error) {
                 showStatus(statusEl, `Error: ${error.message}`, 'error');
            }
        });
    }

    if (editJobDescriptionForm) {
        editJobDescriptionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const jobId = form.querySelector('#editJobId').value;
            const jobData = {
                title: form.querySelector('#editJobTitle').value, 
                company: form.querySelector('#editCompanyName').value, 
                description: form.querySelector('#editJobDescriptionText').value,
                required_skills: form.querySelector('#editRequiredSkills').value.split(',').map(s => s.trim()).filter(Boolean),
                required_experience_years: form.querySelector('#editRequiredExperienceYears').value ? parseInt(form.querySelector('#editRequiredExperienceYears').value) : null,
                required_certifications: form.querySelector('#editRequiredCertifications').value.split(',').map(s => s.trim()).filter(Boolean)
            };
            const statusEl = form.querySelector('#editJobStatus');
            showStatus(statusEl, 'Saving...', 'info');
            try {
                const response = await fetchWithAuth(`${API_BASE_URL}/job-description/${jobId}`, { 
                    method: 'PUT', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify(jobData) 
                });
                if (!response.ok) throw new Error((await response.json()).detail);
                showStatus(statusEl, 'Saved successfully!', 'success');
                setTimeout(() => jobEditModal.classList.remove('modal-active'), 1000);
                fetchAndDisplayJobDescriptions();
            } catch (error) {
                showStatus(statusEl, `Error: ${error.message}`, 'error');
            }
        });
    }
    
    if (matchResumesBtn) {
        matchResumesBtn.addEventListener('click', async () => {
            const jobId = document.getElementById('jobSelect').value;
            if (!jobId) {
                showStatus(matchStatus, 'Please select a job.', 'error');
                return;
            }
            showStatus(matchStatus, 'Matching...', 'info');
            const formData = new FormData();
            formData.append('job_id', jobId);
            try {
                const response = await fetchWithAuth(`${API_BASE_URL}/match-resumes`, { method: 'POST', body: formData });
                if (!response.ok) throw new Error((await response.json()).detail);
                renderMatchingResults(await response.json());
                showStatus(matchStatus, 'Matching complete.', 'success');
            } catch (error) {
                showStatus(matchStatus, `Error: ${error.message}`, 'error');
            }
        });
    }

    // --- Main Event Listener for Delegated Clicks (View, Edit, Delete buttons) ---
    document.body.addEventListener('click', async (e) => {
        const target = e.target;
        if (target.matches('.view-resume-btn')) {
            const resumeId = target.dataset.resumeId;
            const response = await fetchWithAuth(`${API_BASE_URL}/resume/${resumeId}`);
            if (!response.ok) { alert('Could not load resume details.'); return; }
            const resume = await response.json();
            
            resumeDetailsModal.querySelector('#modalResumeFilename').textContent = resume.filename;
            renderSkillTags(resumeDetailsModal.querySelector('#modalResumeSkills'), resume.extracted_skills);
            renderExperienceEntries(resumeDetailsModal.querySelector('#modalResumeExperience'), resume.experience);
            renderEducationEntries(resumeDetailsModal.querySelector('#modalResumeEducation'), resume.education);
            resumeDetailsModal.querySelector('#modalResumeRawText').textContent = resume.raw_text;
            resumeDetailsModal.classList.add('modal-active');
        }
        if (target.matches('.delete-resume-btn')) {
            if (confirm('Are you sure you want to delete this resume?')) {
                const resumeId = target.dataset.resumeId;
                await fetchWithAuth(`${API_BASE_URL}/resume/${resumeId}`, { method: 'DELETE' });
                fetchAndDisplayResumes();
            }
        }
        if (target.matches('.view-job-btn')) {
            const jobId = target.dataset.jobId;
            const response = await fetchWithAuth(`${API_BASE_URL}/job-description/${jobId}`);
            if (!response.ok) { alert('Could not load job details.'); return; }
            const job = await response.json();
            jobDetailsModal.querySelector('#modalJobTitle').textContent = job.title;
            jobDetailsModal.querySelector('#modalJobCompany').textContent = job.company;
            jobDetailsModal.querySelector('#modalJobRequiredExperience').textContent = job.required_experience_years !== null ? `${job.required_experience_years} years` : 'N/A';
            jobDetailsModal.querySelector('#modalJobDescriptionText').textContent = job.description;
            renderSkillTags(jobDetailsModal.querySelector('#modalJobRequiredSkills'), job.required_skills);
            renderSkillTags(jobDetailsModal.querySelector('#modalJobRequiredCertifications'), job.required_certifications);
            jobDetailsModal.classList.add('modal-active');
        }
        if (target.matches('.edit-job-btn')) {
            const jobId = target.dataset.jobId;
            const response = await fetchWithAuth(`${API_BASE_URL}/job-description/${jobId}`);
            if (!response.ok) { alert('Could not load job details for editing.'); return; }
            const job = await response.json();
            const form = editJobDescriptionForm;
            form.querySelector('#editJobId').value = job.id;
            form.querySelector('#editJobTitle').value = job.title;
            form.querySelector('#editCompanyName').value = job.company;
            form.querySelector('#editJobDescriptionText').value = job.description;
            form.querySelector('#editRequiredSkills').value = job.required_skills.join(', ');
            form.querySelector('#editRequiredExperienceYears').value = job.required_experience_years || '';
            form.querySelector('#editRequiredCertifications').value = job.required_certifications.join(', ');
            jobEditModal.classList.add('modal-active');
        }
        if (target.matches('.delete-job-btn')) {
            if (confirm('Are you sure you want to delete this job description?')) {
                const jobId = target.dataset.jobId;
                await fetchWithAuth(`${API_BASE_URL}/job-description/${jobId}`, { method: 'DELETE' });
                fetchAndDisplayJobDescriptions();
            }
        }
        if (target.matches('.close-button') || e.target.matches('.modal')) {
             document.querySelectorAll('.modal').forEach(modal => modal.classList.remove('modal-active'));
        }
    });
    
    // --- Initial Page Load ---
    if (protectedPages.some(page => currentPage.includes(page))) {
        if (currentPage.includes('/dashboard')) fetchAndDisplayJobDescriptions();
        if (currentPage.includes('/uploaded-resumes')) fetchAndDisplayResumes();
        if (currentPage.includes('/job-descriptions-page')) fetchAndDisplayJobDescriptions();
    }
});