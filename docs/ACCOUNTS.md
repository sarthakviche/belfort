# Accounts and sync

Accounts are optional. Without them Belfort is local only, exactly as before. With them, a user's paper account, journal, learning progress and settings follow them between Windows and Android. Built in T43.

## Turning accounts on (maintainers, once)

1. Create a Supabase project (supabase.com). Keep the **service-role key** private; Belfort never uses it.
2. In the project's SQL editor, run `supabase/migrations/20261128000000_user_state.sql`. It creates:
   - the `user_state` table
   - row-level security (each user can read and write only their own rows)
   - a trigger that sets `updated_at` from the server clock
   - `delete_my_account()`
3. Authentication, then Providers:
   - Keep **Email** on.
   - For **Google**, add a Google OAuth client ID and secret.
4. Authentication, then URL configuration, then Redirect URLs: add `http://127.0.0.1:*/auth/callback` and `http://localhost:*/auth/callback` (the desktop app's local server), and the Android app link when T48 ships.
5. Put the project URL and the **anon** key in `.env` (see `.env.example`):
   ```
   SUPABASE_URL=https://<project>.supabase.co
   SUPABASE_ANON_KEY=<anon key>
   ```
   The anon key is safe to ship in the app, because row-level security is what protects the data. Never put either value in a commit.

Free Supabase projects pause after about a week without traffic. For a public release, someone must own the project and keep it active or on a paid plan.

Accounts switch themselves off when `ACCESS_CODES` is set. One running app has one signed-in user, so sharing it on a network would share the account.

## How it works

| Piece | Where |
|---|---|
| Sign-in, sign-up, Google (PKCE), token refresh, sign-out, account deletion | `belfort/core/auth.py` (the only module that knows the provider) |
| Who the current user is | `belfort/core/users.py::current_user_id()` |
| Per-user data | `belfort/core/db.py::path_for()`: the local user keeps `belfort.db`, and each signed-in user gets `users/<user id>.db` |
| Sync | `belfort/core/sync.py`, on sign-in, every minute while signed in, on **Sync now**, and when the app closes |
| API | `belfort/core/accounts_router.py`: `/api/auth/*`, `/api/sync`, `/api/sync/settings`, `/auth/callback` |
| UI | `belfort/static/auth.js`, `auth.css`: the full-screen sign-in on first launch, and the account menu in the header |

**Why one database file per user** rather than a `user_id` filter in every query: users can't leak into each other through a forgotten `WHERE`, the practice and learn code doesn't change, and new tables (T42's game state) are scoped automatically. The `user_id TEXT DEFAULT 'local'` columns in the shared contract stay harmless: inside a user's file every row belongs to that user.

**Last write wins.** For each kind of document, Belfort keeps the hash it last synced and the server's `updated_at`.
- If only one side changed, that side wins.
- If both changed, the newer one wins. "Newer" compares the server time with the time the local file was last written.
- On the first sync on a new computer, an existing account copy wins.
- Whatever is replaced is saved first to `sync-backups/` in the data folder.

**Moving local data in.** If the account is new and this computer already has practice or lessons, the user is asked whether to bring them in. The local copy stays where it is either way.

## Document shapes (for the Android app)

One `user_state` row per `(user_id, kind)`, with `payload` as JSON:

- `practice`: the Practice backup, exactly as Settings, then Backup exports it (`belfort/practice/backup.py`):
  `{"format": "belfort-practice-backup", "version": 1, "app_version", "exported_on", "accounts": [...], "trades": [...], "predictions": [...], "replays": [...]}`.
  Each row's columns are listed in `backup.py` (`ACCOUNT_COLUMNS`, `TABLES`).
- `learn`: `{"lessons": [{"lesson_id", "completed_on", "quiz_score"}], "activity": [{"day", "kind"}], ...}`.
  Other modules add their own keys through `sync.LEARN_PARTS` (T42: `"game"` for XP, streak and hearts).
- `settings`: `{"style", "capital", "risk", "language", "aiProvider", "aiModel", "aiBase"}`, each optional. **Never an AI key**: unknown keys are dropped on the server side and the browser never sends the key.

## Privacy

The sign-in screen shows what an account stores:
- only email and the user's own documents
- no prices, no research, no tracking, never the AI key

Users can delete their account and synced data from the account menu. This is Belfort's notice under India's Digital Personal Data Protection Act, 2023 (amended rule 7 in `docs/COMPLIANCE.md`, #30). A lawyer's review is decision D3.
