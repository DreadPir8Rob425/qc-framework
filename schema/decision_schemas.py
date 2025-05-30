# Option Alpha Bot Schema - Main Entry Point
# Import this file to get access to the complete enhanced schema system

"""
Option Alpha Bot Schema System

This module provides a comprehensive JSON schema system for defining Option Alpha trading bots
that can be backtested in QuantConnect. The schema supports all Option Alpha features plus
custom multi-leg strategies.

Usage:
    from oa_bot_schema import COMPLETE_SCHEMA, BotConfigValidator, TemplateGenerator
    
    # Validate a bot configuration
    validator = BotConfigValidator()
    is_valid, errors = validator.validate_bot_config(my_config)
    
    # Generate templates
    templates = TemplateGenerator()
    simple_bot = templates.create_simple_long_call_bot()
    
    # Get the complete schema for external tools
    schema = COMPLETE_SCHEMA
"""

# Import all components
from enhanced_bot_schema_enums import *
from decision_recipe_enums import *
from position_configuration_enums import *
from enhanced_bot_schema_core import ENHANCED_OA_BOT_SCHEMA, ValidationLimits
from position_schemas import POSITION_SCHEMA_COMPONENTS, create_position_template, validate_position_config
from decision_schemas import DECISION_SCHEMAS, validate_decision_config
from complete_enhanced_bot_schema import (
    COMPLETE_ENHANCED_OA_BOT_SCHEMA, 
    CompleteSchemaValidator, 
    EnhancedTemplateGenerator,
    create_complete_enhanced_schema
)

# =============================================================================
# MAIN EXPORTS - What users should import
# =============================================================================

# The complete schema
COMPLETE_SCHEMA = COMPLETE_ENHANCED_OA_BOT_SCHEMA

# Main classes for users
BotConfigValidator = CompleteSchemaValidator
TemplateGenerator = EnhancedTemplateGenerator

# Schema components for advanced users
CORE_SCHEMA = ENHANCED_OA_BOT_SCHEMA
POSITION_SCHEMAS = POSITION_SCHEMA_COMPONENTS
DECISION_SCHEMA_COMPONENTS = DECISION_SCHEMAS

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_bot_configuration(config):
    """
    Validate a bot configuration dictionary.
    
    Args:
        config (dict): Bot configuration to validate
        
    Returns:
        tuple: (is_valid: bool, errors: List[str])
    """
    validator = BotConfigValidator()
    return validator.validate_bot_config(config)

def create_simple_bot_template():
    """Create a simple long call bot template"""
    generator = TemplateGenerator()
    return generator.create_simple_long_call_bot()

def create_complex_bot_template():
    """Create a complex iron condor bot template"""
    generator = TemplateGenerator()
    return generator.create_complex_iron_condor_bot()

def get_schema_for_tools():
    """Get the complete schema for external tools (JSON schema validators, IDEs, etc.)"""
    return COMPLETE_SCHEMA

def save_schema_to_file(filename="oa_bot_schema.json"):
    """Save the complete schema to a JSON file"""
    import json
    with open(filename, 'w') as f:
        json.dump(COMPLETE_SCHEMA, f, indent=2)
    print(f"Schema saved to {filename}")

# =============================================================================
# VERSION INFO
# =============================================================================

__version__ = "1.0.0"
__author__ = "QC Framework Team"
__description__ = "Complete Option Alpha Bot Schema for QuantConnect Integration"

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Main Schema
    'COMPLETE_SCHEMA',
    
    # Main Classes
    'BotConfigValidator',
    'TemplateGenerator',
    
    # Convenience Functions
    'validate_bot_configuration',
    'create_simple_bot_template', 
    'create_complex_bot_template',
    'get_schema_for_tools',
    'save_schema_to_file',
    
    # Enums (most commonly used ones)
    'ScanSpeed',
    'TriggerType',
    'ActionType',
    'PositionType',
    'DecisionType',
    'ComparisonOperator',
    'SmartPricing',
    'OptionType',
    'OptionSide',
    
    # Schema Components (for advanced users)
    'CORE_SCHEMA',
    'POSITION_SCHEMAS',
    'DECISION_SCHEMA_COMPONENTS',
    'ValidationLimits',
    
    # Validation functions
    'validate_position_config',
    'validate_decision_config',
    
    # Template functions
    'create_position_template',
    
    # Version info
    '__version__',
    '__author__',
    '__description__'
]

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def demo_usage():
    """Demonstrate basic usage of the schema system"""
    
    print("Option Alpha Bot Schema Demo")
    print("=" * 40)
    
    # 1. Create a simple bot template
    print("\n1. Creating simple bot template...")
    simple_bot = create_simple_bot_template()
    print(f"✓ Created bot: {simple_bot['name']}")
    
    # 2. Validate the template
    print("\n2. Validating bot configuration...")
    is_valid, errors = validate_bot_configuration(simple_bot)
    if is_valid:
        print("✓ Bot configuration is valid")
    else:
        print("✗ Validation errors:")
        for error in errors:
            print(f"  - {error}")
    
    # 3. Show schema statistics
    print("\n3. Schema statistics...")
    schema = get_schema_for_tools()
    print(f"✓ Schema has {len(schema['definitions'])} component definitions")
    print(f"✓ Main schema properties: {len(schema['properties'])}")
    
    # 4. Create a complex bot
    print("\n4. Creating complex bot template...")
    complex_bot = create_complex_bot_template()
    print(f"✓ Created bot: {complex_bot['name']}")
    print(f"✓ Bot has {len(complex_bot['automations'])} automations")
    
    # 5. Validate complex bot
    print("\n5. Validating complex bot...")
    is_valid, errors = validate_bot_configuration(complex_bot)
    if is_valid:
        print("✓ Complex bot configuration is valid")
    else:
        print("✗ Complex bot validation errors:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    print("\n" + "=" * 40)
    print("Demo complete!")

if __name__ == "__main__":
    demo_usage()