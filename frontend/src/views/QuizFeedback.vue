<template>
  <div class="container mt-4">
    <div v-if="notification" :class="['alert', notificationType === 'success' ? 'alert-success' : 'alert-danger']" role="alert" style="position:sticky;top:0;z-index:1000;">
      {{ notification }}
    </div>
    <h2 class="text-center">Quiz Feedback</h2>
    <div class="alert alert-info text-center">
      Your Score: <strong>{{ score.toFixed(2) }}%</strong>
    </div>
    <div class="card p-4 shadow-lg border-0 rounded-3">
      <div v-for="(answer, idx) in userAnswersArray" :key="idx" class="mb-4">
        <h5>{{ idx + 1 }}. {{ answer.question }}</h5>
        <ul class="list-group">
          <li v-for="(optionText, optionNumber) in answer.options" :key="optionNumber"
              class="list-group-item"
              :class="{
                'list-group-item-success': optionNumber == answer.correct_option,
                'list-group-item-danger': answer.selected_option !== null && answer.selected_option == optionNumber && answer.selected_option != answer.correct_option
              }">
            <span v-if="optionNumber == answer.correct_option">✅ Correct Answer </span>
            <span v-else-if="answer.selected_option !== null && answer.selected_option == optionNumber && answer.selected_option != answer.correct_option">❌ Your Answer </span>
            <span v-else>⚪ </span>
            {{ optionText }}
          </li>
        </ul>
      </div>
    </div>
    <div class="text-center mt-4">
      <router-link to="/dashboard" class="btn btn-primary">Return to Dashboard</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuizFeedback',
  data() {
    return {
      score: 0,
      userAnswers: {},
      notification: '',
      notificationType: '',
      notificationTimeout: null
    };
  },
  computed: {
    userAnswersArray() {
      // Convert userAnswers object to array for v-for
      return Object.values(this.userAnswers);
    }
  },
  mounted() {
    // Get feedback data from router state (passed from QuizAttempt)
    if (this.$router && this.$router.options && this.$router.options.history && this.$router.options.history.state) {
      const state = this.$router.options.history.state;
      if (state && state.score !== undefined && state.userAnswers) {
        this.score = state.score;
        this.userAnswers = state.userAnswers;
        return;
      }
    }
    // If not available, fallback to default (could fetch from backend if needed)
    this.showNotification('No feedback data found.', 'error');
  },
  methods: {
    showNotification(message, type = 'error') {
      this.notification = message;
      this.notificationType = type;
      if (this.notificationTimeout) clearTimeout(this.notificationTimeout);
      this.notificationTimeout = setTimeout(() => {
        this.notification = '';
        this.notificationType = '';
      }, 3000);
    }
  }
};
</script>

<style scoped>
.list-group-item {
  transition: background 0.3s ease-in-out;
}
.list-group-item-success {
  background-color: #d4edda !important;
}
.list-group-item-danger {
  background-color: #f8d7da !important;
}
</style> 