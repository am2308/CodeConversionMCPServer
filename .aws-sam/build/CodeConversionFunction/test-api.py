#!/usr/bin/env python3
"""
Test script for MCP Multi-Language to Python Converter API
"""
import requests
import json
import time
import sys

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_supported_languages():
    """Test supported languages endpoint"""
    print("\n🔍 Testing supported languages endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/supported-languages")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total languages: {data['total_languages']}")
        print(f"Total extensions: {data['total_extensions']}")
        print("Supported languages:")
        for lang, extensions in data['supported_languages'].items():
            print(f"  {lang}: {', '.join(extensions)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Supported languages test failed: {e}")
        return False

def test_conversion(repo_owner, repo_name, branch="main", source_languages=None):
    """Test conversion endpoint"""
    print(f"\n🔍 Testing conversion for {repo_owner}/{repo_name}...")
    
    payload = {
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "branch": branch
    }
    
    if source_languages:
        payload["source_languages"] = source_languages
    
    try:
        response = requests.post(
            f"{BASE_URL}/convert",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            task_id = response.json().get("task_id")
            print(f"✅ Conversion started with task ID: {task_id}")
            return task_id
        else:
            print(f"❌ Conversion failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Conversion test failed: {e}")
        return None

def test_status(task_id):
    """Test status endpoint"""
    print(f"\n🔍 Testing status for task {task_id}...")
    try:
        response = requests.get(f"{BASE_URL}/status/{task_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Status test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting MCP Converter API Tests")
    print("=" * 50)
    
    # Test basic endpoints
    if not test_health():
        print("❌ Health check failed. Make sure the service is running.")
        sys.exit(1)
    
    if not test_supported_languages():
        print("❌ Supported languages test failed.")
        sys.exit(1)
    
    # Get repository details from user
    print("\n" + "=" * 50)
    print("📝 Repository Conversion Test")
    print("Enter repository details to test conversion:")
    
    repo_owner = input("Repository owner (e.g., 'octocat'): ").strip()
    repo_name = input("Repository name (e.g., 'Hello-World'): ").strip()
    branch = input("Branch (default: main): ").strip() or "main"
    
    print("\nOptional: Specify source languages to convert (comma-separated)")
    print("Available: shell, javascript, typescript, go, rust, python, java, etc.")
    source_langs_input = input("Source languages (leave empty for all): ").strip()
    
    source_languages = None
    if source_langs_input:
        source_languages = [lang.strip() for lang in source_langs_input.split(",")]
    
    if not repo_owner or not repo_name:
        print("❌ Repository owner and name are required.")
        sys.exit(1)
    
    # Test conversion
    task_id = test_conversion(repo_owner, repo_name, branch, source_languages)
    
    if task_id:
        # Test status endpoint
        time.sleep(2)  # Wait a bit before checking status
        test_status(task_id)
        
        print("\n✅ All tests completed!")
        print(f"🔗 Check your GitHub repository for the pull request: https://github.com/{repo_owner}/{repo_name}/pulls")
    else:
        print("❌ Conversion test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()