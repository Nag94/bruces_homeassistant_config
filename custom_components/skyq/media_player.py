"""The skyq platform allows you to control a SkyQ set top box."""
import logging
from datetime import datetime, timedelta
from pathlib import Path

from homeassistant.components.homekit.const import (
    ATTR_KEY_NAME,
    EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED,
    KEY_FAST_FORWARD,
    KEY_REWIND,
)
from homeassistant.components.media_player import DEVICE_CLASS_RECEIVER, DEVICE_CLASS_TV, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_APP,
    MEDIA_TYPE_TVSHOW,
    SUPPORT_BROWSE_MEDIA,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_UNKNOWN,
)
from pyskyqremote.const import APP_EPG, SKY_STATE_OFF, SKY_STATE_ON, SKY_STATE_PAUSED, SKY_STATE_STANDBY
from pyskyqremote.skyq_remote import SkyQRemote

from .classes.config import Config
from .classes.mediabrowser import Media_Browser
from .classes.switchmaker import Switch_Maker
from .classes.volumeentity import Volume_Entity
from .const import (
    APP_IMAGE_URL_BASE,
    CONF_EPG_CACHE_LEN,
    CONST_DEFAULT_EPGCACHELEN,
    CONST_SKYQ_CHANNELNO,
    CONST_SKYQ_MEDIA_TYPE,
    DOMAIN,
    DOMAINBROWSER,
    ERROR_TIMEOUT,
    FEATURE_BASE,
    FEATURE_GET_LIVE_RECORD,
    FEATURE_IMAGE,
    FEATURE_LIVE_TV,
    FEATURE_SWITCHES,
    FEATURE_TV_DEVICE_CLASS,
    REMOTE_BUTTONS,
    SKYQ_APP,
    SKYQ_ICONS,
    SKYQ_LIVE,
    SKYQ_LIVEREC,
    SKYQ_PVR,
    SKYQREMOTE,
)
from .utils import App_Image_Url, get_command

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the SkyQ platform."""
    host = config.get(CONF_HOST)
    epg_cache_len = config.get(CONF_EPG_CACHE_LEN, CONST_DEFAULT_EPGCACHELEN)
    remote = await hass.async_add_executor_job(SkyQRemote, host, epg_cache_len)

    unique_id = None
    name = config.get(CONF_NAME)

    await _async_setup_platform_entry(
        config,
        async_add_entities,
        remote,
        unique_id,
        name,
        hass,
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a SKY Q entity."""
    remote = hass.data[DOMAIN][config_entry.entry_id][SKYQREMOTE]

    unique_id = config_entry.unique_id
    name = config_entry.data[CONF_NAME]

    await _async_setup_platform_entry(
        config_entry.options,
        async_add_entities,
        remote,
        unique_id,
        name,
        hass,
    )


async def _async_setup_platform_entry(config_item, async_add_entities, remote, unique_id, name, hass):

    config = Config(unique_id, name, config_item)

    player = SkyQDevice(
        hass,
        remote,
        config,
    )

    should_cache = False
    files_path = Path(__file__).parent / "static"
    hass.http.register_static_path(APP_IMAGE_URL_BASE, str(files_path), should_cache)

    async_add_entities([player], True)

    async def _async_homekit_event(_event):
        if player.entity_id != _event.data[ATTR_ENTITY_ID]:
            return

        keyname = _event.data[ATTR_KEY_NAME]
        # _LOGGER.debug(f"D0030M - Homekit event - {player.entity_id} - {keyname}")
        if keyname in REMOTE_BUTTONS:
            await player.async_play_media(REMOTE_BUTTONS[keyname], DOMAIN)
        elif keyname == KEY_REWIND:
            # Lovelace previous_track buttons do rewind
            await player.async_media_previous_track()
        elif keyname == KEY_FAST_FORWARD:
            # Lovelace next_track buttons do fast forward
            await player.async_media_next_track()
        else:
            _LOGGER.warning(f"W0040M - Invalid Homekit event - {player.entity_id} - {keyname}")

    hass.bus.async_listen(EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED, _async_homekit_event)


class SkyQDevice(MediaPlayerEntity):
    """Representation of a SkyQ Box."""

    def __init__(
        self,
        hass,
        remote,
        config,
    ):
        """Initialise the SkyQRemote."""
        self._config = config
        self._unique_id = config.unique_id
        if config.volume_entity:
            self._volume_entity = Volume_Entity(hass, config.volume_entity, self._config.name)
        else:
            self._volume_entity = None
        self._appImageUrl = App_Image_Url()
        self._media_browser = Media_Browser(remote, config, self._appImageUrl)
        self._state = STATE_OFF
        self._skyq_type = STATE_OFF
        self._skyq_channelno = None
        self._title = None
        self._channel = None
        self._episode = None
        self._imageUrl = None
        self._imageRemotelyAccessible = False
        self._season = None
        self._remote = remote
        self._available = True
        self._errorTime = None
        self._startupSetup = True
        self._deviceInfo = None
        self._channel_list = None
        self._use_internal = True
        self._switches_generated = False

        if not self._remote.deviceSetup:
            self._available = False
            self._startupSetup = False
            _LOGGER.warning(f"W0010M - Device is not available: {self.name}")

        self._supported_features = FEATURE_BASE

    @property
    def supported_features(self):
        """Get the supported features."""
        if self._config.volume_entity:
            self._supported_features = self._supported_features | SUPPORT_VOLUME_MUTE
            self._supported_features = self._supported_features | SUPPORT_VOLUME_STEP
            if (
                self._volume_entity.supported_features()
                and self._volume_entity.supported_features() & SUPPORT_VOLUME_SET
            ):
                self._supported_features = self._supported_features | SUPPORT_VOLUME_SET
        if len(self._config.source_list) > 0 and self.state not in (
            STATE_OFF,
            STATE_UNKNOWN,
        ):
            return self._supported_features | SUPPORT_BROWSE_MEDIA

        return self._supported_features

    @property
    def name(self):
        """Get the name of the devices."""
        return self._config.name

    @property
    def should_poll(self):
        """Device should be polled."""
        return True

    @property
    def state(self):
        """Get the device state. An exception means OFF state."""
        return self._state

    @property
    def source_list(self):
        """Get the list of sources for the device."""
        if not self.source or self.source in self._config.source_list:
            return self._config.source_list
        sources = self._config.source_list.copy()
        sources.insert(0, self.source)
        return sources

    @property
    def source(self):
        """Title of current playing media."""
        if self._skyq_type == SKYQ_PVR:
            return SKYQ_PVR.upper()

        return self._channel if self._channel is not None else None

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._imageUrl if self._config.enabled_features & FEATURE_IMAGE else None

    @property
    def media_image_remotely_accessible(self):
        """Is the media image available outside home network."""
        return self._imageRemotelyAccessible

    @property
    def media_channel(self):
        """Channel currently playing."""
        return self._channel

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        if self.state == STATE_UNKNOWN:
            return None
        if self._skyq_type == SKYQ_APP:
            return MEDIA_TYPE_APP

        return MEDIA_TYPE_TVSHOW

    @property
    def media_series_title(self):
        """Get the title of the series of current playing media."""
        return self._title if self._channel is not None else None

    @property
    def media_title(self):
        """Title of current playing media."""
        return self._channel if self._channel is not None else self._title

    @property
    def media_season(self):
        """Season of current playing media (TV Show only)."""
        return self._season

    @property
    def media_episode(self):
        """Episode of current playing media (TV Show only)."""
        return self._episode

    @property
    def icon(self):
        """Entity icon."""
        return SKYQ_ICONS[self._skyq_type]

    @property
    def device_class(self):
        """Entity class."""
        return DEVICE_CLASS_TV if self._config.enabled_features & FEATURE_TV_DEVICE_CLASS else DEVICE_CLASS_RECEIVER

    @property
    def available(self):
        """Entity availability."""
        return self._available

    @property
    def device_info(self):
        """Entity device information."""
        return (
            {
                "identifiers": {(DOMAIN, self._deviceInfo.serialNumber)},
                "name": self.name,
                "manufacturer": self._deviceInfo.manufacturer,
                "model": self._deviceInfo.hardwareModel,
                "sw_version": f"{self._deviceInfo.ASVersion}:{self._deviceInfo.versionNumber}",
            }
            if self._deviceInfo
            else None
        )

    @property
    def unique_id(self):
        """Entity unique id."""
        return self._unique_id

    @property
    def device_state_attributes(self):
        """Return entity specific state attributes."""
        attributes = {CONST_SKYQ_MEDIA_TYPE: self._skyq_type}
        if self._skyq_channelno:
            attributes[CONST_SKYQ_CHANNELNO] = self._skyq_channelno
        return attributes

    @property
    def volume_level(self):
        """Volume level of entity specified in config."""
        return self._volume_entity.volume_level() if self._volume_entity else None

    @property
    def is_volume_muted(self):
        """Boolean if volume is muted."""
        return self._volume_entity.is_volume_muted() if self._volume_entity else None

    async def async_update(self):
        """Get the latest data and update device state."""
        self._channel = None
        self._skyq_channelno = None
        self._episode = None
        self._imageUrl = None
        self._season = None
        self._title = None

        if not self._deviceInfo:
            await self._async_getDeviceInfo()

        if self._deviceInfo:
            await self._async_updateState()

        if self._state not in [STATE_UNKNOWN, STATE_OFF]:
            await self._async_updateCurrentProgramme()

        if self._volume_entity:
            await self._volume_entity.async_update_volume_state(self.hass)

        if not self._switches_generated and self.entity_id:
            self._switches_generated = True
            if self._config.enabled_features & FEATURE_SWITCHES:
                Switch_Maker(
                    self.hass.config.config_dir,
                    self.entity_id,
                    self._config.room,
                    self._config.source_list,
                )

    async def async_turn_off(self):
        """Turn SkyQ box off."""
        powerStatus = await self.hass.async_add_executor_job(self._remote.powerStatus)
        if powerStatus == SKY_STATE_ON:
            await self.hass.async_add_executor_job(self._remote.press, "power")
            await self.async_update()

    async def async_turn_on(self):
        """Turn SkyQ box on."""
        powerStatus = await self.hass.async_add_executor_job(self._remote.powerStatus)
        if powerStatus == SKY_STATE_STANDBY:
            await self.hass.async_add_executor_job(self._remote.press, ["home", "dismiss"])
            await self.async_update()

    async def async_media_play(self):
        """Play the current media item."""
        await self.hass.async_add_executor_job(self._remote.press, "play")
        self._state = STATE_PLAYING
        self.async_write_ha_state()

    async def async_media_pause(self):
        """Pause the current media item."""
        await self.hass.async_add_executor_job(self._remote.press, "play")
        self._state = STATE_PAUSED
        self.async_write_ha_state()

    async def async_media_next_track(self):
        """Fast forward the current media item."""
        await self.hass.async_add_executor_job(self._remote.press, "fastforward")
        await self.async_update()

    async def async_media_previous_track(self):
        """Rewind the current media item."""
        await self.hass.async_add_executor_job(self._remote.press, "rewind")
        await self.async_update()

    async def async_select_source(self, source):
        """Select the specified source."""
        command = get_command(self._config.custom_sources, self._channel_list, source)
        if command:
            await self.hass.async_add_executor_job(self._remote.press, command)
            await self.async_update()

    async def async_play_media(self, media_id, media_type, **kwargs):
        """Perform a media action."""
        if media_type.casefold() == DOMAIN:
            await self.hass.async_add_executor_job(self._remote.press, media_id.casefold())
            await self.async_update()
        if media_type.casefold() == DOMAINBROWSER:
            await self.async_select_source(media_id)

    async def async_mute_volume(self, mute):
        """Mute the volume."""
        if self._volume_entity.supported_features() & SUPPORT_VOLUME_MUTE:
            await self._volume_entity.async_mute_volume(self.hass, mute)
        else:
            await self.async_set_volume_level(0)

    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        # _LOGGER.debug(f"D9999M - Volume level - {self.name}")
        await self._volume_entity.async_set_volume_level(self.hass, volume)

    async def async_volume_up(self):
        """Turn volume up for media player."""
        # _LOGGER.debug(f"D9999M - Volume up - {self.name}")
        if self._volume_entity.supported_features() & SUPPORT_VOLUME_STEP:
            await self._volume_entity.async_volume_up(self.hass)
        elif self.volume_level:
            await self.async_set_volume_level(self.volume_level + 0.02)

    async def async_volume_down(self):
        """Turn volume down for media player."""
        # _LOGGER.debug(f"D9999M - Volume down - {self.name}")
        if self._volume_entity.supported_features() & SUPPORT_VOLUME_STEP:
            await self._volume_entity.async_volume_down(self.hass)
        elif self.volume_level:
            await self.async_set_volume_level(self.volume_level - 0.02)

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Implement the websocket media browsing helper."""
        return await self._media_browser.async_browse_media(
            self.hass, self._channel_list, media_content_type, media_content_id
        )

    async def _async_updateState(self):
        powerState = await self.hass.async_add_executor_job(self._remote.powerStatus)
        self._setPowerStatus(powerState)
        if powerState == SKY_STATE_STANDBY:
            self._skyq_type = STATE_OFF
            self._state = STATE_OFF
            return
        if powerState != SKY_STATE_ON:
            self._skyq_type = STATE_UNKNOWN
            self._state = STATE_OFF
            return

        currentState = await self.hass.async_add_executor_job(self._remote.getCurrentState)

        if currentState == SKY_STATE_PAUSED:
            self._state = STATE_PAUSED
        else:
            self._state = STATE_PLAYING

    async def _async_updateCurrentProgramme(self):

        app = await self.hass.async_add_executor_job(self._remote.getActiveApplication)
        appTitle = app.title

        if app.appId == APP_EPG:
            await self._async_getCurrentMedia()
        else:
            self._skyq_type = SKYQ_APP
            self._title = appTitle

        self._imageRemotelyAccessible = True
        if not self._imageUrl:
            appImageUrl = self._appImageUrl.getAppImageUrl(appTitle)
            if appImageUrl:
                self._imageUrl = appImageUrl
                self._imageRemotelyAccessible = False

    async def _async_getCurrentMedia(self):
        currentMedia = None
        try:
            currentMedia = await self.hass.async_add_executor_job(self._remote.getCurrentMedia)

            if not currentMedia:
                return None

            if currentMedia.live and currentMedia.sid:
                await self._async_get_live_media(currentMedia)

            elif currentMedia.pvrId:
                await self._async_get_recording(currentMedia)

        except Exception as err:
            _LOGGER.exception(f"X0010M - Current Media retrieval failed: {currentMedia} : {err}")

    async def _async_get_live_media(self, currentMedia):
        self._channel = currentMedia.channel
        self._skyq_channelno = currentMedia.channelno
        self._imageUrl = currentMedia.imageUrl
        self._skyq_type = SKYQ_LIVE
        if not self._config.enabled_features & FEATURE_LIVE_TV:
            return

        currentProgramme = await self.hass.async_add_executor_job(
            self._remote.getCurrentLiveTVProgramme, currentMedia.sid
        )
        if not currentProgramme:
            return

        self._episode = currentProgramme.episode
        self._season = currentProgramme.season
        self._title = currentProgramme.title
        if currentProgramme.imageUrl:
            self._imageUrl = currentProgramme.imageUrl

        if not self._config.enabled_features & FEATURE_GET_LIVE_RECORD:
            return

        recordings = await self.hass.async_add_executor_job(self._remote.getRecordings, "RECORDING")
        for recording in recordings.programmes:
            if currentProgramme.programmeuuid == recording.programmeuuid:
                self._skyq_type = SKYQ_LIVEREC

    async def _async_get_recording(self, currentMedia):
        recording = await self.hass.async_add_executor_job(self._remote.getRecording, currentMedia.pvrId)
        self._skyq_type = SKYQ_PVR
        if recording:
            self._channel = recording.channelname
            self._skyq_channelno = None
            self._episode = recording.episode
            self._season = recording.season
            self._title = recording.title
            self._imageUrl = recording.imageUrl

    async def _async_getDeviceInfo(self):
        await self.hass.async_add_executor_job(
            self._remote.setOverrides,
            self._config.overrideCountry,
            self._config.test_channel,
        )
        self._deviceInfo = await self.hass.async_add_executor_job(self._remote.getDeviceInformation)
        if self._deviceInfo:
            if not self._unique_id:
                self._unique_id = self._deviceInfo.epgCountryCode + "".join(
                    e for e in self._deviceInfo.serialNumber.casefold() if e.isalnum()
                )

            if not self._channel_list and len(self._config.channel_sources) > 0:
                channelData = await self.hass.async_add_executor_job(self._remote.getChannelList)
                self._channel_list = channelData.channels

    def _setPowerStatus(self, powerStatus):

        if powerStatus == SKY_STATE_OFF:
            self._powerStatus_off_handling()
        else:
            self._powerStatus_on_handling()

    def _powerStatus_off_handling(self):
        error_time_target = self._errorTime + timedelta(seconds=ERROR_TIMEOUT) if self._errorTime else 0
        if not self._errorTime or datetime.now() < error_time_target:
            if not self._errorTime:
                self._errorTime = datetime.now()
            _LOGGER.debug(f"D0010M - Device is not available - {self._error_time_so_far()} Seconds: {self.name}")
        elif datetime.now() >= error_time_target and self._available:
            self._available = False
            _LOGGER.warning(f"W0030M - Device is not available: {self.name}")

    def _powerStatus_on_handling(self):
        if not self._available:
            self._available = True
            if self._startupSetup:
                _LOGGER.info(f"I0020M - Device is now available: {self.name}")
            else:
                self._startupSetup = True
                _LOGGER.warning(f"W0020M - Device is now available: {self.name}")
        elif self._errorTime:
            _LOGGER.debug(f"D0020M - Device is now available - {self._error_time_so_far()} Seconds: {self.name}")
        self._errorTime = None

    def _error_time_so_far(self):
        return (datetime.now() - self._errorTime).seconds if self._errorTime else 0
