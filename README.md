# codeBuddy
⚠️ Project Status: In active development

This project is under active development. Core functionality is implemented, with ongoing work on additional features, testing, and documentation.


A self-hosted classroom platform built with Flask that supports teacher and student roles, assignment workflows, automated testing and marking, and local or containerised deployment.

## Engineering Focus
This project demonstrates backend system design, including:
- Role-based access control
- Secure authentication and token handling
- File upload management and validation
- Modular Flask application structure
- Testable, maintainable code organisation

## Overview
codeBuddy is a web-based classroom system designed to support the teaching and learning of programming. It allows teachers to create assignments, invite students, manage submissions, and provide automated and manual feedback, all within a single application.

The project focuses on real-world backend concerns such as authentication, role-based access, file uploads, data persistence, and maintainable application structure.

## Key Features
- Teacher and student roles with secure authentication
- Assignment creation and submission workflows
- Automated test execution and marking
- Rubrics, feedback, and grading support
- Invite tokens for controlled user onboarding
- File upload handling with size limits
- SQLite-backed persistence
- Dockerised deployment for consistency

## Tech Stack
- Python
- Flask
- SQLite
- HTML / CSS / JavaScript
- Docker

## Getting Started

### Prerequisites
- Python 3.10+
- pip
- (Optional) Docker

### Local Setup
```bash
git clone https://github.com/missallgar01/codeBuddy.git
cd codeBuddy
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask run

