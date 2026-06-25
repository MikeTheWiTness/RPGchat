from dataclasses import dataclass, field

from rpg_chat.types import PlotOutline, PlotChapter, PlotEvent


@dataclass
class PlotTracker:
    outline: PlotOutline | None = None
    current_chapter_id: str = ""
    completed_events: set[str] = field(default_factory=set)
    discovered_clues: list[str] = field(default_factory=list)

    @classmethod
    def from_outline(cls, outline: PlotOutline | None) -> "PlotTracker":
        tracker = cls(outline=outline)
        if outline and outline.chapters:
            tracker.current_chapter_id = outline.chapters[0].id
        return tracker

    def get_current_chapter(self) -> PlotChapter | None:
        if not self.outline:
            return None
        for ch in self.outline.chapters:
            if ch.id == self.current_chapter_id:
                return ch
        return None

    def get_current_context(self) -> str:
        """返回当前剧情阶段的 LLM 可读摘要。"""
        if not self.outline:
            return ""

        parts = []
        if self.outline.title:
            parts.append(f"剧情大纲: {self.outline.title}")

        chapter = self.get_current_chapter()
        if chapter:
            parts.append(f"当前章节: {chapter.title}")
            if chapter.summary:
                parts.append(f"章节概要: {chapter.summary}")

            # 关键事件
            pending_events = [
                e for e in chapter.key_events
                if e.id not in self.completed_events
            ]
            if pending_events:
                ev_lines = "\n".join(
                    f"  - [{e.id}] {e.description}"
                    + (f" (触发: {e.trigger})" if e.trigger else "")
                    for e in pending_events
                )
                parts.append(f"待发生的关键事件:\n{ev_lines}")

            completed = [
                e for e in chapter.key_events
                if e.id in self.completed_events
            ]
            if completed:
                ev_lines = "\n".join(f"  - {e.description}" for e in completed)
                parts.append(f"已完成事件:\n{ev_lines}")

            # 可发现的线索
            if chapter.clues:
                clues_available = [
                    c for c in chapter.clues
                    if c not in self.discovered_clues
                ]
                if clues_available:
                    parts.append(f"可安排出现的线索: {', '.join(clues_available)}")

            # 完结方向
            if chapter.possible_transitions:
                parts.append(
                    f"本章可导向的下一阶段: {', '.join(chapter.possible_transitions)}"
                )

        # 可能结局
        if self.outline.possible_endings:
            parts.append(
                f"可能的结局方向: {', '.join(self.outline.possible_endings)}"
            )

        return "\n".join(parts)

    def mark_event_completed(self, event_id: str):
        self.completed_events.add(event_id)

    def discover_clue(self, clue: str):
        if clue not in self.discovered_clues:
            self.discovered_clues.append(clue)

    def try_advance_chapter(self, new_chapter_id: str) -> bool:
        """尝试推进到新章节。返回是否成功。"""
        if not self.outline:
            return False
        chapter = self.get_current_chapter()
        if chapter and new_chapter_id in chapter.possible_transitions:
            self.current_chapter_id = new_chapter_id
            return True
        # 也允许直接跳转到任意章节
        for ch in self.outline.chapters:
            if ch.id == new_chapter_id:
                self.current_chapter_id = new_chapter_id
                return True
        return False

    def snapshot(self) -> dict:
        return {
            "current_chapter_id": self.current_chapter_id,
            "completed_events": list(self.completed_events),
            "discovered_clues": list(self.discovered_clues),
        }

    def restore(self, data: dict):
        self.current_chapter_id = data.get("current_chapter_id", "")
        self.completed_events = set(data.get("completed_events", []))
        self.discovered_clues = list(data.get("discovered_clues", []))
