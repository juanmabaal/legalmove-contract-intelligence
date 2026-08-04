from langgraph.graph import END, START, StateGraph

from src.graph.nodes import (
    build_image_parsing_output_node,
    parse_amendment_contract_node,
    parse_original_contract_node,
)
from src.graph.state import ContractAnalysisState

def build_image_parsing_graph():
    graph = StateGraph(ContractAnalysisState)

    graph.add_node("parse_original_contract", parse_original_contract_node)
    graph.add_node("parse_amendment_contract", parse_amendment_contract_node)
    graph.add_node("build_image_parsing_output", build_image_parsing_output_node)

    graph.add_edge(START, "parse_original_contract")
    graph.add_edge("parse_original_contract", "parse_amendment_contract")
    graph.add_edge("parse_amendment_contract", "build_image_parsing_output")
    graph.add_edge("build_image_parsing_output", END)

    return graph.compile()

def run_image_parsing_graph(
        case_id: str,
        original_image_path: str,
        amendment_image_path: str,
        vision_provider: str | None = None,
) -> dict:
    app = build_image_parsing_graph()

    initial_state: ContractAnalysisState = {
        "case_id" : case_id,
        "original_image_path": original_image_path,
        "amendment_image_path": amendment_image_path,
    }

    if vision_provider:
        initial_state["vision_provider"] = vision_provider

    final_state = app.invoke(initial_state)

    return final_state["final_output"]


