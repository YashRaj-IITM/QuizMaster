<template>
  <div class="container mt-4">
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading statistics...</p>
    </div>

    <div v-else>
      <!-- Header -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold text-dark">📊 Admin Statistics</h2>
        <button class="btn btn-outline-primary" @click="refreshStats">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
      </div>

      <!-- Overview Cards -->
      <div class="row mb-4">
        <div class="col-md-3 mb-3">
          <div class="card bg-primary text-white h-100">
            <div class="card-body text-center">
              <i class="fas fa-users fa-2x mb-2"></i>
              <h3 class="mb-0">{{ stats.totalUsers }}</h3>
              <p class="mb-0">Total Users</p>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card bg-success text-white h-100">
            <div class="card-body text-center">
              <i class="fas fa-question-circle fa-2x mb-2"></i>
              <h3 class="mb-0">{{ stats.totalQuizzes }}</h3>
              <p class="mb-0">Total Quizzes</p>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card bg-info text-white h-100">
            <div class="card-body text-center">
              <i class="fas fa-clipboard-check fa-2x mb-2"></i>
              <h3 class="mb-0">{{ stats.totalAttempts }}</h3>
              <p class="mb-0">Quiz Attempts</p>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card bg-warning text-white h-100">
            <div class="card-body text-center">
              <i class="fas fa-book fa-2x mb-2"></i>
              <h3 class="mb-0">{{ stats.totalQuestions }}</h3>
              <p class="mb-0">Total Questions</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Quiz Performance Table -->
      <div class="row">
        <div class="col-lg-8">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">📈 Quiz Performance Overview</h5>
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead class="table-dark">
                    <tr>
                      <th>Quiz</th>
                      <th>Subject</th>
                      <th>Date</th>
                      <th>Attempts</th>
                      <th>Avg Score</th>
                      <th>Completion Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="quiz in stats.quizStats" :key="quiz.id">
                      <td>
                        <strong>{{ quiz.remarks }}</strong>
                      </td>
                      <td>{{ quiz.subject }}</td>
                      <td>{{ formatDate(quiz.date_of_quiz) }}</td>
                      <td>
                        <span class="badge bg-primary">{{ quiz.attempts }}</span>
                      </td>
                      <td>
                        <span class="badge" :class="getScoreBadgeClass(quiz.avgScore)">
                          {{ quiz.avgScore.toFixed(1) }}%
                        </span>
                      </td>
                      <td>
                        <div class="progress" style="height: 20px;">
                          <div 
                            class="progress-bar" 
                            :class="getCompletionBadgeClass(quiz.completionRate)"
                            :style="{ width: quiz.completionRate + '%' }"
                          >
                            {{ quiz.completionRate.toFixed(1) }}%
                          </div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- User Activity Sidebar -->
        <div class="col-lg-4">
          <div class="card mb-3">
            <div class="card-header">
              <h6 class="mb-0">👥 Recent User Activity</h6>
            </div>
            <div class="card-body">
              <div v-for="activity in stats.recentActivity" :key="activity.id" class="d-flex align-items-center mb-2">
                <div class="avatar me-2">
                  <i class="fas fa-user-circle fa-lg text-primary"></i>
                </div>
                <div class="flex-grow-1">
                  <small class="fw-bold">{{ activity.user_name }}</small>
                  <br>
                  <small class="text-muted">{{ activity.action }} - {{ formatDateTime(activity.timestamp) }}</small>
                </div>
              </div>
            </div>
          </div>

          <!-- Top Performers -->
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">🏆 Top Performers</h6>
            </div>
            <div class="card-body">
              <div v-for="(performer, index) in stats.topPerformers" :key="performer.id" class="d-flex align-items-center mb-2">
                <div class="rank me-2">
                  <span class="badge" :class="getRankBadgeClass(index + 1)">
                    {{ index + 1 }}
                  </span>
                </div>
                <div class="flex-grow-1">
                  <small class="fw-bold">{{ performer.name }}</small>
                  <br>
                  <small class="text-muted">Avg Score: {{ performer.avgScore.toFixed(1) }}%</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Subject-wise Statistics -->
      <div class="row mt-4">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">📚 Subject-wise Statistics</h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div v-for="subject in stats.subjectStats" :key="subject.id" class="col-md-4 mb-3">
                  <div class="card border-primary">
                    <div class="card-header bg-primary text-white">
                      <h6 class="mb-0">{{ subject.name }}</h6>
                    </div>
                    <div class="card-body">
                      <div class="row text-center">
                        <div class="col-6">
                          <h5 class="text-primary">{{ subject.chapters }}</h5>
                          <small class="text-muted">Chapters</small>
                        </div>
                        <div class="col-6">
                          <h5 class="text-success">{{ subject.quizzes }}</h5>
                          <small class="text-muted">Quizzes</small>
                        </div>
                      </div>
                      <hr>
                      <div class="text-center">
                        <h6 class="text-info">{{ subject.avgScore.toFixed(1) }}%</h6>
                        <small class="text-muted">Average Score</small>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getAdminStats } from '@/api.js'

export default {
  name: 'AdminStats',
  data() {
    return {
      loading: true,
      stats: {
        totalUsers: 0,
        totalQuizzes: 0,
        totalAttempts: 0,
        totalQuestions: 0,
        quizStats: [],
        recentActivity: [],
        topPerformers: [],
        subjectStats: []
      }
    }
  },
  async mounted() {
    await this.loadStats()
  },
  methods: {
    async loadStats() {
      try {
        this.loading = true
        const response = await getAdminStats()
        this.stats = response.data
        this.loading = false
      } catch (error) {
        console.error('Error loading stats:', error)
        this.loading = false
        this.showNotification('Failed to load statistics', 'error')
      }
    },
    
    async refreshStats() {
      await this.loadStats()
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString()
    },
    
    formatDateTime(dateString) {
      return new Date(dateString).toLocaleString()
    },
    
    getScoreBadgeClass(score) {
      if (score >= 80) return 'bg-success'
      if (score >= 60) return 'bg-warning'
      return 'bg-danger'
    },
    
    getCompletionBadgeClass(rate) {
      if (rate >= 80) return 'bg-success'
      if (rate >= 50) return 'bg-warning'
      return 'bg-danger'
    },
    
    getRankBadgeClass(rank) {
      if (rank === 1) return 'bg-warning'
      if (rank === 2) return 'bg-secondary'
      if (rank === 3) return 'bg-danger'
      return 'bg-primary'
    },
    
    showNotification(message, type = 'info') {
      alert(`${type.toUpperCase()}: ${message}`)
    }
  }
}
</script>

<style scoped>
.card {
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.progress {
  border-radius: 10px;
}

.table th {
  border-top: none;
}

.avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rank {
  width: 30px;
  text-align: center;
}

.badge {
  font-size: 0.8em;
}
</style> 