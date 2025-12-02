import os
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from config import GEMINI_API_KEY


class VideoInsights(BaseModel):
    """Structured insights about a YouTube video"""
    main_topic: str = Field(description="The main topic of the video in one sentence")
    key_takeaways: List[str] = Field(description="3-4 key takeaways from the video")
    target_audience: str = Field(description="The target audience for this video")
    content_type: str = Field(description="Type of content: Tutorial, Review, Educational, Entertainment, etc.")
    suggested_questions: List[str] = Field(description="3-5 questions viewers might want to ask about the video")


def generate_structured_insights(transcript: str) -> Dict[str, Any]:
    """
    Generate structured insights using LangChain and Pydantic output parser
    
    Args:
        transcript: Full video transcript text
        
    Returns:
        Dictionary with structured insights
    """
    api_key = os.environ.get('GEMINI_API_KEY') or GEMINI_API_KEY
    if not api_key or api_key.strip() == '' or api_key == 'YOUR_ACTUAL_API_KEY_HERE':
        raise Exception('Gemini API key missing; set GEMINI_API_KEY or update config.py')
    
    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=api_key,
        temperature=0.3
    )
    
    # Create output parser
    parser = PydanticOutputParser(pydantic_object=VideoInsights)
    
    # Truncate transcript if too long
    max_chars = 30000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "\n\n[Transcript truncated for processing]"
    
    # Create prompt template
    prompt = PromptTemplate(
        template="""Analyze the following YouTube video transcript and provide structured insights.

{format_instructions}

Transcript:
{transcript}

Provide your analysis in the exact JSON format specified above.""",
        input_variables=["transcript"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Create the chain
    chain = prompt | llm | parser
    
    try:
        # Execute the chain
        result = chain.invoke({"transcript": transcript})
        
        # Convert Pydantic model to dictionary
        return result.dict()
    except Exception as e:
        print(f"Error generating structured insights: {e}")
        # Fallback to basic structure if parsing fails
        return {
            "main_topic": "Unable to analyze video",
            "key_takeaways": ["Error processing transcript"],
            "target_audience": "Unknown",
            "content_type": "Unknown",
            "suggested_questions": ["What is this video about?"]
        }
