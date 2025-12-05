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
        # 初始时，self.device_id 存储的是用户配置的值（可能是数字ID、UUID或名称）
        # 在 connect() 成功后，它会被更新为真实的 UUID
        self.device_id = str(settings.mi_did)
        logger.info(f"Configured device identifier: {self.device_id}")
        
        self.account: Optional[MiAccount] = None
        self.service: Optional[MiNAService] = None
        self.session: Optional[ClientSession] = None

    async def connect(self) -> None:
        """Connect to Xiaomi account and initialize MiNA service."""
        try:
            logger.info("Connecting to Xiaomi account...")
            
            if not self.session:
                self.session = ClientSession()
            
            self.account = MiAccount(
                session=self.session,
                username=settings.mi_user,
                password=settings.mi_pass
            )
            self.service = MiNAService(self.account)
            
            # Get device list to find the correct UUID
            try:
                devices = await self.service.device_list()
                logger.info(f"Found {len(devices)} devices attached to account")
                
                target_did = self.device_id
                found_device = None
                
                # 遍历查找匹配的设备
                for device in devices:
                    # 提取设备信息
                    d_name = device.get('name', 'Unknown')
                    d_uuid = device.get('deviceID', '')           # 真实控制用的 UUID
                    d_miot_did = str(device.get('miotDID', ''))   # 数字 ID (米家APP里看到的)
                    d_hardware = device.get('hardware', '')       # 硬件型号
                    
                    # 调试日志：打印每个设备的信息以便排查
                    logger.debug(f"Checking device: Name='{d_name}', Model='{d_hardware}', MiotDID='{d_miot_did}', UUID='{d_uuid}'")
                    
                    # 匹配逻辑 (优先级: UUID > 数字ID > 名称)
                    if target_did == d_uuid:
                        found_device = device
                        logger.info(f"Matched device by UUID: {target_did}")
                        break
                    
                    if target_did == d_miot_did:
                        found_device = device
                        logger.info(f"Matched device by MiotDID (Numeric): {target_did}")
                        break
                        
                    if target_did == d_name:
                        found_device = device
                        logger.info(f"Matched device by Name: {target_did}")
                        break

                if found_device:
                    # 重要：将 self.device_id 更新为 UUID，因为后续 API 调用只认 UUID
                    self.device_id = found_device.get('deviceID')
                    logger.info(f"Connected to: {found_device.get('name')} (UUID: {self.device_id})")
                else:
                    # 如果没找到，打印所有可用设备，帮助用户修正配置
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
            logger.error(f"Please check MI_USER, MI_PASS, and MI_DID environment variables")
            raise

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def play_audio_url(self, audio_url: str) -> bool:
        """Play audio from URL on the speaker."""
        if not self.service:
            await self.connect()

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
