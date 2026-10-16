<template>
  <div class="container mt-5">
    <h2 class="text-center fw-bold text-dark">🏆 Leaderboard</h2>
    <div class="card shadow-lg border-0 rounded-4 p-4">
      <table class="table table-striped text-center">
        <thead class="table-dark">
          <tr>
            <th>Rank</th>
            <th>Username</th>
            <th>Average Score (%)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, idx) in topUsers" :key="user.id">
            <td class="fw-bold">#{{ idx + 1 }}</td>
            <td>{{ user.full_name }}</td>
            <td class="text-success fw-bold">{{ user.avg_score.toFixed(2) }}%</td>
          </tr>
          <tr v-if="!topUsers.length">
            <td colspan="3" class="text-center text-muted">No scores available yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { getLeaderboard } from '../api';

export default {
  name: 'LeaderboardPage',
  data() {
    return {
      topUsers: []
    };
  },
  async mounted() {
    try {
      const response = await getLeaderboard();
      this.topUsers = response.data;
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      // Optionally, show an error message to the user
    }
  }
};
</script>

<style scoped>
.card {
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
.table {
  border-radius: 10px;
  overflow: hidden;
}
.fw-bold {
  font-size: 18px;
}
</style> 