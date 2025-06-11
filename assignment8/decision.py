from memory import load_state
from prompt_loader import load_prompt


def generate_tool_descriptions(tools):
    descriptions = []
    for i, tool in enumerate(tools):
        try:
            name = getattr(tool, 'name', f'tool_{i}')
            desc = getattr(tool, 'description', 'No description available')
            props = tool.inputSchema.get('properties', {})
            param_details = [f"{p}: {info.get('type', 'unknown')}" for p, info in props.items()]
            params_str = ', '.join(param_details) if param_details else 'no parameters'
            descriptions.append(f"{i+1}. {name}({params_str}) - {desc}")
        except Exception:
            descriptions.append(f"{i+1}. Error processing tool")
    return "\n".join(descriptions)

def build_prompt(tools_desc: str, original_query: str) -> str:
    prefix_prompt = load_prompt('user_prompt.txt')
    print(f"Prefix prompt: {prefix_prompt}")
    main_prompt = load_prompt('system_prompt.txt')
    print(f"Main prompt: {main_prompt}")
    context = f"{prefix_prompt}: {tools_desc} \
                {main_prompt}"
    history = load_state()
    return f"Context: {context} \
             User Query: {original_query} \
             Decision History which has been taken for this task: {history}\
             The response from previous tool is present under 'result' which needs to be used for next itertion. \
             Now what should I do next? "
