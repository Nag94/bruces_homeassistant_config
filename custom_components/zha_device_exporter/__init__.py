"""Custom component used to export ZHA Zigbee devices to a JSON file."""
import logging
import os

from homeassistant.util.json import save_json
import voluptuous as vol


ATTR_OUTPUT_DIR = "output_dir"
DOMAIN = "zha_device_exporter"
CONFIG_OUTPUT_DIR_NAME = "zha-device-export"
SERVICE_EXPORT_DEVICES = "export_devices"
SERVICE_SCHEMAS = {SERVICE_EXPORT_DEVICES: vol.Schema({})}

LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up zha-device-exporter from config."""
    if DOMAIN not in config:
        return True

    try:
        zha_gateway = hass.data["zha"]["zha_gateway"]
    except KeyError:
        return False

    output_dir = os.path.join(hass.config.config_dir, CONFIG_OUTPUT_DIR_NAME)

    def mkdir(directory):
        try:
            os.mkdir(directory)
            return True
        except OSError as exc:
            LOGGER.error("Couldn't create '%s' dir: %s", directory, exc)
            return False

    if not os.path.isdir(output_dir):
        if not await hass.async_add_executor_job(mkdir, output_dir):
            return False

    def get_devices():
        """Get all ZHA Zigbee device information."""
        return [device.async_get_info() for device in zha_gateway.devices.values()]

    async def export_devices_handler(service):
        """Export ZHA devices to a json file right now."""
        file_name = os.path.join(output_dir, "zha-devices.json")
        await hass.async_add_executor_job(save_json, file_name, get_devices())

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DEVICES,
        export_devices_handler,
        schema=SERVICE_SCHEMAS[SERVICE_EXPORT_DEVICES],
    )

    return True
