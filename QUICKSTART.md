# Quick Start Guide

Get your MySQL database transfer running in 5 minutes!

## 🚀 Super Quick Setup

### Windows Users
1. Double-click `start.bat`
2. Follow the prompts
3. Open browser to `http://localhost:5000`

### Mac/Linux Users
```bash
chmod +x start.sh
./start.sh
```

## ⚙️ Manual Setup (if needed)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database
```bash
copy config.json.template config.json    # Windows
cp config.json.template config.json      # Mac/Linux
```

Edit `config.json` with your database credentials:
```json
{
  "source_db": {
    "host": "localhost",
    "database": "source_db_name",
    "user": "username",
    "password": "password"
  },
  "target_db": {
    "host": "localhost", 
    "database": "target_db_name",
    "user": "username",
    "password": "password"
  },
  "tables": ["table1", "table2", "table3"]
}
```

### 3. Start the Application
```bash
python app.py
```

### 4. Transfer Data
- Open `http://localhost:5000` in your browser
- Click "Transfer Data" button
- Watch the magic happen! ✨

## 🔧 Command Line Alternative
```bash
python db_transfer.py
```

## 📋 Requirements Checklist
- [ ] Python 3.7+ installed
- [ ] MySQL server running
- [ ] Database credentials ready
- [ ] Source database has data
- [ ] Target database exists (can be empty)

## 🆘 Quick Troubleshooting
- **Can't connect to database?** Check credentials in `config.json`
- **Config file missing?** Copy `config.json.template` to `config.json`
- **Permission errors?** Make sure database user has proper permissions
- **Port 5000 busy?** Set `PORT=8080` environment variable

## 📖 More Help
- Read `README.md` for detailed instructions
- Check `transfer.log` for detailed logs
- Visit the Configuration page in the web interface

---
**Ready to transfer? Let's go! 🎯**
