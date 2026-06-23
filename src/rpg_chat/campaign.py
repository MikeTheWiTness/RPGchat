from rpg_chat.types import CampaignBackground
from rpg_chat.llm import LLMGateway


class CampaignBackgroundParser:
    SHORT_TEXT_THRESHOLD = 200

    def __init__(self, llm: LLMGateway):
        self._llm = llm

    def parse(self, user_input: str) -> CampaignBackground:
        if len(user_input) < self.SHORT_TEXT_THRESHOLD:
            data = self._llm.expand_campaign_background(user_input)
        else:
            data = self._llm.extract_campaign_background(user_input)

        return CampaignBackground(
            raw_input=user_input,
            world_setting=data.get("world_setting", ""),
            factions=data.get("factions", []),
            history=data.get("history", []),
            important_locations=data.get("important_locations", []),
            initial_situation=data.get("initial_situation", ""),
        )

    def get_world_info(self, background: CampaignBackground) -> str:
        return background.world_setting

    def get_faction(
        self, background: CampaignBackground, name: str
    ) -> dict | None:
        for faction in background.factions:
            if faction.get("name") == name:
                return faction
        return None

    def get_history_period(
        self, background: CampaignBackground, period: str
    ) -> dict | None:
        for h in background.history:
            if h.get("period") == period:
                return h
        return None
