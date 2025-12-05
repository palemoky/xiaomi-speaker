"""MiService integration for Xiaomi speaker control."""

import asyncio
import logging
from typing import Optional

from aiohttp import ClientSession
from miservice import MiAccount, MiNAService

from src.config import settings

logger = logging.getLogger(__name__)


class SpeakerService:
    """Service for controlling Xiaomi speaker via MiService (async)."""

    def __init__(self) -> None:
        """Initialize the speaker service."""
        # Device ID should be UUID string (e.g., '3538628d-2c49-4eaf-8420-6b760673296f')
        # Not the hardware ID (e.g., 77889911)
        self.device_id = settings.mi_did
        logger.info(f"Using device ID: {self.device_id}")
        
        self.account: Optional[MiAccount] = None
        self.service: Optional[MiNAService] = None
        self.session: Optional[ClientSession] = None

    async def connect(self) -> None:
        """Connect to Xiaomi account and initialize MiNA service."""
        try:
            logger.info("Connecting to Xiaomi account...")
            logger.debug(f"MI_USER: {settings.mi_user}, MI_DID: {settings.mi_did}")
            
            if not self.session:
                self.session = ClientSession()
            
            self.account = MiAccount(
                session=self.session,
                username=settings.mi_user,
                password=settings.mi_pass
            )
            self.service = MiNAService(self.account)
            
            # Get device list to find UUID from DID (hardware ID)
            try:
                devices = await self.service.device_list()
                logger.info(f"Found {len(devices)} devices")
                
                # Log available devices
                for device in devices:
                    device_id = device.get('deviceID')  # UUID
                    hardware = device.get('hardware', '')  # DID (hardware ID)
                    name = device.get('name', 'Unknown')
                    logger.info(f"  Device: {name} (UUID: {device_id}, DID: {hardware})")
                
                # If MI_DID is a hardware ID (numeric), find the corresponding UUID
                if settings.mi_did.replace('-', '').isdigit():
                    # MI_DID looks like a hardware ID, find the UUID
                    logger.info(f"MI_DID appears to be a hardware ID: {settings.mi_did}")
                    for device in devices:
                        if str(device.get('hardware', '')) == settings.mi_did:
                            self.device_id = device.get('deviceID')
                            logger.info(f"Found UUID for DID {settings.mi_did}: {self.device_id}")
                            break
                    else:
                        logger.error(f"Hardware ID {settings.mi_did} not found in device list!")
                        available_dids = [str(d.get('hardware', '')) for d in devices if d.get('hardware')]
                        logger.error(f"Available hardware IDs: {available_dids}")
                        raise ValueError(
                            f"Hardware ID '{settings.mi_did}' not found. "
                            f"Available IDs: {available_dids}"
                        )
                else:
                    # MI_DID is already a UUID
                    device_ids = [d.get('deviceID') for d in devices]
                    if self.device_id not in device_ids:
                        logger.error(f"Device UUID {self.device_id} not found in device list!")
                        logger.error(f"Available UUIDs: {device_ids}")
                        raise ValueError(
                            f"Device UUID '{self.device_id}' not found. "
                            f"Available UUIDs: {device_ids}"
                        )
                
            except Exception as e:
                logger.error(f"Failed to get device list: {e}")
                raise
            
            logger.info(f"Successfully connected, using device UUID: {self.device_id}")
        except Exception as e:
            logger.error(f"Failed to connect to Xiaomi account: {e}")
            logger.error(f"Please check MI_USER, MI_PASS, and MI_DID environment variables")
            raise

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def play_audio_url(self, audio_url: str) -> bool:
        """Play audio from URL on the speaker.

        Args:
            audio_url: HTTP URL of the audio file to play

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            await self.connect()

        try:
            logger.info(f"Playing audio from URL: {audio_url}")
            logger.debug(f"Device ID: {self.device_id}, Type: {type(self.device_id)}")
            
            # Use MiNAService to play audio by URL
            result = await self.service.play_by_url(self.device_id, audio_url)
            
            logger.info(f"play_by_url result: {result}")
            logger.debug(f"Result type: {type(result)}")
            
            # Check if result indicates success
            # MiNA API might return different formats
            if result is None or result == "":
                logger.info("Audio playback initiated successfully (no error)")
                return True
            elif isinstance(result, dict):
                if result.get("code") == 0 or result.get("status") == "success":
                    logger.info("Audio playback initiated successfully")
                    return True
                else:
                    logger.error(f"API returned error: {result}")
                    return False
            else:
                # Unknown result format, log it
                logger.warning(f"Unexpected result format: {result}")
                return True  # Assume success if no exception
                
        except Exception as e:
            logger.error(f"Failed to play audio: {e}", exc_info=True)
            return False

    async def play_tts(self, text: str) -> bool:
        """Play text-to-speech on the speaker.

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            await self.connect()

        try:
            logger.info(f"Playing TTS: {text}")
            # Use MiNAService text_to_speech method
            result = await self.service.text_to_speech(self.device_id, text)
            logger.info(f"TTS playback initiated: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to play TTS: {e}")
            return False

    async def set_volume(self, volume: int) -> bool:
        """Set speaker volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            await self.connect()

        if not 0 <= volume <= 100:
            logger.error(f"Invalid volume level: {volume}")
            return False

        try:
            logger.info(f"Setting volume to: {volume}")
            # Use MiNAService player_set_volume method
            result = await self.service.player_set_volume(self.device_id, volume)
            logger.info(f"Volume set: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

