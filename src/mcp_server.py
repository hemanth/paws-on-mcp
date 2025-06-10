from mcp.server.fastmcp import FastMCP
import httpx
import random
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json

# Create a FastMCP server instance with latest capabilities
mcp = FastMCP("Unified MCP Server")

# MCP Protocol Version - Updated to latest spec
MCP_PROTOCOL_VERSION = "2025-03-26"

# --- MCP 2025-03-26 Direct Method Handlers ---
# Note: These functions provide server information but are not exposed as tools
# since they represent server capabilities rather than user-callable functions

@mcp.tool()
def get_server_prompts() -> List[Dict[str, Any]]:
    """List all available prompt templates."""
    return [
        {
            "name": "analyze_tech_trends",
            "description": "Generate a prompt for analyzing technology trends in a specific area",
            "arguments": [
                {"name": "technology_area", "description": "Technology area to analyze (e.g., AI, blockchain)", "required": True},
                {"name": "time_period", "description": "Time period for analysis (day, week, month, year)", "required": False},
                {"name": "detail_level", "description": "Level of detail (brief, standard, comprehensive)", "required": False}
            ]
        },
        {
            "name": "project_research", 
            "description": "Generate a prompt for researching project development approaches",
            "arguments": [
                {"name": "project_type", "description": "Type of project (e.g., web application, mobile app)", "required": True},
                {"name": "tech_stack", "description": "Technology stack preference", "required": False},
                {"name": "focus_area", "description": "Area of focus (e.g., best practices, performance)", "required": False}
            ]
        },
        {
            "name": "competitive_analysis",
            "description": "Generate a prompt for competitive analysis in a specific domain", 
            "arguments": [
                {"name": "domain", "description": "Domain to analyze (e.g., software tools, AI frameworks)", "required": True},
                {"name": "timeframe", "description": "Time scope (recent, trending, established)", "required": False},
                {"name": "analysis_depth", "description": "Level of analysis (overview, detailed, comprehensive)", "required": False}
            ]
        },
        {
            "name": "learning_roadmap",
            "description": "Generate a prompt for creating a learning roadmap",
            "arguments": [
                {"name": "skill_area", "description": "Skill or technology area to learn", "required": True},
                {"name": "experience_level", "description": "Current experience level (beginner, intermediate, advanced)", "required": False},
                {"name": "learning_style", "description": "Preferred learning approach (practical, theoretical, project-based)", "required": False}
            ]
        },
        {
            "name": "code_review_assistant",
            "description": "Generate a prompt for code review assistance",
            "arguments": [
                {"name": "language", "description": "Programming language", "required": False},
                {"name": "review_focus", "description": "Focus area (security, performance, maintainability, general)", "required": False},
                {"name": "project_context", "description": "Type of project (open source, enterprise, startup)", "required": False}
            ]
        }
    ]

# --- Roots Support ---
@mcp.resource("roots://")
def list_roots():
    """List available resource roots for discovery."""
    return {
        "contents": [
            {
                "uri": "roots://",
                "mimeType": "application/json", 
                "text": """
{
  "description": "Available resource categories",
  "roots": [
    "hackernews://",
    "github://",
    "sampling://",
    "status://"
  ],
  "usage": "Use these URIs to explore different data sources"
}
"""
            }
        ]
    }

# Add sampling resource for server capabilities
@mcp.resource("sampling://{sampling_type}/{num_samples}")
def get_sampling_data(sampling_type: str, num_samples: str):
    """Provide server-side sampling with different strategies."""
    
    try:
        n = int(num_samples)
        if n <= 0 or n > 1000:
            raise ValueError("Number of samples must be between 1 and 1000")
    except ValueError as e:
        return {"error": f"Invalid num_samples: {str(e)}"}
        
    if sampling_type == "random":
        # Generate random data points
        samples = [
            {
                "id": i + 1,
                "value": random.uniform(0, 100),
                "category": random.choice(["A", "B", "C", "D"]),
                "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 24*7))).isoformat()
            } for i in range(n)
        ]
        
    elif sampling_type == "sequential":
        # Generate sequential data
        samples = [
            {
                "id": i + 1,
                "value": i * 2.5,
                "status": "active" if i % 2 == 0 else "inactive",
                "timestamp": datetime.now().isoformat()
            } for i in range(n)
        ]
        
    elif sampling_type == "distribution":
        # Generate samples from normal distribution
        samples = [
            {
                "id": i + 1,
                "measurement": random.gauss(50, 15),
                "quality": "high" if random.gauss(50, 15) > 50 else "low",
                "timestamp": datetime.now().isoformat()
            } for i in range(n)
        ]
        
    else:
        return {"error": f"Unknown sampling type: {sampling_type}. Available types: random, sequential, distribution"}
        
    return {
        "sampling_type": sampling_type,
        "requested_samples": n,
        "actual_samples": len(samples),
        "generated_at": datetime.now().isoformat(),
        "samples": samples
    }

# Add server status resource
@mcp.resource("status://server")
def get_server_status():
    """Get current server status and capabilities."""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "capabilities": {
            "resources": True,
            "tools": True,
            "prompts": True,
            "roots": True
        },
        "endpoints": {
            "hackernews": ["top", "search"],
            "github": ["trending", "repo_info"],
            "sampling": ["random", "sequential", "distribution", "repositories", "hackernews"]
        }
    }

# Add resource discovery endpoint
@mcp.resource("status://resources")
def list_available_resources():
    """List all available resources in the server."""
    return {
        "available_resources": [
            "roots://",
            "hackernews://top/{limit}",
            "github://trending/{language}/{since}",
            "sampling://{sampling_type}/{num_samples}",
            "sampling://repositories/{language}/{count}",
            "sampling://hackernews/{count}",
            "status://server",
            "status://resources"
        ],
        "description": "Use these URIs to access different data sources",
        "timestamp": datetime.now().isoformat()
    }

# Initialize HTTP client for API requests
http_client = httpx.Client(timeout=10.0)

# --- Static Resource Registrations for Discovery ---
# These ensure resources appear in list_resources()

@mcp.resource("hackernews://top/10")
def get_hn_top_10() -> List[Dict[str, Any]]:
    """Get top 10 stories from HackerNews."""
    return get_hn_top_stories(10)

@mcp.resource("hackernews://top/5")  
def get_hn_top_5() -> List[Dict[str, Any]]:
    """Get top 5 stories from HackerNews."""
    return get_hn_top_stories(5)

@mcp.resource("github://trending/python/daily")
def get_github_python_daily() -> List[Dict[str, Any]]:
    """Get trending Python repositories (daily)."""
    return get_github_trending("python", "daily")

@mcp.resource("github://trending/javascript/weekly")
def get_github_js_weekly() -> List[Dict[str, Any]]:
    """Get trending JavaScript repositories (weekly)."""
    return get_github_trending("javascript", "weekly")

# --- Server Sampling Resources ---

@mcp.resource("sampling://repositories/{language}/{count}")
def sample_repositories_resource(language: str = "all", count: int = 3) -> List[Dict[str, Any]]:
    """Server-side sampling of repositories by language.
    
    Args:
        language: Programming language to filter by or 'all' for all languages
        count: Number of repositories to sample (default: 3, max: 10)
        
    Returns:
        List of randomly sampled repositories
    """
    # Limit the count
    count = min(max(1, int(count)), 10)
    
    try:
        # Build search query
        query_parts = ["sort:stars"]
        if language and language != "all":
            query_parts.append(f"language:{language}")
        
        query = " ".join(query_parts)
        
        # Get more repositories than needed for sampling
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=50"
        
        response = http_client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Randomly sample from the results
        repositories = data.get("items", [])
        if len(repositories) > count:
            repositories = random.sample(repositories, count)
        
        # Format the response
        sampled_repos = []
        for repo in repositories:
            sampled_repos.append({
                "name": repo.get("full_name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "stars": repo.get("stargazers_count"),
                "language": repo.get("language"),
                "forks": repo.get("forks_count"),
                "sampled": True  # Indicate this is server-sampled data
            })
        
        return sampled_repos
    except Exception as e:
        return [{"error": f"Failed to sample repositories: {str(e)}"}]

@mcp.resource("sampling://hackernews/{count}")
def sample_hackernews_stories(count: int = 5) -> List[Dict[str, Any]]:
    """Server-side sampling of HackerNews stories.
    
    Args:
        count: Number of stories to sample (default: 5, max: 20)
        
    Returns:
        List of randomly sampled HackerNews stories
    """
    # Limit the count
    count = min(max(1, int(count)), 20)
    
    try:
        # Get the top story IDs
        response = http_client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        response.raise_for_status()
        all_story_ids = response.json()[:100]  # Get top 100 for sampling
        
        # Randomly sample story IDs
        sampled_ids = random.sample(all_story_ids, min(count, len(all_story_ids)))
        
        # Fetch details for each sampled story
        stories = []
        for story_id in sampled_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story_resp = http_client.get(story_url)
            if story_resp.status_code == 200:
                story_data = story_resp.json()
                stories.append({
                    "id": story_data.get("id"),
                    "title": story_data.get("title"),
                    "url": story_data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                    "score": story_data.get("score"),
                    "by": story_data.get("by"),
                    "time": story_data.get("time"),
                    "descendants": story_data.get("descendants", 0),
                    "sampled": True  # Indicate this is server-sampled data
                })
        
        return stories
    except Exception as e:
        return [{"error": f"Failed to sample HackerNews stories: {str(e)}"}]

# --- HackerNews API Integration ---

@mcp.resource("hackernews://top/{limit}")
def get_hn_top_stories(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top stories from HackerNews.
    
    Args:
        limit: Maximum number of stories to return (default: 10, max: 30)
        
    Returns:
        List of top stories with details
    """
    # Limit the number of stories
    limit = min(max(1, limit), 30)
    
    try:
        # Get the top story IDs
        response = http_client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        response.raise_for_status()
        top_ids = response.json()[:limit]
        
        # Fetch details for each story
        stories = []
        for story_id in top_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story_resp = http_client.get(story_url)
            if story_resp.status_code == 200:
                story_data = story_resp.json()
                stories.append({
                    "id": story_data.get("id"),
                    "title": story_data.get("title"),
                    "url": story_data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                    "score": story_data.get("score"),
                    "by": story_data.get("by"),
                    "time": story_data.get("time"),
                    "descendants": story_data.get("descendants", 0)
                })
        
        return stories
    except Exception as e:
        # Return error in a structured way
        return [{"error": f"Failed to fetch HackerNews stories: {str(e)}"}]

@mcp.tool()
def search_hackernews(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search HackerNews stories by title.
    
    Args:
        query: Search term to look for in story titles
        limit: Maximum number of stories to return (default: 5, max: 20)
        
    Returns:
        List of matching stories
    """
    # Limit the number of results
    limit = min(max(1, limit), 20)
    
    try:
        # Get a larger set of stories to search through
        response = http_client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        response.raise_for_status()
        story_ids = response.json()[:100]  # Get top 100 to search through
        
        # Search for stories matching the query
        matching_stories = []
        for story_id in story_ids:
            if len(matching_stories) >= limit:
                break
                
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story_resp = http_client.get(story_url)
            if story_resp.status_code == 200:
                story_data = story_resp.json()
                title = story_data.get("title", "").lower()
                
                if query.lower() in title:
                    matching_stories.append({
                        "id": story_data.get("id"),
                        "title": story_data.get("title"),
                        "url": story_data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "score": story_data.get("score"),
                        "by": story_data.get("by")
                    })
        
        return matching_stories
    except Exception as e:
        return [{"error": f"Failed to search HackerNews: {str(e)}"}]

# --- GitHub API Integration ---

@mcp.resource("github://trending/{language}/{since}")
def get_github_trending(language: str = "", since: str = "daily") -> List[Dict[str, Any]]:
    """Get trending repositories from GitHub.
    
    Args:
        language: Programming language filter (empty for all languages)
        since: Time range (daily, weekly, monthly)
        
    Returns:
        List of trending repositories
    """
    # Validate parameters
    valid_since = ["daily", "weekly", "monthly"]
    if since not in valid_since:
        since = "daily"
    
    try:
        # GitHub trending API doesn't have an official endpoint, so we'll simulate with the search API
        query_parts = ["sort:stars"]
        
        # Add language filter if specified
        if language and language != "all":
            query_parts.append(f"language:{language}")
        
        # Add time filter based on 'since'
        if since == "daily":
            query_parts.append("created:>=" + get_date_offset(days=1))
        elif since == "weekly":
            query_parts.append("created:>=" + get_date_offset(days=7))
        elif since == "monthly":
            query_parts.append("created:>=" + get_date_offset(days=30))
        
        query = " ".join(query_parts)
        
        # Make the API request with authentication headers if available
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=10"
        
        response = http_client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Format the response
        repositories = []
        for repo in data.get("items", []):
            repositories.append({
                "name": repo.get("full_name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "stars": repo.get("stargazers_count"),
                "language": repo.get("language"),
                "forks": repo.get("forks_count")
            })
        
        return repositories
    except Exception as e:
        return [{"error": f"Failed to fetch GitHub trending repos: {str(e)}"}]

@mcp.tool()
def get_github_repo_info(owner: str, repo: str) -> Dict[str, Any]:
    """Get detailed information about a specific GitHub repository.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        
    Returns:
        Detailed repository information
    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        response = http_client.get(url, headers=headers)
        response.raise_for_status()
        repo_data = response.json()
        
        # Format the response
        return {
            "name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "url": repo_data.get("html_url"),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "issues": repo_data.get("open_issues_count"),
            "language": repo_data.get("language"),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "topics": repo_data.get("topics", [])
        }
    except Exception as e:
        return {"error": f"Failed to fetch repository info: {str(e)}"}

# --- Prompts ---

@mcp.prompt("analyze_tech_trends")
def tech_trends_prompt(
    technology_area: str = "AI",
    time_period: str = "month", 
    detail_level: str = "comprehensive"
) -> str:
    """Generate a prompt for analyzing technology trends.
    
    Args:
        technology_area: The technology area to analyze (e.g., "AI", "blockchain", "web development")
        time_period: Time period for analysis (day, week, month, year)
        detail_level: Level of detail (brief, standard, comprehensive)
        
    Returns:
        A formatted prompt for tech trend analysis
    """
    return f"""
Analyze the current trends in {technology_area} over the past {time_period}.

Please provide a {detail_level} analysis that includes:

1. **Recent Developments**: Key developments, releases, or breakthroughs
2. **Popular Projects**: Trending repositories and tools gaining traction
3. **Community Interest**: What the developer community is focusing on
4. **Market Impact**: How these trends might affect the industry
5. **Future Outlook**: Predictions for where this technology is heading

Use the available tools to:
- Search HackerNews for recent discussions about {technology_area}
- Find trending GitHub repositories related to {technology_area}
- Use server sampling to discover popular repositories in {technology_area}

Focus on providing actionable insights and concrete examples.
"""

@mcp.prompt("project_research")
def project_research_prompt(
    project_type: str = "web application",
    tech_stack: str = "modern",
    focus_area: str = "best practices"
) -> str:
    """Generate a prompt for researching project development approaches.
    
    Args:
        project_type: Type of project (e.g., "web application", "mobile app", "API service")
        tech_stack: Technology stack preference (e.g., "React", "Python", "modern")
        focus_area: Area of focus (e.g., "best practices", "performance", "security")
        
    Returns:
        A formatted prompt for project research
    """
    return f"""
Research the current best approaches for developing a {project_type} using {tech_stack} technologies, with a focus on {focus_area}.

Please provide a comprehensive guide that includes:

1. **Technology Selection**: Recommended tools, frameworks, and libraries
2. **Architecture Patterns**: Best architectural approaches and design patterns
3. **Development Practices**: Coding standards, testing strategies, and workflows
4. **Popular Examples**: Successful projects and repositories to learn from
5. **Community Resources**: Active communities, tutorials, and documentation

Use the available tools to:
- Find trending repositories related to {tech_stack} and {project_type}
- Search HackerNews for discussions about {focus_area} in {project_type}
- Sample popular repositories to identify common patterns and practices

Provide specific examples and actionable recommendations.
"""

@mcp.prompt("competitive_analysis")
def competitive_analysis_prompt(
    domain: str = "software tools",
    timeframe: str = "recent",
    analysis_depth: str = "detailed"
) -> str:
    """Generate a prompt for competitive analysis in a specific domain.
    
    Args:
        domain: The domain to analyze (e.g., "software tools", "AI frameworks", "web frameworks")
        timeframe: Time scope (e.g., "recent", "trending", "established")
        analysis_depth: Level of analysis (e.g., "overview", "detailed", "comprehensive")
        
    Returns:
        A formatted prompt for competitive analysis
    """
    return f"""
Conduct a {analysis_depth} competitive analysis of {timeframe} {domain}.

Please provide an analysis that covers:

1. **Market Leaders**: Identify the top players and their key strengths
2. **Emerging Solutions**: New or trending alternatives gaining traction
3. **Feature Comparison**: Key features, capabilities, and differentiators
4. **Community Adoption**: Developer/user adoption metrics and sentiment
5. **Technology Assessment**: Technical advantages and limitations
6. **Market Positioning**: How different solutions position themselves

Use the available tools to:
- Search for {timeframe} discussions about {domain} on HackerNews
- Find trending repositories in the {domain} space
- Sample popular projects to understand feature sets and approaches
- Gather community sentiment and adoption indicators

Focus on providing objective insights and clear comparisons.
"""

@mcp.prompt("learning_roadmap")
def learning_roadmap_prompt(
    skill_area: str = "programming",
    experience_level: str = "beginner",
    learning_style: str = "practical"
) -> str:
    """Generate a prompt for creating a learning roadmap.
    
    Args:
        skill_area: The skill or technology area to learn (e.g., "Python", "machine learning", "web development")
        experience_level: Current experience level (e.g., "beginner", "intermediate", "advanced")
        learning_style: Preferred learning approach (e.g., "practical", "theoretical", "project-based")
        
    Returns:
        A formatted prompt for learning roadmap creation
    """
    return f"""
Create a {learning_style} learning roadmap for {skill_area} suitable for a {experience_level} learner.

Please develop a structured learning path that includes:

1. **Prerequisites**: Essential background knowledge and skills needed
2. **Learning Phases**: Progressive stages from basics to advanced concepts
3. **Practical Projects**: Hands-on projects to reinforce learning at each stage
4. **Resources**: Best tutorials, documentation, courses, and community resources
5. **Assessment Milestones**: How to measure progress and validate learning
6. **Real-world Applications**: How these skills apply in professional contexts

Use the available tools to:
- Find popular {skill_area} repositories to understand current practices
- Search HackerNews for learning discussions and resource recommendations
- Sample educational repositories and tutorial projects
- Identify trending tools and technologies in the {skill_area} space

Focus on creating a practical, actionable roadmap with specific next steps.
"""

@mcp.prompt("code_review_assistant")
def code_review_prompt(
    language: str = "any",
    review_focus: str = "general",
    project_context: str = "open source"
) -> str:
    """Generate a prompt for code review assistance.
    
    Args:
        language: Programming language (e.g., "Python", "JavaScript", "any")
        review_focus: Focus area (e.g., "security", "performance", "maintainability", "general")
        project_context: Type of project (e.g., "open source", "enterprise", "startup")
        
    Returns:
        A formatted prompt for code review assistance
    """
    return f"""
Assist with reviewing {language} code in a {project_context} context, focusing on {review_focus}.

Please provide a thorough code review that covers:

1. **Code Quality**: Readability, maintainability, and adherence to best practices
2. **{review_focus.title()} Considerations**: Specific focus on {review_focus} aspects
3. **Architecture Review**: Design patterns, structure, and scalability
4. **Performance Analysis**: Efficiency, optimization opportunities, and bottlenecks
5. **Security Assessment**: Potential vulnerabilities and security best practices
6. **Testing Coverage**: Test completeness and quality

Use the available tools to:
- Research current best practices for {language} development
- Find examples of high-quality {language} repositories
- Search for recent discussions about {review_focus} in {language}
- Sample popular projects to understand industry standards

Provide specific, actionable feedback with examples and recommendations.
"""

# --- Utility Functions ---

def get_date_offset(days: int) -> str:
    """Get a date string for X days ago in ISO format."""
    date = datetime.now() - timedelta(days=days)
    return date.strftime("%Y-%m-%d")

# Add sampling capabilities and fix roots implementation
@mcp.tool()
def create_sampling_request(
    prompt: str,
    context_data: Optional[Dict[str, Any]] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    model_hint: Optional[str] = None,
    intelligence_priority: float = 0.8,
    cost_priority: float = 0.3,
    speed_priority: float = 0.5
) -> Dict[str, Any]:
    """Create a sampling request according to MCP 2025-03-26 specification.
    
    This tool demonstrates proper MCP sampling by creating requests that clients
    can process to get LLM completions with server context and enhanced model preferences.
    
    Args:
        prompt: The prompt to send to the LLM
        context_data: Optional context data to include
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 to 1.0)
        model_hint: Optional model name hint (e.g., "claude-3-sonnet", "gpt-4")
        intelligence_priority: How much to prioritize intelligence (0.0-1.0)
        cost_priority: How much to prioritize cost efficiency (0.0-1.0)
        speed_priority: How much to prioritize response speed (0.0-1.0)
        
    Returns:
        Properly formatted MCP sampling request per 2025-03-26 spec
    """
    try:
        # Validate priority parameters
        for priority, name in [(intelligence_priority, "intelligence"), (cost_priority, "cost"), (speed_priority, "speed")]:
            if not 0.0 <= priority <= 1.0:
                return {"error": f"{name}_priority must be between 0.0 and 1.0"}
        
        # Build enhanced messages with proper content structure
        content = {
            "type": "text",
            "text": prompt
        }
        
        # Add context data if provided
        if context_data:
            context_text = f"\n\nContext data: {json.dumps(context_data, indent=2)}"
            content["text"] += context_text
            # Add annotations for context
            content["annotations"] = {
                "audience": ["human", "assistant"],
                "priority": 0.8
            }
        
        messages = [
            {
                "role": "user", 
                "content": content
            }
        ]
        
        # Build model preferences according to 2025-03-26 spec
        model_preferences = {
            "intelligencePriority": intelligence_priority,
            "costPriority": cost_priority,
            "speedPriority": speed_priority
        }
        
        # Add model hints if provided
        if model_hint:
            model_preferences["hints"] = [{"name": model_hint}]
        
        # Create sampling request per latest spec
        sampling_request = {
            "method": "sampling/createMessage",
            "params": {
                "messages": messages,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "modelPreferences": model_preferences,
                "includeContext": "thisServer",
                "_meta": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "serverContext": context_data or {}
                }
            }
        }
        
        return {
            "sampling_request": sampling_request,
            "status": "ready_for_client",
            "description": f"MCP {MCP_PROTOCOL_VERSION} sampling request with enhanced model preferences",
            "model_preferences": model_preferences
        }
        
    except Exception as e:
        return {"error": f"Failed to create sampling request: {str(e)}"}

@mcp.tool()
def analyze_hackernews_trends_with_ai(
    topic: str = "AI", 
    count: int = 5,
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """Analyze HackerNews trends using AI through sampling.
    
    This tool demonstrates how servers can use sampling to get AI analysis
    of data they collect.
    
    Args:
        topic: Topic to analyze in HackerNews stories
        count: Number of stories to analyze
        analysis_type: Type of analysis (brief, detailed, comprehensive)
        
    Returns:
        AI analysis request with collected data
    """
    try:
        # First collect HackerNews data
        stories = search_hackernews(topic, count)
        if "error" in stories:
            return stories
            
        # Parse the collected stories
        story_content = []
        for content_item in stories.get("content", []):
            if content_item.get("type") == "text":
                try:
                    story_data = json.loads(content_item["text"])
                    story_content.append(story_data)
                except json.JSONDecodeError:
                    continue
        
        if not story_content:
            return {"error": "No valid stories found to analyze"}
        
        # Prepare stories summary for AI analysis
        stories_summary = "\n".join([
            f"- {story.get('title', 'No title')} ({story.get('score', 0)} points)"
            for story in story_content[:count]
        ])
        
        # Create sampling request for AI analysis
        messages = [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"""Please analyze these HackerNews stories about {topic}:

{stories_summary}

Provide a {analysis_type} analysis covering:
1. Main themes and trends
2. Community sentiment and engagement
3. Technical developments highlighted
4. Potential impact and implications
5. Key takeaways for the tech community

Focus on providing actionable insights based on the story titles and engagement levels."""
                }
            }
        ]
        
        # Create analysis prompt with context
        analysis_prompt = f"""Please analyze these HackerNews stories about {topic}:

{stories_summary}

Provide a {analysis_type} analysis covering:
1. Main themes and trends
2. Community sentiment and engagement
3. Technical developments highlighted
4. Potential impact and implications
5. Key takeaways for the tech community

Focus on providing actionable insights based on the story titles and engagement levels."""

        return create_sampling_request(
            prompt=analysis_prompt,
            context_data={
                "topic": topic,
                "analysis_type": analysis_type,
                "story_count": len(story_content),
                "stories": story_content[:count],
                "source": "hackernews",
                "timestamp": datetime.now().isoformat()
            },
            temperature=0.3,
            max_tokens=1500,
            model_hint="claude-3-sonnet",
            intelligence_priority=0.9,
            cost_priority=0.2,
            speed_priority=0.4
        )
        
    except Exception as e:
        return {"error": f"Failed to analyze trends: {str(e)}"}

@mcp.tool()
def code_review_with_ai(
    repo_owner: str,
    repo_name: str,
    review_focus: str = "general"
) -> Dict[str, Any]:
    """Get AI-powered code review insights for a GitHub repository.
    
    Demonstrates using sampling to get AI analysis of repository data.
    
    Args:
        repo_owner: GitHub repository owner
        repo_name: Repository name
        review_focus: Focus area (security, performance, architecture, general)
        
    Returns:
        AI code review request with repository context
    """
    try:
        # Get repository information
        repo_info = get_github_repo_info(repo_owner, repo_name)
        if "error" in repo_info:
            return repo_info
            
        # Parse repository data
        repo_data = None
        for content_item in repo_info.get("content", []):
            if content_item.get("type") == "text":
                try:
                    repo_data = json.loads(content_item["text"])
                    break
                except json.JSONDecodeError:
                    continue
        
        if not repo_data or "error" in repo_data:
            return {"error": "Could not retrieve repository information"}
        
        # Prepare repository context
        repo_context = f"""Repository: {repo_data.get('name')}
Description: {repo_data.get('description', 'No description')}
Language: {repo_data.get('language', 'Unknown')}
Stars: {repo_data.get('stars', 0)}
Forks: {repo_data.get('forks', 0)}
Last updated: {repo_data.get('updated_at', 'Unknown')}
Topics: {', '.join(repo_data.get('topics', []))}"""
        
        # Create analysis request
        messages = [
            {
                "role": "user", 
                "content": {
                    "type": "text",
                    "text": f"""Please provide a {review_focus} code review analysis for this GitHub repository:

{repo_context}

Based on the repository metadata, provide insights on:
1. Code quality indicators (based on stars, activity, community engagement)
2. Architectural considerations (based on language and project type)
3. {review_focus.title()} specific analysis
4. Recommendations for improvement
5. Community adoption and maintenance indicators

Focus on actionable insights that can help developers understand the project's strengths and areas for improvement."""
                }
            }
        ]
        
        # Create code review prompt with context
        review_prompt = f"""Please provide a {review_focus} code review analysis for this GitHub repository:

{repo_context}

Based on the repository metadata, provide insights on:
1. Code quality indicators (based on stars, activity, community engagement)
2. Architectural considerations (based on language and project type)
3. {review_focus.title()} specific analysis
4. Recommendations for improvement
5. Community adoption and maintenance indicators

Focus on actionable insights that can help developers understand the project's strengths and areas for improvement."""

        return create_sampling_request(
            prompt=review_prompt,
            context_data={
                "repository": f"{repo_owner}/{repo_name}",
                "review_focus": review_focus,
                "repo_metadata": repo_data,
                "source": "github",
                "timestamp": datetime.now().isoformat()
            },
            temperature=0.4,
            max_tokens=1200,
            model_hint="claude-3-sonnet",
            intelligence_priority=0.95,
            cost_priority=0.1,
            speed_priority=0.3
        )
        
    except Exception as e:
        return {"error": f"Failed to prepare code review: {str(e)}"}

# Enhanced resource endpoints
@mcp.resource("analysis://hackernews/{topic}/{count}")
def analyze_hackernews_resource(topic: str = "technology", count: int = 10):
    """Provide AI analysis of HackerNews trends as a resource."""
    try:
        # Get the analysis request
        analysis_request = analyze_hackernews_trends_with_ai(topic, int(count), "comprehensive")
        
        return {
            "analysis_topic": topic,
            "story_count": count,
            "analysis_request": analysis_request,
            "instructions": "Send the sampling request to your LLM client for analysis",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to create analysis resource: {str(e)}"}

@mcp.resource("analysis://github/{owner}/{repo}")
def analyze_github_resource(owner: str, repo: str):
    """Provide AI analysis of GitHub repository as a resource."""
    try:
        analysis_request = code_review_with_ai(owner, repo, "comprehensive")
        
        return {
            "repository": f"{owner}/{repo}",
            "analysis_request": analysis_request,
            "instructions": "Send the sampling request to your LLM client for code review analysis",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to create GitHub analysis resource: {str(e)}"}

# Enhanced sampling resources with AI integration
@mcp.resource("sampling://ai-analysis/{data_type}/{params}")
def ai_analysis_sampling(data_type: str, params: str):
    """Server-side sampling with AI analysis capabilities.
    
    Args:
        data_type: Type of data to analyze (hackernews, github, trends)
        params: Parameters in format param1:value1,param2:value2
    """
    try:
        # Parse parameters
        param_dict = {}
        if params:
            for param in params.split(','):
                if ':' in param:
                    key, value = param.split(':', 1)
                    param_dict[key.strip()] = value.strip()
        
        if data_type == "hackernews":
            topic = param_dict.get("topic", "AI")
            count = int(param_dict.get("count", "5"))
            return analyze_hackernews_trends_with_ai(topic, count)
            
        elif data_type == "github":
            owner = param_dict.get("owner", "microsoft")
            repo = param_dict.get("repo", "vscode")
            return code_review_with_ai(owner, repo)
            
        elif data_type == "trends":
            # Multi-source trend analysis
            hn_data = search_hackernews(param_dict.get("query", "AI"), 3)
            gh_data = sample_repositories_resource(param_dict.get("language", "python"), 3)
            
            # Combine data for comprehensive analysis
            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text", 
                        "text": f"""Analyze current technology trends based on this data:

HackerNews Stories: {json.dumps(hn_data, indent=2)}

GitHub Repositories: {json.dumps(gh_data, indent=2)}

Provide insights on:
1. Emerging technology trends
2. Developer community interests
3. Market momentum and adoption
4. Future implications
5. Recommended actions for developers"""
                    }
                }
            ]
            
            # Create comprehensive analysis prompt
            analysis_prompt = f"""Analyze current technology trends based on this data:

HackerNews Stories: {json.dumps(hn_data, indent=2)}

GitHub Repositories: {json.dumps(gh_data, indent=2)}

Provide insights on:
1. Emerging technology trends
2. Developer community interests
3. Market momentum and adoption
4. Future implications
5. Recommended actions for developers"""

            return create_sampling_request(
                prompt=analysis_prompt,
                context_data={
                    "query": param_dict.get("query", "AI"),
                    "language": param_dict.get("language", "python"),
                    "hackernews_data": hn_data,
                    "github_data": gh_data,
                    "analysis_type": "multi_source_trends",
                    "timestamp": datetime.now().isoformat()
                },
                temperature=0.5,
                max_tokens=2000,
                model_hint="claude-3-sonnet",
                intelligence_priority=0.85,
                cost_priority=0.3,
                speed_priority=0.4
            )
        else:
            return {"error": f"Unknown data type: {data_type}. Supported: hackernews, github, trends"}
            
    except Exception as e:
        return {"error": f"Failed to create AI analysis: {str(e)}"}

if __name__ == "__main__":
    try:
        print("🚀 Starting Unified MCP Server on http://127.0.0.1:8000/mcp/")
        print("📋 Available features:")
        print("   • HackerNews integration (resources & tools)")
        print("   • GitHub repository discovery") 
        print("   • Server-side sampling with roots capability")
        print("   • Tech trends analysis prompts")
        print("💡 Use Ctrl+C to stop the server")
        
        # Use FastMCP's built-in run method
        mcp.run("streamable-http")
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        raise