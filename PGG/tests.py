from otree.api import Bot, SubmissionMustFail

from . import Contribute, Constants, FinalResults, Instructions, Results



class PlayerBot(Bot):

    cases = ['basic', 'min', 'max']

    def play_round(self):
        case = self.case
        if self.player.round_number == 1:
            yield Instructions

        if case == 'basic':
            if self.player.id_in_group == 1:
                for invalid_contribution in [-1, 101]:
                    yield SubmissionMustFail(Contribute, {'choice': invalid_contribution})

        contribution = {
            'min': 0,
            'max': 100,
            'basic': 50,
        }[case]

        yield (Contribute, {'choice': contribution})

        yield Results

        if self.player.round_number == Constants.num_rounds:
            yield FinalResults

        if self.player.id_in_group == 1:

            if case == 'min':
                expected_payoff = 100
            elif case == 'max':
                expected_payoff = 200
            else:
                expected_payoff = 150
            assert self.player.payoff == expected_payoff
