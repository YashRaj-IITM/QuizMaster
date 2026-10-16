<template>
  <div class="container mt-4">
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading quiz...</p>
    </div>

    <div v-else-if="quiz && currentQuestion && totalQuestions > 0" class="quiz-container">
      <!-- Quiz Header -->
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h4 class="mb-0">{{ quiz.remarks }}</h4>
          <small>Question {{ currentQuestionIndex + 1 }} of {{ totalQuestions }}</small>
          <span class="badge float-end fs-6" :class="remainingSeconds <= 60 ? 'bg-danger' : 'bg-light text-dark'">
            ⏱ {{ timeDisplay }}
          </span>
        </div>
      </div>

      <!-- Question Card -->
      <div class="card">
        <div class="card-body">
          <h5 class="card-title mb-4">{{ currentQuestion.question_statement }}</h5>
          
          <!-- Options -->
          <div class="options-container">
            <div 
              v-for="(option, index) in options" 
              :key="index"
              class="option-item mb-3"
              :class="{ 'selected': selectedAnswer === (index + 1) }"
              @click="selectAnswer(index + 1)"
            >
              <div class="option-content">
                <span class="option-label">{{ String.fromCharCode(65 + index) }}.</span>
                <span class="option-text">{{ option }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation Buttons -->
      <div class="d-flex justify-content-between mt-4">
        <button 
          class="btn btn-secondary" 
          @click="previousQuestion"
          :disabled="currentQuestionIndex === 0"
        >
          <i class="fas fa-arrow-left"></i> Previous
        </button>

        <div class="d-flex gap-2">
          <button 
            v-if="currentQuestionIndex < totalQuestions - 1"
            class="btn btn-primary" 
            @click="nextQuestion"
            :disabled="!selectedAnswer"
          >
            Next <i class="fas fa-arrow-right"></i>
          </button>
          
          <button 
            v-else
            class="btn btn-success" 
            @click="submitQuiz()"
            :disabled="!selectedAnswer"
          >
            Submit Quiz <i class="fas fa-check"></i>
          </button>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="progress mt-3" style="height: 8px;">
        <div 
          class="progress-bar bg-success" 
          :style="{ width: progressPercentage + '%' }"
        ></div>
      </div>
      <small class="text-muted">{{ answeredQuestions }} of {{ totalQuestions }} questions answered</small>
    </div>

    <div v-else class="text-center">
      <div v-if="quiz && totalQuestions === 0" class="alert alert-warning">
        <h4>No Questions Available</h4>
        <p>This quiz doesn't have any questions yet. Please contact your administrator.</p>
        <router-link to="/dashboard" class="btn btn-primary">Return to Dashboard</router-link>
      </div>
      <div v-else class="alert alert-danger">
        <h4>Failed to Load Quiz</h4>
        <p>Unable to load quiz data. Please try again or contact support.</p>
        <router-link to="/dashboard" class="btn btn-primary">Return to Dashboard</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { getQuiz, submitQuiz } from '@/api.js'

export default {
  name: 'QuizAttempt',
  data() {
    return {
      loading: true,
      quiz: null,
      currentQuestion: null,
      currentQuestionIndex: 0,
      totalQuestions: 0,
      selectedAnswer: null,
      userAnswers: {},
      answeredQuestions: 0,
      remainingSeconds: 0,
      timerId: null,
      submitting: false
    }
  },
  computed: {
    options() {
      if (!this.currentQuestion) return []
      return [
        this.currentQuestion.option1,
        this.currentQuestion.option2,
        this.currentQuestion.option3,
        this.currentQuestion.option4
      ]
    },
    timeDisplay() {
      const s = Math.max(0, this.remainingSeconds)
      const m = Math.floor(s / 60)
      return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
    },
    progressPercentage() {
      return this.totalQuestions > 0 ? (this.answeredQuestions / this.totalQuestions) * 100 : 0
    }
  },
  async mounted() {
    await this.loadQuiz()
  },
  beforeUnmount() {
    clearInterval(this.timerId)
  },
  methods: {
    async loadQuiz() {
      try {
        this.loading = true
        const quizId = this.$route.params.quizId
        console.log('Loading quiz with ID:', quizId, 'question index:', this.currentQuestionIndex)
        
        const response = await getQuiz(quizId, this.currentQuestionIndex)
        console.log('Quiz response:', response)
        
        if (!response.data || !response.data.quiz || !response.data.question) {
          throw new Error('Invalid response structure from server')
        }
        
        this.quiz = response.data.quiz
        this.currentQuestion = response.data.question
        this.currentQuestionIndex = response.data.current_question_index
        this.totalQuestions = response.data.total_questions
        this.startTimer(response.data.remaining_seconds)
        
        // Load saved answer for current question
        this.selectedAnswer = this.userAnswers[this.currentQuestion.id] || null
        
        this.loading = false
      } catch (error) {
        console.error('Error loading quiz:', error)
        console.error('Error details:', error.response?.data || error.message)
        this.loading = false
        
        let errorMessage = 'Failed to load quiz data'
        if (error.response?.status === 404) {
          errorMessage = 'Quiz not found. Please check the quiz ID.'
        } else if (error.response?.status === 401) {
          errorMessage = 'Please log in to access this quiz.'
        } else if (error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.message) {
          errorMessage = error.message
        }
        
        this.showNotification(errorMessage, 'error')
      }
    },
    
    startTimer(seconds) {
      // The server owns the clock: we only count down from what it reports
      this.remainingSeconds = seconds
      clearInterval(this.timerId)
      this.timerId = setInterval(() => {
        this.remainingSeconds -= 1
        if (this.remainingSeconds <= 0) {
          clearInterval(this.timerId)
          this.submitQuiz(true)
        }
      }, 1000)
    },

    async loadQuestion(questionIndex) {
      try {
        this.loading = true
        const quizId = this.$route.params.quizId
        const response = await getQuiz(quizId, questionIndex)
        
        if (!response.data || !response.data.question) {
          throw new Error('Invalid response structure from server')
        }
        
        this.currentQuestion = response.data.question
        this.currentQuestionIndex = response.data.current_question_index
        this.startTimer(response.data.remaining_seconds)
        
        // Load saved answer for current question
        this.selectedAnswer = this.userAnswers[this.currentQuestion.id] || null
        
        this.loading = false
      } catch (error) {
        console.error('Error loading question:', error)
        this.loading = false
        
        let errorMessage = 'Failed to load question'
        if (error.response?.status === 404) {
          errorMessage = 'Question not found.'
        } else if (error.response?.status === 400) {
          errorMessage = 'Question index out of range.'
        } else if (error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.message) {
          errorMessage = error.message
        }
        
        this.showNotification(errorMessage, 'error')
      }
    },
    
    selectAnswer(optionNumber) {
      this.selectedAnswer = optionNumber
      this.userAnswers[this.currentQuestion.id] = optionNumber
      
      // Update answered questions count
      this.updateAnsweredCount()
    },
    
    updateAnsweredCount() {
      this.answeredQuestions = Object.keys(this.userAnswers).length
    },
    
    async nextQuestion() {
      if (this.currentQuestionIndex < this.totalQuestions - 1) {
        await this.loadQuestion(this.currentQuestionIndex + 1)
      }
    },
    
    async previousQuestion() {
      if (this.currentQuestionIndex > 0) {
        await this.loadQuestion(this.currentQuestionIndex - 1)
      }
    },
    
    async submitQuiz(timedOut = false) {
      if (this.submitting) return
      this.submitting = true
      clearInterval(this.timerId)
      if (timedOut === true) this.showNotification('Time is up! Submitting your answers.', 'info')
      try {
        const quizId = this.$route.params.quizId
        const response = await submitQuiz(quizId, this.userAnswers)
        
        // Navigate to feedback page with results
        this.$router.push({
          name: 'QuizFeedback',
          state: {
            score: response.data.score,
            userAnswers: response.data.user_answers,
            totalQuestions: this.totalQuestions
          }
        })
      } catch (error) {
        console.error('Error submitting quiz:', error)
        this.showNotification(error.response?.data?.error || 'Failed to submit quiz', 'error')
        if (error.response && [403, 409].includes(error.response.status)) this.$router.push('/dashboard')
        else this.submitting = false
      }
    },
    
    showNotification(message, type = 'info') {
      // You can implement a toast notification system here
      alert(`${type.toUpperCase()}: ${message}`)
    }
  }
}
</script>

<style scoped>
.quiz-container {
  max-width: 800px;
  margin: 0 auto;
}

.option-item {
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

.option-item:hover {
  border-color: #007bff;
  background-color: #e3f2fd;
}

.option-item.selected {
  border-color: #007bff;
  background-color: #007bff;
  color: white;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.option-label {
  font-weight: bold;
  min-width: 30px;
}

.option-text {
  flex: 1;
}

.progress {
  border-radius: 10px;
}

.card-header {
  border-radius: 8px 8px 0 0 !important;
}

.btn {
  border-radius: 6px;
  padding: 8px 16px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style> 