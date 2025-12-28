"""
School Textbook Chatbot - Streamlit UI
=======================================
Beautiful Streamlit interface for 6th Standard English Textbook Chatbot.

Features:
- PDF Upload
- Chat interface
- Guardrails status display
- Safety metrics dashboard

Author: Sathish Suresh
Assignment: Social Eagle AI - Gen AI Architect Program
"""

import streamlit as st
import os
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()

# Must be first Streamlit command
st.set_page_config(
    page_title="📚 6th Std English Textbook Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import our RAG system
from school_rag import SchoolTextbookRAG, QualityLevel, RetrievalLevel

# Get API key from environment
API_KEY = os.getenv("OPENAI_API_KEY")


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #f5f7fa;
    }
    
    /* Header */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    }
    
    /* Chat messages */
    .student-message {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 4px solid #2196f3;
    }
    
    .bot-message {
        background-color: #f3e5f5;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 4px solid #9c27b0;
    }
    
    .blocked-message {
        background-color: #ffebee;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 4px solid #f44336;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'pdf_loaded' not in st.session_state:
    st.session_state.pdf_loaded = False

if 'document_count' not in st.session_state:
    st.session_state.document_count = 0


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 📄 Upload Textbook")
    
    # Check API Key
    if not API_KEY:
        st.error("❌ OPENAI_API_KEY not found in .env file!")
        st.info("Create a .env file with:\nOPENAI_API_KEY=sk-your-key")
        st.stop()
    
    # PDF Upload
    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=['pdf'],
        help="Upload your 6th Standard English Textbook PDF"
    )
    
    if uploaded_file:
        if st.button("📥 Load Textbook", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Initializing RAG system...")
                progress_bar.progress(10)
                
                # Initialize RAG system
                st.session_state.rag_system = SchoolTextbookRAG(
                    openai_api_key=API_KEY
                )
                progress_bar.progress(30)
                
                status_text.text("📄 Reading PDF file...")
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                progress_bar.progress(50)
                
                status_text.text("✂️ Processing content...")
                # Load PDF
                chunk_count = st.session_state.rag_system.load_pdf(tmp_path)
                progress_bar.progress(80)
                
                # Clean up
                os.unlink(tmp_path)
                progress_bar.progress(100)
                
                if chunk_count > 0:
                    st.session_state.pdf_loaded = True
                    st.session_state.document_count = chunk_count
                    status_text.empty()
                    progress_bar.empty()
                    st.success(f"✅ Loaded {chunk_count} sections!")
                else:
                    status_text.empty()
                    progress_bar.empty()
                    st.error("❌ No content extracted from PDF.")
                    st.info("💡 Try a different PDF or use Sample Data")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                error_msg = str(e)
                st.error(f"❌ Error: {error_msg}")
                
                # Helpful error messages
                if "list index" in error_msg.lower():
                    st.info("💡 The PDF might have image-based content. Try a text-based PDF.")
                elif "api" in error_msg.lower() or "key" in error_msg.lower():
                    st.info("💡 Check your OpenAI API key in .env file")
    
    # Load sample data for testing
    st.markdown("---")
    st.markdown("## 🧪 Test Mode")
    
    if st.button("📚 Load Sample Data"):
        with st.spinner("Loading sample content..."):
            try:
                st.session_state.rag_system = SchoolTextbookRAG(
                    openai_api_key=API_KEY
                )
                
                sample_texts = [
                    """Chapter 1: The Giving Tree
                    A young boy loved a tree very much. Every day he would come to play 
                    under the tree. The tree gave him shade when it was hot, apples to eat 
                    when he was hungry, and branches to swing on when he wanted to play.
                    
                    As the boy grew older, he needed more things. The tree gave him apples 
                    to sell, branches to build a house, and finally its trunk to make a boat.
                    The story teaches us about unconditional love, generosity, and sacrifice.""",
                    
                    """Chapter 1: New Words (Vocabulary)
                    - Shade: A dark area created when something blocks the sunlight
                    - Branch: A part of a tree that grows out from the trunk
                    - Trunk: The main thick stem of a tree
                    - Generous: Ready to give more than what is expected
                    - Sacrifice: Giving up something valuable for others
                    - Unconditional: Without any conditions or limits""",
                    
                    """Chapter 2: The Friendly Mongoose
                    A farmer had a pet mongoose. One day, the farmer and his wife went to 
                    the market, leaving their baby at home with the mongoose.
                    
                    When a snake entered the house and tried to harm the baby, the brave 
                    mongoose fought the snake and killed it. When the farmer's wife returned, 
                    she saw blood on the mongoose and thought it had hurt the baby.
                    
                    Without thinking, she killed the mongoose. Then she saw the dead snake 
                    and realized her terrible mistake. The story teaches us to think before 
                    we act and not to jump to conclusions.""",
                    
                    """Chapter 2: New Words (Vocabulary)
                    - Mongoose: A small animal that can kill snakes
                    - Brave: Ready to face danger
                    - Conclusion: A judgment or decision reached after thinking
                    - Terrible: Very bad or serious
                    - Mistake: Something done wrongly""",
                    
                    """Grammar: Parts of Speech
                    Nouns: Names of people, places, things, or ideas
                    Examples: boy, tree, happiness, India
                    
                    Verbs: Action words
                    Examples: run, jump, think, give
                    
                    Adjectives: Words that describe nouns
                    Examples: big, beautiful, kind, green
                    
                    Pronouns: Words used instead of nouns
                    Examples: he, she, it, they, we"""
                ]
                
                chunk_count = st.session_state.rag_system.load_text_documents(
                    sample_texts, "Sample English Textbook"
                )
                
                st.session_state.pdf_loaded = True
                st.session_state.document_count = chunk_count
                st.success(f"✅ Loaded {chunk_count} sections!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Status display
    st.markdown("---")
    st.markdown("## 📊 Status")
    
    if st.session_state.pdf_loaded:
        st.success(f"📚 Textbook Loaded")
        st.info(f"📄 {st.session_state.document_count} sections")
    else:
        st.warning("📚 No textbook loaded")
    
    # Safety metrics
    if st.session_state.rag_system:
        st.markdown("---")
        st.markdown("## 🛡️ Safety Metrics")
        metrics = st.session_state.rag_system.get_guardrail_metrics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Checks", metrics['total_input_checks'])
            st.metric("Safe", metrics['safe_queries'])
        with col2:
            blocked = (
                metrics['blocked_sexual'] + 
                metrics['blocked_violence'] + 
                metrics['blocked_bullying'] +
                metrics['blocked_drugs'] +
                metrics['blocked_cheating']
            )
            st.metric("Blocked", blocked)
            st.metric("PII Protected", metrics['pii_detected'])
    
    # Clear chat
    st.markdown("---")
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()


# ============================================================
# MAIN CONTENT
# ============================================================

# Header
st.markdown("""
<div class="header-container">
    <h1>📚 6th Standard English Textbook Chatbot</h1>
    <p>Ask questions about your English lessons! I'm here to help you learn! 🎓</p>
</div>
""", unsafe_allow_html=True)

# Check if ready
if not st.session_state.pdf_loaded:
    st.info("👈 Please upload your textbook PDF or load sample data from the sidebar")
    st.stop()

# Chat interface
st.markdown("### 💬 Chat with your Textbook")

# Display chat history
for message in st.session_state.chat_history:
    if message['role'] == 'student':
        st.markdown(f"""
        <div class="student-message">
            <strong>👦 You:</strong><br>{message['content']}
        </div>
        """, unsafe_allow_html=True)
    elif message['role'] == 'blocked':
        st.markdown(f"""
        <div class="blocked-message">
            <strong>🛡️ Safety Filter:</strong><br>{message['content']}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="bot-message">
            <strong>🤖 Study Buddy:</strong><br>{message['content']}
            <br><br>
            <small>📊 Quality: {message.get('quality', 'N/A')} | 
            🎯 Confidence: {message.get('confidence', 'N/A')} |
            📚 Sources: {message.get('sources', 'N/A')}</small>
        </div>
        """, unsafe_allow_html=True)

# Input area
st.markdown("---")

col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "Ask a question about your textbook:",
        placeholder="e.g., What is the story about? What does 'generous' mean?",
        key="user_input",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("📤 Send", type="primary", use_container_width=True)

# Process input
if send_button and user_input:
    # Add student message to history
    st.session_state.chat_history.append({
        'role': 'student',
        'content': user_input
    })
    
    # Get response
    with st.spinner("🤔 Thinking..."):
        response = st.session_state.rag_system.query(user_input, verbose=False)
    
    # Add response to history
    if response.guardrail_passed:
        st.session_state.chat_history.append({
            'role': 'bot',
            'content': response.answer,
            'quality': response.context_quality.value,
            'confidence': response.confidence,
            'sources': ', '.join(response.sources) if response.sources else 'General knowledge'
        })
    else:
        st.session_state.chat_history.append({
            'role': 'blocked',
            'content': response.answer
        })
    
    # Rerun to show updated chat
    st.rerun()

# Example questions
st.markdown("---")
st.markdown("### 💡 Try these questions:")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📖 What is Chapter 1 about?"):
        st.session_state.example_query = "What is the story in Chapter 1 about?"
        st.rerun()

with col2:
    if st.button("📝 Explain vocabulary words"):
        st.session_state.example_query = "What are the new vocabulary words?"
        st.rerun()

with col3:
    if st.button("📚 What is a noun?"):
        st.session_state.example_query = "What is a noun? Give examples."
        st.rerun()

# Handle example queries
if 'example_query' in st.session_state:
    query = st.session_state.example_query
    del st.session_state.example_query
    
    st.session_state.chat_history.append({
        'role': 'student',
        'content': query
    })
    
    with st.spinner("🤔 Thinking..."):
        response = st.session_state.rag_system.query(query, verbose=False)
    
    if response.guardrail_passed:
        st.session_state.chat_history.append({
            'role': 'bot',
            'content': response.answer,
            'quality': response.context_quality.value,
            'confidence': response.confidence,
            'sources': ', '.join(response.sources) if response.sources else 'General knowledge'
        })
    else:
        st.session_state.chat_history.append({
            'role': 'blocked',
            'content': response.answer
        })
    
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>🛡️ This chatbot is protected by Guardrails to ensure safe learning environment for students</p>
    <p>Made with ❤️ for 6th Standard Students | Social Eagle AI - Gen AI Architect Program</p>
</div>
""", unsafe_allow_html=True)
