#!/usr/bin/env python3
"""
MySQL Database Transfer Script
------------------------------
This script transfers data from a source MySQL database to a target MySQL database.
It includes proper error handling, logging, and duplicate key management.
Now supports dynamic database and table discovery.
"""

import mysql.connector
from mysql.connector import Error
import logging
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transfer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DatabaseTransfer:
    """Handles data transfer between MySQL databases"""
    
    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize the database transfer object
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config = self._load_config(config_file)
        self.source_conn = None
        self.target_conn = None
        self.server_conn = None
    
    def _load_config(self, config_file: str) -> Dict:
        """
        Load configuration from JSON file
        
        Args:
            config_file (str): Path to configuration file
            
        Returns:
            Dict: Configuration dictionary
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def _create_connection(self, db_config: Dict) -> mysql.connector.MySQLConnection:
        """
        Create a MySQL database connection
        
        Args:
            db_config (Dict): Database configuration parameters
            
        Returns:
            MySQLConnection: Database connection object
        """
        try:
            connection = mysql.connector.connect(
                host=db_config['host'],
                port=db_config.get('port', 3306),
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                autocommit=False
            )
            logger.info(f"Connected to database: {db_config['host']}:{db_config.get('port', 3306)}")
            return connection
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            raise
    
    def connect_databases(self) -> bool:
        """
        Establish connections to both source and target databases
        
        Returns:
            bool: True if both connections successful, False otherwise
        """
        try:
            self.source_conn = self._create_connection(self.config['source_db'])
            self.target_conn = self._create_connection(self.config['target_db'])
            logger.info("Successfully connected to both databases")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            self._close_connections()
            return False
    
    def _close_connections(self):
        """Close database connections if they exist"""
        if self.source_conn and self.source_conn.is_connected():
            self.source_conn.close()
            logger.info("Source database connection closed")
        
        if self.target_conn and self.target_conn.is_connected():
            self.target_conn.close()
            logger.info("Target database connection closed")
    
    def _get_table_structure(self, connection: mysql.connector.MySQLConnection, table_name: str) -> List[Tuple]:
        """
        Get the structure of a table
        
        Args:
            connection: Database connection
            table_name (str): Name of the table
            
        Returns:
            List[Tuple]: Table structure information
        """
        cursor = connection.cursor()
        try:
            cursor.execute(f"DESCRIBE {table_name}")
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting table structure for {table_name}: {e}")
            raise
        finally:
            cursor.close()
    
    def _get_primary_keys(self, connection: mysql.connector.MySQLConnection, table_name: str) -> List[str]:
        """
        Get primary key columns for a table
        
        Args:
            connection: Database connection
            table_name (str): Name of the table
            
        Returns:
            List[str]: List of primary key column names
        """
        cursor = connection.cursor()
        try:
            query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'
                ORDER BY ORDINAL_POSITION
            """
            cursor.execute(query, (connection.database, table_name))
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            logger.error(f"Error getting primary keys for {table_name}: {e}")
            raise
        finally:
            cursor.close()
    
    def _create_server_connection(self) -> mysql.connector.MySQLConnection:
        """
        Create a MySQL server connection without specifying a database
        
        Returns:
            MySQLConnection: Server connection object
        """
        try:
            connection = mysql.connector.connect(
                host=self.config['server']['host'],
                port=self.config['server'].get('port', 3306),
                user=self.config['server']['user'],
                password=self.config['server']['password']
            )
            logger.info(f"Connected to MySQL server: {self.config['server']['host']}:{self.config['server'].get('port', 3306)}")
            return connection
        except Error as e:
            logger.error(f"Error connecting to MySQL server: {e}")
            raise
    
    def get_databases(self) -> List[str]:
        """
        Get list of all databases on the MySQL server
        
        Returns:
            List[str]: List of database names
        """
        try:
            if not self.server_conn or not self.server_conn.is_connected():
                self.server_conn = self._create_server_connection()
            
            cursor = self.server_conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            cursor.close()
            
            # Filter out system databases
            system_dbs = ['information_schema', 'mysql', 'performance_schema', 'sys']
            user_databases = [db for db in databases if db not in system_dbs]
            
            logger.info(f"Found {len(user_databases)} user databases")
            return user_databases
            
        except Error as e:
            logger.error(f"Error getting databases: {e}")
            return []
    
    def get_tables(self, database_name: str) -> List[str]:
        """
        Get list of all tables in a specific database
        
        Args:
            database_name (str): Name of the database
            
        Returns:
            List[str]: List of table names
        """
        try:
            if not self.server_conn or not self.server_conn.is_connected():
                self.server_conn = self._create_server_connection()
            
            cursor = self.server_conn.cursor()
            cursor.execute(f"USE `{database_name}`")
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            
            logger.info(f"Found {len(tables)} tables in database '{database_name}'")
            return tables
            
        except Error as e:
            logger.error(f"Error getting tables from database '{database_name}': {e}")
            return []
    
    def get_table_info(self, database_name: str, table_name: str) -> Dict:
        """
        Get detailed information about a table
        
        Args:
            database_name (str): Name of the database
            table_name (str): Name of the table
            
        Returns:
            Dict: Table information including row count, columns, etc.
        """
        try:
            if not self.server_conn or not self.server_conn.is_connected():
                self.server_conn = self._create_server_connection()
            
            cursor = self.server_conn.cursor()
            cursor.execute(f"USE `{database_name}`")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            
            # Get column information
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            
            cursor.close()
            
            return {
                'database': database_name,
                'table': table_name,
                'row_count': row_count,
                'columns': [{'name': col[0], 'type': col[1], 'null': col[2], 'key': col[3]} for col in columns]
            }
            
        except Error as e:
            logger.error(f"Error getting table info for '{database_name}.{table_name}': {e}")
            return {}
    
    def transfer_single_table(self, source_db: str, target_db: str, table_name: str) -> Dict:
        """
        Transfer data from a single table between specified databases
        
        Args:
            source_db (str): Source database name
            target_db (str): Target database name
            table_name (str): Name of the table to transfer
            
        Returns:
            Dict: Transfer statistics
        """
        logger.info(f"Starting transfer: {source_db}.{table_name} -> {target_db}.{table_name}")
        
        # Create database-specific connections
        try:
            source_config = {
                'host': self.config['server']['host'],
                'port': self.config['server'].get('port', 3306),
                'database': source_db,
                'user': self.config['server']['user'],
                'password': self.config['server']['password']
            }
            
            target_config = {
                'host': self.config['server']['host'],
                'port': self.config['server'].get('port', 3306),
                'database': target_db,
                'user': self.config['server']['user'],
                'password': self.config['server']['password']
            }
            
            self.source_conn = self._create_connection(source_config)
            self.target_conn = self._create_connection(target_config)
            
            # Perform the transfer
            result = self.transfer_table_data(table_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in single table transfer: {e}")
            return {
                "status": "error",
                "message": f"Transfer failed: {str(e)}"
            }
        finally:
            self._close_connections()
    
    def _create_target_table_if_not_exists(self, table_name: str) -> bool:
        """
        Create target table with same structure as source if it doesn't exist
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            bool: True if successful, False otherwise
        """
        source_cursor = self.source_conn.cursor()
        target_cursor = self.target_conn.cursor()
        
        try:
            # Get CREATE TABLE statement from source
            source_cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_statement = source_cursor.fetchone()[1]
            
            # Check if target table exists
            target_cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{self.target_conn.database}' 
                AND TABLE_NAME = '{table_name}'
            """)
            
            if target_cursor.fetchone()[0] == 0:
                # Create table in target database
                target_cursor.execute(create_statement)
                self.target_conn.commit()
                logger.info(f"Created table {table_name} in target database")
            else:
                logger.info(f"Table {table_name} already exists in target database")
            
            return True
            
        except Error as e:
            logger.error(f"Error creating target table {table_name}: {e}")
            self.target_conn.rollback()
            return False
        finally:
            source_cursor.close()
            target_cursor.close()
    
    def transfer_table_data(self, table_name: str, batch_size: int = 1000) -> Dict:
        """
        Transfer data from source table to target table
        
        Args:
            table_name (str): Name of the table to transfer
            batch_size (int): Number of rows to process in each batch
            
        Returns:
            Dict: Transfer statistics
        """
        logger.info(f"Starting data transfer for table: {table_name}")
        
        # Ensure target table exists
        if not self._create_target_table_if_not_exists(table_name):
            return {"status": "error", "message": "Failed to create target table"}
        
        source_cursor = self.source_conn.cursor(dictionary=True)
        target_cursor = self.target_conn.cursor()
        
        try:
            # Get table structure
            table_structure = self._get_table_structure(self.source_conn, table_name)
            columns = [col[0] for col in table_structure]
            primary_keys = self._get_primary_keys(self.source_conn, table_name)
            
            # Count total rows in source table
            source_cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            total_rows = source_cursor.fetchone()['count']
            logger.info(f"Total rows to transfer: {total_rows}")
            
            if total_rows == 0:
                return {
                    "status": "success",
                    "rows_transferred": 0,
                    "rows_updated": 0,
                    "total_rows": 0,
                    "message": "No data to transfer"
                }
            
            # Prepare INSERT ... ON DUPLICATE KEY UPDATE statement
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f"`{col}`" for col in columns])
            
            if primary_keys:
                # Create ON DUPLICATE KEY UPDATE clause
                update_clauses = []
                for col in columns:
                    if col not in primary_keys:  # Don't update primary key columns
                        update_clauses.append(f"`{col}` = VALUES(`{col}`)")
                
                if update_clauses:
                    update_clause = "ON DUPLICATE KEY UPDATE " + ", ".join(update_clauses)
                else:
                    update_clause = ""
            else:
                # If no primary key, use IGNORE to skip duplicates
                update_clause = ""
                insert_type = "INSERT IGNORE"
            
            if primary_keys and update_clauses:
                insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders}) {update_clause}"
            else:
                insert_query = f"INSERT IGNORE INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
            
            # Transfer data in batches
            offset = 0
            rows_transferred = 0
            rows_updated = 0
            
            while offset < total_rows:
                # Fetch batch from source
                source_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
                batch = source_cursor.fetchall()
                
                if not batch:
                    break
                
                # Prepare data for insertion
                batch_data = []
                for row in batch:
                    batch_data.append([row[col] for col in columns])
                
                # Insert batch into target
                target_cursor.executemany(insert_query, batch_data)
                
                # Get affected rows count
                affected_rows = target_cursor.rowcount
                rows_transferred += len(batch_data)
                
                # Commit batch
                self.target_conn.commit()
                
                logger.info(f"Processed batch: {offset + len(batch)}/{total_rows} rows")
                offset += batch_size
            
            logger.info(f"Data transfer completed for table {table_name}")
            
            return {
                "status": "success",
                "rows_transferred": rows_transferred,
                "total_rows": total_rows,
                "message": f"Successfully transferred {rows_transferred} rows"
            }
            
        except Error as e:
            logger.error(f"Error transferring data for table {table_name}: {e}")
            self.target_conn.rollback()
            return {
                "status": "error",
                "message": f"Error transferring data: {str(e)}"
            }
        finally:
            source_cursor.close()
            target_cursor.close()
    
    def transfer_all_tables(self) -> Dict:
        """
        Transfer data from all configured tables
        
        Returns:
            Dict: Overall transfer results
        """
        if not self.connect_databases():
            return {"status": "error", "message": "Failed to connect to databases"}
        
        tables_to_transfer = self.config.get('tables', [])
        if not tables_to_transfer:
            return {"status": "error", "message": "No tables specified in configuration"}
        
        results = {}
        overall_success = True
        
        try:
            start_time = datetime.now()
            logger.info(f"Starting bulk transfer of {len(tables_to_transfer)} tables")
            
            for table_name in tables_to_transfer:
                logger.info(f"Transferring table: {table_name}")
                result = self.transfer_table_data(table_name)
                results[table_name] = result
                
                if result['status'] != 'success':
                    overall_success = False
                    logger.error(f"Failed to transfer table {table_name}: {result['message']}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "status": "success" if overall_success else "partial_success",
                "duration_seconds": duration,
                "tables_processed": len(tables_to_transfer),
                "results": results,
                "message": "Transfer completed" if overall_success else "Transfer completed with some errors"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during bulk transfer: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
        finally:
            self._close_connections()


def main():
    """Main function for standalone script execution"""
    try:
        transfer = DatabaseTransfer()
        result = transfer.transfer_all_tables()
        
        print("\n" + "="*50)
        print("TRANSFER RESULTS")
        print("="*50)
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if 'duration_seconds' in result:
            print(f"Duration: {result['duration_seconds']:.2f} seconds")
        
        if 'results' in result:
            print("\nTable Results:")
            for table, table_result in result['results'].items():
                print(f"  {table}: {table_result['status']} - {table_result['message']}")
        
        return result['status'] == 'success'
        
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
