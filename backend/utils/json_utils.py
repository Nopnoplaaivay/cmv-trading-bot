"""
JSON serialization utilities for handling Decimal and other non-serializable objects
"""

import json
from decimal import Decimal
from typing import Any, Dict, List, Union

class JSONUtils:
    @staticmethod
    def convert_decimals_to_float(obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: JSONUtils.convert_decimals_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [JSONUtils.convert_decimals_to_float(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(JSONUtils.convert_decimals_to_float(item) for item in obj)
        else:
            return obj
        
    @staticmethod
    def safe_json_dumps(obj: Any, **kwargs) -> str:
        converted = JSONUtils.convert_decimals_to_float(obj)
        return json.dumps(converted, **kwargs)
    
    @staticmethod
    def make_json_serializable(data: Dict[str, Any]) -> Dict[str, Any]:
        return JSONUtils.convert_decimals_to_float(data)



def find_decimals_in_object(obj: Any, path: str = "root") -> List[str]:
    decimal_paths = []

    if isinstance(obj, Decimal):
        decimal_paths.append(f"{path} = {obj} (Decimal)")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            decimal_paths.extend(find_decimals_in_object(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            decimal_paths.extend(find_decimals_in_object(item, f"{path}[{i}]"))
    elif isinstance(obj, tuple):
        for i, item in enumerate(obj):
            decimal_paths.extend(find_decimals_in_object(item, f"{path}({i})"))

    return decimal_paths


def has_decimals(obj: Any) -> bool:
    return len(find_decimals_in_object(obj)) > 0


def validate_json_serializable(obj: Any, raise_on_error: bool = True) -> bool:
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError) as e:
        if raise_on_error:
            # Find and report specific problematic values
            decimals = find_decimals_in_object(obj)
            if decimals:
                error_msg = f"JSON serialization failed due to Decimal objects:\n"
                error_msg += "\n".join(decimals[:10])  # Show first 10
                if len(decimals) > 10:
                    error_msg += f"\n... and {len(decimals) - 10} more"
                raise TypeError(error_msg) from e
            else:
                raise e
        return False


def debug_json_serialization(obj: Any) -> Dict[str, Any]:
    result = {
        "is_serializable": False,
        "has_decimals": False,
        "decimal_count": 0,
        "decimal_paths": [],
        "error_message": None,
    }

    # Check for Decimals
    decimal_paths = find_decimals_in_object(obj)
    result["has_decimals"] = len(decimal_paths) > 0
    result["decimal_count"] = len(decimal_paths)
    result["decimal_paths"] = decimal_paths

    # Test JSON serialization
    try:
        json.dumps(obj)
        result["is_serializable"] = True
    except Exception as e:
        result["error_message"] = str(e)

    return result
