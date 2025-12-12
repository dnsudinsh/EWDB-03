#!/usr/bin/env python3
"""
Malaysian Armed Forces (MAF) Context Verification Test
Tests specific Malaysian context features in AEGIS MIND system
"""

import requests
import json
import sys
from datetime import datetime

class MalaysianContextTester:
    def __init__(self, base_url="https://radar-guardian-2.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def test_malaysian_scenarios(self):
        """Test that scenarios contain Malaysian context"""
        try:
            response = requests.get(f"{self.base_url}/scenarios", timeout=30)
            if response.status_code != 200:
                self.log_test("Malaysian Scenarios - API Call", False, f"Status: {response.status_code}")
                return False
            
            scenarios = response.json()
            
            # Check for 3 Malaysian scenarios
            if len(scenarios) != 3:
                self.log_test("Malaysian Scenarios - Count", False, f"Expected 3 scenarios, got {len(scenarios)}")
                return False
            
            self.log_test("Malaysian Scenarios - Count", True, "Found 3 scenarios")
            
            # Check for specific Malaysian scenario names
            expected_scenarios = [
                "Selat Melaka Guardian",
                "Rajawali Shield", 
                "Nusantara Spectrum"
            ]
            
            expected_bahasa_names = [
                "Penjaga Selat Melaka",
                "Perisai Rajawali",
                "Spektrum Nusantara"
            ]
            
            scenario_names = [s.get('name', '') for s in scenarios]
            bahasa_names = [s.get('name_bm', '') for s in scenarios]
            
            # Check English names
            missing_scenarios = [name for name in expected_scenarios if name not in scenario_names]
            if missing_scenarios:
                self.log_test("Malaysian Scenarios - English Names", False, f"Missing: {missing_scenarios}")
            else:
                self.log_test("Malaysian Scenarios - English Names", True, "All Malaysian scenarios present")
            
            # Check Bahasa Malaysia names
            missing_bahasa = [name for name in expected_bahasa_names if name not in bahasa_names]
            if missing_bahasa:
                self.log_test("Malaysian Scenarios - Bahasa Names", False, f"Missing Bahasa names: {missing_bahasa}")
            else:
                self.log_test("Malaysian Scenarios - Bahasa Names", True, "All Bahasa Malaysia names present")
            
            # Check Malaysian regions
            regions = [s.get('region', '') for s in scenarios]
            malaysian_regions = ['Selat Melaka', 'ESSZONE', 'Laut China Selatan']
            
            region_check = all(any(mr in region for mr in malaysian_regions) for region in regions)
            if region_check:
                self.log_test("Malaysian Scenarios - Regions", True, f"Regions: {regions}")
            else:
                self.log_test("Malaysian Scenarios - Regions", False, f"Non-Malaysian regions found: {regions}")
            
            return True
            
        except Exception as e:
            self.log_test("Malaysian Scenarios - API Call", False, f"Error: {str(e)}")
            return False

    def test_malaysian_emitters(self):
        """Test that emitters contain Malaysian assets and threats"""
        try:
            response = requests.get(f"{self.base_url}/emitters", timeout=30)
            if response.status_code != 200:
                self.log_test("Malaysian Emitters - API Call", False, f"Status: {response.status_code}")
                return False
            
            emitters = response.json()
            
            # Check for Malaysian friendly assets
            malaysian_assets = [
                "KD Lekiu - TLDM Frigate",
                "KD Keris - LCS Patrol", 
                "F/A-18D Hornet - TUDM",
                "ESSCOM Command Post",
                "Lumut EW Station",
                "Kasawari Gas Platform"
            ]
            
            emitter_names = [e.get('name', '') for e in emitters]
            found_assets = [asset for asset in malaysian_assets if asset in emitter_names]
            
            if len(found_assets) >= 4:  # At least 4 Malaysian assets
                self.log_test("Malaysian Emitters - MAF Assets", True, f"Found {len(found_assets)} Malaysian assets: {found_assets}")
            else:
                self.log_test("Malaysian Emitters - MAF Assets", False, f"Only found {len(found_assets)} Malaysian assets: {found_assets}")
            
            # Check for Malaysian threats
            malaysian_threats = [
                "CCG 5901 - Coast Guard Cutter",
                "Abu Sayyaf Comms - Baofeng Radio",
                "Maritime Militia Flotilla"
            ]
            
            found_threats = [threat for threat in malaysian_threats if threat in emitter_names]
            
            if len(found_threats) >= 2:  # At least 2 Malaysian-specific threats
                self.log_test("Malaysian Emitters - Regional Threats", True, f"Found {len(found_threats)} regional threats: {found_threats}")
            else:
                self.log_test("Malaysian Emitters - Regional Threats", False, f"Only found {len(found_threats)} regional threats: {found_threats}")
            
            # Check for Malaysian origins
            malaysian_emitters = [e for e in emitters if e.get('origin') == 'Malaysia']
            if len(malaysian_emitters) >= 5:
                self.log_test("Malaysian Emitters - Origin Malaysia", True, f"Found {len(malaysian_emitters)} Malaysian-origin emitters")
            else:
                self.log_test("Malaysian Emitters - Origin Malaysia", False, f"Only found {len(malaysian_emitters)} Malaysian-origin emitters")
            
            return True
            
        except Exception as e:
            self.log_test("Malaysian Emitters - API Call", False, f"Error: {str(e)}")
            return False

    def test_malaysian_countermeasures(self):
        """Test that countermeasures include Malaysian-specific options"""
        try:
            response = requests.get(f"{self.base_url}/countermeasures", timeout=30)
            if response.status_code != 200:
                self.log_test("Malaysian Countermeasures - API Call", False, f"Status: {response.status_code}")
                return False
            
            countermeasures = response.json()
            
            # Check for Malaysian-specific countermeasures
            malaysian_cms = [
                "Dagaie NG Decoy System",
                "AI Spectrum Manager", 
                "Portable EW Jammer - Handheld",
                "GPS Spoofing Defense"
            ]
            
            cm_names = [cm.get('name', '') for cm in countermeasures]
            found_cms = [cm for cm in malaysian_cms if cm in cm_names]
            
            if len(found_cms) >= 3:
                self.log_test("Malaysian Countermeasures - MAF Specific", True, f"Found {len(found_cms)} Malaysian countermeasures: {found_cms}")
            else:
                self.log_test("Malaysian Countermeasures - MAF Specific", False, f"Only found {len(found_cms)} Malaysian countermeasures: {found_cms}")
            
            return True
            
        except Exception as e:
            self.log_test("Malaysian Countermeasures - API Call", False, f"Error: {str(e)}")
            return False

    def test_ai_malaysian_context(self):
        """Test that AI responses include MAF-specific context"""
        try:
            test_message = {
                "message": "What are the current threats to Malaysian territorial waters?",
                "session_id": "maf_test"
            }
            
            response = requests.post(f"{self.base_url}/ai/chat", json=test_message, timeout=30)
            if response.status_code != 200:
                self.log_test("AI Malaysian Context - API Call", False, f"Status: {response.status_code}")
                return False
            
            ai_response = response.json()
            ai_text = ai_response.get('response', '').lower()
            
            # Check for Malaysian military references
            maf_terms = ['atm', 'tldm', 'tudm', 'tdm', 'malaysia', 'malaysian', 'maf', 'esscom', 'petronas']
            found_terms = [term for term in maf_terms if term in ai_text]
            
            if len(found_terms) >= 3:
                self.log_test("AI Malaysian Context - MAF References", True, f"Found MAF terms: {found_terms}")
            else:
                self.log_test("AI Malaysian Context - MAF References", False, f"Limited MAF context, found: {found_terms}")
            
            # Check response length (should be substantial)
            if len(ai_text) > 200:
                self.log_test("AI Malaysian Context - Response Quality", True, f"Substantial response: {len(ai_text)} characters")
            else:
                self.log_test("AI Malaysian Context - Response Quality", False, f"Short response: {len(ai_text)} characters")
            
            return True
            
        except Exception as e:
            self.log_test("AI Malaysian Context - API Call", False, f"Error: {str(e)}")
            return False

    def test_map_coordinates(self):
        """Test that scenarios are centered on Malaysian regions"""
        try:
            response = requests.get(f"{self.base_url}/scenarios", timeout=30)
            if response.status_code != 200:
                return False
            
            scenarios = response.json()
            
            # Malaysian coordinate ranges (approximate)
            # Malaysia spans roughly 1°N to 7°N, 99°E to 119°E
            malaysia_lat_range = (1.0, 7.0)
            malaysia_lng_range = (99.0, 119.0)
            
            malaysian_centered = 0
            for scenario in scenarios:
                lat = scenario.get('center_lat', 0)
                lng = scenario.get('center_lng', 0)
                
                if (malaysia_lat_range[0] <= lat <= malaysia_lat_range[1] and 
                    malaysia_lng_range[0] <= lng <= malaysia_lng_range[1]):
                    malaysian_centered += 1
            
            if malaysian_centered == len(scenarios):
                self.log_test("Map Coordinates - Malaysian Centered", True, f"All {malaysian_centered} scenarios centered on Malaysia")
            else:
                self.log_test("Map Coordinates - Malaysian Centered", False, f"Only {malaysian_centered}/{len(scenarios)} scenarios centered on Malaysia")
            
            return True
            
        except Exception as e:
            self.log_test("Map Coordinates - API Call", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all Malaysian context tests"""
        print("🇲🇾 Starting Malaysian Armed Forces (MAF) Context Tests")
        print(f"📡 Testing endpoint: {self.base_url}")
        print("=" * 70)

        # Run Malaysian context tests
        self.test_malaysian_scenarios()
        self.test_malaysian_emitters()
        self.test_malaysian_countermeasures()
        self.test_ai_malaysian_context()
        self.test_map_coordinates()

        # Print summary
        print("=" * 70)
        print(f"📊 Malaysian Context Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Malaysian context tests passed! MAF integration verified.")
        else:
            failed_tests = [t for t in self.test_results if not t['success']]
            print(f"⚠️  {len(failed_tests)} tests failed:")
            for test in failed_tests:
                print(f"   - {test['test_name']}: {test['details']}")

        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = MalaysianContextTester()
    success = tester.run_all_tests()
    
    # Save results
    with open('/app/test_reports/malaysian_context_results.json', 'w') as f:
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