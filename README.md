# MCP-Server - Personal Assistant Backend
![Static Badge](https://img.shields.io/badge/ws25__26__apip__do1__grp04-blue)

## Contributors
- [**Aiham Zaria**](@staizari)
- [**Artur Castilho Lau**](@starcasti)
- [**Auriand Dester Ngouateu Kemma**](@staungoua)
- [**Mohamed Hamada**](@stmohamad)
- [**Omar Ibrahim Arfa**](@stomarfaa)
- [**Simon Pototzki**](@stsipotot)

---

## Project Idea & Objectives
The MCP Server (Model Context Protocol Server) forms the technical foundation for building a personal AI assistant.  
It enables standardized communication between AI systems and external applications through a unified protocol.

**Goal:**  
To develop a modular Python-based server that communicates with an AI agent (e.g., Claude or GPT-5) and aggregates information from multiple data sources.

### Key Features
- Weather Module → Forecasts (e.g., outfit recommendations)  
- Calendar Module → Daily overview & event management  
- Unified access layer for external APIs (e.g., Open-Meteo, Google Calendar)  
- Extensible design for new modules and data sources  

---
## Tech Stack
- **Language:** Python 3.14+
- **Libraries & Frameworks:**
  - Fast MCP (Model Context Protocol implementation)
  - httpx / Requests (API communication)
  - dotenv (Environment variable management)
  - pytest (Testing framework)
- **Development Tools:**
  - uv (Package manager)
  - Ruff (Linter and formatter)
---
## Architecture Overview
![Architecture Preview](/_docs/architecture.png)
---
# Getting Started
While this guide focuses specifically on integrating the server with Claude Desktop, the MCP server is not limited to Claude alone - you can also use it with other AI Agents such as Cline, Continue & Open Interpreter.

### Prerequisites
- Python 3.11 or higher installed
- The MCP Server script available locally
- [Claude Desktop](https://www.claude.com/download) installed (and also registered)

## Adding MCP Server to Claude
1. Open **Claude Desktop**.
2. Open the User Menu (buttom-left) and Navigatie to **Settings** $\rightarrow$ **Developer**
3. Click on **Edit Config** and the file explorer will open the certain directory.
4. Open the file **claude-desktop_config.json** and replace everything the following JSON:

```json
{
  "mcpServers": {
    "personal-assistant": {
      "command": "/path_to/python.exe",
      "args": [
        "-u",
        "/path_to/main.py"
      ]
    }
  }
}
```

You have to change the file paths of course.

Example paths for windows:<br>
`C:\\Users\\USER\\AppData\\Local\\Programs\\Python\\Python314\\python.exe`<br>
`C:\\Users\\USER\\PycharmProjects\\ws25_26_apip_do1_grp04\\main.py`


## Starting the Server
0. After adding the Server you have to **restart** Claude Desktop.
1. Open a new conversation.
2. Ask him something he can answer using the tools provided.
3. Have fun :^)