# Library Management System API

A comprehensive and scalable solution for modern libraries, built with FastAPI and MySQL.

## 🚀 Features

- **Robust Authentication**: Secure login with both JWT tokens and API keys
- **Role-Based Access Control**: Different permissions for Admins, Librarians, and Users
- **Complete Book Management**: Add, search, update, and categorize books
- **Borrowing System**: Seamless book checkout and return processes
- **Real-Time Notifications**: WebSocket integration for instant updates
- **Security First**: Rate limiting, encrypted API keys, and HTTPS support
- **Redis Caching**: High performance with intelligent caching
- **Docker Ready**: Easy deployment with containerization

## 📋 Requirements

- Python 3.9+
- MySQL 8.0+
- Redis (for caching)
- Docker and Docker Compose (for containerized deployment)

## 🏁 Quick Start with Docker

Get up and running in minutes:

```bash
# Clone the repository
git clone https://github.com/Ali-y-Suliman/library-management-system.git

# Navigate to the project directory
cd library-management-system

# Start the application
docker-compose up -d