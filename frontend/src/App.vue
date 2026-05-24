<template>
  <div id="app">
    <nav class="navbar navbar-dark bg-primary mb-4">
      <div class="container d-flex justify-content-between align-items-center">
        <span class="navbar-brand mb-0 h1"><i class="fas fa-graduation-cap me-2"></i> Placement Portal V2</span>
        <span v-if="user && $route.path !== '/' && $route.path !== '/register'" class="navbar-text text-white d-flex align-items-center gap-2">
          <i class="fas fa-user-circle"></i><strong>{{ user.username }}</strong>
          <span class="badge bg-light text-dark">{{ user.role }}</span>
        </span>
      </div>
    </nav>
    <router-view @vue:mounted="refreshUser" />
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      user: null
    }
  },
  mounted() {
    this.refreshUser();
  },
  watch: {
    // Watch route changes — refresh user on every page navigation
    $route() {
      this.refreshUser();
    }
  },
  methods: {
    refreshUser() {
      const u = localStorage.getItem('user');
      this.user = u ? JSON.parse(u) : null;
    }
  }
}
</script>

<style>
body {
  background-color: #f8f9fa;
}
</style>