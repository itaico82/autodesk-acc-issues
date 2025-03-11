# Autodesk Construction Cloud Issues Manager

A Python tool for managing issues in Autodesk Construction Cloud (ACC) projects using the ACC API with OAuth authentication.

## Features

- OAuth 2.0 authentication with Autodesk Construction Cloud
- List issues from ACC projects
- Export project information to JSON
- Support for multiple ACC API endpoints
- Persistent session management
- Comprehensive error handling

## Prerequisites

- Python 3.8+
- Autodesk Construction Cloud account
- Autodesk Forge API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/itaico82/autodesk-acc-issues.git
cd autodesk-acc-issues
```

2. Install dependencies using UV:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. Create a `.env` file with your Autodesk Forge credentials:
```env
AUTODESK_CLIENT_ID=your_client_id
AUTODESK_CLIENT_SECRET=your_client_secret
```

## Usage

### Authentication

1. Start the OAuth server:
```bash
uvicorn oauth_server:app --reload --port 8000
```

2. Authenticate by visiting:
```
http://127.0.0.1:8000/login
```

This will redirect you to Autodesk's login page. After successful authentication, you'll be redirected back to the local server.

### Getting Issues

#### Basic Usage

List all issues for a project:
```bash
python list_issues.py --project-id YOUR_PROJECT_ID
```

The project ID can be found in your ACC project URL or through the `--export-projects` command.

#### Advanced Options

1. Export all accessible projects:
```bash
python list_issues.py --export-projects
```
This will create a JSON file with all projects you have access to.

2. Filter issues by status:
```bash
python list_issues.py --project-id YOUR_PROJECT_ID --status open
```
Available statuses: open, closed, draft

3. Filter issues by date:
```bash
python list_issues.py --project-id YOUR_PROJECT_ID --since 2024-01-01
```

4. Export issues to JSON:
```bash
python list_issues.py --project-id YOUR_PROJECT_ID --output issues.json
```

5. Get detailed issue information:
```bash
python list_issues.py --project-id YOUR_PROJECT_ID --issue-id ISSUE_ID
```

#### Issue Fields

When listing issues, the following information is displayed:
- Display ID
- Title
- Status
- Created date
- Created by
- Assigned to
- Due date (if set)
- Priority
- Root cause (if specified)
- Location
- Number of comments
- Number of attachments

#### Error Handling

Common error scenarios and solutions:

1. "No active session found":
   - Ensure the OAuth server is running
   - Re-authenticate at http://127.0.0.1:8000/login

2. "Project not found":
   - Verify the project ID
   - Check your permissions for the project
   - Use --export-projects to list accessible projects

3. "Token expired":
   - Re-authenticate through the OAuth server

## Project Structure

```
autodesk-acc-issues/
├── list_issues.py      # Main script for listing issues
├── oauth_server.py     # OAuth authentication server
├── requirements.txt    # Project dependencies
├── sessions.json      # Session storage
└── .env              # Environment variables (not tracked)
```

## API Endpoints

The tool supports multiple ACC API endpoints:
- Construction Issues API
- Quality Issues API
- BIM360 Issues API
- Field Issues API
- ACC Issues API

## Error Handling

The tool includes comprehensive error handling for:
- Authentication failures
- Invalid project IDs
- API rate limits
- Network issues
- Permission issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details