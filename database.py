import streamlit as st
from sqlalchemy import text
import bcrypt
import pandas as pd

def get_conn():
    # Ansluter automatiskt med referenserna från secrets.toml
    return st.connection("mysql", type="sql")

def init_db():
    conn = get_conn()
    with conn.session as s:
        # Skapa tabeller om de inte finns
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
        '''))
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS collection (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                item_name VARCHAR(255) NOT NULL,
                market_value DECIMAL(10, 2) DEFAULT 0.00,
                image_url VARCHAR(500),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        '''))
        s.commit()

def create_user(username, password):
    conn = get_conn()
    hash_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with conn.session as s:
        try:
            s.execute(text("INSERT INTO users (username, password_hash) VALUES (:u, :p)"), 
                      {"u": username, "p": hash_pw})
            s.commit()
            return True
        except Exception:
            return False # Användarnamn finns förmodligen redan

def verify_user(username, password):
    conn = get_conn()
    with conn.session as s:
        result = s.execute(text("SELECT id, password_hash FROM users WHERE username = :u"), 
                           {"u": username}).fetchone()
        if result and bcrypt.checkpw(password.encode('utf-8'), result[1].encode('utf-8')):
            return result[0] # Returnerar user_id
        return None

def get_user_collection(user_id):
    conn = get_conn()
    # Använder pandas för enkel integration med Streamlit-tabeller/metrics
    query = "SELECT id, item_name, market_value, image_url FROM collection WHERE user_id = :uid"
    return conn.query(query, params={"uid": user_id}, ttl=0) # ttl=0 tvingar live-data

def add_to_collection(user_id, item_name, market_value, image_url):
    conn = get_conn()
    with conn.session as s:
        s.execute(text('''
            INSERT INTO collection (user_id, item_name, market_value, image_url) 
            VALUES (:uid, :name, :val, :img)
        '''), {"uid": user_id, "name": item_name, "val": market_value, "img": image_url})
        s.commit()

def delete_from_collection(item_id, user_id):
    conn = get_conn()
    with conn.session as s:
        s.execute(text("DELETE FROM collection WHERE id = :id AND user_id = :uid"), 
                  {"id": item_id, "uid": user_id})
        s.commit()
