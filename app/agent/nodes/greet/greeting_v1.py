from app.agent.state import AgentState
from app.agent.nodes.base import BaseLLMNode
from app.agent.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.agent.prompt.prompt_library import PROMPT_REGISTRY


class GreetingNode(BaseLLMNode):
    """
    Node that generates friendly greeting responses.
    
    Uses an LLM chain to produce natural, contextual greetings
    based on the user's input.
    """
    
    def _build_chain(self):
        """Build the greeting LLM chain (called once, cached)."""
        return (
            ChatPromptTemplate.from_messages([
                ("system", PROMPT_REGISTRY["greeting_prompt"]),
                ("human", "{user_input}")
            ])
            | get_llm()
            | StrOutputParser()
        )
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Generate a greeting response.
        
        Args:
            state: Agent state containing user_input
            
        Returns:
            Updated state with response_text and expects_user_reply
        """
        self.logger.debug("Generating greeting response", state=state)
        
        try:
            greeting = self.chain.invoke({
                "user_input": self._safe_get(state, "user_input", "")
            })
            state["response_text"] = greeting
            state["expects_user_reply"] = True
            
        except Exception as e:
            return self._handle_error(
                state, e, 
                "Sorry, I'm having trouble responding right now."
            )
        
        return state


# ============================================================================
# EXPORT: This is what gets imported by __init__.py and used by the graph
# ============================================================================
greeting_response = GreetingNode()


if __name__ == "__main__":
    # ---- simple standalone test ----
    test_state = {
        "user_input": "Hi there",
        "messages": []
    }

    # Use the exported instance directly (same as graph would use it)
    updated_state = greeting_response(test_state)

    print("\n=== Greeting Node Test ===")
    print("Response text:")
    print(updated_state.get("response_text"))
    print("\nExpects user reply:")
    print(updated_state.get("expects_user_reply"))
