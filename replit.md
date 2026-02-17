# replit.md

## Overview

This is a full-stack web application built with a React frontend and Express backend. The website serves as a landing page for a Telegram dating bot, showcasing features, live statistics, and a call-to-action to open the bot. The bot itself runs as a separate Python process.

The codebase uses TypeScript throughout, with a monorepo-style structure separating client, server, and shared code.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Routing**: Wouter (lightweight router)
- **State Management**: TanStack React Query for server state
- **UI Components**: shadcn/ui component library built on Radix UI primitives
- **Styling**: Tailwind CSS with CSS variables for theming
- **Build Tool**: Vite with HMR support

The frontend lives in `client/src/` with the following structure:
- `pages/` - Route components (Home, not-found)
- `components/ui/` - Reusable shadcn/ui components
- `hooks/` - Custom React hooks including data fetching hooks
- `lib/` - Utilities including query client configuration

### Backend Architecture
- **Framework**: Express 5 on Node.js
- **Language**: TypeScript with ESM modules
- **Build**: esbuild for production bundling

The server lives in `server/` with:
- `index.ts` - Main entry point, server setup
- `routes.ts` - API route definitions
- `storage.ts` - Data access layer abstraction
- `db.ts` - Database connection using Drizzle ORM
- `vite.ts` - Development server integration with Vite

### Shared Code
Located in `shared/`:
- `schema.ts` - Database schema definitions using Drizzle ORM with PostgreSQL
- `routes.ts` - API route type definitions shared between client and server

### Data Storage
- **ORM**: Drizzle ORM configured for PostgreSQL
- **Schema Location**: `shared/schema.ts`
- **Migrations**: Output to `./migrations` directory
- **Connection**: Requires `DATABASE_URL` environment variable

### Telegram Dating Bot (Python)
The `bot/` directory contains a fully functional Telegram dating bot built with aiogram 3.x:

**Structure:**
- `main.py` - Entry point with dispatcher setup and polling
- `db.py` - SQLite database with users, likes, matches, blocks, comments, tracking tables
- `handlers/` - Message and callback handlers:
  - `registration.py` - /start handler, menus for men and girls, all inline callback handlers
  - `profile.py` - View/edit profile (/profile)
  - `search.py` - Find matches (/search, /stats), profile display with track/comment buttons
  - `matching.py` - Match notifications (/matches, /likes)
  - `chats.py` - Chat management (/chats, /blocked)
  - `admin.py` - Admin commands, adding fake girl profiles with is_girl flag
  - `gifts.py` - Telegram Stars gifting
- `keyboards/` - Reply and inline keyboards
- `states/` - FSM states: Registration, EditProfile, FilterState, CommentState

**User Roles:**
- Men (clients): Auto-registered on /start with city "астрахань". Menu: Browse girls, My tracked, Filters, Chats, Profile, Help.
- Girls (admin-added, is_girl=1): Menu: Edit profile, Photos/videos, Services & prices, Schedule/online, Followers/likes, Stats.
- Role check uses `is_girl` flag (set by admin when adding profiles).

**Features:**
- Men browse girl profiles with Like/Gift/Skip/Track/Comment buttons
- Tracking system: men can follow girls and see their online status
- Comments: men leave reviews on girl profiles
- Girl features: services/prices, schedule, online toggle, follower stats
- Search by city with age filters (min/max)
- 5 sec cooldown, 50/hour limit
- Like/Skip with match notifications
- Block/unblock users
- Admin: stats, ban, unban, broadcast, add girl profiles, manage multiple girl profiles
- Admin profile management (/girls): edit name, age, city, bio, photo, services, prices, schedule, auto-online, parameters (breast/height/weight), view chats per girl
- managed_by column links girl profiles to admin account; admin_add auto-sets managed_by
- In-bot relay chat: client messages forwarded to admin (managed_by) with label "Анкета {name} — сообщение от клиента {client}", admin replies sent as the girl
- bot_chats and bot_messages tables for relay messaging
- Chat created automatically on "Написать" (like) action
- Girls see "Чаты с клиентами" in their menu
- Profile card redesigned: compact header (name/age/city), body stats, price summary, online badge, emoji buttons (Услуги, Написать, Пропустить, Отзывы)

**Environment variables:**
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `ADMIN_USER_ID` - Your Telegram user ID for admin access

**Run:** `python3 bot/main.py`

### API Structure
Routes are defined in `shared/routes.ts` with Zod validation:
- `GET /api/greeting` - Returns a greeting message
- `GET /api/bot-stats` - Returns live bot statistics (totalUsers, totalGirls, totalMen, activeChats, onlineNow) read from bot SQLite DB (bot.db or bot/dating_bot.db)

The pattern uses typed route definitions that can be consumed by both frontend hooks and backend handlers.

### Landing Page
- **Theme**: Pink/purple (primary: 330 80% 55%, accent: 270 60% 55%) with dark mode support
- **Sections**: Hero, animated stats counter, features for men (6 cards), features for girls (6 cards), how it works (4 steps), service catalog (9 categories), security, CTA
- **SEO**: Title, meta description, Open Graph tags in index.html
- **Bot link**: Placeholder `https://t.me/your_bot_username` — needs real bot username

## External Dependencies

### Database
- **PostgreSQL** - Primary database (requires DATABASE_URL environment variable)
- **Drizzle ORM** - Type-safe database queries and migrations
- **connect-pg-simple** - PostgreSQL session store

### Frontend Libraries
- **@tanstack/react-query** - Data fetching and caching
- **Radix UI** - Accessible component primitives (extensive set including dialogs, menus, forms)
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Development server and build tool
- **Zod** - Schema validation (shared between frontend and backend)

### Backend Libraries
- **Express 5** - Web framework
- **express-session** - Session management
- **drizzle-zod** - Zod schema generation from Drizzle schemas

### Development Tools
- **TypeScript** - Type checking
- **esbuild** - Production bundling for server
- **drizzle-kit** - Database migration tooling

### Docker Deployment
- **Dockerfile** - Multi-stage build: Node.js builder + Python venv, production image with both runtimes
- **docker-compose.yml** - Three services: app (Node+Bot), db (PostgreSQL 16), nginx (reverse proxy)
- **nginx.conf** - Reverse proxy config, replace `your-domain.com` with actual domain
- **.env.example** - Template for all required environment variables
- **.dockerignore** - Excludes node_modules, dist, .git, databases, Python caches
- **bot/requirements.txt** - Python dependencies: aiogram, aiohttp, aiofiles, python-dotenv

### Replit-Specific
- **@replit/vite-plugin-runtime-error-modal** - Error overlay
- **@replit/vite-plugin-cartographer** - Dev tooling (development only)
- **@replit/vite-plugin-dev-banner** - Dev banner (development only)