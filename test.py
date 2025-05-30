from schema.oa_bot_schema import (
    COMPLETE_SCHEMA,
    BotConfigValidator, 
    TemplateGenerator,
    validate_bot_configuration,
    create_simple_bot_template
)

# Create and validate a bot
bot_config = create_simple_bot_template()
is_valid, errors = validate_bot_configuration(bot_config)