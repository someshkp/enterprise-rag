import logfire
from app.agents.state import AgentState
from app.config import settings
from langchain_groq import ChatGroq

llm = ChatGroq(api_key=settings.GROQ_API_KEY,model=settings.PRIMARY_MODEL, temperature=0)


def generate_node(state: AgentState):
    """
    Synthesis a response using both
    Documentation context and conversation history
    """
    
    query = state["current_query"]
    
    history_str = ""
    for msg in state["message"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
        
    user_msg = state["message"][-1]["content"] if state["message"] else ""
    
    if query == "CONVERSATIONAL":
        logfire.info("Generating conversational response using memory.")
        prompt = f"""
         You are a friendly and helpful Enterprise AI Assistant.
        Answer the user's latest message using the CONVERSATION HISTORY below.

        CONVERSATION HISTORY:
        {history_str}

        LATEST MESSAGE:
        "{user_msg}" 
        """
        
    else:
        logfire.info("Generating technical RAG response.")
        max_context_chars = 25000
        full_context = ""

        for doc in state["documents"]:
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits.")
                break

        prompt = f"""
        You are a Senior Technical Architect.
        Answer the question using the TECHNICAL CONTEXT provided.

        TECHNICAL CONTEXT:
        {full_context}

        CONVERSATION HISTORY:
        {history_str}

        USER QUESTION:
        "{user_msg}"
        """

    with logfire.span("✍️ LLM Synthesis"):
       try:
           content = llm.invoke(prompt).content
           logfire.info("Response synthesised via LLM.")
           
           return{
               "final_answer": content,
               "status": "Response Generated.",
               "plan": state["plan"],
               "message":[{"role": "assistant", "content": content}]
           }
       except Exception as e:
            logfire.error(f"LLM Synthesis failed: {e}")
            
            return {
                "final_answer": f"Error : {str(e)}",
                "status": "Failed to generate response."
            }