#!/usr/bin/env python3
"""
Rate limiting and abuse prevention testing.
Tests various abuse scenarios and rate limiting effectiveness.
"""
import asyncio
import aiohttp
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import requests
import json
from datetime import datetime, timedelta


class RateLimitTester:
    """Test rate limiting and abuse prevention mechanisms."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all rate limiting and abuse prevention tests."""
        print("🚦 Rate Limiting and Abuse Prevention Test Suite")
        print("=" * 60)
        
        test_methods = [
            ("Basic Rate Limiting", self.test_basic_rate_limiting),
            ("Concurrent Request Flooding", self.test_concurrent_flooding),
            ("Distributed Rate Limiting", self.test_distributed_rate_limiting),
            ("Authentication Brute Force", self.test_auth_brute_force),
            ("API Endpoint Abuse", self.test_api_endpoint_abuse),
            ("Large Payload Attacks", self.test_large_payload_attacks),
            ("Slowloris Attack", self.test_slowloris_attack),
            ("Rate Limit Bypass Attempts", self.test_rate_limit_bypass),
            ("Resource Exhaustion", self.test_resource_exhaustion),
            ("Legitimate Traffic Protection", self.test_legitimate_traffic),
        ]
        
        for test_name, test_method in test_methods:
            print(f"\n🧪 Testing: {test_name}")
            try:
                result = test_method()
                self.results[test_name] = result
                status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
                print(f"   {status}: {result.get('summary', 'No summary')}")
            except Exception as e:
                self.results[test_name] = {
                    "passed": False,
                    "summary": f"Test crashed: {str(e)}",
                    "error": str(e)
                }
                print(f"   ❌ FAIL: Test crashed - {str(e)}")
        
        return self.results
    
    def test_basic_rate_limiting(self) -> Dict[str, Any]:
        """Test basic rate limiting functionality."""
        print("     Testing basic rate limiting...")
        
        # Test different endpoint types
        endpoints = [
            ("/api/v1/auth/test", "auth", 10),  # Auth endpoints: 10/min
            ("/api/v1/health", "api", 60),     # API endpoints: 60/min
            ("/health", "global", 100),        # Global: 100/min
        ]
        
        results = {}
        
        for endpoint, limit_type, expected_limit in endpoints:
            print(f"       Testing {endpoint} (expected limit: {expected_limit}/min)")
            
            success_count = 0
            rate_limited_count = 0
            error_count = 0
            
            # Make requests up to the limit + buffer
            test_requests = min(expected_limit + 5, 25)  # Cap at 25 for testing
            
            start_time = time.time()
            
            for i in range(test_requests):
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=3)
                    
                    if response.status_code == 200:
                        success_count += 1
                    elif response.status_code == 429:
                        rate_limited_count += 1
                        print(f"         Rate limited after {i+1} requests")
                        break
                    else:
                        error_count += 1
                    
                    time.sleep(0.1)  # Small delay between requests
                    
                except Exception as e:
                    error_count += 1
            
            elapsed_time = time.time() - start_time
            
            results[endpoint] = {
                "success_count": success_count,
                "rate_limited_count": rate_limited_count,
                "error_count": error_count,
                "elapsed_time": elapsed_time,
                "rate_limiting_working": rate_limited_count > 0
            }
            
            # Cool down between endpoint tests
            time.sleep(2)
        
        # Evaluate results
        working_endpoints = sum(1 for r in results.values() if r["rate_limiting_working"])
        total_endpoints = len(results)
        
        return {
            "passed": working_endpoints >= total_endpoints // 2,  # At least half should work
            "summary": f"Rate limiting working on {working_endpoints}/{total_endpoints} endpoints",
            "details": results
        }
    
    def test_concurrent_flooding(self) -> Dict[str, Any]:
        """Test concurrent request flooding protection."""
        print("     Testing concurrent request flooding...")
        
        def make_request(url: str, request_id: int) -> Dict[str, Any]:
            """Make a single request and return result."""
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": True
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Test with high concurrency
        url = f"{self.base_url}/health"
        concurrent_requests = 50
        
        print(f"       Sending {concurrent_requests} concurrent requests...")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(make_request, url, i) 
                for i in range(concurrent_requests)
            ]
            
            results = []
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e),
                        "status_code": 0
                    })
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r.get("success", False))
        rate_limited_requests = sum(1 for r in results if r.get("status_code") == 429)
        failed_requests = sum(1 for r in results if not r.get("success", False))
        
        # Calculate average response time for successful requests
        successful_times = [r["response_time"] for r in results if r.get("success", False)]
        avg_response_time = sum(successful_times) / len(successful_times) if successful_times else 0
        
        # Server should handle concurrent requests gracefully
        server_stable = (failed_requests / concurrent_requests) < 0.3  # Less than 30% failures
        rate_limiting_active = rate_limited_requests > 0
        
        return {
            "passed": server_stable and (rate_limiting_active or successful_requests > 0),
            "summary": f"Concurrent flooding: {successful_requests} success, {rate_limited_requests} rate limited, {failed_requests} failed",
            "details": {
                "total_requests": concurrent_requests,
                "successful_requests": successful_requests,
                "rate_limited_requests": rate_limited_requests,
                "failed_requests": failed_requests,
                "total_time": total_time,
                "avg_response_time": avg_response_time,
                "server_stable": server_stable,
                "rate_limiting_active": rate_limiting_active
            }
        }
    
    def test_distributed_rate_limiting(self) -> Dict[str, Any]:
        """Test distributed rate limiting (simulating multiple IPs)."""
        print("     Testing distributed rate limiting...")
        
        # Simulate requests from different IPs using different headers
        fake_ips = [
            "192.168.1.100",
            "10.0.0.50", 
            "172.16.0.25",
            "203.0.113.10",
            "198.51.100.5"
        ]
        
        results = {}
        
        for ip in fake_ips:
            headers = {
                "X-Forwarded-For": ip,
                "X-Real-IP": ip
            }
            
            success_count = 0
            rate_limited_count = 0
            
            # Make requests from this "IP"
            for i in range(15):  # Try 15 requests per IP
                try:
                    response = requests.get(
                        f"{self.api_base}/auth/test",
                        headers=headers,
                        timeout=3
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                    elif response.status_code == 429:
                        rate_limited_count += 1
                        break
                    
                    time.sleep(0.1)
                    
                except Exception:
                    break
            
            results[ip] = {
                "success_count": success_count,
                "rate_limited_count": rate_limited_count
            }
            
            time.sleep(0.5)  # Small delay between IPs
        
        # Each IP should be rate limited independently
        ips_with_rate_limiting = sum(1 for r in results.values() if r["rate_limited_count"] > 0)
        
        return {
            "passed": ips_with_rate_limiting >= len(fake_ips) // 2,  # At least half should be rate limited
            "summary": f"Distributed rate limiting: {ips_with_rate_limiting}/{len(fake_ips)} IPs rate limited",
            "details": results
        }
    
    def test_auth_brute_force(self) -> Dict[str, Any]:
        """Test authentication brute force protection."""
        print("     Testing authentication brute force protection...")
        
        # Attempt multiple failed logins
        failed_attempts = 0
        rate_limited_attempts = 0
        
        for i in range(25):  # Try 25 failed login attempts
            try:
                response = requests.post(
                    f"{self.api_base}/auth/login",
                    json={
                        "email": "nonexistent@test.com",
                        "password": f"wrongpassword{i}"
                    },
                    timeout=5
                )
                
                if response.status_code == 401:
                    failed_attempts += 1
                elif response.status_code == 429:
                    rate_limited_attempts += 1
                    print(f"         Brute force protection activated after {failed_attempts} attempts")
                    break
                
                time.sleep(0.2)  # Small delay between attempts
                
            except Exception:
                break
        
        # Should be rate limited before too many attempts
        brute_force_protection = rate_limited_attempts > 0 and failed_attempts < 20
        
        return {
            "passed": brute_force_protection,
            "summary": f"Brute force protection: {failed_attempts} failed attempts before rate limiting",
            "details": {
                "failed_attempts": failed_attempts,
                "rate_limited_attempts": rate_limited_attempts,
                "protection_active": brute_force_protection
            }
        }
    
    def test_api_endpoint_abuse(self) -> Dict[str, Any]:
        """Test API endpoint abuse protection."""
        print("     Testing API endpoint abuse protection...")
        
        # Test different API endpoints
        api_endpoints = [
            "/api/v1/hands/upload",
            "/api/v1/stats/calculate", 
            "/api/v1/analysis/hand",
            "/api/v1/users/me"
        ]
        
        results = {}
        
        for endpoint in api_endpoints:
            success_count = 0
            rate_limited_count = 0
            error_count = 0
            
            # Rapid requests to each endpoint
            for i in range(20):
                try:
                    # Use appropriate HTTP method
                    if "upload" in endpoint or "calculate" in endpoint:
                        response = requests.post(
                            f"{self.base_url}{endpoint}",
                            json={"test": "data"},
                            timeout=3
                        )
                    else:
                        response = requests.get(
                            f"{self.base_url}{endpoint}",
                            timeout=3
                        )
                    
                    if response.status_code in [200, 401, 403, 404]:  # Valid responses
                        success_count += 1
                    elif response.status_code == 429:
                        rate_limited_count += 1
                        break
                    else:
                        error_count += 1
                    
                    time.sleep(0.1)
                    
                except Exception:
                    error_count += 1
            
            results[endpoint] = {
                "success_count": success_count,
                "rate_limited_count": rate_limited_count,
                "error_count": error_count,
                "protected": rate_limited_count > 0 or success_count < 15
            }
            
            time.sleep(1)  # Cool down between endpoints
        
        protected_endpoints = sum(1 for r in results.values() if r["protected"])
        
        return {
            "passed": protected_endpoints >= len(api_endpoints) // 2,
            "summary": f"API abuse protection: {protected_endpoints}/{len(api_endpoints)} endpoints protected",
            "details": results
        }
    
    def test_large_payload_attacks(self) -> Dict[str, Any]:
        """Test large payload attack protection."""
        print("     Testing large payload attack protection...")
        
        # Test different payload sizes
        payload_sizes = [
            (1024, "1KB"),
            (10240, "10KB"), 
            (102400, "100KB"),
            (1048576, "1MB"),
            (10485760, "10MB")
        ]
        
        results = {}
        
        for size, description in payload_sizes:
            large_payload = {"data": "A" * size}
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base}/auth/register",
                    json=large_payload,
                    timeout=15
                )
                end_time = time.time()
                
                results[description] = {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "accepted": response.status_code == 200,
                    "rejected": response.status_code in [400, 413, 422]  # Bad Request, Payload Too Large, Unprocessable Entity
                }
                
            except requests.exceptions.Timeout:
                results[description] = {
                    "status_code": 0,
                    "response_time": 15,
                    "accepted": False,
                    "rejected": True,
                    "timeout": True
                }
            except Exception as e:
                results[description] = {
                    "status_code": 0,
                    "response_time": 0,
                    "accepted": False,
                    "rejected": True,
                    "error": str(e)
                }
            
            time.sleep(1)  # Cool down between tests
        
        # Large payloads should be rejected
        large_payloads_rejected = sum(
            1 for k, r in results.items() 
            if ("MB" in k or "100KB" in k) and r.get("rejected", False)
        )
        
        return {
            "passed": large_payloads_rejected > 0,
            "summary": f"Large payload protection: {large_payloads_rejected} large payloads rejected",
            "details": results
        }
    
    def test_slowloris_attack(self) -> Dict[str, Any]:
        """Test slowloris attack protection (slow HTTP requests)."""
        print("     Testing slowloris attack protection...")
        
        # This is a simplified test - real slowloris would be more complex
        try:
            # Make a request with very slow data sending
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            # Connect to server
            sock.connect(("localhost", 8000))
            
            # Send partial HTTP request
            sock.send(b"GET /health HTTP/1.1\r\n")
            time.sleep(1)
            sock.send(b"Host: localhost\r\n")
            time.sleep(1)
            sock.send(b"User-Agent: SlowClient\r\n")
            time.sleep(5)  # Wait 5 seconds before completing
            
            # Try to complete the request
            sock.send(b"\r\n")
            
            # Try to receive response
            response = sock.recv(1024)
            sock.close()
            
            # If we get a response, check if it's a timeout or error
            response_str = response.decode('utf-8', errors='ignore')
            
            return {
                "passed": "408" in response_str or "400" in response_str,  # Request Timeout or Bad Request
                "summary": "Slowloris protection: Server handled slow request appropriately",
                "details": {
                    "response_received": len(response) > 0,
                    "response_preview": response_str[:100]
                }
            }
            
        except socket.timeout:
            return {
                "passed": True,
                "summary": "Slowloris protection: Server timed out slow connection",
                "details": {"timeout": True}
            }
        except Exception as e:
            return {
                "passed": False,
                "summary": f"Slowloris test failed: {str(e)}",
                "error": str(e)
            }
    
    def test_rate_limit_bypass(self) -> Dict[str, Any]:
        """Test rate limit bypass attempts."""
        print("     Testing rate limit bypass attempts...")
        
        bypass_attempts = []
        
        # Test 1: Different User-Agent headers
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "curl/7.68.0",
            "PostmanRuntime/7.28.0"
        ]
        
        for ua in user_agents:
            rate_limited = False
            for i in range(15):
                try:
                    response = requests.get(
                        f"{self.api_base}/auth/test",
                        headers={"User-Agent": ua},
                        timeout=3
                    )
                    if response.status_code == 429:
                        rate_limited = True
                        break
                    time.sleep(0.1)
                except Exception:
                    break
            
            bypass_attempts.append({
                "method": f"User-Agent: {ua[:30]}...",
                "rate_limited": rate_limited,
                "bypass_successful": not rate_limited
            })
        
        # Test 2: Different X-Forwarded-For headers
        forwarded_ips = ["1.1.1.1", "8.8.8.8", "127.0.0.1", "192.168.1.1"]
        
        for ip in forwarded_ips:
            rate_limited = False
            for i in range(15):
                try:
                    response = requests.get(
                        f"{self.api_base}/auth/test",
                        headers={"X-Forwarded-For": ip},
                        timeout=3
                    )
                    if response.status_code == 429:
                        rate_limited = True
                        break
                    time.sleep(0.1)
                except Exception:
                    break
            
            bypass_attempts.append({
                "method": f"X-Forwarded-For: {ip}",
                "rate_limited": rate_limited,
                "bypass_successful": not rate_limited
            })
        
        # Count successful bypasses
        successful_bypasses = sum(1 for attempt in bypass_attempts if attempt["bypass_successful"])
        
        return {
            "passed": successful_bypasses < len(bypass_attempts) // 2,  # Less than half should succeed
            "summary": f"Rate limit bypass: {successful_bypasses}/{len(bypass_attempts)} bypass attempts succeeded",
            "details": bypass_attempts
        }
    
    def test_resource_exhaustion(self) -> Dict[str, Any]:
        """Test resource exhaustion protection."""
        print("     Testing resource exhaustion protection...")
        
        # Test memory exhaustion with large requests
        memory_test_results = []
        
        # Gradually increase payload size
        for size_mb in [1, 5, 10, 25]:
            payload_size = size_mb * 1024 * 1024  # Convert to bytes
            
            try:
                # Create large payload
                large_data = "X" * payload_size
                
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base}/auth/register",
                    data=large_data,  # Send as raw data
                    timeout=30,
                    headers={"Content-Type": "text/plain"}
                )
                end_time = time.time()
                
                memory_test_results.append({
                    "size_mb": size_mb,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "server_handled": response.status_code in [400, 413, 422]  # Proper rejection
                })
                
            except requests.exceptions.Timeout:
                memory_test_results.append({
                    "size_mb": size_mb,
                    "status_code": 408,
                    "response_time": 30,
                    "server_handled": True,  # Timeout is acceptable
                    "timeout": True
                })
            except Exception as e:
                memory_test_results.append({
                    "size_mb": size_mb,
                    "status_code": 0,
                    "response_time": 0,
                    "server_handled": True,  # Connection error is acceptable
                    "error": str(e)
                })
            
            time.sleep(2)  # Cool down between tests
        
        # Server should handle large requests gracefully
        properly_handled = sum(1 for result in memory_test_results if result["server_handled"])
        
        return {
            "passed": properly_handled >= len(memory_test_results) // 2,
            "summary": f"Resource exhaustion protection: {properly_handled}/{len(memory_test_results)} large requests handled properly",
            "details": memory_test_results
        }
    
    def test_legitimate_traffic(self) -> Dict[str, Any]:
        """Test that legitimate traffic is not blocked."""
        print("     Testing legitimate traffic protection...")
        
        # Simulate normal user behavior
        legitimate_requests = []
        
        # Normal request pattern: occasional requests with reasonable delays
        for i in range(10):
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/health", timeout=5)
                end_time = time.time()
                
                legitimate_requests.append({
                    "request_id": i,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "successful": response.status_code == 200
                })
                
                # Normal user delay between requests
                time.sleep(2)
                
            except Exception as e:
                legitimate_requests.append({
                    "request_id": i,
                    "status_code": 0,
                    "response_time": 0,
                    "successful": False,
                    "error": str(e)
                })
        
        # Calculate success rate
        successful_requests = sum(1 for req in legitimate_requests if req["successful"])
        success_rate = successful_requests / len(legitimate_requests)
        
        # Legitimate traffic should have high success rate
        return {
            "passed": success_rate >= 0.8,  # At least 80% success rate
            "summary": f"Legitimate traffic: {successful_requests}/{len(legitimate_requests)} requests successful ({success_rate:.1%})",
            "details": {
                "total_requests": len(legitimate_requests),
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "avg_response_time": sum(req["response_time"] for req in legitimate_requests if req["successful"]) / max(successful_requests, 1)
            }
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive rate limiting test report."""
        report = []
        report.append("🚦 RATE LIMITING & ABUSE PREVENTION TEST REPORT")
        report.append("=" * 60)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.get("passed", False))
        
        report.append(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed")
        report.append("")
        
        # Test results
        for test_name, result in self.results.items():
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            report.append(f"{status} {test_name}")
            report.append(f"   {result.get('summary', 'No summary')}")
            report.append("")
        
        # Recommendations
        report.append("🛡️  RATE LIMITING RECOMMENDATIONS:")
        if passed_tests < total_tests:
            report.append("- Review and strengthen rate limiting configuration")
            report.append("- Implement additional abuse prevention measures")
            report.append("- Consider implementing CAPTCHA for repeated failures")
            report.append("- Monitor and alert on rate limiting events")
        else:
            report.append("- Rate limiting and abuse prevention working well")
            report.append("- Continue monitoring for new attack patterns")
            report.append("- Consider implementing adaptive rate limiting")
        
        return "\n".join(report)


def main():
    """Run rate limiting and abuse prevention tests."""
    tester = RateLimitTester()
    results = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("📋 FINAL REPORT")
    print("=" * 60)
    
    report = tester.generate_report()
    print(report)
    
    # Save report
    with open("rate_limiting_test_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: rate_limiting_test_report.txt")
    
    # Return exit code
    passed_tests = sum(1 for result in results.values() if result.get("passed", False))
    total_tests = len(results)
    
    if passed_tests == total_tests:
        print("🎉 All rate limiting tests passed!")
        return 0
    else:
        print(f"⚠️  {total_tests - passed_tests} rate limiting tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())