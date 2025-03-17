import pyodbc
import os
from tkinter import messagebox
import pyodbc
from bs4 import BeautifulSoup


class DatabaseManager:
    """Handles database connections and operations"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def get_connection(self):
        """Create and return a database connection with graceful error handling"""
        try:
            # Check for required environment variables
            db_server = os.getenv("DB_SERVER")
            db_name = os.getenv("DB_NAME")
            db_username = os.getenv("DB_USERNAME")
            db_password = os.getenv("DB_PASSWORD")
            
            # Validate environment variables
            if not all([db_server, db_name, db_username, db_password]):
                missing = []
                if not db_server: missing.append("DB_SERVER")
                if not db_name: missing.append("DB_NAME")
                if not db_username: missing.append("DB_USERNAME")
                if not db_password: missing.append("DB_PASSWORD")
                
                error_msg = f"Missing environment variables: {', '.join(missing)}"
                self.logger.error(error_msg)
                messagebox.showerror("Configuration Error", 
                                f"Please check your .env file. {error_msg}")
                return None
            
            # Try different drivers in order of preference
            drivers = [
                "{ODBC Driver 17 for SQL Server}",
                "{ODBC Driver 13 for SQL Server}",
                "{SQL Server Native Client 11.0}",
                "{SQL Server}"
            ]
            
            conn = None
            conn_err = None
            
            for driver in drivers:
                try:
                    conn_str = f"DRIVER={driver};SERVER={db_server};DATABASE={db_name};UID={db_username};PWD={db_password}"
                    conn = pyodbc.connect(conn_str)
                    self.logger.info(f"Connected using {driver}")
                    break
                except pyodbc.Error as e:
                    conn_err = e
                    continue
                    
            if conn is None:
                if conn_err:
                    raise conn_err
                else:
                    raise Exception("No suitable SQL Server driver found")
                    
            return conn
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            messagebox.showerror("Database Connection Error", str(e))
            return None
    
    def test_connection(self, config):
        """Test connection with specific config"""
        try:
            db_server = config.get('DB_SERVER')
            db_name = config.get('DB_NAME')
            db_username = config.get('DB_USERNAME')
            db_password = config.get('DB_PASSWORD')
            
            if not all([db_server, db_name, db_username, db_password]):
                raise ValueError("Missing required database parameters")
            
            # Try different drivers
            drivers = [
                "{ODBC Driver 17 for SQL Server}",
                "{ODBC Driver 13 for SQL Server}",
                "{SQL Server Native Client 11.0}",
                "{SQL Server}"
            ]
            
            conn = None
            conn_err = None
            used_driver = None
            
            for driver in drivers:
                try:
                    conn_str = f"DRIVER={driver};SERVER={db_server};DATABASE={db_name};UID={db_username};PWD={db_password}"
                    conn = pyodbc.connect(conn_str)
                    used_driver = driver
                    break
                except pyodbc.Error as e:
                    conn_err = e
                    continue
                    
            if conn is None:
                if conn_err:
                    raise conn_err
                else:
                    raise Exception("No suitable SQL Server driver found")
            
            # Close connection
            conn.close()
            return True, used_driver
            
        except Exception as e:
            return False, str(e)
    
    def fetch_company_list(self):
        """Fetch all company names from the database"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            cursor.execute("SELECT company FROM Symbol_List")
            companies = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return companies
        except Exception as e:
            self.logger.error(f"Error fetching company list: {str(e)}")
            return []
    
    def fetch_sector_code_list(self):
        """Fetch all company names from the database"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
                    
            cursor = conn.cursor()
            cursor.execute("SELECT sector_code, MAX(last_updated) AS last_updated FROM sector_info GROUP BY sector_code ORDER BY last_updated;")
            sector_code = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return sector_code
        except Exception as e:
            self.logger.error(f"Error fetching company list: {str(e)}")
            return []
        
    def store_data(self, company_shares,insert_query):
        """Store scraped data in the database"""
        if not company_shares:
            self.logger.warning("No data to store")
            return
        
        try:
            conn = self.get_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            # Insert data into Symbol_Share table
           
            cursor.executemany(insert_query, company_shares)
            conn.commit()
            
            self.logger.info(f"Successfully stored data for {len(company_shares)} companies")
            
            cursor.close()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error storing data: {str(e)}")
