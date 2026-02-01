from app.agent.state import AgentState
from app.utils.logger import get_logger
from app.agent.utils.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.prompt.prompt_library import PROMPT_REGISTRY

logger = get_logger(__name__)

class GreetingResponseNode:
    def __init__(self):
        self.chain = (
            ChatPromptTemplate.from_messages([
                ("system", PROMPT_REGISTRY["greeting_prompt"]),
                ("human", "{user_input}")
            ])
            | get_llm()
            | StrOutputParser()
        )

    def __call__(self, state: AgentState) -> AgentState:
        logger.debug("Generating greeting response", state=state)
        try:
            greeting = self.chain.invoke({
                "user_input": state.get("user_input", "")
            })

            state["response_text"] = greeting
            state["expects_user_reply"] = False

        except Exception as e:
            logger.error("Greeting failed", exc_info=e)
            state["response_text"] = (
                "Sorry, I'm having trouble responding right now."
            )
            state["expects_user_reply"] = False

        return state
    
greeting_response = GreetingResponseNode()
    
if __name__ == "__main__":
    # ---- simple standalone test ----
    greeting_node = GreetingResponseNode()
    test_state = {
        "user_input": "Hi there",
        "messages": []
    }

    updated_state = greeting_node.greeting_response(test_state)

    print("\n=== Greeting Node Test ===")
    print("Response text:")
    print(updated_state.get("response_text"))
    print("\nExpects user reply:")
    print(updated_state.get("expects_user_reply"))
