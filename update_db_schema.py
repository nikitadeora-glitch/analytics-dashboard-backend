from sqlalchemy import text
from database import engine

def update_password_reset_table():
    with engine.connect() as conn:
        # Start a transaction
        with conn.begin():
            # Add email column if it doesn't exist
            conn.execute(text("""
                DO $$
                BEGIN
                    BEGIN
                        ALTER TABLE password_resets ADD COLUMN IF NOT EXISTS email VARCHAR NOT NULL DEFAULT 'unknown@example.com';
                    EXCEPTION
                        WHEN duplicate_column THEN 
                            RAISE NOTICE 'column email already exists in password_resets.';
                    END;
                    
                    BEGIN
                        ALTER TABLE password_resets ADD COLUMN IF NOT EXISTS used_at TIMESTAMP;
                    EXCEPTION
                        WHEN duplicate_column THEN 
                            RAISE NOTICE 'column used_at already exists in password_resets.';
                    END;
                    
                    -- Update existing records with user emails if possible
                    BEGIN
                        UPDATE password_resets pr
                        SET email = u.email
                        FROM users u
                        WHERE pr.user_id = u.id
                        AND pr.email = 'unknown@example.com';
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE NOTICE 'Could not update email for existing password reset records: %', SQLERRM;
                    END;
                    
                    -- Create index if it doesn't exist
                    CREATE INDEX IF NOT EXISTS ix_password_resets_email ON password_resets (email);
                END $$;
            """))

if __name__ == "__main__":
    print("Updating password_resets table...")
    update_password_reset_table()
    print("Database schema updated successfully!")
