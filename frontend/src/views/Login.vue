<template>
  <div class="container vh-100 d-flex align-items-center justify-content-center">
    <div class="card shadow-lg p-4" style="width: 400px; border-radius: 15px;">
      <h2 class="text-center text-primary mb-4">PPA V2 Login</h2>
      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input type="text" v-model="form.username" class="form-control" placeholder="admin" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input type="password" v-model="form.password" class="form-control" placeholder="******" required>
        </div>
        <button type="submit" class="btn btn-primary w-100 py-2">Sign In</button>
      </form>
      <p class="text-center mt-3 small">
        New Student? <router-link to="/register">Register</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  data() {
    return { form: { username: '', password: '' } };
  },
  methods: {
    async handleLogin() {
      try {
        const res = await axios.post('http://127.0.0.1:5000/api/login', this.form);

        // ─── STORE JWT TOKEN ───
        // Save the token separately so axios can use it in all future requests
        localStorage.setItem('access_token', res.data.access_token);

        // Save user info (role, user_id, username) for UI use
        localStorage.setItem('user', JSON.stringify({
          role: res.data.role,
          user_id: res.data.user_id,
          username: res.data.username
        }));

        // ─── SET DEFAULT AXIOS HEADER ───
        // Every future axios request will automatically include this token
        axios.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`;

        // Redirect based on role
        if (res.data.role === 'Admin') this.$router.push('/admin-dash');
        else if (res.data.role === 'Company') this.$router.push('/company-dash');
        else this.$router.push('/student-dash');

      } catch (err) {
        alert(err.response?.data?.error || "Login Failed");
      }
    }
  }
}
</script>