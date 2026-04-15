from cogs.raid import PartyData


class TestPartyData:
    def test_add_participant_within_capacity(self):
        party = PartyData(activity="발탄", max_members=2, creator_id=1)
        result = party.add_member(100)
        assert result == "joined"
        assert 100 in party.participants

    def test_add_participant_over_capacity(self):
        party = PartyData(activity="발탄", max_members=1, creator_id=1)
        party.add_member(100)
        result = party.add_member(200)
        assert result == "waitlisted"
        assert 200 in party.waitlist
        assert 200 not in party.participants

    def test_duplicate_participant_rejected(self):
        party = PartyData(activity="발탄", max_members=2, creator_id=1)
        party.add_member(100)
        result = party.add_member(100)
        assert result == "already_joined"

    def test_remove_participant_promotes_waitlist(self):
        party = PartyData(activity="발탄", max_members=1, creator_id=1)
        party.add_member(100)
        party.add_member(200)  # waitlisted
        promoted = party.remove_member(100)
        assert promoted == 200
        assert 200 in party.participants
        assert 100 not in party.participants

    def test_remove_participant_no_waitlist(self):
        party = PartyData(activity="발탄", max_members=2, creator_id=1)
        party.add_member(100)
        promoted = party.remove_member(100)
        assert promoted is None
        assert 100 not in party.participants

    def test_remove_waitlisted_member(self):
        party = PartyData(activity="발탄", max_members=1, creator_id=1)
        party.add_member(100)
        party.add_member(200)  # waitlisted
        promoted = party.remove_member(200)
        assert promoted is None
        assert 200 not in party.waitlist

    def test_description_field(self):
        party = PartyData(activity="발탄", max_members=4, creator_id=1, description="밤 9시 하드모드")
        assert party.description == "밤 9시 하드모드"
