from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    # The original query from the user
    input: str
    
    # Conversation history
    chat_history: Annotated[List[str], operator.add]
    
    # Internal notes passed between agents
    analysis: str
    plan: str
    dependencies: str
    
    # The current proposed output
    output: str
    
    # Feedback from Evaluators
    evaluation_feedback: str
    
    # Routing decision (e.g., "CHAT", "CODING", "FINISH", "FAIL")
    next_step: str
    
    # Counter for workflow loops (Max 3)
    retry_count: int
    
    # Error tracking for the fallback workflow
    errors: Annotated[List[str], operator.add]
