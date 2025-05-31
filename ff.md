Hey r/webdev,

For this Saturday Show Off, I'm going beyond a typical overview and offering an architectural and technical deep dive into **CertGames** ([Certgames.com](https://certgames.com)). This platform is a solo-developed endeavor aimed at fundamentally changing how individuals prepare for challenging cybersecurity certifications (like the CompTIA suite, CISSP, AWS CCP). The core philosophy is to combat study fatigue and disengagement by creating a deeply gamified, resource-rich, and effective learning ecosystem. I made an iOS App for it as well, but I wont give technical details about it, considering this is r/webdev but heres the link (ios)[https://apps.apple.com/us/app/comptia-cert-games-practice/id6743811522]

This post will cover:
**I. Core Mission & Functional Design**
**II. Detailed System Architecture & Component Interactions**
**III. Key Technology Stack Components**
**IV. Data Modeling & Persistence Strategy**
**V. Gamification Engine: Technical Implementation**
**VI. Security Measures & Infrastructure**
**VII. Development Practices & CI/CD**
**VIII. Simplified Project Directory Structure Overview**
**IX. Challenges & Learnings**

Let's dive in.

**I. Core Mission & Functional Design**

CertGames exists to make cybersecurity education "fun, effective, and addictive." It addresses user needs for:

*   **Engagement & Motivation:** Using game mechanics to combat the monotony of traditional study.
*   **Comprehensive & Centralized Content:** Over 13,000 practice questions (including Performance-Based Questions - PBQs) for 12 certifications, interactive games, flashcards, and a resource library, all in one place.
*   **Practical Skill Application:** Emphasizing learning through doing via PBQs and interactive simulations.
*   **Progress & Confidence Building:** Detailed feedback, progress tracking, and realistic exam simulations.
*   **Community & Support:** An "Ask Anything" support system (with future plans for more community features).

**Key User-Facing Features (Non-AI):**

1.  **Gamified Learning Core:** XP, Levels, Coins, 50+ Achievements, Leaderboards, customizable Avatars & UI Themes via an in-app Shop.
2.  **Practice Test Engine:** Realistic exam simulations for CompTIA (A+, Net+, Sec+, CySA+, PenTest+, CASP+, Linux+, Cloud+, Data+, Server+), ISC2 CISSP, AWS CCP. Includes detailed explanations, progress tracking, and custom test lengths.
3.  **Interactive Cybersecurity Games:**
    *   `Incident Responder`: Decision-tree scenarios.
    *   `Phishing Phrenzy`: Identifying malicious content.
    *   `Cipher Challenge`: Cryptography puzzles.
    *   `Threat Hunter`: Log analysis.
4.  **Daily Engagement:** Bonuses, GRC/PBQ challenges, "Daily Cyber Brief."
5.  **Learning Resources:** 600+ curated external resources, interactive Cyber Flashcards.
6.  **Support System:** 24/7 "Ask Anything" chat with expert responses.
7.  **Account & Subscription Management:** Standard user lifecycle (OAuth, JWTs), Stripe/Apple IAP for premium access.

**II. Detailed System Architecture & Component Interactions**

CertGames employs a distributed, containerized architecture for modularity and scalability.

*   **Overall Flow:** Client (Browser/Mobile) -> Cloudflare -> NGINX -> Flask API (uWSGI/Gevent) -> [Redis/MongoDB/Celery]
*   **Components:**
    *   **Cloudflare:** Edge network (DNS, CDN for static assets, SSL/TLS, WAF, DDoS/Bot protection).
    *   **NGINX (`nginx/`):**
        *   Reverse Proxy: Routes API (`/api/*`) to `http://backend:5000` (Flask service) and WebSockets (`/api/socket.io/`).
        *   Static Server: Serves the React frontend build (from `/usr/share/nginx/html`).
        *   Security: Enforces security headers (CSP, HSTS, X-Frame-Options, etc.).
        *   Honeypot Routing: Directs specific suspicious paths to the Flask-based honeypot.
    *   **React Frontend (SPA - `frontend/my-react-app/`):**
        *   Renders UI, manages client-side state (Redux Toolkit), handles user interactions, makes API calls (Axios for REST, `socket.io-client` for WebSockets).
    *   **React Native Mobile App (iOS - `CertGames iOS` repo):**
        *   Native iOS experience using Expo (SDK 52). Shares Redux store structure and API client logic with web. Native auth (Apple Sign-In), IAP (StoreKit), secure local storage.
    *   **Flask API Server (`backend/app.py`):**
        *   The application's core. Exposes RESTful API endpoints (Flask Blueprints for organization) and WebSocket event handlers (`Flask-SocketIO`).
        *   Handles all business logic, user authentication/authorization (Flask-JWT-Extended, Authlib), gamification engine operations, database CRUD (PyMongo to MongoDB, `redis-py` to Redis), Celery task queuing, and external API interactions (Stripe, Apple, SendGrid).
        *   Runs on uWSGI with Gevent workers for asynchronous request processing.
    *   **Celery Workers (`backend/Celery/celery_app.py`, `tasks/async_tasks.py`):**
        *   Execute long-running/background tasks (e.g., complex achievement computations, email dispatch via SendGrid, DB cleanup via `tasks/cleanup_tokens.py`) offloaded from the main request-response cycle. Uses Redis as broker/result backend.
    *   **Socket.IO (`Flask-SocketIO` backend, `socket.io-client` frontend):**
        *   Enables real-time features like the support chat (typing indicators, new message delivery), admin dashboard updates. Uses Redis as a message queue for broadcasting across multiple Flask worker processes.
    *   **Redis (`redis/`, Docker service `redis_service`):**
        *   Critical in-memory data store for: Flask user sessions (`Flask-Session`), API response caching, DB query result caching, Celery message broker & result backend, Socket.IO message queue, rate limiting counters.
    *   **MongoDB Atlas (External M20 Cluster):**
        *   Primary persistent database. Stores all application data: user profiles, test content, game states, shop items, achievements, support threads, subscription events, performance logs, honeypot data, etc.

**III. Key Technology Stack Components**

*   **Frontend (Web - `frontend/my-react-app/`):**
    *   React 18.3.1, Redux Toolkit 2.5.1, React Router DOM 7.1.1, Axios, Socket.IO Client.
    *   Styling: CSS Modules, global CSS, CSS Variables (for theming). UI Libs: React Icons, `@mui/material` (limited), Recharts.
    *   Build: Craco (for Webpack 5 customization over `react-scripts`).
*   **Mobile (iOS - `CertGames iOS` repo):**
    *   React Native (Expo SDK 52), Redux Toolkit, React Navigation 7, Expo SDK for native features.
*   **Backend (API - `backend/`):**
    *   Python, Flask 3.1.1, uWSGI 2.0.29, Gevent 24.2.1.
    *   DB/Cache Drivers: PyMongo 4.8.0, `redis-py` 6.1.0.
    *   Auth: Flask-JWT-Extended 4.7.0, Authlib 1.3.0, bcrypt 4.1.2.
    *   Real-time: Flask-SocketIO 5.5.1.
    *   Task Queuing: Celery 5.3.6.
    *   External APIs: `stripe` 12.1.0, `sendgrid` 6.12.2, `requests`/`httpx`.
    *   Validation: Pydantic 2.9.2.
*   **Databases:**
    *   MongoDB Atlas (Cloud NoSQL).
    *   Redis 7.2 (Key-Value Store, self-hosted via Docker).
*   **Infrastructure:**
    *   Docker & Docker Compose.
    *   GCP VM (Linux-based).
    *   NGINX (Reverse Proxy).
    *   Cloudflare (CDN, Security).

**IV. Data Modeling & Persistence Strategy**

Data is primarily stored in MongoDB Atlas, with Redis for caching and ephemeral data.

*   **Key MongoDB Collections & Schemas (Application-Enforced):**
    *   `mainusers`: Central user document. Fields include `_id`, `username`, `email`, `hashed_password`, `oauth_providers`, `xp`, `level`, `coins`, `currentAvatar`, `nameColor`, `purchasedItems` (array of shop item IDs), `unlocked_achievements_ids` (array of achievement IDs), detailed achievement counters (e.g., `total_tests_completed`, `perfect_tests_by_category: { SecurityPlus: 2, ... }`), `subscriptionStatus`, `dailyBonusLastClaimed`, `practiceQuestionLimit`, etc. Indexed heavily on `email`, `username`, `xp`.
    *   `tests`: Stores certification practice tests. Contains `testId`, `testName`, `category`, `questions` (embedded array: `id`, `question` text, `options`, `correctAnswerIndex`, `explanation`, `pbq_type` if applicable).
    *   `testAttempts`: User-specific test attempts. Fields: `userId`, `testId`, `score`, `answers` (array of user responses), `startTime`, `endTime`, `examMode`.
    *   `shop`: Items for purchase. Fields: `itemId`, `title`, `cost`, `type` (avatar, theme, xpBoost), `imageUrl`.
    *   `achievements`: Definitions of all achievements. Fields: `achievementId`, `title`, `description`, `icon`, `criteria` (JSON object defining unlock conditions).
    *   `supportThreads`: User support interactions. Contains `userId`, `title`, `status`, `messages` (embedded array).
    *   `subscriptionEvents`: Logs from Stripe/Apple webhooks.
    *   `perfSamples`: Backend request performance data.
    *   `honeypot_interactions`, `scanAttempts`: Security logging.
*   **Data Integrity & Validation:**
    *   Pydantic models on the backend validate incoming request data and structure outgoing responses.
    *   Client-side validation in React forms.
    *   MongoDB schema validation can be used, but primary validation is at the application layer.
*   **Backup & Recovery:** MongoDB Atlas handles automated daily backups (30-day retention) and PITR. Redis uses AOF persistence (`appendfsync everysec`).

**V. Gamification Engine: Technical Implementation**

This is a core differentiator, designed for deep integration.

1.  **XP/Coin Awarding:**
    *   Flask API endpoints (e.g., `POST /test/user/<user_id>/add-xp`) are called by the frontend after specific user actions.
    *   Logic within these endpoints determines the amount based on action type, difficulty, or fixed values.
    *   User documents in `mainusers` are updated directly. `find_one_and_update` with `$inc` is often used for atomicity.
2.  **Leveling System:**
    *   A predefined XP-to-level mapping (e.g., a curve or fixed XP per level) is used.
    *   After XP update, the backend checks if a new level is reached and updates the `level` field in `mainusers`.
3.  **Achievement Unlocking:**
    *   **Criteria Definition:** Stored in `achievements` collection (e.g., `{ "counter": "perfect_tests_by_category.SecurityPlus", "threshold": 3 }`).
    *   **Checking Mechanism:**
        *   **Immediate:** For simple achievements, the API endpoint triggering the condition checks criteria against the user's `mainusers` document.
        *   **Cumulative/Complex:** For achievements requiring aggregation or complex checks (e.g., "complete 50 tests with >80%"), checks might be triggered after relevant events. If computationally intensive, a Celery task (`tasks/async_tasks.py`) can be dispatched to process this asynchronously, querying user stats and `testAttempts`.
        *   The `mainusers.unlocked_achievements_ids` array is updated.
    *   **Frontend Notification:** API response flags new achievements; React `AchievementToast.js` displays it. `AchievementPage.js` shows all.
4.  **Shop & Customization:**
    *   Purchases (`POST /test/shop/purchase/<item_id>`) check `mainusers.coins`, decrement coins, and add `itemId` to `mainusers.purchasedItems`.
    *   Equipping items (`POST /test/shop/equip`) updates fields like `mainusers.currentAvatar` or `mainusers.nameColor`. The React frontend reads these for UI rendering.
5.  **Daily Systems (`DailyStationPage.js`):**
    *   `POST /test/user/<user_id>/daily-bonus` checks `dailyBonusLastClaimed` timestamp before awarding coins.
    *   Daily GRC/PBQ questions are rotated, with answers submitted to `POST /test/daily-question/answer`.

**VI. Security Measures & Infrastructure Operations**

Security is paramount for a cybersecurity training platform.

*   **Authentication:** JWTs (HttpOnly, Secure cookies), bcrypt password hashing, Google/Apple OAuth (Authlib).
*   **Authorization:** Role-Based Access (RBAC) for admin (`admin_routes.py`), subscription-based access for premium features (`middleware/subscription_check.py`).
*   **Transport Security:** TLS/SSL via Cloudflare.
*   **Data at Rest Encryption:** MongoDB Atlas default encryption. Secrets in `.env`.
*   **Web Security Best Practices:**
    *   NGINX/Flask enforced Security Headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy).
    *   CSRF Protection (`middleware/csrf_protection.py`, `csrfHelper.js` for admin panel).
    *   Input Validation (Pydantic, client-side checks) & Sanitization against XSS/NoSQLi.
*   **Rate Limiting (`security/rate_limiters/`):** Redis-backed, IP/user-based, global and per-feature limits.
*   **Honeypot System (`security/honeypot/`):** Extensive decoy pages (`honeypot_pages.py`, templates), interaction logging to MongoDB (`honeypot_interactions`, `scanAttempts`), GeoIP2, proxy/TOR detection.
*   **Hosting & Operations:**
    *   GCP VM, Docker & Docker Compose.
    *   NGINX reverse proxy.
    *   Cloudflare for CDN, WAF, DNS.
    *   SendGrid for email.

**VII. Development Practices & CI/CD**

*   **Version Control:** Git, GitHub. Feature-branch workflow.
*   **Testing (Automated in GitHub Actions):**
    *   Frontend: Jest & React Testing Library (unit/integration).
    *   Backend: PyTest (unit/integration).
    *   E2E: Cypress (web), Detox (mobile).
    *   Performance: Locust (backend), Lighthouse/React Profiler (frontend).
    *   Security: OWASP ZAP, `npm audit`, Snyk, Bandit.
*   **Linting:** ESLint (React/JS)
*   **Local Dev:** `docker-compose.yml.dev` for hot-reloading environment. `.env` for secrets.

**VIII. Simplified Project Directory Structure Overview (omitted quite a bit, but this gives a good overview)**

```
certgames/  # Root directory for the entire CertGames project.
├── README.MD  # Main project documentation: overview, setup, architecture.
├── Stack  # Top-level documentation for technology stack & architecture.
│   └── Architecture  # Detailed architectural documentation.
│       ├── API  # Backend API specific documentation.
│       │   └── routes.md  # Markdown detailing all API endpoints & specifications.
│       ├── Trees  # Textual/detailed explanations of directory structures.
│       │   ├── Flask.md  # Detailed breakdown of the `backend/` (Flask) structure.
│       │   ├── React.md  # Detailed breakdown of the `frontend/my-react-app/` structure.
│       │   └── Root.md  # Detailed breakdown of the top-level project structure.
│       └── diagrams  # Visual architectural diagrams.
│           ├── AI-Integration.png  # Diagram: AI services integration.
│           ├── Auth-flow.png  # Diagram: User authentication flows (JWT, OAuth).
│           ├── Deployment.png  # Diagram: Production deployment architecture.
│           ├── Shared-Logic-Pattern.png  # Diagram: Logic sharing between web/mobile frontends.
│           ├── Unit-Testing.png  # Diagram/overview: Unit testing strategy.
│           └── api-architecture.png  # Diagram: Backend API internal architecture.
├── backend  # Root directory for all Flask (Python) backend server-side code.
│   ├── AI_helpers  # Package: Helpers for AI model interactions & output processing.
│   │   ├── __init__.py  # Initializes `AI_helpers` as a Python package.
│   │   ├── analogy_stream_helper.py  # Helpers for Analogy Hub AI feature (streaming).
│   │   ├── grc_stream_helper.py  # Helpers for GRC Wizard AI feature (streaming).
│   │   ├── scenario_helper.py  # Helpers for ScenarioSphere AI feature (streaming).
│   │   └── xploitcraft_helper.py  # Helpers for XploitCraft AI feature (payload examples).
│   ├── Celery  # Package: Celery configuration for asynchronous task queuing.
│   │   ├── __init__.py  # Initializes `Celery` as a Python package.
│   │   └── celery_app.py  # Defines & configures the Celery application instance (broker: Redis).
│   ├── Clients  # Package: Clients/wrappers for external AI APIs.
│   │   ├── Gemini.py  # Client for Google Gemini API (e.g., Portfolio Generator).
│   │   ├── OpenAI.py  # Client for OpenAI API (e.g., GPT-4o for learning tools).
│   │   └── __init__.py  # Initializes `Clients` as a Python package.
│   ├── Dockerfile.dev  # Docker build instructions for the development backend image (hot-reloading).
│   ├── Dockerfile.prod  # Docker build instructions for the production backend image (optimized).
│   ├── app.py  # Main Flask application: instance creation, config, blueprint registration, extensions init.
│   ├── instance_config.py  # Instance-specific configurations
│   ├── models  # Package: Data model definitions (Pydantic/MongoDB structures).
│   │   ├── __init__.py  # Initializes `models` as a Python package.
│   │   ├── newsletter.py  # Data model(s) for newsletter subscribers & campaigns.
│   │   ├── password_reset.py  # Data model(s) for password reset tokens/logic.
│   │   └── users.py  # User data model: auth fields, profile, gamification stats, password hashing (bcrypt).
│   ├── mongodb  # Package: MongoDB interaction setup.
│   │   ├── __init__.py  # Initializes `mongodb` as a Python package.
│   │   └── database.py  # Logic for connecting to MongoDB Atlas (PyMongo), global DB client.
│   ├── requirements.txt  # Lists Python package dependencies for the backend (e.g., Flask, PyMongo, Celery).
│   ├── routes  # Top-level package: Organizes Flask API endpoints into modular Blueprints.
│   │   ├── AI  # Blueprint: API endpoints for AI-powered learning tools.
│   │   │   ├── __init__.py  # Initializes `AI` Blueprint.
│   │   │   ├── analogy_routes.py  # Flask routes for "Analogy Hub" feature.
│   │   │   ├── gemini_routes.py  # Flask routes for AI Portfolio Generator (Gemini).
│   │   │   ├── grc_routes.py  # Flask routes for "GRC Wizard" feature.
│   │   │   ├── scenario_routes.py  # Flask routes for "ScenarioSphere" feature.
│   │   │   └── xploit_routes.py  # Flask routes for "XploitCraft" payload generator.
│   │   ├── Auth  # Blueprint: Authentication, authorization, session management endpoints.
│   │   │   ├── __init__.py  # Initializes `Auth` Blueprint.
│   │   │   ├── oauth_routes.py  # Flask routes for OAuth 2.0 flows (Google, Apple, GitHub).
│   │   │   └── password_reset_routes.py  # Flask routes for password reset functionality.
│   │   ├── Subscription  # Blueprint: User subscription and payment management.
│   │   │   ├── __init__.py  # Initializes `Subscription` Blueprint.
│   │   │   └── subscription_routes.py  # Flask routes for Stripe/Apple IAP integration.
│   │   ├── __init__.py  # Initializes `routes` as a Python package.
│   │   ├── games  # Blueprint: API endpoints for interactive cybersecurity games.
│   │   │   ├── __init__.py  # Initializes `games` Blueprint.
│   │   │   ├── cipher_routes.py  # Flask routes for "Cipher Challenge" game.
│   │   │   ├── incident_routes.py  # Flask routes for "Incident Responder" game.
│   │   │   ├── phishing_routes.py  # Flask routes for "Phishing Phrenzy" game.
│   │   │   └── threat_hunter_routes.py  # Flask routes for "Threat Hunter" game.
│   │   ├── info  # Blueprint: Informational endpoints, public forms.
│   │   │   ├── __init__.py  # Initializes `info` Blueprint.
│   │   │   └── contact_form.py  # Flask route for public contact form submissions.
│   │   └── main  # Central Blueprint: Core app logic (users, tests, gamification).
│   │       ├── __init__.py  # Initializes `main` Blueprint.
│   │       ├── achievements_routes.py  # API for fetching achievement definitions/user unlocks.
│   │       ├── blueprint.py  # Instantiation/configuration of the `main` Blueprint object.
│   │       ├── daily_question_routes.py  # API for daily GRC/PBQ question & answers.
│   │       ├── flashcard_routes.py  # API for Cyber Flashcards system (categories, cards, progress).
│   │       ├── leaderboard_routes.py  # API for fetching leaderboard data.
│   │       ├── newsletter_routes.py  # API for public newsletter subscription/unsubscription.
│   │       ├── shop_routes.py  # API for in-app shop (listing, purchasing, equipping items).
│   │       ├── support_routes.py  # API for user-facing "Ask Anything" support chat.
│   │       ├── test_attempt_routes.py  # API for managing user practice test attempts.
│   │       ├── test_routes.py  # API for fetching practice test content/questions.
│   │       ├── unlock.py  # API/logic for unlocking features/content (e.g., based on level/achievements).
│   │       └── user_routes.py  # API for user account management (CRUD, profile, stats, JWT).
│   ├── security  # Top-level package: All security-related modules and features.
│   │   ├── __init__.py  # Initializes `security` 
│   │   ├── admin  # Package: Modules for the secure admin dashboard
│   │   │   ├── __init__.py  # Initializes `admin` .
│   │   │   ├── admin_newsletter_routes.py  # Admin panel routes for newsletter management.
│   │   │   └── admin_routes.py  # Core admin panel API: user/content mgt, analytics, support tickets.
│   │   ├── geoip_db  # Directory for GeoIP database files (MaxMind GeoLite2) for IP geolocation.
│   │   ├── helpers  # Package: Utility functions related to security.
│   │   │   ├── __init__.py  # Initializes `helpers` 
│   │   │   └── unhackable.py  # Custom module: various security utility functions.
│   │   ├── honeypot  # Package: Honeypot system for detecting/deceiving attackers.
│   │   │   ├── C2  # Sub-package: Optional Command & Control module for advanced honeypot scenarios.
│   │   │   │   ├── FOR TESTING PURPOSES ONLY  # Experimental/testing C2 contents.
│   │   │   │   │   └── payloads  # Directory for C2 implant payloads.
│   │   │   │   │       └── security-diagnostic.js  # Example JavaScript payload for C2 implant.
│   │   │   │   ├── __init__.py  # Initializes `C2` 
│   │   │   │   └── c2_routes.py  # Flask routes for C2 server (admin commands) & implant comms.
│   │   │   ├── __init__.py  # Initializes `honeypot
│   │   │   ├── helpers  # Helper modules for the honeypot system.
│   │   │   │   ├── __init__.py  # Initializes `helpers` 
│   │   │   │   ├── geo_db_updater.py  # Script to download/update local GeoIP database files.
│   │   │   │   └── proxy_detector.py  # Logic to detect proxy/TOR IP addresses.
│   │   │   ├── honeypot.py  # Core honeypot logic: request handling, logging to MongoDB.
│   │   │   ├── honeypot_pages.py  # Logic for dynamically serving decoy HTML pages.
│   │   │   ├── honeypot_routes.py  # Flask routes for honeypot triggers & admin analytics.
│   │   │   └── templates  # Jinja2 HTML templates for the honeypot.
│   │   │       ├── honeypot  # Subdirectory: Templates for various fake/decoy pages.
│   │   │       │   ├── admin-dashboard.html  # Decoy: Admin dashboard.
│   │   │       │   ├── admin-login.html  # Decoy: Admin login page.
│   │   │       │   ├── cloud-dashboard.html # Decoy: Cloud service dashboard.
│   │   │       │   ├── cms-dashboard.html # Decoy: CMS dashboard (WordPress, Joomla).
│   │   │       │   ├── cpanel-dashboard.html # Decoy: cPanel dashboard.
│   │   │       │   ├── database-dashboard.html # Decoy: Database admin tool (phpMyAdmin).
│   │   │       │   ├── debug-console.html # Decoy: Debug console page.
│   │   │       │   ├── devops-dashboard.html # Decoy: DevOps tool dashboard (Jenkins).
│   │   │       │   ├── ecommerce-dashboard.html # Decoy: E-commerce admin panel.
│   │   │       │   ├── filesharing-dashboard.html # Decoy: File sharing service page.
│   │   │       │   ├── forum-dashboard.html # Decoy: Forum admin panel.
│   │   │       │   ├── framework-dashboard.html # Decoy: Dashboard for a specific web framework.
│   │   │       │   ├── generic-login.html # Decoy: Generic login page.
│   │   │       │   ├── generic-page.html # Decoy: Generic internal-looking page.
│   │   │       │   ├── iot-dashboard.html # Decoy: IoT device management page.
│   │   │       │   ├── mail-dashboard.html # Decoy: Webmail login/dashboard.
│   │   │       │   ├── mobile-api.html # Decoy: Mobile API documentation/endpoint.
│   │   │       │   ├── monitoring-dashboard.html # Decoy: System monitoring dashboard.
│   │   │       │   ├── phpmyadmin-dashboard.html # Decoy: Specific phpMyAdmin interface.
│   │   │       │   ├── remote-access-dashboard.html # Decoy: Remote access tool page (VNC, RDP).
│   │   │       │   ├── shell.html # Decoy: Fake web shell interface.
│   │   │       │   └── wp-dashboard.html  # Decoy: Specific WordPress admin dashboard.
│   │   │       └── redirection  # Templates: Multi-step fake authentication/redirection sequences.
│   │   │           ├── step1.html # Start of the multi-step decoy redirection/auth sequence.
                            ... (step2.html through step14.html omitted for brevity
│   │   │           └── step15.html # End of the multi-step decoy redirection/auth sequence.
│   │   ├── middleware  # Package: Custom Flask middleware for security processing.
│   │   │   ├── __init__.py  # Initializes `middleware` .
│   │   │   ├── csrf_protection.py  # Flask middleware for CSRF token generation & validation.
│   │   │   ├── jwt_auth.py  # Flask middleware for JWT authentication (token verification).
│   │   │   └── subscription_check.py  # Flask middleware for checking user subscription status.
│   │   ├── proxy_cache  # Directory: Cached lists of known proxy/TOR IP addresses.
│   │   │   ├── proxies.json  # JSON file: List of known proxy server IPs.
│   │   │   └── tor_nodes.json  # JSON file: List of known TOR exit node IPs.
│   │   └── rate_limiters  # Package: API rate limiting logic (using Redis).
│   │       ├── __init__.py  # Initializes `rate_limiters`
│   │       ├── ai_guard.py  # Specific rate limiting logic for AI API calls.
│   │       ├── ai_utils.py  # Utility functions supporting `ai_guard.py`.
│   │       ├── global_rate_limiter.py  # Global rate limits for general API endpoints.
│   │       └── rate_limiter.py  # Core rate limiting class/functions.
│   ├── tasks  # Package: Definitions for Celery asynchronous background tasks.
│   │   ├── __init__.py  # Initializes `tasks` 
│   │   ├── async_tasks.py  # Python functions decorated as Celery tasks (e.g., email sending, complex calculations).
│   │   └── cleanup_tokens.py  # Celery task for periodically cleaning up expired tokens (DB).
│   ├── utils  # Package: General backend utility modules.
│   │   ├── __init__.py  # Initializes `utils` 
│   │   ├── apple_iap_verification.py  # Utilities for verifying Apple In-App Purchase receipts.
│   │   ├── deployment_service.py  # Logic for GitHub/Vercel API interaction (Portfolio Generator).
│   │   └── email_sender.py  # Wrapper/utility for sending emails via SendGrid.
│   └── uwsgi.ini  # Configuration file for uWSGI application server (production Flask deployment).
├── data.md  # Markdown: Documentation for data models, DB schema, data migrations.
├── docker-compose.yml  # Docker Compose: Defines/runs multi-container app in production.
├── docker-compose.yml.dev  # Docker Compose: Defines/runs multi-container app for local development (hot-reloading).
├── frontend  # Root directory for all client-side/frontend code.
│   └── my-react-app  # Root directory of the React SPA
│       ├── craco.config.js  # CRACO: Configuration for overriding Webpack settings without ejecting.
│       ├── eslint.config.mjs  # ESLint: Configuration for JavaScript/React linting
│       ├── ops  # Directory: Operational files for frontend (Dockerfiles).
│       │   ├── Dockerfile.audit  # Dockerfile: For running frontend security audits/linters (CI).
│       │   ├── Dockerfile.dev  # Dockerfile: For building/running frontend dev server (hot-reloading).
│       │   └── Dockerfile.prod  # Dockerfile: For building production static assets of frontend.
│       ├── package-lock.json  # Records exact versions of frontend dependencies for reproducible builds.
│       ├── package.json  # Defines frontend project packages
│       ├── public  # Static assets copied directly to build folder (no Webpack processing).
│       │   ├── assets  # Directory for favicons, PWA icons, manifest.
│       │   │   ├── android-chrome-192x192.png  # PWA icon for Android.
│       │   │   ├── android-chrome-512x512.png  # Larger PWA icon for Android.
│       │   │   ├── apple-touch-icon.png  # Icon for iOS home screen.
│       │   │   ├── favicon-16x16.png  # Small favicon.
│       │   │   ├── favicon-32x32.png  # Larger favicon.
│       │   │   ├── favicon.ico  # Default favicon file.
│       │   │   ├── ios.png  # iOS  image/icon.
│       │   │   └── manifest.json  # Web App Manifest for PWA
│       │   ├── avatars  # avatar images
│       │   │   └── (images...g)  # avatar image files.
│       │   ├── index.html  # Main HTML  file for the React SPA
│       │   ├── robots.txt  # Instructions for web crawlers .
│       │   ├── sitemap.xml  # XML sitemap for search engine optimization
│       │   └── xp  # Directory: Images used for XP.
│       │       └── (images..)  # XP-related image files.
│       └── src  # Main source code directory for the React application.
│           ├── App.js  # Root React component; sets up React Router, main layout (sidebar, content).
│           ├── AppSupport  # Support files for the main application.
│           │   ├── global.css  # Global CSS styles, CSS variables for theming, resets.
│           │   └── reportWebVitals.js  # CRA utility for measuring/reporting Core Web Vitals.
│           ├── api.js  # Axios HTTP client setup: base URL, interceptors (JWT), API call functions.
│           ├── components  # Top-level directory for all React components, organized by feature/type.
│           │   ├── GlobalTest  # Components for a global/unified test-taking interface.
│           │   │   ├── GlobalTestList.js  # Component: Lists available global tests/categories.
│           │   │   └── GlobalTestPage.js  # Main page/component for global test experience.
│           │   ├── SEO  # Components/assets for Search Engine Optimization.
│           │   │   ├── SEOHelmet.js  # Wrapper component (react-helmet) for dynamic head tags.
│           │   │   ├── StructuredData.js  # Component for injecting JSON-LD structured data.
│           │   │   └── og-default.jpg  # Default Open Graph image for social sharing.
│           │   ├── Sidebar  # Components for the main application navigation sidebar.
│           │   │   ├── Sidebar.js  # Main React component for the sidebar.
│           │   │   └── assets  # Assets specific to the Sidebar component.
│           │   │       ├── Sidebar.css  # CSS styles for the Sidebar.
│           │   │       └── sidebarlogo.png  # Logo image displayed in the Sidebar.
│           │   ├── cracked  # All frontend components for the admin dashboard.
│           │   │   ├── CrackedAdminDashboard.js  # Main admin dashboard layout component, renders tabs.
│           │   │   ├── CrackedAdminLoginPage.js  # Login page for administrators.
│           │   │   ├── csrfHelper.js  # Frontend utility for CSRF token handling in admin requests.
│           │   │   ├── modals  # Reusable modal components for the admin panel.
│           │   │   │   ├── ConfirmModal.css  # CSS for the confirmation modal.
│           │   │   │   └── ConfirmModal.js  # Generic confirmation modal component.
│           │   │   ├── styles  # Directory for CSS files styling admin components.
│           │   │   │   ├── CrackedAdminDashboard.css  # Main CSS for admin dashboard.
│           │   │   │   ├── CrackedAdminLogin.css  # CSS for admin login page.
│           │   │   │   └── tabstyles  # Directory: Specific CSS for each admin dashboard tab.
│           │   │   │       ├── ActivityLogsTab.css # Styles for Activity Logs tab.
│           │   │   │       ├── C2Tab.css # Styles for C2 Dashboard tab. (not used)
│           │   │   │       ├── DailyTab.css # Styles for Daily Question Management tab.
│           │   │   │       ├── DbShellTab.css # Styles for Database Shell tab.
│           │   │   │       ├── HealthCheckTab.css # Styles for Health Checks tab.
│           │   │   │       ├── HoneypotTab.css # Styles for Honeypot Analytics tab.
│           │   │   │       ├── HtmlInteractionsTab.css # Styles for HTML Interactions (Honeypot) tab.
│           │   │   │       ├── LogIp.css # Styles for specific IP logging/info components.
│           │   │   │       ├── NewsletterTab.css # Styles for Newsletter Management tab.
│           │   │   │       ├── OverviewTab.css # Styles for Admin Overview tab.
│           │   │   │       ├── PerformanceTab.css # Styles for Application Performance tab.
│           │   │   │       ├── RateLimitsTab.css # Styles for Rate Limit Usage tab.
│           │   │   │       ├── RequestLogsTab.css # Styles for Request Logs tab.
│           │   │   │       ├── RevenueTab.css # Styles for Revenue Analytics tab.
│           │   │   │       ├── ServerMetricsTab.css # Styles for Server Metrics tab.
│           │   │   │       ├── SupportTab.css # Styles for Support Ticket Management tab.
│           │   │   │       ├── TestsTab.css # Styles for Test/Quiz Management tab.
│           │   │   │       ├── ToolsTab.css # Styles for Admin Tools tab.
│           │   │   │       └── UsersTab.css # Styles for User Management tab.
│           │   │   └── tabs  # React components, each representing a tab/section in admin dashboard.
│           │   │       ├── ActivityLogsTab.js  # Component for viewing activity/audit logs.
│           │   │       ├── C2Tab.js  # Component for interacting with the C2 honeypot module (not used)
│           │   │       ├── DailyTab.js  # Component for managing daily GRC/PBQ questions.
│           │   │       ├── DbShellTab.js  # Component providing a read-only DB shell for superadmins.
│           │   │       ├── HealthChecksTab.js  # Component for viewing API/DB health check status.
│           │   │       ├── HoneypotTab.js  # Component for viewing honeypot analytics and logs.
│           │   │       ├── HtmlInteractionsTab.js # Component for viewing specific HTML honeypot page interactions.
│           │   │       ├── LogIp.js # Component for logging/displaying specific IP address information/activity.
│           │   │       ├── NewsletterTab.js  # Component for managing newsletter campaigns.
│           │   │       ├── OverviewTab.js  # Component for the main admin dashboard overview/stats.
│           │   │       ├── PerformanceTab.js  # Component for viewing app performance metrics (backend/frontend).
│           │   │       ├── RateLimitsTab.js  # Component for viewing current rate limit usage.
│           │   │       ├── RequestLogsTab.js  # Component for viewing Nginx/API request logs.
│           │   │       ├── RevenueTab.js  # Component for viewing revenue and subscription analytics.
│           │   │       ├── ServerMetricsTab.js  # Component for viewing server resource usage (CPU, memory).
│           │   │       ├── SupportTab.js  # Component for managing user support tickets.
│           │   │       ├── TestsTab.js  # Component for managing (CRUD) practice tests/quizzes.
│           │   │       ├── ToolsTab.js  # Component for various admin tools or utilities.
│           │   │       └── UsersTab.js  # Component for managing users (list, update, delete, toggle sub).
│           │   ├── css  # Directory: General/reusable CSS files not tied to a specific large component/page.
│           │   │   ├── QuestionLimitBanner.css  # Styles for banner: free-tier question usage limits.
│           │   │   ├── UpgradePrompt.css  # Styles for UI elements prompting users to upgrade.
│           │   │   ├── footer.css  # CSS styles for the main application footer.
│           │   │   └── test.css  # General CSS styles for the test-taking interface components.
│           │   ├── pages  # pages
│           │   │   ├── AchievementPage  # Components for displaying user achievements.
│           │   │   │   ├── AchievementPage.js  # Main component for the achievements page.
│           │   │   │   └── assets  # Assets for AchievementPage.
│           │   │   │       ├── AchievementPage.css  # CSS for achievements page.
│           │   │   │       ├── AchievementToast.css  # CSS for achievement unlock notification.
│           │   │   │       └── AchievementToast.js  # React component for achievement unlock toast.
│           │   │   ├── AnalogyPage  # UI components for the "Analogy Hub" AI tool.
│           │   │   │   ├── AnalogyHub.js  # Main component for interacting with Analogy Hub.
│           │   │   │   └── assets  # Assets for AnalogyPage.
│           │   │   │       ├── AnalogyHub.css  # CSS for Analogy Hub page.
│           │   │   │       ├── backround1.jpg  # Background image for Analogy Hub.
│           │   │   │       └── loading2.png  # Loading indicator image.
│           │   │   ├── DailyPage  # Components related to daily content features.
│           │   │   │   ├── DailyCyberBrief.js  # Component to display the Daily Cyber Brief news/tips.
│           │   │   │   └── assets  # Assets for DailyPage.
│           │   │   │       └── DailyCyberBrief.css  # CSS for DailyCyberBrief component.
│           │   │   ├── DailyStation  # UI for "Daily Station" - hub for daily activities.
│           │   │   │   ├── DailyStationPage.js  # Main page for Daily Station (bonus, daily question, brief).
│           │   │   │   └── assets  # Assets for DailyStation.
│           │   │   │       ├── DailyStation.css  # CSS for DailyStation page.
│           │   │   ├── GRCpage  # UI components for the "GRC Wizard" AI tool.
│           │   │   │   ├── GRC.js  # Main component for GRC Wizard.
│           │   │   │   └── assets  # Assets for GRCpage.
│           │   │   │       └── GRC.css  # CSS for GRC Wizard page.
│           │   │   ├── Info  # Components for public-facing informational pages (marketing, blog, etc.).
│           │   │   │   ├── BlogPage.js  # Component for listing blog posts.
│           │   │   │   ├── BlogPostPage.js  # Component for displaying a single blog post.
│           │   │   │   ├── ContactPage.js  # Component for the public contact form page.
│           │   │   │   ├── DemosPage.js  # Component showcasing platform features/demos.
│           │   │   │   ├── ExamsPage.js  # Component providing info about supported certifications.
│           │   │   │   ├── InfoPage.js  # Main landing/marketing page for CertGames.
│           │   │   │   ├── PublicLeaderboardPage.js  # Component for the publicly accessible leaderboard.
│           │   │   │   ├── components  # Sub-components used within the Info pages.
│           │   │   │   │   ├── InfoNavbar.js  # Navigation bar for the public/info pages.
│           │   │   │   │   ├── YouTubeEmbed.js  # Component for embedding YouTube videos.
│           │   │   │   │   ├── navbarScrollUtils.js  # JS utilities for navbar scroll behavior.
│           │   │   │   │   └── videoConfig.js  # Configuration for embedded videos.
│           │   │   │   ├── css  # CSS files for the Info pages.
│           │   │   │   │   ├── BlogPage.css
│           │   │   │   │   ├── ContactPage.css
│           │   │   │   │   ├── DemosPage.css
│           │   │   │   │   ├── ExamsPage.css
│           │   │   │   │   ├── InfoNavbar.css
│           │   │   │   │   ├── InfoPage.css
│           │   │   │   │   └── PublicLeaderboardPage.css
│           │   │   │   └── images  # Image assets used in public pages.
│           │   │   │       └── (alot of images...)  # numerous marketing images.
│           │   │   ├── LeaderboardPage  # Components for the internal user leaderboard.
│           │   │   │   ├── LeaderboardPage.js  # Main component for internal leaderboard.
│           │   │   │   └── assets  # Assets for LeaderboardPage.
│           │   │   │       └── LeaderboardPage.css  # CSS for internal leaderboard.
│           │   │   ├── Legal  # Components for legal pages (Privacy Policy, Terms of Service).
│           │   │   │   ├── PrivacyPolicy.js  # Component for displaying the Privacy Policy.
│           │   │   │   ├── TermsOfService.js  # Component for displaying the Terms of Service.
│           │   │   │   └── assets  # Assets for Legal pages.
│           │   │   │       └── LegalPages.css  # CSS for legal pages.
│           │   │   ├── Portfolio  # UI components for the AI Portfolio Generator feature.
│           │   │   │   ├── PortfolioPage.js  # Main page for creating/managing portfolios.
│           │   │   │   └── assets  # Assets and sub-components for Portfolio feature.
│           │   │   │       ├── CodeEditor.js  # React component wrapping Monaco Editor for code editing.
│           │   │   │       ├── DeploymentMonitor.js  # Component to monitor portfolio deployment status.
│           │   │   │       ├── PortfolioDeployment.js  # Component handling deployment UI/logic.
│           │   │   │       ├── PortfolioForm.js  # Form for user input (resume, preferences).
│           │   │   │       ├── PortfolioList.js  # Component to list user's generated portfolios.
│           │   │   │       ├── PortfolioPreview.js  # Component to preview generated portfolio.
│           │   │   │       └── portfolio.css  # CSS for Portfolio Generator pages.
│           │   │   ├── ResourcesPage  # UI for the curated Resource Library.
│           │   │   │   ├── Resources.js  # Main component for displaying resources.
│           │   │   │   └── assets  # Assets for ResourcesPage.
│           │   │   │       └── Resources.css  # CSS for Resources page.
│           │   │   ├── ScenarioPage  # UI components for the "ScenarioSphere" AI tool.
│           │   │   │   ├── ScenarioSphere.js  # Main component for ScenarioSphere.
│           │   │   │   └── assets  # Assets for ScenarioPage.
│           │   │   │       ├── ScenarioSphere.css  # CSS for ScenarioSphere.
│           │   │   │       └── attacks.js  # JS file listing attack types for ScenarioSphere.
│           │   │   ├── ShopPage  # UI for the in-app virtual goods shop.
│           │   │   │   ├── ShopPage.js  # Main component for displaying shop items and handling purchases.
│           │   │   │   └── assets  # Assets for ShopPage.
│           │   │   │       ├── ShopPage.css  # CSS for Shop page.
│           │   │   ├── StatsPage  # UI for displaying user's performance statistics and progress.
│           │   │   │   ├── StatsPage.js  # Main component for user stats page.
│           │   │   │   └── assets  # Assets for StatsPage.
│           │   │   │       └── StatsPage.css  # CSS for Stats page.
│           │   │   ├── SupportPage  # UI for the "Ask Anything" user support chat system.
│           │   │   │   ├── SupportAskAnythingPage.js  # Main component for support chat interface.
│           │   │   │   └── assets  # Assets for SupportPage.
│           │   │   │       └── SupportAskAnythingPage.css  # CSS for support chat page.
│           │   │   ├── UserPage  # UI for user profile management.
│           │   │   │   ├── UserProfile.js  # Main component for viewing/editing user profile.
│           │   │   │   └── assets  # Assets for UserPage.
│           │   │   │       ├── UserProfile.css  # CSS for user profile page.
│           │   │   │       └── validationUtils.js  # JS utilities for form validation on profile page.
│           │   │   ├── XploitcraftPage  # UI components for the "XploitCraft" AI tool.
│           │   │   │   ├── Xploitcraft.js  # Main component for XploitCraft.
│           │   │   │   └── assets  # Assets for XploitcraftPage.
│           │   │   │       ├── Xploitcraft.css  # CSS for XploitCraft page.
│           │   │   │       ├── backround2.jpg  # Background image.
│           │   │   │       ├── evasionTechniquesList.js  # JS: List of evasion techniques for XploitCraft.
│           │   │   │       ├── loading3.png  # Loading indicator image.
│           │   │   │       ├── logo5.png  # Logo image.
│           │   │   │       └── vulnerabilitiesList.js  # JS: List of vulnerabilities for XploitCraft.
│           │   │   ├── auth  # Components for user authentication pages (login, registration, etc.).
│           │   │   │   ├── CreateUsernameForm.js  # Form for users (e.g., OAuth users) to set a username.
│           │   │   │   ├── ErrorDisplay.js  # Reusable component for displaying error messages.
│           │   │   │   ├── ForgotPassword.js  # Page/component for "forgot password" flow.
│           │   │   │   ├── Login.js  # Login page/component.
│           │   │   │   ├── OAuthSuccess.js  # Page/component to handle redirection after successful OAuth.
│           │   │   │   ├── PasswordRequirements.js  # Component displaying password strength requirements.
│           │   │   │   ├── Register.js  # Registration page/component.
│           │   │   │   ├── ResetPassword.js  # Page/component for resetting password using a token.
│           │   │   │   └── css  # CSS files for authentication pages.
│           │   │   │       ├── CreateUsernameForm.css
│           │   │   │       ├── ErrorDisplay.css
│           │   │   │       ├── ForgotPassword.css
│           │   │   │       ├── Login.css
│           │   │   │       ├── PasswordRequirements.css
│           │   │   │       ├── Register.css
│           │   │   │       └── ResetPassword.css
│           │   │   ├── common  # Reusable, generic UI components used across the application.
│           │   │   │   ├── ErrorMessage.js  # A common component for displaying error messages.
│           │   │   │   ├── LoadingSpinner.js  # A common loading spinner component.
│           │   │   │   └── common.css  # CSS for these common components.
│           │   │   ├── games  # UI components for the various interactive cybersecurity games.
│           │   │   │   ├── CipherChallenge  # Components for "Cipher Challenge" game.
│           │   │   │   │   ├── CipherChallenge.js  # Main component for Cipher Challenge game.
│           │   │   │   │   └── assets  # Assets and sub-components for Cipher Challenge.
│           │   │   │   │       ├── CipherDisplay.js # Displays cipher text.
│           │   │   │   │       ├── CipherHints.js # Handles hint display/unlock.
│           │   │   │   │       ├── CipherInfoModal.js # Modal with info about current cipher.
│           │   │   │   │       ├── CipherInput.js # Input field for solution.
│           │   │   │   │       ├── CipherTools.js # UI for cipher tools (e.g., frequency analysis).
│           │   │   │   │       ├── CongratulationsModal.js # Modal on successful completion.
│           │   │   │   │       ├── LevelSelector.js # Component to select game level/challenge.
│           │   │   │   │       └── css # CSS files for Cipher Challenge components.
│           │   │   │   ├── IncidentResponder  # Components for "Incident Responder" game.
│           │   │   │   │   ├── IncidentResponder.js  # Main component for Incident Responder game.
│           │   │   │   │   └── assets  # Assets and sub-components for Incident Responder.
│           │   │   │   │       ├── DifficultySelector.js # Select game difficulty.
│           │   │   │   │       ├── GameInstructions.js # Displays game instructions.
│           │   │   │   │       ├── ScenarioIntro.js # Displays introduction to a scenario.
│           │   │   │   │       ├── ScenarioResults.js # Displays results after scenario completion.
│           │   │   │   │       ├── ScenarioStage.js # Component for a single stage/decision point.
│           │   │   │   │       ├── css # CSS files for Incident Responder.
│           │   │   │   │       └── theme.mp3 # Background music/theme for the game.
│           │   │   │   ├── PhishingPhrenzy  # Components for "Phishing Phrenzy" game.
│           │   │   │   │   ├── PhishingPhrenzy.js  # Main component for Phishing Phrenzy game.
│           │   │   │   │   └── assets  # Assets and sub-components for Phishing Phrenzy.
│           │   │   │   │       ├── GameOverModal.js # Modal displayed at game over.
│           │   │   │   │       ├── PhishingCard.js # Component to display a single phishing example.
│           │   │   │   │       ├── cardTypeNames.js # JS mapping for card types.
│           │   │   │   │       └── css # CSS files for Phishing Phrenzy (many card styles).
│           │   │   │   └── ThreatHunter  # Components for "Threat Hunter" game.
│           │   │   │       ├── ThreatHunter.js  # Main component for Threat Hunter game.
│           │   │   │       └── assets  # Assets and sub-components for Threat Hunter.
│           │   │   │           ├── AnalysisTools.js # UI for log analysis tools.
│           │   │   │           ├── GameInstructions.js # (Shared name, specific to this game)
│           │   │   │           ├── LogViewer.js # Component for displaying log data.
│           │   │   │           ├── ScenarioSelector.js # Select log analysis scenario.
│           │   │   │           ├── ThreatControls.js # UI for game controls/submission.
│           │   │   │           ├── ThreatResultsModal.js # Modal for displaying analysis results.
│           │   │   │           └── css # CSS files for Threat Hunter.
│           │   │   ├── ios  # Components for legal pages specifically shown within the iOS app context.
│           │   │   │   ├── PrivacyPolicyIOS.js  # Privacy Policy tailored for iOS.
│           │   │   │   ├── TermsOfServiceIOS.js  # Terms of Service tailored for iOS.
│           │   │   │   └── assets  # Assets for iOS legal pages.
│           │   │   │       └── AppleLegalPages.css  # CSS for iOS legal pages.
│           │   │   ├── store  # Redux Toolkit global state management setup.
│           │   │   │   ├── slice  # Directory for feature-specific Redux slices.
│           │   │   │   │   ├── achievementsSlice.js  # Redux slice for achievements state.
│           │   │   │   │   ├── cipherChallengeSlice.js  # Redux slice for Cipher Challenge game state.
│           │   │   │   │   ├── incidentResponderSlice.js  # Redux slice for Incident Responder game state.
│           │   │   │   │   ├── phishingPhrenzySlice.js  # Redux slice for Phishing Phrenzy game state.
│           │   │   │   │   ├── shopSlice.js  # Redux slice for shop items and user purchases.
│           │   │   │   │   ├── threatHunterSlice.js  # Redux slice for Threat Hunter game state.
│           │   │   │   │   └── userSlice.js  # Redux slice for user profile, auth status, XP, coins, etc.
│           │   │   │   └── store.js  # Root Redux store configuration, combining all slices.
│           │   │   ├── subscription  # Components related to user subscription management.
│           │   │   │   ├── StripeCheckout.js  # Component integrating Stripe Checkout for web payments.
│           │   │   │   ├── SubscriptionCancel.js  # Page/component confirming subscription cancellation.
│           │   │   │   ├── SubscriptionPage.js  # Page for viewing/managing subscription, upgrading.
│           │   │   │   ├── SubscriptionSuccess.js  # Page/component shown after successful payment.
│           │   │   │   └── css  # CSS files for subscription pages.
│           │   │   └── tests  # UI components for the practice test-taking interfaces, organized by certification.
│           │   │       ├── aplus  # CompTIA A+ Core 1 test components.
│           │   │       │   ├── APlusTestList.js  # Lists A+ Core 1 practice tests.
│           │   │       │   └── APlusTestPage.js  # Main test interface for A+ Core 1.
│           │   │       ├── aplus2  # CompTIA A+ Core 2 test components.
│           │   │       │   ├── APlusCore2TestPage.js
│           │   │       │   └── AplusCore2TestList.js
│           │   │       ├── awscloud  # AWS Cloud Practitioner test components.
│           │   │       │   ├── AWSCloudTestList.js
│           │   │       │   └── AWSCloudTestPage.js
│           │   │       ├── casp  # CompTIA CASP+ test components.
│           │   │       │   ├── CaspPlusTestList.js
│           │   │       │   └── CaspPlusTestPage.js
│           │   │       ├── cissp  # ISC2 CISSP test components.
│           │   │       │   ├── CisspTestList.js
│           │   │       │   └── CisspTestPage.js
│           │   │       ├── cloudplus  # CompTIA Cloud+ test components.
│           │   │       │   ├── CloudPlusTestList.js
│           │   │       │   └── CloudPlusTestPage.js
│           │   │       ├── cysa  # CompTIA CySA+ test components.
│           │   │       │   ├── CySAPlusTestList.js
│           │   │       │   └── CySAPlusTestPage.js
│           │   │       ├── dataplus  # CompTIA Data+ test components.
│           │   │       │   ├── DataPlusTestList.js
│           │   │       │   └── DataPlusTestPage.js
│           │   │       ├── linuxplus  # CompTIA Linux+ test components.
│           │   │       │   ├── LinuxPlusTestList.js
│           │   │       │   └── LinuxPlusTestPage.js
│           │   │       ├── nplus  # CompTIA Network+ test components.
│           │   │       │   ├── NPlusTestList.js
│           │   │       │   └── NetworkPlusTestPage.js
│           │   │       ├── penplus  # CompTIA PenTest+ test components.
│           │   │       │   ├── PenPlusTestList.js
│           │   │       │   └── PenPlusTestPage.js
│           │   │       ├── secplus  # CompTIA Security+ test components.
│           │   │       │   ├── SecurityPlusTestList.js
│           │   │       │   └── SecurityPlusTestPage.js
│           │   │       └── serverplus  # CompTIA Server+ test components.
│           │   │           ├── ServerPlusTestList.js
│           │   │           └── ServerPlusTestPage.js
│           │   └── utils  # Common utility React components and JavaScript helper functions.
│           │       ├── Footer.js  # Reusable Footer component for the application.
│           │       ├── FormattedQuestion.js  # Component to format and display test questions (e.g., handling markdown or special formatting).
│           │       ├── ProtectedRoute.js  # Higher-order component or wrapper to protect routes that require authentication. (defense in depth)
│           │       ├── QuestionDropdown.js  # A dropdown component, possibly for selecting question categories or test options.
│           │       ├── QuestionLimitBanner.js  # Component for displaying the free-tier question limit banner.
│           │       ├── ScrollToTop.js  # Utility component to scroll to the top of the page on route changes.
│           │       ├── SubscriptionErrorHandler.js # Component or hook to handle subscription-related errors.
│           │       ├── UpgradePrompt.js  # Reusable component to prompt users to upgrade their subscription.
│           │       ├── colorMapping.js  # JS module mapping semantic names to color codes (for theming).
│           │       ├── iconMapping.js  # JS module mapping identifiers to specific icons (from React Icons).
│           │       └── rIcons.js  # .to reduce imports from multiple icon libraries (e.g., FontAwesome, Simple Icons, Feather Icons) into a single, combined import
│           └── index.js  # The main entry point 
├── nginx  # Directory containing NGINX web server configuration files.
│   ├── logs  # Directory where NGINX access and error logs are stored
│   │   ├── access.log  # NGINX access log file.
│   │   └── error.log  # NGINX error log file.
│   ├── nginx.conf  # Main NGINX configuration file (global settings, http block).
│   ├── sites-enabled  # Directory for enabled NGINX site configurations.
│   │   └── proxy.conf  # Specific NGINX site configuration for CertGames production: server blocks, location directives for serving static frontend, proxying API/WebSocket requests to backend, security headers.
│   └── sites-enabled-dev  # NGINX site configurations specifically for development.
│       └── proxy-dev.conf  # Development NGINX proxy configuration.
└── redis  # Directory containing Redis server configuration.
    └── redis.conf  # Redis configuration file
```

**IX. Challenges & Learnings**

*   **Gamification Depth vs. Performance:** The most significant challenge was implementing a truly deep gamification system (tracking many user stats, complex achievement criteria) without bogging down the user experience. This involved careful data modeling in MongoDB (e.g., embedding counters in user docs), optimizing queries with appropriate indexes, and judiciously using Celery for heavier background computations related to achievement unlocks.
*   **State Management at Scale (React/Redux):** With numerous interactive elements, dynamic UI themes, user stats, and game states, managing client-side state effectively with Redux Toolkit was crucial. Structuring slices logically and using selectors efficiently helped maintain performance and code sanity.
*   **Real-time Feedback with Flask-SocketIO & uWSGI/Gevent:** Getting Flask-SocketIO to work seamlessly across multiple uWSGI/Gevent workers required careful configuration and robust use of Redis as the message queue to ensure broadcasts reached all relevant client sessions.
*   **Security Posture for a Cybersecurity Platform:** Building a platform *about* cybersecurity meant holding myself to a high standard. Implementing the honeypot, comprehensive security headers, rate limiting, and CSRF protection was as much a learning exercise as it was a feature set.
*   **Solo Developer Scope:** Managing the breadth of this full-stack project solo – from frontend UX to backend architecture, database design, CI/CD, and security – has been incredibly demanding but also immensely rewarding in terms of learning.


Cheers! (yes AI 'obviously' helped me write this, its 2025...)
