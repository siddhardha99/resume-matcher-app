from typing import Dict, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import StateGraph, END

# Define the state for our LangGraph
class GraphState(TypedDict):
    resume: str
    job_description: str
    skills_analysis: Dict
    experience_analysis: Dict
    keyword_analysis: Dict
    final_recommendations: str

# Create nodes for the graph
def extract_skills(state: GraphState) -> GraphState:
    """Extract skills from both resume and job description"""
    template = """You are an expert in skill identification. Analyze the following resume and job description to identify skills:
    
Resume:
{resume}

Job Description:
{job_description}

Return a JSON with the following structure:
{{
  "skills_in_job_description": ["skill1", "skill2"],
  "skills_in_resume": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "matching_skills": ["skill1", "skill2"]
}}
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Initialize the LLM
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    skills_analysis = chain.invoke({
        "resume": state["resume"],
        "job_description": state["job_description"]
    })
    
    return {"skills_analysis": skills_analysis, **state}

def analyze_experience(state: GraphState) -> GraphState:
    """Analyze experience requirements vs. resume experience"""
    template = """You are an expert in analyzing professional experience. Compare the experience mentioned in the resume with the requirements in the job description:
    
Resume:
{resume}

Job Description:
{job_description}

Return a JSON with the following structure:
{{
  "experience_required": ["req1", "req2"],
  "experience_in_resume": ["exp1", "exp2"],
  "experience_gaps": ["gap1", "gap2"],
  "experience_highlights": ["highlight1", "highlight2"]
}}
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Initialize the LLM
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    experience_analysis = chain.invoke({
        "resume": state["resume"],
        "job_description": state["job_description"]
    })
    
    return {"experience_analysis": experience_analysis, **state}

def extract_keywords(state: GraphState) -> GraphState:
    """Extract important keywords from the job description"""
    template = """You are an expert in keyword optimization for resumes. Analyze this job description and identify key terms that should be included in a resume:
    
Job Description:
{job_description}

Return a JSON with the following structure:
{{
  "essential_keywords": ["keyword1", "keyword2"],
  "technical_terms": ["term1", "term2"],
  "industry_buzzwords": ["buzzword1", "buzzword2"],
  "action_verbs": ["verb1", "verb2"]
}}
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Initialize the LLM
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    keyword_analysis = chain.invoke({
        "job_description": state["job_description"]
    })
    
    return {"keyword_analysis": keyword_analysis, **state}

def generate_recommendations(state: GraphState) -> GraphState:
    """Generate final recommendations based on all analyses with specific replacement examples"""
    template = """You are a professional resume consultant. Based on the detailed analysis, provide specific recommendations for improving the resume to match the job description better.
    
Resume:
{resume}

Job Description:
{job_description}

Skills Analysis:
{skills_analysis}

Experience Analysis:
{experience_analysis}

Keyword Analysis:
{keyword_analysis}

Provide detailed, actionable recommendations organized in these sections. For each recommendation, include BOTH:
1. The original text or section from the resume that should be changed (or indicate where to add new content)
2. The exact replacement text that should be used instead

FORMAT YOUR RESPONSE LIKE THIS:

## Skills to Add or Highlight

ORIGINAL: "Proficient in Excel and data analysis"
REPLACEMENT: "Expert in data analysis using advanced Excel functions including VLOOKUP, pivot tables, and statistical analysis, resulting in 30% more accurate financial forecasts"

ORIGINAL: [Add to Skills Section]
NEW ADDITION: "Project management: Successfully coordinated cross-functional teams to deliver projects on time and under budget"

## Experience to Emphasize or Reframe

ORIGINAL: "Responsible for customer service and handling client inquiries"
REPLACEMENT: "Delivered exceptional customer experiences by resolving complex client inquiries, resulting in 95% client satisfaction rating and 40% increase in repeat business"

## Keywords to Incorporate

ORIGINAL: "Team player with good communication skills"
REPLACEMENT: "Collaborative team leader with excellent verbal and written communication skills, facilitating effective cross-departmental collaboration on high-priority initiatives"

## Structural Changes

ORIGINAL: [Current format with paragraphs]
REPLACEMENT: "Convert to bullet points highlighting key achievements and quantifiable results for each position. Move education section below work experience."

## Additional Improvements

ORIGINAL: "Managed social media accounts"
REPLACEMENT: "Grew company social media presence by 200%, increasing engagement by 45% and generating 60+ qualified leads per month"
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Initialize the LLM
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    chain = prompt | llm | StrOutputParser()
    
    final_recommendations = chain.invoke({
        "resume": state["resume"],
        "job_description": state["job_description"],
        "skills_analysis": str(state["skills_analysis"]),
        "experience_analysis": str(state["experience_analysis"]),
        "keyword_analysis": str(state["keyword_analysis"])
    })
    
    return {"final_recommendations": final_recommendations, **state}

# Create the graph
def create_analysis_graph():
    # Initialize the graph
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("extract_skills", extract_skills)
    graph.add_node("analyze_experience", analyze_experience)
    graph.add_node("extract_keywords", extract_keywords)
    graph.add_node("generate_recommendations", generate_recommendations)
    
    # Define the flow
    graph.add_edge("extract_skills", "analyze_experience")
    graph.add_edge("analyze_experience", "extract_keywords")
    graph.add_edge("extract_keywords", "generate_recommendations")
    graph.add_edge("generate_recommendations", END)
    
    # Set the entry point
    graph.set_entry_point("extract_skills")
    
    return graph.compile()