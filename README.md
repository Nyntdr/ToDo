# Django REST Framework (DRF) + Vue 3 Full-Stack Tutorial Guide

This guide walks you through building a decoupled full-stack application using **Django REST Framework (DRF)** on the backend and **Vue 3 (Vite)** on the frontend. It covers user authentication, permission-based authorization, generic class-based API views, database setup, and frontend-to-backend communication.

---

## 📑 Table of Contents
1. [Core Mental Model & Architecture](#1-core-mental-model--architecture)
2. [Project Structure](#2-project-structure)
3. [Step 1: Environment & Project Initialization](#step-1-environment--project-initialization)
4. [Step 2: Settings, CORS & Database Configuration](#step-2-settings-cors--database-configuration)
5. [Step 3: Models & Serializers](#step-3-models--serializers)
6. [Step 4: Generic Class-Based Views & URL Routing](#step-4-generic-class-based-views--url-routing)
7. [Step 5: Vue 3 Frontend & API Connection](#step-5-vue-3-frontend--api-connection)
8. [VS Code & IDE Configuration (Troubleshooting Errors)](#vs-code--ide-configuration)
9. [Authentication Deep Dive: DRF Tokens vs. JWT](#authentication-deep-dive-drf-tokens-vs-jwt)
10. [Running the Application](#running-the-application)

---

## 1. Core Mental Model & Architecture

### Request-Response Lifecycle in DRF

```
[ Client (Vue 3 / Axios) ]
         │
         │  HTTP Request (Method + JSON Payload + "Authorization: Token <key>")
         ▼
     urls.py               --> Resolves URL path and dispatches to the correct View
         │
     views.py              --> Generic Class-Based View (checks auth, coordinates business logic)
        ╱ ╲
       ╱   ╲
      ▼     ▼
models.py   serializers.py --> Translates Model instances <-> Python primitives <-> JSON
(Database)                 --> Validates incoming request data
         │
         ▼
[ Client (Vue 3 / Axios) ] <-- HTTP Response (JSON status code + payload)
```

### Django "Project" vs. "App"
* **Project (`backend/`)**: The master configuration container. Holds global settings (`settings.py`), global URL routing (`urls.py`), ASGI/WSGI servers, and the database connection.
* **App (`todos/`)**: A modular, reusable sub-component focused on a single domain. Contains its own models, serializers, views, and urls.

---

## 2. Project Structure

```text
ToDoTutorial/
├── .gitignore                  <-- Ignores venv, node_modules, sqlite, cache
├── .vscode/
│   └── settings.json           <-- Points VS Code to backend/venv Python interpreter
├── README.md                   <-- This complete guide
├── backend/                    <-- DRF Backend
│   ├── manage.py
│   ├── db.sqlite3              <-- SQLite database
│   ├── venv/                   <-- Python virtual environment
│   ├── backend/                <-- Project configuration
│   │   ├── settings.py
│   │   └── urls.py
│   └── todos/                  <-- Application logic
│       ├── models.py           <-- Todo database table
│       ├── serializers.py      <-- Todo & User serializers
│       ├── views.py            <-- Generic Class-Based Views
│       ├── urls.py             <-- App-level API endpoints
│       └── admin.py            <-- Django Admin registration
└── frontend/                   <-- Vue 3 Frontend (Vite)
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js             <-- App entry point (imports style.css)
        ├── style.css           <-- Pure light-theme styling
        ├── api.js              <-- Axios instance with auth interceptor
        └── App.vue             <-- Main component (Auth + To-Do CRUD)
```

---

## Step 1: Environment & Project Initialization

### 1. Create directory and virtual environment
```bash
mkdir backend
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install backend dependencies
```bash
pip install django djangorestframework django-cors-headers
```

### 3. Initialize Django project and app
```bash
django-admin startproject backend .
python manage.py startapp todos
```
> **Tip:** The `.` at the end of `startproject backend .` creates `manage.py` directly in the current directory, preventing unnecessary nested folders.

---

## Step 2: Settings, CORS & Database Configuration

Edit `backend/backend/settings.py`:

### 1. Register installed apps
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',  # Generates database table for auth tokens
    'corsheaders',               # Handles CORS headers for Vue

    # Local apps
    'todos',
]
```

### 2. Add CORS Middleware
Place `CorsMiddleware` at the very top of `MIDDLEWARE`:
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must precede CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... rest of middlewares
]
```

### 3. Configure DRF and Allowed Origins
Append to the bottom of `settings.py`:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

### 4. Database Explanation
Django defaults to SQLite:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
* **SQLite:** Zero configuration, stored in a single file `db.sqlite3`. Perfect for local development and learning.
* **PostgreSQL:** For production, switch `'ENGINE'` to `'django.db.backends.postgresql'` and provide database credentials (`NAME`, `USER`, `PASSWORD`, `HOST`, `PORT`).

### 5. Apply initial migrations & create superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Step 3: Models & Serializers

### 1. Define Model (`backend/todos/models.py`)
```python
from django.db import models
from django.contrib.auth.models import User

class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
```

### 2. Define Serializers (`backend/todos/serializers.py`)
```python
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Todo

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ['id', 'user', 'title', 'description', 'completed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
```

### 3. Create & Run Migrations
```bash
python manage.py makemigrations todos
python manage.py migrate
```

---

## Step 4: Generic Class-Based Views & URL Routing

### 1. Create Views (`backend/todos/views.py`)
```python
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from .models import Todo
from .serializers import TodoSerializer, RegisterSerializer, UserSerializer

# --- Auth Views ---
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "token": token.key
        })

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

# --- Todo CRUD Generic Views ---
class TodoListCreateView(generics.ListCreateAPIView):
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Data Isolation: Only return todos owned by the requesting user
        return Todo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Auto-assign owner on creation
        serializer.save(user=self.request.user)

class TodoDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Data Isolation: Users cannot inspect, update, or delete other users' tasks
        return Todo.objects.filter(user=self.request.user)
```

### 2. App Routing (`backend/todos/urls.py`)
```python
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import RegisterView, UserProfileView, TodoListCreateView, TodoDetailView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', obtain_auth_token, name='login'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('todos/', TodoListCreateView.as_view(), name='todo-list-create'),
    path('todos/<int:pk>/', TodoDetailView.as_view(), name='todo-detail'),
]
```

### 3. Root Routing (`backend/backend/urls.py`)
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('todos.urls')),
]
```

---

## Step 5: Vue 3 Frontend & API Connection

### 1. Scaffold Vue + Vite
```bash
cd /home/nayan/Django/ToDoTutorial/frontend
npm create vite@latest . -- --template vue
npm install
npm install axios
```

### 2. Configure Axios Client (`frontend/src/api.js`)
```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Attach token if user is authenticated
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Token ${token}`
  }
  return config
})

export default api
```

### 3. Pure Light-Mode Styling (`frontend/src/style.css`)
Contains clean variables, form inputs, card layouts, and list item styling without dark mode media queries.

### 4. Vue Main Component (`frontend/src/App.vue`)
Contains the user state, auth toggle (login vs register), token storage in `localStorage`, and CRUD methods calling `api.get('todos/')`, `api.post('todos/', {...})`, `api.patch('todos/:id/', {...})`, and `api.delete('todos/:id/')`.

---

## VS Code & IDE Configuration

### Why VS Code Shows Missing Import Errors
When the workspace root is at the project root (`ToDoTutorial/`), VS Code defaults to the system-wide Python interpreter (`/usr/bin/python3`), where `django` and `rest_framework` are not installed.

### The Fix: Workspace Configuration (`.vscode/settings.json`)
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.analysis.extraPaths": [
    "${workspaceFolder}/backend"
  ]
}
```
Reloading VS Code or restarting the language server (`Ctrl + Shift + P` -> `Python: Restart Language Server`) clears all diagnostic import warnings.

---

## Authentication Deep Dive: DRF Tokens vs. JWT

| Criteria | DRF Built-in Token (`rest_framework.authtoken`) | JWT (`djangorestframework-simplejwt`) |
| :--- | :--- | :--- |
| **Storage** | Stored in database table (`authtoken_token`) | Stateless (cryptographically signed) |
| **Expiration** | None (lasts forever until deleted) | Short-lived Access Token (e.g., 5–15 mins) + Refresh Token |
| **DB Lookups** | Hits database on every API request | No database lookup needed to authenticate |
| **Multi-session** | Single token per user account | Independent tokens per device/session |
| **Best For** | Learning, MVPs, internal dashboards | Production SaaS, mobile applications |

---

## Running the Application

### Start the Backend (Terminal 1)
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```
Runs at: `http://127.0.0.1:8000/`

### Start the Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
Runs at: `http://localhost:5173/`
