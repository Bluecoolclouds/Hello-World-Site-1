# replit.md

## Overview

This is a full-stack web application built with a React frontend and Express backend. The project appears to be a starter template that currently displays a simple greeting message ("Привет, Мир" / "Hello World"). Based on attached assets, the intended direction is to build a Telegram dating bot with user registration, profile management, matching, and messaging features.

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
- `db.py` - SQLite database with users, likes, matches, blocks tables
- `handlers/` - Message and callback handlers:
  - `registration.py` - User registration flow (/start)
  - `profile.py` - View/edit profile (/profile)
  - `search.py` - Find matches (/search, /stats)
  - `matching.py` - Match notifications (/matches, /likes)
  - `chats.py` - Chat management (/chats, /blocked)
  - `admin.py` - Admin commands (/admin_stats, /admin_ban, /admin_unban)
- `keyboards/` - Reply and inline keyboards
- `states/` - FSM states for registration

**Features:**
- Search by city + gender preferences
- 5 sec cooldown, 50/hour limit
- Like/Skip with match notifications
- Block/unblock users
- Admin: stats, ban, unban, broadcast

**Environment variables:**
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `ADMIN_USER_ID` - Your Telegram user ID for admin access

**Run:** `python3 bot/main.py`

### API Structure
Routes are defined in `shared/routes.ts` with Zod validation:
- `GET /api/greeting` - Returns a greeting message

The pattern uses typed route definitions that can be consumed by both frontend hooks and backend handlers.

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

### Replit-Specific
- **@replit/vite-plugin-runtime-error-modal** - Error overlay
- **@replit/vite-plugin-cartographer** - Dev tooling (development only)
- **@replit/vite-plugin-dev-banner** - Dev banner (development only)