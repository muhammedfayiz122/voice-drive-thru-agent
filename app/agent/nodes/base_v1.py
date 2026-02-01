"""
Base node classes for production-grade LangGraph nodes.

This module provides the foundational patterns for building OOP-based nodes
that are fully compatible with LangGraph's functional expectations.

Usage Pattern:
    1. Inherit from BaseNode (or BaseLLMNode for LLM-based nodes)
    2. Implement __call__(self, state: AgentState) -> AgentState
    3. Export an instance at module level: my_node = MyNode()

Example:
    class GreetingNode(BaseLLMNode):
        def __init__(self):
            super().__init__()
            self.chain = self.build_chain()
        
        def __call__(self, state: AgentState) -> AgentState:
            state["response_text"] = self.chain.invoke(...)
            return state
    
    # Export the callable instance
    greeting_response = GreetingNode()
"""

from abc import ABC, abstractmethod
from typing import Union
from app.agent.state import AgentState
from app.utils.logger import get_logger


class BaseNode(ABC):
    """
    Abstract base class for all LangGraph nodes.
    
    By implementing __call__, instances become callable objects that
    LangGraph can use directly: graph.add_node("name", my_node_instance)
    
    Benefits:
        - Single initialization of expensive resources (LLM chains, etc.)
        - Clean separation of setup (__init__) and execution (__call__)
        - Consistent error handling and logging
        - Testable: can access internals for unit tests
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def __call__(self, state: AgentState) -> AgentState:
        """
        Execute the node logic.
        
        Args:
            state: The current agent state
            
        Returns:
            Updated agent state
        """
        pass
    
    def _safe_get(self, state: AgentState, key: str, default=None):
        """Safely get a value from state with a default."""
        return state.get(key, default)


class BaseLLMNode(BaseNode):
    """
    Base class for nodes that use LLM chains.
    
    Provides common patterns for LLM-based nodes including:
        - Lazy chain initialization
        - Standard error handling
        - Response text management
    """
    
    def __init__(self):
        super().__init__()
        self._chain = None
    
    @property
    def chain(self):
        """Lazy initialization of the LLM chain."""
        if self._chain is None:
            self._chain = self._build_chain()
        return self._chain
    
    def _build_chain(self):
        """
        Build the LLM chain. Override in subclasses.
        
        Returns:
            A LangChain runnable chain
        """
        raise NotImplementedError("Subclasses must implement _build_chain()")
    
    def _handle_error(self, state: AgentState, error: Exception, fallback_message: str) -> AgentState:
        """
        Standard error handling for LLM nodes.
        
        Args:
            state: Current agent state
            error: The exception that occurred
            fallback_message: Message to show the user
            
        Returns:
            Updated state with error information
        """
        self.logger.error(f"Node execution failed: {error}", exc_info=error)
        state["response_text"] = fallback_message
        state["error"] = str(error)
        state["expects_user_reply"] = False
        return state


class BaseRouterNode(BaseNode):
    """
    Base class for routing nodes that return the next node name.
    
    Router nodes are special - they return a string (next node name)
    instead of the state. LangGraph uses these for conditional edges.
    """
    
    @abstractmethod
    def __call__(self, state: AgentState) -> str:
        """
        Determine the next node based on state.
        
        Args:
            state: The current agent state
            
        Returns:
            Name of the next node to execute
        """
        pass
