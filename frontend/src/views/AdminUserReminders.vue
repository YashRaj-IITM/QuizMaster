<template>
  <div class="container mt-4">
    <!-- Header -->
    <div class="row mb-4">
      <div class="col-12">
        <h2 class="text-center mb-3">📧 User Reminders</h2>
        <p class="text-center text-muted">Send reminders to users who haven't completed their quizzes</p>
      </div>
    </div>

    <!-- Notification -->
    <div v-if="notification" :class="['alert', notificationType === 'success' ? 'alert-success' : 'alert-danger']" role="alert">
      {{ notification }}
    </div>
    
         <!-- User Filter -->
     <div class="row mb-4">
              <div class="col-md-6">
         <span class="text-muted">{{ users.length }} users found</span>
              </div>
              <div class="col-md-6 text-end">
         <div class="form-check form-check-inline">
           <input class="form-check-input" type="checkbox" id="pendingOnly" v-model="pendingOnly">
           <label class="form-check-label" for="pendingOnly">Pending quizzes only</label>
                </div>
              </div>
            </div>
            
    <!-- Send Reminders -->
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">📤 Send Reminders</h5>
      </div>
              <div class="card-body">
                <div class="row">
          <div class="col-md-6">
                    <label class="form-label">Reminder Time</label>
                    <input type="datetime-local" v-model="reminderTime" class="form-control" required>
                  </div>
          <div class="col-md-6">
                    <label class="form-label">Subject</label>
            <input type="text" v-model="reminderSubject" class="form-control" placeholder="Quiz Reminder">
          </div>
                  </div>
        <div class="row mt-3">
          <div class="col-12">
                    <label class="form-label">Message</label>
            <textarea v-model="reminderBody" class="form-control" rows="2" placeholder="You have pending quizzes to complete..."></textarea>
          </div>
        </div>
        <div class="row mt-3">
          <div class="col-12">
            <button @click="sendReminders" class="btn btn-primary">
              <i class="fas fa-paper-plane"></i> Send Reminders
            </button>
                  </div>
                </div>
              </div>
            </div>
            
    <!-- Monthly Report Scheduling -->
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">📊 Monthly Report Scheduling</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <label class="form-label">Day of Month</label>
            <select v-model="reportDay" class="form-select">
              <option value="1">1st</option>
              <option value="2">2nd</option>
              <option value="3">3rd</option>
              <option value="4">4th</option>
              <option value="5">5th</option>
              <option value="6">6th</option>
              <option value="7">7th</option>
              <option value="8">8th</option>
              <option value="9">9th</option>
              <option value="10">10th</option>
              <option value="11">11th</option>
              <option value="12">12th</option>
              <option value="13">13th</option>
              <option value="14">14th</option>
              <option value="15">15th</option>
              <option value="16">16th</option>
              <option value="17">17th</option>
              <option value="18">18th</option>
              <option value="19">19th</option>
              <option value="20">20th</option>
              <option value="21">21st</option>
              <option value="22">22nd</option>
              <option value="23">23rd</option>
              <option value="24">24th</option>
              <option value="25">25th</option>
              <option value="26">26th</option>
              <option value="27">27th</option>
              <option value="28">28th</option>
              <option value="29">29th</option>
              <option value="30">30th</option>
              <option value="31">31st</option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label">Time</label>
            <input type="time" v-model="reportTime" class="form-control" required>
          </div>
        </div>
                   <div class="row mt-3">
             <div class="col-md-12">
               <div class="alert alert-info">
                 <i class="fas fa-info-circle"></i>
                 <strong>Note:</strong> Monthly reports will be automatically sent to all registered users ({{ users.length }} users).
                  </div>
                  </div>
                  </div>
        <div class="row mt-3">
                       <div class="col-12">
               <button @click="scheduleMonthlyReport" class="btn btn-info me-2">
                 <i class="fas fa-calendar-plus"></i> Schedule Monthly Report
               </button>
                  </div>
                </div>
              </div>
            </div>
            


    <!-- CSV Export -->
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">📊 CSV Export</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <div class="form-check mb-3">
              <input class="form-check-input" type="checkbox" id="exportAllUsers" v-model="exportAllUsersOption">
              <label class="form-check-label" for="exportAllUsers">
                Export all users data ({{ users.length }} users)
              </label>
            </div>
            <button @click="exportAllUsers" class="btn btn-success" :disabled="exporting">
              <i class="fas fa-download"></i> Download CSV
            </button>
          </div>
          <div class="col-md-6">
            <div class="form-check mb-3">
              <input class="form-check-input" type="checkbox" id="sendToAllUsers" v-model="sendToAllUsersOption">
              <label class="form-check-label" for="sendToAllUsers">
                Send CSV to all users via email ({{ users.length }} users)
              </label>
            </div>
            <button @click="sendCSVToAllUsers" class="btn btn-info" :disabled="exporting">
              <i class="fas fa-envelope"></i> Send via Email
            </button>
          </div>
            </div>
            
        <!-- Export Progress -->
        <div v-if="exporting" class="mt-3">
          <div class="progress">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 :style="{ width: exportProgress + '%' }" 
                 role="progressbar">
              {{ exportProgress }}%
            </div>
          </div>
          <small class="text-muted">Processing... Please wait.</small>
        </div>
      </div>
    </div>


  </div>
</template>

<script>
import { getInactiveUsers, scheduleBulkReminders, scheduleMonthlyReport as scheduleMonthlyReportAPI, exportCSVEmail } from '../api';

export default {
  name: 'AdminUserReminders',
  data() {
    return {
      users: [],
      pendingOnly: false,
      reminderTime: '',
      reminderSubject: 'Quiz Reminder',
      reminderBody: 'You have pending quizzes to complete. Please visit the platform and attempt them.',
      notification: '',
      notificationType: '',
      
      // Monthly Report Scheduling
      reportDay: '1',
      reportTime: '09:00',
      
      // CSV Export
      exporting: false,
      exportProgress: 0,
      exportAllUsersOption: true,
      sendToAllUsersOption: false,


    };
  },
  methods: {
    showNotification(message, type = 'success') {
      this.notification = message;
      this.notificationType = type;
      setTimeout(() => {
        this.notification = '';
        this.notificationType = '';
      }, 3000);
    },

    async loadUsers() {
      try {
        const response = await getInactiveUsers(this.pendingOnly);
        this.users = response.data;
      } catch (error) {
        this.showNotification('Failed to load users.', 'error');
      }
    },

    async sendReminders() {
      if (!this.reminderTime) {
        this.showNotification('Please select a reminder time.', 'error');
        return;
      }

      try {
        const localDate = new Date(this.reminderTime);
        const allUserIds = this.users.map(user => user.id);
        const response = await scheduleBulkReminders(
          allUserIds, 
          localDate.toISOString(), 
          this.reminderSubject, 
          this.reminderBody
        );
        
        this.showNotification(`Reminders sent to ${response.data.scheduled_count} users!`);
        this.reminderTime = '';
        this.reminderSubject = 'Quiz Reminder';
        this.reminderBody = 'You have pending quizzes to complete. Please visit the platform and attempt them.';
        await this.loadUsers();
      } catch (error) {
        this.showNotification('Failed to send reminders.', 'error');
      }
    },

    // Monthly Report Scheduling
    async scheduleMonthlyReport() {
      if (!this.reportTime) {
        this.showNotification('Please select a time for the report.', 'error');
        return;
      }

      if (this.users.length === 0) {
        this.showNotification('No users found. Please load users first.', 'error');
        return;
      }
      
      try {
        // Generate cron expression from user-friendly inputs
        const [hours, minutes] = this.reportTime.split(':');
        const cronExpression = `${minutes} ${hours} ${this.reportDay} * *`;
        
        // Get all user emails automatically
        const allUserEmails = this.users.map(user => user.email).join(',');
        
        console.log('Scheduling report with:', {
          cronExpression,
          userCount: this.users.length,
          emails: allUserEmails.substring(0, 100) + '...'
        });
        
        // Call the backend API to schedule the report with Celery Beat
        const response = await scheduleMonthlyReportAPI(
          cronExpression,
          allUserEmails
        );
        
        console.log('API Response:', response.data);
        
        if (response.data.success) {
          this.showNotification(`Monthly report scheduled for ${this.getDayWithSuffix(this.reportDay)} at ${this.reportTime}!`);
          
          // Reset form
          this.reportDay = '1';
          this.reportTime = '09:00';
        } else {
          this.showNotification('Failed to schedule report: ' + (response.data.error || 'Unknown error'), 'error');
        }
      } catch (error) {
        console.error('Schedule report error:', error);
        this.showNotification('Failed to schedule report: ' + (error.response?.data?.error || error.message), 'error');
      }
    },

    getDayWithSuffix(day) {
      const dayNum = parseInt(day);
      if (dayNum >= 11 && dayNum <= 13) {
        return dayNum + 'th';
      }
      switch (dayNum % 10) {
        case 1: return dayNum + 'st';
        case 2: return dayNum + 'nd';
        case 3: return dayNum + 'rd';
        default: return dayNum + 'th';
      }
    },







    async exportAllUsers() {
      await this.startExport('all-users');
    },

    async sendCSVToAllUsers() {
      this.exporting = true;
      this.exportProgress = 0;

      try {
        // Simulate progress
        const progressInterval = setInterval(() => {
          this.exportProgress += 20;
          if (this.exportProgress >= 80) {
            clearInterval(progressInterval);
          }
        }, 300);

        // Call the real API
        const response = await exportCSVEmail();
        
        clearInterval(progressInterval);
        this.exportProgress = 100;
        
        if (response.data.success) {
          this.showNotification('CSV export started - it will be emailed to your admin address shortly.');
        } else {
          this.showNotification('Failed to send CSV: ' + (response.data.error || 'Unknown error'), 'error');
        }

      } catch (error) {
        console.error('CSV export error:', error);
        this.showNotification('Failed to send CSV: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.exporting = false;
        this.exportProgress = 0;
      }
    },

    async startExport(type) {
      this.exporting = true;
      this.exportProgress = 0;

      try {
        // Simulate export progress
        const interval = setInterval(() => {
          this.exportProgress += 10;
          if (this.exportProgress >= 100) {
            clearInterval(interval);
            this.exporting = false;
            this.exportProgress = 0;
            
            if (type === 'all-users') {
              this.showNotification('Export completed! CSV file downloaded.');
              this.downloadCSV();
            }
          }
        }, 200);

      } catch (error) {
        this.exporting = false;
        this.exportProgress = 0;
        this.showNotification('Export failed.', 'error');
      }
    },

    downloadCSV() {
      const csvContent = this.generateAllUsersCSV();
      
      // Create and download file
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `all-users-data-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    },

    generateAllUsersCSV() {
      const headers = [
        'User ID',
        'Full Name',
        'Email',
        'Quizzes Taken',
        'Average Score',
        'Total Score',
        'Last Activity',
        'Status',
        'Pending Quizzes'
      ];

      const rows = this.users.map(user => [
        user.id,
        user.full_name,
        user.email,
        user.attempted_quizzes || 0,
        '75%', // Mock data
        '150', // Mock data
        this.formatDate(user.last_activity),
        user.is_inactive ? 'Inactive' : 'Active',
        user.pending_quizzes || 0
      ]);

      return [headers, ...rows].map(row => row.join(',')).join('\n');
    },



    formatDate(dateString) {
      if (!dateString) return 'Never';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },


  },

  async mounted() {
    await this.loadUsers();
  },

  watch: {
    pendingOnly() {
      this.loadUsers();
    }
  }
};
</script>

<style scoped>
.card {
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  border-radius: 12px 12px 0 0 !important;
}

.table th {
  border-top: none;
  font-weight: 600;
  color: #495057;
}

.table td {
  vertical-align: middle;
}

.badge {
  font-size: 0.75em;
  padding: 0.5em 0.75em;
}

.btn {
  border-radius: 8px;
  padding: 0.5rem 1rem;
}

.form-control, .form-select {
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.form-control:focus, .form-select:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.table-hover tbody tr:hover {
  background-color: #f8f9fa;
}

.progress {
  height: 20px;
  border-radius: 10px;
}

.card.bg-primary, .card.bg-success, .card.bg-info, .card.bg-warning {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style> 