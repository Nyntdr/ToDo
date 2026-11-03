<script setup>
import { ref, onMounted } from 'vue'
import api from './api'

// ----------------------------------------------------------------------------
// STATE
// ----------------------------------------------------------------------------
// Auth state
const token = ref(localStorage.getItem('token') || '')
const username = ref('')
const password = ref('')
const isRegistering = ref(false)
const currentUser = ref(null)
const authError = ref('')

// Todos state
const todos = ref([])
const newTitle = ref('')
const newDescription = ref('')
const loading = ref(false)

// ----------------------------------------------------------------------------
// AUTH METHODS
// ----------------------------------------------------------------------------
async function handleAuth() {
  authError.value = ''
  try {
    if (isRegistering.value) {
      // Register view (generics.CreateAPIView)
      const res = await api.post('auth/register/', {
        username: username.value,
        password: password.value,
      })
      token.value = res.data.token
      currentUser.value = res.data.user
    } else {
      // Login view (obtain_auth_token)
      const res = await api.post('auth/login/', {
        username: username.value,
        password: password.value,
      })
      token.value = res.data.token
    }

    localStorage.setItem('token', token.value)
    username.value = ''
    password.value = ''
    await fetchProfileAndTodos()
  } catch (err) {
    authError.value =
      err.response?.data?.non_field_errors?.[0] ||
      err.response?.data?.username?.[0] ||
      'Authentication failed. Please verify your credentials.'
  }
}

function handleLogout() {
  token.value = ''
  currentUser.value = null
  todos.value = []
  localStorage.removeItem('token')
}

async function fetchProfileAndTodos() {
  if (!token.value) return
  try {
    const userRes = await api.get('auth/profile/')
    currentUser.value = userRes.data
    await fetchTodos()
  } catch (err) {
    handleLogout()
  }
}

// ----------------------------------------------------------------------------
// TO-DO CRUD METHODS (Hits Generic DRF Views)
// ----------------------------------------------------------------------------
async function fetchTodos() {
  loading.value = true
  try {
    const res = await api.get('todos/')
    todos.value = res.data
  } catch (err) {
    console.error('Failed to fetch todos', err)
  } finally {
    loading.value = false
  }
}

async function createTodo() {
  if (!newTitle.value.trim()) return
  try {
    const res = await api.post('todos/', {
      title: newTitle.value,
      description: newDescription.value,
    })
    todos.value.unshift(res.data)
    newTitle.value = ''
    newDescription.value = ''
  } catch (err) {
    alert('Failed to create task')
  }
}

async function toggleTodo(todo) {
  try {
    const res = await api.patch(`todos/${todo.id}/`, {
      completed: !todo.completed,
    })
    todo.completed = res.data.completed
  } catch (err) {
    alert('Failed to update task')
  }
}

async function deleteTodo(id) {
  try {
    await api.delete(`todos/${id}/`)
    todos.value = todos.value.filter((t) => t.id !== id)
  } catch (err) {
    alert('Failed to delete task')
  }
}

onMounted(() => {
  if (token.value) {
    fetchProfileAndTodos()
  }
})
</script>

<template>
  <div class="container">
    <header>
      <h1>📝 To-Do List</h1>
      <div v-if="token" class="user-info">
        <span>Logged in: <strong>{{ currentUser?.username }}</strong></span>
        <button class="btn-logout" @click="handleLogout">Logout</button>
      </div>
    </header>

    <!-- AUTHENTICATION FORM (When not logged in) -->
    <div v-if="!token" class="card auth-box">
      <h2>{{ isRegistering ? 'Create an Account' : 'Sign In' }}</h2>
      <p v-if="authError" class="error-msg">{{ authError }}</p>

      <form @submit.prevent="handleAuth">
        <input
          v-model="username"
          type="text"
          placeholder="Username"
          required
        />
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          required
        />
        <button type="submit" class="btn-primary">
          {{ isRegistering ? 'Register' : 'Login' }}
        </button>
      </form>

      <p class="switch-mode">
        {{ isRegistering ? 'Already have an account?' : "Don't have an account?" }}
        <a href="#" @click.prevent="isRegistering = !isRegistering">
          {{ isRegistering ? 'Login here' : 'Register here' }}
        </a>
      </p>
    </div>

    <!-- TO-DO DASHBOARD (When logged in) -->
    <div v-else>
      <!-- Create Todo Card -->
      <div class="card">
        <h3>Add New Task</h3>
        <form @submit.prevent="createTodo">
          <input
            v-model="newTitle"
            type="text"
            placeholder="What needs to be done?"
            required
          />
          <input
            v-model="newDescription"
            type="text"
            placeholder="Description (optional)"
          />
          <button type="submit" class="btn-primary">Add Task</button>
        </form>
      </div>

      <!-- Todo List Card -->
      <div class="card">
        <h3>My Tasks ({{ todos.length }})</h3>
        <p v-if="loading" class="empty-msg">Loading tasks...</p>
        <p v-else-if="todos.length === 0" class="empty-msg">No tasks yet. Create one above!</p>

        <ul v-else class="todo-list">
          <li
            v-for="item in todos"
            :key="item.id"
            class="todo-item"
            :class="{ completed: item.completed }"
          >
            <div class="todo-item-left">
              <input
                type="checkbox"
                :checked="item.completed"
                @change="toggleTodo(item)"
              />
              <div class="todo-text">
                <span class="todo-title">{{ item.title }}</span>
                <span v-if="item.description" class="todo-desc">{{ item.description }}</span>
              </div>
            </div>
            <button class="btn-delete" @click="deleteTodo(item.id)">Delete</button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>