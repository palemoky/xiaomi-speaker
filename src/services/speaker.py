"""MiService integration for Xiaomi speaker control."""

import json
import logging
import random
import string
from pathlib import Path

from aiohttp import ClientSession
from miservice import MiAccount, MiNAService

from src.config import settings

logger = logging.getLogger(__name__)


class SpeakerService:
    """Service for controlling Xiaomi speaker via MiService (async)."""

    def __init__(self) -> None:
        """Initialize the speaker service."""
        # 初始时，self.device_id 存储的是用户配置的值（可能是数字ID、UUID或名称）
        # 在 connect() 成功后，它会被更新为真实的 UUID
        self.device_id = str(settings.mi_did)
        logger.info(f"Configured device identifier: {self.device_id}")

        self.account: MiAccount | None = None
        self.service: MiNAService | None = None
        self.session: ClientSession | None = None

    @staticmethod
    def _write_token_cache(token_path: Path) -> None:
        """Write userId and passToken from env to the token cache file.

        Merges with existing token data to preserve any service-specific tokens.
        This enables passToken-based cookie auth, bypassing broken password login.
        """
        # Load existing token data if present
        token: dict = {}
        if token_path.is_file():
            try:
                token = json.loads(token_path.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning(f"Failed to read existing token file: {token_path}")

        # Generate a random deviceId if not already present
        if "deviceId" not in token:
            token["deviceId"] = "".join(random.choices(string.ascii_letters + string.digits, k=16)).upper()

        # Write userId and passToken from env vars
        token["userId"] = settings.mi_user_id
        token["passToken"] = settings.mi_pass_token

        try:
            token_path.write_text(json.dumps(token, indent=2))
            logger.info("Token cache updated from MI_USER_ID and MI_PASS_TOKEN")
        except OSError as e:
            logger.error(f"Failed to write token cache file: {e}")

    async def connect(self) -> None:
        """Connect to Xiaomi account and initialize MiNA service."""
        try:
            logger.info("Connecting to Xiaomi account...")

            if not self.session:
                self.session = ClientSession()

            # Ensure token directory exists
            token_path = Path(settings.mi_token_path)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using token file: {token_path}")

            # If MI_USER_ID and MI_PASS_TOKEN are configured, write them to the token cache
            # file so MiAccount can use passToken-based cookie auth (bypasses broken password login)
            if settings.mi_user_id and settings.mi_pass_token:
                self._write_token_cache(token_path)

            self.account = MiAccount(
                session=self.session,
                username=settings.mi_user,
                password=settings.mi_pass,
                token_store=str(token_path),  # Enable token persistence
            )
            self.service = MiNAService(self.account)

            # Get device list to find the correct UUID
            try:
                devices = await self.service.device_list()
                logger.info(f"Found {len(devices)} devices attached to account")

                target_did = self.device_id

                # Build lookup dictionaries for O(1) access
                devices_by_uuid = {}
                devices_by_miot_did = {}
                devices_by_name = {}

                for device in devices:
                    d_name = device.get("name", "Unknown")
                    d_uuid = device.get("deviceID", "")
                    d_miot_did = str(device.get("miotDID", ""))
                    d_hardware = device.get("hardware", "")

                    # Build lookup dictionaries
                    if d_uuid:
                        devices_by_uuid[d_uuid] = device
                    if d_miot_did:
                        devices_by_miot_did[d_miot_did] = device
                    if d_name:
                        devices_by_name[d_name] = device

                    # Debug log
                    logger.debug(
                        f"Device: Name='{d_name}', Model='{d_hardware}', MiotDID='{d_miot_did}', UUID='{d_uuid}'"
                    )

                # Try to find device (priority: UUID > MiotDID > Name)
                found_device = None

                if target_did in devices_by_uuid:
                    found_device = devices_by_uuid[target_did]
                    logger.info(f"Matched device by UUID: {target_did}")
                elif target_did in devices_by_miot_did:
                    found_device = devices_by_miot_did[target_did]
                    logger.info(f"Matched device by MiotDID (Numeric): {target_did}")
                elif target_did in devices_by_name:
                    found_device = devices_by_name[target_did]
                    logger.info(f"Matched device by Name: {target_did}")

                if found_device:
                    # Update self.device_id to UUID for API calls
                    self.device_id = found_device.get("deviceID")
                    logger.info(
                        f"Connected to: {found_device.get('name')} (UUID: {self.device_id})"
                    )
                else:
                    # Device not found, print available devices
                    logger.error(f"Target device '{target_did}' not found in account!")
                    logger.error("Available devices:")
                    for d in devices:
                        logger.error(
                            f"  - Name: {d.get('name')} | "
                            f"ID: {d.get('miotDID', 'N/A')} | "
                            f"UUID: {d.get('deviceID')}"
                        )
                    raise ValueError(f"Device '{target_did}' not found.")

            except Exception as e:
                logger.error(f"Failed to get device list or find device: {e}")
                raise

        except Exception as e:
            logger.error(f"Failed to connect to Xiaomi account: {e}")
            logger.error("Please check MI_USER, MI_PASS, and MI_DID environment variables")
            raise

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def play_audio_url(self, audio_url: str) -> bool:
        """Play audio from URL on the speaker."""
        # Auto-connect if not connected
        if not self.service:
            await self.connect()

        assert self.service is not None  # For mypy

        try:
            logger.info(f"Playing audio from URL: {audio_url}")
            # Use MiNAService to play audio by URL (requires UUID)
            result = await self.service.play_by_url(self.device_id, audio_url)

            logger.debug(f"play_by_url result: {result}")

            # Check result
            if result is None or result == "":
                return True
            elif isinstance(result, dict):
                if result.get("code") == 0 or result.get("status") == "success":
                    return True
                else:
                    logger.error(f"API returned error: {result}")
                    return False
            return True

        except Exception as e:
            logger.error(f"Failed to play audio: {e}", exc_info=True)
            return False

    async def play_tts(self, text: str) -> bool:
        """Play text-to-speech on the speaker."""
        if not self.service:
            await self.connect()

        assert self.service is not None  # For mypy

        try:
            logger.info(f"Playing TTS: {text}")
            result = await self.service.text_to_speech(self.device_id, text)
            logger.info(f"TTS playback initiated: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to play TTS: {e}")
            return False

    async def set_volume(self, volume: int) -> bool:
        """Set speaker volume."""
        if not self.service:
            await self.connect()

        assert self.service is not None  # For mypy

        if not 0 <= volume <= 100:
            logger.error(f"Invalid volume level: {volume}")
            return False

        try:
            logger.info(f"Setting volume to: {volume}")
            result = await self.service.player_set_volume(self.device_id, volume)
            logger.info(f"Volume set: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
