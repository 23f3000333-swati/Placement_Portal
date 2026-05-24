import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import '@fortawesome/fontawesome-free/css/all.css'

// Import Bootstrap CSS and JS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

// ─── ADD THIS LINE FOR DYNAMIC AXIOS ROUTING ───
// This tells axios to use whatever URL is configured in your active environment variables (.env files)
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL;

// RESTORE JWT TOKEN ON PAGE LOAD / REFRESH | When user refreshes the page, axios loses its default headers. This restores the token from localStorage so all API calls keep working.
const token = localStorage.getItem('access_token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

const app = createApp(App)

app.use(router)

app.mount('#app')