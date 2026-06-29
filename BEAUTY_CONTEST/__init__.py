from otree.api import *
import json
import os
from hashlib import sha256
from html import escape
from textwrap import dedent

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
- An optional AI commentary feature that provides insights into the results based on the data collected, using the OpenAI API. The commentary is generated in either Italian or English, depending on the session configuration
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
        language_name='Italian',
        admin_report_title='Beauty Contest - Report amministratore',
        admin_round='Round',
        guess_distribution='Distribuzione dei guess',
        no_guesses_histogram="Nessun guess registrato per costruire l'istogramma.",
        group_statistics='Statistiche di gruppo',
        group_id='Group ID',
        target_value_column='Target value',
        best_guess='Best guess',
        winners_count='# vincitori',
        participant_details='Dettagli partecipanti',
        participant='Partecipante',
        guess='Guess',
        winner='Vincitore?',
        payoff='Payoff',
        yes='Sì',
        no='No',
        no_data='Nessun dato disponibile.',
        histogram_participants='Numero di partecipanti',
        histogram_guess_interval='Intervallo di guess',
        histogram_participants_axis='# partecipanti',
        ai_commentary_title='Commento AI sui risultati',
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
        language_name='English',
        admin_report_title='Beauty Contest - Admin Report',
        admin_round='Round',
        guess_distribution='Guess distribution',
        no_guesses_histogram='No guesses recorded to build the histogram.',
        group_statistics='Group statistics',
        group_id='Group ID',
        target_value_column='Target value',
        best_guess='Best guess',
        winners_count='# winners',
        participant_details='Participant details',
        participant='Participant',
        guess='Guess',
        winner='Winner?',
        payoff='Payoff',
        yes='Yes',
        no='No',
        no_data='No data available.',
        histogram_participants='Number of participants',
        histogram_guess_interval='Guess interval',
        histogram_participants_axis='# participants',
        ai_commentary_title='AI commentary on results',
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


BEAUTY_AI_SYSTEM_PROMPTS = {
    'it': dedent(
        """
        Sei un assistente didattico esperto di economia sperimentale e beauty
        contest game.

        Devi commentare i risultati aggregati di un Beauty Contest per un
        report amministrativo oTree in italiano.

        Regole:
        - Usa solo i dati forniti nel JSON.
        - Non inventare intenzioni o spiegazioni psicologiche individuali.
        - Distingui pattern descrittivi e possibili interpretazioni didattiche.
        - Cita valori numerici quando sono utili.
        - Mantieni il testo breve e adatto a una discussione in aula.
        - Produci solo un frammento HTML, non Markdown.

        Struttura richiesta:
        <h4>Lettura generale</h4>
        <h4>Distribuzione delle stime</h4>
            - Commenta su k-level (k=0 (50),1 (33),2 (22),...) e iterazioni strategiche: 50 * (2/3)^k
        <h4>Target e vincitori</h4>
        <h4>Spunti per il debriefing</h4>
            - Quale è la soluzione "razionale" del gioco (equilibrio di Nash=0)? Come si confronta con la media osservata?
            - Quali pattern di comportamento sono stati osservati? Come si confrontano con le aspettative teoriche?
         
        """
    ).strip(),
    'en': dedent(
        """
        You are a teaching assistant specializing in experimental economics and
        beauty contest games.

        Comment on the aggregate results of a Beauty Contest for an oTree admin
        report in English.

        Rules:
        - Use only the data provided in the JSON.
        - Do not invent individual intentions or psychological explanations.
        - Distinguish descriptive patterns from possible teaching interpretations.
        - Cite numerical values when useful.
        - Keep the text short and suitable for classroom discussion.
        - Produce only an HTML fragment, not Markdown.

        Required structure:
        <h4>General reading</h4>
        <h4>Distribution of guesses</h4>
            - Comment on k-level (k=0 (50),1 (33),2 (22),...) and strategic iteration: 50 * (2/3)^k
        <h4>Target and winners</h4>
        <h4>Debriefing prompts</h4>
            - What is the "rational" solution of the game (Nash equilibrium=0)? How does it compare to the observed average?
            - What behavioral patterns were observed? How do they compare to theoretical expectations?
        """
    ).strip(),
}


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


def _openai_unavailable_reason(session):
    settings = _session_openai_settings(session)
    lang = get_language(session)
    missing_items = []

    if openai is None:
        if lang == 'en':
            missing_items.append("the Python package 'openai' is not installed")
        else:
            missing_items.append("il pacchetto Python 'openai' non è installato")

    if not settings["api_key"]:
        if lang == 'en':
            missing_items.append(
                "no OpenAI key was found in the session configuration "
                "('openai_api_key') or in the OPENAI_API_KEY environment variable"
            )
        else:
            missing_items.append(
                "non è stata trovata alcuna chiave OpenAI nella configurazione "
                "della sessione ('openai_api_key') o nella variabile d'ambiente "
                "OPENAI_API_KEY"
            )

    return "; ".join(missing_items)


def _openai_client(session):
    settings = _session_openai_settings(session)
    if openai is None or not settings["api_key"]:
        return None
    return openai.OpenAI(api_key=settings["api_key"])


def _ai_commentary_unavailable_html(session, reason):
    if get_language(session) == 'en':
        return (
            "<h4>AI commentary unavailable</h4>"
            "<p>The experiment data were collected correctly, but the automatic "
            "commentary cannot be generated right now.</p>"
            f"<p><strong>Reason:</strong> {escape(reason or 'OpenAI client unavailable')}</p>"
            "<p>Set <code>openai_api_key</code> in the session configuration, or "
            "the <code>OPENAI_API_KEY</code> environment variable, to enable the "
            "commentary.</p>"
        )
    return (
        "<h4>Commento AI non disponibile</h4>"
        "<p>I dati dell'esperimento sono stati raccolti correttamente, ma il "
        "commento automatico non può essere generato in questo momento.</p>"
        f"<p><strong>Motivo:</strong> {escape(reason or 'client OpenAI non disponibile')}</p>"
        "<p>Imposta <code>openai_api_key</code> nella configurazione della "
        "sessione, oppure la variabile d'ambiente <code>OPENAI_API_KEY</code>, "
        "per abilitare il commento.</p>"
    )


def _beauty_ai_payload(session, data):
    guesses = data["guess_values"]
    summary = dict(
        total_players=len(data["rows"]),
        recorded_guesses=len(guesses),
        missing_guesses=len(data["rows"]) - len(guesses),
        mean_guess=round(sum(guesses) / len(guesses), 2) if guesses else None,
        min_guess=min(guesses) if guesses else None,
        max_guess=max(guesses) if guesses else None,
        multiplier=C.MULTIPLIER_LABEL,
        guess_max=C.GUESS_MAX,
    )
    return dict(
        experiment=dict(
            name="Beauty Contest",
            language=get_text(session)["language_name"],
            rule=(
                "Participants choose an integer from 0 to 100. The target is "
                f"{C.MULTIPLIER_LABEL} of the average submitted guess. The "
                "participant(s) closest to the target split the jackpot."
            ),
        ),
        summary=summary,
        group_stats=data["group_stats"],
        participant_rows=data["rows"],
    )


def _beauty_ai_commentary(session, data):
    if not data["guess_values"]:
        return ""

    lang = get_language(session)
    payload = _beauty_ai_payload(session, data)
    fingerprint = sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    cache_key = "beauty_ai_commentary"
    cached = session.vars.get(cache_key)
    if cached and cached.get("fingerprint") == fingerprint:
        cached_html = cached.get("html", "")
        if (
            "AI commentary unavailable" not in cached_html
            and "Commento AI non disponibile" not in cached_html
        ):
            return cached_html

    client = _openai_client(session)
    if client is None:
        return _ai_commentary_unavailable_html(session, _openai_unavailable_reason(session))

    settings = _session_openai_settings(session)
    if lang == 'en':
        prompt = dedent(
            f"""
            Experiment data in JSON format:
            {json.dumps(payload, ensure_ascii=False, indent=2)}

            Write an interpretive comment for the instructor. Highlight:
            - the average guess and spread of guesses;
            - the relation between the average guess, target value, and best guess;
            - whether responses suggest naïve high guesses or strategic iteration;
            - winners and payoff distribution;
            - two or three useful classroom debriefing questions.

            Remember: describe observed patterns, not unobserved intentions.
            """
        ).strip()
    else:
        prompt = dedent(
            f"""
            Dati dell'esperimento in formato JSON:
            {json.dumps(payload, ensure_ascii=False, indent=2)}

            Scrivi un commento interpretativo per il docente. Metti in evidenza:
            - media e dispersione dei guess;
            - relazione tra media, target e best guess;
            - se le risposte suggeriscono guess alti naïve o iterazione strategica;
            - vincitori e distribuzione dei payoff;
            - due o tre domande utili per il debriefing in aula.

            Ricorda: descrivi pattern osservati, non intenzioni non osservate.
            """
        ).strip()

    try:
        try:
            response = client.chat.completions.create(
                model=settings["model"],
                messages=[
                    {"role": "system", "content": BEAUTY_AI_SYSTEM_PROMPTS[lang]},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.35,
            )
            html = _clean_text(response.choices[0].message.content)
        except Exception:
            response = client.responses.create(
                model=settings["model"],
                instructions=BEAUTY_AI_SYSTEM_PROMPTS[lang],
                input=prompt,
            )
            html = _clean_text(getattr(response, "output_text", ""))
        if not html:
            empty_reason = (
                "the model returned an empty response"
                if lang == 'en'
                else "il modello ha restituito una risposta vuota"
            )
            return _ai_commentary_unavailable_html(session, empty_reason)
    except Exception as exc:
        return _ai_commentary_unavailable_html(session, str(exc))

    session.vars[cache_key] = dict(fingerprint=fingerprint, html=html)
    return html


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

    report_data = dict(
        **common_template_vars(subsession),
        rows=rows,
        group_stats=group_stats,
        guess_values=guess_values,
        guess_max=C.GUESS_MAX,
        multiplier_label=C.MULTIPLIER_LABEL,
        round_number=subsession.round_number,
    )
    report_data["ai_commentary_html"] = _beauty_ai_commentary(subsession.session, report_data)
    return report_data


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
