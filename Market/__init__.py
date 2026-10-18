from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html import escape
import json
import os
from textwrap import dedent
import time

from otree.api import *

try:
    import openai
except ImportError:
    openai = None


doc = """
A classroom continuous double auction. Participant 1 is the instructor.
The instructor starts and stops rounds; all other participants trade one unit.
Participant pages and admin analytics are available in Italian and English.
The admin report includes an optional AI commentary on equilibrium and efficiency.
"""

DEFAULT_LANGUAGE = 'it'

TEXTS = {
    'it': dict(
        instructor='Docente',
        student='Studente',
        nickname_label='Pseudonimo',
        welcome_title='Entra nel mercato in aula',
        auction_type='Asta doppia continua',
        welcome_heading='Benvenuto nel mercato',
        welcome_lead=(
            'Scegli uno pseudonimo anonimo. Il tuo ruolo e il tuo valore privato '
            'saranno assegnati quando il docente aprirà il round.'
        ),
        enter_market='Entra nel mercato',
        one_unit='Una unità',
        one_trade_round='Una transazione per round',
        private_values='Valori privati',
        instructions_title='Istruzioni del mercato',
        before_trading='Prima dell’apertura del mercato',
        how_market_works='Come funziona il mercato',
        assignment_intro=(
            'In ogni round ti sarà assegnata una unità da acquistare o vendere. '
            'Il tuo ruolo e il tuo numero privato sono visibili soltanto a te.'
        ),
        if_buyer='Se sei un acquirente',
        buyer_private='Il tuo numero privato è il tuo valore',
        buyer_rule=(
            'Presenta proposte di acquisto non superiori al tuo valore. Un prezzo '
            'di transazione più basso ti dà un profitto maggiore.'
        ),
        buyer_formula='Profitto = valore − prezzo di transazione',
        if_seller='Se sei un venditore',
        seller_private='Il tuo numero privato è il tuo costo',
        seller_rule=(
            'Presenta proposte di vendita non inferiori al tuo costo. Un prezzo '
            'di transazione più alto ti dà un profitto maggiore.'
        ),
        seller_formula='Profitto = prezzo di transazione − costo',
        making_trade='Concludere una transazione',
        bids_asks_meet='Le proposte di acquisto e vendita si incontrano nel mercato',
        matching_rule=(
            'Una transazione avviene quando la proposta di acquisto più alta è '
            'almeno pari alla proposta di vendita più bassa. Si applica il prezzo '
            'della proposta presentata per prima.'
        ),
        during_round='Durante il round',
        trade_once='Puoi effettuare una sola transazione',
        revise_offer=(
            'Puoi modificare la tua proposta finché non viene abbinata. I prezzi '
            'possono essere inseriti a incrementi di €0,10. Dopo la transazione, '
            'attendi la chiusura del round.'
        ),
        remember='Ricorda',
        remember_rule=(
            'Non offrire mai più del tuo valore di acquisto e non chiedere mai '
            'meno del tuo costo di vendita. Se non effettui una transazione, il '
            'tuo profitto nel round è zero. Ruoli e numeri privati vengono '
            'riassegnati a ogni nuovo round.'
        ),
        instructor_opens='Il docente aprirà il mercato quando tutti saranno pronti.',
        understand_continue='Ho capito — continua',
        double_auction='Asta doppia',
        round='Round',
        session='Sessione',
        live_market='Mercato in tempo reale',
        waiting='In attesa',
        time_remaining='Tempo rimanente',
        time_left='TEMPO RIMASTO',
        instructor_controls='Controlli del docente',
        open_when_ready='Apri il mercato quando la classe è pronta',
        places_prefix='Ci sono',
        places_suffix=(
            'posti per studenti in questa sessione. Solo gli studenti indicati '
            'come entrati riceveranno ruolo e valore secondo la sequenza fissa.'
        ),
        buyers='Acquirenti',
        sellers='Venditori',
        seconds='Secondi',
        start_round='Avvia il round',
        stop_round='Ferma il round',
        your_assignment='La tua assegnazione',
        waiting_instructor='In attesa del docente',
        role_value_here='Il tuo ruolo e il tuo valore privato appariranno qui.',
        current_profit='PROFITTO ATTUALE',
        highest_bid='Proposta di acquisto più alta',
        best_buyer_price='Miglior prezzo offerto da un acquirente',
        market='MERCATO',
        lowest_ask='Proposta di vendita più bassa',
        best_seller_price='Miglior prezzo offerto da un venditore',
        submit_offer='Presenta una proposta',
        market_not_open='Mercato non aperto',
        wait_start='Attendi che il docente avvii questo round.',
        submit='Invia',
        open_order_book='Proposte aperte',
        active_offers='Proposte attive',
        live='LIVE',
        bids='Proposte di acquisto',
        no_active_bids='Nessuna proposta di acquisto attiva',
        asks='Proposte di vendita',
        no_active_asks='Nessuna proposta di vendita attiva',
        trade_tape='Registro delle transazioni',
        completed_transactions='Transazioni concluse',
        no_transactions_yet='Nessuna transazione finora',
        instructor_only='Solo per il docente',
        participants='Partecipanti',
        ready='pronti',
        nickname='Pseudonimo',
        status='Stato',
        continue_results='Continua ai risultati',
        offer_number='Proposta n.',
        elapsed_seconds='secondi',
        joined='Entrato',
        not_joined='Non ancora entrato',
        role_value_on_open=(
            'Il tuo ruolo e il tuo valore privato appariranno all’apertura del round.'
        ),
        you_are_buyer='Sei un acquirente',
        you_are_seller='Sei un venditore',
        max_willingness='La tua disponibilità massima a pagare è {value}.',
        min_acceptable='Il tuo prezzo minimo accettabile è {value}.',
        place_bid='Presenta una proposta di acquisto',
        post_ask='Presenta una proposta di vendita',
        trade_complete='Transazione conclusa al prezzo di {value}.',
        bid_limit='La tua proposta non può superare {value}.',
        ask_limit='La tua richiesta non può essere inferiore a {value}.',
        submit_bid='Invia proposta di acquisto',
        submit_ask='Invia proposta di vendita',
        market_open='Mercato aperto',
        round_closed='Round chiuso',
        enter_price_first='Inserisci prima un prezzo.',
        results_title='Risultati del round {round_number}',
        round_complete='Round completato',
        closed_admin=(
            'Il mercato è chiuso. Le analisi dettagliate sono disponibili nei '
            'report di amministrazione di oTree.'
        ),
        market_closed='Il mercato è chiuso.',
        your_profit='IL TUO PROFITTO',
        traded_at='Transazione al prezzo di',
        no_transaction='Nessuna transazione',
        ready_next='Pronto per il round {round_number}?',
        reassigned='Ruoli e valori privati saranno assegnati nuovamente.',
        market_complete='Mercato completato',
        continue_finish='Continua per terminare la sessione.',
        next_round='Round successivo',
        finish='Termina',
        nickname_too_short='Inserisci uno pseudonimo di almeno 2 caratteri.',
        nickname_too_long='Lo pseudonimo non può superare i 24 caratteri.',
        only_instructor_start='Solo il docente può avviare il mercato.',
        already_started='Questo round è già stato avviato.',
        whole_numbers='Inserisci un numero intero per la durata.',
        minimum_traders=(
            'Almeno due studenti devono entrare prima di avviare il mercato.'
        ),
        trader_count=(
            'La somma di acquirenti e venditori deve essere {count}, cioè il '
            'numero di studenti partecipanti connessi.'
        ),
        duration_range='La durata del round deve essere compresa tra {minimum} e {maximum} secondi.',
        only_instructor_stop='Solo il docente può fermare il mercato.',
        unknown_action='Azione di mercato sconosciuta.',
        market_not_open_error='Il mercato non è aperto.',
        not_assigned='Non sei stato assegnato a una transazione in questo round.',
        joined_too_late=(
            'Il mercato è stato avviato prima del tuo ingresso. Potrai '
            'partecipare dal prossimo round.'
        ),
        already_traded='Hai già scambiato la tua unità.',
        positive_price='Inserisci un prezzo positivo a incrementi di 0,1.',
        bid_exceeds='La tua proposta non può superare il tuo valore di {value}.',
        ask_below='La tua richiesta non può essere inferiore al tuo costo di {value}.',
        all_exchanged='Tutte le unità sono state scambiate. Puoi fermare il round.',
        every_buyer_traded=(
            'Non sono possibili altre transazioni: tutti gli acquirenti hanno '
            'effettuato uno scambio.'
        ),
        every_seller_traded=(
            'Non sono possibili altre transazioni: tutti i venditori hanno '
            'effettuato uno scambio.'
        ),
        no_beneficial_trades=(
            'Non sono possibili altre transazioni mutuamente vantaggiose: il '
            'valore più alto tra gli acquirenti rimasti è inferiore al costo '
            'più basso tra i venditori rimasti.'
        ),
        report_title='Analisi del mercato — round {round_number}',
        transactions='Transazioni',
        average_price='Prezzo medio',
        price_range='Intervallo dei prezzi',
        equilibrium_quantity='Quantità di equilibrio',
        equilibrium_price_range='Intervallo del prezzo di equilibrio',
        actual_gains='Guadagni effettivi',
        maximum_gains='Guadagni massimi',
        allocative_efficiency='Efficienza allocativa',
        trade_completion='Completamento degli scambi',
        theoretical_supply_demand='Domanda e offerta teoriche',
        theory_description=(
            'La domanda ordina gli acquirenti dal valore più alto al più basso; '
            'l’offerta ordina i venditori dal costo più basso al più alto. La '
            'linea tratteggiata indica la quantità di equilibrio e il segmento '
            'ombreggiato l’intervallo competitivo del prezzo di equilibrio.'
        ),
        demand_legend='Domanda (valori degli acquirenti)',
        supply_legend='Offerta (costi dei venditori)',
        equilibrium_legend='Intervallo del prezzo di equilibrio',
        unit='Unità',
        buyer='Acquirente',
        value='Valore',
        seller='Venditore',
        cost='Costo',
        potential_surplus='Surplus potenziale',
        efficient_trade='Scambio efficiente',
        yes='Sì',
        no='No',
        transaction_prices_time='Prezzi di transazione nel tempo',
        prices_description=(
            'Prezzi eseguiti rispetto ai secondi trascorsi dall’apertura del round.'
        ),
        transaction_record='Registro completo degli scambi abbinati e dei guadagni realizzati.',
        time='Tempo',
        buyer_value='Valore acquirente',
        seller_cost='Costo venditore',
        price='Prezzo',
        surplus='Surplus',
        no_transactions_round='Nessuna transazione in questo round.',
        all_offers='Tutte le proposte',
        offers_description=(
            'Tutte le proposte di acquisto e vendita, incluse quelle abbinate e scadute.'
        ),
        participant='Partecipante',
        role='Ruolo',
        value_cost='Valore / costo',
        side='Lato',
        offer='Proposta',
        no_offers='Nessuna proposta presentata finora.',
        participant_outcomes='Risultati dei partecipanti',
        outcomes_description=(
            'Ruoli, valori privati, transazioni e profitti del round corrente.'
        ),
        traded='Scambio effettuato',
        trade_price='Prezzo di transazione',
        profit='Profitto',
        theory_chart_empty='Le curve appariranno dopo l’avvio del round.',
        theory_chart_aria='Curve teoriche di domanda e offerta',
        efficient_q='Q efficiente',
        quantity='Quantità',
        value_cost_axis='Valore / costo',
        no_prices_chart='Nessun prezzo di transazione da rappresentare.',
        equilibrium_price='Prezzo di equilibrio',
        lower_equilibrium='Limite inferiore di equilibrio',
        upper_equilibrium='Limite superiore di equilibrio',
        prices_chart_aria='Prezzi di transazione nel tempo',
        at='a',
        time_axis='Tempo',
        price_axis='Prezzo',
        language_name='Italian',
        ai_commentary_title='Commento AI sulle dinamiche di mercato',
        status_waiting='in attesa',
        status_active='attivo',
        status_finished='terminato',
        role_buyer='acquirente',
        role_seller='venditore',
        role_unassigned='non assegnato',
        side_bid='acquisto',
        side_ask='vendita',
        offer_active='attiva',
        offer_matched='abbinata',
        offer_expired='scaduta',
    ),
    'en': dict(
        instructor='Instructor',
        student='Student',
        nickname_label='Nickname',
        welcome_title='Join the classroom market',
        auction_type='Continuous double auction',
        welcome_heading='Welcome to the market',
        welcome_lead=(
            'Choose an anonymous nickname. Your role and private value will be '
            'assigned when the instructor opens the round.'
        ),
        enter_market='Enter market',
        one_unit='One unit',
        one_trade_round='One trade per round',
        private_values='Private values',
        instructions_title='Market Instructions',
        before_trading='Before trading begins',
        how_market_works='How the market works',
        assignment_intro=(
            'In every round you will be assigned one unit to buy or sell. Your '
            'role and private number are visible only to you.'
        ),
        if_buyer='If you are a buyer',
        buyer_private='Your private number is your value',
        buyer_rule=(
            'Submit bids at or below your value. A lower transaction price gives '
            'you a higher profit.'
        ),
        buyer_formula='Profit = value − transaction price',
        if_seller='If you are a seller',
        seller_private='Your private number is your cost',
        seller_rule=(
            'Submit asks at or above your cost. A higher transaction price gives '
            'you a higher profit.'
        ),
        seller_formula='Profit = transaction price − cost',
        making_trade='Making a trade',
        bids_asks_meet='Bids and asks meet in the market',
        matching_rule=(
            'A trade occurs when the highest bid is at least as high as the lowest '
            'ask. The transaction uses the price of the offer submitted first.'
        ),
        during_round='During the round',
        trade_once='You can trade only once',
        revise_offer=(
            'You may revise your offer until it is matched. Prices may be entered '
            'in €0.10 increments. After trading, wait for the round to close.'
        ),
        remember='Remember',
        remember_rule=(
            'Never bid above your buyer value or ask below your seller cost. If '
            'you do not trade, your profit for the round is zero. Roles and '
            'private numbers are assigned again in each new round.'
        ),
        instructor_opens='The instructor will open the market when everyone is ready.',
        understand_continue='I understand — continue',
        double_auction='Double Auction',
        round='Round',
        session='Session',
        live_market='Live market',
        waiting='Waiting',
        time_remaining='Time remaining',
        time_left='TIME LEFT',
        instructor_controls='Instructor controls',
        open_when_ready='Open the market when the class is ready',
        places_prefix='There are',
        places_suffix=(
            'student places in this session. Only students marked as joined '
            'will receive a role and value from the fixed sequence.'
        ),
        buyers='Buyers',
        sellers='Sellers',
        seconds='Seconds',
        start_round='Start round',
        stop_round='Stop round',
        your_assignment='Your assignment',
        waiting_instructor='Waiting for the instructor',
        role_value_here='Your role and private value will appear here.',
        current_profit='CURRENT PROFIT',
        highest_bid='Highest bid',
        best_buyer_price='Best price offered by a buyer',
        market='MARKET',
        lowest_ask='Lowest ask',
        best_seller_price='Best price offered by a seller',
        submit_offer='Submit an offer',
        market_not_open='Market not open',
        wait_start='Wait for the instructor to start this round.',
        submit='Submit',
        open_order_book='Open order book',
        active_offers='Active offers',
        live='LIVE',
        bids='Bids',
        no_active_bids='No active bids',
        asks='Asks',
        no_active_asks='No active asks',
        trade_tape='Trade tape',
        completed_transactions='Completed transactions',
        no_transactions_yet='No transactions yet',
        instructor_only='Instructor only',
        participants='Participants',
        ready='ready',
        nickname='Nickname',
        status='Status',
        continue_results='Continue to results',
        offer_number='Offer #',
        elapsed_seconds='seconds',
        joined='Joined',
        not_joined='Not joined yet',
        role_value_on_open=(
            'Your role and private value will appear when the round opens.'
        ),
        you_are_buyer='You are a buyer',
        you_are_seller='You are a seller',
        max_willingness='Your maximum willingness to pay is {value}.',
        min_acceptable='Your minimum acceptable price is {value}.',
        place_bid='Place a bid',
        post_ask='Post an ask',
        trade_complete='Trade complete at {value}.',
        bid_limit='Your bid cannot exceed {value}.',
        ask_limit='Your ask cannot be below {value}.',
        submit_bid='Submit bid',
        submit_ask='Submit ask',
        market_open='Market open',
        round_closed='Round closed',
        enter_price_first='Enter a price first.',
        results_title='Round {round_number} Results',
        round_complete='Round complete',
        closed_admin=(
            'The market is closed. Detailed analytics are available in oTree '
            'Admin Reports.'
        ),
        market_closed='The market is closed.',
        your_profit='YOUR PROFIT',
        traded_at='Traded at',
        no_transaction='No transaction',
        ready_next='Ready for round {round_number}?',
        reassigned='Roles and private values will be assigned again.',
        market_complete='Market complete',
        continue_finish='Continue to finish the session.',
        next_round='Next round',
        finish='Finish',
        nickname_too_short='Please enter a nickname with at least 2 characters.',
        nickname_too_long='Please keep your nickname to 24 characters or fewer.',
        only_instructor_start='Only the instructor can start the market.',
        already_started='This round has already been started.',
        whole_numbers='Enter a whole number for the duration.',
        minimum_traders='At least two students must join before the market can start.',
        trader_count=(
            'Buyers plus sellers must equal {count}, the number of connected '
            'student participants.'
        ),
        duration_range='Round duration must be between {minimum} and {maximum} seconds.',
        only_instructor_stop='Only the instructor can stop the market.',
        unknown_action='Unknown market action.',
        market_not_open_error='The market is not open.',
        not_assigned='You are not assigned to trade in this round.',
        joined_too_late=(
            'The market started before you joined. You can participate from '
            'the next round.'
        ),
        already_traded='You have already traded your unit.',
        positive_price='Enter a positive price in increments of 0.1.',
        bid_exceeds='Your bid cannot exceed your value of {value}.',
        ask_below='Your ask cannot be below your cost of {value}.',
        all_exchanged='All items have been exchanged. You can stop the round.',
        every_buyer_traded='No further trades are possible: every buyer has traded.',
        every_seller_traded='No further trades are possible: every seller has traded.',
        no_beneficial_trades=(
            'No further mutually beneficial trades are possible: the highest '
            'remaining buyer value is below the lowest remaining seller cost.'
        ),
        report_title='Round {round_number} market analytics',
        transactions='Transactions',
        average_price='Average price',
        price_range='Price range',
        equilibrium_quantity='Equilibrium quantity',
        equilibrium_price_range='Equilibrium price range',
        actual_gains='Actual gains',
        maximum_gains='Maximum gains',
        allocative_efficiency='Allocative efficiency',
        trade_completion='Trade completion',
        theoretical_supply_demand='Theoretical supply and demand',
        theory_description=(
            'Demand orders buyers from highest to lowest value; supply orders '
            'sellers from lowest to highest cost. The dashed line marks the '
            'equilibrium quantity, and the shaded segment is the competitive '
            'equilibrium price range.'
        ),
        demand_legend='Demand (buyer values)',
        supply_legend='Supply (seller costs)',
        equilibrium_legend='Equilibrium price range',
        unit='Unit',
        buyer='Buyer',
        value='Value',
        seller='Seller',
        cost='Cost',
        potential_surplus='Potential surplus',
        efficient_trade='Efficient trade',
        yes='Yes',
        no='No',
        transaction_prices_time='Transaction prices over time',
        prices_description='Executed prices plotted against seconds elapsed since the round opened.',
        transaction_record='Complete matched-trade record with realized gains from trade.',
        time='Time',
        buyer_value='Buyer value',
        seller_cost='Seller cost',
        price='Price',
        surplus='Surplus',
        no_transactions_round='No transactions in this round.',
        all_offers='All offers',
        offers_description=(
            'Every submitted bid and ask, including matched and expired offers.'
        ),
        participant='Participant',
        role='Role',
        value_cost='Value / cost',
        side='Side',
        offer='Offer',
        no_offers='No offers submitted yet.',
        participant_outcomes='Participant outcomes',
        outcomes_description=(
            'Roles, private values, trades, and profits for the current round.'
        ),
        traded='Traded',
        trade_price='Trade price',
        profit='Profit',
        theory_chart_empty='The schedules will appear after the round starts.',
        theory_chart_aria='Theoretical supply and demand curves',
        efficient_q='efficient Q',
        quantity='Quantity',
        value_cost_axis='Value / cost',
        no_prices_chart='No transaction prices to chart.',
        equilibrium_price='Equilibrium price',
        lower_equilibrium='Lower equilibrium bound',
        upper_equilibrium='Upper equilibrium bound',
        prices_chart_aria='Transaction prices over time',
        at='at',
        time_axis='Time',
        price_axis='Price',
        language_name='English',
        ai_commentary_title='AI commentary on market dynamics',
        status_waiting='waiting',
        status_active='active',
        status_finished='finished',
        role_buyer='buyer',
        role_seller='seller',
        role_unassigned='unassigned',
        side_bid='bid',
        side_ask='ask',
        offer_active='active',
        offer_matched='matched',
        offer_expired='expired',
    ),
}


def get_language(source):
    session = source.session if hasattr(source, 'session') else source
    lang = str((session.config or {}).get('language', DEFAULT_LANGUAGE)).lower()
    return lang if lang in TEXTS else DEFAULT_LANGUAGE


def get_text(source):
    return TEXTS[get_language(source)]


def common_template_vars(source):
    lang = get_language(source)
    return dict(lang=lang, locale='it-IT' if lang == 'it' else 'en-IE', t=TEXTS[lang])


def _money_display(value):
    if value is None:
        return None
    return f'{Decimal(str(float(value))).quantize(Decimal("0.01")):.2f}'


MARKET_AI_SYSTEM_PROMPTS = {
    'it': dedent(
        """
        Scrivi un brevissimo commento didattico in italiano sui risultati di
        un'asta doppia continua.

        - Usa esclusivamente i dati forniti nel JSON.
        - Concentrati soltanto su quantità di equilibrio, intervallo del prezzo
          di equilibrio, scambi conclusi ed efficienza allocativa.
        - Distingui previsioni teoriche e risultati osservati.
        - Se il mercato è ancora attivo, specifica che i risultati sono provvisori.
        - Non discutere strategie, psicologia, tempistica delle proposte o
          dinamica dei prezzi.
        - Usa al massimo 80 parole.
        - Produci soltanto un frammento HTML, senza Markdown.
        """
    ).strip(),
    'en': dedent(
        """
        Write a very short teaching comment in English on the results of a
        continuous double auction.

        - Use only the data provided in the JSON.
        - Focus only on equilibrium quantity, the equilibrium price range,
          completed trades, and allocative efficiency.
        - Distinguish theoretical predictions from observed outcomes.
        - If the market is still active, state that the results are provisional.
        - Do not discuss strategies, psychology, offer timing, or price dynamics.
        - Use no more than 80 words.
        - Produce only an HTML fragment, not Markdown.
        """
    ).strip(),
}


def _clean_text(value):
    return " ".join(str(value or "").split()).strip()


def _session_openai_settings(session):
    session_config = session.config or {}
    api_key = session_config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
    model = (
        session_config.get('openai_market_model')
        or session_config.get('openai_beauty_model')
        or session_config.get('openai_pgg_model')
        or os.getenv('OPENAI_MARKET_MODEL')
        or os.getenv('OPENAI_BEAUTY_MODEL')
        or os.getenv('OPENAI_PGG_MODEL')
        or 'gpt-5.4-mini'
    )
    return dict(api_key=api_key, model=model)


def _openai_unavailable_reason(session):
    settings = _session_openai_settings(session)
    lang = get_language(session)
    missing_items = []

    if openai is None:
        missing_items.append(
            "the Python package 'openai' is not installed"
            if lang == 'en'
            else "il pacchetto Python 'openai' non è installato"
        )
    if not settings['api_key']:
        missing_items.append(
            (
                "no OpenAI key was found in the session configuration "
                "('openai_api_key') or in the OPENAI_API_KEY environment variable"
            )
            if lang == 'en'
            else (
                "non è stata trovata alcuna chiave OpenAI nella configurazione "
                "della sessione ('openai_api_key') o nella variabile d'ambiente "
                "OPENAI_API_KEY"
            )
        )
    return '; '.join(missing_items)


def _openai_client(session):
    settings = _session_openai_settings(session)
    if openai is None or not settings['api_key']:
        return None
    return openai.OpenAI(api_key=settings['api_key'])


def _ai_commentary_unavailable_html(session, reason):
    if get_language(session) == 'en':
        return (
            '<h4>AI commentary unavailable</h4>'
            '<p>The market data were collected correctly, but the automatic '
            'commentary cannot be generated right now.</p>'
            f"<p><strong>Reason:</strong> {escape(reason or 'OpenAI client unavailable')}</p>"
            '<p>Set <code>openai_api_key</code> in the session configuration, or '
            'the <code>OPENAI_API_KEY</code> environment variable, to enable the '
            'commentary.</p>'
        )
    return (
        '<h4>Commento AI non disponibile</h4>'
        '<p>I dati del mercato sono stati raccolti correttamente, ma il commento '
        'automatico non può essere generato in questo momento.</p>'
        f"<p><strong>Motivo:</strong> {escape(reason or 'client OpenAI non disponibile')}</p>"
        '<p>Imposta <code>openai_api_key</code> nella configurazione della '
        'sessione, oppure la variabile d’ambiente <code>OPENAI_API_KEY</code>, '
        'per abilitare il commento.</p>'
    )


def _price_position(price, lower, upper):
    if lower is None or upper is None:
        return None
    if price < lower:
        return 'below'
    if price > upper:
        return 'above'
    return 'within'


def _distance_from_price_range(price, lower, upper):
    if lower is None or upper is None:
        return None
    return round(max(lower - price, price - upper, 0), 2)


def _market_ai_payload(group, report_data):
    summary = report_data['summary']
    theoretical = report_data['theoretical']
    lower = summary['equilibrium_price_low']
    upper = summary['equilibrium_price_high']

    transaction_timeline = []
    distances = []
    for row in report_data['transactions']:
        distance = _distance_from_price_range(row['price'], lower, upper)
        if distance is not None:
            distances.append(distance)
        transaction_timeline.append(
            dict(
                sequence=row['sequence'],
                elapsed_seconds=row['elapsed'],
                price=row['price'],
                price_position=_price_position(row['price'], lower, upper),
                distance_from_equilibrium_range=distance,
                buyer_value=row['buyer_value'],
                seller_cost=row['seller_cost'],
                realized_gains_from_trade=row['surplus'],
            )
        )

    prices = [row['price'] for row in report_data['transactions']]
    price_dynamics = dict(
        first_price=prices[0] if prices else None,
        last_price=prices[-1] if prices else None,
        first_distance_from_equilibrium_range=distances[0] if distances else None,
        last_distance_from_equilibrium_range=distances[-1] if distances else None,
        mean_distance_from_equilibrium_range=(
            round(sum(distances) / len(distances), 2) if distances else None
        ),
        prices_below_range=sum(
            row['price_position'] == 'below' for row in transaction_timeline
        ),
        prices_within_range=sum(
            row['price_position'] == 'within' for row in transaction_timeline
        ),
        prices_above_range=sum(
            row['price_position'] == 'above' for row in transaction_timeline
        ),
    )

    offer_timeline = [
        dict(
            sequence=row['sequence'],
            elapsed_seconds=row['elapsed'],
            participant_role=row['role'],
            side=row['side'],
            private_value_or_cost=row['private_value'],
            price=row['price'],
            final_status=row['status'],
        )
        for row in report_data['offers']
    ]

    return dict(
        experiment=dict(
            name='Continuous Double Auction',
            language=get_text(group)['language_name'],
            round_number=group.round_number,
            market_status=group.market_status,
            round_duration_seconds=group.round_duration,
            rules=(
                'Each buyer and seller can trade one unit. A trade occurs when '
                'the highest bid is at least the lowest ask. The transaction uses '
                'the price of the offer submitted first.'
            ),
        ),
        theoretical_predictions=dict(
            buyer_values=[row['value'] for row in theoretical['buyers']],
            seller_costs=[row['value'] for row in theoretical['sellers']],
            equilibrium_quantity=summary['theoretical_trades'],
            equilibrium_price_range=dict(lower=lower, upper=upper),
            maximum_gains_from_trade=summary['maximum_gains'],
        ),
        observed_outcomes=dict(
            transaction_count=summary['transaction_count'],
            trade_completion_percent=summary['completion_rate'],
            average_price=summary['average_price'],
            minimum_price=summary['minimum_price'],
            maximum_price=summary['maximum_price'],
            realized_gains_from_trade=summary['total_gains'],
            allocative_efficiency_percent=summary['efficiency_rate'],
            price_dynamics=price_dynamics,
            transaction_timeline=transaction_timeline,
            offer_timeline=offer_timeline,
        ),
    )


def _market_ai_commentary(group, report_data):
    if group.market_status == 'waiting' or not report_data['theoretical']['rows']:
        return ''

    lang = get_language(group)
    payload = _market_ai_payload(group, report_data)
    fingerprint = sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()
    cache_key = f'market_ai_commentary_round_{group.round_number}'
    cached = group.session.vars.get(cache_key)
    if cached and cached.get('fingerprint') == fingerprint:
        cached_html = cached.get('html', '')
        if (
            'AI commentary unavailable' not in cached_html
            and 'Commento AI non disponibile' not in cached_html
        ):
            return cached_html

    client = _openai_client(group.session)
    if client is None:
        return _ai_commentary_unavailable_html(
            group.session,
            _openai_unavailable_reason(group.session),
        )

    settings = _session_openai_settings(group.session)
    if lang == 'en':
        prompt = dedent(
            f"""
            Experimental-market data in JSON format:
            {json.dumps(payload, ensure_ascii=False, indent=2)}

            In one short HTML paragraph, compare completed trades with equilibrium
            quantity, observed prices with the equilibrium range, and reported
            allocative efficiency with the theoretical benchmark.
            """
        ).strip()
    else:
        prompt = dedent(
            f"""
            Dati del mercato sperimentale in formato JSON:
            {json.dumps(payload, ensure_ascii=False, indent=2)}

            In un solo breve paragrafo HTML, confronta gli scambi conclusi con la
            quantità di equilibrio, i prezzi osservati con l'intervallo di
            equilibrio e l'efficienza allocativa con il riferimento teorico.
            """
        ).strip()

    try:
        try:
            response = client.chat.completions.create(
                model=settings['model'],
                messages=[
                    {'role': 'system', 'content': MARKET_AI_SYSTEM_PROMPTS[lang]},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.35,
            )
            html = _clean_text(response.choices[0].message.content)
        except Exception:
            response = client.responses.create(
                model=settings['model'],
                instructions=MARKET_AI_SYSTEM_PROMPTS[lang],
                input=prompt,
            )
            html = _clean_text(getattr(response, 'output_text', ''))
        if not html:
            empty_reason = (
                'the model returned an empty response'
                if lang == 'en'
                else 'il modello ha restituito una risposta vuota'
            )
            return _ai_commentary_unavailable_html(group.session, empty_reason)
    except Exception as exc:
        return _ai_commentary_unavailable_html(group.session, str(exc))

    group.session.vars[cache_key] = dict(fingerprint=fingerprint, html=html)
    return html


def _ai_commentary_enabled(session):
    """Return True only when a session explicitly opts in to AI commentary."""
    return (session.config or {}).get('enable_ai_commentary') is True


class C(BaseConstants):
    NAME_IN_URL = 'double_auction'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 5
    DEFAULT_ROUND_SECONDS = 180
    MIN_ROUND_SECONDS = 30
    MAX_ROUND_SECONDS = 900
    # Applied in order to students who actually joined. Complete six-person
    # blocks reproduce the same theoretical supply and demand schedules.
    ASSIGNMENT_SEQUENCE = (
        ('buyer', 10),
        ('seller', 2),
        ('buyer', 7),
        ('seller', 5),
        ('buyer', 4),
        ('seller', 8),
    )


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    market_status = models.StringField(initial='waiting')
    started_at = models.FloatField(blank=True)
    ends_at = models.FloatField(blank=True)
    round_duration = models.IntegerField(initial=C.DEFAULT_ROUND_SECONDS)
    theoretical_trades = models.IntegerField(initial=0)


class Player(BasePlayer):
    nickname = models.StringField(blank=True)
    market_role = models.StringField(initial='unassigned')
    private_value = models.CurrencyField(blank=True)
    profit = models.CurrencyField(initial=0)
    has_traded = models.BooleanField(initial=False)
    traded_price = models.CurrencyField(blank=True)


class Offer(ExtraModel):
    group = models.Link(Group)
    player = models.Link(Player)
    side = models.StringField()
    price = models.CurrencyField()
    sequence = models.IntegerField()
    timestamp = models.FloatField()
    status = models.StringField(initial='active')


class Transaction(ExtraModel):
    group = models.Link(Group)
    buyer = models.Link(Player)
    seller = models.Link(Player)
    price = models.CurrencyField()
    sequence = models.IntegerField()
    timestamp = models.FloatField()
    elapsed_seconds = models.FloatField()


def creating_session(subsession):
    for player in subsession.get_players():
        if player.id_in_group == 1:
            player.market_role = 'teacher'
            player.nickname = get_text(player)['instructor']


def _is_teacher(player):
    return player.id_in_group == 1


def _display_name(player):
    text = get_text(player)
    if _is_teacher(player):
        return text['instructor']
    participant_name = player.participant.vars.get('nickname')
    current_name = player.field_maybe_none('nickname')
    return (
        participant_name
        or current_name
        or f"{text['student']} {player.id_in_group - 1}"
    )


def _sync_names(group, players=None):
    for player in (players if players is not None else group.get_players()):
        new_name = _display_name(player)
        if player.field_maybe_none('nickname') != new_name:
            player.nickname = new_name


def _student_players(group, players=None):
    all_players = players if players is not None else group.get_players()
    return [p for p in all_players if not _is_teacher(p)]


def _joined_students(group, players=None):
    return sorted(
        [
            p
            for p in _student_players(group, players=players)
            if p.participant.vars.get('nickname')
        ],
        key=lambda player: player.id_in_group,
    )


def _active_offers(group, side=None):
    offers = Offer.filter(group=group, status='active')
    if side:
        offers = [offer for offer in offers if offer.side == side]
    return offers


def _best_bid_from(offers):
    bids = [offer for offer in offers if offer.status == 'active' and offer.side == 'bid']
    return min(
        bids,
        key=lambda offer: (-float(offer.price), offer.timestamp, offer.sequence),
        default=None,
    )


def _best_ask_from(offers):
    asks = [offer for offer in offers if offer.status == 'active' and offer.side == 'ask']
    return min(
        asks,
        key=lambda offer: (float(offer.price), offer.timestamp, offer.sequence),
        default=None,
    )


def _best_bid(group):
    return _best_bid_from(_active_offers(group, 'bid'))


def _best_ask(group):
    return _best_ask_from(_active_offers(group, 'ask'))


def _expire_player_offers(group, player, active_offers=None):
    offers = active_offers if active_offers is not None else _active_offers(group)
    for offer in offers:
        if offer.status == 'active' and offer.player == player:
            offer.status = 'expired'


def _next_offer_sequence(group):
    key = f'market_offer_seq_{group.round_number}'
    current = group.session.vars.get(key)
    if current is None:
        current = len(Offer.filter(group=group))
    next_seq = current + 1
    group.session.vars[key] = next_seq
    return next_seq


def _next_transaction_sequence(group):
    key = f'market_tx_seq_{group.round_number}'
    current = group.session.vars.get(key)
    if current is None:
        current = len(Transaction.filter(group=group))
    next_seq = current + 1
    group.session.vars[key] = next_seq
    return next_seq


def _match_market(group, active_offers=None):
    offers = active_offers if active_offers is not None else _active_offers(group)
    while True:
        bid = _best_bid_from(offers)
        ask = _best_ask_from(offers)
        if bid is None or ask is None or bid.price < ask.price:
            return

        if (bid.timestamp, bid.sequence) < (ask.timestamp, ask.sequence):
            transaction_price = bid.price
        else:
            transaction_price = ask.price

        bid.status = 'matched'
        ask.status = 'matched'

        buyer = bid.player
        seller = ask.player
        buyer.has_traded = True
        seller.has_traded = True
        buyer.traded_price = transaction_price
        seller.traded_price = transaction_price
        buyer.profit = buyer.private_value - transaction_price
        seller.profit = transaction_price - seller.private_value
        buyer.payoff = buyer.profit
        seller.payoff = seller.profit

        _expire_player_offers(group, buyer, active_offers=offers)
        _expire_player_offers(group, seller, active_offers=offers)

        now = time.time()
        Transaction.create(
            group=group,
            buyer=buyer,
            seller=seller,
            price=transaction_price,
            sequence=_next_transaction_sequence(group),
            timestamp=now,
            elapsed_seconds=max(0, now - group.started_at),
        )


def _finish_market(group):
    if group.market_status == 'finished':
        return False
    group.market_status = 'finished'
    for offer in _active_offers(group):
        offer.status = 'expired'
    return True


def _close_if_expired(group):
    if (
        group.market_status == 'active'
        and group.ends_at
        and time.time() >= group.ends_at
    ):
        return _finish_market(group)
    return False


def _market_schedules(group):
    buyers = []
    sellers = []
    for player in _student_players(group):
        private_value = player.field_maybe_none('private_value')
        if private_value is None:
            continue
        entry = dict(
            nickname=_display_name(player),
            value=float(private_value),
            value_display=_money_display(private_value),
        )
        if player.market_role == 'buyer':
            buyers.append(entry)
        elif player.market_role == 'seller':
            sellers.append(entry)

    buyers.sort(key=lambda entry: entry['value'], reverse=True)
    sellers.sort(key=lambda entry: entry['value'])
    rows = []
    maximum_gains = 0
    efficient_trades = 0
    for index in range(max(len(buyers), len(sellers))):
        buyer = buyers[index] if index < len(buyers) else None
        seller = sellers[index] if index < len(sellers) else None
        surplus = (
            round(buyer['value'] - seller['value'], 2)
            if buyer is not None and seller is not None
            else None
        )
        efficient = surplus is not None and surplus >= 0
        if efficient:
            efficient_trades += 1
            maximum_gains += surplus
        rows.append(
            dict(
                quantity=index + 1,
                buyer=buyer,
                seller=seller,
                surplus=surplus,
                surplus_display=_money_display(surplus),
                efficient=efficient,
            )
        )

    equilibrium_price_low = None
    equilibrium_price_high = None
    if efficient_trades:
        marginal_buyer = buyers[efficient_trades - 1]['value']
        marginal_seller = sellers[efficient_trades - 1]['value']
        next_buyer = (
            buyers[efficient_trades]['value']
            if efficient_trades < len(buyers)
            else None
        )
        next_seller = (
            sellers[efficient_trades]['value']
            if efficient_trades < len(sellers)
            else None
        )
        equilibrium_price_low = max(
            marginal_seller,
            next_buyer if next_buyer is not None else marginal_seller,
        )
        equilibrium_price_high = min(
            marginal_buyer,
            next_seller if next_seller is not None else marginal_buyer,
        )

    return dict(
        buyers=buyers,
        sellers=sellers,
        rows=rows,
        efficient_trades=efficient_trades,
        maximum_gains=round(maximum_gains, 2),
        maximum_gains_display=_money_display(maximum_gains),
        equilibrium_price_low=equilibrium_price_low,
        equilibrium_price_low_display=_money_display(equilibrium_price_low),
        equilibrium_price_high=equilibrium_price_high,
        equilibrium_price_high_display=_money_display(equilibrium_price_high),
    )


def _summary(group):
    transactions = Transaction.filter(group=group)
    prices = [float(tx.price) for tx in transactions]
    total_gains = sum(float(p.profit) for p in _student_players(group))
    theoretical = _market_schedules(group)
    possible = theoretical['efficient_trades']
    maximum_gains = theoretical['maximum_gains']
    average_price = round(sum(prices) / len(prices), 2) if prices else None
    minimum_price = min(prices) if prices else None
    maximum_price = max(prices) if prices else None
    return dict(
        transaction_count=len(transactions),
        average_price=average_price,
        average_price_display=_money_display(average_price),
        minimum_price=minimum_price,
        minimum_price_display=_money_display(minimum_price),
        maximum_price=maximum_price,
        maximum_price_display=_money_display(maximum_price),
        total_gains=round(total_gains, 2),
        total_gains_display=_money_display(total_gains),
        theoretical_trades=possible,
        equilibrium_price_low=theoretical['equilibrium_price_low'],
        equilibrium_price_low_display=theoretical['equilibrium_price_low_display'],
        equilibrium_price_high=theoretical['equilibrium_price_high'],
        equilibrium_price_high_display=theoretical['equilibrium_price_high_display'],
        completion_rate=round(100 * len(transactions) / possible, 1) if possible else 0,
        maximum_gains=maximum_gains,
        maximum_gains_display=theoretical['maximum_gains_display'],
        efficiency_rate=(
            round(100 * total_gains / maximum_gains, 1)
            if maximum_gains
            else 0
        ),
    )


def _market_notice(group, players=None):
    if group.market_status != 'active':
        return None

    text = get_text(group)
    students = _joined_students(group, players=players)
    unmatched_buyers = [
        player
        for player in students
        if player.market_role == 'buyer' and not player.has_traded
    ]
    unmatched_sellers = [
        player
        for player in students
        if player.market_role == 'seller' and not player.has_traded
    ]

    if not unmatched_buyers and not unmatched_sellers:
        return text['all_exchanged']
    if not unmatched_buyers:
        return text['every_buyer_traded']
    if not unmatched_sellers:
        return text['every_seller_traded']

    highest_remaining_value = max(
        float(player.private_value) for player in unmatched_buyers
    )
    lowest_remaining_cost = min(
        float(player.private_value) for player in unmatched_sellers
    )
    if highest_remaining_value < lowest_remaining_cost:
        return text['no_beneficial_trades']
    return None


def _shared_student_market_state(group, active_offers=None):
    offers = (
        [o for o in active_offers if o.status == 'active']
        if active_offers is not None
        else _active_offers(group)
    )
    sorted_bids = sorted(
        [x for x in offers if x.side == 'bid'],
        key=lambda x: (-float(x.price), x.timestamp, x.sequence),
    )
    sorted_asks = sorted(
        [x for x in offers if x.side == 'ask'],
        key=lambda x: (float(x.price), x.timestamp, x.sequence),
    )
    transactions = sorted(
        Transaction.filter(group=group),
        key=lambda tx: tx.sequence,
    )
    return dict(
        best_bid=float(sorted_bids[0].price) if sorted_bids else None,
        best_ask=float(sorted_asks[0].price) if sorted_asks else None,
        bids=[
            dict(price=float(o.price), sequence=o.sequence)
            for o in sorted_bids[:8]
        ],
        asks=[
            dict(price=float(o.price), sequence=o.sequence)
            for o in sorted_asks[:8]
        ],
        transactions=[
            dict(
                sequence=tx.sequence,
                price=float(tx.price),
                elapsed=round(tx.elapsed_seconds, 1),
            )
            for tx in transactions
        ],
    )


def _state_for(group, viewer, error=None, shared=None, players=None, now=None):
    if now is None:
        _close_if_expired(group)
        now = time.time()

    state = dict(
        status=group.market_status,
        round_number=group.round_number,
        session_code=group.session.code,
        server_time=now,
        ends_at=group.ends_at if group.market_status == 'active' else None,
        time_left=(
            max(0, int(group.ends_at - now))
            if group.market_status == 'active' and group.ends_at
            else 0
        ),
        error=error,
    )

    if _is_teacher(viewer):
        state['participants'] = [
            dict(
                nickname=_display_name(p),
                joined=bool(p.participant.vars.get('nickname')),
            )
            for p in _student_players(group, players=players)
        ]
        state['market_notice'] = _market_notice(group, players=players)
        return state

    if shared is None:
        shared = _shared_student_market_state(group)

    private_val = viewer.field_maybe_none('private_value')
    traded_val = viewer.field_maybe_none('traded_price')
    state.update(
        **shared,
        me=dict(
            nickname=_display_name(viewer),
            role=viewer.market_role,
            private_value=float(private_val) if private_val is not None else None,
            profit=float(viewer.profit),
            has_traded=viewer.has_traded,
            traded_price=float(traded_val) if traded_val is not None else None,
        ),
    )
    return state


def _responses(group, errors=None, recipients=None, active_offers=None):
    errors = errors or {}
    all_players = group.get_players()
    target_players = recipients if recipients is not None else all_players
    now = time.time()
    has_student_target = any(not _is_teacher(p) for p in target_players)
    shared = (
        _shared_student_market_state(group, active_offers=active_offers)
        if has_student_target
        else None
    )
    return {
        player.id_in_group: _state_for(
            group,
            player,
            errors.get(player.id_in_group),
            shared=shared,
            players=all_players,
            now=now,
        )
        for player in target_players
    }


def _fixed_assignments(count):
    sequence = C.ASSIGNMENT_SEQUENCE
    return [sequence[index % len(sequence)] for index in range(count)]


def _possible_trades(players):
    buyer_values = sorted(
        [float(p.private_value) for p in players if p.market_role == 'buyer'],
        reverse=True,
    )
    seller_costs = sorted(
        [float(p.private_value) for p in players if p.market_role == 'seller']
    )
    return sum(
        buyer_value >= seller_cost
        for buyer_value, seller_cost in zip(buyer_values, seller_costs)
    )


def _start_market(player, data):
    group = player.group
    text = get_text(player)
    if not _is_teacher(player):
        return text['only_instructor_start']
    if group.market_status != 'waiting':
        return text['already_started']

    all_players = group.get_players()
    students = _joined_students(group, players=all_players)
    try:
        duration = int(data.get('duration'))
    except (TypeError, ValueError):
        return text['whole_numbers']

    if len(students) < 2:
        return text['minimum_traders']
    if not C.MIN_ROUND_SECONDS <= duration <= C.MAX_ROUND_SECONDS:
        return text['duration_range'].format(
            minimum=C.MIN_ROUND_SECONDS,
            maximum=C.MAX_ROUND_SECONDS,
        )

    _sync_names(group, players=all_players)
    for student in _student_players(group, players=all_players):
        student.market_role = 'unassigned'
        student.private_value = None
        student.profit = cu(0)
        student.payoff = cu(0)
        student.has_traded = False

    assignments = _fixed_assignments(len(students))
    for student, (role, value) in zip(students, assignments):
        student.market_role = role
        student.private_value = cu(value)

    buyer_count = sum(role == 'buyer' for role, _ in assignments)
    seller_count = len(assignments) - buyer_count

    group.session.vars[f'market_offer_seq_{group.round_number}'] = 0
    group.session.vars[f'market_tx_seq_{group.round_number}'] = 0
    group.theoretical_trades = _possible_trades(students)
    group.round_duration = duration
    group.started_at = time.time()
    group.ends_at = group.started_at + duration
    group.market_status = 'active'

    player.participant.vars['market_config'] = dict(
        buyer_count=buyer_count,
        seller_count=seller_count,
        participant_count=len(students),
        duration=duration,
    )
    return None


def _parse_price(raw_price):
    try:
        decimal_price = Decimal(str(raw_price))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not decimal_price.is_finite() or decimal_price <= 0:
        return None
    if decimal_price != decimal_price.quantize(Decimal('0.1')):
        return None
    return cu(decimal_price)


def live_market(player, data):
    group = player.group
    text = get_text(player)
    expired_now = _close_if_expired(group)
    message_type = data.get('type') if isinstance(data, dict) else None

    def _error_response(err_msg):
        if expired_now:
            return _responses(group, {player.id_in_group: err_msg})
        return _responses(
            group,
            {player.id_in_group: err_msg},
            recipients=[player],
        )

    if message_type == 'tick':
        if expired_now:
            return _responses(group)
        if group.market_status == 'finished':
            return _responses(group, recipients=[player])
        return {}

    if message_type == 'load':
        if expired_now:
            return _responses(group)
        if not _is_teacher(player) and group.market_status == 'waiting':
            teacher = group.get_player_by_id(1)
            return _responses(group, recipients=[teacher, player])
        return _responses(group, recipients=[player])

    if message_type == 'start':
        error = _start_market(player, data)
        if error:
            return _error_response(error)
        return _responses(group)

    if message_type == 'stop':
        if not _is_teacher(player):
            return _error_response(text['only_instructor_stop'])
        _finish_market(group)
        return _responses(group)

    if message_type != 'offer':
        return _error_response(text['unknown_action'])

    if group.market_status != 'active':
        return _error_response(text['market_not_open_error'])
    if _is_teacher(player) or player.market_role not in ('buyer', 'seller'):
        return _error_response(text['not_assigned'])
    if player.has_traded:
        return _error_response(text['already_traded'])

    price = _parse_price(data.get('price'))
    if price is None:
        return _error_response(text['positive_price'])
    if player.market_role == 'buyer' and price > player.private_value:
        return _error_response(
            text['bid_exceeds'].format(value=player.private_value)
        )
    if player.market_role == 'seller' and price < player.private_value:
        return _error_response(
            text['ask_below'].format(value=player.private_value)
        )

    active_offers = _active_offers(group)
    _expire_player_offers(group, player, active_offers=active_offers)
    new_offer = Offer.create(
        group=group,
        player=player,
        side='bid' if player.market_role == 'buyer' else 'ask',
        price=price,
        sequence=_next_offer_sequence(group),
        timestamp=time.time(),
        status='active',
    )
    active_offers.append(new_offer)
    _match_market(group, active_offers=active_offers)
    return _responses(group, active_offers=active_offers)


class Welcome(Page):
    form_model = 'player'
    form_fields = ['nickname']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and not _is_teacher(player)

    @staticmethod
    def error_message(player, values):
        text = get_text(player)
        nickname = (values.get('nickname') or '').strip()
        if len(nickname) < 2:
            return text['nickname_too_short']
        if len(nickname) > 24:
            return text['nickname_too_long']

    @staticmethod
    def vars_for_template(player):
        return common_template_vars(player)

    @staticmethod
    def before_next_page(player, timeout_happened):
        nickname = player.nickname.strip()
        player.nickname = nickname
        player.participant.vars['nickname'] = nickname


class Market(Page):
    live_method = live_market

    @staticmethod
    def is_displayed(player):
        return player.round_number <= player.session.config.get('num_rounds', 3)

    @staticmethod
    def vars_for_template(player):
        group = player.group
        new_name = _display_name(player)
        if player.field_maybe_none('nickname') != new_name:
            player.nickname = new_name
        students = _student_players(group)
        config = player.participant.vars.get('market_config', {})
        return dict(
            **common_template_vars(player),
            is_teacher=_is_teacher(player),
            student_count=len(students),
            default_duration=config.get(
                'duration',
                player.session.config.get(
                    'round_duration_seconds',
                    C.DEFAULT_ROUND_SECONDS,
                ),
            ),
        )


class Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and not _is_teacher(player)

    @staticmethod
    def vars_for_template(player):
        return common_template_vars(player)


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number <= player.session.config.get('num_rounds', 3)

    @staticmethod
    def vars_for_template(player):
        text = get_text(player)
        next_round_number = player.round_number + 1
        return dict(
            **common_template_vars(player),
            is_teacher=_is_teacher(player),
            active_rounds=player.session.config.get('num_rounds', 3),
            next_round_number=next_round_number,
            results_page_title=text['results_title'].format(
                round_number=player.round_number
            ),
            ready_next_text=text['ready_next'].format(
                round_number=next_round_number
            ),
            profit_display=_money_display(player.profit),
            traded_price_display=_money_display(
                player.field_maybe_none('traded_price')
            ),
        )


page_sequence = [Instructions, Welcome,  Market, Results]


def vars_for_admin_report(subsession):
    groups = subsession.get_groups()
    if not groups:
        return dict()
    group = groups[0]
    _close_if_expired(group)
    _sync_names(group)
    text = get_text(group)
    students = _joined_students(group)
    theoretical = _market_schedules(group)
    started_at = group.field_maybe_none('started_at')
    offers = sorted(Offer.filter(group=group), key=lambda offer: offer.sequence)
    transactions = sorted(
        Transaction.filter(group=group),
        key=lambda transaction: transaction.sequence,
    )

    participant_rows = []
    for student in students:
        private_value = student.field_maybe_none('private_value')
        traded_price = student.field_maybe_none('traded_price')
        participant_rows.append(
            dict(
                nickname=_display_name(student),
                role=student.market_role,
                role_label=text.get(f'role_{student.market_role}', student.market_role),
                private_value=float(private_value) if private_value is not None else None,
                private_value_display=_money_display(private_value),
                has_traded=student.has_traded,
                traded_price=float(traded_price) if traded_price is not None else None,
                traded_price_display=_money_display(traded_price),
                profit=float(student.profit),
                profit_display=_money_display(student.profit),
            )
        )

    offer_rows = [
        dict(
            sequence=offer.sequence,
            elapsed=(
                round(max(0, offer.timestamp - started_at), 1)
                if started_at is not None
                else 0
            ),
            nickname=_display_name(offer.player),
            role=offer.player.market_role,
            role_label=text.get(
                f'role_{offer.player.market_role}',
                offer.player.market_role,
            ),
            private_value=float(offer.player.private_value),
            private_value_display=_money_display(offer.player.private_value),
            side=offer.side,
            side_label=text.get(f'side_{offer.side}', offer.side),
            price=float(offer.price),
            price_display=_money_display(offer.price),
            status=offer.status,
            status_label=text.get(f'offer_{offer.status}', offer.status),
        )
        for offer in offers
    ]
    transaction_rows = [
        dict(
            sequence=transaction.sequence,
            elapsed=round(transaction.elapsed_seconds, 1),
            buyer=_display_name(transaction.buyer),
            seller=_display_name(transaction.seller),
            buyer_value=float(transaction.buyer.private_value),
            buyer_value_display=_money_display(transaction.buyer.private_value),
            seller_cost=float(transaction.seller.private_value),
            seller_cost_display=_money_display(transaction.seller.private_value),
            price=float(transaction.price),
            price_display=_money_display(transaction.price),
            surplus=round(
                float(transaction.buyer.private_value)
                - float(transaction.seller.private_value),
                2,
            ),
            surplus_display=_money_display(
                transaction.buyer.private_value - transaction.seller.private_value
            ),
        )
        for transaction in transactions
    ]

    report_data = dict(
        **common_template_vars(group),
        round_number=group.round_number,
        report_title=text['report_title'].format(
            round_number=group.round_number
        ),
        status=group.market_status,
        status_label=text.get(
            f'status_{group.market_status}',
            group.market_status,
        ),
        summary=_summary(group),
        theoretical=theoretical,
        offers=offer_rows,
        transactions=transaction_rows,
        students=participant_rows,
        chart_data=dict(
            demand=[
                dict(quantity=index + 1, price=entry['value'])
                for index, entry in enumerate(theoretical['buyers'])
            ],
            supply=[
                dict(quantity=index + 1, price=entry['value'])
                for index, entry in enumerate(theoretical['sellers'])
            ],
            transaction_prices=[
                dict(elapsed=row['elapsed'], price=row['price'])
                for row in transaction_rows
            ],
            efficient_trades=theoretical['efficient_trades'],
            equilibrium_price_low=theoretical['equilibrium_price_low'],
            equilibrium_price_high=theoretical['equilibrium_price_high'],
            round_duration=group.round_duration,
        ),
    )
    report_data['ai_commentary_html'] = (
        _market_ai_commentary(group, report_data)
        if _ai_commentary_enabled(group.session)
        else ''
    )
    return report_data


def custom_export(players):
    yield [
        'record_type',
        'session_code',
        'round',
        'sequence',
        'nickname',
        'role',
        'private_value',
        'side',
        'offer_price',
        'offer_status',
        'buyer',
        'seller',
        'transaction_price',
        'elapsed_seconds',
        'profit',
        'timestamp',
    ]
    groups = {}
    for player in players:
        groups[(player.session.code, player.round_number)] = player.group

    for (session_code, round_number), group in groups.items():
        for offer in sorted(Offer.filter(group=group), key=lambda o: o.sequence):
            yield [
                'offer',
                session_code,
                round_number,
                offer.sequence,
                _display_name(offer.player),
                offer.player.market_role,
                offer.player.private_value,
                offer.side,
                offer.price,
                offer.status,
                '',
                '',
                '',
                '',
                offer.player.profit,
                offer.timestamp,
            ]
        for tx in sorted(
            Transaction.filter(group=group),
            key=lambda transaction: transaction.sequence,
        ):
            yield [
                'transaction',
                session_code,
                round_number,
                tx.sequence,
                '',
                '',
                '',
                '',
                '',
                '',
                _display_name(tx.buyer),
                _display_name(tx.seller),
                tx.price,
                tx.elapsed_seconds,
                tx.buyer.profit + tx.seller.profit,
                tx.timestamp,
            ]
