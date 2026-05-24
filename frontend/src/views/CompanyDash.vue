<template>
  <div class="container mt-4 pb-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="text-success fw-bold">{{ company.name }} Dashboard</h2>
      <button @click="logout" class="btn btn-outline-danger btn-sm">Logout</button>
    </div>

    <!-- Company Info Card -->
    <div class="card mb-4 border-0 shadow-sm bg-light">
      <div class="card-body">
        <h6 class="fw-bold">About Company</h6>
        <p class="mb-0 text-muted">{{ company.description || 'No description provided.' }}</p>
      </div>
    </div>

    <!-- Tabs -->
    <ul class="nav nav-pills mb-4">
      <li class="nav-item">
        <button class="nav-link active" data-bs-toggle="pill" data-bs-target="#my-drives">My Drives</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-bs-toggle="pill" data-bs-target="#new-drive">Post New Drive</button>
      </li>
    </ul>

    <div class="tab-content">

      <!-- Tab 1: My Drives -->
      <div class="tab-pane fade show active" id="my-drives">
        <div v-if="drives.length === 0" class="text-center text-muted py-5">
          <p class="mb-0">No drives created yet. Click <strong>Post New Drive</strong> to get started.</p>
        </div>

        <div class="row">
          <div v-for="drive in drives" :key="drive.id" class="col-md-6 mb-3">
            <div class="card shadow-sm h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <h5 class="card-title mb-0">{{ drive.title }}</h5>
                  <span :class="getDriveStatusBadge(drive.status)">
                    {{ getDriveStatusLabel(drive.status) }}
                  </span>
                </div>
                <p class="text-muted small mb-1"><i class="fas fa-calendar-alt"></i> Drive Date: {{ drive.date }}</p>
                <p class="text-muted small mb-1"><i class="fas fa-clock"></i> Deadline: {{ drive.deadline }}</p>
                <p class="text-muted small mb-3">
                  <i class="fas fa-check-circle text-success"></i>Min CGPA: {{ drive.eligibility != null ? drive.eligibility : 'Open to all' }}
                </p>
                <div class="bg-light p-2 rounded mb-3 text-center">
                  <span class="fw-bold h4">{{ drive.applicant_count }}</span><br>
                  <small class="text-uppercase text-muted">Applicants</small>
                </div>
                <button @click="viewApplicants(drive.id)" class="btn btn-sm btn-primary w-100">
                  Manage Applications
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 2: Post New Drive -->
      <div class="tab-pane fade" id="new-drive">
        <div class="card border-0 shadow-sm col-md-8 mx-auto p-4">
          <form @submit.prevent="createDrive">

            <div class="mb-3">
              <label class="form-label">Drive Title / Job Role</label>
              <input type="text" v-model="newDrive.title" class="form-control" required>
            </div>

            <div class="mb-3">
              <label class="form-label">Minimum CGPA Required</label>
              <input
                type="number"
                v-model="newDrive.eligibility"
                class="form-control"
                step="0.1"
                min="0"
                max="10"
                placeholder="e.g. 7.5 — leave blank for open to all"
              >
              <div class="form-text">Leave blank if there is no CGPA requirement.</div>
            </div>

            <div class="mb-3">
              <label class="form-label">Application Deadline</label>
              <input type="date" v-model="newDrive.deadline" class="form-control" required>
            </div>

            <div class="mb-3">
              <label class="form-label">Scheduled Drive Date</label>
              <input type="date" v-model="newDrive.date" class="form-control" required>
            </div>

            <div class="mb-3">
              <label class="form-label">Drive Description</label>
              <textarea v-model="newDrive.description" class="form-control" rows="3"
                placeholder="Describe the role, responsibilities, etc."></textarea>
            </div>

            <button type="submit" class="btn btn-success w-100">Submit for Admin Approval</button>
          </form>
        </div>
      </div>

    </div>

    <!-- Applications Modal -->
    <div v-if="showModal" class="modal show d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Applications for Drive</h5>
            <button @click="showModal = false" class="btn-close"></button>
          </div>
          <div class="modal-body">
            <div v-if="activeApplications.length === 0" class="text-center text-muted py-4">
              No applicants for this drive yet.
            </div>
            <table v-else class="table align-middle">
              <thead class="table-light">
                <tr>
                  <th>Student</th>
                  <th>Status</th>
                  <th>Interview Schedule</th>
                  <th>Update Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="app in activeApplications" :key="app.app_id">
                  <td>
                    {{ app.student_name }}<br>
                    <small class="text-muted">{{ app.student_email }}</small><br>
                    <small class="text-muted">CGPA: <strong>{{ app.cgpa ?? 'N/A' }}</strong></small><br>
                    <template v-if="app.resume">
                      <a
                        :href="`http://127.0.0.1:5000/static/uploads/${app.resume}`"
                        target="_blank"
                        class="btn btn-outline-secondary btn-sm mt-1"
                      ><i class="fas fa-file-pdf text-danger"></i>View Resume</a>
                    </template>
                    <span v-else class="text-danger small">No resume uploaded</span>
                  </td>
                  <td>
                    <span :class="getAppStatusBadge(app.status)" class="badge">{{ app.status }}</span>
                  </td>
                  <td style="min-width: 200px;">
                    <!-- Interview scheduling — only visible for Shortlisted applicants -->
                    <template v-if="app.status === 'Shortlisted'">
                      <div v-if="app.interview_date">
                        <small class="text-success fw-bold"><i class="fas fa-calendar-alt"></i> {{ app.interview_date }}</small><br>
                        <small class="text-muted">{{ app.interview_notes }}</small><br>
                        <button class="btn btn-link btn-sm p-0 mt-1" @click="openScheduler(app)"><i class="fas fa-edit"></i> Edit</button>
                      </div>
                      <button v-else class="btn btn-outline-primary btn-sm" @click="openScheduler(app)">
                        <i class="fas fa-calendar-alt"></i> Schedule Interview
                      </button>
                    </template>
                    <span v-else class="text-muted small">—</span>
                  </td>
                  <td>
                    <select class="form-select form-select-sm"
                      @change="updateStatus(app.app_id, $event.target.value)">
                      <option value="">Change Status</option>
                      <option value="Shortlisted">Shortlist</option>
                      <option value="Selected">Select</option>
                      <option value="Rejected">Reject</option>
                    </select>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Interview Scheduler Sub-Modal -->
    <div v-if="showScheduler" class="modal show d-block" style="background: rgba(0,0,0,0.65); z-index: 1060;">
      <div class="modal-dialog modal-sm">
        <div class="modal-content">
          <div class="modal-header">
            <h6 class="modal-title fw-bold">Schedule Interview</h6>
            <button @click="showScheduler = false" class="btn-close"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted small mb-3">Student: <strong>{{ schedulerApp.student_name }}</strong></p>
            <div class="mb-3">
              <label class="form-label small fw-bold">Interview Date <span class="text-danger">*</span></label>
              <input type="date" v-model="schedulerDate" class="form-control form-control-sm">
            </div>
            <div class="mb-3">
              <label class="form-label small fw-bold">Venue / Notes</label>
              <input type="text" v-model="schedulerNotes" class="form-control form-control-sm"
                placeholder="e.g. Room 301, Google Meet link, etc.">
            </div>
            <button @click="saveInterview" class="btn btn-success btn-sm w-100"><i class="fas fa-check-circle text-success"></i> Confirm Schedule</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import axios from 'axios';
export default {
  data() {
    return {
      user_id: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).user_id : null,
      company: {},
      drives: [],
      newDrive: { title: '', eligibility: '', deadline: '', date: '', description: '' },
      activeApplications: [],
      showModal: false,
      activeDriveId: null,   // ← track which drive's modal is open
      // Interview scheduler
      showScheduler: false,
      schedulerApp: {},
      schedulerDate: '',
      schedulerNotes: ''
    }
  },
  mounted() {
    if (!this.user_id) { this.$router.push('/'); return; }
    this.fetchData();
  },
  methods: {
    async fetchData() {
      try {
        const res = await axios.get(`http://127.0.0.1:5000/api/company/dashboard/${this.user_id}`);
        this.company = res.data.details;
        this.drives = res.data.drives;
      } catch (err) { console.error("Fetch error:", err); }
    },

    async createDrive() {
      try {
        await axios.post('http://127.0.0.1:5000/api/company/create_drive', {
          ...this.newDrive,
          user_id: this.user_id
        });
        alert("Drive submitted for Admin approval!");
        this.newDrive = { title: '', eligibility: '', deadline: '', date: '', description: '' };
        this.fetchData();
      } catch (error) {
        alert(error.response?.data?.error || "Failed to create drive.");
      }
    },

    async viewApplicants(driveId) {
      try {
        const res = await axios.get(`http://127.0.0.1:5000/api/company/applications/${driveId}`);
        this.activeApplications = res.data;
        this.activeDriveId = driveId;
        this.showModal = true;
      } catch (err) { console.error("Error fetching applicants:", err); }
    },

    async updateStatus(app_id, status) {
      if (!status) return;
      try {
        await axios.post('http://127.0.0.1:5000/api/company/update_status', { app_id, status });
        alert("Status Updated!");
        this.showModal = false;
        this.fetchData();
      } catch (err) { alert("Failed to update status."); }
    },

    // ─── Interview Scheduler ───
    openScheduler(app) {
      this.schedulerApp = app;
      this.schedulerDate = app.interview_date || '';
      this.schedulerNotes = app.interview_notes || '';
      this.showScheduler = true;
    },

    async saveInterview() {
      if (!this.schedulerDate) {
        alert("Please select an interview date.");
        return;
      }
      try {
        await axios.post('http://127.0.0.1:5000/api/company/schedule_interview', {
          app_id: this.schedulerApp.app_id,
          interview_date: this.schedulerDate,
          interview_notes: this.schedulerNotes
        });
        alert("Interview scheduled successfully!");
        this.showScheduler = false;
        // Refresh the applications list in the open modal
        await this.viewApplicants(this.activeDriveId);
      } catch (err) {
        alert("Failed to schedule interview.");
      }
    },

    getDriveStatusBadge(status) {
      if (status === 'Approved') return 'badge bg-success';
      if (status === 'Rejected') return 'badge bg-danger';
      return 'badge bg-warning text-dark';
    },

    getDriveStatusLabel(status) {
      if (status === 'Approved') return 'Live';
      if (status === 'Rejected') return 'Rejected by Admin';
      return 'Pending Admin';
    },

    getAppStatusBadge(status) {
      if (status === 'Selected') return 'bg-success';
      if (status === 'Rejected') return 'bg-danger';
      if (status === 'Shortlisted') return 'bg-warning text-dark';
      return 'bg-info text-dark';
    },

    logout() { localStorage.clear(); this.$router.push('/'); }
  }
}
</script>