class DecisionMaking:
    def decide_next_action(self, llm_response):
        if "error" in llm_response:
            return {"type": "error", "message": llm_response["error"]}
        
        action = llm_response.get("action", {})
        action_type = action.get("type")
        
        if action_type == "function_call":
            return {
                "type": "tool_call",
                "tool_name": action.get("tool_name"),
                "tool_input": action.get("tool_input")
            }
        elif action_type == "final_answer":
            return {
                "type": "final_answer",
                "answer": action.get("answer")
            }
        else:
            return {"type": "unknown", "message": "Unrecognized action type"}