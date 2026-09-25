# Technical Specification Document

## 1. System Architecture
- **Language:** Python 3
- **Framework:** Flask (RESTful API architecture)
- **Database:** SQLite3 (`tickets.db`)
- **Frontend:** HTML5, CSS3, Modern JavaScript (Fetch API)

## 2. Database Schema

### `users` Table
Stores account information and access roles.
- `id` (INTEGER, Primary Key, Autoincrement)
- `username` (TEXT, Unique, Not Null)
- `password` (TEXT, Not Null)
- `role` (TEXT, Allowed: 'Admin', 'Requestor', 'Developer')

### `tickets` Table
Stores ticket information, assignments, and notifications.
- `id` (INTEGER, Primary Key, Autoincrement)
- `title` (TEXT, Not Null)
- `description` (TEXT, Not Null)
- `status` (TEXT, Default: 'Open')
- `requestor_id` (INTEGER, Foreign Key -> `users.id`)
- `assigned_to` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `notifications` (TEXT, Default: '')

## 3. API Endpoints

| Endpoint | Method | Payload / Parameters | Description |
| :--- | :--- | :--- | :--- |
| `/api/register` | `POST` | `{ username, password, role }` | Registers a new user account. |
| `/api/login` | `POST` | `{ username, password }` | Authenticates a user and returns role/ID. |
| `/api/reset-password` | `PUT` | `{ username, new_password }` | Updates password for a given username. |
| `/api/tickets` | `POST` | `{ title, description, requestor_id }` | Creates a new support ticket. |
| `/api/tickets/assign` | `PUT` | `{ ticketId, developerId }` | Assigns a ticket to a developer and logs notification. |
| `/api/tickets/resolve` | `PUT` | `{ ticketId }` | Marks ticket status as 'Resolved' and updates notification. |
| `/api/tickets` | `GET` | *None* | Fetches all system tickets. |