from typing import Dict, List, Any

def serialize_pydantic_result(result: Dict[str, List[Any]]) -> Dict[str, List[Dict]]:
    return {
        key: [item.model_dump() for item in value]
        for key, value in result.items()
    }