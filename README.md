# EduMentor AI - Multimodal Student Tutoring System

A comprehensive AI-powered tutoring application that supports students from Class 1 to Postgraduate level through text, image, and voice interactions.

## 🚀 Features

- **Multimodal Input Support**: Text, image (OCR), and voice recognition
- **Adaptive Learning**: Responses tailored to student's class level and academic board
- **Language Support**: English, Hindi, and mixed language options (Romanized)
- **Indian Education System**: Supports CBSE, ICSE, SSC, IB, IGCSE boards
- **Real-time Chat Interface**: Interactive conversation history
- **Session Management**: Persistent student profiles
- **Responsive Design**: Works on desktop and mobile devices

## 📁 Project Structure

```
edumentor-ai/
├── main.py              # Flask backend server
├── templates/           # HTML templates directory
│   └── index.html      # Main frontend interface
├── static/             # Static files directory
│   └── script.js       # Frontend JavaScript
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🛠️ Installation & Setup

### Prerequisites

1. **Python 3.7+** installed on your system
2. **Tesseract OCR** for image text extraction
3. **Microphone access** for voice input (optional)

### Step 1: Install Tesseract OCR

#### Windows:
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Verify: `tesseract --version`

#### macOS:
```bash
brew install tesseract
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### Step 2: Clone and Setup Project

```bash
# Create project directory
mkdir edumentor-ai
cd edumentor-ai

# Create required directories
mkdir templates static

# Copy the provided files to correct locations:
# - main.py → root directory
# - index.html → templates/index.html
# - script.js → static/script.js
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Create requirements.txt

Create a `requirements.txt` file with the following content:

```txt
Flask==2.3.3
Flask-CORS==4.0.0
Pillow==10.0.1
pytesseract==0.3.10
SpeechRecognition==3.10.0
openai==1.3.5
python-multipart==0.0.6
python-dotenv==1.0.0
```

### Step 5: Directory Structure Correction

**IMPORTANT**: Make sure your files are in the correct locations:

```
edumentor-ai/
├── main.py                    # Root directory
├── requirements.txt           # Root directory
├── templates/                 # Templates folder
│   └── index.html            # HTML file goes here
└── static/                    # Static files folder
    └── script.js             # JavaScript file goes here
```

### Step 6: Update main.py for Correct Paths

Update the Flask route in `main.py`:

```python
@app.route('/')
def index():
    return render_template('index.html')  # Flask will look in templates/ folder
```

And update the HTML file to reference the correct JavaScript path:

```html
<!-- At the bottom of index.html, change: -->
<script src="script.js"></script>
<!-- To: -->
<script src="{{ url_for('static', filename='script.js') }}"></script>
```

## 🚀 Running the Application

```bash
# Make sure you're in the project directory
cd edumentor-ai

# Activate virtual environment if not already activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run the Flask application
python main.py
```

The application will be available at: `http://localhost:5000`

## 🔧 Configuration

### AI Service Integration

#### **OpenAI Integration (Recommended)**:

1. **Create a `.env` file** in your project root:
   ```env
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

2. **Get your OpenAI API key**:
   - Visit https://platform.openai.com/api-keys
   - Create an account or log in
   - Generate a new API key
   - Copy the key to your `.env` file

3. **Install python-dotenv** (included in requirements.txt):
   ```bash
   pip install python-dotenv
   ```

The application will automatically detect your API key and use OpenAI's GPT-3.5-turbo model for intelligent responses. If no API key is found, it will fall back to enhanced demo responses.

#### **API Key Security**:
- Never commit your `.env` file to version control
- Add `.env` to your `.gitignore` file
- Use environment variables in production

### Environment Variables (Optional)

Create a `.env` file for sensitive configurations:

```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

## 🎯 Usage Guide

### 1. Student Registration
- Enter student name (optional)
- Select class level (Class 1 to Postgraduate)
- Choose academic board (CBSE, ICSE, etc.)
- Pick language preference
- Click "Save Information"

### 2. Asking Questions

#### Text Input:
- Type questions in the text area
- Press Ctrl+Enter or click "Ask Question"
- Example: "Explain photosynthesis for Class 7 CBSE"

#### Image Input:
- Click "Image" tab
- Upload or drag-drop an image with questions
- Click "Analyze Image"
- Supports handwritten and printed text

#### Voice Input:
- Click "Voice" tab
- Click microphone button to start recording
- Speak your question clearly
- Click stop button when finished

## 🔍 Troubleshooting

### Common Issues:

1. **TemplateNotFound Error**:
   ```
   Solution: Ensure index.html is in templates/ folder
   ```

2. **Static Files Not Loading**:
   ```
   Solution: Ensure script.js is in static/ folder
   Update HTML to use: {{ url_for('static', filename='script.js') }}
   ```

3. **Tesseract Not Found**:
   ```
   Solution: Install Tesseract OCR and add to system PATH
   ```

4. **Microphone Access Denied**:
   ```
   Solution: Allow microphone permissions in browser
   Use HTTPS for production deployment
   ```

5. **Import Errors**:
   ```bash
   # Install missing packages
   pip install package_name
   ```

### Debug Mode

Run in debug mode for development:

```python
# In main.py, change:
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 🚀 Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y tesseract-ocr

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
```

## 📊 Performance Optimization

### For Large Scale Deployment:

1. **Database Integration**: Replace in-memory storage with PostgreSQL/MongoDB
2. **Redis Caching**: Add session caching with Redis
3. **Load Balancing**: Use Nginx for load balancing
4. **CDN**: Serve static files through CDN
5. **Async Processing**: Use Celery for heavy tasks

## 🛡️ Security Considerations

1. **API Rate Limiting**: Implement rate limiting for API endpoints
2. **Input Validation**: Validate and sanitize all user inputs
3. **File Upload Security**: Restrict file types and sizes
4. **HTTPS**: Use SSL certificates in production
5. **Environment Variables**: Store secrets in environment variables

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Verify all dependencies are correctly installed

## 🔄 Version History

- **v1.0.0**: Initial release with multimodal support
- Features: Text, image, and voice input processing
- Support for Indian education boards
- Responsive web interface

---

**Note**: This application is designed to handle millions of students with proper infrastructure scaling. For production deployment, consider using cloud services like AWS, Google Cloud, or Azure with appropriate scaling configurations.