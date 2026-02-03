"""
Comprehensive API endpoint testing script for ABFI platform.
Tests all endpoints to ensure they return valid responses.
"""

import requests
import json
from typing import Dict, List, Any

BASE_URL = "https://abfi-ai.vercel.app"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_endpoint(method: str, endpoint: str, expected_status: int = 200, data: Dict = None) -> Dict[str, Any]:
    """Test a single endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        success = response.status_code == expected_status
        
        result = {
            "success": success,
            "status_code": response.status_code,
            "url": url,
        }
        
        # Try to parse JSON response
        try:
            result["data"] = response.json()
            result["data_type"] = type(result["data"]).__name__
            if isinstance(result["data"], list):
                result["data_count"] = len(result["data"])
            elif isinstance(result["data"], dict):
                result["data_keys"] = list(result["data"].keys())
        except:
            result["data"] = response.text[:200]
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url,
        }

def print_result(endpoint: str, result: Dict[str, Any]):
    """Print test result with colors."""
    if result["success"]:
        print(f"{Colors.GREEN}✓{Colors.END} {endpoint}")
        if "data_type" in result:
            print(f"  Type: {result['data_type']}", end="")
            if "data_count" in result:
                print(f", Count: {result['data_count']}")
            elif "data_keys" in result:
                print(f", Keys: {', '.join(result['data_keys'][:5])}")
            else:
                print()
    else:
        print(f"{Colors.RED}✗{Colors.END} {endpoint}")
        if "error" in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Status: {result.get('status_code', 'unknown')}")

def main():
    """Run all endpoint tests."""
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}ABFI Platform API Endpoint Testing{Colors.END}")
    print(f"{Colors.BLUE}Base URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    tests = []
    
    # System Endpoints
    print(f"\n{Colors.YELLOW}System Endpoints:{Colors.END}")
    tests.append(("GET", "/", "Root endpoint"))
    tests.append(("GET", "/health", "Health check"))
    tests.append(("GET", "/api/v1/status", "API status"))
    
    # Sentiment API
    print(f"\n{Colors.YELLOW}Sentiment API:{Colors.END}")
    tests.append(("GET", "/api/v1/sentiment/index", "Current sentiment index"))
    tests.append(("GET", "/api/v1/sentiment/index/history", "Sentiment history"))
    tests.append(("GET", "/api/v1/sentiment/trend", "Sentiment trend"))
    tests.append(("GET", "/api/v1/sentiment/lenders", "Lender scores"))
    tests.append(("GET", "/api/v1/sentiment/documents/feed", "Document feed"))
    
    # Prices API
    print(f"\n{Colors.YELLOW}Prices API:{Colors.END}")
    tests.append(("GET", "/api/v1/prices/kpis", "Price KPIs"))
    tests.append(("GET", "/api/v1/prices/current/UCO", "Current UCO price"))
    tests.append(("GET", "/api/v1/prices/ohlc/UCO", "OHLC data"))
    tests.append(("GET", "/api/v1/prices/forward/UCO", "Forward curve"))
    tests.append(("GET", "/api/v1/prices/heatmap/UCO", "Regional heatmap"))
    tests.append(("GET", "/api/v1/prices/feedstock", "Feedstock prices"))
    tests.append(("GET", "/api/v1/prices/regional", "Regional prices"))
    
    # Policy API
    print(f"\n{Colors.YELLOW}Policy API:{Colors.END}")
    tests.append(("GET", "/api/v1/policy/kpis", "Policy KPIs"))
    tests.append(("GET", "/api/v1/policy/timeline", "Policy timeline"))
    tests.append(("GET", "/api/v1/policy/kanban", "Policy kanban"))
    tests.append(("GET", "/api/v1/policy/mandate-scenarios", "Mandate scenarios"))
    tests.append(("GET", "/api/v1/policy/accu-price", "ACCU price"))
    tests.append(("GET", "/api/v1/policy/updates", "Policy updates"))
    tests.append(("GET", "/api/v1/policy/carbon-prices", "Carbon prices"))
    tests.append(("GET", "/api/v1/policy/sustainability", "Sustainability metrics"))
    
    # Carbon Calculator (POST)
    print(f"\n{Colors.YELLOW}Carbon Calculator:{Colors.END}")
    carbon_input = {
        "annual_output_tonnes": 50000,
        "emission_factor": 0.85,
        "carbon_price": 34.50
    }
    tests.append(("POST", "/api/v1/policy/carbon-calculator", "Carbon calculator", carbon_input))
    
    # Intelligence API
    print(f"\n{Colors.YELLOW}Intelligence API:{Colors.END}")
    tests.append(("GET", "/api/v1/intelligence/latest", "Latest intelligence"))
    
    # Run all tests
    results = []
    for test in tests:
        method, endpoint, description = test[:3]
        data = test[3] if len(test) > 3 else None
        
        result = test_endpoint(method, endpoint, data=data)
        result["description"] = description
        results.append(result)
        print_result(f"{method} {endpoint} - {description}", result)
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary:{Colors.END}")
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    
    pass_rate = (passed / total * 100) if total > 0 else 0
    print(f"Pass Rate: {pass_rate:.1f}%")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    # Save detailed results
    with open("/home/ubuntu/abfi-ai/api_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Detailed results saved to: api_test_results.json\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
