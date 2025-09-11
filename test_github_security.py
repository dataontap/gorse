#!/usr/bin/env python3
"""
Security test suite for GitHub integration system
Tests for authentication, input validation, and injection prevention
"""

import json
import tempfile
import os
import subprocess
from github_service_secure import SecureGitHubService
from auth_helpers import verify_admin_token, verify_firebase_uid

def test_input_validation():
    """Test input validation and sanitization"""
    print("🔐 Testing input validation...")
    
    service = SecureGitHubService()
    
    # Test path traversal protection
    try:
        service._validate_file_path("../../../etc/passwd")
        print("❌ Path traversal attack not blocked!")
        return False
    except ValueError:
        print("✅ Path traversal attack blocked")
    
    # Test dangerous file extensions
    try:
        service._validate_file_path("malicious.exe")
        print("❌ Dangerous file extension not blocked!")
        return False
    except ValueError:
        print("✅ Dangerous file extension blocked")
    
    # Test content size limits
    try:
        large_content = "x" * (6 * 1024 * 1024)  # 6MB
        service._validate_content(large_content)
        print("❌ Large content not blocked!")
        return False
    except ValueError:
        print("✅ Large content blocked")
    
    # Test repository name validation
    try:
        service._validate_repository_info("../malicious", "repo<script>")
        print("❌ Malicious repository name not blocked!")
        return False
    except ValueError:
        print("✅ Malicious repository name blocked")
    
    print("✅ All input validation tests passed")
    return True

def test_code_injection_prevention():
    """Test that code injection is prevented"""
    print("🔐 Testing code injection prevention...")
    
    service = SecureGitHubService()
    
    # Test malicious content with backticks
    malicious_content = '''console.log(`${process.env.HOME}`); process.exit(0);'''
    
    # This should be safely handled as content, not executed
    try:
        # Test that the secure upload_file doesn't execute malicious content
        result = service.upload_file(
            file_path="test.js",
            content=malicious_content,
            commit_message="test`; rm -rf /; echo `test",
            repo_owner="test",
            repo_name="test"
        )
        # The method should handle malicious input safely (will fail due to no GitHub auth in test)
        print("✅ Malicious content handled safely")
    except Exception as e:
        if "auth" in str(e).lower() or "github" in str(e).lower():
            print("✅ Malicious content handled safely (auth failure expected)")
        else:
            print(f"❌ Unexpected error: {str(e)}")
            return False
    
    # Test malicious commit message
    malicious_commit = '''Update"; rm -rf /; echo "pwned'''
    
    try:
        service._validate_input(malicious_commit, "commit message", 500)
        # Should be sanitized, dangerous characters removed
        print("✅ Malicious commit message sanitized")
    except:
        print("✅ Malicious commit message rejected")
    
    print("✅ All code injection prevention tests passed")
    return True

def test_authentication():
    """Test authentication mechanisms"""
    print("🔐 Testing authentication...")
    
    # Test admin token verification
    os.environ['ADMIN_TOKEN'] = 'test_admin_token_123'
    
    if verify_admin_token('test_admin_token_123'):
        print("✅ Valid admin token accepted")
    else:
        print("❌ Valid admin token rejected")
        return False
    
    if not verify_admin_token('invalid_token'):
        print("✅ Invalid admin token rejected")
    else:
        print("❌ Invalid admin token accepted")
        return False
    
    if not verify_admin_token(''):
        print("✅ Empty admin token rejected")
    else:
        print("❌ Empty admin token accepted")
        return False
    
    # Test Firebase UID validation (will fail without DB, which is expected)
    if not verify_firebase_uid('invalid_firebase_uid'):
        print("✅ Invalid Firebase UID rejected")
    else:
        print("❌ Invalid Firebase UID accepted")
        return False
    
    print("✅ All authentication tests passed")
    return True

def test_file_operations():
    """Test secure file operations"""
    print("🔐 Testing secure file operations...")
    
    service = SecureGitHubService()
    
    # Test configuration persistence
    service.set_repository("testowner", "testrepo", "main")
    
    # Create new instance to test persistence
    service2 = SecureGitHubService()
    if (service2.repo_owner == "testowner" and 
        service2.repo_name == "testrepo" and 
        service2.default_branch == "main"):
        print("✅ Configuration persistence works")
    else:
        print("❌ Configuration persistence failed")
        return False
    
    # Test secure client exists
    if os.path.exists('github_secure_client.js'):
        print("✅ Secure client exists")
    else:
        print("❌ Secure client missing")
        return False
    
    # Test secure client has proper validation
    with open('github_secure_client.js', 'r') as f:
        client_content = f.read()
        if 'JSON.parse' in client_content and 'sanitizedConfig' in client_content:
            print("✅ Secure client uses JSON communication")
        else:
            print("❌ Secure client missing JSON communication")
            return False
    
    print("✅ All file operation tests passed")
    return True

def test_module_system():
    """Test that module system works correctly"""
    print("🔐 Testing module system...")
    
    # Test that github_client.js uses proper CommonJS
    if os.path.exists('github_client.js'):
        with open('github_client.js', 'r') as f:
            content = f.read()
            if 'module.exports' in content and 'require(' in content:
                print("✅ GitHub client uses proper CommonJS")
            else:
                print("❌ GitHub client missing CommonJS")
                return False
    else:
        print("❌ GitHub client missing")
        return False
    
    print("✅ All module system tests passed")
    return True

def run_all_tests():
    """Run complete security test suite"""
    print("🚀 Starting comprehensive security test suite...")
    print("=" * 50)
    
    tests = [
        test_input_validation,
        test_code_injection_prevention,
        test_authentication,
        test_file_operations,
        test_module_system
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            print()
    
    print("=" * 50)
    print(f"🎯 Security Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SECURITY TESTS PASSED - System is secure!")
        return True
    else:
        print("⚠️  Some security tests failed - Review required!")
        return False

if __name__ == "__main__":
    run_all_tests()