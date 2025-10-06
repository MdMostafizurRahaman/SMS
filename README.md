# 📱 SMS Sender

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5.4-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com/)

A modern, full-stack web application for bulk SMS sending to students and guardians using Excel file uploads. Built with Next.js frontend and FastAPI backend, featuring real-time SMS delivery tracking and balance monitoring.

## ✨ Features

- 📊 **Excel File Upload**: Support for .xlsx and .xls files with automatic data parsing
- 👨‍👩‍👧‍👦 **Dual Phone Numbers**: Send to both student and guardian phone numbers
- 📱 **SMS Integration**: Integrated with sms.net.bd API for reliable delivery
- 💰 **Balance Monitoring**: Real-time SMS balance checking
- 🔍 **Data Preview**: Preview extracted data before sending SMS
- 📈 **Delivery Tracking**: Track sent/failed SMS counts
- 🎨 **Modern UI**: Beautiful, responsive Bootstrap-based interface
- ⚡ **Fast Performance**: Optimized with Next.js and FastAPI
- 🔒 **Secure**: Environment-based configuration for API keys

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15.5.4
- **UI Library**: React 19.1.0
- **Styling**: Tailwind CSS 4.0
- **Icons**: Bootstrap Icons

### Backend
- **Framework**: FastAPI 0.115.6
- **ASGI Server**: Uvicorn 0.32.1
- **Data Processing**: Pandas 2.2.3
- **Excel Support**: OpenPyXL 3.1.5
- **HTTP Client**: Requests 2.32.3

### Infrastructure
- **SMS Provider**: sms.net.bd API
- **File Upload**: Python-multipart
- **Environment**: python-dotenv

## 📋 Prerequisites

Before running this application, make sure you have the following installed:

- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **Python** (3.10 or higher) - [Download](https://python.org/)
- **Git** - [Download](https://git-scm.com/)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/MdMostafizurRahaman/SMS.git
cd SMS
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install
```

### 4. Environment Configuration

Create a `.env` file in the `backend` directory:

```env
# SMS.net.bd API Configuration
SMS_API_KEY=your_sms_api_key_here
SMS_API_URL=URL
SMS_DRY_RUN=false

# CORS Origins (add your frontend URL)
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com

# Other settings
DEBUG=true
```

> **⚠️ Important**: Replace `your_sms_api_key_here` with your actual SMS.net.bd API key.

## 🎯 Usage

### Starting the Application

1. **Start Backend** (Terminal 1):
   ```bash
   cd backend
   venv\Scripts\activate  # Activate virtual environment
   python main.py
   ```
   Backend will run on `http://localhost:8000`

2. **Start Frontend** (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will run on `http://localhost:3000`

### Using the Application

1. **Open Browser**: Navigate to `http://localhost:3000`
2. **Check Balance**: Click "Check Balance" to view SMS credits
3. **Upload Excel**: Select your Excel file (.xlsx or .xls format)
4. **Preview Data**: Review the extracted student and guardian information
5. **Send SMS**: Click "Confirm & Send SMS" to dispatch messages

### Excel File Format

Your Excel file should contain columns like:
- `Student Phone No` - Student's phone number
- `Guardian Phone No` - Guardian's phone number
- `Result` - SMS message content
- Other columns will be preserved but not used for SMS

## 📡 API Documentation

### Backend Endpoints

#### `POST /upload`
Upload and parse Excel file.

**Request**: Multipart form data with `file` field
**Response**: JSON with extracted data array

#### `POST /send-sms`
Send SMS to multiple recipients.

**Request**: JSON array of recipient objects
**Response**: Success/failure counts

#### `GET /balance`
Check SMS account balance.

**Response**: Current SMS balance

## 📁 Project Structure

```
SMS/
├── backend/                    # FastAPI Backend
│   ├── main.py                # Main application file
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── uploads/               # Uploaded files directory
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.js      # Root layout
│   │   │   ├── page.js        # Main page component
│   │   │   ├── globals.css    # Global styles
│   │   │   └── favicon.ico    # App favicon
│   │   └── components/        # React components (future)
│   ├── public/                # Static assets
│   ├── package.json           # Node dependencies
│   └── next.config.mjs        # Next.js configuration
├── .gitignore                 # Git ignore rules
└── README.md                  # Project documentation
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SMS_API_KEY` | SMS.net.bd API key | Required |
| `SMS_API_URL` | SMS API endpoint | `https://api.sms.net.bd/sendsms` |
| `SMS_DRY_RUN` | Test mode (true/false) | `false` |
| `CORS_ORIGINS` | Allowed frontend URLs | `http://localhost:3000` |
| `DEBUG` | Debug mode | `true` |

## 🐛 Troubleshooting

### Common Issues

**"SMS sent to 0 numbers"**
- Check if Excel file has correct column names
- Verify phone numbers are in the right format
- Ensure SMS balance is sufficient

**"API key not configured"**
- Check your `.env` file exists and contains `SMS_API_KEY`
- Restart the backend server after adding the key

**"File upload failed"**
- Ensure file is .xlsx or .xls format
- Check file size (should be under 10MB)
- Verify file is not corrupted

**Frontend not loading**
- Ensure Node.js is installed and `npm install` was run
- Check if port 3000 is available
- Try `npm run dev` from frontend directory

### Phone Number Format
- Bangladeshi numbers: `01712345678` or `8801712345678`
- System automatically adds country code (+880) if missing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint rules for JavaScript/React
- Add tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support or questions:
- **Developer**: Md Mostafizur Rahaman
- **Email**: [your-email@example.com]
- **GitHub**: [https://github.com/MdMostafizurRahaman](https://github.com/MdMostafizurRahaman)

---

<div align="center">

**Made with ❤️ for educational institutions**

⭐ Star this repo if you found it helpful!

</div>
