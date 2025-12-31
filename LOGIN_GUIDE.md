# Login Guide

## How to Access the Frontend

1. **Start the application** (if not already running):
   ```bash
   docker-compose up -d
   ```

2. **Access the frontend**:
   - Open your browser and navigate to: `http://localhost:3000`
   - You will be automatically redirected to the login page if you're not authenticated

3. **Create an account**:
   - Click on "create a new account" link on the login page
   - Or navigate directly to: `http://localhost:3000/register`
   - Enter your email and password
   - Click "Sign up"

4. **Login**:
   - Navigate to: `http://localhost:3000/login`
   - Enter your email and password
   - Click "Sign in"

## Authentication Flow

- The main page (`/`) is protected and requires authentication
- If you're not logged in, you'll be automatically redirected to `/login`
- After successful login, you'll be redirected to the main dashboard
- Your session is stored in localStorage and persists across page refreshes

## API Authentication

All API requests to `/api/reconcile` and other protected endpoints require a JWT token:
- The token is automatically included in requests from the frontend
- Tokens expire after the configured time (default: 30 minutes)
- Refresh tokens are used to get new access tokens automatically

## Troubleshooting

### Can't see the login page?
- Make sure the frontend is running: `docker-compose ps`
- Check frontend logs: `docker logs financial-reconciliation-frontend`

### Login fails?
- Verify the backend is running: `docker-compose ps`
- Check backend logs: `docker logs financial-reconciliation-backend`
- Ensure the database is accessible and migrations are run

### Database not storing records?
- Verify database connection: Check `DATABASE_URL` in `.env`
- Run migrations: `alembic upgrade head`
- Check database logs: `docker logs <database-container>` (if using Docker)





