from otree.api import Bot, SubmissionMustFail

from . import C, Guess, Introduction, Results


class PlayerBot(Bot):
    cases = ['p1_wins', 'p1_and_p2_win']

    def play_round(self):
        if self.subsession.round_number == 1:
            yield Introduction

        if self.case == 'p1_wins':
            if self.player.id_in_group == 1:
                for invalid_guess in [-1, C.GUESS_MAX + 1]:
                    yield SubmissionMustFail(Guess, {"guess": invalid_guess})
                yield (Guess, {"guess": 9})
                assert self.player.payoff == C.JACKPOT
            else:
                yield (Guess, {"guess": 10})
                assert self.player.payoff == 0
        else:
            if self.player.id_in_group in [1, 2]:
                yield (Guess, {"guess": 9})
                assert self.player.payoff == C.JACKPOT / 2
            else:
                yield (Guess, {"guess": 10})
                assert self.player.payoff == 0

        yield Results
