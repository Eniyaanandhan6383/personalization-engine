 🧠 Privacy-First Personalization & Ad Engine


 🚀 Overview

An API-first SaaS platform that delivers real-time content recommendations and targeted ads using first-party behavioral data — without relying on third-party tracking.

> This project was developed collaboratively, focusing on cloud deployment and backend API development.


✨ Key Features

* 🔐 JWT-based Authentication
* 📊 User Behavior Tracking (clicks, watch time, searches)
* 🧠 Personalization Engine (ML-based logic)
* 🎯 Recommendation System
* 💰 Ad Targeting Engine
* 🔍 Explainability API ("Why this recommendation?")
* ☁️ Cloud Deployment using AWS



🏗️ Architecture


Client Request
      ↓
 FastAPI (EC2)
      ↓
 ┌───────────────┐
 │   RDS (DB)    │
 └───────────────┘
      ↓
 ┌───────────────┐
 │   S3 Storage  │
 └───────────────┘


⚙️ Tech Stack

| Layer    | Technology              |
| -------- | ----------------------- |
| Backend  | FastAPI (Python)        |
| Database | MySQL (AWS RDS)         |
| Cloud    | AWS EC2, S3, CloudWatch |
| DevOps   | Git, GitHub, SSH        |



🔌 API Endpoints

| Feature         | Endpoint            |
| --------------- | ------------------- |
| Register        | POST /auth/register |
| Login           | POST /auth/login    |
| Refresh Token   | POST /auth/refresh  |
| Track Behavior  | POST /track         |
| Recommendations | GET /recommend      |
| Ads             | GET /ads            |
| Explainability  | GET /why-this       |



⚡ Setup Instructions

 1. Clone Repository

bash
git clone https://github.com/Bhuvanesh-S03/personalization-engine.git
cd personalization-engine

2. Create Virtual Environment

bash
python3 -m venv venv
source venv/bin/activate


 3. Install Dependencies

bash
pip install -r requirements.txt


 4. Configure Environment Variables

Create a `.env` file:


DB_HOST=your-rds-endpoint
DB_PORT=3306
DB_NAME=personalization_db
DB_USER=admin
DB_PASSWORD=yourpassword


 5. Run Server

bash
uvicorn main:app --host 0.0.0.0 --port 8000




 🌐 Live API

* Base URL: `http://54.85.206.159:8000`
* API Docs: `http://54.85.206.159:8000/docs`



👥 Team & Contributions

* ☁️ **Eniya Anandhan – Cloud Engineer**

  * AWS Infrastructure (EC2, RDS, S3)
  * Deployment & Server Management
  * GitHub Integration & DevOps
  * Monitoring & Cost Optimization

* 💻 **Bhuvanesh – Backend Developer**

  * API Development (FastAPI)
  * Database Models & Business Logic
  * Personalization & Recommendation Engine



 🚀 Future Enhancements

* Redis Caching
* Real-time data streaming
* Advanced ML models
* Dashboard analytics


⭐ Support

If you find this project useful, give it a ⭐ on GitHub!



 📄 License

This project is for educational purposes.
