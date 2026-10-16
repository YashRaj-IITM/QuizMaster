<template>
  <div class="container mt-5">
    <h2 class="text-center">User List</h2>
    <table class="table table-bordered mt-3">
      <thead>
        <tr>
          <th>ID</th>
          <th>Full Name</th>
          <th>Email</th>
          <th>Qualification</th>
          <th>Date of Birth</th>
          <th>Admin Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.full_name }}</td>
          <td>{{ user.email }}</td>
          <td>{{ user.qualification || 'N/A' }}</td>
          <td>{{ user.dob ? formatDate(user.dob) : 'N/A' }}</td>
          <td>{{ user.is_admin ? 'Admin' : 'User' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { getUsers } from '../api';

export default {
  name: 'UserList',
  data() {
    return {
      users: []
    };
  },
  methods: {
    formatDate(date) {
      const d = new Date(date);
      return d.toISOString().slice(0, 10);
    }
  },
  async mounted() {
    try {
      const response = await getUsers();
      this.users = response.data;
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  }
};
</script>

<style scoped>
.user-list-container { max-width: 700px; margin: 0 auto; padding: 2rem; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: center; }
</style> 