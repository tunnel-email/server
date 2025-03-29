import mysql.connector
import json
from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="registrator",
            password=getenv("MYSQL_PASSWORD"),
            database="service_db",
            port=int(getenv("MYSQL_PORT"))
        )

        self.cursor = self.connection.cursor()
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def add_token(self, yandex_id, token):
        try:
            query = "INSERT INTO users (yandex_id, token) VALUES (%s, %s)"
            self.cursor.execute(query, (yandex_id, token))
            self.connection.commit()
            return True
        except mysql.connector.Error:
            return False

    def get_user_tokens(self, yandex_id):
        query = "SELECT token FROM users WHERE yandex_id = %s"
        self.cursor.execute(query, (yandex_id,))
        
        results = self.cursor.fetchall()
        if results:
            return [result[0] for result in results]
        return None

    def user_exists(self, yandex_id):
        query = "SELECT 1 FROM users WHERE yandex_id = %s LIMIT 1"
        self.cursor.execute(query, (yandex_id,))
        result = self.cursor.fetchone()
        return bool(result)

    def get_id_by_token(self, token):
        query = "SELECT yandex_id FROM users WHERE token = %s LIMIT 1"
        self.cursor.execute(query, (token,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def number_of_tokens(self, yandex_id):

        query = "SELECT COUNT(*) FROM users WHERE yandex_id = %s"
        self.cursor.execute(query, (yandex_id,))

        result = self.cursor.fetchone()
    
        return result[0] if result else 0

    def token_is_taken(self, token):
        query = "SELECT 1 FROM users WHERE token = %s LIMIT 1"
        self.cursor.execute(query, (token,))
    
        result = self.cursor.fetchone()

        return bool(result)


    def close(self):
        self.cursor.close()
        self.connection.close()
