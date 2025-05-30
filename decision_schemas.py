# Enhanced Option Alpha Bot Schema - Decision Recipe Schemas
# Comprehensive decision schemas for all Option Alpha decision types

from typing import Dict, Any
from decision_recipe_enums import *
from enhanced_bot_schema_enums import *

# =============================================================================
# DECISION SCHEMA DEFINITIONS
# =============================================================================

DECISION_SCHEMAS = {
    "decision": {
        "type": "object",
        "required": ["recipe_type"],
        "properties": {
            "recipe_type": {
                "enum": [item.value for item in DecisionType],
                "description": "Type of decision recipe to evaluate"
            },
            "logic_operator": {
                "enum": ["and", "or"],
                "description": "Logic operator for grouped decisions"
            },
            "grouped_decisions": {
                "type": "array",
                "items": {"$ref": "#/definitions/decision"},
                "description": "Sub-decisions for grouped logic (requires logic_operator)"
            }
        },
        "allOf": [
            # =============================================================================
            # STOCK DECISION RECIPES
            # =============================================================================
            {
                "if": {"properties": {"recipe_type": {"const": DecisionType.STOCK.value}}},
                "then": {
                    "required": ["symbol", "comparison"],
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to evaluate"
                        },
                        "price_field": {
                            "enum": [item.value for item in StockPriceField],
                            "default": StockPriceField.LAST_PRICE.value,
                            "description": "Stock price field to compare"
                        },
                        "comparison": {
                            "enum": [item.value for item in ComparisonOperator],
                            "description": "Comparison operator"
                        },
                        "value": {
                            "type": "number",
                            "description": "Target value for comparison"
                        },
                        "value2": {
                            "type": "number", 
                            "description": "Second value for 'between' comparisons"
                        },
                        "reference_point": {
                            "enum": [item.value for item in PriceReference],
                            "description": "Reference point for price comparisons"
                        },
                        "time_frame": {
                            "enum": [item.value for item in TimeFrame],
                            "description": "Time frame for comparison"
                        },
                        "days_ago": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 365,
                            "description": "Number of days ago for historical comparisons"
                        },
                        "expiration_config": {
                            "$ref": "#/definitions/expiration_config",
                            "description": "Expiration configuration for expected move calculations"
                        },
                        "probability_config": {
                            "type": "object",
                            "description": "Configuration for probability-based stock decisions",
                            "properties": {
                                "above_percent": {"type": "number"},
                                "below_percent": {"type": "number"},
                                "low_price": {"type": "number"},
                                "high_price": {"type": "number"},
                                "days": {"type": "integer", "minimum": 1},
                                "probability_threshold": {"type": "number", "minimum": 0, "maximum": 100}
                            }
                        