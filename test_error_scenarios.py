#!/usr/bin/env python3
"""
Error Testing Script for AI Voice Agent - Day 11
This script helps test different error scenarios by temporarily disabling API keys
"""

import os
import subprocess
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color):
    print(f"{color}{message}{Colors.ENDC}")

def backup_main_py():
    """Create a backup of main.py before testing"""
    subprocess.run(["cp", "main.py", "main.py.backup"], check=True)
    print_colored("✅ Backed up main.py to main.py.backup", Colors.GREEN)

def restore_main_py():
    """Restore main.py from backup"""
    subprocess.run(["cp", "main.py.backup", "main.py"], check=True)
    print_colored("✅ Restored main.py from backup", Colors.GREEN)

def simulate_error(error_type):
    """Simulate different types of API errors"""
    
    # Read the current main.py
    with open("main.py", "r") as f:
        content = f.read()
    
    if error_type == "stt":
        # Disable AssemblyAI API key
        content = content.replace(
            'ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")',
            '# ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")  # TESTING: STT Error\nASSEMBLYAI_API_KEY = None'
        )
        print_colored("🔧 Simulating STT (AssemblyAI) Error...", Colors.YELLOW)
        
    elif error_type == "llm":
        # Disable Gemini API key
        content = content.replace(
            'GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")',
            '# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")  # TESTING: LLM Error\nGEMINI_API_KEY = None'
        )
        print_colored("🔧 Simulating LLM (Gemini) Error...", Colors.YELLOW)
        
    elif error_type == "tts":
        # Disable Murf API key
        content = content.replace(
            'MURF_API_KEY = os.getenv("MURF_API_KEY")',
            '# MURF_API_KEY = os.getenv("MURF_API_KEY")  # TESTING: TTS Error\nMURF_API_KEY = None'
        )
        print_colored("🔧 Simulating TTS (Murf) Error...", Colors.YELLOW)
        
    elif error_type == "all":
        # Disable all API keys
        content = content.replace(
            'MURF_API_KEY = os.getenv("MURF_API_KEY")',
            '# MURF_API_KEY = os.getenv("MURF_API_KEY")  # TESTING: All APIs Error\nMURF_API_KEY = None'
        )
        content = content.replace(
            'ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")',
            '# ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")  # TESTING: All APIs Error\nASSEMBLYAI_API_KEY = None'
        )
        content = content.replace(
            'GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")',
            '# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")  # TESTING: All APIs Error\nGEMINI_API_KEY = None'
        )
        print_colored("🔧 Simulating ALL API Errors (Complete Outage)...", Colors.RED)
        
    elif error_type == "timeout":
        # Simulate timeout errors by reducing timeout values
        content = content.replace(
            'timeout=30',
            'timeout=1  # TESTING: Timeout Error'
        )
        content = content.replace(
            'timeout=10',
            'timeout=1  # TESTING: Timeout Error'
        )
        content = content.replace(
            'timeout=8',
            'timeout=1  # TESTING: Timeout Error'
        )
        print_colored("🔧 Simulating TIMEOUT Errors (1s timeout)...", Colors.YELLOW)
        
    elif error_type == "network":
        # Simulate network errors by using invalid URLs
        content = content.replace(
            '"https://api.murf.ai/v1/speech/generate"',
            '"https://invalid-murf-api.example.com/v1/speech/generate"  # TESTING: Network Error'
        )
        print_colored("🔧 Simulating NETWORK Errors (invalid URLs)...", Colors.YELLOW)
        
    elif error_type == "mixed":
        # Simulate mixed service degradation
        content = content.replace(
            'ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")',
            '# ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")  # TESTING: Mixed Errors\nASSEMBLYAI_API_KEY = None'
        )
        content = content.replace(
            'timeout=30',
            'timeout=2  # TESTING: Mixed Errors'
        )
        print_colored("🔧 Simulating MIXED Service Degradation (STT + Timeout)...", Colors.YELLOW)
    
    # Write the modified content
    with open("main.py", "w") as f:
        f.write(content)
    
    print_colored(f"✅ Error simulation for {error_type.upper()} activated!", Colors.GREEN)
    print_test_scenarios(error_type)

def print_test_scenarios(error_type):
    """Print specific test scenarios for each error type"""
    print_colored("\n📋 TEST SCENARIOS TO TRY:", Colors.BLUE)
    
    if error_type == "stt":
        scenarios = [
            "1. 🎤 Record audio in the AI Voice Assistant",
            "2. 🗣️ Try different speech lengths (short vs long)",
            "3. 🔊 Test with background noise or unclear speech",
            "4. 📱 Verify fallback message is spoken if TTS works"
        ]
    elif error_type == "llm":
        scenarios = [
            "1. 🤖 Try AI chat with voice recording",
            "2. 📝 Test with text-only LLM queries",
            "3. 💬 Send multiple messages to test consistency",
            "4. 🔄 Verify fallback responses make sense"
        ]
    elif error_type == "tts":
        scenarios = [
            "1. 🔊 Try Text-to-Speech generation",
            "2. 🎯 Test AI chat (should show text-only responses)",
            "3. 📱 Test different text lengths",
            "4. 🎤 Verify STT still works but no audio output"
        ]
    elif error_type == "timeout":
        scenarios = [
            "1. ⏱️ Try all features - they should timeout quickly",
            "2. 🔄 Verify retry mechanisms work",
            "3. 📊 Test client-side timeout handling",
            "4. 🚨 Check user-friendly timeout messages"
        ]
    elif error_type == "network":
        scenarios = [
            "1. 🌐 Test TTS generation (should fail with network error)",
            "2. 🔗 Verify fallback text is displayed",
            "3. 🔄 Test client-side retry logic",
            "4. 📱 Check error message clarity"
        ]
    elif error_type == "all":
        scenarios = [
            "1. 🚨 Try all features - complete system failure",
            "2. 🛡️ Verify graceful degradation everywhere",
            "3. 📝 Test fallback text responses",
            "4. 🔄 Check if any retry mechanisms work",
            "5. 💔 Verify the app doesn't crash completely"
        ]
    elif error_type == "mixed":
        scenarios = [
            "1. 🎯 Test partial service degradation",
            "2. 🔄 Some features work, others don't",
            "3. 📊 Verify intelligent fallbacks",
            "4. 🎤 Test combination of working/failing services"
        ]
    else:
        scenarios = ["Test the specific error type manually"]
    
    for scenario in scenarios:
        print(f"   {scenario}")
    
    print_colored("\n📸 DOCUMENTATION TIPS:", Colors.BLUE)
    doc_tips = [
        "• Take screenshots of error messages",
        "• Record video of fallback behavior",
        "• Note which features still work vs fail",
        "• Test both desktop and mobile if possible",
        "• Document the user experience during failures"
    ]
    
    for tip in doc_tips:
        print(f"   {tip}")
    
    print_colored(f"\n🔄 Run 'python test_error_scenarios.py restore' to restore when done", Colors.BLUE)

def main():
    if len(sys.argv) < 2:
        print_colored("🧪 AI Voice Agent - Enhanced Error Testing Script", Colors.BOLD)
        print_colored("Day 11: Comprehensive Error Handling & Fallback Testing", Colors.BLUE)
        print_colored("\nUsage:", Colors.BLUE)
        print("  python test_error_scenarios.py backup     # Create backup")
        print("  python test_error_scenarios.py stt        # Test STT errors")
        print("  python test_error_scenarios.py llm        # Test LLM errors") 
        print("  python test_error_scenarios.py tts        # Test TTS errors")
        print("  python test_error_scenarios.py timeout    # Test timeout errors")
        print("  python test_error_scenarios.py network    # Test network errors")
        print("  python test_error_scenarios.py mixed      # Test mixed service degradation")
        print("  python test_error_scenarios.py all        # Test complete system failure")
        print("  python test_error_scenarios.py restore    # Restore original")
        
        print_colored("\n🎯 ERROR TYPES EXPLAINED:", Colors.YELLOW)
        explanations = [
            "STT:     Speech-to-Text (AssemblyAI) failures",
            "LLM:     AI Language Model (Gemini) failures", 
            "TTS:     Text-to-Speech (Murf) failures",
            "TIMEOUT: Service timeout scenarios",
            "NETWORK: Network connectivity issues",
            "MIXED:   Partial service degradation",
            "ALL:     Complete system outage simulation"
        ]
        for explanation in explanations:
            print(f"  {explanation}")
        
        print_colored("\n💡 TESTING WORKFLOW:", Colors.GREEN)
        workflow = [
            "1. Run 'backup' to save current state",
            "2. Run specific error type (e.g., 'stt')",
            "3. Test the application thoroughly",
            "4. Document behaviors and take screenshots",
            "5. Run 'restore' to return to normal",
            "6. Repeat for other error types"
        ]
        for step in workflow:
            print(f"  {step}")
        return
    
    command = sys.argv[1].lower()
    
    if command == "backup":
        backup_main_py()
    elif command == "restore":
        if Path("main.py.backup").exists():
            restore_main_py()
        else:
            print_colored("❌ No backup found! Please run 'backup' first.", Colors.RED)
    elif command in ["stt", "llm", "tts", "timeout", "network", "mixed", "all"]:
        if not Path("main.py.backup").exists():
            print_colored("📋 Creating backup first...", Colors.YELLOW)
            backup_main_py()
        simulate_error(command)
    else:
        print_colored(f"❌ Unknown command: {command}", Colors.RED)

if __name__ == "__main__":
    main()
