# Create as custom_components/telegram_bot_conversation/__init__.py
# Requires telegram_bot to be set up. 
from homeassistant import core
from homeassistant.components.telegram_bot import (
    EVENT_TELEGRAM_TEXT,
    ATTR_TEXT,
    SERVICE_SEND_MESSAGE,
    DOMAIN as TELEGRAM_DOMAIN,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_USER_ID,
    ATTR_CHAT_ID,
)
from homeassistant.components.conversation import _async_converse

DOMAIN = "telegram_bot_conversation"

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    
    async def text_events(event: core.Event):
        
        # Only deal with private chats.
        if event.data[ATTR_CHAT_ID] != event.data[ATTR_USER_ID]:
            return
        
        # Process the conversation intent
        response = await _async_converse(hass, event.data[ATTR_TEXT], event.data[ATTR_USER_ID], "telegram-bot")

        # Deliver the response back
        await hass.services.async_call(
            TELEGRAM_DOMAIN,
            SERVICE_SEND_MESSAGE,
            {
                ATTR_MESSAGE: response.speech["plain"]["speech"],
                ATTR_TARGET: event.data[ATTR_USER_ID],
            },
        )

    # Subscribe to Telegram text events
    hass.bus.async_listen(EVENT_TELEGRAM_TEXT, text_events)
    return True