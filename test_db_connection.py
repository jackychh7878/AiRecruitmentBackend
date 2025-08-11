#!/usr/bin/env python3
"""
Simple script to test Azure PostgreSQL database connection
"""
import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def test_connection():
    """Test the database connection"""
    try:
        # Get the database URL from environment
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print("❌ ERROR: DATABASE_URL not found in environment variables")
            print("Make sure you have a .env file with your Azure PostgreSQL connection string")
            return False
        
        print("🔍 Testing database connection...")
        print(f"🔗 Connecting to: {database_url.split('@')[1].split('/')[0]}")  # Hide credentials
        
        # Test connection
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print(f"✅ SUCCESS: Connected to PostgreSQL")
        print(f"📋 Database version: {db_version[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to database")
        print(f"🔍 Error details: {str(e)}")
        print("\n💡 Common issues:")
        print("  - Check your DATABASE_URL in .env file")
        print("  - Verify Azure PostgreSQL server is running")
        print("  - Check firewall rules (allow your IP)")
        print("  - Verify username format: username@servername")
        print("  - Ensure SSL is required (?sslmode=require)")
        
        return False

if __name__ == "__main__":
    test_connection() 