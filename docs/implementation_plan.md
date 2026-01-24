# Implementation Plan: SynoCast Transformation Project

## Phase 1: Foundation (Current Focus)

- [x] **1.1 Project Management**
  - [x] Create Implementation Plan Document
  - [x] Update `requirements.txt` with new dependencies (`Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-Babel`)
- [x] **1.2 Folder Structure Refactoring**
  - [x] Create `app/models/` for database models
  - [x] Create `app/services/` for business logic
  - [x] Create `app/blueprints/` for modular routes
  - [x] Create `app/translations/` for i18n
- [x] **1.3 Database Migration to SQLAlchemy**
  - [x] Configure `Flask-SQLAlchemy` in `app/extensions.py`
  - [x] Initialize `db` and `migrate` in `app/__init__.py`
  - [x] Port existing SQLite schema to SQLAlchemy Models in `app/models/`
    - [x] `User`/`Subscriber` model
    - [x] `Location` model
    - [x] `Preferences` model

## Phase 2: Core Refactor

- [x] **2.1 Internationalization (i18n)**
  - [x] Configure `Flask-Babel`
  - [x] Translate static UI strings (Extraction Setup Complete)
- [x] **2.2 Route Refactoring**
  - [x] Port `app/routes/*` to `app/blueprints/*`
  - [x] Update imports and blueprint registration

## Phase 3: Visuals & 3D

- [x] **3.1 Frontend Architecture**
  - [x] Implement Glass UI CSS variables
  - [x] Set up Three.js environment (Added CDN and Canvas)
- [x] **3.2 Weather Effects**
  - [x] Create 3D Scene component (Basic setup)
  - [x] Implement Particle Systems (Rain included)

## Phase 4: Advanced Features

- [x] **4.1 Content Management**
  - [x] Create Content Models (News, Education)
  - [x] Build basic CMS Admin interface (Admin Blueprint & Routes)
- [x] **4.2 Push Notifications**
  - [x] Implement VAPID key generation
  - [x] Create Notification Service
