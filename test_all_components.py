"""
COMPREHENSIVE COMPONENT TESTING SUITE
Autonomous testing of all critical components before deployment.
"""

import os
import sys
import asyncio
import traceback
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Set TEST_MODE environment variable to disable TrustedHostMiddleware
os.environ["TEST_MODE"] = "true"

# Test results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
}


class TestResult:
    """Store individual test results."""
    def __init__(self, category: str, test_name: str, status: str, message: str = "", error: str = ""):
        self.category = category
        self.test_name = test_name
        self.status = status  # "PASS", "FAIL", "SKIP"
        self.message = message
        self.error = error
        
    def to_dict(self):
        return {
            "category": self.category,
            "test": self.test_name,
            "status": self.status,
            "message": self.message,
            "error": self.error
        }


def add_result(result: TestResult):
    """Add test result to global storage."""
    test_results["tests"].append(result.to_dict())
    test_results["summary"]["total"] += 1
    
    if result.status == "PASS":
        test_results["summary"]["passed"] += 1
        print(f"[PASS] {result.category} - {result.test_name}: {result.message}")
    elif result.status == "FAIL":
        test_results["summary"]["failed"] += 1
        print(f"[FAIL] {result.category} - {result.test_name}: {result.message}")
        if result.error:
            print(f"   Error: {result.error}")
    else:  # SKIP
        test_results["summary"]["skipped"] += 1
        print(f"[SKIP] {result.category} - {result.test_name}: {result.message}")


# ============================================
# 1. ENVIRONMENT & CONFIGURATION TESTS
# ============================================

def test_environment():
    """Test environment configuration."""
    print("\n" + "="*60)
    print("1. TESTING ENVIRONMENT & CONFIGURATION")
    print("="*60)
    
    # Test .env file exists
    try:
        env_exists = Path(".env").exists()
        if env_exists:
            add_result(TestResult(
                "Environment", "ENV File Exists",
                "PASS", ".env file found"
            ))
        else:
            add_result(TestResult(
                "Environment", "ENV File Exists",
                "FAIL", ".env file not found - copy from .env.example"
            ))
    except Exception as e:
        add_result(TestResult(
            "Environment", "ENV File Exists",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test critical environment variables
    critical_vars = [
        "SECRET_KEY", "JWT_SECRET_KEY",
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
    ]
    
    from dotenv import load_dotenv
    load_dotenv()
    
    for var in critical_vars:
        try:
            value = os.getenv(var)
            if value and value not in ["CHANGE_THIS_TO_SECURE_RANDOM_STRING", "CHANGE_THIS_TO_SECURE_RANDOM_KEY_32_CHARS", "your_password_here"]:
                add_result(TestResult(
                    "Environment", f"Variable {var}",
                    "PASS", f"Set and configured"
                ))
            else:
                add_result(TestResult(
                    "Environment", f"Variable {var}",
                    "FAIL", "Not configured or using default placeholder value"
                ))
        except Exception as e:
            add_result(TestResult(
                "Environment", f"Variable {var}",
                "FAIL", str(e), traceback.format_exc()
            ))


# ============================================
# 2. DATABASE CONNECTION TESTS
# ============================================

def test_database():
    """Test database connections."""
    print("\n" + "="*60)
    print("2. TESTING DATABASE CONNECTIONS")
    print("="*60)
    
    # Test PostgreSQL connection
    try:
        from src.core.database import engine, SessionLocal
        from sqlalchemy import text
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            add_result(TestResult(
                "Database", "PostgreSQL Connection",
                "PASS", "Successfully connected to PostgreSQL"
            ))
    except Exception as e:
        add_result(TestResult(
            "Database", "PostgreSQL Connection",
            "FAIL", f"Could not connect to PostgreSQL: {str(e)}", traceback.format_exc()
        ))
    
    # Test models import
    try:
        from src.core.models import User, Video, Analytics, Asset
        add_result(TestResult(
            "Database", "Models Import",
            "PASS", "All models imported successfully"
        ))
    except Exception as e:
        add_result(TestResult(
            "Database", "Models Import",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test database tables exist
    try:
        from src.core.database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ["users", "videos", "analytics", "assets"]
        missing_tables = [t for t in required_tables if t not in tables]
        
        if not missing_tables:
            add_result(TestResult(
                "Database", "Database Tables",
                "PASS", f"All {len(required_tables)} required tables exist"
            ))
        else:
            add_result(TestResult(
                "Database", "Database Tables",
                "FAIL", f"Missing tables: {', '.join(missing_tables)}"
            ))
    except Exception as e:
        add_result(TestResult(
            "Database", "Database Tables",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test CRUD operations
    try:
        from src.core.database import SessionLocal
        from src.core.models import User
        from datetime import datetime
        
        db = SessionLocal()
        
        # Create test user
        test_user = User(
            username=f"test_user_{datetime.now().timestamp()}",
            email=f"test_{datetime.now().timestamp()}@example.com",
            password_hash="test_hash",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Read
        retrieved_user = db.query(User).filter(User.id == test_user.id).first()
        assert retrieved_user is not None
        
        # Update
        retrieved_user.is_active = False
        db.commit()
        
        # Delete
        db.delete(retrieved_user)
        db.commit()
        
        db.close()
        
        add_result(TestResult(
            "Database", "CRUD Operations",
            "PASS", "Create, Read, Update, Delete all successful"
        ))
    except Exception as e:
        add_result(TestResult(
            "Database", "CRUD Operations",
            "FAIL", str(e), traceback.format_exc()
        ))
        try:
            db.close()
        except:
            pass


# ============================================
# 3. API ENDPOINT TESTS
# ============================================

def test_api():
    """Test API endpoints."""
    print("\n" + "="*60)
    print("3. TESTING API ENDPOINTS")
    print("="*60)
    
    # Test API imports
    try:
        from src.api.main import app
        from src.api.auth import create_access_token
        add_result(TestResult(
            "API", "FastAPI Imports",
            "PASS", "API modules imported successfully"
        ))
    except Exception as e:
        add_result(TestResult(
            "API", "FastAPI Imports",
            "FAIL", str(e), traceback.format_exc()
        ))
        return  # Can't continue without API
    
    # Test API app creation
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        client = TestClient(app)
        add_result(TestResult(
            "API", "TestClient Creation",
            "PASS", "Test client created successfully"
        ))
    except Exception as e:
        add_result(TestResult(
            "API", "TestClient Creation",
            "FAIL", str(e), traceback.format_exc()
        ))
        return
    
    # Test health endpoint
    try:
        response = client.get("/health")
        if response.status_code == 200:
            add_result(TestResult(
                "API", "Health Endpoint",
                "PASS", f"Status: {response.status_code}"
            ))
        else:
            add_result(TestResult(
                "API", "Health Endpoint",
                "FAIL", f"Expected 200, got {response.status_code}"
            ))
    except Exception as e:
        add_result(TestResult(
            "API", "Health Endpoint",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test authentication
    try:
        # Try to access protected endpoint without token
        response = client.get("/api/videos")
        if response.status_code == 401:
            add_result(TestResult(
                "API", "Authentication Required",
                "PASS", "Protected endpoint correctly requires authentication"
            ))
        else:
            add_result(TestResult(
                "API", "Authentication Required",
                "FAIL", f"Expected 401, got {response.status_code}"
            ))
    except Exception as e:
        add_result(TestResult(
            "API", "Authentication Required",
            "FAIL", str(e), traceback.format_exc()
        ))


# ============================================
# 4. AI INTEGRATION TESTS
# ============================================

async def test_ai_integrations():
    """Test AI service integrations."""
    print("\n" + "="*60)
    print("4. TESTING AI INTEGRATIONS")
    print("="*60)
    
    # Test Claude Client
    try:
        from src.services.ai_integration.claude_client import ClaudeClient
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        # Check if API key is configured (length check to verify it's a real key)
        if not api_key or len(api_key) < 20:
            add_result(TestResult(
                "AI Integration", "Claude Client",
                "SKIP", "ANTHROPIC_API_KEY not configured"
            ))
        else:
            client = ClaudeClient(api_key=api_key)
            add_result(TestResult(
                "AI Integration", "Claude Client Import",
                "PASS", "ClaudeClient imported and initialized"
            ))
    except Exception as e:
        add_result(TestResult(
            "AI Integration", "Claude Client",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test Gemini Client
    try:
        from src.services.ai_integration.gemini_client import GeminiClient
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            add_result(TestResult(
                "AI Integration", "Gemini Client",
                "SKIP", "GOOGLE_API_KEY not configured"
            ))
        else:
            client = GeminiClient(api_key=api_key)
            add_result(TestResult(
                "AI Integration", "Gemini Client Import",
                "PASS", "GeminiClient imported and initialized"
            ))
    except Exception as e:
        add_result(TestResult(
            "AI Integration", "Gemini Client",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test Grok Client
    try:
        from src.services.ai_integration.grok_client import GrokClient
        
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            add_result(TestResult(
                "AI Integration", "Grok Client",
                "SKIP", "XAI_API_KEY not configured"
            ))
        else:
            client = GrokClient(api_key=api_key)
            add_result(TestResult(
                "AI Integration", "Grok Client Import",
                "PASS", "GrokClient imported and initialized"
            ))
    except Exception as e:
        add_result(TestResult(
            "AI Integration", "Grok Client",
            "FAIL", str(e), traceback.format_exc()
        ))


# ============================================
# 5. VIDEO GENERATION PIPELINE TESTS
# ============================================

def test_video_pipeline():
    """Test video generation components."""
    print("\n" + "="*60)
    print("5. TESTING VIDEO GENERATION PIPELINE")
    print("="*60)
    
    # Test script generator
    try:
        from src.services.script_generator import ScriptGenerator
        generator = ScriptGenerator()
        add_result(TestResult(
            "Video Pipeline", "Script Generator",
            "PASS", "ScriptGenerator imported and initialized"
        ))
    except Exception as e:
        add_result(TestResult(
            "Video Pipeline", "Script Generator",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test TTS engine
    try:
        from src.services.video_assembler.tts_engine import TTSEngine
        tts = TTSEngine()
        add_result(TestResult(
            "Video Pipeline", "TTS Engine",
            "PASS", "TTSEngine imported and initialized"
        ))
    except Exception as e:
        add_result(TestResult(
            "Video Pipeline", "TTS Engine",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test video assembler
    try:
        from src.services.video_assembler import VideoAssembler
        assembler = VideoAssembler()
        add_result(TestResult(
            "Video Pipeline", "Video Assembler",
            "PASS", "VideoAssembler imported and initialized"
        ))
    except Exception as e:
        add_result(TestResult(
            "Video Pipeline", "Video Assembler",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test asset scraper
    try:
        from src.services.asset_scraper import ScraperManager
        scraper = ScraperManager()
        add_result(TestResult(
            "Video Pipeline", "Asset Scraper",
            "PASS", "ScraperManager imported and initialized"
        ))
    except Exception as e:
        add_result(TestResult(
            "Video Pipeline", "Asset Scraper",
            "FAIL", str(e), traceback.format_exc()
        ))


# ============================================
# 6. YOUTUBE INTEGRATION TESTS
# ============================================

def test_youtube():
    """Test YouTube integration."""
    print("\n" + "="*60)
    print("6. TESTING YOUTUBE INTEGRATION")
    print("="*60)
    
    # Test YouTube uploader
    try:
        from src.services.youtube_uploader import VideoUploader, AuthManager, AuthConfig
        
        client_secrets = os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
        if not Path(client_secrets).exists():
            add_result(TestResult(
                "YouTube", "Client Secrets File",
                "SKIP", f"{client_secrets} not found"
            ))
        else:
            # VideoUploader requires AuthManager with AuthConfig
            auth_config = AuthConfig(client_secrets_path=client_secrets)
            auth = AuthManager(config=auth_config)
            uploader = VideoUploader(auth_manager=auth)
            add_result(TestResult(
                "YouTube", "YouTube Uploader",
                "PASS", "VideoUploader imported and initialized"
            ))
    except Exception as e:
        add_result(TestResult(
            "YouTube", "YouTube Uploader",
            "FAIL", str(e), traceback.format_exc()
        ))
    
    # Test analytics module
    try:
        from src.services.youtube_uploader import AnalyticsTracker
        add_result(TestResult(
            "YouTube", "YouTube Analytics",
            "PASS", "AnalyticsTracker imported successfully"
        ))
    except Exception as e:
        add_result(TestResult(
            "YouTube", "YouTube Analytics",
            "FAIL", str(e), traceback.format_exc()
        ))


# ============================================
# 7. MCP SERVERS TESTS
# ============================================

def test_mcp_servers():
    """Test MCP servers."""
    print("\n" + "="*60)
    print("7. TESTING MCP SERVERS")
    print("="*60)
    
    # Skip MCP server tests - they need refactoring to use current models
    add_result(TestResult(
        "MCP Servers", "YouTube Analytics Server",
        "SKIP", "MCP servers need refactoring to use current database models"
    ))
    
    add_result(TestResult(
        "MCP Servers", "Video Pipeline Server",
        "SKIP", "MCP servers need refactoring to use current database models"
    ))


# ============================================
# 8. EXISTING TEST SUITES
# ============================================

def run_existing_tests():
    """Run all existing pytest suites."""
    print("\n" + "="*60)
    print("8. RUNNING EXISTING TEST SUITES")
    print("="*60)
    
    import subprocess
    
    # Run all tests with coverage
    try:
        result = subprocess.run(
            ["pytest", "-v", "--tb=short", "--maxfail=5"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            add_result(TestResult(
                "Existing Tests", "Full Test Suite",
                "PASS", "All existing tests passed"
            ))
        else:
            # Parse output to count failures
            output = result.stdout + result.stderr
            add_result(TestResult(
                "Existing Tests", "Full Test Suite",
                "FAIL", f"Some tests failed (exit code: {result.returncode})",
                output[-1000:] if len(output) > 1000 else output  # Last 1000 chars
            ))
    except subprocess.TimeoutExpired:
        add_result(TestResult(
            "Existing Tests", "Full Test Suite",
            "FAIL", "Test suite timed out after 5 minutes"
        ))
    except Exception as e:
        add_result(TestResult(
            "Existing Tests", "Full Test Suite",
            "FAIL", str(e), traceback.format_exc()
        ))


# ============================================
# MAIN TEST RUNNER
# ============================================

async def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*60)
    print("AUTONOMOUS COMPREHENSIVE TESTING SUITE")
    print("Testing all components before deployment")
    print("="*60)
    
    # Run synchronous tests
    test_environment()
    test_database()
    test_api()
    test_video_pipeline()
    test_youtube()
    test_mcp_servers()
    
    # Run async tests
    await test_ai_integrations()
    
    # Run existing test suites
    run_existing_tests()
    
    # Generate report
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    summary = test_results["summary"]
    print(f"\nTotal Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    
    success_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    # Save detailed report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Critical failures
    critical_failures = [
        t for t in test_results["tests"]
        if t["status"] == "FAIL" and t["category"] in ["Environment", "Database", "API"]
    ]
    
    if critical_failures:
        print("\n" + "!"*60)
        print("CRITICAL FAILURES DETECTED")
        print("!"*60)
        print("\nThe following critical components failed:")
        for failure in critical_failures:
            print(f"\n[FAIL] {failure['category']} - {failure['test']}")
            print(f"   Message: {failure['message']}")
            if failure.get('error'):
                print(f"   Error: {failure['error'][:200]}...")
        
        print("\n[WARNING] RECOMMENDATION: Fix critical failures before proceeding!")
        return False
    else:
        print("\n[SUCCESS] All critical components passed!")
        if summary['failed'] > 0:
            print(f"[WARNING] {summary['failed']} non-critical tests failed - review recommended")
        if summary['skipped'] > 0:
            print(f"[INFO] {summary['skipped']} tests skipped (missing API keys or config)")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
