from typing import TypedDict
from langgraph.graph import StateGraph, END
from llm import GeminiLLM


class SummaryState(TypedDict):
    ai_response: str
    summary: str


def summarize_ai_response(state: SummaryState) -> SummaryState:
    llm = GeminiLLM()

    prompt = f"""
Summarize the following assistant response into a short title
(5 to 10 words maximum).

Assistant Response:
{state['ai_response']}
"""

    summary = llm.generate(prompt)

    return {
        "ai_response": state["ai_response"],
        "summary": summary
    }


def build_summary_graph():
    graph = StateGraph(SummaryState)

    graph.add_node("summarize", summarize_ai_response)
    graph.set_entry_point("summarize")
    graph.add_edge("summarize", END)

    return graph.compile()
