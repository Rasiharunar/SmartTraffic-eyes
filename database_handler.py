"""
Database operations untuk Vehicle Counter - Updated with graceful error handling
Updated: 2025-07-31 17:33:23 UTC by Rasiharunar
"""

import psycopg2
import datetime
import tkinter.simpledialog
from tkinter import messagebox
from config import DATABASE_CONFIG

class DatabaseHandler:
    def __init__(self):
        self.db_conn = None
        self.cursor = None
        self.init_database()
    
    def init_database(self):
        """Initialize PostgreSQL database connection with graceful error handling"""
        try:
            self.db_conn = psycopg2.connect(**DATABASE_CONFIG)
            self.cursor = self.db_conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS deteksi_kendaraan_directional (
                    id SERIAL PRIMARY KEY,
                    motor_up INTEGER NOT NULL,
                    motor_down INTEGER NOT NULL,
                    mobil_up INTEGER NOT NULL,
                    mobil_down INTEGER NOT NULL,
                    truk_up INTEGER NOT NULL,
                    truk_down INTEGER NOT NULL,
                    bus_up INTEGER NOT NULL,
                    bus_down INTEGER NOT NULL,
                    total_up INTEGER NOT NULL,
                    total_down INTEGER NOT NULL,
                    session_name VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self.db_conn.commit()
            print("✅ Database connected and initialized successfully.")
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            print("⚠️  Application will continue without database functionality.")
            self.db_conn = None
            self.cursor = None

    def save_counts(self, vehicle_counts_up, vehicle_counts_down, total_up, total_down, parent_window=None):
        """Save vehicle counts to database"""
        if not self.db_conn:
            messagebox.showerror("Database Error", "❌ Database connection not established.\nPlease check your database configuration.")
            return

        session_name = tkinter.simpledialog.askstring(
            "Session Name", 
            "Enter session name for this record:",
            initialvalue=f"Session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if not session_name:
            return

        # Extract counts safely
        motor_up = vehicle_counts_up.get('motorcycle', 0)
        motor_down = vehicle_counts_down.get('motorcycle', 0)
        mobil_up = vehicle_counts_up.get('car', 0)
        mobil_down = vehicle_counts_down.get('car', 0)
        truk_up = vehicle_counts_up.get('truck', 0)
        truk_down = vehicle_counts_down.get('truck', 0)
        bus_up = vehicle_counts_up.get('bus', 0)
        bus_down = vehicle_counts_down.get('bus', 0)
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.cursor.execute('''
                INSERT INTO deteksi_kendaraan_directional 
                (motor_up, motor_down, mobil_up, mobil_down, truk_up, truk_down, 
                 bus_up, bus_down, total_up, total_down, session_name, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            ''', (motor_up, motor_down, mobil_up, mobil_down, truk_up, truk_down, 
                  bus_up, bus_down, total_up, total_down, session_name, current_time))
            self.db_conn.commit()
            
            messagebox.showinfo("💾 Database Save", 
                               f"✅ Successfully saved counts to database!\n\n"
                               f"📊 Session: {session_name}\n"
                               f"📈 Total UP: {total_up}\n"
                               f"📉 Total DOWN: {total_down}\n"
                               f"🕐 Time: {current_time}")
            
            print(f"✅ Saved directional counts to DB: Session={session_name}, "
                  f"UP={total_up}, DOWN={total_down} at {current_time}")
                  
        except psycopg2.Error as e:
            messagebox.showerror("💾 Database Error", f"❌ Error saving counts to database:\n{e}")
            print(f"❌ Error saving counts to database: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def close_connection(self):
        """Close database connection"""
        if self.db_conn:
            try:
                self.db_conn.close()
                print("✅ Database connection closed successfully.")
            except psycopg2.Error as e:
                print(f"❌ Error closing database connection: {e}")