
# from rasa_core.trackers import DialogueStateTracker
# from rasa_core.domain import Domain
import numpy as np
from rasa_core.actions import Action
from rasa_core.events import Event, SlotSet


class Plan(object):
    """Next action to be taken in response to a dialogue state."""

    def next_action_idx(self, tracker, domain):
        # type: (DialogueStateTracker, Domain) -> List[Event]
        """
        Choose an action idx given the current state of the tracker and the plan.

        Args:
            tracker (DialogueStateTracker): the state tracker for the current user.
                You can access slot values using ``tracker.get_slot(slot_name)``
                and the most recent user message is ``tracker.latest_message.text``.
            domain (Domain): the bot's domain

        Returns:
            idx: the index of the next planned action in the domain

        """

        raise NotImplementedError

    def __str__(self):
        return "Plan('{}')".format(self.name)


class SimpleForm(Plan):
    def __init__(self, name, required_slots, finish_action, optional_slots=None, exit_dict=None, chitchat_dict=None, details_intent=None, rules=None):
        self.name = name
        self.required_slots = required_slots
        self.optional_slots = optional_slots
        # exit dict is {exit_intent_name: exit_action_name}
        self.exit_dict = exit_dict
        self.chitchat_dict = chitchat_dict
        self.finish_action = finish_action
        self.details_intent = details_intent
        self.rules = self._process_rules(rules)
        self.last_question = None

    def _process_rules(self, rules):
        print(rules)
        rule_dict = {}
        for slot, values in rules[0].items():
            print(values)
            for value, rules in values.items():
                print(value)
                rule_dict[(slot, value[0])] = (value.get('need'), value.get('lose'))
        print(rule_dict)
        exit()

    def _update_requirements(self, tracker):
        #type: (DialogueStateTracker)
        if self.rules is None:
            return
        print(self.rules)
        print(list(tracker.current_slot_values().items()))


    def next_action_idx(self, tracker, domain):
        # type: (DialogueStateTracker, Domain) -> int
        intent = tracker.latest_message.parse_data['intent']['name']
        self._update_requirements(tracker)
        exit()
        if "utter_ask_" in tracker.latest_action_name or tracker.latest_action_name in self.exit_dict.values():
            return domain.index_for_action('action_listen')

        # for v0.1 lets assume that the entities are same as slots so they are already set
        if intent in self.exit_dict.keys():
            # actions in this dict should deactivate this plan in the tracker
            return domain.index_for_action(self.exit_dict[intent])
        elif intent in self.chitchat_dict.keys() and tracker.latest_action_name not in self.chitchat_dict.values():
            return domain.index_for_action(self.chitchat_dict[intent])
        elif intent in self.details_intent and 'utter_explain' not in tracker.latest_action_name:
            return domain.index_for_action("utter_explain_{}_restaurant".format(self.last_question))

        current_filled_slots = [key for key, value in tracker.current_slot_values().items() if value is not None]
        still_to_ask = list(set(self.required_slots) - set(current_filled_slots))

        if len(still_to_ask) == 0:
            return domain.index_for_action(self.finish_action)
        else:
            if intent not in self.details_intent:
                self.last_question = np.random.choice(still_to_ask)
            return domain.index_for_action("utter_ask_{}".format(self.last_question))

    def as_dict(self):
        return {"name": self.name,
                "required_slots": self.required_slots,
                "optional_slots": self.optional_slots,
                "finish_action": self.finish_action,
                "exit_dict": self.exit_dict,
                "chitchat_dict": self.chitchat_dict,
                "details_intent": self.details_intent,
                "rules": self.rules}


class ActivatePlan(Action):
    def __init__(self):
        self._name = 'activate_plan'

    def run(self, dispatcher, tracker, domain):
        """Simple run implementation uttering a (hopefully defined) template."""
        # tracker.activate_plan(domain)
        return [StartPlan(domain), SlotSet('active_plan', True)]

    def name(self):
        return self._name

    def __str__(self):
        return "ActivatePlan('{}')".format(self.name())


class PlanComplete(Action):
    def __init__(self):
        self._name = 'deactivate_plan'

    def run(self, dispatcher, tracker, domain):
        return [EndPlan(), SlotSet('active_plan', False)]

    def name(self):
        return self._name

    def __str__(self):
        return "PlanComplete('{}')".format(self.name())


class StartPlan(Event):
    def __init__(self, domain):
        super(StartPlan).__init__()
        self.plan = domain._plans

    def apply_to(self, tracker):
        # type: (DialogueStateTracker) -> None
        tracker.activate_plan(self.plan)

    def as_story_string(self):
        return None


class EndPlan(Event):
    def apply_to(self, tracker):
        tracker.deactivate_plan()

    def as_story_string(self):
        return None