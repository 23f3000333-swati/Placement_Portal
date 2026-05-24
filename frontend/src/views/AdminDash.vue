<template>
  <div class="container mt-4 pb-5">

    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
      <h2 class="fw-bold text-primary">Admin Control Center</h2>
      <div class="d-flex gap-2">
        <!-- Dropdown: Student / Company / Drive -->
        <select v-model="searchRole" class="form-select form-select-sm" style="width: 130px;">
          <option value="Student">Student</option>
          <option value="Company">Company</option>
          <option value="Drive">Drive</option>
        </select>
        <input
          type="text"
          v-model="searchQuery"
          class="form-control form-control-sm"
          :placeholder="searchRole === 'Drive' ? 'Search by drive title...' : 'Search by name/email...'"
        >
        <button @click="handleSearch" class="btn btn-primary btn-sm px-3">Search</button>
        <button v-if="isSearching" @click="resetSearch" class="btn btn-secondary btn-sm px-3">Reset</button>
        <button @click="logout" class="btn btn-outline-danger btn-sm px-3">Logout</button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="row mb-4">
      <div class="col-md-4" v-for="(val, key) in data.stats" :key="key">
        <div class="card shadow-sm border-0 bg-light text-center py-2">
          <div class="card-body">
            <p class="text-muted text-uppercase mb-1 small fw-bold">{{ key.replace(/_/g, ' ') }}</p>
            <h2 class="fw-bold text-dark">{{ val }}</h2>
          </div>
        </div>
      </div>
    </div>

    <!-- Global Student Applications -->
    <div class="card mb-4 shadow-sm border-0">
      <div class="card-header bg-primary text-white fw-bold">Global Student Applications</div>
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-light">
            <tr>
              <th>Student</th>
              <th>Company</th>
              <th>Placement Drive</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!data.applications || data.applications.length === 0">
              <td colspan="4" class="text-center text-muted py-3">No applications recorded yet.</td>
            </tr>
            <tr v-for="app in data.applications" :key="app.id">
              <td>{{ app.student_name }}</td>
              <td>{{ app.company_name }}</td>
              <td>{{ app.drive_title }}</td>
              <td>
                <span :class="getStatusBadge(app.status)" class="badge">{{ app.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Student Directory -->
    <div class="card mb-4 shadow-sm border-0">
      <div class="card-header bg-white fw-bold border-bottom">
        Student Directory
        <span v-if="isSearching && searchRole === 'Student'" class="text-muted small ms-2">
          — showing results for "{{ lastSearch }}"
        </span>
      </div>
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-light">
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!data.students || data.students.length === 0">
              <td colspan="4" class="text-center text-muted py-3">
                {{ isSearching && searchRole === 'Student' ? `No student found with "${lastSearch}"` : 'No students registered yet.' }}
              </td>
            </tr>
            <tr v-for="s in data.students" :key="s.id">
              <td>{{ s.username }}</td>
              <td>{{ s.email }}</td>
              <td>
                <span :class="s.is_active ? 'badge bg-success' : 'badge bg-danger'">
                  {{ s.is_active ? 'Active' : 'Blacklisted' }}
                </span>
              </td>
              <td>
                <button
                  @click="toggleUserStatus(s.id)"
                  :class="s.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                  class="btn btn-sm px-3"
                >
                  {{ s.is_active ? 'Blacklist' : 'Activate' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Company Management + Drive Requests -->
    <div class="row">

      <!-- Company Management -->
      <div class="col-md-6 mb-4">
        <div class="card shadow-sm border-0 h-100">
          <div class="card-header bg-white fw-bold">
            Company Management
            <span v-if="isSearching && searchRole === 'Company'" class="text-muted small ms-2">
              — showing results for "{{ lastSearch }}"
            </span>
          </div>
          <ul class="list-group list-group-flush">
            <li
              v-if="!data.companies || data.companies.length === 0"
              class="list-group-item text-center text-muted py-3"
            >
              {{ isSearching && searchRole === 'Company' ? `No company found with "${lastSearch}"` : 'No companies registered yet.' }}
            </li>
            <li
              v-for="c in data.companies"
              :key="c.id"
              class="list-group-item d-flex justify-content-between align-items-center py-3"
            >
              <div>
                <span class="d-block fw-bold">{{ c.name }}</span>
                <span :class="c.is_approved ? 'text-success small' : 'text-warning small'">
                  {{ c.is_approved ? '● Approved' : '● Pending Approval' }}
                </span>
              </div>
              <div class="btn-group">
                <button v-if="!c.is_approved" @click="approveCompany(c.id)" class="btn btn-success btn-sm">
                  Approve
                </button>
                <button v-if="!c.is_approved" @click="rejectCompany(c.id)" class="btn btn-danger btn-sm">
                  Reject
                </button>
                <button
                  @click="toggleUserStatus(c.user_id)"
                  :class="c.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                  class="btn btn-sm"
                >
                  {{ c.is_active ? 'Blacklist' : 'Enable' }}
                </button>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- Drive Requests -->
      <div class="col-md-6 mb-4">
        <div class="card shadow-sm border-0 h-100">
          <div class="card-header bg-white fw-bold">
            Placement Drive Requests
            <span v-if="isSearching && searchRole === 'Drive'" class="text-muted small ms-2">
              — showing results for "{{ lastSearch }}"
            </span>
          </div>
          <ul class="list-group list-group-flush">
            <li
              v-if="!data.drives || data.drives.length === 0"
              class="list-group-item text-center text-muted py-3"
            >
              {{ isSearching && searchRole === 'Drive' ? `No drive found with "${lastSearch}"` : 'No drives submitted yet.' }}
            </li>
            <li
              v-for="d in data.drives"
              :key="d.id"
              class="list-group-item d-flex justify-content-between align-items-center py-3"
            >
              <div>
                <span class="d-block fw-bold">{{ d.title }}</span>
                <span :class="d.is_approved ? 'text-success small' : 'text-warning small'">
                  {{ d.is_approved ? '● Live on Portal' : '● Pending Review' }}
                </span>
              </div>
              <div class="btn-group">
                <button v-if="!d.is_approved" @click="approveDrive(d.id)" class="btn btn-success btn-sm">
                  Approve
                </button>
                <button v-if="!d.is_approved" @click="rejectDrive(d.id)" class="btn btn-danger btn-sm">
                  Reject
                </button>
                <span v-if="d.is_approved" class="badge bg-success align-self-center">Live</span>
              </div>
            </li>
          </ul>
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
      data: {
        stats: {},
        students: [],
        companies: [],
        drives: [],
        applications: []
      },
      searchQuery: '',
      searchRole: 'Student',
      isSearching: false,
      lastSearch: ''
    }
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      try {
        const [dashRes, appRes] = await Promise.all([
          axios.get('http://127.0.0.1:5000/api/admin/dashboard_data'),
          axios.get('http://127.0.0.1:5000/api/admin/all_applications')
        ]);
        this.data = dashRes.data;
        this.data.applications = appRes.data;
      } catch (err) {
        console.error("Load error:", err);
      }
    },

    async approveCompany(id) {
      await axios.post(`http://127.0.0.1:5000/api/admin/approve_company/${id}`);
      this.loadData();
    },

    async rejectCompany(id) {
      const confirm_action = confirm("Are you sure you want to reject this company?");
      if (confirm_action) {
        await axios.post(`http://127.0.0.1:5000/api/admin/reject_company/${id}`);
        this.loadData();
      }
    },

    async approveDrive(id) {
      await axios.post(`http://127.0.0.1:5000/api/admin/approve_drive/${id}`);
      this.loadData();
    },

    async rejectDrive(id) {
      const confirm_action = confirm("Are you sure you want to reject this drive?");
      if (confirm_action) {
        await axios.post(`http://127.0.0.1:5000/api/admin/reject_drive/${id}`);
        this.loadData();
      }
    },

    async toggleUserStatus(userId) {
      const action = confirm("Change access status for this account?");
      if (action) {
        await axios.post(`http://127.0.0.1:5000/api/admin/toggle_user_status/${userId}`);
        this.loadData();
      }
    },

    async handleSearch() {
      if (!this.searchQuery) return;
      try {
        const res = await axios.get(
          `http://127.0.0.1:5000/api/admin/search?q=${this.searchQuery}&role=${this.searchRole}`
        );

        this.lastSearch = this.searchQuery;
        this.isSearching = true;

        if (this.searchRole === 'Student') {
          // ONLY update student section
          this.data.students = res.data.map(u => ({
            id: u.id,
            username: u.username,
            email: u.email,
            is_active: u.is_active
          }));
        } else if (this.searchRole === 'Company') {
          // ONLY update company section
          this.data.companies = res.data.map(u => ({
            id: u.company_id,
            name: u.company_name,
            is_approved: u.is_approved,
            user_id: u.id,
            is_active: u.is_active
          }));
        } else if (this.searchRole === 'Drive') {
          // ONLY update drives section
          this.data.drives = res.data.map(d => ({
            id: d.id,
            title: d.title,
            status: d.status,
            is_approved: d.is_approved
          }));
        }
      } catch (err) {
        console.error("Search error:", err);
      }
    },

    resetSearch() {
      this.searchQuery = '';
      this.searchRole = 'Student';
      this.isSearching = false;
      this.lastSearch = '';
      this.loadData();
    },

    getStatusBadge(status) {
      if (status === 'Selected') return 'bg-success';
      if (status === 'Rejected') return 'bg-danger';
      if (status === 'Shortlisted') return 'bg-warning text-dark';
      return 'bg-info text-dark';
    },

    logout() {
      localStorage.clear();
      this.$router.push('/');
    }
  }
}
</script>