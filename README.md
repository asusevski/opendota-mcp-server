# OpenDota MCP Server
[![smithery badge](https://smithery.ai/badge/@asusevski/opendota-mcp-server)](https://smithery.ai/server/@asusevski/opendota-mcp-server)

A Model Context Protocol (MCP) server implementation for accessing OpenDota API data. This server enables LLMs and AI assistants to retrieve real-time Dota 2 statistics, match data, player information, and more through a standard interface.

## Features

- Access player profiles, statistics, and match history
- Retrieve detailed match information 
- Look up professional players and teams
- Get hero statistics and rankings
- Search for players by name
- And more!


## Installation

### Installing via Smithery

To install OpenDota API Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@asusevski/opendota-mcp-server):

```bash
npx -y @smithery/cli install @asusevski/opendota-mcp-server --client claude
```

### Manual Installation
```bash
# Clone the repository
git clone https://github.com/asusevski/opendota-mcp-server.git
cd opendota-mcp-server

# Option 1: Automated setup (works with bash, zsh, and other shells)
./scripts/setup_env.sh

# Option 2: Manual installation with uv
uv add pyproject.toml

# For development dependencies
uv pip install -e ".[dev]"
```

## Usage

### Setting up your environment

1. (Optional but recommended) Create an OpenDota API key at https://www.opendota.com/api-keys
2. Set your API key as an environment variable:

```bash
export OPENDOTA_API_KEY=your_api_key_here
```

### Running the server directly

```bash
python -m src.opendota_server.server
```

### Running the server with Claude Desktop

Follow this: https://modelcontextprotocol.io/quickstart/user

If you use WSL, assuming you have cloned the repo and set up the python environment, this is how I wrote the claude_desktop_config.json:

```json
{
  "mcpServers": {
    "opendota": {
      "command": "wsl.exe",
      "args": [
        "--",
        "bash",
        "-c",
        "cd ~/opendota-mcp-server && source .venv/bin/activate && python src/opendota_server/server.py"
      ]
    }
  }
}
```

### Using the example client

```bash
python -m src.client
```

### Specific tools included:
  - get_player_by_id - Retrieve player information by account ID
  - get_player_recent_matches - Get recent matches for a player
  - get_match_data - Get detailed data for a specific match
  - get_player_win_loss - Get win/loss statistics for a player
  - get_player_heroes - Get a player's most played heroes
  - get_hero_stats - Get statistics for heroes
  - search_player - Search for players by name
  - get_pro_players - Get list of professional players
  - get_pro_matches - Get recent professional matches
  - get_player_peers - Get players who have played with a specified player
  - get_heroes - Get list of all Dota 2 heroes
  - get_player_totals - Get player's overall stats totals
  - get_player_rankings - Get player hero rankings
  - get_player_wordcloud - Get most common words used by player in chat
  - get_team_info - Get information about a team
  - get_public_matches - Get recent public matches
  - get_match_heroes - Get heroes played in a specific match

## Security
[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/asusevski-opendota-mcp-server-badge.png)](https://mseep.ai/app/asusevski-opendota-mcp-server)

## License

MIT
