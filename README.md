# Gausium OpenAPI MCP Server

This project implements an MCP (Model Control Protocol) server that acts as a bridge to the Gausium OpenAPI, allowing AI models or other clients to interact with Gausium robots through a standardized interface.

## Features

The server currently supports the following functionalities as MCP tools:

*   **`list_robots`**: Lists robots accessible via the API key. (Based on: [List Robots API](https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/List%20Robots))
*   **`get_robot_status`**: Fetches the detailed status of a specific robot by its serial number. (Based on: [Get Robot Status API](https://developer.gs-robot.com/zh_CN/Robot%20Information%20Service/V1%20Get%20Robot%20Status))
*   **`list_robot_task_reports`**: Retrieves cleaning task reports for a specific robot, with optional time filtering. (Based on: [List Robot Task Reports API](https://developer.gs-robot.com/zh_CN/Robot%20Cleaning%20Data%20Service/V1%20List%20Robot%20Task%20Reports))
*   **`list_robot_maps`**: Lists the maps associated with a specific robot. (Based on: [List Robot Maps API](https://developer.gs-robot.com/zh_CN/Robot%20Map%20Service/V1%20List%20Robot%20Map))

## Project Structure

The project follows a structured layout based on Python best practices:

```
. 
├── .venv/                # Virtual environment directory
├── src/
│   └── gs_openapi/
│       ├── __init__.py
│       ├── api/            # Modules for direct API interactions
│       │   ├── __init__.py
│       │   ├── maps.py
│       │   └── robots.py
│       ├── auth/           # Authentication related modules
│       │   ├── __init__.py
│       │   └── token_manager.py # Handles OAuth token lifecycle
│       ├── config.py       # Configuration (URLs, Env Vars)
│       └── mcp/            # MCP server specific implementations
│           ├── __init__.py
│           └── gausium_mcp.py # GausiumMCP class extending FastMCP
├── .gitignore
├── main.py               # Main application entry point, tool registration, server run
├── README.md             # This file
└── requirements.txt      # Project dependencies
```

*   **`src/gs_openapi/config.py`**: Contains base URLs, API paths, and environment variable names.
*   **`src/gs_openapi/auth/token_manager.py`**: Manages acquiring and refreshing OAuth tokens.
*   **`src/gs_openapi/api/`**: Contains modules (`robots.py`, `maps.py`) with functions that directly call the Gausium OpenAPI endpoints using `httpx`.
*   **`src/gs_openapi/mcp/gausium_mcp.py`**: Defines the `GausiumMCP` class which integrates the API calls and token management.
*   **`main.py`**: Initializes `GausiumMCP`, registers the API functionalities as MCP tools using `@mcp.tool()`, configures basic logging, and starts the server using `mcp.run()`.

## Setup and Running

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Credentials:**
    The application expects Gausium API credentials to be set as environment variables:
    *   `GS_CLIENT_ID`: Your Gausium Application Client ID.
    *   `GS_CLIENT_SECRET`: Your Gausium Application Client Secret.
    *   `GS_OPEN_ACCESS_KEY`: Your Gausium OpenAPI Access Key.

    You can set these directly in your shell:
    ```bash
    export GS_CLIENT_ID="your_client_id"
    export GS_CLIENT_SECRET="your_client_secret"
    export GS_OPEN_ACCESS_KEY="your_access_key"
    ```
    (Alternatively, modify `src/gs_openapi/config.py` for development, but **do not commit credentials**).

5.  **Run the server:**
    ```bash
    python main.py
    ```
    By default, this starts the server using SSE transport on `http://0.0.0.0:8000`. You can modify `main.py` to use `stdio` transport if needed.

## Connecting an MCP Client

Once the server is running, an MCP client (like Cursor or another compatible tool) can connect to it via the appropriate transport (SSE or stdio) to utilize the defined tools.
