"""
Search Service for the MCP server.
Provides advanced search and filtering capabilities for resources with enhanced metadata.
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

class SearchService:
    """Advanced search service for resources with enhanced metadata."""
    
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
    
    def search_resources(self, query: str = None, tags: List[str] = None, 
                        any_tags: List[str] = None, category: str = None,
                        resource_type: str = None, created_after: str = None,
                        created_before: str = None, min_access_count: int = 0,
                        limit: int = 50, sort_by: str = "created_at", 
                        sort_order: str = "desc") -> Dict[str, Any]:
        """Search resources using various criteria."""
        try:
            # Get all resources
            all_resources = self.resource_manager.resources
            
            # Apply filters
            filtered_resources = []
            
            for uri, metadata in all_resources.items():
                if self._matches_criteria(metadata, query, tags, any_tags, category,
                                        resource_type, created_after, created_before,
                                        min_access_count):
                    filtered_resources.append({
                        "uri": uri,
                        "metadata": metadata
                    })
            
            # Sort results
            filtered_resources = self._sort_results(filtered_resources, sort_by, sort_order)
            
            # Apply limit
            if limit > 0:
                filtered_resources = filtered_resources[:limit]
            
            # Format results
            results = []
            for item in filtered_resources:
                metadata = item["metadata"]
                results.append({
                    "uri": item["uri"],
                    "name": metadata.get("name", "Unknown"),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", []),
                    "category": metadata.get("category", "general"),
                    "type": metadata.get("type", "unknown"),
                    "created_at": metadata.get("created_at", ""),
                    "access_count": metadata.get("access_count", 0),
                    "last_accessed": metadata.get("last_accessed", ""),
                    "search_score": item.get("search_score", 0)
                })
            
            # Build search criteria summary
            search_criteria = {}
            if query:
                search_criteria["query"] = query
            if tags:
                search_criteria["tags"] = tags
            if any_tags:
                search_criteria["any_tags"] = any_tags
            if category:
                search_criteria["category"] = category
            if resource_type:
                search_criteria["resource_type"] = resource_type
            if created_after:
                search_criteria["created_after"] = created_after
            if created_before:
                search_criteria["created_before"] = created_before
            if min_access_count > 0:
                search_criteria["min_access_count"] = min_access_count
            
            return {
                "results": results,
                "total_count": len(results),
                "search_criteria": search_criteria,
                "status": "completed"
            }
            
        except Exception as e:
            return {
                "results": [],
                "total_count": 0,
                "search_criteria": {},
                "status": "failed",
                "error": str(e)
            }
    
    def _matches_criteria(self, metadata: Dict[str, Any], query: str = None,
                         tags: List[str] = None, any_tags: List[str] = None,
                         category: str = None, resource_type: str = None,
                         created_after: str = None, created_before: str = None,
                         min_access_count: int = 0) -> bool:
        """Check if a resource matches all specified criteria."""
        
        # Text query search
        if query:
            if not self._matches_text_query(metadata, query):
                return False
        
        # Tags filter (ALL tags must match)
        if tags:
            resource_tags = set(metadata.get("tags", []))
            if not all(tag in resource_tags for tag in tags):
                return False
        
        # Any tags filter (ANY tag can match)
        if any_tags:
            resource_tags = set(metadata.get("tags", []))
            if not any(tag in resource_tags for tag in any_tags):
                return False
        
        # Category filter
        if category:
            if metadata.get("category") != category:
                return False
        
        # Resource type filter
        if resource_type:
            if metadata.get("type") != resource_type:
                return False
        
        # Date range filters
        if created_after:
            created_at = metadata.get("created_at", "")
            if created_at and created_at < created_after:
                return False
        
        if created_before:
            created_at = metadata.get("created_at", "")
            if created_at and created_at > created_before:
                return False
        
        # Access count filter
        if min_access_count > 0:
            access_count = metadata.get("access_count", 0)
            if access_count < min_access_count:
                return False
        
        return True
    
    def _matches_text_query(self, metadata: Dict[str, Any], query: str) -> bool:
        """Check if resource matches text query using fuzzy search."""
        query_lower = query.lower()
        
        # Search in name
        name = metadata.get("name", "").lower()
        if self._fuzzy_match(name, query_lower):
            return True
        
        # Search in description
        description = metadata.get("description", "").lower()
        if self._fuzzy_match(description, query_lower):
            return True
        
        # Search in tags
        tags = [tag.lower() for tag in metadata.get("tags", [])]
        for tag in tags:
            if self._fuzzy_match(tag, query_lower):
                return True
        
        # Search in SQL query (for table resources)
        type_metadata = metadata.get("metadata", {})
        sql_query = type_metadata.get("sql_query", "").lower()
        if self._fuzzy_match(sql_query, query_lower):
            return True
        
        # Search in column names (for table resources)
        columns = [col.lower() for col in type_metadata.get("columns", [])]
        for column in columns:
            if self._fuzzy_match(column, query_lower):
                return True
        
        return False
    
    def _fuzzy_match(self, text: str, query: str, threshold: float = 0.6) -> bool:
        """Perform fuzzy string matching."""
        # Exact match
        if query in text:
            return True
        
        # Word-based matching
        query_words = query.split()
        text_words = text.split()
        
        for query_word in query_words:
            if len(query_word) < 3:  # Skip very short words
                continue
            
            # Check if any word in text contains the query word
            for text_word in text_words:
                if query_word in text_word or text_word in query_word:
                    return True
                
                # Fuzzy similarity check
                similarity = SequenceMatcher(None, query_word, text_word).ratio()
                if similarity >= threshold:
                    return True
        
        return False
    
    def _sort_results(self, resources: List[Dict[str, Any]], sort_by: str, sort_order: str) -> List[Dict[str, Any]]:
        """Sort results by specified field and order."""
        reverse = sort_order.lower() == "desc"
        
        def get_sort_key(item):
            metadata = item["metadata"]
            
            if sort_by == "created_at":
                return metadata.get("created_at", "")
            elif sort_by == "name":
                return metadata.get("name", "").lower()
            elif sort_by == "access_count":
                return metadata.get("access_count", 0)
            elif sort_by == "last_accessed":
                last_accessed = metadata.get("last_accessed", "")
                return last_accessed if last_accessed else ""
            else:
                return metadata.get(sort_by, "")
        
        return sorted(resources, key=get_sort_key, reverse=reverse)
    
    def get_popular_resources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed resources."""
        return self.search_resources(
            min_access_count=1,
            sort_by="access_count",
            sort_order="desc",
            limit=limit
        )
    
    def get_recent_resources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently created resources."""
        return self.search_resources(
            sort_by="created_at",
            sort_order="desc",
            limit=limit
        )
    
    def get_resources_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get resources by category."""
        return self.search_resources(
            category=category,
            limit=limit
        )
    
    def get_resources_by_tags(self, tags: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """Get resources that have any of the specified tags."""
        return self.search_resources(
            any_tags=tags,
            limit=limit
        ) 