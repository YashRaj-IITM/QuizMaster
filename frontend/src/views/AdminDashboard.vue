<template>
  <div class="container mt-5">
    <div v-if="notification" :class="['alert', notificationType === 'success' ? 'alert-success' : 'alert-danger']" role="alert" style="position:sticky;top:0;z-index:1000;">
      {{ notification }}
    </div>
    <h2 class="fw-medium text-center text-dark mb-4">Admin Dashboard</h2>
    <div class="row g-4">
      <!-- Quick Actions -->
      <div class="col-12 mb-3">
        <div class="d-flex justify-content-end">
          <router-link to="/admin/user-reminders" class="btn btn-info me-2">
            <i class="fas fa-bell"></i> Manage User Reminders
          </router-link>
          <router-link to="/admin/stats" class="btn btn-secondary">
            <i class="fas fa-chart-bar"></i> View Statistics
          </router-link>
        </div>
      </div>
      
      <!-- Subjects Section -->
      <div class="col-md-3 col-sm-6">
        <div class="card border-0 shadow rounded-4 mb-4">
          <div class="card-header bg-gradient-primary text-dark text-center fw-bold rounded-top-4">📚 Subjects</div>
          <div class="card-body">
            <form class="d-flex mb-3" @submit.prevent="addSubject">
              <input type="text" v-model="newSubjectName" class="form-control form-control-sm rounded-pill shadow-sm me-2" placeholder="Enter subject" required>
              <button type="submit" class="btn btn-primary btn-sm rounded-pill px-3" :disabled="!newSubjectName">Add</button>
            </form>
            <div class="list-group">
              <div v-for="subject in subjects" :key="subject.id" class="d-flex justify-content-between align-items-center list-group-item list-group-item-action"
                :class="{ 'active-admin': selectedSubject && selectedSubject.id === subject.id }"
                @mouseover="hoveredSubject = subject.id" @mouseleave="hoveredSubject = null"
                :style="hoveredSubject === subject.id ? 'background: #f0f8ff;' : ''">
                <template v-if="editingSubjectId === subject.id">
                  <input v-model="editingSubjectName" class="form-control form-control-sm me-2" style="max-width: 120px;" autofocus />
                  <button class="btn btn-sm btn-success me-2" @click="saveSubjectEdit(subject.id)">✅</button>
                  <button class="btn btn-sm btn-secondary" @click="cancelSubjectEdit">⛔</button>
                </template>
                <template v-else>
                  <a href="#" class="text-decoration-none flex-grow-1" @click.prevent="selectSubject(subject)">{{ subject.name }}</a>
                  <div class="d-flex">
                    <button class="btn btn-sm btn-outline-secondary me-2" @click="startSubjectEdit(subject)">✏️</button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteSubject(subject.id)">❌</button>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- Chapters Section -->
      <div class="col-md-3 col-sm-6">
        <div class="card border-0 shadow rounded-4 mb-4">
          <div class="card-header bg-gradient-secondary text-dark text-center fw-bold rounded-top-4">📖 Chapters</div>
          <div class="card-body">
            <form v-if="selectedSubject" class="d-flex mb-3" @submit.prevent="addChapter">
              <input type="text" v-model="newChapterName" class="form-control form-control-sm rounded-pill shadow-sm me-2" placeholder="New Chapter" required>
              <button type="submit" class="btn btn-secondary btn-sm rounded-pill px-3" :disabled="!newChapterName">Add</button>
            </form>
            <div class="list-group">
              <div v-for="chapter in chapters" :key="chapter.id" class="d-flex justify-content-between align-items-center list-group-item list-group-item-action"
                :class="{ 'active-admin': selectedChapter && selectedChapter.id === chapter.id }"
                @mouseover="hoveredChapter = chapter.id" @mouseleave="hoveredChapter = null"
                :style="hoveredChapter === chapter.id ? 'background: #f0f8ff;' : ''">
                <template v-if="editingChapterId === chapter.id">
                  <input v-model="editingChapterName" class="form-control form-control-sm me-2" style="max-width: 120px;" autofocus />
                  <button class="btn btn-sm btn-success me-2" @click="saveChapterEdit(chapter.id)">✅</button>
                  <button class="btn btn-sm btn-secondary" @click="cancelChapterEdit">⛔</button>
                </template>
                <template v-else>
                  <a href="#" class="text-decoration-none flex-grow-1" @click.prevent="selectChapter(chapter)">{{ chapter.name }}</a>
                  <div class="d-flex">
                    <button class="btn btn-sm btn-outline-secondary me-2" @click="startChapterEdit(chapter)">✏️</button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteChapter(chapter.id)">❌</button>
                  </div>
                </template>
              </div>
            </div>
            <p v-if="!selectedSubject" class="text-muted text-center mt-3">Select a subject to view available chapters.</p>
          </div>
        </div>
      </div>
      <!-- Quizzes Section -->
      <div class="col-md-3 col-sm-6">
        <div class="card border-0 shadow rounded-4 mb-4">
          <div class="card-header bg-gradient-warning text-dark text-center fw-bold rounded-top-4">📝 Quizzes</div>
          <div class="card-body">
            <form v-if="selectedChapter" class="mb-3" @submit.prevent="addQuiz">
              <input type="date" v-model="newQuizDate" class="form-control" required>
              <input type="text" v-model="newQuizRemarks" class="form-control mt-2" placeholder="Name" required>
              <input type="text" v-model="newQuizDuration" class="form-control mt-2" placeholder="Duration HH:MM (default 00:30)" pattern="[0-9]{1,2}:[0-5][0-9]">
              <button type="submit" class="btn btn-warning w-100 mt-2" :disabled="!newQuizDate || !newQuizRemarks">Add Quiz</button>
            </form>
            <div class="list-group">
              <div v-for="quiz in quizzes" :key="quiz.id" class="d-flex justify-content-between align-items-center list-group-item list-group-item-action"
                :class="{ 'active-admin': selectedQuiz && selectedQuiz.id === quiz.id }"
                @mouseover="hoveredQuiz = quiz.id" @mouseleave="hoveredQuiz = null"
                :style="hoveredQuiz === quiz.id ? 'background: #f0f8ff;' : ''">
                <template v-if="editingQuizId === quiz.id">
                  <input type="date" v-model="editingQuizDate" class="form-control form-control-sm me-2" style="max-width: 120px;" autofocus />
                  <input type="text" v-model="editingQuizRemarks" class="form-control form-control-sm me-2" style="max-width: 120px;" placeholder="Remarks" />
                  <button class="btn btn-sm btn-success me-2" @click="saveQuizEdit(quiz.id)">✅</button>
                  <button class="btn btn-sm btn-secondary" @click="cancelQuizEdit">⛔</button>
                </template>
                <template v-else>
                  <a href="#" class="text-decoration-none flex-grow-1" @click.prevent="selectQuiz(quiz)">{{ quiz.remarks }}</a>
                  <div class="d-flex">
                    <button class="btn btn-sm btn-outline-secondary me-2" @click="startQuizEdit(quiz)">✏️</button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteQuiz(quiz.id)">❌</button>
                  </div>
                </template>
              </div>
            </div>
            <p v-if="!selectedChapter" class="text-muted text-center mt-3">Select a chapter to see available quizzes.</p>
          </div>
        </div>
      </div>
      <!-- Questions Section -->
      <div class="col-md-3 col-sm-6">
        <div class="card border-0 shadow rounded-4 mb-4">
          <div class="card-header bg-gradient-success text-dark text-center fw-bold rounded-top-4">🧠 Questions</div>
          <div class="card-body">
            <form v-if="selectedQuiz" class="mb-3" @submit.prevent="addQuestion">
              <input type="text" v-model="newQuestionStatement" class="form-control mb-2" placeholder="Enter question" required>
              <input type="text" v-model="newOption1" class="form-control mb-2" placeholder="Option 1" required>
              <input type="text" v-model="newOption2" class="form-control mb-2" placeholder="Option 2" required>
              <input type="text" v-model="newOption3" class="form-control mb-2" placeholder="Option 3" required>
              <input type="text" v-model="newOption4" class="form-control mb-2" placeholder="Option 4" required>
              <label class="mt-2">Correct Option:</label>
              <select v-model="newCorrectOption" class="form-select mt-1 mb-2" required>
                <option value="1">Option 1</option>
                <option value="2">Option 2</option>
                <option value="3">Option 3</option>
                <option value="4">Option 4</option>
              </select>
              <button type="submit" class="btn btn-success w-100 mt-2" :disabled="!newQuestionStatement || !newOption1 || !newOption2 || !newOption3 || !newOption4">Add Question</button>
            </form>
            <ul class="list-group">
              <li v-for="(question, idx) in questions" :key="question.id" class="list-group-item list-group-item-action"
                :class="{ 'active-admin': editingQuestionId === question.id }"
                @mouseover="hoveredQuestion = question.id" @mouseleave="hoveredQuestion = null"
                :style="hoveredQuestion === question.id ? 'background: #f0f8ff;' : ''">
                <template v-if="editingQuestionId === question.id">
                  <input v-model="editingQuestionStatement" class="form-control form-control-sm mb-1" placeholder="Question" autofocus />
                  <input v-model="editingOption1" class="form-control form-control-sm mb-1" placeholder="Option 1" />
                  <input v-model="editingOption2" class="form-control form-control-sm mb-1" placeholder="Option 2" />
                  <input v-model="editingOption3" class="form-control form-control-sm mb-1" placeholder="Option 3" />
                  <input v-model="editingOption4" class="form-control form-control-sm mb-1" placeholder="Option 4" />
                  <select v-model="editingCorrectOption" class="form-select form-select-sm mb-1">
                    <option value="1">Option 1</option>
                    <option value="2">Option 2</option>
                    <option value="3">Option 3</option>
                    <option value="4">Option 4</option>
                  </select>
                  <button class="btn btn-sm btn-success me-2" @click="saveQuestionEdit(question.id)">✅</button>
                  <button class="btn btn-sm btn-secondary" @click="cancelQuestionEdit">⛔</button>
                </template>
                <template v-else>
                  <strong>Q{{ idx + 1 }}:</strong> {{ question.question_statement }}
                  <ul class="mt-1">
                    <li v-for="i in 4" :key="i" :class="{ 'text-success fw-bold': question.correct_option == i }">
                      {{ i }}. {{ question['option' + i] }}
                    </li>
                  </ul>
                  <div class="d-flex justify-content-end">
                    <button class="btn btn-sm btn-outline-secondary me-2" @click="startQuestionEdit(question)">✏️</button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteQuestion(question.id)">❌</button>
                  </div>
                </template>
              </li>
            </ul>
            <p v-if="!selectedQuiz" class="text-muted text-center mt-3">Select a quiz to see and add questions.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getSubjects, createSubject, deleteSubject, updateSubject, getChapters, createChapter, deleteChapter, updateChapter, getQuizzes, createQuiz, deleteQuiz, updateQuiz, getQuestions, createQuestion, deleteQuestion, updateQuestion } from '../api';

export default {
  name: 'AdminDashboard',
  data() {
    return {
      search: '',
      subjects: [],
      selectedSubject: null,
      newSubjectName: '',
      editingSubjectId: null,
      editingSubjectName: '',
      
      chapters: [],
      selectedChapter: null,
      newChapterName: '',
      editingChapterId: null,
      editingChapterName: '',
      
      quizzes: [],
      selectedQuiz: null,
      newQuizDate: '',
      newQuizRemarks: '',
      newQuizDuration: '',
      editingQuizId: null,
      editingQuizDate: '',
      editingQuizRemarks: '',

      questions: [],
      selectedQuestion: null,
      newQuestionStatement: '',
      newOption1: '',
      newOption2: '',
      newOption3: '',
      newOption4: '',
      newCorrectOption: 1,
      editingQuestionId: null,
      editingQuestionStatement: '',
      editingOption1: '',
      editingOption2: '',
      editingOption3: '',
      editingOption4: '',
      editingCorrectOption: 1,

      // Hover states
      hoveredSubject: null,
      hoveredChapter: null,
      hoveredQuiz: null,
      hoveredQuestion: null,
      
      notification: '',
      notificationType: '',
      notificationTimeout: null
    };
  },
  methods: {
    // Data Fetching
    async fetchSubjects() {
      try {
        const response = await getSubjects();
        // Deduplicate subjects by ID in case API returns duplicates
        const unique = new Map();
        response.data.forEach(s => unique.set(s.id, s));
        this.subjects = Array.from(unique.values());
      } catch (error) {
        console.error("Failed to fetch subjects:", error);
      }
    },
    async selectSubject(subject) {
      this.selectedSubject = subject;
      this.selectedChapter = null;
      this.selectedQuiz = null;
      this.chapters = [];
      this.quizzes = [];
      this.questions = [];
      this.hoveredSubject = null;
      this.hoveredChapter = null;
      this.hoveredQuiz = null;
      this.hoveredQuestion = null;
      try {
        const response = await getChapters(subject.id);
        const uniqueCh = new Map();
        response.data.forEach(c => uniqueCh.set(c.id, c));
        this.chapters = Array.from(uniqueCh.values());
      } catch (error) {
        console.error("Failed to fetch chapters:", error);
      }
    },
    async selectChapter(chapter) {
      this.selectedChapter = chapter;
      this.selectedQuiz = null;
      this.quizzes = [];
      this.questions = [];
      this.hoveredChapter = null;
      this.hoveredQuiz = null;
      this.hoveredQuestion = null;
      try {
        const response = await getQuizzes(chapter.id);
        const uniqQz = new Map();
        response.data.forEach(q => uniqQz.set(q.id, q));
        this.quizzes = Array.from(uniqQz.values());
      } catch (error) {
        console.error("Failed to fetch quizzes:", error);
      }
    },
    async selectQuiz(quiz) {
      this.selectedQuiz = quiz;
      this.questions = [];
      this.hoveredQuiz = null;
      this.hoveredQuestion = null;
      try {
        const response = await getQuestions(quiz.id);
        const uniqQs = new Map();
        response.data.forEach(q => uniqQs.set(q.id, q));
        this.questions = Array.from(uniqQs.values());
      } catch (error) {
        console.error("Failed to fetch questions:", error);
      }
    },

    // CRUD Operations
    async addSubject() {
      if (!this.newSubjectName) return;
      try {
        const res = await createSubject(this.newSubjectName);
        const newId = res.data.id;
        // Push new subject locally for instant feedback
        this.subjects.push({ id: newId, name: this.newSubjectName, chapters: [] });
        this.newSubjectName = '';
        // Also refetch to ensure consistency
        await this.fetchSubjects();
        this.showNotification('Subject added successfully!', 'success');
      } catch (error) {
        this.showNotification('Failed to add subject.', 'error');
        console.error("Failed to add subject:", error);
      }
    },
    async deleteSubject(id) {
      const subject = this.subjects.find(s => s.id === id);
      const confirmMessage = `Are you sure you want to delete the subject "${subject ? subject.name : 'Unknown'}"? This will also delete all its chapters, quizzes, questions and every user's scores and attempts for them.`;
      
      if (!confirm(confirmMessage)) {
        return;
      }
      
      try {
        await deleteSubject(id);
        await this.fetchSubjects();
        if (this.selectedSubject && this.selectedSubject.id === id) {
          this.selectedSubject = null;
          this.chapters = [];
          this.quizzes = [];
          this.questions = [];
        }
        this.showNotification('Subject deleted.', 'success');
      } catch (error) {
        this.showNotification('Failed to delete subject.', 'error');
        console.error("Failed to delete subject:", error);
      }
    },
    async addChapter() {
      if (!this.newChapterName || !this.selectedSubject) return;
      try {
        await createChapter(this.newChapterName, this.selectedSubject.id);
        this.newChapterName = '';
        await this.selectSubject(this.selectedSubject); // Refresh chapters
        this.showNotification('Chapter added!', 'success');
      } catch (error) {
        this.showNotification('Failed to add chapter.', 'error');
        console.error("Failed to add chapter:", error);
      }
    },
    async deleteChapter(id) {
      const chapter = this.chapters.find(c => c.id === id);
      const confirmMessage = `Are you sure you want to delete the chapter "${chapter ? chapter.name : 'Unknown'}"? This will also delete all its quizzes, questions and every user's scores and attempts for them.`;
      
      if (!confirm(confirmMessage)) {
        return;
      }
      
      try {
        await deleteChapter(id);
        await this.selectSubject(this.selectedSubject); // Refresh chapters
        if (this.selectedChapter && this.selectedChapter.id === id) {
          this.selectedChapter = null;
          this.quizzes = [];
          this.questions = [];
        }
        this.showNotification('Chapter deleted.', 'success');
      } catch (error) {
        this.showNotification('Failed to delete chapter.', 'error');
        console.error("Failed to delete chapter:", error);
      }
    },
    async addQuiz() {
      if (!this.newQuizDate || !this.newQuizRemarks || !this.selectedChapter) return;
      try {
        await createQuiz(this.selectedChapter.id, this.newQuizDate, this.newQuizRemarks, this.newQuizDuration);
        this.newQuizDate = '';
        this.newQuizRemarks = '';
        this.newQuizDuration = '';
        await this.selectChapter(this.selectedChapter); // Refresh quizzes
        this.showNotification('Quiz added!', 'success');
      } catch (error) {
        this.showNotification(error.response?.data?.error || 'Failed to add quiz.', 'error');
        console.error("Failed to add quiz:", error);
      }
    },
    async deleteQuiz(id) {
      const quiz = this.quizzes.find(q => q.id === id);
      const confirmMessage = `Are you sure you want to delete the quiz "${quiz ? quiz.remarks : 'Unknown'}"? This will also delete all its questions and every user's scores and attempts for it.`;
      
      if (!confirm(confirmMessage)) {
        return;
      }
      
      try {
        await deleteQuiz(id);
        await this.selectChapter(this.selectedChapter); // Refresh quizzes
        if (this.selectedQuiz && this.selectedQuiz.id === id) {
          this.selectedQuiz = null;
          this.questions = [];
        }
        this.showNotification('Quiz deleted.', 'success');
      } catch (error) {
        this.showNotification('Failed to delete quiz.', 'error');
        console.error("Failed to delete quiz:", error);
      }
    },
    async addQuestion() {
      if (!this.newQuestionStatement || !this.selectedQuiz) return;
      try {
        await createQuestion(
          this.selectedQuiz.id,
          this.newQuestionStatement,
          this.newOption1,
          this.newOption2,
          this.newOption3,
          this.newOption4,
          this.newCorrectOption
        );
        // Reset form
        this.newQuestionStatement = '';
        this.newOption1 = '';
        this.newOption2 = '';
        this.newOption3 = '';
        this.newOption4 = '';
        this.newCorrectOption = 1;
        await this.selectQuiz(this.selectedQuiz); // Refresh questions
        this.showNotification('Question added!', 'success');
      } catch (error) {
        this.showNotification('Failed to add question.', 'error');
        console.error("Failed to add question:", error);
      }
    },
    async deleteQuestion(id) {
      const question = this.questions.find(q => q.id === id);
      const confirmMessage = `Are you sure you want to delete the question "${question ? question.question_statement.substring(0, 50) + '...' : 'Unknown'}"?`;
      
      if (!confirm(confirmMessage)) {
        return;
      }
      
      try {
        await deleteQuestion(id);
        await this.selectQuiz(this.selectedQuiz); // Refresh questions
        this.showNotification('Question deleted.', 'success');
      } catch (error) {
        this.showNotification('Failed to delete question.', 'error');
        console.error("Failed to delete question:", error);
      }
    },
    editSubject() {},
    editChapter() {},
    editQuiz() {},
    editQuestion() {},
    startSubjectEdit(subject) {
      this.editingSubjectId = subject.id;
      this.editingSubjectName = subject.name;
    },
    cancelSubjectEdit() {
      this.editingSubjectId = null;
      this.editingSubjectName = '';
    },
    async saveSubjectEdit(id) {
      if (!this.editingSubjectName) return;
      try {
        await updateSubject(id, this.editingSubjectName);
        this.editingSubjectId = null;
        this.editingSubjectName = '';
        await this.fetchSubjects();
        this.showNotification('Subject updated!', 'success');
      } catch (error) {
        this.showNotification('Failed to update subject.', 'error');
        console.error('Failed to update subject:', error);
      }
    },
    // Chapter Edit
    startChapterEdit(chapter) {
      this.editingChapterId = chapter.id;
      this.editingChapterName = chapter.name;
    },
    cancelChapterEdit() {
      this.editingChapterId = null;
      this.editingChapterName = '';
    },
    async saveChapterEdit(id) {
      if (!this.editingChapterName) return;
      try {
        await updateChapter(id, this.editingChapterName);
        this.editingChapterId = null;
        this.editingChapterName = '';
        await this.selectSubject(this.selectedSubject);
        this.showNotification('Chapter updated!', 'success');
      } catch (error) {
        this.showNotification('Failed to update chapter.', 'error');
        console.error('Failed to update chapter:', error);
      }
    },
    // Quiz Edit
    startQuizEdit(quiz) {
      this.editingQuizId = quiz.id;
      this.editingQuizDate = quiz.date_of_quiz.slice(0, 10);
      this.editingQuizRemarks = quiz.remarks;
    },
    cancelQuizEdit() {
      this.editingQuizId = null;
      this.editingQuizDate = '';
      this.editingQuizRemarks = '';
    },
    async saveQuizEdit(id) {
      if (!this.editingQuizDate || !this.editingQuizRemarks) return;
      try {
        await updateQuiz(id, { date_of_quiz: this.editingQuizDate, remarks: this.editingQuizRemarks });
        this.editingQuizId = null;
        this.editingQuizDate = '';
        this.editingQuizRemarks = '';
        await this.selectChapter(this.selectedChapter);
        this.showNotification('Quiz updated!', 'success');
      } catch (error) {
        this.showNotification('Failed to update quiz.', 'error');
        console.error('Failed to update quiz:', error);
      }
    },
    // Question Edit
    startQuestionEdit(question) {
      this.editingQuestionId = question.id;
      this.editingQuestionStatement = question.question_statement;
      this.editingOption1 = question.option1;
      this.editingOption2 = question.option2;
      this.editingOption3 = question.option3;
      this.editingOption4 = question.option4;
      this.editingCorrectOption = question.correct_option;
    },
    cancelQuestionEdit() {
      this.editingQuestionId = null;
      this.editingQuestionStatement = '';
      this.editingOption1 = '';
      this.editingOption2 = '';
      this.editingOption3 = '';
      this.editingOption4 = '';
      this.editingCorrectOption = 1;
    },
    async saveQuestionEdit(id) {
      if (!this.editingQuestionStatement || !this.editingOption1 || !this.editingOption2 || !this.editingOption3 || !this.editingOption4) return;
      try {
        await updateQuestion(id, {
          question_statement: this.editingQuestionStatement,
          option1: this.editingOption1,
          option2: this.editingOption2,
          option3: this.editingOption3,
          option4: this.editingOption4,
          correct_option: this.editingCorrectOption
        });
        this.cancelQuestionEdit();
        await this.selectQuiz(this.selectedQuiz);
        this.showNotification('Question updated!', 'success');
      } catch (error) {
        this.showNotification('Failed to update question.', 'error');
        console.error('Failed to update question:', error);
      }
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
    formatDate(dateString) {
      if (!dateString) return 'Never';
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
  },
  async mounted() {
    await this.fetchSubjects();
  }
};
</script>

<style scoped>
.card {
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}
.card-header {
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
  cursor: pointer;
}
.list-group-item-action:hover {
  background-color: #e9ecef;
  color: #007bff;
  transform: translateX(5px);
}
.active-admin {
  background-color: #007bff !important;
  color: #ffffff !important;
}

/* Ensure all elements inside active-admin have white text */
.active-admin * {
  color: #ffffff !important;
}

/* Override button colors inside active-admin */
.active-admin .btn {
  color: #ffffff !important;
  border-color: #ffffff !important;
}

.active-admin .btn:hover {
  background-color: rgba(255, 255, 255, 0.2) !important;
  color: #ffffff !important;
}

.active-admin .btn:active {
  background-color: rgba(255, 255, 255, 0.3) !important;
  color: #ffffff !important;
}

/* When editing, change text color to black for better readability */
.list-group-item input {
  color: #000000 !important;
}

.list-group-item input::placeholder {
  color: #6c757d !important;
}

/* Make dropdown text black in questions list */
.list-group-item select {
  color: #000000 !important;
}

.list-group-item select option {
  color: #000000 !important;
}

/* Ensure edit buttons and text are black when in edit mode */
.list-group-item .btn-success,
.list-group-item .btn-secondary {
  color: #000000 !important;
  border-color: #000000 !important;
}

.list-group-item .btn-success:hover,
.list-group-item .btn-secondary:hover {
  color: #000000 !important;
}

.list-group-item .btn-success:active,
.list-group-item .btn-secondary:active {
  color: #000000 !important;
}
.btn-outline-secondary, .btn-outline-danger {
  border-radius: 8px;
  padding: 4px 10px;
  margin-left: 2px;
  transition: all 0.2s;
}
.btn-outline-secondary:hover {
  background-color: #007bff;
  color: #fff;
}
.btn-outline-secondary:active {
  background-color: #0056b3;
  color: #fff !important;
}
.btn-outline-danger:hover {
  background-color: #dc3545;
  color: #fff;
}
.btn-outline-danger:active {
  background-color: #c82333;
  color: #fff !important;
}

/* Add white text effect for all buttons when clicked */
.btn:active {
  color: #fff !important;
}

/* Specific button types for better visual feedback */
.btn-primary:active {
  background-color:rgb(115, 127, 139) !important;
  color: #fff !important;
}

.btn-secondary:active {
  background-color: #545b62 !important;
  color: #fff !important;
}

.btn-success:active {
  background-color: #1e7e34 !important;
  color: #fff !important;
}

.btn-warning:active {
  background-color: #e0a800 !important;
  color: #fff !important;
}

.btn-info:active {
  background-color: #117a8b !important;
  color: #fff !important;
}

.btn-danger:active {
  background-color: #c82333 !important;
  color: #fff !important;
}
</style> 