from oa_framework_core import OABot
from oa_bot_schema import OABotConfigGenerator

# Generate config
config = OABotConfigGenerator().generate_simple_long_call_bot()

# Save and run
import json
with open('test_bot.json', 'w') as f:
    json.dump(config, f, indent=2)

bot = OABot('test_bot.json')
bot.start()
print(bot.get_status())
bot.stop()