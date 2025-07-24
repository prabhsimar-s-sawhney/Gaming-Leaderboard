#!/usr/bin/env python3
"""
Smoke tests for Gaming Leaderboard application
"""

import requests
import time
import sys
import json


class SmokeTests:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.frontend_url = "http://localhost:3000"
        
    def test_backend_health(self):
        """Test if backend is responding."""
        try:
            response = requests.get(f"{self.api_url}/games/", timeout=10)
            assert response.status_code == 200
            print("✅ Backend health check passed")
            return True
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False
    
    def test_frontend_health(self):
        """Test if frontend is responding."""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            assert response.status_code == 200
            print("✅ Frontend health check passed")
            return True
        except Exception as e:
            print(f"❌ Frontend health check failed: {e}")
            return False
    
    def test_score_submission(self):
        """Test score submission endpoint."""
        try:
            data = {
                "game_id": 1,
                "score": 1000,
                "user_id": 1
            }
            response = requests.post(
                f"{self.api_url}/submit-score/",
                json=data,
                timeout=10
            )
            assert response.status_code == 201
            print("✅ Score submission test passed")
            return True
        except Exception as e:
            print(f"❌ Score submission test failed: {e}")
            return False
    
    def test_leaderboard_retrieval(self):
        """Test leaderboard retrieval."""
        try:
            response = requests.get(
                f"{self.api_url}/leaderboard/1/top10/",
                timeout=10
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            print("✅ Leaderboard retrieval test passed")
            return True
        except Exception as e:
            print(f"❌ Leaderboard retrieval test failed: {e}")
            return False
    
    def test_player_rank(self):
        """Test player rank endpoint."""
        try:
            response = requests.get(
                f"{self.api_url}/leaderboard/1/player/1/",
                timeout=10
            )
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            print("✅ Player rank test passed")
            return True
        except Exception as e:
            print(f"❌ Player rank test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all smoke tests."""
        print("🚀 Running Gaming Leaderboard smoke tests...")
        
        tests = [
            self.test_backend_health,
            self.test_frontend_health,
            self.test_score_submission,
            self.test_leaderboard_retrieval,
            self.test_player_rank
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        
        print(f"\n📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All smoke tests passed!")
            return True
        else:
            print("💥 Some smoke tests failed!")
            return False


def main():
    """Main function to run smoke tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Gaming Leaderboard smoke tests')
    parser.add_argument('--backend-url', default='http://localhost:8000',
                       help='Backend URL (default: http://localhost:8000)')
    parser.add_argument('--frontend-url', default='http://localhost:3000',
                       help='Frontend URL (default: http://localhost:3000)')
    
    args = parser.parse_args()
    
    smoke_tests = SmokeTests(args.backend_url)
    smoke_tests.frontend_url = args.frontend_url
    
    success = smoke_tests.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
