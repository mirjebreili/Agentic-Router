import logging
from typing import Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from agentic_router.config import AGENTS_CONFIG

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the language model
# Make sure OPENAI_API_KEY is set in your environment
try:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
except ImportError:
    logger.error("OpenAI dependencies not found. Please install with `pip install langchain-openai`.")
    llm = None
except Exception as e:
    logger.error(f"Failed to initialize ChatOpenAI: {e}. Ensure OPENAI_API_KEY is set.")
    llm = None

def create_classification_prompt() -> PromptTemplate:
    """Creates a prompt template for agent classification."""

    agent_descriptions = "\n".join(
        f"- **{key}**: {details['name']} ({details['description']})"
        for key, details in AGENTS_CONFIG.items()
    )

    template = f"""
You are an expert at routing user requests to the correct specialized agent.
Based on the user's request, identify the most suitable agent from the following options.

**Available Agents:**
{agent_descriptions}

**User Request:**
"{{input_text}}"

**Instruction:**
Respond with only the agent's key (e.g., "gitlab", "jira"). Do not provide any other text or explanation.
Your response should be a single word from the available agent keys.
"""
    return PromptTemplate.from_template(template)

async def classify(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifies the user input and determines the appropriate agent.

    Args:
        state: The current state of the graph, containing `input_text`.

    Returns:
        A dictionary with the `agent_key` to be merged into the state.
    """
    if not llm:
        raise RuntimeError("ChatOpenAI is not initialized. Cannot proceed with classification.")

    input_text = state.get("input_text")
    if not input_text:
        raise ValueError("`input_text` not found in state. Cannot classify request.")

    logger.info(f"Classifying input: '{input_text}'")

    prompt = create_classification_prompt()
    chain = prompt | llm | StrOutputParser()

    agent_key = await chain.ainvoke({"input_text": input_text})
    agent_key = agent_key.strip().lower()

    if agent_key not in AGENTS_CONFIG:
        logger.error(f"LLM returned an invalid agent key: '{agent_key}'. Valid keys are: {list(AGENTS_CONFIG.keys())}")
        raise ValueError(f"Classification failed. Invalid agent key '{agent_key}' returned.")

    logger.info(f"Classified request for agent: '{agent_key}'")

    # Return the updates to be merged into the state
    return {"agent_key": agent_key}