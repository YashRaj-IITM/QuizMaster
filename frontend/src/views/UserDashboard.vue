<template>
  <div class="container mt-5">
    <div v-if="notification" :class="['alert', notificationType === 'success' ? 'alert-success' : 'alert-danger']" role="alert" style="position:sticky;top:0;z-index:1000;">
      {{ notification }}
    </div>
    <!-- Search Bar -->
    <div class="row mb-4">
      <div class="col-12">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="input-group">
              <span class="input-group-text bg-primary text-white">
                <i class="fas fa-search"></i>
              </span>
              <input 
                type="text" 
                class="form-control" 
                placeholder="Search subjects, chapters, or quizzes..."
                v-model="searchQuery"
                @input="performSearch"
              >
              <button 
                class="btn btn-outline-secondary" 
                type="button"
                @click="clearSearch"
                v-if="searchQuery"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div v-if="searchQuery && searchResults.length > 0" class="mt-3">
              <h6 class="text-muted mb-2">Search Results ({{ searchResults.length }})</h6>
              <div class="search-results">
                <div 
                  v-for="result in searchResults" 
                  :key="`${result.type}-${result.id}`"
                  class="search-result-item p-2 border rounded mb-2"
                  @click="handleSearchResultClick(result)"
                >
                  <div class="d-flex align-items-center">
                    <i :class="getSearchResultIcon(result.type)" class="text-primary me-2"></i>
                    <div class="flex-grow-1">
                      <strong>{{ result.name }}</strong>
                      <br>
                      <small class="text-muted">{{ result.type }} • {{ result.path }}</small>
                    </div>
                    <i class="fas fa-chevron-right text-muted"></i>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="searchQuery && searchResults.length === 0" class="mt-3">
              <p class="text-muted text-center mb-0">No results found for "{{ searchQuery }}"</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="fw-bold text-dark">Welcome, {{ user.full_name }} 👋</h2>
      <div v-if="upcomingQuiz" class="badge bg-danger text-white p-2">
        🔔 Upcoming Quiz: {{ formatDate(upcomingQuiz.date_of_quiz) }} (Subject: {{ upcomingQuiz.subject }})
      </div>
    </div>
    <div class="row">
      <!-- Subjects Section -->
      <div class="col-lg-3">
        <div class="card border-0 shadow-sm rounded-lg">
          <div class="card-header bg-white fw-bold text-center border-bottom">📚 Subjects</div>
          <div class="card-body">
            <div class="list-group">
              <a v-for="subject in subjects" :key="subject.id"
                 :href="`#subject-${subject.id}`"
                 class="list-group-item list-group-item-action text-dark fw-semibold"
                 :class="{ active: selectedSubject && selectedSubject.id === subject.id }"
                 @click.prevent="selectSubject(subject)">
                {{ subject.name }}
              </a>
            </div>
          </div>
        </div>
      </div>
      <!-- Chapters Section -->
      <div class="col-lg-3">
        <div class="card border-0 shadow-sm rounded-lg">
          <div class="card-header bg-white fw-bold text-center border-bottom">📖 Chapters</div>
          <div class="card-body">
            <div v-if="selectedSubject">
              <div class="list-group">
                <a v-for="chapter in selectedSubject.chapters" :key="chapter.id"
                   :href="`#chapter-${chapter.id}`"
                   class="list-group-item list-group-item-action text-dark fw-semibold"
                   :class="{ active: selectedChapter && selectedChapter.id === chapter.id }"
                   @click.prevent="selectChapter(chapter)">
                  {{ chapter.name }}
                </a>
              </div>
            </div>
            <p v-else class="text-muted text-center">Select a subject to view chapters.</p>
          </div>
        </div>
      </div>
      <!-- Quizzes Section -->
      <div class="col-lg-3">
        <div class="card border-0 shadow-sm rounded-lg">
          <div class="card-header bg-white fw-bold text-center border-bottom">📝 Quizzes</div>
          <div class="card-body">
            <div v-if="selectedChapter">
              <div v-for="quiz in selectedChapter.quizzes" :key="quiz.id" class="card quiz-card border-0 mb-3 shadow-sm">
                <div class="card-body text-center">
                  <h6 class="fw-bold text-primary">{{ formatDate(quiz.date_of_quiz) }}</h6>
                  <p class="text-muted"><strong>{{ quiz.remarks }}</strong></p>
                  <button v-if="isPast(quiz.date_of_quiz)" class="btn btn-danger btn-sm rounded-pill" disabled>Deadline Passed</button>
                  <button v-else-if="attemptedQuizzes.includes(quiz.id)" class="btn btn-secondary btn-sm rounded-pill" disabled>Already Attempted</button>
                  <router-link v-else :to="{ name: 'QuizAttempt', params: { quizId: quiz.id } }" class="btn btn-outline-primary btn-sm rounded-pill">Attempt Quiz</router-link>
                </div>
              </div>
            </div>
            <p v-else class="text-muted text-center">Select a chapter to see available quizzes.</p>
          </div>
        </div>
      </div>
      <!-- Upcoming Quiz / Info Section -->
      <div class="col-lg-3" v-if="upcomingQuiz">
        <div class="card border-0 shadow-sm rounded-lg h-100">
          <div class="card-header bg-white fw-bold text-center border-bottom">🔔 Upcoming Quiz</div>
          <div class="card-body d-flex flex-column justify-content-center align-items-center">
            <h6 class="fw-bold text-primary mb-2">{{ formatDate(upcomingQuiz.date_of_quiz) }}</h6>
            <p class="text-muted">Subject: {{ upcomingQuiz.subject }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Past Quiz Attempts Section (Collapsible) -->
    <div class="row mt-5">
      <div class="col-lg-12">
        <div class="card border-0 shadow-sm rounded-lg">
          <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
            <span>📊 Past Quiz Attempts</span>
            <button class="btn btn-sm btn-outline-secondary" @click="togglePastAttempts">
              {{ showPastAttempts ? 'Hide' : 'Show' }}
            </button>
          </div>
          <div class="card-body" v-show="showPastAttempts">
            <div v-if="pastAttempts.length">
              <div v-for="(attempt, idx) in pastAttempts" :key="idx" class="card border-0 shadow-sm mb-2 past-attempt-card">
                <div class="card-body p-2">
                  <h6 class="fw-bold text-primary mb-1">Quiz on {{ formatDate(attempt.quiz.date_of_quiz) }}</h6>
                  <small class="text-muted"><strong>Score:</strong> {{ attempt.score.total_score }}% | <strong>Attempted:</strong> {{ formatDateTime(attempt.score.time_stamp) }}</small>
                </div>
              </div>
            </div>
            <p v-else class="text-muted text-center">No past quiz attempts yet.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getUserDashboard } from '../api';

export default {
  name: 'UserDashboard',
  data() {
    return {
      user: {},
      upcomingQuiz: null,
      subjects: [],
      selectedSubject: null,
      selectedChapter: null,
      attemptedQuizzes: [],
      pastAttempts: [],
      showPastAttempts: true,
      notification: '',
      notificationType: '',
      notificationTimeout: null,
      searchQuery: '',
      searchResults: [],
      searchTimeout: null,
    };
  },
  methods: {
    async selectSubject(subject) {
      this.selectedSubject = subject;
      this.selectedChapter = null;
      // Don't refetch dashboard data when just selecting a subject
      // The chapters are already available in the subject object
    },
    async selectChapter(chapter) {
      this.selectedChapter = chapter;
      // Only fetch dashboard data when selecting a chapter to get quiz-specific data
      await this.fetchDashboard(this.selectedSubject.id, chapter.id);
    },
    togglePastAttempts() {
      this.showPastAttempts = !this.showPastAttempts;
    },
    formatDate(date) {
      const d = new Date(date);
      return d.toISOString().slice(0, 10);
    },
    formatDateTime(date) {
      const d = new Date(date);
      return d.toLocaleString();
    },
    isPast(date) {
      return new Date(date) < new Date();
    },
    showNotification(message, type = 'success') {
      this.notification = message;
      this.notificationType = type;
      if (this.notificationTimeout) clearTimeout(this.notificationTimeout);
      this.notificationTimeout = setTimeout(() => {
        this.notification = '';
        this.notificationType = '';
      }, 3000);
    },
    async fetchDashboard(subject_id = null, chapter_id = null) {
      const params = {};
      if (subject_id) params.subject_id = subject_id;
      if (chapter_id) params.chapter_id = chapter_id;
      try {
        const res = await getUserDashboard(params);
        const data = res.data;
        this.user = data.user;
        this.subjects = data.subjects;
        
        // Only update selected subject/chapter if they're not already set
        // This prevents the blinking issue
        if (!this.selectedSubject && data.selected_subject) {
          this.selectedSubject = data.selected_subject;
        }
        if (!this.selectedChapter && data.selected_chapter) {
          this.selectedChapter = data.selected_chapter;
        }
        
        this.pastAttempts = data.past_attempts;
        this.attemptedQuizzes = data.attempted_quizzes;
        this.upcomingQuiz = data.upcoming_quiz;
      } catch (error) {
        this.showNotification('Failed to load dashboard data.', 'error');
        console.error('Failed to fetch dashboard:', error);
      }
    },
    
    performSearch() {
      // Clear previous timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }
      
      // Debounce search to avoid too many searches
      this.searchTimeout = setTimeout(() => {
        this.searchResults = [];
        
        if (!this.searchQuery.trim()) {
          return;
        }
        
        const query = this.searchQuery.toLowerCase().trim();
        
        // Search through subjects
        this.subjects.forEach(subject => {
          if (subject.name.toLowerCase().includes(query)) {
            this.searchResults.push({
              type: 'Subject',
              id: subject.id,
              name: subject.name,
              path: `Subject`,
              data: subject
            });
          }
          
          // Search through chapters in this subject
          subject.chapters.forEach(chapter => {
            if (chapter.name.toLowerCase().includes(query)) {
              this.searchResults.push({
                type: 'Chapter',
                id: chapter.id,
                name: chapter.name,
                path: `${subject.name} > Chapter`,
                data: { subject, chapter }
              });
            }
            
            // Search through quizzes in this chapter
            chapter.quizzes.forEach(quiz => {
              if (quiz.remarks.toLowerCase().includes(query) || 
                  quiz.date_of_quiz.includes(query)) {
                this.searchResults.push({
                  type: 'Quiz',
                  id: quiz.id,
                  name: quiz.remarks,
                  path: `${subject.name} > ${chapter.name} > Quiz`,
                  data: { subject, chapter, quiz }
                });
              }
            });
          });
        });
        
        // Limit results to 10
        this.searchResults = this.searchResults.slice(0, 10);
      }, 300);
    },
    
    clearSearch() {
      this.searchQuery = '';
      this.searchResults = [];
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }
    },
    
    handleSearchResultClick(result) {
      switch (result.type) {
        case 'Subject':
          this.selectSubject(result.data);
          break;
        case 'Chapter':
          this.selectSubject(result.data.subject);
          this.selectChapter(result.data.chapter);
          break;
        case 'Quiz': {
          this.selectSubject(result.data.subject);
          this.selectChapter(result.data.chapter);
          // Navigate to quiz attempt if not attempted and not past
          const quiz = result.data.quiz;
          if (!this.isPast(quiz.date_of_quiz) && !this.attemptedQuizzes.includes(quiz.id)) {
            this.$router.push({ name: 'QuizAttempt', params: { quizId: quiz.id } });
          }
          break;
        }
      }
      
      // Clear search after selection
      this.clearSearch();
    },
    
    getSearchResultIcon(type) {
      switch (type) {
        case 'Subject':
          return 'fas fa-book';
        case 'Chapter':
          return 'fas fa-file-alt';
        case 'Quiz':
          return 'fas fa-question-circle';
        default:
          return 'fas fa-search';
      }
    },


  },
  async mounted() {
    await this.fetchDashboard();
  }
};
</script>

<style scoped>
body {
  background-color: #f4f6f9;
}
.card {
  border-radius: 12px;
}
.card-header {
  background-color: #ffffff !important;
  border-bottom: 1px solid #ddd;
  font-size: 16px;
  padding: 12px 16px;
}
.list-group-item {
  transition: all 0.3s ease-in-out;
  border-radius: 8px;
  margin-bottom: 6px;
  font-size: 15px;
  padding: 12px 14px;
  border: none;
}
.list-group-item:hover {
  background-color: rgba(0, 123, 255, 0.1);
  color: #007bff;
  transform: translateX(5px);
}
.active {
  background-color: #007bff !important;
  color: #ffffff !important;
}
.quiz-card {
  transition: all 0.3s ease-in-out;
  background: #ffffff;
  border-radius: 10px;
  padding: 12px;
  text-align: center;
}
.quiz-card:hover {
  background-color: #f8f9fa;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
}
.btn-outline-primary {
  border-radius: 8px;
  padding: 6px 14px;
  transition: all 0.3s ease-in-out;
}
.btn-outline-primary:hover {
  background-color: #007bff;
  color: #fff;
}
.past-attempt-card {
  border-left: 5px solid #007bff;
  padding: 8px;
  transition: all 0.3s ease-in-out;
}
.past-attempt-card:hover {
  background-color: #f8f9fa;
}
#toggle-past-attempts {
  font-size: 14px;
  padding: 4px 10px;
  border-radius: 6px;
}

/* Search Styles */
.search-results {
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6 !important;
}

.search-result-item:hover {
  background-color: #e9ecef;
  border-color: #007bff !important;
  transform: translateX(5px);
}

.search-result-item:active {
  transform: scale(0.98);
}

.input-group-text {
  border: none;
}

.form-control:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}
</style> 