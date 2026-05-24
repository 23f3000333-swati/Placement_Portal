import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import '@fortawesome/fontawesome-free/css/all.css'

// Import Bootstrap CSS and JS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

// ─── UPDATED TO EXPLICIT PRODUCTION RENDER LINK ───
axios.defaults.baseURL = 'https://ppa-backend-cxvk.onrender.com';

// RESTORE JWT TOKEN ON PAGE LOAD / REFRESH
const token = localStorage.getItem('access_token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

const app = createApp(App)

app.use(router)

app.mount('#app')