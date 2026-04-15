import pytest
from cogs.raid import RaidData


class TestRaidData:
    def test_add_participant_within_capacity(self):
        raid = RaidData(boss="발탄", max_members=2, creator_id=1)
        result = raid.add_member(100)
        assert result == "joined"
        assert 100 in raid.participants

    def test_add_participant_over_capacity(self):
        raid = RaidData(boss="발탄", max_members=1, creator_id=1)
        raid.add_member(100)
        result = raid.add_member(200)
        assert result == "waitlisted"
        assert 200 in raid.waitlist
        assert 200 not in raid.participants

    def test_duplicate_participant_rejected(self):
        raid = RaidData(boss="발탄", max_members=2, creator_id=1)
        raid.add_member(100)
        result = raid.add_member(100)
        assert result == "already_joined"

    def test_remove_participant_promotes_waitlist(self):
        raid = RaidData(boss="발탄", max_members=1, creator_id=1)
        raid.add_member(100)
        raid.add_member(200)  # waitlisted
        promoted = raid.remove_member(100)
        assert promoted == 200
        assert 200 in raid.participants
        assert 100 not in raid.participants

    def test_remove_participant_no_waitlist(self):
        raid = RaidData(boss="발탄", max_members=2, creator_id=1)
        raid.add_member(100)
        promoted = raid.remove_member(100)
        assert promoted is None
        assert 100 not in raid.participants

    def test_remove_waitlisted_member(self):
        raid = RaidData(boss="발탄", max_members=1, creator_id=1)
        raid.add_member(100)
        raid.add_member(200)  # waitlisted
        promoted = raid.remove_member(200)
        assert promoted is None
        assert 200 not in raid.waitlist
