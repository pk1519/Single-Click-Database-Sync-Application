# MySQL Database Transfer Tool

A complete Python-based solution for transferring data between MySQL databases with a user-friendly web interface. Transfer data between databases with just one click!

## Features

- **🔄 Dynamic Database Discovery**: Automatically lists all available databases on your MySQL server
- **📋 Smart Table Selection**: Browse and select tables from dropdown menus with row counts
- **🎯 One-Click Transfer**: Simple web interface to transfer data between any databases
- **🛠️ Automatic Table Creation**: Target tables are created automatically if they don't exist
- **🔒 Duplicate Handling**: Uses `INSERT ... ON DUPLICATE KEY UPDATE` for proper duplicate management
- **📊 Progress Tracking**: Real-time progress updates during transfer
- **⚡ Error Handling**: Comprehensive error handling with detailed logging
- **📦 Batch Processing**: Processes data in configurable batches for memory efficiency
- **🌐 Modern Web Interface**: Clean, responsive web UI built with Bootstrap
- **📝 Detailed Logging**: Complete logs of all transfer operations

## Project Structure

```
mysql_data_transfer/
├── app.py                 # Flask web application
├── db_transfer.py         # Core database transfer logic
├── config.json.template   # Configuration template
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Main page
│   ├── config.html       # Configuration page
│   ├── logs.html         # Logs viewing page
│   └── error.html        # Error page
└── static/               # Static files (CSS, JS, images)
```

## Prerequisites

- **Python 3.7+** (3.8 or higher recommended)
- **MySQL Server** (5.7 or higher recommended)
- **pip** (Python package installer)

## Installation and Setup

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd mysql_data_transfer
```

Or download and extract the project files to a directory.

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up MySQL Databases

Ensure you have:
- **Source database** with the data you want to transfer
- **Target database** (can be empty, tables will be created automatically)
- **Database users** with appropriate permissions:
  - Source user: `SELECT` permission on source database
  - Target user: `CREATE`, `INSERT`, `UPDATE` permissions on target database

#### MySQL Setup Commands (if needed):

```sql
-- Create databases
CREATE DATABASE source_db;
CREATE DATABASE target_db;

-- Create users and grant permissions
CREATE USER 'transfer_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT ON source_db.* TO 'transfer_user'@'localhost';
GRANT CREATE, INSERT, UPDATE ON target_db.* TO 'transfer_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configure Database Connection

1. Copy the configuration template:
   ```bash
   copy config.json.template config.json
   # On macOS/Linux: cp config.json.template config.json
   ```

2. Edit `config.json` with your MySQL server settings:
   ```json
   {
     "server": {
       "host": "localhost",
       "port": 3306,
       "user": "your_mysql_username",
       "password": "your_mysql_password"
     }
   }
   ```

**⚠️ Security Note**: Never commit the `config.json` file with real credentials to version control!

**📌 Important**: Databases and tables are now selected dynamically through the web interface dropdowns!

## Usage

### Web Interface (Recommended)

1. **Start the Flask application:**
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Select your databases and table:**
   - Choose **Source Database** from the dropdown (automatically populated)
   - Choose **Target Database** from the dropdown
   - Select **Table** to transfer (loaded dynamically with row counts)

4. **Click "Transfer Data"** to start the transfer process

5. **Monitor progress** in real-time on the web interface

6. **View logs** by clicking the "View Logs" button

### Command Line Interface

You can also run the transfer directly from the command line:

```bash
python db_transfer.py
```

## Configuration Options

### Database Configuration

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `host` | Database server hostname/IP | Yes | - |
| `port` | Database server port | No | 3306 |
| `database` | Database name | Yes | - |
| `user` | Database username | Yes | - |
| `password` | Database password | Yes | - |

### Tables Configuration

- `tables`: Array of table names to transfer
- Tables will be created automatically in the target database if they don't exist
- Table structure is copied exactly from the source database

## Features in Detail

### Duplicate Key Handling

The tool automatically handles duplicate entries using MySQL's `INSERT ... ON DUPLICATE KEY UPDATE` syntax:

- If a table has primary keys: Updates existing records with new data
- If no primary keys: Uses `INSERT IGNORE` to skip duplicates

### Progress Tracking

- Real-time progress updates in the web interface
- Shows current table being processed
- Displays completion percentage
- Tracks total time elapsed

### Error Handling

- Comprehensive error handling for database connections
- Detailed error messages and logging
- Automatic rollback on failures
- Connection cleanup on errors

### Logging

All operations are logged to `transfer.log` with:
- Timestamp for each operation
- Connection status
- Transfer progress
- Error details
- Performance metrics

## Troubleshooting

### Common Issues

1. **"Configuration file not found"**
   - Make sure `config.json` exists in the project directory
   - Copy from `config.json.template` and update with your settings

2. **"Access denied" or connection errors**
   - Verify database credentials in `config.json`
   - Ensure MySQL server is running
   - Check firewall settings
   - Verify user permissions

3. **"Table doesn't exist" errors**
   - Ensure source tables exist and are accessible
   - Check user permissions on source database

4. **Memory issues with large tables**
   - Adjust batch size in `db_transfer.py` (default: 1000 rows)
   - Consider increasing available memory

### Environment Variables

You can use environment variables for additional configuration:

```bash
# Flask settings
export FLASK_DEBUG=true          # Enable debug mode
export PORT=5000                 # Set port (default: 5000)
export HOST=127.0.0.1           # Set host (default: 127.0.0.1)
export SECRET_KEY=your-secret-key # Set Flask secret key
```

### Log Levels

To change log levels, modify the logging configuration in `db_transfer.py`:

```python
logging.basicConfig(level=logging.DEBUG)  # More detailed logs
logging.basicConfig(level=logging.WARNING)  # Less verbose logs
```

## Security Considerations

- **Never commit credentials** to version control
- Use **strong passwords** for database users
- Consider using **environment variables** for sensitive data
- **Restrict database user permissions** to minimum required
- **Use SSL connections** for remote database access
- **Run on secure networks** only

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for educational and commercial use. Please ensure you comply with any applicable licenses for dependencies.

## Support

For issues, questions, or contributions:

1. Check the troubleshooting section above
2. Review the logs in `transfer.log`
3. Open an issue with detailed error information

## Version History

- **v2.0.0** - Enhanced Dynamic Interface
  - 🆕 Dynamic database discovery and listing
  - 📝 Smart table selection with row counts
  - 🔄 Real-time dropdown population
  - 🛡️ Enhanced error handling and validation
  - 📋 Simplified configuration (server-only setup)
  - 🌐 Improved web interface with better UX

- **v1.0.0** - Initial release
  - Basic data transfer functionality
  - Web interface with one-click transfer
  - Progress tracking and logging
  - Duplicate key handling
  - Automatic table creation

---

Contact me -- priyanshu345kumar@gmail.com

**Happy data transferring! 🚀**
