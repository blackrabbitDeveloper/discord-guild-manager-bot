from dataclasses import dataclass, field


@dataclass
class RaidData:
    boss: str
    max_members: int
    creator_id: int
    participants: list[int] = field(default_factory=list)
    waitlist: list[int] = field(default_factory=list)

    def add_member(self, user_id: int) -> str:
        if user_id in self.participants or user_id in self.waitlist:
            return "already_joined"
        if len(self.participants) < self.max_members:
            self.participants.append(user_id)
            return "joined"
        self.waitlist.append(user_id)
        return "waitlisted"

    def remove_member(self, user_id: int) -> int | None:
        if user_id in self.participants:
            self.participants.remove(user_id)
            if self.waitlist:
                promoted = self.waitlist.pop(0)
                self.participants.append(promoted)
                return promoted
            return None
        if user_id in self.waitlist:
            self.waitlist.remove(user_id)
        return None
