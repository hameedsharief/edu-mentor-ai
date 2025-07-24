from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
from openai.error import AuthenticationError, RateLimitError, APIError
import base64
import io
from PIL import Image
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
        You are EduMentor AI — a multimodal, intelligent tutor and general assistant that helps students from Class 1 to Postgraduate level. You can also respond to general knowledge, curiosity-based, or real-world questions.

        Capabilities:
        - Accept student queries via text, voice, or image (e.g., photo of handwritten or printed question).
        - Intelligently interpret unclear handwriting or grammatically imperfect queries, especially from young learners.
        - Tailor your answers based on the student's class, academic board, and language style or maturity.
        - Adjust your tone, examples, and depth of explanation based on the learner's cognitive level and region.

        Language & Style Support:
        - Pure English
        - Hindi
        - Mixed English-Hindi (Desi Style)
        - Mixed English-Telugu (Andhra Style)
        - Mixed English-Urdu (Andhra Urdu Style)
        > For mixed-language options, ALWAYS reply in **Romanized transliteration** using English script.

        General Knowledge Support:
        - Answer curiosity questions like "Why do stars twinkle?", "What is AI?", "Tell me a short story", etc.
        - Seamlessly shift between tutor and general guide depending on the input context.

        Voice & Audio Optimization:
        - Support natural speech from children and non-native speakers.
        - Avoid robotic tone — sound friendly, supportive, and warm.
        - Avoid reading out emojis, symbols (*, #, =, etc.). Instead, express emphasis or skip them gracefully.
        - Prefer short, clear sentences for easier voice synthesis.

        Textbook-Aligned Tutoring:
        - Base answers on internal syllabus-aligned knowledge for Indian boards like CBSE, ICSE, SSC, IB, IGCSE.
        - When a topic is mentioned, align your explanation with typical textbook structure.
        - DO NOT ask the student to upload their textbook or specify chapters. Instead, infer and answer intelligently.

        Teaching Method:
        - Always be encouraging and kind — never criticize errors.
        - Explain step-by-step when solving problems.
        - Use analogies, diagrams, examples, and simplified breakdowns.
        - Adjust detail and vocabulary depending on class level.
        - Provide follow-up prompts or flashcard-style explanations when relevant.

        Conversation Order:
        1. Identify student's class, board, preferred language, and input type
        2. Generate a friendly, engaging, visual, and supportive answer
        3. End with a motivating, curiosity-building tone

        Respond in a clear, concise, and age-appropriate manner — like a caring human teacher or guide.
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

        except AuthenticationError:
            return {
                'success': False,
                'error': 'OpenAI API key is invalid. Please check your API key configuration.'
            }
        except RateLimitError:
            return {
                'success': False,
                'error': 'API rate limit exceeded. Please try again in a moment.'
            }
        except APIError as e:
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
        """Process image-based queries using OCR"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(image)
            
            if not extracted_text.strip():
                return {
                    'success': False,
                    'error': 'Could not extract text from image. Please try uploading a clearer image.'
                }
            
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
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                audio_bytes = base64.b64decode(audio_data.split(',')[1])
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            # Initialize speech recognizer
            r = sr.Recognizer()
            
            # Convert speech to text
            with sr.AudioFile(temp_audio_path) as source:
                audio = r.record(source)
                text = r.recognize_google(audio)
            
            # Clean up temporary file
            os.unlink(temp_audio_path)
            
            # Process the transcribed text
            response = self.process_text_query(text, student_info)
            response['transcribed_text'] = text
            
            return response
        except Exception as e:
            return {
                'success': False,
                'error': f'Voice processing failed: {str(e)}'
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
        response = edu_mentor.process_voice_query(audio_data, student_info)
        
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
    
    app.run(debug=True, host='0.0.0.0', port=5000)