# Library Management System API

A FastAPI-based Library Management System with MySQL database integration.

## Features

- User authentication (JWT tokens and API keys)
- Role-based access control (Admin, Librarian, User)
- Book management
- Book borrowing and returns
- Real-time notifications via WebSockets
- Secure API with rate limiting
- HTTPS support

## Requirements

- Python 3.9+
- MySQL 8.0+
- Docker and Docker Compose (for containerized deployment)

## Quick Start with Docker

1. Clone the repository
2. Navigate to the project directory
3. Start the application with Docker Compose:

```bash
docker-compose up -d