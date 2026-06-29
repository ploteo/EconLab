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
This is a Public Goods Game (PGG) experiment implemented in oTree. In this game, participants are grouped together and each participant receives an initial endowment. They must decide how much of their endowment to contribute to a common project. The total contributions are then multiplied by a factor and distributed equally among the group members. The goal is to study cooperation and decision-making in a social dilemma context.
Feedback is provided to participants after each round, and the game can be repeated for multiple rounds. The experiment can be conducted in different languages, and it includes an AI commentary feature that provides insights into the results based on the data collected.
"""



class Constants(BaseConstants):
    name_in_url = 'PGG'
    players_per_group = 3
    num_rounds = 3
    endowment = cu(100)
    multiplier = 2


DEFAULT_LANGUAGE = 'it'

TEXTS = {
    'it': dict(
        language_name='Italian',
        instructions_title='Istruzioni',
        interaction_heading="L'interazione",
        instructions_group_prefix='In questo studio, farai parte di un gruppo formato da',
        participants='partecipanti',
        groups_random='I gruppi sono formati in modo casuale e l\'identità degli altri non sarà conosciuta.',
        endowment_prefix='Ogni partecipante nel gruppo riceve',
        endowment_suffix='(E).',
        contribution_decision='Ogni partecipante nel gruppo decide quanto contribuire a un progetto comune.',
        contribution_range_prefix='I contributi possono essere qualsiasi numero intero tra 0 e',
        earnings_heading='Il tuo guadagno',
        pgg_schema_alt='Schema del gioco dei beni pubblici',
        earnings_intro='I guadagni dal progetto sono calcolati come segue:',
        contributions_added_prefix='I contributi (C) di tutti i',
        contributions_added_suffix='partecipanti sono sommati.',
        multiplier_prefix='La somma dei contributi è moltiplicata per un fattore di',
        multiplier_suffix=': questi sono i guadagni totali dal progetto.',
        split_prefix='I guadagni totali dal progetto sono quindi divisi equamente tra tutti i',
        split_suffix='partecipanti: questi sono i tuoi guadagni dal progetto (R).',
        payoff_rule='Il tuo guadagno è dato dai tuoi guadagni dal progetto più l\'importo che non hai contribuito.',
        repetitions_prefix='Parteciperai a',
        repetitions_mid='round durante i quali ripeterai la medesima scelta e sarai associato agli stessi altri',
        repetitions_suffix='partecipanti.',
        total_payoff_rule='Il tuo guadagno totale sarà la somma dei tuoi guadagni in ogni round.',
        contribute_title='Contribuire',
        round='Round',
        of='di',
        choice_label='Quanto contribuisci al progetto comune?',
        integer_hint_prefix='Un numero intero tra 0 e',
        results_title='Risultati',
        this_round='Questo round',
        you_contributed='Hai contribuito al progetto:',
        others_contributed='Gli altri partecipanti hanno contribuito al progetto:',
        total_contribution='Contributo totale al progetto:',
        total_project_earnings='Guadagni totali dal progetto:',
        your_project_earnings='I tuoi guadagni dal progetto:',
        you_kept='Hai tenuto per te (non contribuito):',
        total_earned='Così in totale hai guadagnato:',
        history='Storia',
        final_results_title='Risultato finale',
        final_total_prefix='In totale, nei',
        final_total_mid='round, hai guadagnato',
        finish='Concludi',
        admin_report_title='PGG - Report amministratore',
        session_participants='Partecipanti nella sessione',
        recorded_choices='Scelte registrate',
        overall_mean_contribution='Contributo medio complessivo',
        overall_contributions='Contributi medi complessivi',
        overall_mean='Media complessiva',
        total_contributed='Totale contribuito',
        individual_endowment='Dotazione individuale',
        ai_commentary_title='Commento AI sui risultati',
        choices='Scelte',
        mean='Media',
        total='Totale',
        min='Min',
        max='Max',
        group_mean_contributions='Contributi medi per gruppo',
        group='Gruppo',
        overall_mean_label='Media complessiva',
        earnings_ranking='Ranking guadagni complessivi',
        rank='Rank',
        participant='Partecipante',
        completed_rounds='Round completati',
        total_earnings='Guadagno totale',
        round_average='Media per round',
        average_contribution='Contributo medio',
        contribution_round='Contributo R',
        earning_round='Guadagno R',
        individual_choices='Scelte individuali registrate',
        contribution='Contributo',
        no_contributions='Nessuna contribuzione registrata finora.',
        chart_group_contribution='Contribuzione del gruppo al progetto comune',
        chart_group_series='Contribuzione del gruppo',
        chart_y_points='Punti',
        chart_individual_contribution='La tua contribuzione al progetto comune',
        chart_individual_series='La tua contribuzione',
        chart_payoffs='I tuoi guadagni totali',
        chart_payoffs_series='I tuoi guadagni totali',
        chart_average_contribution='Contributo medio',
        chart_group_average_suffix='media',
    ),
    'en': dict(
        language_name='English',
        instructions_title='Instructions',
        interaction_heading='The interaction',
        instructions_group_prefix='In this study, you will be part of a group of',
        participants='participants',
        groups_random='Groups are formed randomly and the identity of the others will not be known.',
        endowment_prefix='Each participant in the group receives',
        endowment_suffix='(E).',
        contribution_decision='Each participant in the group decides how much to contribute to a common project.',
        contribution_range_prefix='Contributions can be any integer between 0 and',
        earnings_heading='Your payoff',
        pgg_schema_alt='Public goods game diagram',
        earnings_intro='Earnings from the project are calculated as follows:',
        contributions_added_prefix='The contributions (C) of all',
        contributions_added_suffix='participants are added up.',
        multiplier_prefix='The sum of contributions is multiplied by a factor of',
        multiplier_suffix=': these are the total earnings from the project.',
        split_prefix='The total earnings from the project are then divided equally among all',
        split_suffix='participants: these are your earnings from the project (R).',
        payoff_rule='Your payoff is given by your earnings from the project plus the amount you did not contribute.',
        repetitions_prefix='You will take part in',
        repetitions_mid='rounds in which you will repeat the same choice and be matched with the same other',
        repetitions_suffix='participants.',
        total_payoff_rule='Your total payoff will be the sum of your payoffs in each round.',
        contribute_title='Contribute',
        round='Round',
        of='of',
        choice_label='How much do you contribute to the common project?',
        integer_hint_prefix='An integer between 0 and',
        results_title='Results',
        this_round='This round',
        you_contributed='You contributed to the project:',
        others_contributed='The other participants contributed to the project:',
        total_contribution='Total contribution to the project:',
        total_project_earnings='Total earnings from the project:',
        your_project_earnings='Your earnings from the project:',
        you_kept='You kept for yourself (not contributed):',
        total_earned='Thus in total you earned:',
        history='History',
        final_results_title='Final result',
        final_total_prefix='In total, over',
        final_total_mid='rounds, you earned',
        finish='Finish',
        admin_report_title='PGG - Admin Report',
        session_participants='Participants in session',
        recorded_choices='Recorded choices',
        overall_mean_contribution='Overall mean contribution',
        overall_contributions='Overall mean contributions',
        overall_mean='Overall mean',
        total_contributed='Total contributed',
        individual_endowment='Individual endowment',
        ai_commentary_title='AI commentary on results',
        choices='Choices',
        mean='Mean',
        total='Total',
        min='Min',
        max='Max',
        group_mean_contributions='Mean contributions by group',
        group='Group',
        overall_mean_label='Overall mean',
        earnings_ranking='Overall earnings ranking',
        rank='Rank',
        participant='Participant',
        completed_rounds='Completed rounds',
        total_earnings='Total earnings',
        round_average='Average per round',
        average_contribution='Average contribution',
        contribution_round='Contribution R',
        earning_round='Earning R',
        individual_choices='Recorded individual choices',
        contribution='Contribution',
        no_contributions='No contributions recorded yet.',
        chart_group_contribution='Group contribution to the common project',
        chart_group_series='Group contribution',
        chart_y_points='Points',
        chart_individual_contribution='Your contribution to the common project',
        chart_individual_series='Your contribution',
        chart_payoffs='Your total earnings',
        chart_payoffs_series='Your total earnings',
        chart_average_contribution='Average contribution',
        chart_group_average_suffix='average',
    ),
}


def get_language(source):
    # Sessions can set language='it' or language='en'; otherwise fall back to Italian.
    session = source.session if hasattr(source, 'session') else source
    lang = str((session.config or {}).get('language', DEFAULT_LANGUAGE)).lower()
    return lang if lang in TEXTS else DEFAULT_LANGUAGE


def get_text(source):
    return TEXTS[get_language(source)]


def common_template_vars(source):
    return dict(lang=get_language(source), t=get_text(source))


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    total_choices = models.CurrencyField()  # for VC is withdrawals, for CP is contributions
    individual_share = models.CurrencyField()
    total_earnings = models.CurrencyField()


class Player(BasePlayer):
    choice = models.CurrencyField(min=0, max=Constants.endowment)  #ì
    payoff_final = models.CurrencyField()
    # to store final payoff


# FUNCTIONS
def creating_session(subsession: Subsession):
    if subsession.round_number == 1:  # this way we get a fixed role across repetitions
        subsession.group_randomly()
    else:
        subsession.group_like_round(1)


def set_payoffs(group: Group):
    players = group.get_players()
    choices = [p.choice for p in players]
    print(choices)
    group.total_choices = sum(choices)
    group.total_earnings = group.total_choices * Constants.multiplier
    group.individual_share = group.total_earnings / Constants.players_per_group
    for p in players:
        p.payoff = Constants.endowment - p.choice + group.individual_share

    # compute final payoff (as sum of all payoffs)
    if group.round_number == Constants.num_rounds:
        for p in players:
            hist = p.in_all_rounds()
            p.payoff_final = sum([g.payoff for g in hist])
            # print(p.payoff_final)


def _mean(values):
    if values:
        return round(sum(values) / len(values), 2)
    return None


PGG_AI_SYSTEM_PROMPTS = {
    'it': dedent(
        """
        Sei un assistente didattico esperto di economia sperimentale e giochi di
        beni pubblici.

        Devi commentare i risultati aggregati di un Public Goods Game per un
        report amministrativo oTree in italiano.

        Regole:
        - Usa solo i dati forniti nel JSON.
        - Non inventare spiegazioni psicologiche individuali non osservabili.
        - Distingui chiaramente tra pattern descrittivi e possibili
          interpretazioni didattiche.
        - Cita valori numerici quando sono utili.
        - Mantieni il testo breve, concreto e adatto a una discussione in aula.
        - Produci solo un frammento HTML, non Markdown.

        Struttura richiesta:
        <h4>Lettura generale</h4>
        <h4>Dinamica per round</h4>
        <h4>Differenze tra gruppi</h4>
        <h4>Comportamenti individuali e payoff</h4>
        <h4>Spunti per il debriefing</h4>
            - Differenze nelle strategie di gruppo e possibili ragioni.
            - Relazione tra contributi e payoff individuali.
            - Domande per stimolare la discussione in aula.
        """
    ).strip(),
    'en': dedent(
        """
        You are a teaching assistant specializing in experimental economics and
        public goods games.

        Comment on the aggregate results of a Public Goods Game for an oTree
        admin report in English.

        Rules:
        - Use only the data provided in the JSON.
        - Do not invent unobservable individual psychological explanations.
        - Clearly distinguish descriptive patterns from possible teaching
          interpretations.
        - Cite numerical values when useful.
        - Keep the text short, concrete, and suitable for classroom discussion.
        - Produce only an HTML fragment, not Markdown.

        Required structure:
        <h4>General reading</h4>
        <h4>Round dynamics</h4>
        <h4>Differences between groups</h4>
        <h4>Individual behavior and payoffs</h4>
        <h4>Debriefing prompts</h4>
            - Differences in group strategies and possible reasons.
            - Relationship between contributions and individual payoffs.
            - Questions to stimulate classroom discussion.
        """
    ).strip(),
}


def _clean_text(value):
    return " ".join(str(value or "").split()).strip()


def _session_openai_settings(session):
    session_config = session.config or {}
    api_key = session_config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    model = (
        session_config.get("openai_pgg_model")
        or session_config.get("openai_case_model")
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


def _pgg_ai_payload(session, data):
    lang = get_language(session)
    if lang == 'en':
        payoff_rule = (
            "Each participant keeps the amount not contributed. The sum of group "
            "contributions is multiplied and divided equally among group members."
        )
    else:
        payoff_rule = (
            "Ogni partecipante conserva la parte non contribuita. "
            "La somma dei contributi del gruppo viene moltiplicata e "
            "divisa in parti uguali tra i membri del gruppo."
        )
    return dict(
        experiment=dict(
            name="Public Goods Game",
            language=get_text(session)["language_name"],
            players_per_group=Constants.players_per_group,
            num_rounds=Constants.num_rounds,
            endowment=float(Constants.endowment),
            multiplier=Constants.multiplier,
            payoff_rule=payoff_rule,
        ),
        summary=dict(
            total_players=data["total_players"],
            recorded_choices=data["recorded_choices"],
            expected_choices=data["expected_choices"],
            overall_mean=data["overall_mean"],
            overall_total=data["overall_total"],
        ),
        round_rows=data["round_rows"],
        group_rows=data["group_rows"],
        participant_rows=data["participant_rows"],
        earnings_rows=data["earnings_rows"],
    )


def _pgg_ai_commentary(session, data):
    if not data["recorded_choices"]:
        return ""

    lang = get_language(session)
    payload = _pgg_ai_payload(session, data)
    fingerprint = sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    cache_key = "pgg_ai_commentary"
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
            - the average cooperation level relative to the endowment;
            - contribution trends across rounds;
            - differences between groups;
            - high contributors, low contributors, or free-riding patterns that
              can be described from the data;
            - the descriptive relationship between contributions and payoffs;
            - two or three useful questions for classroom discussion.

            Remember: describe observed patterns, not unobserved intentions.
            """
        ).strip()
    else:
        prompt = dedent(
            f"""
            Dati dell'esperimento in formato JSON:
            {json.dumps(payload, ensure_ascii=False, indent=2)}

            Scrivi un commento interpretativo per il docente. Metti in evidenza:
            - livello medio di cooperazione rispetto alla dotazione;
            - andamento dei contributi tra i round;
            - differenze tra gruppi;
            - presenza di contributori alti, bassi o free-riding descrivibile dai dati;
            - relazione descrittiva tra contributi e payoff;
            - due o tre domande utili per discutere i risultati in aula.

            Ricorda: descrivi pattern osservati, non intenzioni non osservate.
            """
        ).strip()

    try:
        response = client.chat.completions.create(
            model=settings["model"],
            messages=[
                {"role": "system", "content": PGG_AI_SYSTEM_PROMPTS[lang]},
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
        )
        html = _clean_text(response.choices[0].message.content)
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


def _participant_id(player: Player):
    return (
        getattr(player, 'label', None)
        or player.participant.label
        or getattr(player, 'code', None)
        or player.participant.code
    )


def _choice_value(player: Player):
    choice = player.field_maybe_none('choice')
    if choice is None:
        return None
    return float(choice)


def _payoff_value(player: Player):
    if player.group.field_maybe_none('total_choices') is None:
        return None
    payoff = player.field_maybe_none('payoff')
    if payoff is None:
        return None
    return float(payoff)


def vars_for_admin_report(subsession: Subsession):
    session = subsession.session
    subsessions = sorted(
        Subsession.objects_filter(session=session),
        key=lambda ss: ss.round_number,
    )

    total_players = len(subsessions[0].get_players()) if subsessions else 0
    all_choices = []
    round_rows = []
    group_data = {}
    participant_rows = []
    earnings_data = {}

    for ss in subsessions:
        round_choices = []
        for player in ss.get_players():
            player_key = player.participant.code
            player_earnings = earnings_data.setdefault(player_key, dict(
                participant=_participant_id(player),
                group=player.group.id_in_subsession,
                earnings_by_round=[None] * Constants.num_rounds,
                contributions_by_round=[None] * Constants.num_rounds,
                total=0,
                contribution_total=0,
                completed_rounds=0,
                completed_contributions=0,
            ))
            payoff = _payoff_value(player)
            if payoff is not None:
                player_earnings['earnings_by_round'][ss.round_number - 1] = round(payoff, 2)
                player_earnings['total'] += payoff
                player_earnings['completed_rounds'] += 1

            choice = _choice_value(player)
            if choice is None:
                continue
            player_earnings['contributions_by_round'][ss.round_number - 1] = round(choice, 2)
            player_earnings['contribution_total'] += choice
            player_earnings['completed_contributions'] += 1
            all_choices.append(choice)
            round_choices.append(choice)
            participant_rows.append(dict(
                participant=_participant_id(player),
                round=ss.round_number,
                group=player.group.id_in_subsession,
                choice=round(choice, 2),
            ))

        round_rows.append(dict(
            round=ss.round_number,
            n=len(round_choices),
            mean=_mean(round_choices),
            total=round(sum(round_choices), 2) if round_choices else None,
            min_value=round(min(round_choices), 2) if round_choices else None,
            max_value=round(max(round_choices), 2) if round_choices else None,
        ))

        for group in ss.get_groups():
            group_id = group.id_in_subsession
            item = group_data.setdefault(group_id, dict(
                group=group_id,
                choices=[],
                rounds=[],
                individuals={},
            ))
            group_choices = []
            for player in group.get_players():
                choice = _choice_value(player)
                if choice is not None:
                    group_choices.append(choice)
                    individual = item['individuals'].setdefault(
                        player.participant.code,
                        dict(
                            participant=_participant_id(player),
                            choices=[None] * Constants.num_rounds,
                        ),
                    )
                    individual['choices'][ss.round_number - 1] = round(choice, 2)
            item['choices'].extend(group_choices)
            item['rounds'].append(dict(
                round=ss.round_number,
                n=len(group_choices),
                mean=_mean(group_choices),
                total=round(sum(group_choices), 2) if group_choices else None,
            ))

    group_rows = []
    for group_id in sorted(group_data):
        item = group_data[group_id]
        group_rows.append(dict(
            group=item['group'],
            n=len(item['choices']),
            mean=_mean(item['choices']),
            total=round(sum(item['choices']), 2) if item['choices'] else None,
            rounds=item['rounds'],
            individuals=sorted(
                item['individuals'].values(),
                key=lambda individual: individual['participant'],
            ),
        ))

    participant_rows.sort(key=lambda row: (row['round'], row['group'], row['participant']))
    earnings_rows = [
        dict(
            participant=item['participant'],
            group=item['group'],
            total=round(item['total'], 2),
            completed_rounds=item['completed_rounds'],
            average=round(item['total'] / item['completed_rounds'], 2) if item['completed_rounds'] else None,
            earnings_by_round=item['earnings_by_round'],
            average_contribution=(
                round(item['contribution_total'] / item['completed_contributions'], 2)
                if item['completed_contributions'] else None
            ),
            contributions_by_round=item['contributions_by_round'],
        )
        for item in earnings_data.values()
        if item['completed_rounds']
    ]
    earnings_rows.sort(key=lambda row: (-row['total'], row['participant']))
    for index, row in enumerate(earnings_rows, start=1):
        row['rank'] = index

    report_data = dict(
        **common_template_vars(session),
        total_players=total_players,
        total_rounds=Constants.num_rounds,
        recorded_choices=len(all_choices),
        expected_choices=total_players * Constants.num_rounds,
        overall_mean=_mean(all_choices),
        overall_total=round(sum(all_choices), 2) if all_choices else None,
        endowment=float(Constants.endowment),
        round_rows=round_rows,
        group_rows=group_rows,
        participant_rows=participant_rows,
        earnings_rows=earnings_rows,
        round_labels=list(range(1, Constants.num_rounds + 1)),
        chart_text=get_text(session),
    )
    report_data["ai_commentary_html"] = _pgg_ai_commentary(session, report_data)
    return report_data


# PAGES
class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return {
            **common_template_vars(player),
            'other_players': Constants.players_per_group - 1,
            'common_proj': Constants.endowment * Constants.players_per_group,
        }

class Contribute(Page):
    form_model = 'player'
    form_fields = ['choice']
    # the player will fill out the field choice and it will be saved in player model (see models)
    @staticmethod
    def vars_for_template(player: Player):
        return {
            **common_template_vars(player),
            'round_number': player.round_number,
            'endowment': Constants.endowment,
        }


class ResultsWaitPage(WaitPage):
    # If you have a WaitPage in your sequence of pages, then oTree waits until all players in the group have arrived at that point in the sequence, and then all players are allowed to proceed.
    after_all_players_arrive = 'set_payoffs'
    # see method 'set_payoffs' in class Group in models.py
    # payoffs are computed here


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # retrieve historical values
        hist = player.in_all_rounds()
        # for the dynamic history graph
        history_contrib = [g.group.total_choices for g in hist]
        history_contrib = safe_json(history_contrib)

        history_individ = [g.choice for g in hist]
        history_individ = safe_json(history_individ)

        history_payoff = [g.payoff for g in hist]
        history_payoff = safe_json(history_payoff)

        # history data
        data_hist = [
            [g.choice for g in hist],
            [g.group.individual_share for g in hist],
            [g.payoff for g in hist]
        ]
        print(data_hist)
        # organize them
        table_hist = []
        for j in range(0, (player.round_number-1)):  # start from 
            t = []
            t.append(j+1)#round
            for i in data_hist:
                t.append(i[j])
            table_hist.append(t)
        print(table_hist)

        amount_kept = Constants.endowment - player.choice
        return {
            **common_template_vars(player),
            'history_contrib': history_contrib,
            'history_individ': history_individ,  
            'history_payoff': history_payoff,  
            'chart_text': safe_json(get_text(player)),
            'round_number': player.round_number,
            'kept': amount_kept,
            # old values
            'table_hist': table_hist
        }


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player: Player):
        return {**common_template_vars(player), 'payoff_final': player.payoff_final}  #


page_sequence = [Instructions, Contribute, ResultsWaitPage, Results, FinalResults]
