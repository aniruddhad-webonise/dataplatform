"""
SQL Explanation Helper for the MCP server.
Handles generation of explanations for SQL queries.
"""

import os
import openai

class SQLExplanationHelper:
    """Helper class for generating SQL explanations."""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    async def generate_explanation(self, sql_query: str, target_audience: str = "business_user") -> str:
        """Generate explanation for a SQL query.
        
        Args:
            sql_query: The SQL query to explain
            target_audience: Target audience for the explanation ("business_user", "developer", "analyst")
        
        Returns:
            str: Human-readable explanation of the SQL query
        """
        try:
            # Customize prompt based on target audience
            if target_audience == "business_user":
                system_prompt = """You are a data analyst explaining SQL queries to business users. 
                Explain what the query does in simple, non-technical terms that a business person would understand.
                Focus on the business value and insights the query provides.
                Use clear, concise language and avoid technical jargon."""
                
            elif target_audience == "developer":
                system_prompt = """You are a senior developer explaining SQL queries to other developers.
                Explain the technical aspects of the query, including:
                - What tables and columns are being used
                - How joins and relationships work
                - Performance considerations
                - Potential optimizations
                Use technical but clear language."""
                
            elif target_audience == "analyst":
                system_prompt = """You are a data analyst explaining SQL queries to other analysts.
                Explain the analytical approach and methodology:
                - What data is being analyzed
                - What insights can be derived
                - Statistical or analytical concepts used
                - Potential follow-up analyses
                Use analytical terminology appropriately."""
                
            else:
                system_prompt = """Explain the following SQL query in clear, understandable terms.
                Describe what the query does and what results it will produce."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"SQL Query: {sql_query}\n\nPlease explain what this query does."}
                ],
                temperature=0.3
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    async def generate_detailed_explanation(self, sql_query: str) -> dict:
        """Generate a detailed explanation with multiple perspectives.
        
        Returns:
            dict: Dictionary containing explanations for different audiences
        """
        try:
            explanations = {}
            
            # Generate explanations for different audiences
            explanations["business_user"] = await self.generate_explanation(sql_query, "business_user")
            explanations["developer"] = await self.generate_explanation(sql_query, "developer")
            explanations["analyst"] = await self.generate_explanation(sql_query, "analyst")
            
            return {
                "sql_query": sql_query,
                "explanations": explanations,
                "status": "generated"
            }
            
        except Exception as e:
            return {
                "sql_query": sql_query,
                "error": str(e),
                "status": "failed"
            } 