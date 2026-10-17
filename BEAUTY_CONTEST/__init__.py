from otree.api import *
import json
import os
from hashlib import sha256

try:
    import openai
except ImportError:
    openai = None


doc = """
This is a oTree implementation of the "Beauty Contest" game, as described in Nagel (1995).

References:
Nagel, R. (1995). Unraveling in Guessing Games: An Experimental Study. The American Economic Review, 85(5), 1313–1326. http://www.jstor.org/stable/2950991

It is a simple game where participants are asked to choose a number between 0 and 100. The winner is the participant whose guess is closest to a fraction (typically 2/3) of the average of all guesses. The game is often used to study strategic thinking and iterative reasoning in experimental economics.
This implementation includes:
- A simple interface for participants to submit their guesses.
- Automatic calculation of the average guess, target value, and identification of the winner(s).
- An optional AI feedback feature for individual participant feedback. It is
  disabled by default and is generated only when the session configuration
  explicitly enables it.
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
        guess_title='La tua stima (Round {round_number} di {num_rounds})',
        guess_intro_1='Inserisci il valore desiderato digitandolo nel campo numerico qui sotto.',
        guess_intro_2='Puoi usare le frecce su/giù o scrivere direttamente un numero nel campo.',
        guess_intro_3='Una volta scelta la stima, premi il bottone Conferma che si attiva in basso.',
        guess_aria='Inserisci un numero nel campo',
        chosen_value='Il valore scelto è',
        confirm='Conferma',
        reread_instructions='Clicca qui per rileggere le istruzioni',
        instructions_title='Istruzioni',
        instructions_rules='Regole del gioco',
        your_task='Il tuo compito',
        how_to_win='Come vincere',
        number_range_hint='Scegli un numero intero tra 0 e {max_guess}',
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
        finish='Continua',
        final_results_title='Risultati finali',
        experiment_over="L'esperimento è terminato",
        total_earnings='Il tuo guadagno totale è',
        language_name='Italian',
        admin_report_title='Beauty Contest - Report amministratore',
        admin_round='Round',
        guess_distribution='Distribuzione dei guess',
        no_guesses_histogram="Nessun guess registrato per costruire l'istogramma.",
        histogram_participants='Numero di partecipanti',
        histogram_guess_interval='Intervallo di guess',
        histogram_participants_axis='# partecipanti',
        choice_distribution='Dove si colloca la tua scelta?',
        choice_distribution_intro='L’istogramma mostra le scelte del gruppo. La barra verde contiene il valore vincente; il bordo rosso indica l’intervallo della tua scelta.',
        winning_value='Valore vincente',
        your_choice='La tua scelta',
        target_marker='Valore obiettivo',
        participant_feedback_title='Feedback sulla tua scelta',
    ),
    'en': dict(
        start_game='Start the game',
        guess_title='Your guess (Round {round_number} of {num_rounds})',
        guess_intro_1='Enter your chosen value in the numeric field below.',
        guess_intro_2='You can use the up/down arrows or type a number directly.',
        guess_intro_3='Once you have chosen your guess, press the Confirm button that appears below.',
        guess_aria='Enter a number in the field',
        chosen_value='The chosen value is',
        confirm='Confirm',
        reread_instructions='Click here to read the instructions again',
        instructions_title='Instructions',
        instructions_rules='Game Rules',
        your_task='Your task',
        how_to_win='How to win',
        number_range_hint='Choose a whole number between 0 and {max_guess}',
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
        finish='Continue',
        final_results_title='Final results',
        experiment_over='The experiment is over',
        total_earnings='Your total earnings are',
        language_name='English',
        admin_report_title='Beauty Contest - Admin Report',
        admin_round='Round',
        guess_distribution='Guess distribution',
        no_guesses_histogram='No guesses recorded to build the histogram.',
        histogram_participants='Number of participants',
        histogram_guess_interval='Guess interval',
        histogram_participants_axis='# participants',
        choice_distribution='Where does your choice sit?',
        choice_distribution_intro='The histogram shows the group’s choices. The green bar contains the winning value; the red outline marks the interval containing your choice.',
        winning_value='Winning value',
        your_choice='Your choice',
        target_marker='Target value',
        participant_feedback_title='Feedback on your choice',
    ),
}


def get_language(source):
    # Sessions can set language='it' or language='en'; otherwise fall back to Italian.
    session = source.session if hasattr(source, 'session') else source
    lang = str((session.config or {}).get('language', DEFAULT_LANGUAGE)).lower()
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


def _clean_text(value):
    return " ".join(str(value or "").split()).strip()


def _session_openai_settings(session):
    session_config = session.config or {}
    api_key = session_config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    model = (
        session_config.get("openai_beauty_model")
        or session_config.get("openai_pgg_model")
        or session_config.get("openai_case_model")
        or os.getenv("OPENAI_BEAUTY_MODEL")
        or os.getenv("OPENAI_PGG_MODEL")
        or os.getenv("OPENAI_CASE_MODEL")
        or "gpt-5.4-mini"
    )
    return dict(api_key=api_key, model=model)


def _openai_client(session):
    settings = _session_openai_settings(session)
    if openai is None or not settings["api_key"]:
        return None
    return openai.OpenAI(api_key=settings["api_key"])


def _ai_commentary_enabled(session):
    """Return True only when a session explicitly opts in to AI commentary."""
    return (session.config or {}).get("enable_ai_commentary") is True


def _number_for_feedback(value):
    """Format whole numbers cleanly while keeping meaningful decimal values."""
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def _nearest_reasoning_steps(guess):
    """Return the closest value in the repeated two-thirds sequence from 50."""
    benchmarks = [50 * C.MULTIPLIER ** steps for steps in range(9)]
    steps, value = min(
        enumerate(benchmarks), key=lambda item: abs(guess - item[1])
    )
    return steps, value, abs(guess - value)


def _participant_choice_interpretation_html(player):
    """Relate the submitted number to feasible targets and repeated reasoning."""
    guess = player.guess
    max_target = C.MULTIPLIER * C.GUESS_MAX
    steps, step_value, step_distance = _nearest_reasoning_steps(guess)
    near_step_value = step_distance <= 3

    if get_language(player) == 'en':
        if guess > max_target:
            return (
                f"<p><strong>A useful boundary:</strong> {guess} is above "
                f"<strong>{_number_for_feedback(max_target)}</strong>, the highest "
                "possible target when every choice is at most 100. It therefore "
                "cannot be the target itself. A value this high can still be closest "
                "when the group chooses very high numbers, but it is not consistent "
                "with the repeated two-thirds sequence, which starts at 50 and moves "
                "downward. That sequence does not give a useful step estimate for "
                "this choice.</p>"
            )
        if guess == 0:
            return (
                "<p><strong>Your choice and repeated reasoning:</strong> Starting "
                "at 50 and repeatedly taking two-thirds makes the estimate smaller "
                "(about 33, 22, 15, and so on), moving toward 0. Your choice is "
                "consistent with many steps of this reasoning—roughly 8 or more on "
                "this simple scale. A single number cannot reveal the exact number "
                "of steps you considered.</p>"
            )
        if near_step_value:
            step_estimate = (
                "the starting point, before any two-thirds step"
                if steps == 0
                else f"about {steps} two-thirds step{'s' if steps != 1 else ''} "
                     "from the starting point"
            )
            return (
                f"<p><strong>Your choice and repeated reasoning:</strong> {guess} "
                f"is close to <strong>{_number_for_feedback(step_value)}</strong> "
                f"in the sequence 50 → 33 → 22 → 15 → …. That is roughly "
                f"{step_estimate}. This is only a comparison with the sequence, "
                "not an exact measure of how you reasoned.</p>"
            )
        return (
            f"<p><strong>Your choice and repeated reasoning:</strong> {guess} lies "
            f"between the reference values in the sequence 50 → 33 → 22 → 15 → …. "
            f"Its closest reference is {_number_for_feedback(step_value)}, about "
            f"{steps} step{'s' if steps != 1 else ''} from the start. This is a "
            "rough estimate, not an exact measure of your thinking. It is also "
            "useful to consider what group average you expected, since the target "
            "is two-thirds of that average.</p>"
        )

    if guess > max_target:
        return (
            f"<p><strong>Un limite utile:</strong> {guess} è superiore a "
            f"<strong>{_number_for_feedback(max_target)}</strong>, il valore "
            "obiettivo massimo possibile quando ogni scelta è al massimo 100. Non "
            "può quindi coincidere con il valore obiettivo. Un valore così alto può "
            "comunque essere il più vicino se il gruppo sceglie numeri molto alti, "
            "ma non segue la sequenza dei due terzi, che parte da 50 e scende. "
            "Questa sequenza non permette di stimare in modo utile i passaggi per "
            "una scelta così alta.</p>"
        )
    if guess == 0:
        return (
            "<p><strong>La tua scelta e il ragionamento ripetuto:</strong> partendo "
            "da 50 e prendendone ripetutamente i due terzi, la stima diminuisce "
            "(circa 33, 22, 15 e così via), avvicinandosi a 0. La tua scelta è "
            "compatibile con molti passaggi di questo ragionamento—circa 8 o più "
            "su questa scala semplice. Un solo numero non permette di sapere quanti "
            "passaggi hai considerato esattamente.</p>"
        )
    if near_step_value:
        step_estimate = (
            "il punto di partenza, prima di applicare i due terzi"
            if steps == 0
            else f"circa {steps} passaggi dei due terzi dal punto di partenza"
        )
        return (
            f"<p><strong>La tua scelta e il ragionamento ripetuto:</strong> {guess} "
            f"è vicino a <strong>{_number_for_feedback(step_value)}</strong> "
            f"nella sequenza 50 → 33 → 22 → 15 → …. Corrisponde a "
            f"{step_estimate}. È solo un confronto con la sequenza, non una "
            "misura esatta del tuo ragionamento.</p>"
        )
    return (
        f"<p><strong>La tua scelta e il ragionamento ripetuto:</strong> {guess} è "
        f"compresa tra i valori di riferimento della sequenza 50 → 33 → 22 → 15 → …. "
        f"Il più vicino è {_number_for_feedback(step_value)}, a circa {steps} "
        f"pass{'o' if steps == 1 else 'i'} dall'inizio. È una stima approssimativa, "
        "non una misura esatta del tuo ragionamento. È utile anche considerare "
        "quale media del gruppo ti aspettavi, dato che l'obiettivo è due terzi di "
        "quella media.</p>"
    )


def _participant_strategy_questions_html(player):
    """Prompt participants to connect their own guess with strategic reasoning."""
    guess = player.guess
    best_guess = player.group.best_guess
    max_target = C.MULTIPLIER * C.GUESS_MAX
    steps, step_value, step_distance = _nearest_reasoning_steps(guess)
    near_step_value = step_distance <= 3
    if get_language(player) == 'en':
        if guess > max_target:
            first_question = (
                f"The target cannot exceed {_number_for_feedback(max_target)}. "
                f"What did you expect others to choose that made {guess} seem like a good response?"
            )
        elif guess == 0:
            first_question = (
                "The repeated two-thirds sequence keeps shrinking toward 0. About "
                "how many times did you apply that idea, and what did you expect "
                "the other participants to choose?"
            )
        elif near_step_value:
            first_question = (
                f"Your choice is close to {_number_for_feedback(step_value)}, about "
                f"{steps} two-thirds step{'s' if steps != 1 else ''} from 50. Does "
                "that match how many times you applied the idea? What did you expect "
                "others to choose?"
            )
        else:
            first_question = (
                f"Your choice is between the reference values in the repeated "
                f"two-thirds sequence; the nearest is about {steps} steps from 50, "
                f"near {_number_for_feedback(step_value)}. Where did you stop, and "
                f"what average did you expect from others when choosing {guess}?"
            )
        return (
            "<h4>Questions for your strategy</h4>"
            "<ul>"
            f"<li>{first_question}</li>"
            f"<li>Taking one more two-thirds step from {_number_for_feedback(step_value)} gives about {_number_for_feedback(step_value * C.MULTIPLIER)}. Would that be closer to this round’s winning value, {best_guess}?</li>"
            f"<li>In this one-round game, predicting what others will actually choose may matter more than carrying the number sequence all the way down. What does the winning value {best_guess} suggest about the group’s choices?</li>"
            "</ul>"
        )

    if guess > max_target:
        first_question = (
            f"Il valore obiettivo non può superare {_number_for_feedback(max_target)}. "
            f"Che cosa ti aspettavi scegliessero gli altri perché {guess} ti sembrasse una buona risposta?"
        )
    elif guess == 0:
        first_question = (
            "La sequenza ripetuta dei due terzi continua a ridursi verso 0. Quante "
            "volte hai applicato questa idea, più o meno, e che cosa ti aspettavi "
            "scegliessero gli altri partecipanti?"
        )
    elif near_step_value:
        first_question = (
            f"La tua scelta è vicina a {_number_for_feedback(step_value)}, circa "
            f"{steps} pass{'o' if steps == 1 else 'i'} dei due terzi a partire da 50. "
            "Questo corrisponde a quante volte hai applicato l'idea? Che cosa ti "
            "aspettavi scegliessero gli altri?"
        )
    else:
        first_question = (
            f"La tua scelta è tra i valori di riferimento della sequenza ripetuta "
            f"dei due terzi; il più vicino è a circa {steps} passaggi da 50, vicino "
            f"a {_number_for_feedback(step_value)}. Dove ti sei fermato/a e quale "
            f"media ti aspettavi dagli altri quando hai scelto {guess}?"
        )
    return (
        "<h4>Domande sulla tua strategia</h4>"
        "<ul>"
        f"<li>{first_question}</li>"
        f"<li>Applicando ancora una volta i due terzi a {_number_for_feedback(step_value)} si ottiene circa {_number_for_feedback(step_value * C.MULTIPLIER)}. Sarebbe più vicino al valore vincente di questo round, {best_guess}?</li>"
        f"<li>In questo gioco a una sola manche, prevedere che cosa sceglieranno davvero gli altri può contare più che portare la sequenza fino in fondo. Che cosa suggerisce il valore vincente {best_guess} sulle scelte del gruppo?</li>"
        "</ul>"
    )


def _participant_feedback_fallback(player, guesses):
    """Give every participant a concise, outcome-specific strategic debrief.

    This is deliberately deterministic: feedback remains useful in classroom
    sessions that have not opted in to calls to an external AI service.
    """
    lang = get_language(player)
    guess = player.guess
    target = player.group.target_value
    best_guess = player.group.best_guess
    average = sum(guesses) / len(guesses)
    distance_to_winner = abs(guess - best_guess)

    if lang == 'en':
        result = (
            f"<p>You chose <strong>{guess}</strong>. It was "
            f"<strong>{_number_for_feedback(distance_to_winner)}</strong> away "
            f"from the winning value, <strong>{best_guess}</strong>. "
            f"Your choice was {'below' if guess < average else 'above' if guess > average else 'equal to'} "
            f"the group average ({_number_for_feedback(average)}) and "
            f"{'below' if guess < target else 'above' if guess > target else 'equal to'} "
            f"the target ({_number_for_feedback(target)}).</p>"
        )
        if player.is_winner:
            result += "<p><strong>Your choice was the closest to the target in this round.</strong></p>"
        result += (
            "<p><strong>The idea behind repeated reasoning:</strong> the target is "
            "two-thirds of the group average. If you start by expecting an average "
            "near 50, two-thirds is about 33. If you then expect others to make the "
            "same adjustment, two-thirds of 33 is about 22, then about 15, and so on "
            "toward 0. But in this one-round game, predicting what other participants "
            "will actually choose is often more useful than knowing where this "
            "sequence would end. A good choice depends on your expectations about "
            "their average.</p>"
        )
        return (
            result
            + _participant_choice_interpretation_html(player)
            + _participant_strategy_questions_html(player)
        )

    result = (
        f"<p>Hai scelto <strong>{guess}</strong>. La distanza dal valore vincente, "
        f"<strong>{best_guess}</strong>, era di "
        f"<strong>{_number_for_feedback(distance_to_winner)}</strong>. "
        f"La tua scelta era {'inferiore' if guess < average else 'superiore' if guess > average else 'uguale'} "
        f"alla media del gruppo ({_number_for_feedback(average)}) e "
        f"{'inferiore' if guess < target else 'superiore' if guess > target else 'uguale'} "
        f"al valore obiettivo ({_number_for_feedback(target)}).</p>"
    )
    if player.is_winner:
        result += "<p><strong>La tua scelta è stata la più vicina al valore obiettivo in questo round.</strong></p>"
    result += (
        "<p><strong>L'idea del ragionamento ripetuto:</strong> il valore obiettivo "
        "è due terzi della media del gruppo. Se inizi aspettandoti una media vicina "
        "a 50, due terzi sono circa 33. Se poi pensi che gli altri facciano lo stesso "
        "ragionamento, due terzi di 33 sono circa 22, poi circa 15, e così via verso "
        "0. In questo gioco a una sola manche, però, prevedere che cosa sceglieranno "
        "davvero gli altri è spesso più utile che sapere dove arriverebbe questa "
        "sequenza. Per scegliere bene conta la tua previsione della loro media.</p>"
    )
    return (
        result
        + _participant_choice_interpretation_html(player)
        + _participant_strategy_questions_html(player)
    )


def _participant_ai_feedback(player, guesses):
    """Optionally replace the local debrief with a short personalised AI comment."""
    fallback = _participant_feedback_fallback(player, guesses)
    choice_interpretation = _participant_choice_interpretation_html(player)
    strategy_questions = _participant_strategy_questions_html(player)
    session = player.session
    if not _ai_commentary_enabled(session):
        return fallback

    client = _openai_client(session)
    if client is None:
        return fallback

    lang = get_language(player)
    steps, step_value, step_distance = _nearest_reasoning_steps(player.guess)
    payload = dict(
        chosen_value=player.guess,
        group_average=round(sum(guesses) / len(guesses), 2),
        target_value=player.group.target_value,
        winning_value=player.group.best_guess,
        is_winner=player.is_winner,
        multiplier=C.MULTIPLIER_LABEL,
        maximum_possible_target=round(C.MULTIPLIER * C.GUESS_MAX, 2),
        estimated_reasoning_steps=dict(
            steps=steps,
            reference_value=round(step_value, 2),
            distance=round(step_distance, 2),
        ),
    )
    fingerprint = sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    cache_key = f"beauty_ai_feedback_round_{player.round_number}"
    cached = player.participant.vars.get(cache_key)
    if cached and cached.get("fingerprint") == fingerprint:
        cached_html = cached.get("html")
        return (
            cached_html + choice_interpretation + strategy_questions
            if cached_html else fallback
        )

    if lang == 'en':
        instructions = (
            "You are a warm experimental-economics teaching assistant. Write only "
            "two short HTML paragraphs for this participant. Use plain, intuitive "
            "language and avoid academic game-theory terminology. First comment on "
            "their chosen value relative to the group outcome and its approximate "
            "position in the repeated two-thirds sequence starting at 50. Treat the "
            "provided step estimate only as a rough comparison, not a measure of "
            "their actual thought process. If the choice exceeds the maximum possible target, explain that it "
            "cannot itself be the target, without saying it could not be closest. "
            "Then explain how each repeated two-thirds step makes the estimate "
            "smaller, and emphasize that in a one-round game predicting what others "
            "will actually choose may matter more than understanding where the "
            "sequence would end. Use only the supplied data; do not infer motives."
        )
        prompt = f"Round outcome data: {json.dumps(payload, ensure_ascii=False)}"
    else:
        instructions = (
            "Sei un assistente didattico cordiale di economia sperimentale. Scrivi "
            "solo due brevi paragrafi HTML per questo partecipante. Usa un linguaggio "
            "semplice e intuitivo, evitando il gergo accademico di teoria dei giochi. "
            "Prima commenta il suo valore rispetto all'esito del gruppo e alla sua "
            "posizione approssimativa nella sequenza ripetuta dei due terzi a partire "
            "da 50. Presenta il numero di passaggi solo come confronto approssimativo, "
            "non come misura del ragionamento effettivo. Se supera il valore obiettivo massimo possibile, spiega che non "
            "può coincidere con il target, senza dire che non potrebbe essere il più "
            "vicino. Poi spiega come ogni passaggio ripetuto dei due terzi riduca la "
            "stima e sottolinea che, in una sola manche, prevedere che cosa "
            "sceglieranno davvero gli altri può contare più che sapere dove "
            "arriverebbe la sequenza. Usa solo i dati forniti; non attribuire "
            "intenzioni."
        )
        prompt = f"Dati dell'esito: {json.dumps(payload, ensure_ascii=False)}"

    try:
        settings = _session_openai_settings(session)
        try:
            response = client.chat.completions.create(
                model=settings["model"],
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.35,
            )
            html = _clean_text(response.choices[0].message.content)
        except Exception:
            response = client.responses.create(
                model=settings["model"], instructions=instructions, input=prompt
            )
            html = _clean_text(getattr(response, "output_text", ""))
    except Exception:
        return fallback

    if not html:
        return fallback
    jargon_terms = (
        "nash",
        "equilibrium",
        "equilibria",
        "equilibrio",
        "k-level",
        "level-k",
        "level k",
    )
    if any(term in html.casefold() for term in jargon_terms):
        return fallback
    player.participant.vars[cache_key] = dict(fingerprint=fingerprint, html=html)
    return html + choice_interpretation + strategy_questions


def vars_for_admin_report(subsession: Subsession):
    # The administrator sees aggregate outcomes only; this report makes no AI calls.
    guess_values = [
        p.guess for p in subsession.get_players() if p.guess not in (None, -99)
    ]
    groups = subsession.get_groups()
    winning_value = (
        groups[0].field_maybe_none('best_guess') if len(groups) == 1 else None
    )
    average_value = (
        round(sum(guess_values) / len(guess_values), 2)
        if guess_values else None
    )
    target_value = (
        groups[0].field_maybe_none('target_value') if len(groups) == 1 else None
    )
    if target_value is None and average_value is not None:
        target_value = round(C.MULTIPLIER * average_value, 2)

    return dict(
        **common_template_vars(subsession),
        guess_values=guess_values,
        num_guesses=len(guess_values),
        average_value=average_value,
        target_value=target_value,
        winning_value=winning_value,
        guess_max=C.GUESS_MAX,
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
            guess_title=get_text(player)['guess_title'].format(
                round_number=player.round_number,
                num_rounds=C.NUM_ROUNDS,
            ),
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
        player_guess = player.guess if player.guess != -99 else None
        return dict(
            common_template_vars(player),
            sorted_guesses=sorted_guesses,
            average=round(sum(sorted_guesses) / len(sorted_guesses), 2),
            target_value=player.group.target_value,
            histogram_values=sorted_guesses,
            winning_value=player.group.best_guess,
            player_guess_for_chart=player_guess,
            participant_feedback_html=(
                _participant_ai_feedback(player, sorted_guesses)
                if player_guess is not None else ""
            ),
        )

page_sequence = [Introduction, Guess, ResultsWaitPage, Results]
