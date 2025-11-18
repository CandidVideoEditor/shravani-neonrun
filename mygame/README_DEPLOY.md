1. Push this folder to GitHub.

2. Create a Replit project (Python / Flask) or use Replit's import from GitHub.

3. Set environment variables in Replit Secrets:
   - GOOGLE_CLIENT_ID   (from Google Cloud Console)
   - GOOGLE_CLIENT_SECRET
   - APP_SECRET         (random string)
   - BASE_URL           (e.g., https://<your-repl>.repl.co)  -- ensure redirect URI in Google console matches BASE_URL + /authorize

4. In Google Cloud Console:
   - Create OAuth 2.0 Client ID (Web application).
   - Add authorized redirect URI:  <BASE_URL>/authorize
   - Set allowed origins as needed.

5. In Replit, install requirements: `pip install -r requirements.txt`
   Or let Replit auto-install from requirements.txt.

6. Start the app: `python app.py` (Replit should expose the PORT automatically).

7. Visit the site, sign-in with Google. On first sign-in you'll be prompted to choose a unique username.

8. Replace placeholder assets under `static/assets/` with premium images/spritesheets and sounds. Update game.js to use your spritesheet frames if necessary.

Notes:
- The app requires that Google reports the email as verified. If you test with accounts that are not verified, Google won't allow play.
- Username uniqueness is enforced in SQLite.
