#!/usr/bin/env python3
"""
Flask Web Application for MySQL Database Transfer
-----------------------------------------------
A simple web interface that provides a one-click solution for transferring
data between MySQL databases.
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import threading
import os
import sys
from datetime import datetime
import logging
from db_transfer import DatabaseTransfer

# Configure logging for Flask app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Global variables to track transfer status
transfer_status = {
    'running': False,
    'last_result': None,
    'last_run': None,
    'progress': None
}


class TransferProgress:
    """Thread-safe class to track transfer progress"""
    
    def __init__(self):
        self.status = 'idle'
        self.message = 'Ready to transfer'
        self.current_table = None
        self.tables_completed = 0
        self.total_tables = 0
        self.start_time = None
        self.end_time = None
        self.result = None
    
    def reset(self):
        """Reset progress to initial state"""
        self.status = 'idle'
        self.message = 'Ready to transfer'
        self.current_table = None
        self.tables_completed = 0
        self.total_tables = 0
        self.start_time = None
        self.end_time = None
        self.result = None
    
    def start(self, total_tables):
        """Mark transfer as started"""
        self.status = 'running'
        self.message = 'Transfer in progress...'
        self.total_tables = total_tables
        self.tables_completed = 0
        self.start_time = datetime.now()
        self.end_time = None
        self.result = None
    
    def update_table(self, table_name):
        """Update current table being processed"""
        self.current_table = table_name
        self.message = f'Processing table: {table_name}'
    
    def complete_table(self):
        """Mark current table as completed"""
        self.tables_completed += 1
        if self.total_tables > 0:
            progress_pct = (self.tables_completed / self.total_tables) * 100
            self.message = f'Completed {self.tables_completed}/{self.total_tables} tables ({progress_pct:.1f}%)'
    
    def finish(self, result):
        """Mark transfer as finished"""
        self.status = 'completed'
        self.end_time = datetime.now()
        self.result = result
        
        if result['status'] == 'success':
            self.message = 'Transfer completed successfully!'
        elif result['status'] == 'partial_success':
            self.message = 'Transfer completed with some errors'
        else:
            self.message = f'Transfer failed: {result["message"]}'
    
    def error(self, error_message):
        """Mark transfer as failed"""
        self.status = 'error'
        self.end_time = datetime.now()
        self.message = f'Transfer failed: {error_message}'
    
    def to_dict(self):
        """Convert progress to dictionary for JSON serialization"""
        duration = None
        if self.start_time:
            end = self.end_time or datetime.now()
            duration = (end - self.start_time).total_seconds()
        
        return {
            'status': self.status,
            'message': self.message,
            'current_table': self.current_table,
            'tables_completed': self.tables_completed,
            'total_tables': self.total_tables,
            'duration_seconds': duration,
            'result': self.result
        }


# Global progress tracker
progress = TransferProgress()


def run_transfer():
    """
    Run the database transfer in a background thread
    """
    global progress
    
    try:
        logger.info("Starting database transfer in background thread")
        progress.start(0)  # We'll update this when we know the table count
        
        # Create transfer instance
        transfer = DatabaseTransfer()
        
        # Get table count from config
        tables = transfer.config.get('tables', [])
        progress.total_tables = len(tables)
        progress.start(len(tables))
        
        # Custom logging to update progress
        class ProgressHandler(logging.Handler):
            def emit(self, record):
                message = record.getMessage()
                if 'Transferring table:' in message:
                    table_name = message.split(': ')[1]
                    progress.update_table(table_name)
                elif 'Data transfer completed for table' in message:
                    progress.complete_table()
        
        # Add progress handler to logger
        progress_handler = ProgressHandler()
        transfer_logger = logging.getLogger('db_transfer')
        transfer_logger.addHandler(progress_handler)
        
        # Run the transfer
        result = transfer.transfer_all_tables()
        
        # Update global status
        progress.finish(result)
        transfer_status['running'] = False
        transfer_status['last_result'] = result
        transfer_status['last_run'] = datetime.now()
        
        logger.info(f"Transfer completed with status: {result['status']}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Transfer failed with exception: {error_msg}")
        
        progress.error(error_msg)
        transfer_status['running'] = False
        transfer_status['last_result'] = {'status': 'error', 'message': error_msg}
        transfer_status['last_run'] = datetime.now()


@app.route('/')
def index():
    """Main page with database and table selection dropdowns"""
    try:
        # Check if config file exists
        config_exists = os.path.exists('config.json')
        
        databases = []
        connection_error = None
        
        if config_exists:
            try:
                # Get available databases
                transfer = DatabaseTransfer()
                databases = transfer.get_databases()
            except Exception as e:
                connection_error = str(e)
                logger.error(f"Error getting databases: {e}")
        
        return render_template('index.html', 
                             config_exists=config_exists,
                             databases=databases,
                             connection_error=connection_error,
                             transfer_status=transfer_status,
                             progress=progress.to_dict())
    except Exception as e:
        logger.error(f"Error loading main page: {e}")
        flash(f'Error loading page: {str(e)}', 'error')
        return render_template('index.html', 
                             config_exists=False,
                             databases=[],
                             connection_error=None,
                             transfer_status=transfer_status,
                             progress=progress.to_dict())


@app.route('/get_tables/<database_name>')
def get_tables(database_name):
    """Get tables for a specific database as JSON"""
    try:
        if not os.path.exists('config.json'):
            return jsonify({'error': 'Configuration file not found'}), 400
        
        transfer = DatabaseTransfer()
        tables = transfer.get_tables(database_name)
        
        # Get additional info for each table
        table_info = []
        for table in tables:
            info = transfer.get_table_info(database_name, table)
            table_info.append({
                'name': table,
                'row_count': info.get('row_count', 0)
            })
        
        return jsonify({'tables': table_info})
        
    except Exception as e:
        logger.error(f"Error getting tables for database '{database_name}': {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/transfer', methods=['POST'])
def start_transfer():
    """Start the database transfer process"""
    global transfer_status, progress
    
    # Check if transfer is already running
    if transfer_status['running']:
        flash('Transfer is already in progress!', 'warning')
        return redirect(url_for('index'))
    
    # Check if config file exists
    if not os.path.exists('config.json'):
        flash('Configuration file (config.json) not found! Please create it first.', 'error')
        return redirect(url_for('index'))
    
    # Get form data
    source_db = request.form.get('source_database')
    target_db = request.form.get('target_database')
    table_name = request.form.get('table_name')
    
    if not all([source_db, target_db, table_name]):
        flash('Please select source database, target database, and table.', 'error')
        return redirect(url_for('index'))
    
    if source_db == target_db:
        flash('Source and target databases cannot be the same.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Reset progress
        progress.reset()
        
        # Mark as running
        transfer_status['running'] = True
        transfer_status['last_result'] = None
        
        # Start transfer in background thread
        def run_single_table_transfer():
            global progress, transfer_status
            try:
                progress.start(1)  # Single table transfer
                progress.update_table(table_name)
                
                transfer = DatabaseTransfer()
                result = transfer.transfer_single_table(source_db, target_db, table_name)
                
                progress.finish(result)
                transfer_status['running'] = False
                transfer_status['last_result'] = result
                transfer_status['last_run'] = datetime.now()
                
                logger.info(f"Single table transfer completed: {result['status']}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Single table transfer failed: {error_msg}")
                
                progress.error(error_msg)
                transfer_status['running'] = False
                transfer_status['last_result'] = {'status': 'error', 'message': error_msg}
                transfer_status['last_run'] = datetime.now()
        
        thread = threading.Thread(target=run_single_table_transfer, daemon=True)
        thread.start()
        
        flash(f'Data transfer started: {source_db}.{table_name} → {target_db}.{table_name}', 'info')
        logger.info(f"Single table transfer initiated: {source_db}.{table_name} -> {target_db}.{table_name}")
        
    except Exception as e:
        transfer_status['running'] = False
        error_msg = f"Failed to start transfer: {str(e)}"
        flash(error_msg, 'error')
        logger.error(error_msg)
    
    return redirect(url_for('index'))


@app.route('/status')
def get_status():
    """Get current transfer status as JSON"""
    return jsonify({
        'transfer_status': transfer_status,
        'progress': progress.to_dict()
    })


@app.route('/logs')
def view_logs():
    """View transfer logs"""
    try:
        log_content = ""
        if os.path.exists('transfer.log'):
            with open('transfer.log', 'r') as f:
                # Get last 50 lines
                lines = f.readlines()
                log_content = ''.join(lines[-50:])
        
        return render_template('logs.html', log_content=log_content)
    
    except Exception as e:
        flash(f'Error reading logs: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/config')
def view_config():
    """View current configuration"""
    try:
        config_content = ""
        config_exists = False
        
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config_content = f.read()
            config_exists = True
        
        return render_template('config.html', 
                             config_content=config_content,
                             config_exists=config_exists)
    
    except Exception as e:
        flash(f'Error reading configuration: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', 
                         error_code=500,
                         error_message="Internal server error"), 500


if __name__ == '__main__':
    # Check if running in development mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    logger.info(f"Starting Flask application on {host}:{port}")
    logger.info(f"Debug mode: {debug_mode}")
    
    # Create config.json template if it doesn't exist
    if not os.path.exists('config.json'):
        logger.warning("config.json not found. Please create it using the provided template.")
    
    app.run(host=host, port=port, debug=debug_mode)
