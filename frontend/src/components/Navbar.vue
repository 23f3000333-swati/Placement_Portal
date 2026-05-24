<template>
  <nav class="navbar">
    <ul>
      <li><router-link to="/">Login</router-link></li>
      <li><router-link to="/admin">Admin Dashboard</router-link></li>
      <li><router-link to="/company">Company Dashboard</router-link></li>
      <li><router-link to="/student">Student Dashboard</router-link></li>
    </ul>
  </nav>
</template>

<script>
export default {
  name: 'Navbar',
};
</script>

<style>
.navbar {
  background-color: #333;
  color: white;
  padding: 10px;
}
.navbar ul {
  list-style: none;
  display: flex;
  gap: 10px;
}
.navbar a {
  color: white;
  text-decoration: none;
}
</style>