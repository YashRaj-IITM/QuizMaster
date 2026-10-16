import axios from 'axios';

// Empty baseURL in development: the dev server proxies /api to Flask (vue.config.js).
// Set VUE_APP_API_URL (see .env.example) when the API is hosted elsewhere.
const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || ''
});

// Attach the Flask-Security access token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers['Authentication-Token'] = token;
  return config;
});

// Expired / invalid token: clear the session and go back to the login page
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = (error.config && error.config.url) || '';
    if (error.response && error.response.status === 401 && !url.includes('/api/login')) {
      clearAuthSession();
      if (!window.location.pathname.startsWith('/login')) window.location.assign('/login');
    }
    return Promise.reject(error);
  }
);

// Token management
export function setAuthToken(token) {
  if (token) localStorage.setItem('token', token);
  else localStorage.removeItem('token');
}

export function getAuthToken() {
  return localStorage.getItem('token');
}

// Remove only this application's session keys; preserve unrelated browser storage.
export function clearAuthSession() {
  ['token', 'is_admin', 'full_name', 'user'].forEach((key) => localStorage.removeItem(key));
}

// Auth APIs
export function login(email, password) {
  return api.post('/api/login', { email, password });
}

export function register(email, full_name, password, qualification = '', dob = '') {
  return api.post('/api/register', { email, full_name, password, qualification, dob });
}

export function logout() {
  return api.post('/api/logout');
}

// User APIs
export function getUserDashboard(params) {
  return api.get('/api/user/dashboard', { params });
}
export function getLeaderboard() {
  return api.get('/api/user/leaderboard');
}
export function getQuizStats() {
  return api.get('/api/user/quiz_stats');
}
export function getQuiz(quizId, questionIndex = 0) {
  return api.get(`/api/user/quiz/${quizId}`, { 
    params: { question_index: questionIndex } 
  });
}
export function submitQuiz(quizId, user_answers) {
  return api.post(`/api/user/quiz/${quizId}/submit`, { user_answers });
}

// User CSV export of quiz history (async Celery job; poll until the file is ready)
export function startExport() {
  return api.post('/api/user/export');
}
export function downloadExport(taskId) {
  return api.get(`/api/user/export/${taskId}`, { responseType: 'blob' });
}

// Admin APIs
export function getSubjects() {
  return api.get('/api/admin/subjects');
}
export function createSubject(name) {
  return api.post('/api/admin/subjects', { name });
}
export function updateSubject(id, name) {
  return api.put(`/api/admin/subjects/${id}`, { name });
}
export function deleteSubject(id) {
  return api.delete(`/api/admin/subjects/${id}`);
}

export function getChapters(subject_id) {
  return api.get('/api/admin/chapters', { params: { subject_id } });
}
export function createChapter(name, subject_id) {
  return api.post('/api/admin/chapters', { name, subject_id });
}
export function updateChapter(id, name) {
  return api.put(`/api/admin/chapters/${id}`, { name });
}
export function deleteChapter(id) {
  return api.delete(`/api/admin/chapters/${id}`);
}

export function getQuizzes(chapter_id) {
  return api.get('/api/admin/quizzes', { params: { chapter_id } });
}
export function createQuiz(chapter_id, date_of_quiz, remarks, time_duration = '') {
  return api.post('/api/admin/quizzes', { chapter_id, date_of_quiz, remarks, time_duration });
}
export function updateQuiz(id, data) {
  return api.put(`/api/admin/quizzes/${id}`, data);
}
export function deleteQuiz(id) {
  return api.delete(`/api/admin/quizzes/${id}`);
}

export function getQuestions(quiz_id) {
  return api.get('/api/admin/questions', { params: { quiz_id } });
}
export function createQuestion(quiz_id, question_statement, option1, option2, option3, option4, correct_option) {
  return api.post('/api/admin/questions', { quiz_id, question_statement, option1, option2, option3, option4, correct_option });
}
export function updateQuestion(id, data) {
  return api.put(`/api/admin/questions/${id}`, data);
}
export function deleteQuestion(id) {
  return api.delete(`/api/admin/questions/${id}`);
}

export function getUsers() {
  return api.get('/api/admin/users');
}

export function getAdminStats() {
  return api.get('/api/admin/stats');
}

export function scheduleReminder(email, reminder_time, subject = 'Quiz Reminder', body = 'This is your quiz reminder!') {
  return api.post('/api/user/reminders', { email, reminder_time, subject, body });
}

export function getInactiveUsers(onlyPending = false) {
  return api.get('/api/admin/inactive_users', { 
    params: { only_pending: onlyPending } 
  });
}

export function scheduleBulkReminders(user_ids, reminder_time, subject, body) {
  return api.post('/api/admin/reminders', { user_ids, reminder_time, subject, body });
}

export function scheduleMonthlyReport(cron_expression, recipients) {
  return api.post('/api/admin/scheduled_reports', { 
    cron_expression, 
    recipients
  });
}

export function getScheduledReports() {
  return api.get('/api/admin/scheduled_reports');
}

export function deleteScheduledReport(reportId) {
  return api.delete(`/api/admin/scheduled_reports/${reportId}`);
}

export function exportCSVEmail() {
  return api.post('/api/admin/export_csv_email');
}

export default api; 