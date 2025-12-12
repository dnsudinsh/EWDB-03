#!/usr/bin/env python3
"""
AEGIS MIND Backend API Testing Suite
Tests all backend endpoints for the Electronic Warfare Decision Support System
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

class AegisMindTester:
    def __init__(self, base_url="https://ew-dashboard.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                 data: Dict = None, headers: Dict = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            try:
                response_json = response.json()
            except:
                response_json = {"raw_response": response.text}

            details = f"Status: {response.status_code}"
            if not success:
                details += f" (expected {expected_status})"
                if response.text:
                    details += f" - Response: {response.text[:200]}"

            self.log_test(name, success, details, response_json)
            return success, response_json

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - backend may be down")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test system health endpoint"""
        success, response = self.run_test("Health Check", "GET", "health")
        if success and response:
            expected_fields = ["status", "system", "version", "timestamp"]
            missing_fields = [f for f in expected_fields if f not in response]
            if missing_fields:
                self.log_test("Health Check - Response Format", False, 
                            f"Missing fields: {missing_fields}")
            else:
                self.log_test("Health Check - Response Format", True, 
                            f"System: {response.get('system')}, Status: {response.get('status')}")
        return success

    def test_emitters_endpoint(self):
        """Test emitters endpoint"""
        success, response = self.run_test("Get Emitters", "GET", "emitters")
        if success and isinstance(response, list):
            emitter_count = len(response)
            self.log_test("Emitters - Data Format", True, f"Found {emitter_count} emitters")
            
            if emitter_count > 0:
                # Check first emitter structure
                emitter = response[0]
                required_fields = ["name", "emitter_type", "platform", "origin", 
                                 "threat_level", "latitude", "longitude", "affiliation"]
                missing_fields = [f for f in required_fields if f not in emitter]
                if missing_fields:
                    self.log_test("Emitters - Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Emitters - Structure", True, 
                                f"Sample: {emitter.get('name')} ({emitter.get('affiliation')})")
        elif success:
            self.log_test("Emitters - Data Format", False, "Response is not a list")
        
        return success

    def test_scenarios_endpoint(self):
        """Test scenarios endpoint"""
        success, response = self.run_test("Get Scenarios", "GET", "scenarios")
        if success and isinstance(response, list):
            scenario_count = len(response)
            self.log_test("Scenarios - Data Format", True, f"Found {scenario_count} scenarios")
            
            if scenario_count > 0:
                scenario = response[0]
                required_fields = ["id", "name", "description", "region", "center_lat", "center_lng"]
                missing_fields = [f for f in required_fields if f not in scenario]
                if missing_fields:
                    self.log_test("Scenarios - Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Scenarios - Structure", True, 
                                f"Sample: {scenario.get('name')} in {scenario.get('region')}")
        elif success:
            self.log_test("Scenarios - Data Format", False, "Response is not a list")
        
        return success

    def test_threats_assessment(self):
        """Test threat assessment endpoint"""
        success, response = self.run_test("Threat Assessment", "GET", "threats/assess")
        if success and isinstance(response, dict):
            required_fields = ["total_threats", "critical_count", "assessments", "timestamp"]
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                self.log_test("Threats - Structure", False, f"Missing fields: {missing_fields}")
            else:
                total = response.get('total_threats', 0)
                critical = response.get('critical_count', 0)
                self.log_test("Threats - Structure", True, 
                            f"Total: {total}, Critical: {critical}")
        elif success:
            self.log_test("Threats - Data Format", False, "Response is not a dict")
        
        return success

    def test_countermeasures_endpoint(self):
        """Test countermeasures endpoint"""
        success, response = self.run_test("Get Countermeasures", "GET", "countermeasures")
        if success and isinstance(response, list):
            cm_count = len(response)
            self.log_test("Countermeasures - Data Format", True, f"Found {cm_count} countermeasures")
            
            if cm_count > 0:
                cm = response[0]
                required_fields = ["name", "technique_type", "description", "success_rate"]
                missing_fields = [f for f in required_fields if f not in cm]
                if missing_fields:
                    self.log_test("Countermeasures - Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Countermeasures - Structure", True, 
                                f"Sample: {cm.get('name')} ({cm.get('technique_type')})")
        elif success:
            self.log_test("Countermeasures - Data Format", False, "Response is not a list")
        
        return success

    def test_metrics_endpoint(self):
        """Test system metrics endpoint"""
        success, response = self.run_test("System Metrics", "GET", "metrics")
        if success and isinstance(response, dict):
            required_fields = ["emitters_tracked", "hostile_count", "friendly_count", 
                             "classification_accuracy", "timestamp"]
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                self.log_test("Metrics - Structure", False, f"Missing fields: {missing_fields}")
            else:
                tracked = response.get('emitters_tracked', 0)
                hostile = response.get('hostile_count', 0)
                accuracy = response.get('classification_accuracy', 0)
                self.log_test("Metrics - Structure", True, 
                            f"Tracked: {tracked}, Hostile: {hostile}, Accuracy: {accuracy:.1%}")
        elif success:
            self.log_test("Metrics - Data Format", False, "Response is not a dict")
        
        return success

    def test_ai_chat_endpoint(self):
        """Test AI chat endpoint with Malaysian context"""
        test_message = {
            "message": "Situasi ancaman?",
            "session_id": "test"
        }
        
        success, response = self.run_test("AI Chat - Malaysian Query", "POST", "ai/chat", 200, test_message)
        if success and isinstance(response, dict):
            required_fields = ["response", "context"]
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                self.log_test("AI Chat - Structure", False, f"Missing fields: {missing_fields}")
            else:
                ai_response = response.get('response', '')
                context = response.get('context', {})
                self.log_test("AI Chat - Structure", True, 
                            f"Response length: {len(ai_response)} chars, Context keys: {list(context.keys())}")
                
                # Check if response contains relevant Malaysian military context
                if any(term in ai_response.lower() for term in ['malaysia', 'maf', 'tldm', 'tudm', 'halimun']):
                    self.log_test("AI Chat - Malaysian Context", True, "Response contains Malaysian military context")
                else:
                    self.log_test("AI Chat - Malaysian Context", False, "Response lacks Malaysian military context")
        elif success:
            self.log_test("AI Chat - Data Format", False, "Response is not a dict")
        
        return success

    def test_ai_analysis_endpoint(self):
        """Test AI analysis endpoint for specific emitters"""
        # Test with URL encoded emitter name
        emitter_name = "KD%20Lekiu%20-%20TLDM%20Frigate"
        success, response = self.run_test("AI Analysis - KD Lekiu", "GET", f"ai/analyze/{emitter_name}")
        
        if success and isinstance(response, dict):
            required_fields = ["emitter_id", "emitter_name", "analysis", "timestamp"]
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                self.log_test("AI Analysis - Structure", False, f"Missing fields: {missing_fields}")
            else:
                analysis = response.get('analysis', '')
                emitter_name_resp = response.get('emitter_name', '')
                self.log_test("AI Analysis - Structure", True, 
                            f"Analyzed: {emitter_name_resp}, Analysis length: {len(analysis)} chars")
                
                # Check if analysis contains tactical assessment
                if any(term in analysis.lower() for term in ['threat', 'countermeasure', 'tactical', 'assessment']):
                    self.log_test("AI Analysis - Tactical Content", True, "Analysis contains tactical assessment")
                else:
                    self.log_test("AI Analysis - Tactical Content", False, "Analysis lacks tactical assessment")
        elif success:
            self.log_test("AI Analysis - Data Format", False, "Response is not a dict")
        
        return success

    def test_specific_scenarios(self):
        """Test specific PROJEK HALIMUN scenarios"""
        scenarios_to_test = [
            ("scenario_1", "SELAT MELAKA GUARDIAN"),
            ("scenario_2", "RAJAWALI SHIELD"), 
            ("scenario_3", "NUSANTARA SPECTRUM")
        ]
        
        all_success = True
        
        for scenario_id, expected_name in scenarios_to_test:
            success, response = self.run_test(f"Get Scenario - {expected_name}", "GET", f"scenarios/{scenario_id}")
            if success and isinstance(response, dict):
                actual_name = response.get('name', '')
                if expected_name in actual_name:
                    self.log_test(f"Scenario {scenario_id} - Name Match", True, f"Found: {actual_name}")
                else:
                    self.log_test(f"Scenario {scenario_id} - Name Match", False, f"Expected: {expected_name}, Got: {actual_name}")
                    all_success = False
                
                # Check for emitters
                emitter_data = response.get('emitter_data', [])
                if emitter_data and len(emitter_data) > 0:
                    self.log_test(f"Scenario {scenario_id} - Emitters", True, f"Found {len(emitter_data)} emitters")
                else:
                    self.log_test(f"Scenario {scenario_id} - Emitters", False, "No emitters found")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_scenario_activation(self):
        """Test scenario activation for scenario_1"""
        success, response = self.run_test("Activate Scenario 1", "POST", "scenarios/scenario_1/activate")
        
        if success and isinstance(response, dict):
            required_fields = ["scenario_id", "status", "emitters_loaded", "timestamp"]
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                self.log_test("Scenario Activation - Structure", False, f"Missing fields: {missing_fields}")
            else:
                loaded = response.get('emitters_loaded', 0)
                status = response.get('status', '')
                scenario_id = response.get('scenario_id', '')
                
                if status == "activated" and loaded > 0:
                    self.log_test("Scenario Activation - Success", True, 
                                f"Scenario {scenario_id}: {status}, Emitters loaded: {loaded}")
                else:
                    self.log_test("Scenario Activation - Success", False, 
                                f"Status: {status}, Emitters: {loaded}")
        elif success:
            self.log_test("Scenario Activation - Data Format", False, "Response is not a dict")
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting AEGIS MIND Backend API Tests")
        print(f"📡 Testing endpoint: {self.base_url}")
        print("=" * 60)

        # Core API tests
        self.test_health_check()
        self.test_emitters_endpoint()
        self.test_scenarios_endpoint()
        self.test_threats_assessment()
        self.test_countermeasures_endpoint()
        self.test_metrics_endpoint()
        
        # AI and advanced features
        self.test_ai_chat_endpoint()
        self.test_scenario_activation()

        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! AEGIS MIND backend is operational.")
        else:
            failed_tests = [t for t in self.test_results if not t['success']]
            print(f"⚠️  {len(failed_tests)} tests failed:")
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test['details']}")

        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = AegisMindTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
            'test_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())