# Option Alpha Framework - Phase 0

A modular backtesting architecture for Option Alpha bot strategies using QuantConnect's Python LEAN libraries.

## Phase 0 Status: ✅ COMPLETE

Phase 0 provides the core foundation with JSON schema, configuration loading, event system, logging, state management, and stubbed decision/position engines.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    OA Bot Framework                         │
├─────────────────────────────────────────────────────────────┤
│  📋 JSON Configuration Layer                               │
│    • Bot config schema validation                          │
│    • Enum-based type safety                               │
│    • Configuration loading & validation                    │
├─────────────────────────────────────────────────────────────┤
│  🎯 Event System                                          │
│    • Publisher/Subscriber pattern                         │
│    • Async event processing                               │
│    • Market, Trade, System events                         │
├─────────────────────────────────────────────────────────────┤
│  📝 Logging System                                        │
│    • Multi-level categorized logging                      │
│    • Memory-based with rotation                           │
│    • QuantConnect-friendly                                │
├─────────────────────────────────────────────────────────────┤
│  💾 State Management                                       │
│    • Hot State: In-memory real-time                       │
│    • Warm State: SQLite session data                      │
│    • Cold State: Historical trades/analysis               │
├─────────────────────────────────────────────────────────────┤
│  🧠 Decision Engine (Stubbed)                             │
│    • Stock, Indicator, Position decisions                 │
│    • Grouped AND/OR logic                                 │
│    • Option Alpha recipe compatibility                    │
├─────────────────────────────────────────────────────────────┤
│  📊 Position Manager (Stubbed)                            │
│    • Multi-leg options positions                          │
│    • P&L tracking and Greeks                              │
│    • Portfolio-level risk management                      │
├─────────────────────────────────────────────────────────────┤
│  🤖 Bot Orchestration                                     │
│    • Configuration-driven bot creation                    │
│    • Automation scheduling and execution                  │
│    • Status monitoring and control                        │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Framework Files

| File | Purpose | Status |
|------|---------|--------|
| `oa_bot_schema.py` | JSON schema, validation, config loading | ✅ Complete |
| `oa_framework_enums.py` | Type-safe enums and constants | ✅ Complete |
| `oa_framework_core.py` | Core classes and bot orchestration | ✅ Complete |
| `phase0_test.py` | Comprehensive test suite | ✅ Complete |
| `README.md` | Documentation | ✅ Complete |

## 🚀 Quick Start

### 1. Run the Test Suite

```bash
python phase0_test.py
```

Expected output:
```
🚀 Starting Phase 0 Test Suite
========================================================
🧪 Testing: Schema Validation
✅ Schema Validation: PASSED
...
📊 TEST SUMMARY
========================================================
✅ Passed: 10
❌ Failed: 0
📈 Success Rate: 100.0%

🎉 ALL TESTS PASSED! Phase 0 is ready for production.
```

### 2. Create and Run a Bot

```python
from oa_bot_schema import OABotConfigGenerator
from oa_framework_core import OABot
import json
import tempfile

# Generate sample configuration
generator = OABotConfigGenerator()
config = generator.generate_simple_long_call_bot()

# Save to file
with open('my_bot_config.json', 'w') as f:
    json.dump(config, f, indent=2)

# Initialize and run bot
bot = OABot('my_bot_config.json')
bot.start()

# Check status
status = bot.get_status()
print(f"Bot: {status['name']}")
print(f"State: {status['state']}")
print(f"Automations: {len(status['automations'])}")

# Stop bot
bot.stop()
```

### 3. Test Individual Components

```python
from oa_framework_core import FrameworkLogger, StateManager
from oa_framework_enums import LogCategory, LogLevel

# Test logging
logger = FrameworkLogger("MyTest")
logger.info(LogCategory.SYSTEM, "Framework is working!", version="1.0")

# Test state management
state_mgr = StateManager()
state_mgr.set_hot_state("current_price", {"SPY": 450.25})
price = state_mgr.get_hot_state("current_price")
print(f"Current price: {price}")
```

## 📋 Configuration Schema

The framework uses JSON configuration files that define complete bot strategies:

```json
{
  "name": "My Trading Bot",
  "account": "paper_trading",
  "group": "Test Strategies",
  "safeguards": {
    "capital_allocation": 10000,
    "daily_positions": 5,
    "position_limit": 15,
    "daytrading_allowed": false
  },
  "scan_speed": "15_minutes",
  "symbols": {
    "type": "static",
    "list": ["SPY", "QQQ"]
  },
  "automations": [
    {
      "name": "Long Call Scanner",
      "trigger": {
        "type": "continuous",
        "automation_type": "scanner"
      },
      "actions": [
        {
          "type": "decision",
          "decision": {
            "recipe_type": "stock",
            "symbol": "SPY",
            "price_field": "last_price",
            "comparison": "greater_than",
            "value": 400
          },
          "yes_path": [
            {
              "type": "open_position",
              "position": {
                "strategy_type": "long_call",
                "symbol": "SPY",
                "expiration": {
                  "type": "between_days",
                  "days": 30,
                  "days_end": 45
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## 🔧 Available Components

### Enums & Constants
- **Position Types**: `long_call`, `iron_condor`, `short_put_spread`, etc.
- **Decision Types**: `stock`, `indicator`, `position`, `bot`, `opportunity`
- **Comparison Operators**: `greater_than`, `less_than`, `between`, etc.
- **Technical Indicators**: `RSI`, `MACD`, `SMA`, `EMA`, etc.
- **Event Types**: `market_open`, `position_opened`, `bot_started`, etc.

### Decision Recipes (Phase 0 - Stubbed)
All Option Alpha decision recipes are defined but return stub results:
- **Stock Decisions**: Price, volume, IV rank, earnings, etc.
- **Indicator Decisions**: RSI, MACD, moving averages, etc.
- **Position Decisions**: P&L, Greeks, time decay, etc.
- **Bot Decisions**: Capital, position limits, portfolio metrics
- **Opportunity Decisions**: Bid/ask spread, probability metrics

### State Management
- **Hot State**: Real-time data in memory (positions, prices)
- **Warm State**: Session data in SQLite (daily P&L, settings)
- **Cold State**: Historical data (completed trades, analytics)

## 📈 What's Working (Phase 0)

✅ **Complete JSON Schema** - All Option Alpha recipes defined
✅ **Configuration Loading** - File-based bot configuration
✅ **Type Safety** - Comprehensive enums and validation
✅ **Event System** - Publisher/subscriber with async processing
✅ **Logging** - Multi-level categorized logging system
✅ **State Management** - Hot/warm/cold data persistence
✅ **Bot Framework** - Complete orchestration and lifecycle
✅ **Error Handling** - Standardized error codes and messages
✅ **Test Coverage** - Comprehensive test suite

## 🚧 What's Stubbed (Phase 0)

⚠️ **Decision Engine** - All decisions return `YES` (Phase 2)
⚠️ **Position Management** - Creates fake positions (Phase 3)
⚠️ **Market Data** - No real data integration (Phase 1)
⚠️ **QuantConnect Integration** - No QC algorithm yet (Phase 1)
⚠️ **Options Chains** - No real options data (Phase 1)
⚠️ **Risk Management** - Basic structure only (Phase 3)

## 🎯 Next Steps: Phase 1

Phase 1 will implement:
1. **QuantConnect Algorithm Integration**
2. **Basic Market Data Handling**
3. **Simple Long Call/Put Strategies**
4. **Real Position Opening/Closing**
5. **Basic Options Chain Processing**

## 🧪 Testing

The framework includes comprehensive tests for all Phase 0 components:

```bash
# Run all tests
python phase0_test.py

# Expected: 10/10 tests passing
# Tests cover: Schema, Config, Enums, Logging, State, Events, etc.
```

## 📚 Key Design Patterns

- **Factory Pattern**: Position creation from JSON config
- **Observer Pattern**: Event handling and notifications
- **State Machine**: Position and bot lifecycle management
- **Strategy Pattern**: Different automation logic types
- **Command Pattern**: Action execution framework

## 🔍 Debugging

Enable debug logging to see detailed framework operation:

```python
from oa_framework_enums import LogLevel

# In your bot configuration
logger = FrameworkLogger("Debug", LogLevel.DEBUG)
logger.debug(LogCategory.SYSTEM, "Debug message", data={"key": "value"})

# View logs
logs = logger.get_logs(level=LogLevel.DEBUG)
for log in logs:
    print(f"{log['timestamp']}: {log['message']}")
```

## ⚡ Performance Notes

- **Memory Usage**: Hot state kept in memory for speed
- **Database**: SQLite for persistence, optimized queries
- **Threading**: Event processing in background threads
- **Caching**: Built-in caching for expensive operations

## 🤝 Contributing

Phase 0 is complete, but improvements are welcome:

1. Additional validation rules
2. More comprehensive error messages
3. Performance optimizations
4. Additional utility functions

## 📄 License

This framework is designed for educational and backtesting purposes. Use in accordance with QuantConnect and Option Alpha terms of service.

---

**Phase 0 Status: ✅ READY FOR PHASE 1**

The foundation is solid and all core components are working correctly. Ready to proceed with QuantConnect integration and basic strategy implementation.