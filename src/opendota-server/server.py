#!/usr/bin/env python3
"""
OpenDota MCP Server

This Model Context Protocol server provides access to OpenDota API data,
allowing AI assistants to retrieve real-time Dota 2 statistics, match data,
player information, and more.

Usage:
    python opendota_mcp.py

Environment Variables:
    OPENDOTA_API_KEY - Your OpenDota API key (optional but recommended to avoid rate limits)
"""

import os
import json
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("OpenDota")

# Constants
OPENDOTA_API_BASE = "https://api.opendota.com/api"
USER_AGENT = "python-opendota-mcp-server"
OPENDOTA_API_KEY = os.getenv("OPENDOTA_API_KEY", "")

# Add API key to requests if available
API_PARAMS = {"api_key": OPENDOTA_API_KEY} if OPENDOTA_API_KEY else {}

# Models for response data
@dataclass
class Player:
    """Player information from OpenDota"""
    account_id: int
    personaname: Optional[str] = None
    name: Optional[str] = None
    steam_id: Optional[str] = None
    avatar: Optional[str] = None
    profile_url: Optional[str] = None
    rank_tier: Optional[int] = None
    mmr_estimate: Optional[int] = None
    country_code: Optional[str] = None
    is_pro: bool = False
    team_name: Optional[str] = None
    team_id: Optional[int] = None

@dataclass
class Match:
    """Match information from OpenDota"""
    match_id: int
    duration: int
    start_time: int
    radiant_win: bool
    radiant_score: Optional[int] = None
    dire_score: Optional[int] = None
    game_mode: Optional[int] = None
    lobby_type: Optional[int] = None
    region: Optional[int] = None
    players: List[Dict] = None

@dataclass
class Hero:
    """Hero information from OpenDota"""
    id: int
    name: str
    localized_name: str
    primary_attr: str
    attack_type: str
    roles: List[str] = None

# Helper Functions
async def make_opendota_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """Make a request to the OpenDota API with proper error handling."""
    url = f"{OPENDOTA_API_BASE}/{endpoint}"
    request_params = API_PARAMS.copy()
    if params:
        request_params.update(params)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params=request_params,
                headers={"User-Agent": USER_AGENT},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutError:
            return {"error": "Request timed out, please try again later"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return {"error": "Rate limit exceeded. Consider using an API key for more requests."}
            if e.response.status_code == 404:
                return {"error": "Not found. The requested resource doesn't exist."}
            if e.response.status_code >= 500:
                return {"error": "OpenDota API server error. Please try again later."}
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

def format_rank_tier(rank_tier: Optional[int]) -> str:
    """Format rank tier into human-readable format."""
    if not rank_tier:
        return "Unknown"
    
    ranks = [
        "Unranked", "Herald", "Guardian", "Crusader", 
        "Archon", "Legend", "Ancient", "Divine", "Immortal"
    ]
    
    tier = rank_tier // 10
    stars = rank_tier % 10
    
    if tier < 1 or tier >= len(ranks):
        return "Unknown"
        
    if tier == 8 and stars == 0:  # Immortal with no stars
        return "Immortal"
        
    return f"{ranks[tier]} {stars}"

def format_duration(seconds: int) -> str:
    """Format seconds into minutes and seconds."""
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"

def format_timestamp(unix_timestamp: int) -> str:
    """Format Unix timestamp to a human-readable date."""
    from datetime import datetime
    dt = datetime.fromtimestamp(unix_timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_player(player_data: Dict) -> Player:
    """Parse API response into a Player object."""
    profile = player_data.get("profile", {})
    
    return Player(
        account_id=player_data.get("account_id"),
        personaname=profile.get("personaname"),
        name=profile.get("name"),
        steam_id=profile.get("steamid"),
        avatar=profile.get("avatarfull"),
        profile_url=profile.get("profileurl"),
        rank_tier=player_data.get("rank_tier"),
        mmr_estimate=player_data.get("mmr_estimate", {}).get("estimate"),
        country_code=profile.get("loccountrycode"),
        is_pro=bool(player_data.get("is_pro", False)),
        team_name=player_data.get("team_name"),
        team_id=player_data.get("team_id")
    )

def format_match_data(match: Dict) -> str:
    """Format match data into a readable string."""
    if not match or "match_id" not in match:
        return "Match data not found."
    
    # Basic match info
    match_id = match.get("match_id", "Unknown")
    duration = match.get("duration", 0)
    duration_formatted = format_duration(duration)
    start_time = format_timestamp(match.get("start_time", 0))
    
    game_mode = match.get("game_mode", "Unknown")
    radiant_win = match.get("radiant_win", False)
    winner = "Radiant" if radiant_win else "Dire"
    
    # Scores
    radiant_score = match.get("radiant_score", 0)
    dire_score = match.get("dire_score", 0)
    
    # Teams
    radiant_team = match.get("radiant_team", {}).get("name", "Radiant")
    dire_team = match.get("dire_team", {}).get("name", "Dire")
    
    # Format players data
    player_data = []
    players = match.get("players", [])
    
    for player in players:
        account_id = player.get("account_id", "Anonymous")
        hero_id = player.get("hero_id", "Unknown")
        hero_name = player.get("hero_name", "Unknown Hero")
        kills = player.get("kills", 0)
        deaths = player.get("deaths", 0)
        assists = player.get("assists", 0)
        gpm = player.get("gold_per_min", 0)
        xpm = player.get("xp_per_min", 0)
        team = "Radiant" if player.get("player_slot", 0) < 128 else "Dire"
        
        player_data.append(
            f"Player ID: {account_id}\n"
            f"- Team: {team}\n"
            f"- Hero: {hero_name} (ID: {hero_id})\n"
            f"- K/D/A: {kills}/{deaths}/{assists}\n"
            f"- GPM/XPM: {gpm}/{xpm}"
        )
    
    formatted_output = (
        f"Match ID: {match_id}\n"
        f"Date: {start_time}\n"
        f"Duration: {duration_formatted}\n"
        f"Game Mode: {game_mode}\n"
        f"Teams: {radiant_team} vs {dire_team}\n"
        f"Score: {radiant_score} - {dire_score}\n"
        f"Winner: {winner}\n\n"
        f"Player Details:\n"
        f"{'-' * 40}\n"
        f"{'\n\n'.join(player_data)}"
    )
    
    return formatted_output

def format_player_data(player: Dict, wl: Dict = None, recent_matches: List = None) -> str:
    """Format player data into a readable string."""
    if not player:
        return "Player data not found."
    
    # Parse the player data
    player_obj = parse_player(player)
    
    # Basic info
    account_id = player_obj.account_id
    name = player_obj.personaname or "Anonymous"
    rank = format_rank_tier(player_obj.rank_tier)
    mmr = player_obj.mmr_estimate or "Unknown"
    
    # Win/Loss record
    wins = wl.get("win", 0) if wl else 0
    losses = wl.get("lose", 0) if wl else 0
    total_games = wins + losses
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    
    # Format recent matches if available
    recent_matches_text = ""
    if recent_matches:
        match_texts = []
        for match in recent_matches[:5]:  # Limit to 5 matches
            hero_id = match.get("hero_id", "Unknown")
            kills = match.get("kills", 0)
            deaths = match.get("deaths", 0)
            assists = match.get("assists", 0)
            win = "Won" if (match.get("radiant_win") == (match.get("player_slot", 0) < 128)) else "Lost"
            match_date = format_timestamp(match.get("start_time", 0))
            
            match_texts.append(
                f"Match ID: {match.get('match_id')}\n"
                f"- Date: {match_date}\n"
                f"- Hero: {hero_id}\n"
                f"- K/D/A: {kills}/{deaths}/{assists}\n"
                f"- Result: {win}"
            )
        
        recent_matches_text = "\n\nRecent Matches:\n" + "\n\n".join(match_texts)
    
    # Professional player info if applicable
    pro_info = ""
    if player_obj.is_pro:
        pro_info = f"\nProfessional Player: Yes\nTeam: {player_obj.team_name or 'Unknown'}"
    
    return (
        f"Player: {name} (ID: {account_id})\n"
        f"Rank: {rank}\n"
        f"Estimated MMR: {mmr}\n"
        f"Win/Loss: {wins}/{losses} ({win_rate:.1f}% win rate){pro_info}{recent_matches_text}"
    )

# Tool Implementation
@mcp.tool()
async def get_player_by_id(account_id: int) -> str:
    """Get a player's information by their account ID.
    
    Args:
        account_id: The player's Steam32 account ID
    
    Returns:
        Player information including rank, matches, and statistics
    """
    player_data = await make_opendota_request(f"players/{account_id}")
    
    if "error" in player_data:
        return f"Error retrieving player data: {player_data['error']}"
    
    # Get win/loss stats
    wl_data = await make_opendota_request(f"players/{account_id}/wl")
    
    # Get recent matches
    recent_matches = await make_opendota_request(f"players/{account_id}/recentMatches")
    
    return format_player_data(player_data, wl_data, recent_matches)

@mcp.tool()
async def get_player_recent_matches(account_id: int, limit: int = 5) -> str:
    """Get recent matches played by a player.

    Args:
        account_id: Steam32 account ID of the player
        limit: Number of matches to retrieve (default: 5)
    
    Returns:
        List of recent matches with details
    """
    if limit > 20:
        limit = 20  # Cap for reasonable response size
        
    recent_matches = await make_opendota_request(f"players/{account_id}/recentMatches")
    
    if "error" in recent_matches:
        return f"Error retrieving recent matches: {recent_matches['error']}"
    
    if not recent_matches or len(recent_matches) == 0:
        return "No recent matches found for this player."
    
    formatted_matches = []
    
    for i, match in enumerate(recent_matches[:limit]):
        hero_id = match.get("hero_id", "Unknown")
        kills = match.get("kills", 0)
        deaths = match.get("deaths", 0)
        assists = match.get("assists", 0)
        win = "Won" if (match.get("radiant_win") == (match.get("player_slot", 0) < 128)) else "Lost"
        gpm = match.get("gold_per_min", 0)
        xpm = match.get("xp_per_min", 0)
        match_date = format_timestamp(match.get("start_time", 0))
        duration = format_duration(match.get("duration", 0))
        
        formatted_matches.append(
            f"Match {i+1}:\n"
            f"- Match ID: {match.get('match_id')}\n"
            f"- Date: {match_date}\n"
            f"- Duration: {duration}\n"
            f"- Hero ID: {hero_id}\n"
            f"- K/D/A: {kills}/{deaths}/{assists}\n"
            f"- GPM/XPM: {gpm}/{xpm}\n"
            f"- Result: {win}"
        )
    
    return f"Recent Matches for Player ID {account_id}:\n\n" + "\n\n".join(formatted_matches)

@mcp.tool()
async def get_match_data(match_id: int) -> str:
    """Get detailed data for a specific match.
    
    Args:
        match_id: ID of the match to retrieve
    
    Returns:
        Detailed match information including players, scores, and stats
    """
    match_data = await make_opendota_request(f"matches/{match_id}")
    
    if "error" in match_data:
        return f"Error retrieving match data: {match_data['error']}"
    
    return format_match_data(match_data)

@mcp.tool()
async def get_player_win_loss(account_id: int) -> str:
    """Get win/loss statistics for a player.
    
    Args:
        account_id: Steam32 account ID of the player
    
    Returns:
        Win/loss record
    """
    wl_data = await make_opendota_request(f"players/{account_id}/wl")
    
    if "error" in wl_data:
        return f"Error retrieving win/loss data: {wl_data['error']}"
    
    wins = wl_data.get("win", 0)
    losses = wl_data.get("lose", 0)
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    return (
        f"Win/Loss Record for Player ID {account_id}:\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
        f"Total Games: {total}\n"
        f"Win Rate: {win_rate:.2f}%"
    )

@mcp.tool()
async def get_player_heroes(account_id: int, limit: int = 5) -> str:
    """Get a player's most played heroes.
    
    Args:
        account_id: Steam32 account ID of the player
        limit: Number of heroes to retrieve (default: 5)
    
    Returns:
        List of most played heroes with stats
    """
    if limit > 20:
        limit = 20  # Cap for reasonable response size
        
    heroes_data = await make_opendota_request(f"players/{account_id}/heroes")
    
    if "error" in heroes_data:
        return f"Error retrieving heroes data: {heroes_data['error']}"
    
    if not heroes_data or len(heroes_data) == 0:
        return "No hero data found for this player."
    
    # Get hero names
    heroes_names = await make_opendota_request("heroes")
    hero_id_to_name = {}
    
    if not isinstance(heroes_names, dict) and not isinstance(heroes_names, list):
        # Use simple dictionary for hero names
        hero_id_to_name = {
            1: "Anti-Mage", 2: "Axe", 3: "Bane", 4: "Bloodseeker", 5: "Crystal Maiden",
            # This is just a small sample, in practice we'd have all heroes
        }
    else:
        # Process the heroes data to create a mapping
        for hero in heroes_names:
            if isinstance(hero, dict) and "id" in hero and "localized_name" in hero:
                hero_id_to_name[hero["id"]] = hero["localized_name"]
    
    # Sort heroes by games played
    sorted_heroes = sorted(heroes_data, key=lambda x: x.get("games", 0), reverse=True)
    
    formatted_heroes = []
    
    for i, hero in enumerate(sorted_heroes[:limit]):
        hero_id = hero.get("hero_id", 0)
        hero_name = hero_id_to_name.get(hero_id, f"Hero {hero_id}")
        games = hero.get("games", 0)
        wins = hero.get("win", 0)
        win_rate = (wins / games * 100) if games > 0 else 0
        
        formatted_heroes.append(
            f"{i+1}. {hero_name} (ID: {hero_id})\n"
            f"   Games: {games}\n"
            f"   Wins: {wins}\n"
            f"   Win Rate: {win_rate:.2f}%"
        )
    
    return f"Most Played Heroes for Player ID {account_id}:\n\n" + "\n\n".join(formatted_heroes)

@mcp.tool()
async def get_hero_stats(hero_id: Optional[int] = None) -> str:
    """Get statistics for heroes.
    
    Args:
        hero_id: Optional hero ID to get stats for a specific hero
    
    Returns:
        Hero statistics including win rates by skill bracket
    """
    hero_stats = await make_opendota_request("heroStats")
    
    if "error" in hero_stats:
        return f"Error retrieving hero stats: {hero_stats['error']}"
    
    if hero_id is not None:
        # Filter for specific hero
        hero_stats = [hero for hero in hero_stats if hero.get("id") == hero_id or hero.get("hero_id") == hero_id]
        
        if not hero_stats:
            return f"No stats found for hero ID {hero_id}."
        
        hero = hero_stats[0]
        localized_name = hero.get("localized_name", f"Hero {hero_id}")
        
        # Calculate win rates by bracket
        brackets = ["herald", "guardian", "crusader", "archon", "legend", "ancient", "divine", "immortal"]
        bracket_stats = []
        
        for i, bracket in enumerate(brackets, 1):
            picks = hero.get(f"{i}_pick", 0)
            wins = hero.get(f"{i}_win", 0)
            win_rate = (wins / picks * 100) if picks > 0 else 0
            bracket_stats.append(f"{bracket.capitalize()}: {win_rate:.2f}% ({wins}/{picks})")
        
        # Pro stats
        pro_picks = hero.get("pro_pick", 0)
        pro_wins = hero.get("pro_win", 0)
        pro_win_rate = (pro_wins / pro_picks * 100) if pro_picks > 0 else 0
        pro_ban_rate = hero.get("pro_ban", 0)
        
        # Hero attributes
        roles = hero.get("roles", [])
        primary_attr = hero.get("primary_attr", "Unknown")
        attack_type = hero.get("attack_type", "Unknown")
        
        return (
            f"Hero Stats for {localized_name} (ID: {hero_id}):\n\n"
            f"Roles: {', '.join(roles)}\n"
            f"Primary Attribute: {primary_attr}\n"
            f"Attack Type: {attack_type}\n\n"
            f"Win Rates by Bracket:\n"
            f"{', '.join(bracket_stats)}\n\n"
            f"Pro Scene:\n"
            f"Pick Rate: {pro_picks} picks\n"
            f"Win Rate: {pro_win_rate:.2f}% ({pro_wins}/{pro_picks})\n"
            f"Ban Rate: {pro_ban_rate} bans"
        )
    else:
        # Return summary of all heroes
        formatted_heroes = []
        
        for hero in sorted(hero_stats, key=lambda x: x.get("localized_name", "")):
            localized_name = hero.get("localized_name", f"Hero {hero.get('id')}")
            
            # Calculate overall win rate
            total_picks = sum(hero.get(f"{i}_pick", 0) for i in range(1, 9))
            total_wins = sum(hero.get(f"{i}_win", 0) for i in range(1, 9))
            win_rate = (total_wins / total_picks * 100) if total_picks > 0 else 0
            
            formatted_heroes.append(f"{localized_name}: {win_rate:.2f}% win rate")
        
        return "Hero Win Rates:\n\n" + "\n".join(formatted_heroes)

@mcp.tool()
async def search_player(query: str) -> str:
    """Search for players by name.
    
    Args:
        query: Name to search for
    
    Returns:
        List of matching players
    """
    search_results = await make_opendota_request("search", {"q": query})
    
    if "error" in search_results:
        return f"Error searching for players: {search_results['error']}"
    
    if not search_results or len(search_results) == 0:
        return f"No players found matching '{query}'."
    
    formatted_results = []
    
    for i, player in enumerate(search_results[:10]):  # Limit to 10 players
        account_id = player.get("account_id", "Unknown")
        name = player.get("personaname", "Anonymous")
        similarity = player.get("similarity", 0)
        
        formatted_results.append(
            f"{i+1}. {name}\n"
            f"   Account ID: {account_id}\n"
            f"   Similarity: {similarity:.2f}"
        )
    
    return f"Players matching '{query}':\n\n" + "\n\n".join(formatted_results)

@mcp.tool()
async def get_pro_players(limit: int = 10) -> str:
    """Get list of professional players.
    
    Args:
        limit: Number of players to retrieve (default: 10)
    
    Returns:
        List of professional players
    """
    if limit > 30:
        limit = 30  # Cap for reasonable response size
        
    pro_players = await make_opendota_request("proPlayers")
    
    if "error" in pro_players:
        return f"Error retrieving pro players: {pro_players['error']}"
    
    if not pro_players or len(pro_players) == 0:
        return "No professional players found."
    
    # Sort by name for consistency
    sorted_players = sorted(
        pro_players, 
        key=lambda x: (x.get("team_name", ""), x.get("name", ""), x.get("account_id", 0))
    )
    
    formatted_players = []
    
    for i, player in enumerate(sorted_players[:limit]):
        account_id = player.get("account_id", "Unknown")
        name = player.get("name", "Anonymous")
        team_name = player.get("team_name", "No Team")
        country_code = player.get("country_code", "Unknown")
        
        formatted_players.append(
            f"{i+1}. {name}\n"
            f"   Team: {team_name}\n"
            f"   Country: {country_code}\n"
            f"   Account ID: {account_id}"
        )
    
    return f"Professional Players:\n\n" + "\n\n".join(formatted_players)

@mcp.tool()
async def get_pro_matches(limit: int = 5) -> str:
    """Get recent professional matches.
    
    Args:
        limit: Number of matches to retrieve (default: 5)
    
    Returns:
        List of recent professional matches
    """
    if limit > 20:
        limit = 20  # Cap for reasonable response size
        
    pro_matches = await make_opendota_request("proMatches")
    
    if "error" in pro_matches:
        return f"Error retrieving pro matches: {pro_matches['error']}"
    
    if not pro_matches or len(pro_matches) == 0:
        return "No professional matches found."
    
    formatted_matches = []
    
    for i, match in enumerate(pro_matches[:limit]):
        match_id = match.get("match_id", "Unknown")
        radiant_name = match.get("radiant_name", "Radiant")
        dire_name = match.get("dire_name", "Dire")
        league_name = match.get("league_name", "Unknown League")
        duration = format_duration(match.get("duration", 0))
        start_time = format_timestamp(match.get("start_time", 0))
        radiant_score = match.get("radiant_score", 0)
        dire_score = match.get("dire_score", 0)
        winner = radiant_name if match.get("radiant_win", False) else dire_name
        
        formatted_matches.append(
            f"{i+1}. {radiant_name} vs {dire_name}\n"
            f"   Match ID: {match_id}\n"
            f"   League: {league_name}\n"
            f"   Date: {start_time}\n"
            f"   Duration: {duration}\n"
            f"   Score: {radiant_score} - {dire_score}\n"
            f"   Winner: {winner}"
        )
    
    return f"Recent Professional Matches:\n\n" + "\n\n".join(formatted_matches)

@mcp.tool()
async def get_player_peers(account_id: int, limit: int = 5) -> str:
    """Get players who have played with the specified player.
    
    Args:
        account_id: Steam32 account ID of the player
        limit: Number of peers to retrieve (default: 5)
    
    Returns:
        List of players frequently played with
    """
    if limit > 20:
        limit = 20  # Cap for reasonable response size
        
    peers_data = await make_opendota_request(f"players/{account_id}/peers")
    
    if "error" in peers_data:
        return f"Error retrieving peers data: {peers_data['error']}"
    
    if not peers_data or len(peers_data) == 0:
        return "No peers found for this player."
    
    # Sort by games played together
    sorted_peers = sorted(peers_data, key=lambda x: x.get("games", 0), reverse=True)
    
    formatted_peers = []
    
    for i, peer in enumerate(sorted_peers[:limit]):
        peer_account_id = peer.get("account_id", "Unknown")
        peer_name = peer.get("personaname", "Anonymous")
        games = peer.get("games", 0)
        wins = peer.get("win", 0)
        win_rate = (wins / games * 100) if games > 0 else 0
        
        formatted_peers.append(
            f"{i+1}. {peer_name} (ID: {peer_account_id})\n"
            f"   Games together: {games}\n"
            f"   Wins: {wins}\n"
            f"   Win Rate: {win_rate:.2f}%"
        )
    
    return f"Peers for Player ID {account_id}:\n\n" + "\n\n".join(formatted_peers)

@mcp.tool()
async def get_heroes() -> str:
    """Get list of all Dota 2 heroes.
    
    Returns:
        List of all heroes with basic information
    """
    heroes_data = await make_opendota_request("heroes")
    
    if "error" in heroes_data:
        return f"Error retrieving heroes data: {heroes_data['error']}"
    
    if not heroes_data or len(heroes_data) == 0:
        return "No heroes data found."
    
    # Sort by hero ID
    sorted_heroes = sorted(heroes_data, key=lambda x: x.get("id", 0))
    
    formatted_heroes = []
    
    for hero in sorted_heroes:
        hero_id = hero.get("id", 0)
        name = hero.get("localized_name", f"Hero {hero_id}")
        primary_attr = hero.get("primary_attr", "Unknown")
        attack_type = hero.get("attack_type", "Unknown")
        roles = ", ".join(hero.get("roles", []))
        
        formatted_heroes.append(
            f"{name} (ID: {hero_id})\n"
            f"Primary Attribute: {primary_attr}\n"
            f"Attack Type: {attack_type}\n"
            f"Roles: {roles}"
        )
    
    return "Dota 2 Heroes:\n\n" + "\n\n".join(formatted_heroes)

@mcp.tool()
async def get_player_totals(account_id: int) -> str:
    """Get player's overall stats totals.
    
    Args:
        account_id: Steam32 account ID of the player
    
    Returns:
        Summary of player's total stats
    """
    totals_data = await make_opendota_request(f"players/{account_id}/totals")
    
    if "error" in totals_data:
        return f"Error retrieving totals data: {totals_data['error']}"
    
    if not totals_data or len(totals_data) == 0:
        return "No totals data found for this player."
    
    # Extract important fields
    formatted_stats = []
    
    for stat in totals_data:
        field = stat.get("field", "")
        count = stat.get("n", 0)
        sum_value = stat.get("sum", 0)
        avg_value = sum_value / count if count > 0 else 0
        
        # Convert field name to something more readable
        readable_field = field.replace('_', ' ').title()
        
        formatted_stats.append(f"{readable_field}: {sum_value:,} total, {avg_value:.2f} avg")
    
    return f"Stat Totals for Player ID {account_id}:\n\n" + "\n".join(formatted_stats)

@mcp.tool()
async def get_player_rankings(account_id: int) -> str:
    """Get player hero rankings.
    
    Args:
        account_id: Steam32 account ID of the player
    
    Returns:
        Player's hero rankings
    """
    rankings_data = await make_opendota_request(f"players/{account_id}/rankings")
    
    if "error" in rankings_data:
        return f"Error retrieving rankings data: {rankings_data['error']}"
    
    if not rankings_data or len(rankings_data) == 0:
        return "No ranking data found for this player."
    
    # Get hero names (just for context)
    heroes_data = await make_opendota_request("heroes")
    hero_id_to_name = {}
    
    if not isinstance(heroes_data, dict) and isinstance(heroes_data, list):
        for hero in heroes_data:
            if isinstance(hero, dict) and "id" in hero and "localized_name" in hero:
                hero_id_to_name[hero["id"]] = hero["localized_name"]
    
    formatted_rankings = []
    
    for ranking in rankings_data:
        hero_id = ranking.get("hero_id", 0)
        hero_name = hero_id_to_name.get(hero_id, f"Hero {hero_id}")
        score = ranking.get("score", 0)
        percent_rank = ranking.get("percent_rank", 0) * 100  # Convert to percentage
        
        formatted_rankings.append(
            f"{hero_name} (ID: {hero_id})\n"
            f"Score: {score:.2f}\n"
            f"Percentile: {percent_rank:.2f}%"
        )
    
    return f"Hero Rankings for Player ID {account_id}:\n\n" + "\n\n".join(formatted_rankings)

@mcp.tool()
async def get_player_wordcloud(account_id: int) -> str:
    """Get most common words used by player in chat.
    
    Args:
        account_id: Steam32 account ID of the player
    
    Returns:
        List of player's most frequently used words
    """
    wordcloud_data = await make_opendota_request(f"players/{account_id}/wordcloud")
    
    if "error" in wordcloud_data:
        return f"Error retrieving wordcloud data: {wordcloud_data['error']}"
    
    my_words = wordcloud_data.get("my_word_counts", {})
    
    if not my_words:
        return "No chat data found for this player."
    
    # Sort words by frequency
    sorted_words = sorted(my_words.items(), key=lambda x: x[1], reverse=True)
    
    # Get top 20 words
    top_words = sorted_words[:20]
    
    formatted_output = []
    for word, count in top_words:
        formatted_output.append(f"{word}: {count} times")
    
    return f"Most Common Words for Player ID {account_id}:\n\n" + "\n".join(formatted_output)

@mcp.tool()
async def get_team_info(team_id: int) -> str:
    """Get information about a team.
    
    Args:
        team_id: Team ID
    
    Returns:
        Team information
    """
    team_data = await make_opendota_request(f"teams/{team_id}")
    
    if "error" in team_data:
        return f"Error retrieving team data: {team_data['error']}"
    
    if not team_data or not isinstance(team_data, dict):
        return f"No data found for team ID {team_id}."
    
    team_name = team_data.get("name", "Unknown")
    team_tag = team_data.get("tag", "")
    rating = team_data.get("rating", 0)
    wins = team_data.get("wins", 0)
    losses = team_data.get("losses", 0)
    total_games = wins + losses
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    last_match_time = format_timestamp(team_data.get("last_match_time", 0))
    
    # Get team players
    players_data = await make_opendota_request(f"teams/{team_id}/players")
    
    formatted_players = []
    if isinstance(players_data, list) and players_data:
        current_players = [p for p in players_data if p.get("is_current_team_member")]
        
        for player in current_players:
            player_name = player.get("name", "Unknown")
            account_id = player.get("account_id", "Unknown")
            games_played = player.get("games_played", 0)
            wins = player.get("wins", 0)
            win_rate = (wins / games_played * 100) if games_played > 0 else 0
            
            formatted_players.append(
                f"{player_name} (ID: {account_id})\n"
                f"Games: {games_played}, Win Rate: {win_rate:.2f}%"
            )
    
    players_section = "\n\nCurrent Players:\n" + "\n".join(formatted_players) if formatted_players else ""
    
    return (
        f"Team: {team_name} [{team_tag}] (ID: {team_id})\n"
        f"Rating: {rating}\n"
        f"Record: {wins}-{losses} ({win_rate:.2f}% win rate)\n"
        f"Last Match: {last_match_time}{players_section}"
    )

@mcp.tool()
async def get_public_matches(limit: int = 5) -> str:
    """Get recent public matches.
    
    Args:
        limit: Number of matches to retrieve (default: 5)
    
    Returns:
        List of recent public matches
    """
    if limit > 20:
        limit = 20  # Cap for reasonable response size
        
    matches_data = await make_opendota_request("publicMatches")
    
    if "error" in matches_data:
        return f"Error retrieving public matches: {matches_data['error']}"
    
    if not matches_data or len(matches_data) == 0:
        return "No public matches found."
    
    formatted_matches = []
    
    for i, match in enumerate(matches_data[:limit]):
        match_id = match.get("match_id", "Unknown")
        duration = format_duration(match.get("duration", 0))
        start_time = format_timestamp(match.get("start_time", 0))
        avg_rank = match.get("avg_rank_tier", 0)
        rank_name = format_rank_tier(avg_rank)
        radiant_win = match.get("radiant_win", False)
        winner = "Radiant" if radiant_win else "Dire"
        
        radiant_heroes = match.get("radiant_team", [])
        dire_heroes = match.get("dire_team", [])
        
        formatted_matches.append(
            f"{i+1}. Match ID: {match_id}\n"
            f"   Date: {start_time}\n"
            f"   Duration: {duration}\n"
            f"   Avg. Rank: {rank_name}\n"
            f"   Winner: {winner}\n"
            f"   Radiant Heroes: {', '.join(str(h) for h in radiant_heroes)}\n"
            f"   Dire Heroes: {', '.join(str(h) for h in dire_heroes)}"
        )
    
    return f"Recent Public Matches:\n\n" + "\n\n".join(formatted_matches)

@mcp.tool()
async def get_match_heroes(match_id: int) -> str:
    """Get heroes played in a specific match.
    
    Args:
        match_id: ID of the match to retrieve
    
    Returns:
        List of heroes played by each player in the match
    """
    match_data = await make_opendota_request(f"matches/{match_id}")
    
    if "error" in match_data:
        return f"Error retrieving match data: {match_data['error']}"
    
    if not match_data or "players" not in match_data:
        return f"No data found for match ID {match_id}."
    
    # Get hero names
    heroes_data = await make_opendota_request("heroes")
    hero_id_to_name = {}
    
    if not isinstance(heroes_data, dict) and isinstance(heroes_data, list):
        for hero in heroes_data:
            if isinstance(hero, dict) and "id" in hero and "localized_name" in hero:
                hero_id_to_name[hero["id"]] = hero["localized_name"]
    
    # Process players
    radiant_players = []
    dire_players = []
    
    for player in match_data["players"]:
        hero_id = player.get("hero_id", 0)
        hero_name = hero_id_to_name.get(hero_id, f"Hero {hero_id}")
        account_id = player.get("account_id", "Anonymous")
        name = player.get("personaname", "Unknown")
        kills = player.get("kills", 0)
        deaths = player.get("deaths", 0)
        assists = player.get("assists", 0)
        
        player_info = f"{name} (ID: {account_id}) - {hero_name}: {kills}/{deaths}/{assists}"
        
        if player.get("player_slot", 0) < 128:
            radiant_players.append(player_info)
        else:
            dire_players.append(player_info)
    
    # Match result
    radiant_win = match_data.get("radiant_win", False)
    result = "Radiant Victory" if radiant_win else "Dire Victory"
    
    return (
        f"Heroes in Match {match_id} ({result}):\n\n"
        f"Radiant:\n" + "\n".join(f"- {p}" for p in radiant_players) + "\n\n"
        f"Dire:\n" + "\n".join(f"- {p}" for p in dire_players)
    )

if __name__ == "__main__":
    mcp.run(transport='stdio')
