def process_voice_query_simple(self, audio_data, student_info):
        """Simplified voice processing - fallback method"""
        try:
            # For now, return a helpful message about voice input
            return {
                'success': True,
                'response': f"I heard your voice message! However, voice-to-text processing needs some additional setup. For now, please type your question in the text box and I'll be happy to help! 🎤➡️📝",
                'transcribed_text': "[Voice input received - please type your question]",
                'timestamp': datetime.now().isoformat(),
                'note': 'Voice processing temporarily disabled - needs FFmpeg installation'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Voice processing error: {str(e)}'
            }
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
#from openai.error import AuthenticationError, RateLimitError, APIError
import base64
import io
from PIL import Image
from PIL import ImageEnhance, ImageFilter
import pytesseract
import speech_recognition as sr
import tempfile
import os
from datetime import datetime
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Verify API key is loaded
if not openai.api_key:
    print("WARNING: OPENAI_API_KEY not found in environment variables!")
    print("Please set your OpenAI API key in a .env file or environment variable.")
else:
    print("✓ OpenAI API key loaded successfully")

# Student session storage (in production, use a proper database)
student_sessions = {}
class EduMentorAI:
    def __init__(self):
        self.system_prompt = """
        🧠 Capabilities:
            Accept student questions via:
				Text
				Voice            
				Image (including printed questions, textbook photos, and handwritten homework) 
			  
            Accurately interpret:            
				Handwritten notes, even if messy, casual, or incomplete
				Imperfect grammar or spelling, especially from young learners
				Partial queries, inferring intelligently using context

			Understand student's:
				Class level (e.g., Class 5, PG)
				Academic board (CBSE, ICSE, SSC, IB, IGCSE)
				Preferred language style (English, Desi Mix, Telugu-English, Urdu-English)

📝 When students upload images (e.g., homework diary):
	Use OCR to extract visible text (printed or handwritten)
	Prioritize understanding handwritten content
	If homework-related:
		Summarize the tasks
		Offer guidance on how to complete them
		Provide relevant support material, like steps, examples, or concepts

	If handwriting is unclear:
		Infer intelligently
		Politely ask for clarification or better images if needed

🗣️ Language & Style Support:
	✅ Pure English
	✅ Hindi
	✅ English-Hindi (Desi Style)
	✅ English-Telugu (Andhra Style)
	✅ English-Urdu (Andhra Urdu Style)

	❗ For mixed styles, reply in Romanized transliteration using English letters — never use native scripts like देवनागरी or اردو.

📚 Textbook-Aligned Tutoring:
	Use internal syllabus-aligned explanations for major Indian boards
	DO NOT ask for chapter names or textbook uploads
	When a topic is mentioned, intelligently align your explanation to the typical textbook structure

🧑‍🏫 Teaching Method:
	Be friendly, patient, and encouraging
	Use step-by-step explanations
	Include:
		Examples
		Analogies
		Diagrams (if referenced)
		Simplified concepts based on student’s level

	Prompt students with follow-up questions or curiosity boosters

🔊 Voice & Audio Optimization:
	Keep sentences short and clear for text-to-speech
	Avoid reading special symbols like #, *, =
	Respond in a natural, non-robotic tone

📐 Response Formatting Guidelines:
	Use clean and engaging Markdown formatting:

✅ Use bold for:
	Important terms
	Definitions
	Key concepts

✅ Use bullet points:
	Use - or numbered 1. 2. 3. format
	Put each point on a new line
✅ Use emojis sparingly:
	Help highlight key ideas (e.g. 🌱, 💡, 📘, ➕)
	Do not overuse
✅ Use short paragraphs:
	Max 2–3 sentences per paragraph
	Avoid long blocks of text

💡 Example Format:
Photosynthesis is the process by which plants make their own food. 🌿
Steps:
	Sunlight is absorbed by chlorophyll in the leaves.
	Carbon dioxide enters from the air.
	Water comes from the roots.
	The plant makes glucose and releases oxygen.

🧭 Conversation Flow:
	Understand the student’s class, board, and language preference
	Determine the input type: text, voice, or image
	Provide:
		A clear, structured, and age-appropriate answer
		Help with understanding homework if from image
		Motivation and encouragement
		Follow-up suggestions or curiosity prompts
		
Respond like a caring, intelligent teacher who adapts your language, tone, and depth to the student’s age, style, and input type.
"""

    def process_text_query(self, query, student_info):
        """Process text-based queries using OpenAI API"""
        try:
            # Check if OpenAI API key is available
            if not openai.api_key:
                return {
                    'success': True,
                    'response': self.generate_demo_response(query, student_info),
                    'timestamp': datetime.now().isoformat(),
                    'note': 'Using demo mode - OpenAI API key not configured'
                }

            # Format the query with student context
            student_context = f"""
Student Information:
- Class/Level: {student_info.get('class', 'Not specified')}
- Academic Board: {student_info.get('board', 'Not specified')}
- Language Preference: {student_info.get('language', 'English')}
- Name: {student_info.get('name', 'Student')}

Instructions: You are EduMentor AI. Respond according to the student's class level and language preference. 
Be encouraging, educational, and age-appropriate. Use simple language for younger students and more detailed 
explanations for older students. If the language preference includes mixed languages, respond in Romanized 
transliteration using English script only.
"""

            user_message = f"{student_context}\n\nStudent's Question: {query}"

            # Make API call to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'response': ai_response,
                'timestamp': datetime.now().isoformat()
            }

        except openai.AuthenticationError:
            return {
                'success': False,
                'error': 'OpenAI API key is invalid. Please check your API key configuration.'
            }
        except openai.RateLimitError:
            return {
                'success': False,
                'error': 'API rate limit exceeded. Please try again in a moment.'
            }
        except openai.APIError as e:
            return {
                'success': False,
                'error': f'OpenAI API error: {str(e)}'
            }
        except Exception as e:
            # Fallback to demo response if API fails
            return {
                'success': True,
                'response': self.generate_demo_response(query, student_info),
                'timestamp': datetime.now().isoformat(),
                'note': f'Using demo mode due to error: {str(e)}'
            }

    def process_image_query(self, image_data, student_info):
        """Process image-based queries using enhanced OCR for handwriting"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_bytes)).convert("L")  # Convert to grayscale

             # Apply preprocessing to enhance handwriting
            image = image.filter(ImageFilter.MedianFilter())  # Reduce noise
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.5)  # Boost contrast
            image = image.point(lambda x: 0 if x < 140 else 255)  # Binarize (threshold)

            # Enhance image for OCR (optional: binarize, sharpen, etc.)
            #image = image.point(lambda x: 0 if x < 150 else 255)  # Simple thresholding

            # Optional save for debugging
            # image.save("preprocessed.png")

            # Use pytesseract with appropriate config for handwriting
            custom_config = r'--oem 3 --psm 6'  # OEM 3 = default + LSTM; PSM 6 = block of text
            extracted_text = pytesseract.image_to_string(image, config=custom_config)

            # OCR config optimized for handwritten-like text
            #ocr_config = "--psm 6"  # Assume a block of text
            
            # Extract text using OCR
            #extracted_text = pytesseract.image_to_string(image, config=ocr_config)
            
            if not extracted_text.strip():
                return {
                    'success': False,
                    'error': '❌ Could not read handwriting. Please upload a clearer image or retake the photo.'
                }

            print("📄 OCR Extracted Text:", extracted_text)
            
            # Process the extracted text
            response = self.process_text_query(extracted_text, student_info)
            response['extracted_text'] = extracted_text
            
            return response
        except Exception as e:
            return {
                'success': False,
                'error': f'Image processing failed: {str(e)}'
            }

    def process_voice_query(self, audio_data, student_info):
        """Process voice-based queries using speech recognition"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data.split(',')[1])
            
            # Create temporary file with proper extension
            temp_audio_path = None
            
            try:
                # Try to convert audio to WAV format using PIL/Pillow audio processing
                # First, save the original audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_original:
                    temp_original.write(audio_bytes)
                    temp_original_path = temp_original.name
                
                # Convert to WAV using system command (fallback method)
                temp_wav_path = temp_original_path.replace('.webm', '.wav')
                
                try:
                    # Try using pydub for audio conversion
                    from pydub import AudioSegment
                    from pydub.utils import which
                    
                    # Load the audio file
                    if audio_data.startswith('data:audio/webm'):
                        audio = AudioSegment.from_file(temp_original_path, format="webm")
                    elif audio_data.startswith('data:audio/mp4'):
                        audio = AudioSegment.from_file(temp_original_path, format="mp4")
                    else:
                        # Try as wav first
                        audio = AudioSegment.from_file(temp_original_path, format="wav")
                    
                    # Export as WAV
                    audio.export(temp_wav_path, format="wav")
                    temp_audio_path = temp_wav_path
                    
                except ImportError:
                    # Pydub not available, try direct approach
                    print("Warning: pydub not installed. Trying direct audio processing...")
                    
                    # Rename the file to .wav and hope it works
                    import shutil
                    shutil.copy(temp_original_path, temp_wav_path)
                    temp_audio_path = temp_wav_path
                
                except Exception as conversion_error:
                    print(f"Audio conversion error: {conversion_error}")
                    # Try using the original file directly
                    temp_audio_path = temp_original_path
                
                # Initialize speech recognizer
                r = sr.Recognizer()
                
                # Adjust for ambient noise and recognition settings
                with sr.AudioFile(temp_audio_path) as source:
                    # Adjust for ambient noise
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    # Record the audio
                    audio = r.record(source)
                
                # Try multiple recognition services for better accuracy
                recognized_text = None
                
                try:
                    # Try Google Speech Recognition (free)
                    recognized_text = r.recognize_google(audio, language='en-IN')  # Indian English
                except sr.UnknownValueError:
                    try:
                        # Fallback to US English
                        recognized_text = r.recognize_google(audio, language='en-US')
                    except sr.UnknownValueError:
                        try:
                            # Try with different audio settings
                            recognized_text = r.recognize_google(audio)
                        except sr.UnknownValueError:
                            return {
                                'success': False,
                                'error': 'Could not understand the audio. Please speak clearly and try again.'
                            }
                except sr.RequestError as e:
                    return {
                        'success': False,
                        'error': f'Speech recognition service error: {str(e)}. Please try again later.'
                    }
                
                if not recognized_text:
                    return {
                        'success': False,
                        'error': 'No speech detected. Please speak louder and try again.'
                    }
                
            finally:
                # Clean up temporary files
                try:
                    if temp_audio_path and os.path.exists(temp_audio_path):
                        os.unlink(temp_audio_path)
                    if 'temp_original_path' in locals() and os.path.exists(temp_original_path):
                        os.unlink(temp_original_path)
                    if 'temp_wav_path' in locals() and temp_wav_path != temp_audio_path and os.path.exists(temp_wav_path):
                        os.unlink(temp_wav_path)
                except Exception as cleanup_error:
                    print(f"Cleanup error: {cleanup_error}")
            
            # Process the transcribed text
            response = self.process_text_query(recognized_text, student_info)
            response['transcribed_text'] = recognized_text
            
            return response
            
        except Exception as e:
            print(f"Voice processing error: {str(e)}")
            return {
                'success': False,
                'error': f'Voice processing failed: {str(e)}. Please try again or use text input.'
            }

    def generate_demo_response(self, query, student_info):
        """Generate enhanced demo responses based on query patterns"""
        query_lower = query.lower()
        class_level = student_info.get('class', '').lower()
        language = student_info.get('language', 'English')
        student_name = student_info.get('name', 'my friend')
        
        # Determine response complexity based on class
        is_primary = any(x in class_level for x in ['1', '2', '3', '4', '5', 'primary'])
        is_secondary = any(x in class_level for x in ['6', '7', '8', '9', '10', 'secondary'])
        is_senior = any(x in class_level for x in ['11', '12', 'senior', 'plus'])
        
        # Enhanced responses for different topics
        if any(word in query_lower for word in ['artificial intelligence', 'ai', 'machine learning']):
            if is_primary:
                return f"Hello {student_name}! Artificial Intelligence (AI) is like making computers think and learn like humans! 🤖\n\nThink of it this way:\n- When you play games on a tablet, the computer learns how you play\n- When you ask Alexa or Google something, that's AI helping you\n- AI helps cars drive themselves and helps doctors find diseases\n\nAI is everywhere around us, making our lives easier! It's like having a very smart computer friend who keeps learning new things every day.\n\nWould you like to know about any specific AI things you see around you?"
            elif is_secondary:
                return f"Great question, {student_name}! Artificial Intelligence (AI) is a branch of computer science that creates smart machines capable of performing tasks that typically require human intelligence.\n\nKey aspects of AI:\n\n🧠 **What AI does:**\n- Recognizes speech and images\n- Makes decisions based on data\n- Learns from experience (Machine Learning)\n- Solves complex problems\n\n🔧 **Types of AI:**\n- **Narrow AI:** Specific tasks (like Siri, recommendation systems)\n- **General AI:** Human-level intelligence (still being developed)\n\n🌟 **Real-world examples:**\n- Netflix suggesting movies you might like\n- Google Translate converting languages\n- Face recognition in photos\n- Medical diagnosis assistance\n\nAI works by processing lots of data and finding patterns, just like how you learn to recognize your friends' faces by seeing them many times!\n\nWhat specific aspect of AI interests you most?"
            else:
                return f"Excellent question, {student_name}! Artificial Intelligence represents one of the most transformative fields in modern computer science and technology.\n\n🎯 **Fundamental Definition:**\nAI encompasses computational systems designed to simulate, replicate, or augment human cognitive processes including learning, reasoning, perception, and decision-making.\n\n🔬 **Core Components:**\n\n**Machine Learning (ML):**\n- Supervised learning (labeled data training)\n- Unsupervised learning (pattern discovery)\n- Reinforcement learning (reward-based optimization)\n\n**Deep Learning:**\n- Neural networks with multiple hidden layers\n- Convolutional Neural Networks (CNNs) for image processing\n- Recurrent Neural Networks (RNNs) for sequence data\n\n**Natural Language Processing (NLP):**\n- Text analysis and generation\n- Sentiment analysis and language translation\n- Conversational AI and chatbots\n\n🚀 **Current Applications:**\n- Computer Vision (autonomous vehicles, medical imaging)\n- Predictive Analytics (financial markets, weather forecasting)\n- Robotics and automation\n- Personalization algorithms\n\n🔮 **Future Implications:**\nAI is driving the Fourth Industrial Revolution, with potential for Artificial General Intelligence (AGI) and eventual technological singularity.\n\nWhich specific domain of AI would you like to explore further - perhaps neural networks, ethical AI, or practical applications in your field of interest?"
        
        elif any(word in query_lower for word in ['photosynthesis']):
            if is_primary:
                return f"Hi {student_name}! Plants make their own food using sunlight! 🌱☀️\n\nIt's like cooking, but plants use:\n- Sunlight (like heat for cooking)\n- Water (from their roots)\n- Air (through tiny holes in leaves)\n\nWhen plants mix these together, they make sugar (their food) and give us fresh oxygen to breathe!\n\nThat's why we need to take care of plants - they help us breathe! 🌿\n\nDo you have any plants at home you'd like to know more about?"
            elif is_secondary:
                return f"Great question, {student_name}! Photosynthesis is how plants make their own food using sunlight energy.\n\n🌿 **The Process:**\n6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂\n\n**What happens:**\n1. **Light absorption:** Chlorophyll in leaves captures sunlight\n2. **Water splitting:** Roots absorb water, which gets broken down\n3. **Carbon dioxide intake:** Stomata (leaf pores) take in CO₂ from air\n4. **Glucose production:** These combine to make glucose (plant food)\n5. **Oxygen release:** O₂ is released as a bonus for us!\n\n**Two main stages:**\n- **Light reactions:** In thylakoids, convert light to chemical energy\n- **Calvin cycle:** In stroma, use that energy to make glucose\n\n🌍 **Why it matters:**\n- Produces oxygen we breathe\n- Forms the base of all food chains\n- Removes CO₂ from atmosphere\n\nThis process happens in chloroplasts - the green parts of plants!\n\nWant to know more about any specific part of this process?"
            else:
                return f"Excellent question, {student_name}! Photosynthesis is a complex biochemical process fundamental to life on Earth.\n\n🔬 **Molecular Mechanism:**\n\n**Overall Equation:**\n6CO₂ + 6H₂O + photons → C₆H₁₂O₆ + 6O₂ + 6H₂O\n\n**Phase 1: Light-Dependent Reactions (Thylakoid Membrane)**\n- **Photosystem II (P680):** Water photolysis, oxygen evolution\n- **Electron Transport Chain:** Plastoquinone → Cytochrome b6f → Plastocyanin\n- **Photosystem I (P700):** NADP+ reduction to NADPH\n- **Chemiosmosis:** ATP synthesis via ATP synthase\n\n**Phase 2: Calvin-Benson-Bassham Cycle (Stroma)**\n- **Carboxylation:** RuBisCO catalyzes CO₂ fixation to RuBP\n- **Reduction:** 3-phosphoglycerate → glyceraldehyde-3-phosphate\n- **Regeneration:** RuBP regeneration for cycle continuation\n\n**Regulatory Mechanisms:**\n- Light regulation of enzyme activity\n- Stomatal conductance optimization\n- C4 and CAM adaptations for water/CO₂ efficiency\n\n**Global Significance:**\n- Primary productivity: ~120 Gt C/year globally\n- Atmospheric O₂ maintenance (~21%)\n- Climate regulation through carbon sequestration\n\nWhich aspect interests you most - the biochemical pathways, evolutionary adaptations, or environmental implications?"
        
        elif any(word in query_lower for word in ['math', 'mathematics', 'algebra', 'equation', 'solve']):
            return f"I'd love to help you with mathematics, {student_name}! 📊\n\nFor solving problems effectively:\n\n1️⃣ **Understand the problem** - Read carefully\n2️⃣ **Identify what you know** - List given information\n3️⃣ **Find what you need** - What are you solving for?\n4️⃣ **Choose the right method** - Formula, equation, or strategy\n5️⃣ **Solve step by step** - Show all work\n6️⃣ **Check your answer** - Does it make sense?\n\nFor your class level ({student_info.get('class', 'your level')}), focus on understanding concepts rather than just memorizing formulas.\n\nCan you share the specific math problem you're working on? I'll guide you through it step by step! 🎯"
        
        elif any(word in query_lower for word in ['science', 'physics', 'chemistry', 'biology']):
            return f"Science is amazing, {student_name}! 🔬✨\n\nScience helps us understand how everything works around us - from tiny atoms to massive galaxies!\n\n🧪 **The scientific method:**\n1. Observe something interesting\n2. Ask questions about it\n3. Form a hypothesis (educated guess)\n4. Test it with experiments\n5. Analyze results and draw conclusions\n\nFor {student_info.get('class', 'your level')}, focus on:\n- Making observations\n- Asking \"why\" and \"how\" questions\n- Connecting science to daily life\n- Hands-on experiments when possible\n\nWhat specific science topic or question do you have? Let's explore it together! 🌟"
        
        else:
            # Generic encouraging response
            student_class = student_info.get('class', 'your level')
            return f"That's a wonderful question, {student_name}! 🌟\n\nI can see you're curious and thinking deeply - that's exactly how great learners approach new topics!\n\nFor {student_class} students, I always recommend:\n- Breaking complex topics into smaller parts\n- Connecting new information to what you already know\n- Asking follow-up questions (like you're doing now!)\n- Using examples from your daily life\n\nCould you tell me more specifically what aspect of this topic you'd like to explore? The more details you give me about what you're curious about, the better I can tailor my explanation to help you understand it perfectly!\n\nRemember: Every expert was once a beginner, and every question you ask makes you smarter! 🎯"

# Initialize EduMentor AI
edu_mentor = EduMentorAI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/student/register', methods=['POST'])
def register_student():
    """Register or update student information"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        student_info = {
            'class': data.get('class', ''),
            'board': data.get('board', ''),
            'language': data.get('language', 'English'),
            'name': data.get('name', ''),
            'registered_at': datetime.now().isoformat()
        }
        
        student_sessions[session_id] = student_info
        
        return jsonify({
            'success': True,
            'message': 'Student information registered successfully',
            'student_info': student_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query/text', methods=['POST'])
def handle_text_query():
    """Handle text-based queries"""
    try:
        data = request.json
        session_id = data.get('session_id')
        query = data.get('query')
        
        if not session_id or session_id not in student_sessions:
            return jsonify({
                'success': False,
                'error': 'Student session not found. Please register first.'
            }), 400
        
        student_info = student_sessions[session_id]
        response = edu_mentor.process_text_query(query, student_info)
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query/image', methods=['POST'])
def handle_image_query():
    """Handle image-based queries"""
    try:
        data = request.json
        session_id = data.get('session_id')
        image_data = data.get('image_data')
        
        if not session_id or session_id not in student_sessions:
            return jsonify({
                'success': False,
                'error': 'Student session not found. Please register first.'
            }), 400
        
        student_info = student_sessions[session_id]
        response = edu_mentor.process_image_query(image_data, student_info)
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query/voice', methods=['POST'])
def handle_voice_query():
    """Handle voice-based queries"""
    try:
        data = request.json
        session_id = data.get('session_id')
        audio_data = data.get('audio_data')
        
        if not session_id or session_id not in student_sessions:
            return jsonify({
                'success': False,
                'error': 'Student session not found. Please register first.'
            }), 400
        
        student_info = student_sessions[session_id]
          # Try full voice processing first, fallback to simple if it fails

        try:

            response = edu_mentor.process_voice_query(audio_data, student_info)

        except Exception as voice_error:

            print(f"Full voice processing failed: {voice_error}")

            response = edu_mentor.process_voice_query_simple(audio_data, student_info)
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/student/info/<session_id>', methods=['GET'])
def get_student_info(session_id):
    """Get student information"""
    if session_id not in student_sessions:
        return jsonify({
            'success': False,
            'error': 'Student session not found'
        }), 404
    
    return jsonify({
        'success': True,
        'student_info': student_sessions[session_id]
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("=== EduMentor AI Setup Instructions ===")
    print("1. Make sure 'index.html' is in the 'templates' folder")
    print("2. Make sure 'script.js' is in the 'static' folder")
    print("3. Current directory structure should be:")
    print("   ├── main.py")
    print("   ├── templates/")
    print("   │   └── index.html")
    print("   └── static/")
    print("       └── script.js")
    print("========================================")
    print("🌐 ACCESS OPTIONS:")
    print("- Local access: http://localhost:5000")
    print("- Network access: http://YOUR_IP:5000")
    print("🎤 MICROPHONE NOTES:")
    print("- Localhost: Full microphone access")
    print("- IP address: May need HTTPS for microphone")
    print("- Grant permissions when browser asks")
    print("========================================")

    # Get local IP address for convenience
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"📡 Your local IP: {local_ip}")
        print(f"🔗 Network URL: http://{local_ip}:5000")
    except:
        print("📡 Could not determine local IP")
    # For production with HTTPS, uncomment these lines:
    # app.run(debug=True, host='0.0.0.0', port=5000, ssl_context='adhoc')
    # For development (current setup)
    # Run Flask development server (works with IP access)

    app.run(
        debug=True, 
        host='0.0.0.0',  # Allow external connections
        port=5000,
        threaded=True    # Handle multiple requests
    )