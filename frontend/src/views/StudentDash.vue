<template>
  <div class="container mt-4 pb-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="text-primary fw-bold">Student Portal</h2>
      <button @click="logout" class="btn btn-outline-danger btn-sm">Logout</button>
    </div>

    <div class="row">
      <!-- LEFT: Profile Card -->
      <div class="col-md-4 mb-4">
        <div class="card shadow-sm border-0 p-3">
          <h5 class="border-bottom pb-2">My Profile</h5>
          <p class="small mb-1"><strong>Username:</strong> {{ profile.username || 'Loading...' }}</p>
          <p class="small mb-1 text-muted"><strong>Email:</strong> {{ profile.email || 'Loading...' }}</p>
          <!-- Show current CGPA -->
          <p class="small mb-1">
            <strong>CGPA:</strong>
            <span v-if="profile.cgpa != null" class="text-success ms-1 fw-bold">{{ profile.cgpa }}</span>
            <span v-else class="text-danger ms-1">Not set</span>
          </p>
          <p class="small mb-3">
            <strong>Resume:</strong>
            <span v-if="profile.resume" class="text-success ms-1">{{ profile.resume }}</span>
            <span v-else class="text-danger ms-1">Not Uploaded</span>
          </p>
          <hr>
          <form @submit.prevent="handleUpload">
            <label class="form-label small">Update Email</label>
            <input type="email" v-model="newEmail" class="form-control form-control-sm mb-2" :placeholder="profile.email">

            <!-- Update CGPA from profile -->
            <label class="form-label small">Update CGPA</label>
            <input
              type="number"
              v-model="newCgpa"
              class="form-control form-control-sm mb-2"
              step="0.01" min="0" max="10"
              :placeholder="profile.cgpa != null ? String(profile.cgpa) : 'e.g. 8.5'"
            >

            <label class="form-label small">Update Resume (PDF)</label>
            <input type="file" @change="onFileChange" class="form-control form-control-sm mb-2" accept=".pdf">
            <button type="submit" class="btn btn-sm btn-dark w-100">Save Changes</button>
          </form>
        </div>
      </div>

      <!-- RIGHT: Drives + History -->
      <div class="col-md-8">

        <!-- Search Bar -->
        <div class="d-flex gap-2 mb-4">
          <select v-model="searchType" class="form-select form-select-sm" style="width: 140px;">
            <option value="title">Drive Title</option>
            <option value="company">Company</option>
          </select>
          <input
            type="text"
            v-model="searchQuery"
            class="form-control form-control-sm"
            :placeholder="searchType === 'title' ? 'Search by drive title...' : 'Search by company name...'"
            @keyup.enter="handleSearch"
          >
          <button @click="handleSearch" class="btn btn-primary btn-sm px-3">Search</button>
          <button v-if="isSearching" @click="resetSearch" class="btn btn-secondary btn-sm px-3">Reset</button>
        </div>

        <!-- Approved Placement Drives -->
        <div class="card shadow-sm border-0 mb-4">
          <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
            Approved Placement Drives
            <span class="badge bg-primary">{{ displayedDrives.length }} Available</span>
          </div>
          <div class="list-group list-group-flush">
            <div v-if="displayedDrives.length === 0" class="list-group-item text-center py-4 text-muted">
              {{ isSearching ? `No drives found for "${lastSearch}"` : 'No approved drives available right now.' }}
            </div>

            <div v-for="drive in displayedDrives" :key="drive.id" class="list-group-item">
              <div class="d-flex justify-content-between align-items-start">
                <div>
                  <h6 class="mb-0 fw-bold">{{ drive.title }}</h6>
                  <small class="text-muted">{{ drive.company_name }}</small><br>
                  <small class="text-muted">
                    Drive Date: {{ drive.date }} &nbsp;|&nbsp; Deadline: {{ drive.deadline }}
                  </small><br>
                  <!-- Show min CGPA requirement -->
                  <small class="text-secondary">
                    Min CGPA: {{ drive.eligibility != null ? drive.eligibility : 'Open to all' }}
                  </small>
                </div>
                <div class="ms-3 text-end">
                  <!-- Already applied -->
                  <span v-if="drive.has_applied" class="badge bg-secondary">Applied</span>

                  <!-- Not eligible — show reason -->
                  <template v-else-if="!drive.is_eligible">
                    <span class="badge bg-danger mb-1 d-block">Not Eligible</span>
                    <small class="text-danger" style="font-size: 0.7rem;">
                      {{ drive.ineligibility_reason }}
                    </small>
                  </template>

                  <!-- Eligible — show Apply button -->
                  <button v-else @click="apply(drive.id)" class="btn btn-sm btn-primary">
                    Apply Now
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- My Applications / History -->
        <div class="card shadow-sm border-0">
          <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
            <span>My Applications / History</span>
            <button @click="triggerExport" class="btn btn-outline-success btn-sm" :disabled="exportLoading">
              {{ exportLoading ? 'Processing...' : 'Export History (CSV)' }}
            </button>
          </div>
          <div class="table-responsive">
            <table class="table mb-0 small">
              <thead class="table-light">
                <tr>
                  <th>Drive</th>
                  <th>Company</th>
                  <th>Applied On</th>
                  <th>Status</th>
                  <th>Interview Date</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="history.length === 0">
                  <td colspan="5" class="text-center text-muted py-3">No applications yet.</td>
                </tr>
                <tr v-for="h in history" :key="h.drive_title + h.application_date">
                  <td>{{ h.drive_title }}</td>
                  <td>{{ h.company_name }}</td>
                  <td>{{ h.application_date ? h.application_date.split('T')[0] : 'N/A' }}</td>
                  <td>
                    <span :class="getStatusClass(h.status)" class="badge">{{ h.status }}</span>
                  </td>
                  <td>
                    <span v-if="h.interview_date" class="text-success fw-bold small">
                      <i class="fas fa-calendar-alt"></i>{{ h.interview_date }}<br>
                      <span class="text-muted fw-normal">{{ h.interview_notes }}</span>
                    </span>
                    <span v-else class="text-muted small">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
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
      exportLoading: false,
      user_id: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).user_id : null,
      profile: {},
      drives: [],
      displayedDrives: [],
      history: [],
      searchQuery: '',
      searchType: 'title',
      isSearching: false,
      lastSearch: '',
      selectedFile: null,
      newEmail: '',
      newCgpa: ''    // ← for updating CGPA from profile
    }
  },
  mounted() {
    if (this.user_id) { this.fetchData(); }
    else { this.$router.push('/'); }
  },
  methods: {
    async fetchData() {
      try {
        const [drivesRes, profileRes, historyRes] = await Promise.all([
          axios.get(`http://127.0.0.1:5000/api/student/dashboard/${this.user_id}`),
          axios.get(`http://127.0.0.1:5000/api/student/profile/${this.user_id}`),
          axios.get(`http://127.0.0.1:5000/api/student/history/${this.user_id}`)
        ]);
        this.drives = drivesRes.data;
        this.displayedDrives = drivesRes.data;
        this.profile = profileRes.data;
        this.history = historyRes.data;
      } catch (err) { console.error("Fetch error:", err); }
    },

    handleSearch() {
      const q = this.searchQuery.trim();
      if (!q) return;
      this.lastSearch = q;
      this.isSearching = true;
      if (this.searchType === 'title') {
        this.displayedDrives = this.drives.filter(d => d.title.toLowerCase().includes(q.toLowerCase()));
      } else {
        this.displayedDrives = this.drives.filter(d => d.company_name.toLowerCase().includes(q.toLowerCase()));
      }
    },

    resetSearch() {
      this.searchQuery = '';
      this.searchType = 'title';
      this.isSearching = false;
      this.lastSearch = '';
      this.displayedDrives = this.drives;
    },

    async apply(driveId) {
      try {
        await axios.post('http://127.0.0.1:5000/api/student/apply', {
          user_id: this.user_id,
          drive_id: driveId
        });
        alert("Applied Successfully!");
        this.fetchData();
      } catch (err) {
        alert(err.response?.data?.error || "Application failed");
      }
    },

    onFileChange(e) { this.selectedFile = e.target.files[0]; },

    async handleUpload() {
      const formData = new FormData();
      formData.append('user_id', this.user_id);
      if (this.selectedFile) formData.append('resume', this.selectedFile);
      if (this.newEmail) formData.append('email', this.newEmail);
      if (this.newCgpa) formData.append('cgpa', this.newCgpa);   // ← send CGPA update

      try {
        await axios.post('http://127.0.0.1:5000/api/student/update_profile', formData);
        alert("Profile updated!");
        this.newEmail = '';
        this.newCgpa = '';
        this.fetchData();  // Refresh drives — eligibility will re-evaluate
      } catch (err) { alert("Upload failed"); }
    },

    getStatusClass(status) {
      if (status === 'Selected') return 'bg-success';
      if (status === 'Rejected') return 'bg-danger';
      if (status === 'Shortlisted') return 'bg-warning text-dark';
      return 'bg-info text-dark';
    },

    async triggerExport() {
      this.exportLoading = true;
      try {
        const response = await axios.post('http://127.0.0.1:5000/api/student/export-history', {
          email: this.profile.email
        });
        alert(response.data.message);
      } catch (error) {
        alert("Export failed. Ensure Celery/Redis is running!");
      } finally {
        this.exportLoading = false;
      }
    },

    logout() { localStorage.clear(); this.$router.push('/'); }
  }
}
</script>