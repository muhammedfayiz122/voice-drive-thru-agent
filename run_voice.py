import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def main():
    """Main entry point for voice agent."""
    
    # Check required environment variables
    if not os.getenv("DEEPGRAM_API_KEY"):
        print("ERROR: DEEPGRAM_API_KEY not set in .env file")
        sys.exit(1)
    
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set in .env file")
        sys.exit(1)
    
    # Import and run voice agent
    try:
        from app.voice_system.voice_agent import run_voice_agent
        run_voice_agent()
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
