
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_db_connection():
    try:
        db_host = os.getenv("DB_HOST", "localhost")

        connection_config = {
            "host": db_host,
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "connection_timeout": 15
        }

        # SSL configuration for cloud database
        if db_host not in ("localhost", "127.0.0.1"):
            ssl_ca = os.getenv(
                "DB_SSL_CA",
                os.path.join(BASE_DIR, "isrgrootx1.pem")
            )

            if not os.path.isfile(ssl_ca):
                print("SSL Certificate not found:", ssl_ca)
                return None

            connection_config.update({
                "ssl_ca": ssl_ca,
                "ssl_verify_cert": True,
                "ssl_verify_identity": True
            })

        connection = mysql.connector.connect(**connection_config)

        print("Database Connected Successfully!")
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
    else:
        print("Database connection failed!")
