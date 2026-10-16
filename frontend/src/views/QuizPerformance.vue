<template>
  <div>
    <h3 style="text-align: center;">📈 Quiz Performance Over Time</h3>
    <canvas id="quizChart"></canvas>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';
import { getQuizStats } from '../api';

export default {
  name: 'QuizPerformance',
  data() {
    return {
      quizLabels: [],
      quizScores: []
    };
  },
  async mounted() {
    try {
      const response = await getQuizStats();
      this.quizLabels = response.data.quiz_labels;
      this.quizScores = response.data.quiz_scores;
      this.renderChart();
    } catch (error) {
      console.error('Failed to fetch quiz stats:', error);
    }
  },
  methods: {
    renderChart() {
      const ctx = document.getElementById('quizChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: this.quizLabels,
          datasets: [{
            label: 'Quiz Scores',
            data: this.quizScores,
            backgroundColor: 'rgba(54, 162, 235, 0.4)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            fill: true
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }
  }
};
</script>

<style scoped>
.quiz-performance-container { max-width: 700px; margin: 0 auto; padding: 2rem; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: center; }
</style> 