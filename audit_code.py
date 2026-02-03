"""
Code audit script using Claude API to identify bugs and issues in ABFI platform.
"""

import os
import json
from pathlib import Path
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def read_file(filepath):
    """Read file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def audit_code_with_claude(files_content, focus_area):
    """Audit code using Claude API."""
    
    prompt = f"""You are an expert software engineer auditing a FastAPI + React application for the Australian bioenergy intelligence platform (ABFI).

Focus Area: {focus_area}

Files to audit:
{files_content}

Please analyze the code and identify:
1. **Critical Bugs**: Errors that will cause runtime failures or crashes
2. **Logic Errors**: Incorrect business logic or data handling
3. **Database Issues**: Schema mismatches, query errors, connection issues
4. **API Issues**: Missing endpoints, incorrect request/response handling, validation errors
5. **Frontend Issues**: API integration problems, state management issues, rendering errors
6. **Configuration Issues**: Missing environment variables, incorrect settings
7. **Performance Issues**: Inefficient queries, memory leaks, slow operations
8. **Security Issues**: SQL injection, XSS, CORS misconfigurations

For each issue found, provide:
- **Severity**: CRITICAL, HIGH, MEDIUM, LOW
- **Location**: File and line number
- **Description**: What the issue is
- **Impact**: What will break or fail
- **Fix**: Specific code changes needed

Format your response as JSON:
{{
  "issues": [
    {{
      "severity": "CRITICAL",
      "location": "app/main.py:45",
      "category": "Runtime Error",
      "description": "...",
      "impact": "...",
      "fix": "..."
    }}
  ],
  "summary": {{
    "total_issues": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  }}
}}
"""
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=16000,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text

def main():
    """Main audit function."""
    
    project_root = Path("/home/ubuntu/abfi-ai")
    
    # Audit areas
    audit_areas = [
        {
            "name": "Backend API Endpoints",
            "files": [
                "app/main.py",
                "app/api/v1/sentiment.py",
                "app/api/v1/prices.py",
                "app/api/v1/policy.py",
                "app/api/v1/carbon.py",
                "app/api/v1/counterparty.py",
                "app/api/v1/intelligence.py",
            ]
        },
        {
            "name": "Database Layer",
            "files": [
                "app/db/database.py",
                "app/db/models.py",
                "app/db/schema.sql",
            ]
        },
        {
            "name": "Services and Business Logic",
            "files": [
                "app/services/llm_analyzer.py",
                "app/services/data_pipeline.py",
                "app/services/intelligence.py",
                "app/services/scheduler.py",
            ]
        },
        {
            "name": "Frontend Dashboard",
            "files": [
                "dashboard/src/App.tsx",
                "dashboard/src/api/client.ts",
                "dashboard/src/pages/SentimentDashboard.tsx",
                "dashboard/src/pages/PricesDashboard.tsx",
                "dashboard/src/pages/PolicyDashboard.tsx",
            ]
        },
        {
            "name": "Configuration and Deployment",
            "files": [
                "app/core/config.py",
                "api/index.py",
                "requirements.txt",
                "requirements-vercel.txt",
                "dashboard/package.json",
            ]
        }
    ]
    
    all_issues = []
    
    for area in audit_areas:
        print(f"\n{'='*80}")
        print(f"Auditing: {area['name']}")
        print(f"{'='*80}")
        
        # Read all files in this area
        files_content = ""
        for filepath in area['files']:
            full_path = project_root / filepath
            if full_path.exists():
                content = read_file(full_path)
                files_content += f"\n\n{'='*60}\nFile: {filepath}\n{'='*60}\n{content}\n"
            else:
                files_content += f"\n\nFile: {filepath} - NOT FOUND\n"
        
        # Audit with Claude
        try:
            result = audit_code_with_claude(files_content, area['name'])
            print(f"\nAudit Result:\n{result}")
            
            # Try to parse JSON
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].split("```")[0].strip()
                else:
                    json_str = result
                
                audit_result = json.loads(json_str)
                all_issues.extend(audit_result.get("issues", []))
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON response for {area['name']}")
                all_issues.append({
                    "severity": "HIGH",
                    "location": area['name'],
                    "category": "Audit Error",
                    "description": "Could not parse audit results",
                    "impact": "Manual review needed",
                    "fix": result[:500]
                })
        except Exception as e:
            print(f"Error auditing {area['name']}: {e}")
            all_issues.append({
                "severity": "HIGH",
                "location": area['name'],
                "category": "Audit Error",
                "description": str(e),
                "impact": "Could not complete audit",
                "fix": "Manual review needed"
            })
    
    # Save all issues to file
    output_file = project_root / "AUDIT_RESULTS.json"
    with open(output_file, 'w') as f:
        json.dump({
            "issues": all_issues,
            "summary": {
                "total_issues": len(all_issues),
                "critical": len([i for i in all_issues if i.get("severity") == "CRITICAL"]),
                "high": len([i for i in all_issues if i.get("severity") == "HIGH"]),
                "medium": len([i for i in all_issues if i.get("severity") == "MEDIUM"]),
                "low": len([i for i in all_issues if i.get("severity") == "LOW"]),
            }
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Audit Complete! Results saved to: {output_file}")
    print(f"Total Issues Found: {len(all_issues)}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
