-- Adds email verification columns for token-based verification flow.
-- Safe to run multiple times.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255),
    ADD COLUMN IF NOT EXISTS token_expiry TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS users_verification_token_key
    ON users(verification_token)
    WHERE verification_token IS NOT NULL;
