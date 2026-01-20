#!/usr/bin/env python3
"""
Security scanner for the poker analyzer application.
Performs static analysis and runtime security checks.
"""
import os
import re
import ast
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class SecurityScanner:
    """Static and dynamic security scanner."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.findings = []
        self.severity_levels = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
            "INFO": 0
        }
    
    def scan_all(self) -> Dict[str, Any]:
        """Run all security scans."""
        print("🔍 Starting comprehensive security scan...")
        
        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "scans": {}
        }
        
        # Static analysis scans
        scan_results["scans"]["hardcoded_secrets"] = self.scan_hardcoded_secrets()
        scan_results["scans"]["sql_injection"] = self.scan_sql_injection_patterns()
        scan_results["scans"]["xss_vulnerabilities"] = self.scan_xss_patterns()
        scan_results["scans"]["insecure_functions"] = self.scan_insecure_functions()
        scan_results["scans"]["weak_crypto"] = self.scan_weak_cryptography()
        scan_results["scans"]["file_permissions"] = self.scan_file_permissions()
        scan_results["scans"]["dependency_vulnerabilities"] = self.scan_dependencies()
        scan_results["scans"]["configuration_security"] = self.scan_configuration()
        scan_results["scans"]["authentication_issues"] = self.scan_authentication()
        scan_results["scans"]["authorization_issues"] = self.scan_authorization()
        
        # Calculate overall risk score
        scan_results["risk_score"] = self.calculate_risk_score(scan_results["scans"])
        scan_results["total_findings"] = sum(len(scan["findings"]) for scan in scan_results["scans"].values())
        
        return scan_results
    
    def scan_hardcoded_secrets(self) -> Dict[str, Any]:
        """Scan for hardcoded secrets and API keys."""
        print("  🔑 Scanning for hardcoded secrets...")
        
        findings = []
        
        # Patterns for common secrets
        secret_patterns = [
            (r'api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', "API Key"),
            (r'secret[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', "Secret Key"),
            (r'password["\s]*[:=]["\s]*["\']([^"\']{8,})["\']', "Password"),
            (r'token["\s]*[:=]["\s]*["\']([a-zA-Z0-9_-]{20,})["\']', "Token"),
            (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API Key"),
            (r'gsk_[a-zA-Z0-9]{20,}', "Groq API Key"),
            (r'AIza[0-9A-Za-z_-]{35}', "Google API Key"),
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
            (r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', "UUID/GUID"),
        ]
        
        # Files to scan
        file_patterns = ["*.py", "*.js", "*.ts", "*.json", "*.yml", "*.yaml", "*.env*", "*.conf", "*.config"]
        
        for pattern in file_patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._should_skip_file(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for secret_pattern, secret_type in secret_patterns:
                        matches = re.finditer(secret_pattern, content, re.IGNORECASE)
                        for match in matches:
                            # Skip if it's in a comment or example
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line_end = content.find('\n', match.end())
                            if line_end == -1:
                                line_end = len(content)
                            line = content[line_start:line_end]
                            
                            if any(keyword in line.lower() for keyword in ['example', 'test', 'dummy', 'placeholder', 'xxx']):
                                continue
                            
                            findings.append({
                                "type": "Hardcoded Secret",
                                "severity": "HIGH",
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": content[:match.start()].count('\n') + 1,
                                "description": f"Potential {secret_type} found",
                                "pattern": secret_pattern,
                                "context": line.strip()
                            })
                            
                except Exception as e:
                    continue
        
        return {
            "name": "Hardcoded Secrets Scan",
            "findings": findings,
            "severity": "HIGH" if findings else "INFO"
        }
    
    def scan_sql_injection_patterns(self) -> Dict[str, Any]:
        """Scan for SQL injection vulnerabilities."""
        print("  💉 Scanning for SQL injection patterns...")
        
        findings = []
        
        # Dangerous SQL patterns
        sql_patterns = [
            (r'execute\s*\(\s*["\'].*%.*["\']', "String formatting in SQL execute"),
            (r'query\s*\(\s*["\'].*\+.*["\']', "String concatenation in SQL query"),
            (r'cursor\.execute\s*\(\s*f["\']', "f-string in SQL execute"),
            (r'\.format\s*\(.*\)\s*\)', "String format in SQL query"),
            (r'SELECT.*\+.*FROM', "String concatenation in SELECT"),
            (r'WHERE.*\+.*=', "String concatenation in WHERE clause"),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in sql_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line_end = content.find('\n', match.end())
                        if line_end == -1:
                            line_end = len(content)
                        line = content[line_start:line_end]
                        
                        findings.append({
                            "type": "SQL Injection Risk",
                            "severity": "HIGH",
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_num,
                            "description": description,
                            "context": line.strip()
                        })
                        
            except Exception:
                continue
        
        return {
            "name": "SQL Injection Scan",
            "findings": findings,
            "severity": "HIGH" if findings else "INFO"
        }
    
    def scan_xss_patterns(self) -> Dict[str, Any]:
        """Scan for XSS vulnerabilities."""
        print("  🕸️  Scanning for XSS patterns...")
        
        findings = []
        
        # XSS vulnerability patterns
        xss_patterns = [
            (r'innerHTML\s*=\s*.*\+', "innerHTML with concatenation"),
            (r'document\.write\s*\(.*\+', "document.write with concatenation"),
            (r'eval\s*\(.*request', "eval with request data"),
            (r'dangerouslySetInnerHTML', "React dangerouslySetInnerHTML"),
            (r'v-html\s*=', "Vue v-html directive"),
        ]
        
        file_patterns = ["*.js", "*.ts", "*.jsx", "*.tsx", "*.vue", "*.html"]
        
        for pattern in file_patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._should_skip_file(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for xss_pattern, description in xss_patterns:
                        matches = re.finditer(xss_pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line_end = content.find('\n', match.end())
                            if line_end == -1:
                                line_end = len(content)
                            line = content[line_start:line_end]
                            
                            findings.append({
                                "type": "XSS Risk",
                                "severity": "MEDIUM",
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_num,
                                "description": description,
                                "context": line.strip()
                            })
                            
                except Exception:
                    continue
        
        return {
            "name": "XSS Vulnerability Scan",
            "findings": findings,
            "severity": "MEDIUM" if findings else "INFO"
        }
    
    def scan_insecure_functions(self) -> Dict[str, Any]:
        """Scan for usage of insecure functions."""
        print("  ⚠️  Scanning for insecure functions...")
        
        findings = []
        
        # Insecure function patterns
        insecure_patterns = [
            (r'\beval\s*\(', "eval() function usage", "HIGH"),
            (r'\bexec\s*\(', "exec() function usage", "HIGH"),
            (r'subprocess\.call\s*\(.*shell\s*=\s*True', "subprocess with shell=True", "HIGH"),
            (r'os\.system\s*\(', "os.system() usage", "HIGH"),
            (r'pickle\.loads?\s*\(', "pickle.load() usage", "MEDIUM"),
            (r'yaml\.load\s*\((?!.*Loader)', "yaml.load() without safe loader", "MEDIUM"),
            (r'random\.random\s*\(', "random.random() for security", "LOW"),
            (r'md5\s*\(', "MD5 hash usage", "MEDIUM"),
            (r'sha1\s*\(', "SHA1 hash usage", "MEDIUM"),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description, severity in insecure_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line_end = content.find('\n', match.end())
                        if line_end == -1:
                            line_end = len(content)
                        line = content[line_start:line_end]
                        
                        findings.append({
                            "type": "Insecure Function",
                            "severity": severity,
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_num,
                            "description": description,
                            "context": line.strip()
                        })
                        
            except Exception:
                continue
        
        return {
            "name": "Insecure Functions Scan",
            "findings": findings,
            "severity": "HIGH" if any(f["severity"] == "HIGH" for f in findings) else "MEDIUM" if findings else "INFO"
        }
    
    def scan_weak_cryptography(self) -> Dict[str, Any]:
        """Scan for weak cryptographic implementations."""
        print("  🔐 Scanning for weak cryptography...")
        
        findings = []
        
        # Weak crypto patterns
        crypto_patterns = [
            (r'DES\s*\(', "DES encryption usage", "HIGH"),
            (r'RC4\s*\(', "RC4 encryption usage", "HIGH"),
            (r'MD5\s*\(', "MD5 hash usage", "MEDIUM"),
            (r'SHA1\s*\(', "SHA1 hash usage", "MEDIUM"),
            (r'random\.randint\s*\(.*security', "random.randint for security", "MEDIUM"),
            (r'ECB\s*\(', "ECB mode usage", "HIGH"),
            (r'key\s*=\s*["\'][^"\']{1,15}["\']', "Short encryption key", "HIGH"),
            (r'iv\s*=\s*["\'][^"\']{1,15}["\']', "Short IV", "MEDIUM"),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description, severity in crypto_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line_end = content.find('\n', match.end())
                        if line_end == -1:
                            line_end = len(content)
                        line = content[line_start:line_end]
                        
                        findings.append({
                            "type": "Weak Cryptography",
                            "severity": severity,
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_num,
                            "description": description,
                            "context": line.strip()
                        })
                        
            except Exception:
                continue
        
        return {
            "name": "Weak Cryptography Scan",
            "findings": findings,
            "severity": "HIGH" if any(f["severity"] == "HIGH" for f in findings) else "MEDIUM" if findings else "INFO"
        }
    
    def scan_file_permissions(self) -> Dict[str, Any]:
        """Scan for insecure file permissions."""
        print("  📁 Scanning file permissions...")
        
        findings = []
        
        # Check sensitive files
        sensitive_files = [
            ".env", ".env.local", ".env.production",
            "config.json", "secrets.json",
            "private.key", "*.pem", "*.key"
        ]
        
        for pattern in sensitive_files:
            for file_path in self.project_root.rglob(pattern):
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]  # Get last 3 digits
                    
                    # Check if file is world-readable (others can read)
                    if int(mode[2]) >= 4:
                        findings.append({
                            "type": "File Permission",
                            "severity": "MEDIUM",
                            "file": str(file_path.relative_to(self.project_root)),
                            "description": f"Sensitive file is world-readable (permissions: {mode})",
                            "recommendation": "Change permissions to 600 or 640"
                        })
                    
                    # Check if file is world-writable
                    if int(mode[2]) >= 2:
                        findings.append({
                            "type": "File Permission",
                            "severity": "HIGH",
                            "file": str(file_path.relative_to(self.project_root)),
                            "description": f"Sensitive file is world-writable (permissions: {mode})",
                            "recommendation": "Change permissions to 600 or 640"
                        })
                        
                except Exception:
                    continue
        
        return {
            "name": "File Permissions Scan",
            "findings": findings,
            "severity": "HIGH" if any(f["severity"] == "HIGH" for f in findings) else "MEDIUM" if findings else "INFO"
        }
    
    def scan_dependencies(self) -> Dict[str, Any]:
        """Scan for vulnerable dependencies."""
        print("  📦 Scanning dependencies...")
        
        findings = []
        
        # Check Python dependencies
        requirements_files = ["requirements.txt", "pyproject.toml", "Pipfile"]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    # Run safety check if available
                    result = subprocess.run(
                        ["safety", "check", "-r", str(req_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0 and "vulnerabilities found" in result.stdout:
                        findings.append({
                            "type": "Vulnerable Dependency",
                            "severity": "HIGH",
                            "file": req_file,
                            "description": "Vulnerable Python packages found",
                            "details": result.stdout
                        })
                        
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # Safety not installed or timeout
                    pass
        
        # Check Node.js dependencies
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.project_root
                )
                
                if result.returncode != 0:
                    audit_data = json.loads(result.stdout)
                    if audit_data.get("metadata", {}).get("vulnerabilities", {}).get("total", 0) > 0:
                        findings.append({
                            "type": "Vulnerable Dependency",
                            "severity": "HIGH",
                            "file": "package.json",
                            "description": "Vulnerable Node.js packages found",
                            "details": f"Total vulnerabilities: {audit_data['metadata']['vulnerabilities']['total']}"
                        })
                        
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                pass
        
        return {
            "name": "Dependency Vulnerability Scan",
            "findings": findings,
            "severity": "HIGH" if findings else "INFO"
        }
    
    def scan_configuration(self) -> Dict[str, Any]:
        """Scan configuration files for security issues."""
        print("  ⚙️  Scanning configuration...")
        
        findings = []
        
        # Check environment files
        env_files = [".env", ".env.local", ".env.production", ".env.example"]
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()
                    
                    # Check for debug mode in production
                    if "DEBUG=True" in content or "DEBUG=true" in content:
                        findings.append({
                            "type": "Configuration Issue",
                            "severity": "MEDIUM",
                            "file": env_file,
                            "description": "Debug mode enabled",
                            "recommendation": "Disable debug mode in production"
                        })
                    
                    # Check for default secrets
                    if "SECRET_KEY=changeme" in content or "SECRET_KEY=default" in content:
                        findings.append({
                            "type": "Configuration Issue",
                            "severity": "HIGH",
                            "file": env_file,
                            "description": "Default secret key in use",
                            "recommendation": "Generate a strong, unique secret key"
                        })
                    
                    # Check for insecure database URLs
                    if re.search(r'DATABASE_URL=.*://.*:.*@.*/', content):
                        if "localhost" not in content and "127.0.0.1" not in content:
                            findings.append({
                                "type": "Configuration Issue",
                                "severity": "MEDIUM",
                                "file": env_file,
                                "description": "Database credentials in environment file",
                                "recommendation": "Use secure credential management"
                            })
                            
                except Exception:
                    continue
        
        return {
            "name": "Configuration Security Scan",
            "findings": findings,
            "severity": "HIGH" if any(f["severity"] == "HIGH" for f in findings) else "MEDIUM" if findings else "INFO"
        }
    
    def scan_authentication(self) -> Dict[str, Any]:
        """Scan authentication implementation."""
        print("  🔑 Scanning authentication...")
        
        findings = []
        
        # Look for authentication files
        auth_files = list(self.project_root.rglob("*auth*.py")) + list(self.project_root.rglob("*security*.py"))
        
        for auth_file in auth_files:
            try:
                with open(auth_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for weak password requirements
                if "len(password) < 8" not in content and "password" in content:
                    findings.append({
                        "type": "Authentication Issue",
                        "severity": "MEDIUM",
                        "file": str(auth_file.relative_to(self.project_root)),
                        "description": "No minimum password length check found",
                        "recommendation": "Implement minimum password length requirement"
                    })
                
                # Check for session timeout
                if "session" in content.lower() and "timeout" not in content.lower():
                    findings.append({
                        "type": "Authentication Issue",
                        "severity": "LOW",
                        "file": str(auth_file.relative_to(self.project_root)),
                        "description": "No session timeout implementation found",
                        "recommendation": "Implement session timeout"
                    })
                
                # Check for rate limiting on auth endpoints
                if "login" in content.lower() and "rate" not in content.lower():
                    findings.append({
                        "type": "Authentication Issue",
                        "severity": "MEDIUM",
                        "file": str(auth_file.relative_to(self.project_root)),
                        "description": "No rate limiting on authentication endpoints",
                        "recommendation": "Implement rate limiting for login attempts"
                    })
                    
            except Exception:
                continue
        
        return {
            "name": "Authentication Security Scan",
            "findings": findings,
            "severity": "MEDIUM" if findings else "INFO"
        }
    
    def scan_authorization(self) -> Dict[str, Any]:
        """Scan authorization implementation."""
        print("  🛡️  Scanning authorization...")
        
        findings = []
        
        # Look for authorization/RBAC files
        authz_files = list(self.project_root.rglob("*rbac*.py")) + list(self.project_root.rglob("*authorization*.py"))
        
        for authz_file in authz_files:
            try:
                with open(authz_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for proper permission checks
                if "def " in content and "permission" not in content.lower():
                    findings.append({
                        "type": "Authorization Issue",
                        "severity": "MEDIUM",
                        "file": str(authz_file.relative_to(self.project_root)),
                        "description": "Functions without permission checks",
                        "recommendation": "Implement proper permission checks"
                    })
                
                # Check for role-based access
                if "user" in content.lower() and "role" not in content.lower():
                    findings.append({
                        "type": "Authorization Issue",
                        "severity": "LOW",
                        "file": str(authz_file.relative_to(self.project_root)),
                        "description": "No role-based access control found",
                        "recommendation": "Implement role-based access control"
                    })
                    
            except Exception:
                continue
        
        return {
            "name": "Authorization Security Scan",
            "findings": findings,
            "severity": "MEDIUM" if findings else "INFO"
        }
    
    def calculate_risk_score(self, scans: Dict[str, Any]) -> int:
        """Calculate overall risk score based on findings."""
        total_score = 0
        
        for scan in scans.values():
            findings = scan.get("findings", [])
            for finding in findings:
                severity = finding.get("severity", "LOW")
                total_score += self.severity_levels.get(severity, 1)
        
        return total_score
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during scanning."""
        skip_patterns = [
            "node_modules", ".git", "__pycache__", ".pytest_cache",
            ".venv", "venv", "env", ".env", "dist", "build",
            ".next", "coverage", ".coverage", "*.pyc", "*.pyo"
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def generate_report(self, scan_results: Dict[str, Any]) -> str:
        """Generate a comprehensive security scan report."""
        report = []
        report.append("🔍 SECURITY SCAN REPORT")
        report.append("=" * 50)
        report.append(f"Scan Date: {scan_results['timestamp']}")
        report.append(f"Total Findings: {scan_results['total_findings']}")
        report.append(f"Risk Score: {scan_results['risk_score']}")
        report.append("")
        
        # Risk level assessment
        risk_score = scan_results['risk_score']
        if risk_score == 0:
            risk_level = "LOW"
        elif risk_score <= 10:
            risk_level = "MEDIUM"
        elif risk_score <= 25:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        report.append(f"🚨 OVERALL RISK LEVEL: {risk_level}")
        report.append("")
        
        # Detailed scan results
        for scan_name, scan_data in scan_results["scans"].items():
            findings = scan_data.get("findings", [])
            severity = scan_data.get("severity", "INFO")
            
            report.append(f"📋 {scan_data['name']}")
            report.append(f"   Severity: {severity}")
            report.append(f"   Findings: {len(findings)}")
            
            if findings:
                # Show top 3 findings
                for finding in findings[:3]:
                    report.append(f"   - {finding['severity']}: {finding['description']}")
                    if 'file' in finding:
                        report.append(f"     File: {finding['file']}")
                    if 'recommendation' in finding:
                        report.append(f"     Fix: {finding['recommendation']}")
                
                if len(findings) > 3:
                    report.append(f"   ... and {len(findings) - 3} more findings")
            
            report.append("")
        
        # Recommendations
        report.append("🛠️  SECURITY RECOMMENDATIONS:")
        if risk_score > 0:
            report.append("1. Address HIGH and CRITICAL severity findings immediately")
            report.append("2. Review and fix hardcoded secrets")
            report.append("3. Update vulnerable dependencies")
            report.append("4. Implement proper input validation")
            report.append("5. Review file permissions on sensitive files")
        else:
            report.append("✅ No security issues found in static analysis")
            report.append("   Continue with regular security monitoring")
        
        return "\n".join(report)


def main():
    """Run security scanner."""
    scanner = SecurityScanner()
    results = scanner.scan_all()
    
    print("\n" + "=" * 50)
    print("📊 SCAN COMPLETE")
    print("=" * 50)
    
    report = scanner.generate_report(results)
    print(report)
    
    # Save results
    with open("security_scan_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    
    with open("security_scan_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 Results saved to:")
    print(f"   - security_scan_results.json (detailed)")
    print(f"   - security_scan_report.txt (summary)")
    
    # Return exit code based on risk level
    risk_score = results['risk_score']
    if risk_score == 0:
        print("\n🎉 No security issues found!")
        return 0
    elif risk_score <= 10:
        print(f"\n⚠️  Medium risk level detected (score: {risk_score})")
        return 1
    else:
        print(f"\n🚨 High risk level detected (score: {risk_score})")
        return 2


if __name__ == "__main__":
    exit(main())