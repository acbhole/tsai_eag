import json
import logging
from ast import literal_eval

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="assignment8.log",
    format='%(asctime)s - %(process)d - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

async def execute_tool(session, tool, func_name, params):
    logger.info(f"Executing tool: {tool}, with params: {params}")
    arguments = {}
    schema = tool.inputSchema.get('properties', {})
    
    for param_name, info in schema.items():
        logger.info(f"param_name: {param_name}, info: {info}")
        if not params:
            raise ValueError(f"Not enough parameters for {func_name}")
        value = params.pop(0)
        ptype = info.get('type', 'string')
        if ptype == 'integer':
            arguments[param_name] = int(value)
        elif ptype == 'number':
            arguments[param_name] = float(value)
        elif ptype == 'array':
            arguments[param_name] = [int(v.strip()) for v in value.strip('[]').split(',')]
        else:
            arguments[param_name] = str(value)

    logger.info(f"Sending arguement: {arguments}")
    result = await session.call_tool(func_name, arguments=arguments)
    logger.info(result)
    
    try:
        return arguments, literal_eval(json.loads(json.dumps(result.content[0].text)))
    except Exception:
        return arguments, result.content[0].text