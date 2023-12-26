from rest_framework.test import APIRequestFactory, force_authenticate, APITransactionTestCase
from .factories import PollFactory, PollProposalFactory
from .utils import generate_poll_phase_kwargs
from ..models import PollDelegateVoting, PollVotingTypeCardinal, Poll, PollProposal, PollVoting
from ..services.vote import poll_proposal_vote_count
from ..views.vote import (PollProposalDelegateVoteUpdateAPI,
                          PollProposalVoteUpdateAPI,
                          PollProposalVoteListAPI,
                          DelegatePollVoteListAPI)
from ...files.tests.factories import FileSegmentFactory
from ...group.tests.factories import GroupFactory, GroupUserFactory, GroupUserDelegateFactory, GroupTagsFactory
from ...user.models import User


class PollVoteTest(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.group = GroupFactory()
        self.group_tag = GroupTagsFactory(group=self.group)
        self.group_user_creator = GroupUserFactory(group=self.group, user=self.group.created_by)
        (self.group_user_one,
         self.group_user_two,
         self.group_user_three) = GroupUserFactory.create_batch(3, group=self.group)
        self.poll_schedule = PollFactory(created_by=self.group_user_one, poll_type=Poll.PollType.SCHEDULE,
                                         tag=GroupTagsFactory(group=self.group), **generate_poll_phase_kwargs('vote'))
        self.poll_cardinal = PollFactory(created_by=self.group_user_one, poll_type=Poll.PollType.CARDINAL,
                                         tag=GroupTagsFactory(group=self.group), **generate_poll_phase_kwargs('vote'))
        self.group_users = [self.group_user_one, self.group_user_two, self.group_user_three]
        (self.poll_schedule_proposal_one,
         self.poll_schedule_proposal_two,
         self.poll_schedule_proposal_three) = [PollProposalFactory(created_by=x,
                                                                   poll=self.poll_schedule) for x in self.group_users]
        (self.poll_cardinal_proposal_one,
         self.poll_cardinal_proposal_two,
         self.poll_cardinal_proposal_three) = [PollProposalFactory(created_by=x,
                                                                   poll=self.poll_cardinal) for x in self.group_users]

    @staticmethod
    def cardinal_vote_update(user: User, poll: Poll, proposals: list[PollProposal], scores: list[int]):
        factory = APIRequestFactory()
        view = PollProposalVoteUpdateAPI.as_view()
        data = dict(proposals=[x.id for x in proposals], scores=scores)
        request = factory.post('', data=data)
        force_authenticate(request, user)
        return view(request, poll=poll.id)

    def test_vote_update_cardinal(self):
        user = self.group_user_one.user
        proposals = [self.poll_cardinal_proposal_three, self.poll_cardinal_proposal_one]
        scores = [23, 980]
        response = self.cardinal_vote_update(user, self.poll_cardinal, proposals, scores)

        self.assertEqual(response.status_code, 200, response.data)

        voting_account = PollVoting.objects.get(created_by=self.group_user_one)
        self.assertEqual(PollVotingTypeCardinal.objects.get(author=voting_account,
                                                            proposal_id=proposals[0].id).score, scores[0])
        self.assertEqual(PollVotingTypeCardinal.objects.get(author=voting_account,
                                                            proposal_id=proposals[1].id).score, scores[1])

    def test_vote_update_cardinal_reset(self):
        self.test_vote_update_cardinal()

        user = self.group_user_one.user
        proposals = [self.poll_cardinal_proposal_one,
                     self.poll_cardinal_proposal_three,
                     self.poll_cardinal_proposal_two]
        scores = [91, 74, 228]
        response = self.cardinal_vote_update(user, self.poll_cardinal, proposals, scores)

        self.assertEqual(response.status_code, 200, response.data)
        voting_account = PollVoting.objects.get(created_by=self.group_user_one)

        for x in range(3):
            self.assertEqual(PollVotingTypeCardinal.objects.get(author=voting_account,
                                                                proposal_id=proposals[x].id).score, scores[x])

    def test_vote_update_cardinal_duplicate(self):
        user = self.group_user_one.user
        proposals = [self.poll_cardinal_proposal_three,
                     self.poll_cardinal_proposal_one,
                     self.poll_cardinal_proposal_one]
        scores = [23, 980, 22]
        response = self.cardinal_vote_update(user, self.poll_cardinal, proposals, scores)

        self.assertEqual(response.status_code, 400)

    def test_vote_count_cardinal(self):
        user = self.group_user_two.user
        proposals = [self.poll_cardinal_proposal_two, self.poll_cardinal_proposal_three]
        scores = [78, 22]
        response = self.cardinal_vote_update(user, self.poll_cardinal, proposals, scores)
        self.assertEqual(response.status_code, 200, response.data)

        user = self.group_user_one.user
        proposals = [self.poll_cardinal_proposal_three, self.poll_cardinal_proposal_one]
        scores = [23, 980]
        response = self.cardinal_vote_update(user, self.poll_cardinal, proposals, scores)
        self.assertEqual(response.status_code, 200, response.data)

        user = self.group_user_three.user
        proposals = [self.poll_cardinal_proposal_three, self.poll_cardinal_proposal_two]
        scores = [14, 86]
        response = self.cardinal_vote_update(user, self.poll_cardinal, proposals, scores)
        self.assertEqual(response.status_code, 200, response.data)

        Poll.objects.filter(id=self.poll_cardinal.id).update(**generate_poll_phase_kwargs('result'))
        poll_proposal_vote_count(poll_id=self.poll_cardinal.id)

        self.poll_cardinal_proposal_one.refresh_from_db()
        self.poll_cardinal_proposal_two.refresh_from_db()
        self.poll_cardinal_proposal_three.refresh_from_db()

        self.assertEqual(self.poll_cardinal_proposal_one.score, 980)
        self.assertEqual(self.poll_cardinal_proposal_two.score, 164)
        self.assertEqual(self.poll_cardinal_proposal_three.score, 59)

    @staticmethod
    def schedule_vote_update(user: User, poll: Poll, proposals: list[PollProposal]):
        factory = APIRequestFactory()
        view = PollProposalVoteUpdateAPI.as_view()
        data = dict(proposals=[x.id for x in proposals])
        request = factory.post('', data=data)
        force_authenticate(request, user)
        return view(request, poll=poll.id)

    def test_vote_count_schedule(self):
        user = self.group_user_two.user
        proposals = [self.poll_schedule_proposal_two, self.poll_schedule_proposal_three]
        response = self.schedule_vote_update(user, self.poll_schedule, proposals)
        self.assertEqual(response.status_code, 200, response.data)

        user = self.group_user_one.user
        proposals = [self.poll_schedule_proposal_three, self.poll_schedule_proposal_one]
        response = self.schedule_vote_update(user, self.poll_schedule, proposals)
        self.assertEqual(response.status_code, 200, response.data)

        user = self.group_user_three.user
        proposals = [self.poll_schedule_proposal_three, self.poll_schedule_proposal_two]
        response = self.schedule_vote_update(user, self.poll_schedule, proposals)
        self.assertEqual(response.status_code, 200, response.data)

        Poll.objects.filter(id=self.poll_schedule.id).update(**generate_poll_phase_kwargs('result'))
        poll_proposal_vote_count(poll_id=self.poll_schedule.id)

        self.poll_schedule_proposal_one.refresh_from_db()
        self.poll_schedule_proposal_two.refresh_from_db()
        self.poll_schedule_proposal_three.refresh_from_db()

        self.assertEqual(self.poll_schedule_proposal_one.score, 1)
        self.assertEqual(self.poll_schedule_proposal_two.score, 2)
        self.assertEqual(self.poll_schedule_proposal_three.score, 3)


class PollDelegateVoteTest(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.group = GroupFactory()
        self.group_user_creator = GroupUserFactory(group=self.group)
        self.delegate = GroupUserDelegateFactory(group=self.group)
        self.delegator = GroupUserFactory(group=self.group)
        (self.poll_one,
         self.poll_two,
         self.poll_three) = [PollFactory(created_by=self.group_user_creator, poll_type=4,
                                         **generate_poll_phase_kwargs('delegate_vote')) for x in range(3)]
        segment = FileSegmentFactory()
        self.poll_three.attachments = segment.collection
        self.poll_three.save()

    def test_delegate_vote(self):
        factory = APIRequestFactory()
        user = self.delegate.group_user.user
        view = PollProposalDelegateVoteUpdateAPI.as_view()

        (proposal_one,
         proposal_two) = [PollProposalFactory(created_by=self.group_user_creator, poll=self.poll_one) for x in range(2)]

        data = dict(proposals=[proposal_two.id, proposal_one.id], scores=[100, 25])

        request = factory.post('', data)
        force_authenticate(request, user=user)
        view(request, poll=self.poll_one.id)

        votes = PollDelegateVoting.objects.get(created_by=self.delegate.pool).pollvotingtypecardinal_set
        self.assertEqual(votes.filter(id__in=data['proposals']).count(), 2)
