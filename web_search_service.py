import logging
import requests
import json
import re
from urllib.parse import quote
from services.llm_service import LLMService
from routes.utils.config_service import ConfigManager

logger = logging.getLogger(__name__)

class WebSearchService:
    """Service for web search and information retrieval"""
    
    @staticmethod
    def is_web_search_enabled():
        """Check if web search is enabled"""
        web_search_enabled = ConfigManager.get("WEB_SEARCH_ENABLED", "False")
        return web_search_enabled.lower() == "true"
    
    @staticmethod
    def search_google(query, num_results=3):
        """Search Google for information on a topic"""
        if not WebSearchService.is_web_search_enabled():
            logger.info("Web search is disabled")
            return None
            
        try:
            # Prepare the query
            search_query = quote(query)
            
            # Using SerpAPI-compatible endpoint
            api_key = ConfigManager.get("SERPAPI_KEY", "")
            if not api_key:
                logger.error("SERPAPI_KEY not configured")
                return None
                
            url = f"https://serpapi.com/search.json?q={search_query}&api_key={api_key}&num={num_results}"
            response = requests.get(url)
            
            # Check response
            if response.status_code != 200:
                logger.error(f"Error searching Google: Status {response.status_code}")
                return None
                
            # Parse results
            data = response.json()
            
            # Extract organic results
            if "organic_results" not in data:
                logger.warning("No organic results found in search response")
                return None
                
            results = []
            for result in data["organic_results"][:num_results]:
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
                
            return results
        
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return None
    
    @staticmethod
    def extract_content_from_url(url):
        """Get content from a URL"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Error fetching URL: Status {response.status_code}")
                return None
                
            # Simple HTML content extraction
            content = response.text
            
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', ' ', content)
            
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Limit content length
            if len(content) > 2000:
                content = content[:2000] + "..."
                
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from URL: {e}")
            return None
    
    @staticmethod
    def get_search_results_for_query(query):
        """Search the web for information about a query"""
        if not WebSearchService.is_web_search_enabled():
            return None
            
        # Search Google
        search_results = WebSearchService.search_google(query)
        if not search_results:
            return None
            
        # Prepare search results summary
        summary = "Search results information:\n\n"
        
        for i, result in enumerate(search_results):
            summary += f"{i+1}. {result['title']}\n"
            summary += f"   URL: {result['link']}\n"
            summary += f"   Summary: {result['snippet']}\n\n"
            
            # Try to get more content from the first result
            if i == 0:
                content = WebSearchService.extract_content_from_url(result['link'])
                if content:
                    summary += f"Extracted content from the top result:\n{content[:500]}...\n\n"
        
        return summary
    
    @staticmethod
    def answer_with_web_search(query):
        """Search the web and generate a response using the search results"""
        if not WebSearchService.is_web_search_enabled():
            return None
            
        # Get search results
        search_results = WebSearchService.get_search_results_for_query(query)
        if not search_results:
            return None
            
        # Generate response using LLM with the search results as context
        return LLMService.generate_response(
            query, 
            rag_context=search_results,
            system_prompt="You are a helpful AI that answers questions based on web search results. " +
                         "Use the provided search results to inform your response, but answer in a natural way. " +
                         "If the search results don't contain relevant information, acknowledge this " +
                         "and provide a general response based on your knowledge."
        )