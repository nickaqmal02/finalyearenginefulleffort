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

### Phase 1 (Completed ✅)
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
- ✅ **Autism Diagnosis System** - DSM-5 specifiers, support levels, approval workflow (therapist proposes → doctor approves)

### Phase 2 (Completed ✅)
- ✅ **Sentiment Analysis** - XLM-RoBERTa Malay model (fine-tuned on therapy conversations)
- ✅ **Text Cleaning** - Dual-purpose cleaner:
  - Light cleaning for sentiment (preserves emotional words, punctuation, intensifiers)
  - Aggressive cleaning for topic modeling (removes stopwords, greetings, fillers)
- ✅ **Malay/English Mix Support** - Stopwords, typo correction, slang mapping, emoji conversion, curse word filtering

### Phase 3 (In Progress 🔄)
- 🔄 **Topic Modeling** - BERTopic with hybrid approach (unsupervised clustering + supervised topic mapping)
  - ✅ Dual cleaning pipeline (`cleaned_text` for sentiment, `cleaned_text_topic` for topics)
  - ✅ 12 predefined therapy topic categories (Speech, Eating, Tantrums, Sleep, Social, School, Physical, Therapy Progress, Parental Emotions, Family, Sensory, Treatment)
  - ✅ Domain words list to preserve therapy-specific terms
  - ✅ UMAP dimensionality reduction + HDBSCAN clustering
  - 🔄 Topic visualization dashboard
  - 🔄 Topic trend analysis over time

### Phase 4 (Future)
- 📱 Mobile app (iOS/Android)
- 📊 Advanced reporting & analytics dashboard
- 🔔 Push notifications
- 🌐 Multi-language support
- ⚡ Real-time topic detection

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Django 6.0.4 |
| **Database** | SQLite (development), PostgreSQL (production ready) |
| **Frontend** | Bootstrap 5, Crispy Forms |
| **ML/AI - Sentiment** | XLM-RoBERTa (fine-tuned on Malay therapy conversations) |
| **ML/AI - Topic Modeling** | BERTopic, Sentence Transformers, UMAP, HDBSCAN |
| **ML/AI - NLP** | scikit-learn (CountVectorizer, cosine similarity) |
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
