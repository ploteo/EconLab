from otree.api import *


doc = """
This is a oTree implementation of the "Beauty Contest" game, as described in Nagel (1995).

References:
Nagel, R. (1995). Unraveling in Guessing Games: An Experimental Study. The American Economic Review, 85(5), 1313–1326. http://www.jstor.org/stable/2950991
"""


class C(BaseConstants):
    # oTree reads these app-level constants when it builds the session.
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    NAME_IN_URL = 'beauty_contest'

    # Main game parameters.
    JACKPOT = Currency(100)
    GUESS_MAX = 100

    # The target number is average_guess * MULTIPLIER.
    # Change these two values if the game should use, for example, 1/2 or 3/4.
    MULTIPLIER_NUMERATOR = 2
    MULTIPLIER_DENOMINATOR = 3
    MULTIPLIER = MULTIPLIER_NUMERATOR / MULTIPLIER_DENOMINATOR
    MULTIPLIER_LABEL = f'{MULTIPLIER_NUMERATOR}/{MULTIPLIER_DENOMINATOR}'


DEFAULT_LANGUAGE = 'it'

# All user-facing text is stored here so the same pages can be shown in
# Italian or English depending on the session config.
TEXTS = {
    'it': dict(
        start_game='Comincia il gioco',
        guess_title='La tua stima',
        guess_intro_1='Inserisci il valore desiderato digitandolo nel campo numerico qui sotto.',
        guess_intro_2='Puoi usare le frecce su/giù o scrivere direttamente un numero nel campo.',
        guess_intro_3='Una volta scelta la stima, premi il bottone Conferma che si attiva in basso.',
        guess_aria='Inserisci un numero nel campo',
        chosen_value='Il valore scelto è',
        confirm='Conferma',
        reread_instructions='Clicca qui per rileggere le istruzioni',
        results_title='Risultati',
        average='Valore medio',
        target_value='Valore obiettivo',
        closest_number='Il numero più vicino è stato',
        your_number_was='Il tuo numero era',
        did_not_participate='Non hai partecipato al gioco',
        congratulations='Complimenti',
        you_are_one_of='Sei uno dei',
        participants_with_winning_number='partecipanti che hanno riportato il numero vincente!',
        you_won='Hai vinto!',
        you_lost='Purtroppo non hai vinto',
        finish='Concludi',
        final_results_title='Risultati finali',
        experiment_over="L'esperimento è terminato",
        total_earnings='Il tuo guadagno totale è',
    ),
    'en': dict(
        start_game='Start the game',
        guess_title='Your guess',
        guess_intro_1='Enter your chosen value in the numeric field below.',
        guess_intro_2='You can use the up/down arrows or type a number directly.',
        guess_intro_3='Once you have chosen your guess, press the Confirm button that appears below.',
        guess_aria='Enter a number in the field',
        chosen_value='The chosen value is',
        confirm='Confirm',
        reread_instructions='Click here to read the instructions again',
        results_title='Results',
        average='Average value',
        target_value='Target value',
        closest_number='The closest number was',
        your_number_was='Your number was',
        did_not_participate='You did not participate in the game',
        congratulations='Congratulations',
        you_are_one_of='You are one of the',
        participants_with_winning_number='participants who submitted the winning number!',
        you_won='You won!',
        you_lost='Unfortunately, you did not win',
        finish='Finish',
        final_results_title='Final results',
        experiment_over='The experiment is over',
        total_earnings='Your total earnings are',
    ),
}


def get_language(source):
    # Sessions can set language='it' or language='en'; otherwise fall back to Italian.
    lang = str(source.session.config.get('language', DEFAULT_LANGUAGE)).lower()
    return lang if lang in TEXTS else DEFAULT_LANGUAGE


def get_text(source):
    # Return the dictionary of translated labels used by the templates.
    return TEXTS[get_language(source)]


def get_instructions_template(source):
    # Pick the language-specific instruction partial included in multiple pages.
    return f'BEAUTY_CONTEST/Instructions_{get_language(source)}.html'


def common_template_vars(source):
    # Shared context passed to every page template.
    return dict(
        lang=get_language(source),
        t=get_text(source),
        instructions_template=get_instructions_template(source),
    )


class Subsession(BaseSubsession):
    pass


def vars_for_admin_report(subsession: Subsession):
    # Build participant rows and group summary data for the oTree admin report.
    players = subsession.get_players()
    rows = []
    guess_values = []
    for p in players:
        # A guess of -99 means the player reached timeout without submitting.
        if p.guess == -99:
            guess_display = '— (timeout)'
        elif p.guess is None:
            guess_display = '—'
        else:
            guess_display = str(p.guess)
            guess_values.append(p.guess)
        rows.append(dict(
            participant=p.participant.label or p.participant.code,
            guess=p.guess,
            guess_display=guess_display,
            is_winner=p.is_winner,
            payoff=float(p.payoff or 0),
        ))

    groups = subsession.get_groups()
    group_stats = [
        dict(
            group_id=g.id,
            target_value=g.field_maybe_none('target_value'),
            best_guess=g.field_maybe_none('best_guess'),
            num_winners=g.field_maybe_none('num_winners'),
        )
        for g in groups
    ]

    return dict(
        rows=rows,
        group_stats=group_stats,
        guess_values=guess_values,
        guess_max=C.GUESS_MAX,
        multiplier_label=C.MULTIPLIER_LABEL,
        round_number=subsession.round_number,
    )


class Group(BaseGroup):
    # Target value participants try to get closest to: average_guess * C.MULTIPLIER.
    target_value = models.FloatField()
    best_guess = models.PositiveIntegerField()
    num_winners = models.PositiveIntegerField()

class Player(BasePlayer):
    # -99 is used as a timeout sentinel so it can be excluded from payoff calculations.
    guess = models.IntegerField(initial=-99, max=C.GUESS_MAX, min=0)
    is_winner = models.BooleanField(initial=False)
    total_payoff = models.CurrencyField()
    display = models.CharField()


# FUNCTIONS
def creating_session(subsession: Subsession):
    # Initialize participant-level variables at the start of the game.
    for p in subsession.get_players():
        if subsession.round_number == 1:
            p.participant.vars['total_payoff'] = 0
            p.participant.vars['history'] = []
            p.display = "slider_50"

def set_payoffs(group: Group):
    # Called by the wait page after everyone has submitted a guess or timed out.
    players = group.get_players()
    guesses = []
    for p in players:
        if p.guess != -99:
            guesses.append(p.guess)

    # Compute the target value and find the submitted guess closest to it.
    target_value = C.MULTIPLIER * sum(guesses) / len(guesses)
    group.target_value = round(target_value, 2)
    group.best_guess = min(guesses, key=lambda guess: abs(guess - group.target_value))

    # Split the jackpot equally if several participants picked the winning number.
    winners = [p for p in players if p.guess == group.best_guess]
    group.num_winners = len(winners)
    for p in winners:
        p.is_winner = True
        p.payoff = C.JACKPOT / group.num_winners

    # Store totals and history on participant.vars so they persist across rounds.
    for p in group.get_players():
        p.participant.vars['total_payoff'] = p.participant.vars['total_payoff'] + p.payoff
        p.total_payoff = p.participant.vars['total_payoff']
        p.participant.vars['history'].append(group.target_value)


# PAGES
class Introduction(Page):
    # The introduction includes the language-specific instructions.
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return common_template_vars(player)

class Guess(Page):
    # Saves the participant's numeric guess into Player.guess.
    form_model = Player
    form_fields = ['guess']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            common_template_vars(player),
            history=player.participant.vars['history'],
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.guess = -99
       

class ResultsWaitPage(WaitPage):
    # Wait until all participants have guessed or timed out, then compute the group outcome.
    @staticmethod
    def after_all_players_arrive(group: Group):
        set_payoffs(group)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # Reconstruct the actual average for display. Timed-out players are excluded.
        sorted_guesses = []
        for p in player.group.get_players():
            if p.guess != -99:
                sorted_guesses.append(p.guess)
        sorted_guesses = sorted(sorted_guesses)
        return dict(
            common_template_vars(player),
            sorted_guesses=sorted_guesses,
            average=round(sum(sorted_guesses) / len(sorted_guesses), 2),
            target_value=player.group.target_value,
        )

page_sequence = [Introduction, Guess, ResultsWaitPage, Results]
