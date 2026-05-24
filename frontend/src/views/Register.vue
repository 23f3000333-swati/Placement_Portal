<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card shadow border-0">
          <div class="card-body p-4">
            <h2 class="text-center mb-4">Create Account</h2>
            <form @submit.prevent="handleRegister">

              <div class="mb-3">
                <label class="form-label">I am a:</label>
                <select v-model="form.role" class="form-select" required>
                  <option value="Student">Student</option>
                  <option value="Company">Company</option>
                </select>
              </div>

              <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" v-model="form.username" class="form-control" required />
              </div>

              <div class="mb-3">
                <label class="form-label">Email</label>
                <input type="email" v-model="form.email" class="form-control" required />
              </div>

              <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" v-model="form.password" class="form-control" required />
              </div>

              <!-- Student-only: CGPA -->
              <div v-if="form.role === 'Student'" class="mb-3">
                <label class="form-label">Your CGPA</label>
                <input
                  type="number"
                  v-model="form.cgpa"
                  class="form-control"
                  step="0.01"
                  min="0"
                  max="10"
                  placeholder="e.g. 8.5"
                  required
                />
                <div class="form-text">Enter your current CGPA (used for drive eligibility checks)</div>
              </div>

              <!-- Company-only fields -->
              <div v-if="form.role === 'Company'" class="mb-3">
                <label class="form-label">Company Name</label>
                <input type="text" v-model="form.company_name" class="form-control" required />
              </div>

              <div v-if="form.role === 'Company'" class="mb-3">
                <label class="form-label">Company Description</label>
                <textarea v-model="form.description" class="form-control" rows="3"
                  placeholder="Brief description about your company" required></textarea>
              </div>

              <div v-if="form.role === 'Company'" class="mb-3">
                <label class="form-label">HR Contact</label>
                <input type="text" v-model="form.hr_contact" class="form-control"
                  placeholder="HR phone or email" required />
              </div>

              <div v-if="form.role === 'Company'" class="mb-3">
                <label class="form-label">Website</label>
                <input type="url" v-model="form.website" class="form-control"
                  placeholder="https://yourcompany.com" />
              </div>

              <button type="submit" class="btn btn-success w-100">Register</button>
            </form>
            <div class="mt-3 text-center">
              <router-link to="/">Back to Login</router-link>
            </div>
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
      form: {
        role: 'Student',
        username: '',
        email: '',
        password: '',
        cgpa: '',           // ← NEW for students
        company_name: '',
        description: '',
        hr_contact: '',
        website: ''
      }
    };
  },
  methods: {
    async handleRegister() {
      try {
        await axios.post('http://127.0.0.1:5000/api/register', this.form);
        alert("Registration Successful! Please login.");
        this.$router.push('/');
      } catch (err) {
        alert(err.response?.data?.error || "Registration Failed");
      }
    }
  }
};
</script>