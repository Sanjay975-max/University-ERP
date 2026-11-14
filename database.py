
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        print("MySQL Connected Successfully!")
        return connection

    except Error as err:
        print("Database Error:", err)
        return None


if __name__ == "__main__":
    print("Testing database connection...")
    db = get_db_connection()

    if db:
        db.close()
        print("Database connection successful!")
