# 🧠 Autism Center Chat Analyzer

A Django-based web application that helps autism centers analyze WhatsApp conversations with clients, track sentiment, and manage therapist-client relationships.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This system addresses the challenge autism centers face in managing and analyzing WhatsApp conversations with clients. It automatically imports chat exports, links messages to clients, performs sentiment analysis using a custom Malay BERT model, and provides therapists with actionable insights.

## ✨ Features

### Phase 1 (Current MVP)
- ✅ **Authentication System** - Admin and Therapist login with session management
- ✅ **Client Management** - Full CRUD operations for client profiles
- ✅ **Therapist Management** - Manage therapists and assign clients
- ✅ **WhatsApp Import** - Upload and parse WhatsApp .txt exports
- ✅ **Smart Client Matching** - Match messages by phone number OR username
- ✅ **Conversation Storage** - All messages stored in structured database
- ✅ **Unmatched Message Handling** - Separate table for unrecognized senders
- ✅ **Admin Dashboard** - Key metrics, recent activity, quick actions
- ✅ **Therapist Portal** - View assigned clients and their conversations
- ✅ **Responsive UI** - Bootstrap 5 with offcanvas navigation

### Phase 2 (In Progress)
- 🔄 **Sentiment Analysis** - Malay BERT model integration
- 🔄 **Text Cleaning** - Malay stop words, typo correction, emoji conversion
- 🔄 **Analytics Dashboard** - Charts and visualizations

### Phase 3 (Future)
- 📱 Mobile app (iOS/Android)
- 📊 Advanced reporting
- 🔔 Push notifications

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Django 6.0.4 |
| **Database** | SQLite (development), PostgreSQL (production ready) |
| **Frontend** | Bootstrap 5, Crispy Forms |
| **ML/AI** | PyTorch, Transformers (Hugging Face), Malay BERT |
| **Authentication** | Custom session-based auth |
| **Deployment** | Ready for PythonAnywhere, Railway, or self-hosted |

## 📦 Installation

### Prerequisites
- Python 3.12 or higher
- pip package manager
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/autism-center-analyzer.git
cd autism-center-analyzer