import logging
import requests
import json
import re
from urllib.parse import quote
from services.llm_service import LLMService
from config import is_web_search_enabled, get_serpapi_key

logger = logging.getLogger(__name__)

class WebSearchService:
    """Service for web search and information retrieval"""
    
    # Method removed as we're now using the imported is_web_search_enabled function
    
    @staticmethod
    def search_google(query, num_results=3):
        """Search Google for information on a topic"""
        if not is_web_search_enabled():
            logger.info("Web search is disabled")
            return None
            
        # 重試機制設置
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Prepare the query
                search_query = quote(query)
                
                # Using SerpAPI-compatible endpoint
                api_key = get_serpapi_key()
                if not api_key:
                    logger.error("SERPAPI_KEY not configured")
                    return None
                    
                url = f"https://serpapi.com/search.json?q={search_query}&api_key={api_key}&num={num_results}"
                
                # 設置請求超時時間
                response = requests.get(url, timeout=15)
                
                # Check response
                if response.status_code != 200:
                    error_msg = f"Error searching Google: Status {response.status_code}"
                    if response.status_code == 429:
                        error_msg = "Rate limit exceeded for SerpAPI. Try again later."
                    elif response.status_code == 401:
                        error_msg = "Invalid SerpAPI key. Please check your configuration."
                    
                    logger.error(error_msg)
                    
                    # 只有在達到請求限制或暫時性錯誤時重試
                    if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    
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
            
            except requests.exceptions.Timeout:
                logger.warning(f"SerpAPI request timed out (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("All SerpAPI request attempts timed out")
                    return None
            
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request error in web search: {req_err}")
                # 網絡連接錯誤時重試
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
            
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error in search response: {json_err}")
                return None
            
            except Exception as e:
                logger.error(f"Unexpected error in web search: {e}")
                return None
    
    @staticmethod
    def extract_content_from_url(url):
        """Get content from a URL"""
        # 重試機制設置
        max_retries = 2
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml",
                    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
                    "Connection": "keep-alive"
                }
                
                # 設置更短的超時時間以避免阻塞
                response = requests.get(url, headers=headers, timeout=8, 
                                        allow_redirects=True, stream=True)
                
                if response.status_code != 200:
                    logger.error(f"Error fetching URL (attempt {attempt+1}): Status {response.status_code}")
                    
                    # 只有特定狀態碼才重試
                    if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    
                    return None
                
                # 只讀取有限的內容，避免大型頁面
                content = response.text[:30000]  # 只提取前 30KB 的內容
                
                # 簡易的 HTML 內容提取，主要針對文本
                # 移除 script 和 style 標籤及其內容
                content = re.sub(r'<script[^>]*>.*?</script>', ' ', content, flags=re.DOTALL)
                content = re.sub(r'<style[^>]*>.*?</style>', ' ', content, flags=re.DOTALL)
                
                # 移除 HTML 標籤
                content = re.sub(r'<[^>]+>', ' ', content)
                
                # 移除多餘空白
                content = re.sub(r'\s+', ' ', content).strip()
                
                # 限制內容長度
                if len(content) > 1500:
                    content = content[:1500] + "..."
                
                return content
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request to {url} timed out (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
                    
            except requests.exceptions.TooManyRedirects:
                logger.error(f"Too many redirects for URL: {url}")
                return None
                
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request error for URL {url}: {req_err}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error extracting content from {url}: {e}")
                return None
    
    @staticmethod
    def get_search_results_for_query(query):
        """Search the web for information about a query"""
        if not is_web_search_enabled():
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
        if not is_web_search_enabled():
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