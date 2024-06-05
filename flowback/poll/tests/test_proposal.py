import json

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.test import APIRequestFactory, force_authenticate, APITransactionTestCase
from .factories import PollFactory, PollProposalFactory, PollProposalPriorityFactory

from .utils import generate_poll_phase_kwargs
from ..models import PollProposal, Poll, PollProposalPriority
from ..selectors.proposal import poll_proposal_list
from ..views.proposal import PollProposalListAPI, PollProposalCreateAPI, PollProposalDeleteAPI, \
    PollProposalPriorityUpdateAPI
from ..views.poll import PollListApi
from ...group.tests.factories import GroupFactory, GroupUserFactory, GroupTagsFactory, GroupPermissionsFactory
from ...schedule.models import ScheduleEvent
from ...user.models import User


class ProposalTest(APITransactionTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.group = GroupFactory()
        self.group_tag = GroupTagsFactory(group=self.group)
        self.group_user_creator = GroupUserFactory(group=self.group, user=self.group.created_by)
        (self.group_user_one,
         self.group_user_two,
         self.group_user_three) = GroupUserFactory.create_batch(3, group=self.group)
        self.poll_schedule = PollFactory(created_by=self.group_user_one, poll_type=Poll.PollType.SCHEDULE,
                                         **generate_poll_phase_kwargs('proposal'))
        self.poll_cardinal = PollFactory(created_by=self.group_user_one, poll_type=Poll.PollType.CARDINAL,
                                         **generate_poll_phase_kwargs('proposal'))
        group_users = [self.group_user_one, self.group_user_two, self.group_user_three]
        (self.poll_schedule_proposal_one,
         self.poll_schedule_proposal_two,
         self.poll_schedule_proposal_three) = [PollProposalFactory(created_by=x,
                                                                   poll=self.poll_schedule) for x in group_users]
        (self.poll_cardinal_proposal_one,
         self.poll_cardinal_proposal_two,
         self.poll_cardinal_proposal_three) = [PollProposalFactory(created_by=x,
                                                                   poll=self.poll_cardinal) for x in group_users]

    def test_proposal_list_cardinal(self):
        factory = APIRequestFactory()
        user = self.group_user_one.user
        view = PollProposalListAPI.as_view()
        request = factory.get('')
        force_authenticate(request, user=user)

        response = view(request, poll=self.poll_cardinal.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 3)

    def test_proposal_list_schedule(self):
        factory = APIRequestFactory()
        user = self.group_user_one.user
        view = PollProposalListAPI.as_view()
        request = factory.get('')
        force_authenticate(request, user=user)

        response = view(request, poll=self.poll_schedule.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 3)


    def _vote_on_poll(self, user,proposal_id,score=1):
        view = PollProposalPriorityUpdateAPI.as_view()
        request = self.factory.post('', data=dict(score=score))
        force_authenticate(request, user.user)
        return view(request, proposal_id=proposal_id)

    def test_poll_changes_to_finalization_after_meeting_proposal_quoram_approval(self):
        poll = PollFactory(
            created_by=self.group_user_creator, 
            **generate_poll_phase_kwargs(poll_start_phase='proposal'),
            description="test poll termination"
        )
        poll_proposal = PollProposalFactory(poll=poll)
        
        # Simulate voting by group members
        users = [
            self.group_user_creator,
            self.group_user_one,
            self.group_user_two,
            self.group_user_three
        ]
        for user in users:
            self._vote_on_poll(user, poll_proposal.id)

        request = self.factory.get('')
        force_authenticate(request, self.group_user_creator.user)
        poll_list_api_view = PollListApi.as_view()
        response = poll_list_api_view(request, group_id=self.group.id)

        response_data = json.loads(response.rendered_content)
        self.assertTrue(len(response_data['results']) == 3)

        poll_status = next((result['status'] for result in response_data['results'] if result['id'] == poll.id), None)
        self.assertEqual(poll_status, 2)


    def test_poll_still_ongoing_without_meeting_proposal_quoram_approval(self):
        poll = PollFactory(
            created_by=self.group_user_creator, 
            **generate_poll_phase_kwargs(poll_start_phase='proposal'),
            description="test poll termination"
        )
        poll_proposal = PollProposalFactory(poll=poll)
        
        # Simulate voting by group members
        users = [
            self.group_user_creator,
            self.group_user_one,
        ]
        for user in users:
            self._vote_on_poll(user, poll_proposal.id)

        request = self.factory.get('')
        force_authenticate(request, self.group_user_creator.user)
        poll_list_api_view = PollListApi.as_view()
        response = poll_list_api_view(request, group_id=self.group.id)

        response_data = json.loads(response.rendered_content)
        self.assertTrue(len(response_data['results']) == 3)

        poll_status = next((result['status'] for result in response_data['results'] if result['id'] == poll.id), None)
        self.assertEqual(poll_status, 0)

    def test_finalization_poll_changes_to_ongoing_after_downvoting(self):
        poll = PollFactory(
            created_by=self.group_user_creator, 
            **generate_poll_phase_kwargs(poll_start_phase='proposal'),
            description="test poll termination"
        )
        poll_proposal = PollProposalFactory(poll=poll)
        
        # Simulate voting by group members
        users = [
            self.group_user_creator,
            self.group_user_one,
            self.group_user_two,
            self.group_user_three
        ]
        for user in users:
            self._vote_on_poll(user, poll_proposal.id)

        # Downvote by a two users
        self._vote_on_poll(self.group_user_three, poll_proposal.id, score=-1)
        self._vote_on_poll(self.group_user_two, poll_proposal.id, score=-1)

        request = self.factory.get('')
        force_authenticate(request, self.group_user_creator.user)
        poll_list_api_view = PollListApi.as_view()
        response = poll_list_api_view(request, group_id=self.group.id)

        response_data = json.loads(response.rendered_content)
        self.assertTrue(len(response_data['results']) == 3)

        poll_status = next((result['status'] for result in response_data['results'] if result['id'] == poll.id), None)
        self.assertEqual(poll_status, 0)


    @staticmethod
    def proposal_create(user: User,
                        poll: Poll,
                        title: str,
                        description: str,
                        event__start_date=None,
                        attachments=None,
                        event__end_date=None):
        factory = APIRequestFactory()
        view = PollProposalCreateAPI.as_view()
        data = {x: y for x, y in
                dict(title=title, description=description, start_date=event__start_date, end_date=event__end_date,
                     attachments=attachments).items() if y is not None}
        request = factory.post('', data=data)
        force_authenticate(request, user)
        return view(request, poll=poll.id)

    def test_proposal_create(self):
        response = self.proposal_create(user=self.group_user_one.user, poll=self.poll_cardinal,
                                        title='Test Proposal', description='Test')

        self.assertEqual(response.status_code, 200, response.data)
        proposal = PollProposal.objects.get(id=int(response.data))

        self.assertEqual(proposal.title, 'Test Proposal')
        self.assertEqual(proposal.description, 'Test')

    def test_proposal_create_schedule(self):
        start_date = timezone.now() + timezone.timedelta(hours=1)
        end_date = timezone.now() + timezone.timedelta(hours=2)
        response = self.proposal_create(user=self.group_user_one.user, poll=self.poll_schedule,
                                        title='Test Proposal', description='Test',
                                        event__start_date=start_date, event__end_date=end_date)

        self.assertEqual(response.status_code, 200, response.data)
        proposal = PollProposal.objects.get(id=int(response.data))

        self.assertEqual(proposal.title, 'Test Proposal')
        self.assertEqual(proposal.description, 'Test')
        self.assertEqual(proposal.pollproposaltypeschedule.event.start_date, start_date)
        self.assertEqual(proposal.pollproposaltypeschedule.event.end_date, end_date)

        response = self.proposal_create(user=self.group_user_one.user, poll=self.poll_schedule,
                                        title='Test Proposal', description='Test',
                                        event__start_date=start_date, event__end_date=end_date)

        self.assertRaises(ObjectDoesNotExist, PollProposal.objects.get, id=proposal.id+1)

    def test_proposal_create_no_schedule_data(self):
        response = self.proposal_create(user=self.group_user_one.user, poll=self.poll_schedule,
                                        title='Test Proposal', description='Test')

        self.assertEqual(response.status_code, 400)

    @staticmethod
    def proposal_delete(proposal, user):
        factory = APIRequestFactory()
        view = PollProposalDeleteAPI.as_view()
        request = factory.post('')
        force_authenticate(request, user=user)

        return view(request, proposal=proposal.id)

    def test_proposal_delete(self):
        user = self.group_user_one.user
        proposal = self.poll_cardinal_proposal_one

        response = self.proposal_delete(proposal, user)
        self.assertEqual(response.status_code, 200, response.data)

    def test_proposal_delete_no_permission(self):
        self.group_user_one.permission = GroupPermissionsFactory(author=self.group_user_one.group,
                                                                 delete_proposal=False)
        self.group_user_one.save()
        user = self.group_user_one.user
        proposal = self.poll_cardinal_proposal_one

        response = self.proposal_delete(proposal, user)
        self.assertEqual(response.status_code, 400)

    def test_proposal_delete_admin(self):
        user = self.group_user_creator.user
        proposal = self.poll_cardinal_proposal_one

        response = self.proposal_delete(proposal, user)
        self.assertEqual(response.status_code, 200, response.data)

    def test_proposal_schedule_delete(self):
        user = self.group_user_one.user
        proposal = self.poll_schedule_proposal_one
        event_id = proposal.pollproposaltypeschedule.event.id

        response = self.proposal_delete(proposal, user)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ScheduleEvent.objects.filter(id=event_id).exists())

    def test_proposal_schedule_delete_no_permission(self):
        self.group_user_one.permission = GroupPermissionsFactory(author=self.group_user_one.group,
                                                                 delete_proposal=False)
        self.group_user_one.save()
        user = self.group_user_one.user
        proposal = self.poll_schedule_proposal_one
        event_id = proposal.pollproposaltypeschedule.event.id

        response = self.proposal_delete(proposal, user)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ScheduleEvent.objects.filter(id=event_id).exists())

    def test_proposal_schedule_delete_admin(self):
        user = self.group_user_creator.user
        proposal = self.poll_schedule_proposal_one
        event_id = proposal.pollproposaltypeschedule.event.id
        self.assertTrue(ScheduleEvent.objects.filter(id=event_id).exists())

        response = self.proposal_delete(proposal, user)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(ScheduleEvent.objects.filter(id=event_id).exists())

    def test_poll_proposal_priority_list(self):
        vote_one = PollProposalPriorityFactory(proposal=self.poll_cardinal_proposal_one,
                                               group_user=self.group_user_one, score=1)
        vote_two = PollProposalPriorityFactory(proposal=self.poll_cardinal_proposal_one,
                                               group_user=self.group_user_two, score=1)
        vote_three = PollProposalPriorityFactory(proposal=self.poll_cardinal_proposal_one,
                                                 group_user=self.group_user_three, score=-1)

        proposals = poll_proposal_list(fetched_by=self.group_user_one.user, poll_id=self.poll_cardinal.id)

        self.assertEqual(proposals.get(id=self.poll_cardinal_proposal_one.id).priority, 1)
        self.assertEqual(proposals.get(id=self.poll_cardinal_proposal_two.id).priority, 0)
        self.assertEqual(proposals.get(id=self.poll_cardinal_proposal_one.id).user_priority, 1)
        self.assertEqual(proposals.get(id=self.poll_cardinal_proposal_two.id).user_priority, None)

    def test_poll_proposal_priority_update(self):
        def vote(score: int):
            factory = APIRequestFactory()
            view = PollProposalPriorityUpdateAPI.as_view()
            data = dict(score=score)
            request = factory.post('', data=data)
            force_authenticate(request, user=self.group_user_one.user)
            view(request, proposal_id=self.poll_cardinal_proposal_one.id)

            if score != 0:
                self.assertEqual(PollProposalPriority.objects.get(proposal_id=self.poll_cardinal_proposal_one.id,
                                                                  group_user=self.group_user_one).score, score)

            else:
                self.assertFalse(PollProposalPriority.objects.filter(proposal_id=self.poll_cardinal_proposal_one.id,
                                                                     group_user=self.group_user_one).exists())

        vote(1)
        vote(-1)
        vote(0)

    