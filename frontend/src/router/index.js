import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import AdminDash from '../views/AdminDash.vue'
import CompanyDash from '../views/CompanyDash.vue' 
import StudentDash from '../views/StudentDash.vue'

const routes = [
  { path: '/', component: Login },
  { path: '/register', component: Register },
  { path: '/admin-dash', component: AdminDash },
  { path: '/company-dash', component: CompanyDash },
  { path: '/student-dash', component: StudentDash }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ROUTE GUARD — Preventing unauthorized access

router.beforeEach((to) => {
  const user = localStorage.getItem('user')
    ? JSON.parse(localStorage.getItem('user'))
    : null;

  const protectedRoutes = {
    '/admin-dash': 'Admin',
    '/company-dash': 'Company',
    '/student-dash': 'Student'
  }

  const requiredRole = protectedRoutes[to.path];

  if (requiredRole) {
    if (!user) return '/';                        
    if (user.role !== requiredRole) return '/';
  }

  return true;
});
export default router