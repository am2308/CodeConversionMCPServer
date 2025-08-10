#!/usr/bin/env python3
"""
Database migration script to add GitHub App columns to users table
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def run_migration():
    """Add GitHub App columns to users table"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/codeconv")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                print("Starting database migration...")
                
                # Check if columns already exist
                check_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('github_installation_id', 'github_oauth_token_encrypted');
                """
                
                result = conn.execute(text(check_query))
                existing_columns = [row[0] for row in result]
                
                # Add github_installation_id column if it doesn't exist
                if 'github_installation_id' not in existing_columns:
                    print("Adding github_installation_id column...")
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN github_installation_id VARCHAR(255)
                    """))
                else:
                    print("github_installation_id column already exists")
                
                # Add github_oauth_token_encrypted column if it doesn't exist
                if 'github_oauth_token_encrypted' not in existing_columns:
                    print("Adding github_oauth_token_encrypted column...")
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN github_oauth_token_encrypted TEXT
                    """))
                else:
                    print("github_oauth_token_encrypted column already exists")
                
                # Commit the transaction
                trans.commit()
                print("Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                raise e
                
    except SQLAlchemyError as e:
        print(f"Database error during migration: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
