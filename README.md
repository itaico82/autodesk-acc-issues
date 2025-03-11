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

1. Start the OAuth server:
```bash
uvicorn oauth_server:app --reload --port 8000
```

2. Authenticate by visiting:
```
http://127.0.0.1:8000/login
```

3. List issues for a project:
```bash
python list_issues.py --project-id YOUR_PROJECT_ID
```

4. Export all accessible projects:
```bash
python list_issues.py --project-id YOUR_PROJECT_ID --export-projects
```

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