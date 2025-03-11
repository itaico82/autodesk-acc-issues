#!/usr/bin/env python
"""
Script to list all issues in a project using the Autodesk Construction Cloud API.
"""
import os
import json
import sys
import argparse
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import time

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Session storage file
SESSIONS_FILE = "sessions.json"

def load_sessions() -> Dict[str, Any]:
    """Load sessions from file."""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {e}")
    return {}

# Load environment variables
load_dotenv()

# Get credentials
AUTODESK_CLIENT_ID = os.environ.get("AUTODESK_CLIENT_ID")
AUTODESK_CLIENT_SECRET = os.environ.get("AUTODESK_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/oauth/callback"

if not AUTODESK_CLIENT_ID or not AUTODESK_CLIENT_SECRET:
    print("Error: AUTODESK_CLIENT_ID and AUTODESK_CLIENT_SECRET must be set in .env file")
    sys.exit(1)

# Required scopes for issues API
REQUIRED_SCOPES = [
    "data:read",
    "data:write",
    "account:read",
    "account:write",
    "user:read",
    "user:write"
]

# Autodesk Construction Cloud API endpoints template
ENDPOINTS = [
    "https://developer.api.autodesk.com/construction/issues/v1/projects/{project_id}/issues",  # Primary ACC endpoint
    "https://developer.api.autodesk.com/issues/v1/containers/{project_id}/quality-issues",     # Quality issues
    "https://developer.api.autodesk.com/bim360/issues/v1/containers/{project_id}/issues",      # BIM360 issues
    "https://developer.api.autodesk.com/construction/v1/projects/{project_id}/issues",         # Construction issues
    "https://developer.api.autodesk.com/field/issues/v1/projects/{project_id}/issues",         # Field issues
    "https://developer.api.autodesk.com/acc/v1/projects/{project_id}/issues"                   # ACC issues
]


class Issue(BaseModel):
    """Model for an issue."""
    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = Field(None, alias="createdAt")
    created_by: Optional[str] = Field(None, alias="createdBy")
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    due_date: Optional[str] = Field(None, alias="dueDate")
    display_id: Optional[int] = Field(None, alias="displayId")
    container_id: Optional[str] = Field(None, alias="containerId")
    issue_type_id: Optional[str] = Field(None, alias="issueTypeId")
    issue_subtype_id: Optional[str] = Field(None, alias="issueSubtypeId")
    owner_id: Optional[str] = Field(None, alias="ownerId")
    comment_count: Optional[int] = Field(None, alias="commentCount")
    attachment_count: Optional[int] = Field(None, alias="attachmentCount")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    updated_by: Optional[str] = Field(None, alias="updatedBy")

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True


def exchange_code_for_token(code: str) -> str:
    """Exchange authorization code for access token."""
    token_url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": AUTODESK_CLIENT_ID,
        "client_secret": AUTODESK_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(token_url, data=data, headers=headers)
            if response.status_code == 200:
                return response.json()["access_token"]
            else:
                print(f"Error exchanging code for token: {response.status_code} - {response.text}")
                sys.exit(1)
    except Exception as e:
        print(f"Exception exchanging code for token: {str(e)}")
        sys.exit(1)


def normalize_project_id(project_id: str) -> str:
    """Normalize the project ID by adding 'b.' prefix if not present."""
    if not project_id.startswith("b."):
        return f"b.{project_id}"
    return project_id


def list_issues(access_token: str, project_id: str) -> List[Issue]:
    """List all issues in the project using the provided access token."""
    # For issues endpoints, we need to remove the 'b.' prefix
    clean_project_id = project_id.replace('b.', '') if project_id.startswith('b.') else project_id
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "limit": 100,  # Maximum number of issues to return
        "offset": 0    # Starting offset
    }
    
    print(f"Listing issues for project {clean_project_id}...")
    
    # Try all endpoints
    with httpx.Client() as client:
        for endpoint_template in ENDPOINTS:
            endpoint = endpoint_template.format(project_id=clean_project_id)
            print(f"Trying endpoint: {endpoint}")
            try:
                response = client.get(
                    endpoint,
                    headers=headers,
                    params=params,
                    timeout=10.0  # Set a timeout
                )
                
                if response.status_code == 200:
                    return parse_issues_response(response.json())
                elif response.status_code == 404:
                    print(f"Project or endpoint not found: {endpoint}")
                elif response.status_code == 403:
                    print(f"Access denied for endpoint: {endpoint}")
                else:
                    print(f"Error with endpoint {endpoint}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Exception with endpoint {endpoint}: {str(e)}")
                continue
        
        print("All endpoints failed.")
        return []


def parse_issues_response(data: Dict[str, Any]) -> List[Issue]:
    """Parse the issues response from the API."""
    issues = []
    
    # Print the raw response for debugging
    print(f"Response data structure: {list(data.keys())}")
    
    # Check for different response formats
    if "results" in data:
        results = data["results"]
    elif "data" in data:
        results = data["data"]
    elif "issues" in data:
        results = data["issues"]
    else:
        print(f"Unexpected response format: {json.dumps(data, indent=2)}")
        return []
    
    print(f"Found {len(results)} issues in the response")
    
    # Parse issues
    for issue_data in results:
        try:
            issue = Issue.model_validate(issue_data)
            issues.append(issue)
        except Exception as e:
            print(f"Error parsing issue: {e}")
            print(f"Issue data: {json.dumps(issue_data, indent=2)}")
    
    return issues


def print_issues(issues: List[Issue]) -> None:
    """Print issues in a readable format."""
    if not issues:
        print("No issues found.")
        return
    
    print(f"\nFound {len(issues)} issues:\n")
    for i, issue in enumerate(issues, 1):
        print(f"Issue {i}:")
        print(f"  ID: {issue.display_id} ({issue.id})")
        print(f"  Title: {issue.title}")
        print(f"  Status: {issue.status or 'Not set'}")
        print(f"  Created at: {issue.created_at or 'Not set'}")
        print(f"  Created by: {issue.created_by or 'Not set'}")
        
        if issue.assigned_to:
            print(f"  Assigned to: {issue.assigned_to}")
        else:
            print("  Assigned to: Not assigned")
        
        if issue.due_date:
            print(f"  Due date: {issue.due_date}")
        
        if issue.description:
            # Truncate description if it's too long
            desc = issue.description
            if len(desc) > 100:
                desc = desc[:97] + "..."
            print(f"  Description: {desc}")
        
        if issue.comment_count is not None:
            print(f"  Comments: {issue.comment_count}")
        
        if issue.attachment_count is not None:
            print(f"  Attachments: {issue.attachment_count}")
        
        print()


def get_access_token() -> Optional[str]:
    """Get access token from active sessions."""
    active_sessions = load_sessions()
    
    if not active_sessions:
        print("No active sessions found. Please visit http://127.0.0.1:8000/login to authenticate.")
        return None
    
    # Get the most recent session
    latest_session_id = None
    latest_created_at = 0
    
    for session_id, session in active_sessions.items():
        if session["created_at"] > latest_created_at:
            latest_created_at = session["created_at"]
            latest_session_id = session_id
    
    if not latest_session_id:
        print("No valid session found.")
        return None
        
    session = active_sessions[latest_session_id]
    
    # Check if session has expired
    if session["expires_at"] < time.time():
        print("Session has expired. Please visit http://127.0.0.1:8000/login to authenticate.")
        return None
    
    # Check if we have all required scopes
    token_scopes = session.get("scope", "").split()
    missing_scopes = [scope for scope in REQUIRED_SCOPES if scope not in token_scopes]
    
    if missing_scopes:
        print(f"Warning: Missing required scopes: {', '.join(missing_scopes)}")
        print("Please visit http://127.0.0.1:8000/login to authenticate with all required scopes.")
        return None
    
    return session.get("access_token")

def verify_project(access_token: str, project_id: str) -> bool:
    """Verify that the project exists and is accessible."""
    # Normalize project ID
    project_id = normalize_project_id(project_id)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Try direct project endpoints first
    direct_endpoints = [
        f"https://developer.api.autodesk.com/bim360/admin/v1/projects/{project_id}",
        f"https://developer.api.autodesk.com/construction/admin/v1/projects/{project_id}",
        f"https://developer.api.autodesk.com/construction/issues/v1/projects/{project_id}"
    ]
    
    with httpx.Client() as client:
        # Try direct project endpoints first
        for endpoint in direct_endpoints:
            try:
                print(f"Checking project endpoint: {endpoint}")
                response = client.get(endpoint, headers=headers)
                if response.status_code == 200:
                    print(f"\nProject found at {endpoint}")
                    return True
                elif response.status_code == 404:
                    print(f"Project not found at {endpoint}")
                elif response.status_code == 403:
                    print(f"Access denied at {endpoint}")
                else:
                    print(f"Error with {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"Error checking {endpoint}: {str(e)}")
        
        # If direct endpoints fail, try listing hubs
        try:
            hubs_url = "https://developer.api.autodesk.com/project/v1/hubs"
            response = client.get(hubs_url, headers=headers)
            if response.status_code == 200:
                hubs_data = response.json()
                print("\nAvailable hubs:")
                for hub in hubs_data.get("data", []):
                    print(f"- {hub.get('attributes', {}).get('name', 'Unknown')} (ID: {hub.get('id', 'Unknown')})")
                    
                    # Try to get projects for this hub
                    projects_url = f"https://developer.api.autodesk.com/project/v1/hubs/{hub['id']}/projects"
                    projects_response = client.get(projects_url, headers=headers)
                    if projects_response.status_code == 200:
                        projects_data = projects_response.json()
                        print("  Projects:")
                        for project in projects_data.get("data", []):
                            project_id_found = project.get("id", "Unknown")
                            project_name = project.get("attributes", {}).get("name", "Unknown")
                            print(f"  - {project_name} (ID: {project_id_found})")
                            if project_id_found == project_id:
                                print(f"\nFound matching project: {project_name}")
                                return True
            else:
                print(f"Error getting hubs: {response.status_code}")
        except Exception as e:
            print(f"Error listing hubs: {str(e)}")
    
    return False

def export_projects(access_token: str) -> None:
    """Export all accessible projects to a JSON file."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    all_projects = []
    
    try:
        # Get hubs from Data Management API
        hubs_url = "https://developer.api.autodesk.com/project/v1/hubs"
        with httpx.Client() as client:
            print("Fetching hubs...")
            hubs_response = client.get(hubs_url, headers=headers)
            
            if hubs_response.status_code != 200:
                print(f"Error fetching hubs: {hubs_response.status_code} - {hubs_response.text}")
                return
            
            hubs_data = hubs_response.json().get("data", [])
            print(f"Found {len(hubs_data)} hubs")
            
            for hub in hubs_data:
                hub_id = hub.get("id")
                hub_name = hub.get("attributes", {}).get("name", "Unknown Hub")
                print(f"\nProcessing hub: {hub_name}")
                
                # Get projects for this hub
                projects_url = f"https://developer.api.autodesk.com/project/v1/hubs/{hub_id}/projects"
                projects_response = client.get(projects_url, headers=headers)
                
                if projects_response.status_code != 200:
                    print(f"Error fetching projects for hub {hub_name}: {projects_response.status_code}")
                    continue
                
                projects_data = projects_response.json().get("data", [])
                print(f"Found {len(projects_data)} projects in hub {hub_name}")
                
                for project in projects_data:
                    project_id = project.get("id")
                    project_attrs = project.get("attributes", {})
                    
                    # Get detailed project info from BIM360 Admin API
                    admin_url = f"https://developer.api.autodesk.com/bim360/admin/v1/projects/{project_id}"
                    try:
                        admin_response = client.get(admin_url, headers=headers)
                        
                        project_info = {
                            "hub_id": hub_id,
                            "hub_name": hub_name,
                            "project_id": project_id,
                            "project_name": project_attrs.get("name", "Unknown Project"),
                            "project_status": project_attrs.get("status", "unknown"),
                            "project_type": project_attrs.get("type", "unknown"),
                            "created_at": project_attrs.get("createdDate"),
                            "updated_at": project_attrs.get("lastModifiedDate")
                        }
                        
                        if admin_response.status_code == 200:
                            admin_data = admin_response.json()
                            
                            # Skip template projects
                            if admin_data.get("template", {}).get("isTemplate", False):
                                print(f"Skipping template project: {project_info['project_name']}")
                                continue
                            
                            # Add additional metadata from admin API
                            project_info.update({
                                "project_status": admin_data.get("status", project_info["project_status"]),
                                "project_type": admin_data.get("type", project_info["project_type"]),
                                "project_number": admin_data.get("projectNumber"),
                                "job_number": admin_data.get("jobNumber"),
                                "start_date": admin_data.get("startDate"),
                                "end_date": admin_data.get("endDate"),
                                "timezone": admin_data.get("timezone"),
                                "language": admin_data.get("language"),
                                "construction_type": admin_data.get("constructionType"),
                                "contract_type": admin_data.get("contractType"),
                                "value": admin_data.get("value"),
                                "currency": admin_data.get("currency"),
                                "address": admin_data.get("address", {})
                            })
                        
                        all_projects.append(project_info)
                        print(f"- {project_info['project_name']} (ID: {project_info['project_id']})")
                        
                    except Exception as e:
                        print(f"Error getting admin data for project {project_id}: {str(e)}")
                        continue
        
        # Export to JSON file
        output_file = "autodesk_projects.json"
        with open(output_file, "w") as f:
            json.dump({"projects": all_projects}, f, indent=2)
        print(f"\nExported {len(all_projects)} projects to {output_file}")
        
    except Exception as e:
        print(f"Error exporting projects: {str(e)}")

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="List issues from Autodesk Construction Cloud")
    parser.add_argument("--project-id", required=True, help="Project ID to list issues from")
    parser.add_argument("--export-projects", action="store_true", help="Export all accessible projects to JSON")
    args = parser.parse_args()
    
    try:
        # Get access token
        access_token = get_access_token()
        if not access_token:
            print("Failed to get access token")
            return
        
        if args.export_projects:
            export_projects(access_token)
            return
        
        print(f"\n=== Autodesk Construction Cloud Issues Lister ===\n")
        print(f"Project ID: {args.project_id}")
        
        # First verify the project exists
        if not verify_project(access_token, args.project_id):
            print("\nPlease check if the project ID is correct and you have access to it.")
            sys.exit(1)
        
        # List issues
        issues = list_issues(access_token, args.project_id)
        
        # Print issues
        print_issues(issues)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()