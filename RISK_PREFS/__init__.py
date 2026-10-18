import json
import math
import os
import random
from hashlib import sha256
from html import escape
from itertools import permutations
from textwrap import dedent

from otree.api import *
from .overall_feedback import overall_choice_profile

try:
    import openai
except ImportError:
    openai = None


doc = """
Combined risk task administering MPL_HL, BRET, and an investment task in
random participant-level order.
Task references:
Holt, C. A. and Laury, S. K. (2002), "Risk Aversion and Incentive Effects,"
American Economic Review 92, 1644–1655 (MPL_HL).
Crosetto, P. and Filippin, A. (2013), "The 'Bomb' Risk Elicitation Task,"
Journal of Risk and Uncertainty 47 (BRET).
Gneezy, U. and Potters, J. (1997), "An Experiment on Risk Taking and
Evaluation Periods," Quarterly Journal of Economics 112, 631–645 (investment).
After all three tasks, participants answer a general risk-willingness question on a
0–10 scale before receiving final preference feedback. Question wording and scale from:
Falk, A., Becker, A., Dohmen, T., Huffman, D., and Sunde, U. (2022),
"The Preference Survey Module: A Validated Instrument for Measuring Risk,
Time, and Social Preferences," Management Science 69(4), 1935–1950.
https://doi.org/10.1287/mnsc.2022.4455
"""


class C(BaseConstants):
    NAME_IN_URL = 'RISK_PREFS'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    MPL_TASK = 'MPL_HL'
    BRET_TASK = 'BRET'
    INVESTMENT_TASK = 'INVESTMENT'

    MPL_A_H = 8
    MPL_A_L = 6
    MPL_B_H = 12
    MPL_B_L = 1

    BRET_NUM_CARDS = 32
    BRET_ENDOWMENT = 5
    BRET_CARD_VALUE = 0.25
    BRET_RISK_NEUTRAL_CARDS = 16

    INVESTMENT_ENDOWMENT = 100
    INVESTMENT_HIGH_RETURN_MULTIPLIER = 2.5

    CRRA_BACKGROUND_WEALTH = 1
    CRRA_SEARCH_MIN = -10
    CRRA_SEARCH_MAX = 10
    CRRA_GRID_STEP = 0.005


DEFAULT_LANGUAGE = 'it'

TEXTS = {
    'it': dict(
        language_name='Italian',
        new_task_title='Nuovo compito',
        new_task_intro='Stai per iniziare un nuovo compito.',
        new_task_read='Leggi attentamente le prossime istruzioni prima di prendere la tua decisione.',
        new_task_read_plural='Leggi attentamente le prossime istruzioni prima di prendere le tue decisioni.',
        mpl_instructions_title='Istruzioni',
        mpl_instructions_intro='In questa parte dell\'esperimento sceglierai tra coppie di lotterie.',
        mpl_instructions_example='Quello che segue e un esempio del tipo di decisione che dovrai affrontare.',
        my_choice='La mia scelta',
        of='di',
        mpl_example_text='Nell\'esempio devi scegliere tra la lotteria A e la lotteria B: la lotteria A assegna {a_h} con probabilita 1/10 e {a_l} con probabilita 9/10.',
        mpl_example_text_b='Analogamente, la lotteria B assegna {b_h} con probabilita 1/10 e {b_l} con probabilita 9/10.',
        mpl_choices_count='Affronterai 10 scelte tra A e B, con probabilita che cambiano tra le scelte.',
        bonus_payment='Pagamento bonus',
        mpl_bonus_rule='Dopo aver fatto le tue scelte, una delle 10 scelte sara selezionata casualmente. L\'esito della lotteria scelta sara calcolato e il risultato della tua scelta sara pagato come bonus.',
        virtual_earnings='Tutti i guadagni sono virtuali, non verra pagato denaro reale. Tuttavia, scegli come se gli importi monetari fossero reali.',
        choice_title='Scelta',
        mpl_choice_intro='Per ogni riga devi scegliere tra la lotteria A e la lotteria B.',
        mpl_choice_click='Per scegliere, clicca A oppure B in ogni riga.',
        mpl_next_hint='Quando hai finito, clicca sul pulsante "Avanti".',
        mpl_all_rows_selected='Tutte le righe hanno una lotteria selezionata.',
        mpl_rows_selected_template='{selected} righe su 10 selezionate.',
        bret_instructions_title='Istruzioni del gioco',
        bret_instructions_intro='Vedrai 32 carte coperte, con una bomba nascosta casualmente tra di esse. Devi decidere quante carte vuoi girare; il software le girera automaticamente.',
        bret_fixed_amount='Ricevi un importo fisso di {amount} euro.',
        bret_rules_title='Regole del gioco',
        bret_rule_zero='Se decidi di non girare alcuna carta, ricevi l\'importo fisso di {amount} euro.',
        bret_rule_bomb='Se trovi la bomba, mantieni l\'importo fisso di {amount} euro ma non ricevi alcun premio per le carte.',
        bret_rule_safe='Se non trovi la bomba, il tuo payoff sara pari a {amount} euro piu {value} euro per ogni carta girata.',
        continue_to_start='Clicca sul pulsante "Continua" per iniziare.',
        your_cards_title='Le tue carte',
        bret_cards_question='Quante carte vuoi girare?',
        confirm_choice='OK, confermo la mia scelta',
        continue_button='OK, continua',
        card_back_alt='Retro della carta',
        bomb_alt='Bomba',
        smiley_alt='Sorriso',
        unhappy_alt='Triste',
        bret_decided_cards='Hai deciso di girare {cards} carte.',
        bret_found_bomb='Purtroppo hai trovato la bomba.',
        bret_bomb_payoff='Mantieni l\'importo fisso, ma non ricevi alcun premio per le carte. Quindi il tuo payoff e {payoff} token.',
        bret_no_bomb='Congratulazioni! Non hai trovato la bomba.',
        bret_safe_payoff='Quindi il tuo payoff e {payoff} token.',
        investment_title='Compito di investimento',
        investment_intro='Ricevi una dotazione di {endowment} token. Scegli quanti token investire; conserverai la parte non investita.',
        investment_low_rule='Con probabilita 2/3, perdi la somma investita e ricevi {endowment} meno i token investiti.',
        investment_high_rule='Con probabilita 1/3, guadagni 2,5 volte la somma investita e ricevi {endowment} piu 2,5 volte i token investiti.',
        investment_choice_question='Quanti token vuoi investire?',
        investment_choice_hint='Inserisci un numero intero da 0 a {endowment}.',
        investment_preview_title='Anteprima dei possibili payoff',
        investment_preview_prompt='Inserisci un importo per vedere i due possibili risultati.',
        investment_preview_low='Se perdi l’investimento (probabilità 2/3)',
        investment_preview_high='Se l’investimento rende (probabilità 1/3)',
        investment_preview_note='Questa è solo un’anteprima: il risultato effettivo sarà determinato dopo la conferma.',
        investment_preview_tokens='token',
        investment_result_title='Risultato dell\'investimento',
        investment_result_low='Si e verificato il risultato meno favorevole (probabilita 2/3).',
        investment_result_high='Si e verificato il risultato piu favorevole (probabilita 1/3).',
        investment_chosen='Hai investito {amount} token su {endowment}.',
        investment_result_payoff='Il tuo payoff in questo compito e {payoff}.',
        investment_payoff_text='Il tuo payoff nel compito di investimento e {payoff}.',
        investment_feedback_title='Feedback investimento',
        investment_feedback_zero='Non hai investito alcun token: hai scelto il payoff certo.',
        investment_feedback_full='Hai investito tutti i token.',
        investment_feedback_partial='Hai investito {amount} token su {endowment}. Un investimento maggiore comporta sia un guadagno potenziale sia una perdita potenziale maggiori.',
        general_risk_title='Disponibilita generale ad assumere rischi',
        general_risk_question='Per favore, indica quanto sei disposto o non disposto ad assumere rischi, in generale.',
        general_risk_instruction='Usa una scala da 0 a 10, dove 0 significa che sei “completamente non disposto ad assumere rischi” e 10 significa che sei “molto disposto ad assumere rischi”.',
        general_risk_numbers='Puoi usare anche qualsiasi numero tra 0 e 10 per indicare dove ti collochi sulla scala, ad esempio 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10.',
        general_risk_low='Completamente non disposto ad assumere rischi',
        general_risk_high='Molto disposto ad assumere rischi',
        summary_title='Risultato finale',
        summary_heading='Riepilogo',
        overall_profile_title='Profilo complessivo delle scelte',
        overall_profile_label='Tendenza media nei tre compiti',
        overall_profile_very_cautious='Molto prudente',
        overall_profile_somewhat_cautious='Abbastanza prudente',
        overall_profile_middle='Intermedio',
        overall_profile_somewhat_willing='Abbastanza disposto ad assumere rischi',
        overall_profile_very_willing='Molto disposto ad assumere rischi',
        overall_profile_method='Media con uguale peso delle categorie interpretate nei compiti MPL, BRET e investimento. E una sintesi descrittiva delle decisioni, non una misura di un tratto personale.',
        overall_profile_partial='Il profilo usa {count} compiti interpretabili su 3; le scelte ambigue non entrano nella media.',
        overall_profile_unavailable='Non ci sono abbastanza scelte interpretabili per calcolare un profilo complessivo.',
        mpl_payoff_text='Il tuo payoff MPL e {payoff}.',
        bret_payoff_text='Il tuo payoff BRET e {payoff}.',
        total_payoff_text='Il tuo payoff totale e {payoff}.',
        mpl_feedback_title='Feedback MPL',
        bret_feedback_title='Feedback BRET',
        risk_type_label='Tipo di preferenza verso il rischio',
        risk_type_very_averse='Molto avverso al rischio',
        risk_type_moderately_averse='Moderatamente avverso al rischio',
        risk_type_slightly_averse='Lievemente avverso al rischio',
        risk_type_neutral='Neutrale al rischio',
        risk_type_moderately_seeking='Moderatamente propenso al rischio',
        risk_type_very_seeking='Molto propenso al rischio',
        risk_type_unclear='Non determinabile da queste scelte',
        risk_type_note='I tipi MPL, BRET e investimento descrivono le scelte nei rispettivi compiti secondo ipotesi specifiche; non sono tratti personali stabili.',
        ai_individual_title='Feedback mediato dall\'IA',
        mpl_feedback_inconsistent='Le tue scelte MPL sono state {choices}. Contengono {switch_count} cambi tra A e B, quindi non indicano chiaramente un unico tipo di preferenza verso il rischio.',
        mpl_feedback_all_a='Hai scelto la lotteria A in ogni riga MPL: e il pattern piu cauto disponibile in questa tabella.',
        mpl_feedback_first_b='Hai scelto la lotteria B gia dalla prima riga MPL: e il pattern piu propenso al rischio disponibile in questa tabella.',
        mpl_feedback_switch='Sei passato dalla lotteria A alla lotteria B alla riga MPL {first_b}. Questa scelta suggerisce il tipo indicato sopra.',
        bret_feedback_zero='Nel compito BRET hai scelto di non girare alcuna carta. Hai mantenuto l\'importo fisso e non hai esposto ad alcun rischio i guadagni delle carte.',
        bret_feedback_below='Nel compito BRET hai scelto di girare {cards} carte, meno del benchmark neutrale al rischio di circa {benchmark} carte in questa configurazione.',
        bret_feedback_equal='Nel compito BRET hai scelto di girare {benchmark} carte, un valore vicino al benchmark neutrale al rischio in questa configurazione.',
        bret_feedback_above='Nel compito BRET hai scelto di girare {cards} carte, piu del benchmark neutrale al rischio di circa {benchmark} carte in questa configurazione.',
        bret_feedback_all='Nel compito BRET hai scelto di girare tutte le {cards} carte. Questo garantisce di trovare la bomba e di ricevere solo l\'importo fisso, quindi non indica chiaramente un tipo di preferenza verso il rischio.',
        waiting_title='In attesa degli altri partecipanti',
        waiting_body='Attendi che tutti abbiano completato i compiti sul rischio.',
        ai_unavailable_title='Feedback mediato dall\'IA non disponibile',
        ai_unavailable_body='I dati dell\'esperimento sono stati raccolti correttamente, ma il feedback automatico non puo essere generato in questo momento.',
        ai_unavailable_reason='Motivo',
        ai_unavailable_hint='Imposta <code>openai_api_key</code> nella configurazione della sessione, oppure la variabile d\'ambiente <code>OPENAI_API_KEY</code>, per abilitare questo feedback.',
        ai_group_pending_title='Feedback di gruppo mediato dall\'IA in attesa',
        ai_group_pending_body='Il feedback di gruppo verra generato dopo che tutti i partecipanti avranno completato i tre compiti e la domanda sul rischio generale.',
        completed_mpl='MPL completato',
        completed_bret='BRET completato',
        completed_investment='Investimento completato',
        completed_survey='Domanda generale completata',
        admin_report_title='RISK_PREFS - Report amministratore',
        participants='Partecipanti',
        inconsistent_mpl_patterns='Pattern MPL incoerenti',
        mpl_crra_estimates='Stime CRRA MPL',
        bret_crra_estimates='Stime CRRA BRET',
        mean='Media',
        paired_crra_estimates='Stime CRRA appaiate',
        participants_with_both='Partecipanti con entrambi i coefficienti MPL e BRET',
        ai_group_feedback_title='Feedback di gruppo mediato dall\'IA',
        distribution_mpl_choices='Distribuzione delle scelte MPL',
        frequency_a_by_row='Frequenza della lotteria A per riga.',
        distribution_bret_choices='Distribuzione delle scelte BRET',
        frequency_cards_turned='Frequenza del numero di carte girate.',
        distribution_investment_choices='Distribuzione degli investimenti',
        frequency_investment='Numero di partecipanti per fascia di investimento.',
        investment_axis='Token investiti',
        general_risk_distribution='Distribuzione delle risposte alla domanda sul rischio generale',
        general_risk_distribution_note='Numero di partecipanti per ciascuna risposta da 0 a 10.',
        general_risk_axis='Disponibilita ad assumere rischi (0–10)',
        mpl_survey_scatter_title='Risposta sul rischio generale e CRRA MPL',
        bret_survey_scatter_title='Risposta sul rischio generale e CRRA BRET',
        investment_survey_scatter_title='CRRA investimento e rischio generale autodichiarato',
        report_choice_distribution_title='Distribuzione delle scelte',
        report_crra_estimates_title='Stime CRRA',
        report_survey_correlation_title='Correlazione tra CRRA e rischio autodichiarato',
        report_cross_task_title='Correlazione tra compiti',
        report_mpl_bret_title='MPL e BRET',
        report_mpl_choice_title='MPL — scelta della lotteria A per riga',
        report_bret_choice_title='BRET — numero di carte girate',
        report_investment_choice_title='Investimento — token investiti',
        report_survey_choice_title='Rischio generale autodichiarato — risposte 0–10',
        report_mpl_crra_title='MPL — distribuzione CRRA',
        report_bret_crra_title='BRET — distribuzione CRRA',
        report_investment_crra_title='Investimento — distribuzione CRRA',
        investment_crra_axis='CRRA investimento stimata',
        investment_crra_distribution_note='Stime finite per scelte interne (1–99 token). Gli investimenti di 0 o 100 token non identificano una stima puntuale finita.',
        investment_risk_type_boundary='Neutrale o propenso al rischio',
        investment_feedback_crra_note='Per un investimento interno, la stima CRRA è positiva e indica avversione al rischio. Poiché il rendimento atteso è positivo, una scelta neutrale al rischio investirebbe tutti i {endowment} token.',
        investment_feedback_zero_crra='Con 0 token investiti non si ottiene una stima CRRA finita; nel modello questa è una scelta estremamente prudente.',
        investment_feedback_full_crra='Con tutti i token investiti, il modello non distingue tra neutralità e propensione al rischio.',
        reveal_intro='Hai completato tutte le decisioni. Ora vengono rivelati i risultati dei tre compiti.',
        mpl_reveal_title='Compito MPL — estrazione della lotteria',
        mpl_reveal_setup='È stata selezionata la riga {row} e la tua scelta in quella riga era la lotteria {choice}.',
        mpl_reveal_urn='L’urna contiene {high} palline per il payoff alto e {low} per il payoff basso.',
        mpl_reveal_high='Payoff alto: {payoff} token',
        mpl_reveal_low='Payoff basso: {payoff} token',
        mpl_reveal_drawn='È stata estratta la pallina {draw} su 10.',
        bret_reveal_title='Compito BRET — rivelazione delle carte',
        investment_reveal_title='Compito di investimento — esito della ruota',
        investment_reveal_low='Perdi l’investimento · probabilità 2/3',
        investment_reveal_high='L’investimento rende · probabilità 1/3',
        reveal_wait='Estrazione in corso…',
        survey_scatter_note='Ogni punto rappresenta un partecipante; la linea mostra la regressione lineare quando e stimabile.',
        paired_observations='Osservazioni appaiate',
        pearson_correlation='Correlazione di Pearson (r)',
        correlation_unavailable='Non stimabile con queste osservazioni',
        linear_fit_label='Regressione lineare',
        estimated_crra_title='Coefficienti di rischio CRRA stimati',
        crra_distribution_note='Distribuzione del proxy mediano dell\'intervallo stimato in ciascun compito.',
        mpl_crra_coefficients='Coefficienti CRRA MPL',
        bret_crra_coefficients='Coefficienti CRRA BRET',
        individual_scatter_title='Scatterplot CRRA individuale',
        scatter_axis_note='Asse orizzontale: CRRA MPL. Asse verticale: CRRA BRET.',
        individual_paired_estimates='Stime individuali appaiate',
        participant_risk_summary='Riepilogo del profilo di rischio dei partecipanti',
        investment_crra='CRRA investimento',
        self_reported_risk='Rischio autodichiarato',
        average_crra='CRRA media',
        mpl_multiple_switches_warning='Switch multipli MPL',
        mpl_dominated_last_warning='Scelta A dominata nell’ultima riga MPL',
        survey_very_averse='Molto avverso al rischio',
        survey_moderately_averse='Moderatamente avverso al rischio',
        survey_neutral='Neutrale al rischio',
        survey_moderately_seeking='Moderatamente propenso al rischio',
        survey_very_seeking='Molto propenso al rischio',
        investment_zero_boundary='Nessuna stima finita (0 investiti)',
        investment_full_boundary='≤ 0 (investimento totale)',
        crra_table_note='CRRA positive (blu): avversione al rischio; negative (rosso): propensione al rischio. Le stime MPL e BRET sono proxy dei punti medi degli intervalli. La CRRA dell’investimento assume utilità CRRA sui payoff in token e una scelta interna ottimale. La media è la media aritmetica delle sole stime finite disponibili; non è un indice validato. Le risposte sono raggruppate a fini descrittivi: 0–2 molto avverso, 3–4 moderatamente avverso, 5 neutrale, 6–7 moderatamente propenso, 8–10 molto propenso; non sono stime CRRA.',
        participant='Partecipante',
        mpl_crra='CRRA MPL',
        bret_crra='CRRA BRET',
        quadrant='Quadrante',
        cards_turned='Carte girate',
        mpl_switches='Switch MPL',
        no_observations='Nessuna osservazione disponibile',
        mpl_row_axis='Riga MPL',
        mpl_crra_midpoint_axis='Punto medio intervallo CRRA MPL',
        bret_crra_midpoint_axis='Punto medio intervallo CRRA BRET',
        consistently_risk_averse='Coerentemente avverso al rischio',
        consistently_risk_seeker='Coerentemente propenso al rischio',
        bret_seeker_mpl_averse='Propenso in BRET, avverso in MPL',
        bret_averse_mpl_seeker='Avverso in BRET, propenso in MPL',
        on_one_or_both_axes='Su uno o entrambi gli assi',
    ),
    'en': dict(
        language_name='English',
        new_task_title='New task',
        new_task_intro='You are now starting a new task.',
        new_task_read='Please read the next instructions carefully before making your decision.',
        new_task_read_plural='Please read the next instructions carefully before making your decisions.',
        mpl_instructions_title='Instructions',
        mpl_instructions_intro='In this part of the experiment you are going to choose between couples of lotteries.',
        mpl_instructions_example='The following is an example of the decision setting you are facing.',
        my_choice='My choice',
        of='of',
        mpl_example_text='In the example, you must choose between lottery A and lottery B, with lottery A delivering {a_h} with probability 1/10 and {a_l} with probability 9/10.',
        mpl_example_text_b='Similarly, lottery B delivers {b_h} with probability 1/10 and {b_l} with probability 9/10.',
        mpl_choices_count='You will face 10 choices between A and B, with probabilities changing across choices.',
        bonus_payment='Bonus payment',
        mpl_bonus_rule='After you make your choices, one of the 10 choices will be randomly selected. The outcome of the chosen lottery will be computed and the result of your choice will be paid as a bonus payment.',
        virtual_earnings='All your earnings are virtual, no cash is going to be paid to you. However, choose as if the monetary stakes were real.',
        choice_title='Choice',
        mpl_choice_intro='For each row, you have to choose between lottery A and lottery B.',
        mpl_choice_click='To choose, click A or B in each row.',
        mpl_next_hint='When done, please click on the button "Next".',
        mpl_all_rows_selected='All rows have a selected lottery.',
        mpl_rows_selected_template='{selected} of 10 rows selected.',
        bret_instructions_title='Game instructions',
        bret_instructions_intro='You will see 32 cards face down, with one bomb randomly hidden among them. You need to decide how many cards you want to flip, and the software will automatically flip them.',
        bret_fixed_amount='You receive a fixed amount of {amount} euros.',
        bret_rules_title='Game rules',
        bret_rule_zero='If you decide not to flip any cards, you receive the fixed amount of {amount} euros.',
        bret_rule_bomb='If you find the bomb, you keep the fixed amount of {amount} euros but receive no reward for the cards.',
        bret_rule_safe='If you do not find the bomb, your payoff will be {amount} euros plus {value} euros for each card you flipped.',
        continue_to_start='Click on the "Continue" button to start.',
        your_cards_title='Your cards',
        bret_cards_question='How many cards do you want to flip?',
        confirm_choice='OK, confirm my choice',
        continue_button='OK, continue',
        card_back_alt='Card Back',
        bomb_alt='Bomb',
        smiley_alt='Smiley',
        unhappy_alt='Unhappy',
        bret_decided_cards='You decided to turn {cards} cards.',
        bret_found_bomb='Unfortunately, you found the bomb.',
        bret_bomb_payoff='You keep the fixed amount, but you receive no reward for the cards. Accordingly, your payoff is {payoff} tokens.',
        bret_no_bomb='Congratulations! You did not find the bomb.',
        bret_safe_payoff='Accordingly, your payoff is {payoff} tokens.',
        investment_title='Investment task',
        investment_intro='You receive an endowment of {endowment} tokens. Choose how many tokens to invest; you keep the amount you do not invest.',
        investment_low_rule='With probability 2/3, you lose the amount invested and receive {endowment} minus the tokens invested.',
        investment_high_rule='With probability 1/3, you gain 2.5 times the amount invested and receive {endowment} plus 2.5 times the tokens invested.',
        investment_choice_question='How many tokens do you want to invest?',
        investment_choice_hint='Enter a whole number from 0 to {endowment}.',
        investment_preview_title='Possible payoff preview',
        investment_preview_prompt='Enter an amount to see the two possible outcomes.',
        investment_preview_low='If you lose the investment (probability 2/3)',
        investment_preview_high='If the investment pays off (probability 1/3)',
        investment_preview_note='This is only a preview: the actual outcome is determined after you confirm your choice.',
        investment_preview_tokens='tokens',
        investment_result_title='Investment result',
        investment_result_low='The lower-return outcome occurred (probability 2/3).',
        investment_result_high='The higher-return outcome occurred (probability 1/3).',
        investment_chosen='You invested {amount} of {endowment} tokens.',
        investment_result_payoff='Your payoff from this task is {payoff}.',
        investment_payoff_text='Your investment-task payoff is {payoff}.',
        investment_feedback_title='Investment feedback',
        investment_feedback_zero='You invested no tokens and chose the certain payoff.',
        investment_feedback_full='You invested all your tokens.',
        investment_feedback_partial='You invested {amount} of {endowment} tokens. A larger investment raises both the potential gain and the potential loss.',
        general_risk_title='General willingness to take risks',
        general_risk_question='Please tell me, in general, how willing or unwilling you are to take risks.',
        general_risk_instruction='Please use a scale from 0 to 10, where 0 means you are “completely unwilling to take risks” and a 10 means you are “very willing to take risks”.',
        general_risk_numbers='You can also use any numbers between 0 and 10 to indicate where you fall on the scale, like 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10.',
        general_risk_low='Completely unwilling to take risks',
        general_risk_high='Very willing to take risks',
        summary_title='End of risk tasks',
        summary_heading='Summary',
        overall_profile_title='Overall choice profile',
        overall_profile_label='Average tendency across the three tasks',
        overall_profile_very_cautious='Very cautious',
        overall_profile_somewhat_cautious='Somewhat cautious',
        overall_profile_middle='In the middle',
        overall_profile_somewhat_willing='Somewhat willing to take risks',
        overall_profile_very_willing='Very willing to take risks',
        overall_profile_method='Equal-weight average of the interpreted MPL, BRET, and investment-task categories. This describes these decisions, not a stable personal trait.',
        overall_profile_partial='The profile uses {count} of 3 interpretable tasks; ambiguous choices are excluded from the average.',
        overall_profile_unavailable='There are too few interpretable choices to calculate an overall profile.',
        mpl_payoff_text='Your MPL payoff is {payoff}.',
        bret_payoff_text='Your BRET payoff is {payoff}.',
        total_payoff_text='Your total payoff is {payoff}.',
        mpl_feedback_title='MPL feedback',
        bret_feedback_title='BRET feedback',
        risk_type_label='Risk type',
        risk_type_very_averse='Very risk averse',
        risk_type_moderately_averse='Moderately risk averse',
        risk_type_slightly_averse='Slightly risk averse',
        risk_type_neutral='Risk neutral',
        risk_type_moderately_seeking='Moderately risk seeking',
        risk_type_very_seeking='Very risk seeking',
        risk_type_unclear='Unclear from these choices',
        risk_type_note='The MPL, BRET, and investment types describe choices in those tasks under task-specific assumptions, not a stable personal trait.',
        ai_individual_title='AI-mediated feedback',
        mpl_feedback_inconsistent='Your MPL choices were {choices}. They contain {switch_count} switches between A and B, so they do not clearly indicate one risk type.',
        mpl_feedback_all_a='You chose lottery A in every MPL row: the most cautious pattern available in this table.',
        mpl_feedback_first_b='You chose lottery B from the first MPL row: the most risk seeking pattern available in this table.',
        mpl_feedback_switch='You switched from lottery A to lottery B at MPL row {first_b}. This choice suggests the risk type shown above.',
        bret_feedback_zero='In the BRET task you chose not to flip any cards. You kept the fixed amount and did not expose any card earnings to risk.',
        bret_feedback_below='In the BRET task you chose to flip {cards} cards, fewer than the risk-neutral benchmark of about {benchmark} cards in this setup.',
        bret_feedback_equal='In the BRET task you chose to flip {benchmark} cards, which is close to the risk-neutral benchmark in this setup.',
        bret_feedback_above='In the BRET task you chose to flip {cards} cards, above the risk-neutral benchmark of about {benchmark} cards in this setup.',
        bret_feedback_all='In the BRET task you chose to flip all {cards} cards. This guarantees finding the bomb and receiving only the fixed amount, so it does not clearly indicate a risk type.',
        waiting_title='Waiting for the other participants',
        waiting_body='Please wait until everyone has completed the risk tasks.',
        ai_unavailable_title='AI-mediated feedback unavailable',
        ai_unavailable_body='The experiment data were collected correctly, but the automatic feedback cannot be generated right now.',
        ai_unavailable_reason='Reason',
        ai_unavailable_hint='Set <code>openai_api_key</code> in the session configuration, or the <code>OPENAI_API_KEY</code> environment variable, to enable this feedback.',
        ai_group_pending_title='AI-mediated group feedback pending',
        ai_group_pending_body='The group-level feedback will be generated after all participants have completed the three tasks and the general risk question.',
        completed_mpl='Completed MPL',
        completed_bret='Completed BRET',
        completed_investment='Completed investment',
        completed_survey='Completed general question',
        admin_report_title='RISK_PREFS - Admin Report',
        participants='Participants',
        inconsistent_mpl_patterns='Inconsistent MPL patterns',
        mpl_crra_estimates='MPL CRRA estimates',
        bret_crra_estimates='BRET CRRA estimates',
        mean='Mean',
        paired_crra_estimates='Paired CRRA estimates',
        participants_with_both='Participants with both MPL and BRET coefficients',
        ai_group_feedback_title='AI-mediated group feedback',
        distribution_mpl_choices='Distribution of MPL Choices',
        frequency_a_by_row='Frequency of lottery A by row.',
        distribution_bret_choices='Distribution of BRET Choices',
        frequency_cards_turned='Frequency of the number of cards turned.',
        distribution_investment_choices='Distribution of Investments',
        frequency_investment='Number of participants in each investment range.',
        investment_axis='Tokens invested',
        general_risk_distribution='Distribution of general risk question responses',
        general_risk_distribution_note='Number of participants choosing each response from 0 to 10.',
        general_risk_axis='Willingness to take risks (0–10)',
        mpl_survey_scatter_title='General risk response vs. MPL CRRA',
        bret_survey_scatter_title='General risk response vs. BRET CRRA',
        investment_survey_scatter_title='Investment CRRA vs. self-reported general risk',
        report_choice_distribution_title='Distribution of choices',
        report_crra_estimates_title='CRRA estimates',
        report_survey_correlation_title='Correlation between CRRA and self-reported risk',
        report_cross_task_title='Cross-task correlation',
        report_mpl_bret_title='MPL and BRET',
        report_mpl_choice_title='MPL — lottery A choices by row',
        report_bret_choice_title='BRET — number of cards turned',
        report_investment_choice_title='Investment — tokens invested',
        report_survey_choice_title='Self-reported general risk — responses 0–10',
        report_mpl_crra_title='MPL — CRRA distribution',
        report_bret_crra_title='BRET — CRRA distribution',
        report_investment_crra_title='Investment — CRRA distribution',
        investment_crra_axis='Estimated investment CRRA',
        investment_crra_distribution_note='Finite estimates for interior choices (1–99 tokens). Investments of 0 or 100 tokens do not identify a finite point estimate.',
        investment_risk_type_boundary='Risk neutral or risk seeking',
        investment_feedback_crra_note='For an interior investment, the CRRA estimate is positive and indicates risk aversion. Because the expected return is positive, a risk-neutral choice would invest all {endowment} tokens.',
        investment_feedback_zero_crra='Investing 0 tokens has no finite CRRA estimate; in this model it is an extremely cautious choice.',
        investment_feedback_full_crra='Investing all tokens cannot distinguish risk neutrality from risk seeking in this model.',
        reveal_intro='You have completed all decisions. The three task outcomes are now being revealed.',
        mpl_reveal_title='MPL task — lottery draw',
        mpl_reveal_setup='Row {row} was selected, and your choice in that row was lottery {choice}.',
        mpl_reveal_urn='The urn contains {high} balls for the high payoff and {low} for the low payoff.',
        mpl_reveal_high='High payoff: {payoff} tokens',
        mpl_reveal_low='Low payoff: {payoff} tokens',
        mpl_reveal_drawn='Ball {draw} of 10 was drawn.',
        bret_reveal_title='BRET task — card reveal',
        investment_reveal_title='Investment task — wheel outcome',
        investment_reveal_low='Investment lost · probability 2/3',
        investment_reveal_high='Investment pays off · probability 1/3',
        reveal_wait='Drawing the outcomes…',
        survey_scatter_note='Each point is one participant; the line shows the linear fit when estimable.',
        paired_observations='Paired observations',
        pearson_correlation='Pearson correlation (r)',
        correlation_unavailable='Not estimable from these observations',
        linear_fit_label='Linear fit',
        estimated_crra_title='Estimated CRRA Risk Coefficients',
        crra_distribution_note='Distribution of the midpoint proxy from the estimated interval in each task.',
        mpl_crra_coefficients='MPL CRRA coefficients',
        bret_crra_coefficients='BRET CRRA coefficients',
        individual_scatter_title='Individual CRRA Scatterplot',
        scatter_axis_note='Horizontal axis: MPL CRRA. Vertical axis: BRET CRRA.',
        individual_paired_estimates='Individual paired estimates',
        participant_risk_summary='Participant Risk Profile Summary',
        investment_crra='Investment CRRA',
        self_reported_risk='Self-reported risk',
        average_crra='Average CRRA',
        mpl_multiple_switches_warning='Multiple MPL switches',
        mpl_dominated_last_warning='Dominated A choice in final MPL row',
        survey_very_averse='Very risk averse',
        survey_moderately_averse='Moderately risk averse',
        survey_neutral='Risk neutral',
        survey_moderately_seeking='Moderately risk seeking',
        survey_very_seeking='Very risk seeking',
        investment_zero_boundary='No finite estimate (0 invested)',
        investment_full_boundary='≤ 0 (full investment)',
        crra_table_note='Positive CRRA (blue): risk aversion; negative CRRA (red): risk seeking. MPL and BRET estimates are interval-midpoint proxies. Investment CRRA assumes CRRA utility over token payoffs and an interior optimal choice. The average is the arithmetic mean of available finite estimates only; it is not a validated index. Survey responses are grouped descriptively: 0–2 very averse, 3–4 moderately averse, 5 neutral, 6–7 moderately seeking, 8–10 very seeking; they are not CRRA estimates.',
        participant='Participant',
        mpl_crra='MPL CRRA',
        bret_crra='BRET CRRA',
        quadrant='Quadrant',
        cards_turned='Cards turned',
        mpl_switches='MPL switches',
        no_observations='No observations yet',
        mpl_row_axis='MPL row',
        mpl_crra_midpoint_axis='MPL CRRA interval midpoint',
        bret_crra_midpoint_axis='BRET CRRA interval midpoint',
        consistently_risk_averse='Consistently risk averse',
        consistently_risk_seeker='Consistently risk seeker',
        bret_seeker_mpl_averse='BRET seeker, MPL averse',
        bret_averse_mpl_seeker='BRET averse, MPL seeker',
        on_one_or_both_axes='On one or both axes',
    ),
}


def get_language(source):
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
    pass


class Player(BasePlayer):
    task_order = models.StringField()

    HL_1 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_2 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_3 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_4 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_5 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_6 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_7 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_8 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_9 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    HL_10 = models.CharField(choices=['A', 'B'], widget=widgets.RadioSelectHorizontal)
    mpl_row = models.IntegerField()
    mpl_drawn = models.IntegerField()
    mpl_choice = models.CharField()
    mpl_payoff = models.CurrencyField()
    mpl_crra_lower = models.FloatField(blank=True)
    mpl_crra_upper = models.FloatField(blank=True)
    mpl_crra_proxy = models.FloatField(blank=True)
    mpl_num_switches = models.IntegerField(blank=True)
    mpl_multiple_switches = models.BooleanField(initial=False)
    mpl_inconsistent_choices = models.BooleanField(initial=False)

    cards_flipped = models.IntegerField(min=0, max=C.BRET_NUM_CARDS)
    selected_bret_cards = models.LongStringField(blank=True)
    bomb_position = models.IntegerField()
    bomb_found = models.BooleanField()
    bret_payoff = models.CurrencyField()
    bret_crra_lower = models.FloatField(blank=True)
    bret_crra_upper = models.FloatField(blank=True)
    bret_crra_proxy = models.FloatField(blank=True)
    investment_amount = models.IntegerField(min=0, max=C.INVESTMENT_ENDOWMENT)
    investment_draw = models.IntegerField()
    investment_high_return = models.BooleanField()
    investment_payoff = models.CurrencyField()
    general_risk_willingness = models.IntegerField(min=0, max=10)
    total_payoff = models.CurrencyField()


_MPL_CRRA_THRESHOLDS = None
_BRET_CRRA_INTERVALS = None


def creating_session(subsession: Subsession):
    players = subsession.get_players()
    possible_orders = list(permutations(
        (C.MPL_TASK, C.BRET_TASK, C.INVESTMENT_TASK)
    ))
    orders = possible_orders * ((len(players) + len(possible_orders) - 1) // len(possible_orders))
    random.shuffle(orders)
    for player, order in zip(players, orders):
        player.task_order = ','.join(order)


def task_at(player: Player, position):
    # Existing sessions may still hold one of the former two-task order values.
    legacy_orders = {
        'MPL_FIRST': (C.MPL_TASK, C.BRET_TASK, C.INVESTMENT_TASK),
        'BRET_FIRST': (C.BRET_TASK, C.MPL_TASK, C.INVESTMENT_TASK),
    }
    order = legacy_orders.get(player.task_order)
    if order is None:
        order = player.task_order.split(',')
    return order[position - 1]


def update_total_payoff(player: Player):
    mpl_payoff = player.field_maybe_none('mpl_payoff') or 0
    bret_payoff = player.field_maybe_none('bret_payoff') or 0
    investment_payoff = player.field_maybe_none('investment_payoff') or 0
    player.total_payoff = mpl_payoff + bret_payoff + investment_payoff
    player.payoff = player.total_payoff


def crra_utility(x, r):
    if abs(r - 1) < 1e-9:
        return math.log(x)
    return x ** (1 - r) / (1 - r)


def find_root(function, lower, upper):
    lower_value = function(lower)
    upper_value = function(upper)
    if lower_value == 0:
        return lower
    if upper_value == 0:
        return upper
    if lower_value * upper_value > 0:
        return None

    for _ in range(80):
        middle = (lower + upper) / 2
        middle_value = function(middle)
        if abs(middle_value) < 1e-12:
            return middle
        if lower_value * middle_value <= 0:
            upper = middle
            upper_value = middle_value
        else:
            lower = middle
            lower_value = middle_value
    return (lower + upper) / 2


def get_mpl_crra_thresholds():
    global _MPL_CRRA_THRESHOLDS
    if _MPL_CRRA_THRESHOLDS is not None:
        return _MPL_CRRA_THRESHOLDS

    thresholds = []
    for row in range(1, 10):
        probability_high = row / 10

        def difference(r):
            eu_a = (
                probability_high * crra_utility(C.MPL_A_H, r)
                + (1 - probability_high) * crra_utility(C.MPL_A_L, r)
            )
            eu_b = (
                probability_high * crra_utility(C.MPL_B_H, r)
                + (1 - probability_high) * crra_utility(C.MPL_B_L, r)
            )
            return eu_a - eu_b

        thresholds.append(
            find_root(difference, C.CRRA_SEARCH_MIN, C.CRRA_SEARCH_MAX)
        )
    _MPL_CRRA_THRESHOLDS = thresholds
    return thresholds


def set_mpl_crra(player: Player, choices):
    thresholds = get_mpl_crra_thresholds()
    switch_count = sum(
        previous != current
        for previous, current in zip(choices, choices[1:])
    )
    player.mpl_num_switches = switch_count
    player.mpl_multiple_switches = switch_count > 1
    first_b = get_first_b_row(choices)
    player.mpl_inconsistent_choices = (
        first_b is not None and 'A' in choices[first_b:]
    )

    if player.mpl_inconsistent_choices:
        player.mpl_crra_lower = None
        player.mpl_crra_upper = None
        player.mpl_crra_proxy = None
        return

    if first_b is None:
        lower = thresholds[-1]
        upper = None
    elif first_b == 1:
        lower = None
        upper = thresholds[0]
    elif first_b >= 10:
        lower = thresholds[-1]
        upper = None
    else:
        lower = thresholds[first_b - 2]
        upper = thresholds[first_b - 1]

    player.mpl_crra_lower = lower
    player.mpl_crra_upper = upper
    player.mpl_crra_proxy = (
        (lower + upper) / 2
        if lower is not None and upper is not None
        else None
    )


def bret_expected_utility(cards_flipped, r):
    background = C.CRRA_BACKGROUND_WEALTH
    if cards_flipped == 0:
        return crra_utility(background + C.BRET_ENDOWMENT, r)

    safe_probability = (C.BRET_NUM_CARDS - cards_flipped) / C.BRET_NUM_CARDS
    safe_payoff = background + C.BRET_ENDOWMENT + C.BRET_CARD_VALUE * cards_flipped
    bomb_payoff = background + C.BRET_ENDOWMENT
    return (
        safe_probability * crra_utility(safe_payoff, r)
        + (1 - safe_probability) * crra_utility(bomb_payoff, r)
    )


def get_bret_crra_intervals():
    global _BRET_CRRA_INTERVALS
    if _BRET_CRRA_INTERVALS is not None:
        return _BRET_CRRA_INTERVALS

    values = {cards: [] for cards in range(C.BRET_NUM_CARDS + 1)}
    num_steps = round((C.CRRA_SEARCH_MAX - C.CRRA_SEARCH_MIN) / C.CRRA_GRID_STEP)
    for step in range(num_steps + 1):
        r = C.CRRA_SEARCH_MIN + step * C.CRRA_GRID_STEP
        expected_utilities = [
            bret_expected_utility(cards, r)
            for cards in range(C.BRET_NUM_CARDS + 1)
        ]
        best_utility = max(expected_utilities)
        for cards, expected_utility in enumerate(expected_utilities):
            if abs(expected_utility - best_utility) < 1e-10:
                values[cards].append(r)
                break

    _BRET_CRRA_INTERVALS = {
        cards: (
            min(r_values),
            max(r_values),
            (min(r_values) + max(r_values)) / 2,
        )
        for cards, r_values in values.items()
        if r_values
    }
    return _BRET_CRRA_INTERVALS


def set_bret_crra(player: Player):
    if player.field_maybe_none('cards_flipped') is None:
        player.bret_crra_lower = None
        player.bret_crra_upper = None
        player.bret_crra_proxy = None
        return

    interval = get_bret_crra_intervals().get(player.cards_flipped)
    if interval is None:
        player.bret_crra_lower = None
        player.bret_crra_upper = None
        player.bret_crra_proxy = None
        return
    lower, upper, proxy = interval
    player.bret_crra_lower = lower
    player.bret_crra_upper = upper
    player.bret_crra_proxy = proxy


def risk_type_from_crra(value):
    """Broad, illustrative bands around the risk-neutral value of zero."""
    if value is None:
        return None
    if value >= 1:
        return 'risk_type_very_averse'
    if value > 0.25:
        return 'risk_type_moderately_averse'
    if value >= -0.25:
        return 'risk_type_neutral'
    if value > -1:
        return 'risk_type_moderately_seeking'
    return 'risk_type_very_seeking'


def mpl_risk_type(player: Player):
    if player.field_maybe_none('mpl_inconsistent_choices'):
        return 'risk_type_unclear'
    first_b = get_first_b_row(get_mpl_choices(player))
    if first_b is None or first_b >= 10:
        return 'risk_type_very_averse'
    if first_b == 1:
        return 'risk_type_very_seeking'
    return risk_type_from_crra(player.field_maybe_none('mpl_crra_proxy')) or 'risk_type_unclear'


def bret_risk_type(player: Player):
    cards = player.field_maybe_none('cards_flipped')
    if cards is None:
        return 'risk_type_unclear'
    if cards == C.BRET_NUM_CARDS:
        return 'risk_type_unclear'
    # Descriptive bands around the 16-card risk-neutral choice. They also
    # cover choices with no CRRA estimate, including zero and 28–31 cards.
    if cards <= 8:
        return 'risk_type_very_averse'
    if cards <= 14:
        return 'risk_type_moderately_averse'
    if cards <= 17:
        return 'risk_type_neutral'
    if cards <= 23:
        return 'risk_type_moderately_seeking'
    return 'risk_type_very_seeking'


def investment_risk_type(player: Player):
    amount = player.field_maybe_none('investment_amount')
    if amount is None:
        return 'risk_type_unclear'
    if amount == 0:
        return 'risk_type_very_averse'
    if amount == C.INVESTMENT_ENDOWMENT:
        return 'investment_risk_type_boundary'
    estimate = investment_crra_estimate(amount)
    if estimate is None:
        return 'risk_type_unclear'
    if estimate > 0.25:
        return (
            'risk_type_very_averse'
            if estimate >= 1
            else 'risk_type_moderately_averse'
        )
    return 'risk_type_slightly_averse'


def format_text(source, key, **kwargs):
    return get_text(source)[key].format(**kwargs)


def get_mpl_choices(player: Player):
    return [
        player.HL_1,
        player.HL_2,
        player.HL_3,
        player.HL_4,
        player.HL_5,
        player.HL_6,
        player.HL_7,
        player.HL_8,
        player.HL_9,
        player.HL_10,
    ]


def get_first_b_row(choices):
    return next((i for i, choice in enumerate(choices, start=1) if choice == 'B'), None)


def mpl_behavior_feedback(player: Player):
    choices = get_mpl_choices(player)
    first_b = get_first_b_row(choices)
    switch_count = player.field_maybe_none('mpl_num_switches')

    if player.field_maybe_none('mpl_inconsistent_choices'):
        return format_text(
            player,
            'mpl_feedback_inconsistent',
            choices=' '.join(choices),
            switch_count=switch_count,
        )
    if first_b is None:
        return format_text(player, 'mpl_feedback_all_a')
    if first_b == 1:
        return format_text(player, 'mpl_feedback_first_b')
    return format_text(player, 'mpl_feedback_switch', first_b=first_b)


def bret_behavior_feedback(player: Player):
    cards = player.cards_flipped
    if cards == 0:
        return format_text(player, 'bret_feedback_zero')
    if cards < C.BRET_RISK_NEUTRAL_CARDS:
        return format_text(
            player,
            'bret_feedback_below',
            cards=cards,
            benchmark=C.BRET_RISK_NEUTRAL_CARDS,
        )
    if cards == C.BRET_RISK_NEUTRAL_CARDS:
        return format_text(
            player,
            'bret_feedback_equal',
            benchmark=C.BRET_RISK_NEUTRAL_CARDS,
        )
    if cards < C.BRET_NUM_CARDS:
        return format_text(
            player,
            'bret_feedback_above',
            cards=cards,
            benchmark=C.BRET_RISK_NEUTRAL_CARDS,
        )
    return format_text(player, 'bret_feedback_all', cards=C.BRET_NUM_CARDS)


def investment_behavior_feedback(player: Player):
    amount = player.field_maybe_none('investment_amount')
    if amount == 0:
        return (format_text(player, 'investment_feedback_zero') + ' '
                + format_text(player, 'investment_feedback_zero_crra'))
    if amount == C.INVESTMENT_ENDOWMENT:
        return (format_text(player, 'investment_feedback_full') + ' '
                + format_text(player, 'investment_feedback_full_crra'))
    return format_text(
        player, 'investment_feedback_partial',
        amount=amount, endowment=C.INVESTMENT_ENDOWMENT,
    ) + ' ' + format_text(
        player,
        'investment_feedback_crra_note',
        endowment=C.INVESTMENT_ENDOWMENT,
    )


def mean_or_none(values):
    return sum(values) / len(values) if values else None


def round_or_none(value, digits=3):
    return round(value, digits) if value is not None else None


def float_or_none(value):
    return float(value) if value is not None else None


def participant_label(player: Player):
    return player.participant.label or player.participant.code


def investment_crra_estimate(amount):
    """Interior optimum under CRRA utility of the investment task's token payoff."""
    if amount is None or amount <= 0 or amount >= C.INVESTMENT_ENDOWMENT:
        return None
    low_payoff = C.INVESTMENT_ENDOWMENT - amount
    high_payoff = C.INVESTMENT_ENDOWMENT + C.INVESTMENT_HIGH_RETURN_MULTIPLIER * amount
    marginal_return_ratio = C.INVESTMENT_HIGH_RETURN_MULTIPLIER / 2
    return math.log(marginal_return_ratio) / math.log(high_payoff / low_payoff)


def report_crra_cell(value):
    if value is None:
        return dict(text='—', style='')
    strength = min(abs(value) / 2, 1)
    opacity = 0.12 + 0.28 * strength
    if value > 0:
        color = '30, 100, 210'
        foreground = '#173b79'
    elif value < 0:
        color = '210, 55, 65'
        foreground = '#8c2330'
    else:
        color = '100, 110, 120'
        foreground = '#404850'
    return dict(
        text=f'{value:.3f}',
        style=f'background-color: rgba({color}, {opacity:.3f}); color: {foreground};',
    )


def report_survey_type(answer):
    if answer <= 2:
        return 'survey_very_averse'
    if answer <= 4:
        return 'survey_moderately_averse'
    if answer == 5:
        return 'survey_neutral'
    if answer <= 7:
        return 'survey_moderately_seeking'
    return 'survey_very_seeking'


RISK_PREFS_AI_SYSTEM_PROMPTS = {
    'individual': dedent(
        """
        You are a teaching assistant specializing in experimental economics and
        risk preferences.

        Write very concise individual feedback for one participant in an oTree
        risk preference experiment with MPL, BRET, and investment tasks.

        Rules:
        - Use only the JSON data provided.
        - Address the participant as "you".
        - Do not infer personality, stable traits, clinical features, or motives.
        - Lead with the supplied risk types for MPL, BRET, and investment.
        - For full investment, say that the task cannot distinguish risk
          neutrality from risk seeking.
        - Use the supplied overall profile as an approximate summary of the
          three choices; do not reinterpret it as a measured personal trait.
        - Describe them as interpretations of task choices, not stable traits.
        - Do not print CRRA values or intervals in participant feedback.
        - Explain inconsistent MPL choices neutrally; do not assign them a
          definite MPL risk type.
            - Violations of stochastic dominance (choosing A in the last MPL row) should be noted.
            - Multiple switches in the MPL should be noted.
            - Choosing to turn all cards in the BRET should be noted.
            - Choosing to turn no cards in the BRET should be noted.
        - Keep the text under 120 words and suitable for a classroom debrief.
        - Produce only an HTML fragment, not Markdown.

        Required structure:
        <p>One short sentence each for MPL, BRET, and investment.</p>
        <p>One short sentence on the overall profile and its limitations.</p>
        - In the MPL sentence, state the first row in which the participant
          switched to lottery B when that row is available.
        - If the MPL choices are inconsistent, explain briefly that no single
          MPL risk type can be inferred.
        - If lottery A was chosen in the last row, note the violation of
          stochastic dominance (non-monotonicity).
        """
    ).strip(),
    'group': dedent(
        """
        You are a teaching assistant specializing in experimental economics and
        risk preferences.

        Comment on aggregate results from an oTree risk preference experiment
        with MPL, BRET, and investment tasks for an admin report.

        Rules:
        - Use only the JSON data provided.
        - Do not invent unobserved motives or psychological explanations.
        - Distinguish descriptive patterns from possible teaching
          interpretations.
        - Cite numerical values when useful.
        - Mention data-quality issues such as inconsistent MPL switching if
          present.
        - Keep the text concise and suitable for classroom discussion.
        - Produce only an HTML fragment, not Markdown.

        Required structure:
        <h4>General reading</h4>
        <h4>MPL patterns</h4>
            - Highlight anomalous or inconsistent switching patterns.
                - Multiple switches, or choosing A in the last row, should be noted. 
        <h4>BRET patterns</h4>
        <h4>Investment patterns</h4>
        <h4>Comparison of CRRA estimates</h4>
        <h4>Debriefing prompts</h4>
        """
    ).strip(),
}


def _clean_text(value):
    return " ".join(str(value or "").split()).strip()


def _session_openai_settings(session):
    session_config = session.config or {}
    api_key = session_config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    model = (
        session_config.get("openai_risk_prefs_model")
        or session_config.get("openai_pgg_model")
        or session_config.get("openai_case_model")
        or os.getenv("OPENAI_RISK_PREFS_MODEL")
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
        missing_items.append(
            "the Python package 'openai' is not installed"
            if lang == 'en'
            else "il pacchetto Python 'openai' non e installato"
        )
    if not settings["api_key"]:
        if lang == 'en':
            missing_items.append(
                "no OpenAI key was found in the session configuration "
                "('openai_api_key') or in the OPENAI_API_KEY environment variable"
            )
        else:
            missing_items.append(
                "non e stata trovata alcuna chiave OpenAI nella configurazione "
                "della sessione ('openai_api_key') o nella variabile d'ambiente "
                "OPENAI_API_KEY"
            )
    return "; ".join(missing_items)


def _openai_client(session):
    settings = _session_openai_settings(session)
    if openai is None or not settings["api_key"]:
        return None
    return openai.OpenAI(api_key=settings["api_key"])


def _ai_feedback_enabled(session):
    """Return True only when a session explicitly opts in to AI feedback."""
    return (session.config or {}).get("enable_ai_feedback") is True


def _ai_feedback_unavailable_html(source, reason):
    t = get_text(source)
    return (
        f"<h4>{t['ai_unavailable_title']}</h4>"
        f"<p>{t['ai_unavailable_body']}</p>"
        f"<p><strong>{t['ai_unavailable_reason']}:</strong> "
        f"{escape(reason or 'OpenAI client unavailable')}</p>"
        f"<p>{t['ai_unavailable_hint']}</p>"
    )


def _risk_prefs_player_payload(player: Player):
    set_bret_crra(player)
    update_total_payoff(player)
    choices = get_mpl_choices(player)
    profile_key, profile_task_count = overall_choice_profile(
        mpl_risk_type(player),
        bret_risk_type(player),
        investment_risk_type(player),
    )
    return dict(
        experiment=dict(
            name="Risk Preferences",
            tasks=["MPL_HL", "BRET", "INVESTMENT"],
            bret_num_cards=C.BRET_NUM_CARDS,
            bret_fixed_payoff=C.BRET_ENDOWMENT,
            bret_card_value=C.BRET_CARD_VALUE,
            bret_risk_neutral_cards=C.BRET_RISK_NEUTRAL_CARDS,
        ),
        participant=dict(
            task_order=player.task_order,
            readable_order=', then '.join(task_at(player, i) for i in range(1, 4)),
        ),
        mpl=dict(
            choices=choices,
            risk_type=get_text(player)[mpl_risk_type(player)],
            first_b_row=get_first_b_row(choices),
            num_switches=player.field_maybe_none('mpl_num_switches'),
            inconsistent_choices=bool(player.field_maybe_none('mpl_inconsistent_choices')),
            payoff=float_or_none(player.field_maybe_none('mpl_payoff')),
            selected_row=player.field_maybe_none('mpl_row'),
            draw=player.field_maybe_none('mpl_drawn'),
            selected_choice=player.field_maybe_none('mpl_choice'),
            deterministic_feedback=mpl_behavior_feedback(player),
        ),
        bret=dict(
            cards_flipped=player.field_maybe_none('cards_flipped'),
            risk_type=get_text(player)[bret_risk_type(player)],
            bomb_position=player.field_maybe_none('bomb_position'),
            bomb_found=player.field_maybe_none('bomb_found'),
            payoff=float_or_none(player.field_maybe_none('bret_payoff')),
            deterministic_feedback=bret_behavior_feedback(player),
        ),
        investment=dict(
            endowment=C.INVESTMENT_ENDOWMENT,
            amount=player.field_maybe_none('investment_amount'),
            risk_type=get_text(player)[investment_risk_type(player)],
            crra_estimate=investment_crra_estimate(player.field_maybe_none('investment_amount')),
            high_return=player.field_maybe_none('investment_high_return'),
            payoff=float_or_none(player.field_maybe_none('investment_payoff')),
            deterministic_feedback=investment_behavior_feedback(player),
        ),
        overall_profile=dict(
            label=get_text(player)[profile_key] if profile_key else None,
            tasks_used=profile_task_count,
            tasks_total=3,
            method='Equal-weight average of the interpreted task categories',
        ),
        total_payoff=float_or_none(player.field_maybe_none('total_payoff')),
    )


def _risk_prefs_individual_ai_feedback(player: Player):
    payload = _risk_prefs_player_payload(player)
    lang = get_language(player)
    fingerprint = sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    cache_key = "risk_prefs_individual_ai_feedback"
    cached = player.participant.vars.get(cache_key)
    if cached and cached.get("fingerprint") == fingerprint:
        cached_html = cached.get("html", "")
        if "AI-mediated feedback unavailable" not in cached_html:
            return cached_html

    client = _openai_client(player.session)
    if client is None:
        return _ai_feedback_unavailable_html(player, _openai_unavailable_reason(player.session))

    settings = _session_openai_settings(player.session)
    prompt = dedent(
        f"""
        Participant data in JSON format:
        {json.dumps(payload, ensure_ascii=False, indent=2)}

        Write the feedback in {'Italian' if lang == 'it' else 'English'}.

        Write individual feedback for the participant. Explain:
        - what their MPL pattern indicates and its supplied risk type;
        - how their BRET number of cards compares with the risk-neutral
          benchmark of {C.BRET_RISK_NEUTRAL_CARDS} and its supplied risk type;
        - what their investment amount and supplied model-based risk type suggest;
        - the supplied overall choice profile and its limitations;
        - whether the three tasks point in a similar or different direction.

        Use the supplied risk-type labels exactly. Do not report numerical
        CRRA estimates. Treat the labels as descriptive and approximate.
        """
    ).strip()

    try:
        response = client.chat.completions.create(
            model=settings["model"],
            messages=[
                {"role": "system", "content": RISK_PREFS_AI_SYSTEM_PROMPTS['individual']},
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
        )
        html = _clean_text(response.choices[0].message.content)
        if not html:
            return _ai_feedback_unavailable_html(player, "the model returned an empty response")
    except Exception as exc:
        return _ai_feedback_unavailable_html(player, str(exc))

    player.participant.vars[cache_key] = dict(fingerprint=fingerprint, html=html)
    return html


def make_crra_histogram(mpl_values, bret_values, bin_width=0.5):
    values = mpl_values + bret_values
    if not values:
        return []

    lower = math.floor(min(values) / bin_width) * bin_width
    upper = math.ceil(max(values) / bin_width) * bin_width
    if lower == upper:
        upper = lower + bin_width

    rows = []
    current = lower
    while current < upper:
        next_value = current + bin_width
        is_last = next_value >= upper
        mpl_count = sum(
            current <= value <= next_value if is_last else current <= value < next_value
            for value in mpl_values
        )
        bret_count = sum(
            current <= value <= next_value if is_last else current <= value < next_value
            for value in bret_values
        )
        rows.append(dict(
            label=f'{current:.1f} to {next_value:.1f}',
            lower=round(current, 3),
            upper=round(next_value, 3),
            mpl_count=mpl_count,
            bret_count=bret_count,
        ))
        current = next_value
    return rows


def make_single_crra_histogram(values, bin_width=0.5):
    if not values:
        return []
    lower = math.floor(min(values) / bin_width) * bin_width
    upper = math.ceil(max(values) / bin_width) * bin_width
    if lower == upper:
        upper += bin_width
    rows = []
    current = lower
    while current < upper:
        next_value = current + bin_width
        is_last = next_value >= upper
        rows.append(dict(
            label=f'{current:.1f} to {next_value:.1f}',
            count=sum(
                current <= value <= next_value if is_last else current <= value < next_value
                for value in values
            ),
        ))
        current = next_value
    return rows


def classify_crra_pair(mpl_value, bret_value):
    if mpl_value > 0 and bret_value > 0:
        return 'consistently_risk_averse'
    if mpl_value < 0 and bret_value < 0:
        return 'consistently_risk_seeker'
    if mpl_value > 0 and bret_value < 0:
        return 'bret_seeker_mpl_averse'
    if mpl_value < 0 and bret_value > 0:
        return 'bret_averse_mpl_seeker'
    return 'on_one_or_both_axes'


def survey_task_relationship(players, measure_field):
    """Pair observed survey answers with observed task measures."""
    points = []
    for player in players:
        answer = player.field_maybe_none('general_risk_willingness')
        measure = (
            measure_field(player) if callable(measure_field)
            else player.field_maybe_none(measure_field)
        )
        if answer is not None and measure is not None:
            points.append(dict(x=answer, y=measure))

    return relationship_from_points(points)


def relationship_from_points(points):
    """Pearson correlation and ordinary least-squares line for paired points."""

    result = dict(points=points, n=len(points), r=None, fit=[])
    if len(points) < 2:
        return result

    mean_x = sum(point['x'] for point in points) / len(points)
    mean_y = sum(point['y'] for point in points) / len(points)
    sum_xx = sum((point['x'] - mean_x) ** 2 for point in points)
    if sum_xx == 0:
        return result

    sum_xy = sum(
        (point['x'] - mean_x) * (point['y'] - mean_y)
        for point in points
    )
    slope = sum_xy / sum_xx
    intercept = mean_y - slope * mean_x
    min_x = min(point['x'] for point in points)
    max_x = max(point['x'] for point in points)
    result['fit'] = [
        dict(x=x, y=intercept + slope * x)
        for x in (min_x, max_x)
    ]

    sum_yy = sum((point['y'] - mean_y) ** 2 for point in points)
    if sum_yy > 0:
        result['r'] = round(sum_xy / math.sqrt(sum_xx * sum_yy), 3)
    return result


def vars_for_admin_report(subsession: Subsession):
    players = subsession.get_players()
    t = get_text(subsession.session)

    for player in players:
        set_bret_crra(player)

    mpl_rows = []
    for row in range(1, 11):
        choices = [
            player.field_maybe_none(f'HL_{row}')
            for player in players
        ]
        count_a = sum(choice == 'A' for choice in choices)
        count_b = sum(choice == 'B' for choice in choices)
        observed = count_a + count_b
        mpl_rows.append(dict(
            row=row,
            count_a=count_a,
            count_b=count_b,
            observed=observed,
            missing=len(players) - observed,
            frequency_a=round_or_none(count_a / observed, 3) if observed else None,
            percent_a=round_or_none(100 * count_a / observed, 1) if observed else None,
        ))

    bret_rows = []
    for cards in range(C.BRET_NUM_CARDS + 1):
        count = sum(
            player.field_maybe_none('cards_flipped') == cards
            for player in players
        )
        bret_rows.append(dict(cards=cards, count=count))

    investment_amounts = [
        player.field_maybe_none('investment_amount')
        for player in players
        if player.field_maybe_none('investment_amount') is not None
    ]
    investment_bin_width = max(1, C.INVESTMENT_ENDOWMENT // 10)
    investment_rows = [
        dict(
            label=(
                str(start) if start == C.INVESTMENT_ENDOWMENT
                else f'{start}–{min(start + investment_bin_width - 1, C.INVESTMENT_ENDOWMENT)}'
            ),
            count=sum(
                start <= amount <= min(start + investment_bin_width - 1, C.INVESTMENT_ENDOWMENT)
                for amount in investment_amounts
            ),
        )
        for start in range(0, C.INVESTMENT_ENDOWMENT + 1, investment_bin_width)
    ]

    mpl_crra_values = [
        player.field_maybe_none('mpl_crra_proxy')
        for player in players
        if player.field_maybe_none('mpl_crra_proxy') is not None
    ]
    bret_crra_values = [
        player.field_maybe_none('bret_crra_proxy')
        for player in players
        if player.field_maybe_none('bret_crra_proxy') is not None
    ]
    investment_crra_values = []
    for player in players:
        estimate = investment_crra_estimate(player.field_maybe_none('investment_amount'))
        if estimate is not None:
            investment_crra_values.append(estimate)
    crra_histogram = make_crra_histogram(mpl_crra_values, bret_crra_values)
    investment_crra_histogram = make_single_crra_histogram(investment_crra_values)
    general_risk_rows = [
        dict(answer=answer, count=sum(
            player.field_maybe_none('general_risk_willingness') == answer
            for player in players
        ))
        for answer in range(11)
    ]
    mpl_survey_relationship = survey_task_relationship(players, 'mpl_crra_proxy')
    bret_survey_relationship = survey_task_relationship(players, 'bret_crra_proxy')
    investment_survey_relationship = survey_task_relationship(
        players,
        lambda player: investment_crra_estimate(player.field_maybe_none('investment_amount')),
    )

    participant_risk_rows = []
    for player in players:
        mpl_value = player.field_maybe_none('mpl_crra_proxy')
        bret_value = player.field_maybe_none('bret_crra_proxy')
        amount = player.field_maybe_none('investment_amount')
        investment_value = investment_crra_estimate(amount)
        survey_answer = player.field_maybe_none('general_risk_willingness')
        finite_values = [
            value for value in (mpl_value, bret_value, investment_value)
            if value is not None and math.isfinite(value)
        ]
        average = mean_or_none(finite_values)
        warnings = []
        if player.field_maybe_none('mpl_multiple_switches'):
            warnings.append(t['mpl_multiple_switches_warning'])
        if player.field_maybe_none('HL_10') == 'A':
            warnings.append(t['mpl_dominated_last_warning'])
        investment_cell = report_crra_cell(investment_value)
        if amount == 0:
            investment_cell['text'] = t['investment_zero_boundary']
        elif amount == C.INVESTMENT_ENDOWMENT:
            investment_cell['text'] = t['investment_full_boundary']
        participant_risk_rows.append(dict(
            participant=participant_label(player),
            mpl=report_crra_cell(mpl_value),
            bret=report_crra_cell(bret_value),
            investment=investment_cell,
            survey=(
                f"{survey_answer}/10 — {t[report_survey_type(survey_answer)]}"
                if survey_answer is not None else '—'
            ),
            average=report_crra_cell(average),
            average_count=len(finite_values),
            warnings=warnings,
        ))

    scatter_points = []
    quadrant_counts = {
        'consistently_risk_averse': 0,
        'consistently_risk_seeker': 0,
        'bret_seeker_mpl_averse': 0,
        'bret_averse_mpl_seeker': 0,
        'on_one_or_both_axes': 0,
    }
    for player in players:
        mpl_value = player.field_maybe_none('mpl_crra_proxy')
        bret_value = player.field_maybe_none('bret_crra_proxy')
        if mpl_value is None or bret_value is None:
            continue
        quadrant = classify_crra_pair(mpl_value, bret_value)
        quadrant_counts[quadrant] += 1
        scatter_points.append(dict(
            participant=participant_label(player),
            mpl=round(mpl_value, 3),
            bret=round(bret_value, 3),
            mpl_raw=mpl_value,
            bret_raw=bret_value,
            quadrant=t[quadrant],
            cards_flipped=player.field_maybe_none('cards_flipped'),
            mpl_switches=player.field_maybe_none('mpl_num_switches'),
        ))
    cross_task_relationship = relationship_from_points([
        dict(x=point['mpl_raw'], y=point['bret_raw'])
        for point in scatter_points
    ])

    completed_mpl = sum(
        all(player.field_maybe_none(f'HL_{row}') is not None for row in range(1, 11))
        for player in players
    )
    completed_bret = sum(
        player.field_maybe_none('cards_flipped') is not None
        for player in players
    )
    completed_investment = len(investment_amounts)
    completed_survey = sum(
        player.field_maybe_none('general_risk_willingness') is not None
        for player in players
    )
    inconsistent_mpl = sum(
        bool(player.field_maybe_none('mpl_inconsistent_choices'))
        for player in players
    )
    all_finished = (
        len(players) > 0
        and completed_mpl == len(players)
        and completed_bret == len(players)
        and completed_investment == len(players)
        and completed_survey == len(players)
    )

    report_data = dict(
        **common_template_vars(subsession.session),
        total_players=len(players),
        completed_mpl=completed_mpl,
        completed_bret=completed_bret,
        completed_investment=completed_investment,
        completed_survey=completed_survey,
        all_finished=all_finished,
        inconsistent_mpl=inconsistent_mpl,
        mpl_rows=mpl_rows,
        bret_rows=bret_rows,
        investment_rows=investment_rows,
        crra_histogram=crra_histogram,
        investment_crra_histogram=investment_crra_histogram,
        general_risk_rows=general_risk_rows,
        mpl_survey_relationship=mpl_survey_relationship,
        bret_survey_relationship=bret_survey_relationship,
        investment_survey_relationship=investment_survey_relationship,
        participant_risk_rows=participant_risk_rows,
        scatter_points=scatter_points,
        cross_task_relationship=cross_task_relationship,
        quadrant_counts=[
            dict(label=t[label], count=count)
            for label, count in quadrant_counts.items()
        ],
        mpl_crra_n=len(mpl_crra_values),
        bret_crra_n=len(bret_crra_values),
        investment_crra_n=len(investment_crra_values),
        scatter_n=len(scatter_points),
        mpl_crra_mean=round_or_none(mean_or_none(mpl_crra_values)),
        bret_crra_mean=round_or_none(mean_or_none(bret_crra_values)),
        investment_crra_mean=round_or_none(mean_or_none(investment_crra_values)),
    )
    return report_data


def set_mpl_payoff(player: Player):
    player.mpl_row = random.randint(1, 10)
    player.mpl_drawn = random.randint(1, 10)
    choices = get_mpl_choices(player)
    set_mpl_crra(player, choices)
    player.mpl_choice = choices[player.mpl_row - 1]

    if player.mpl_drawn <= player.mpl_row:
        player.mpl_payoff = (
            C.MPL_A_H if player.mpl_choice == 'A' else C.MPL_B_H
        )
    else:
        player.mpl_payoff = (
            C.MPL_A_L if player.mpl_choice == 'A' else C.MPL_B_L
        )
    update_total_payoff(player)


def set_bret_payoff(player: Player):
    set_bret_crra(player)
    selected_cards = get_selected_bret_cards(player)
    player.cards_flipped = len(selected_cards)
    player.bomb_position = random.randint(1, C.BRET_NUM_CARDS)
    if player.cards_flipped == 0:
        player.bomb_found = False
        player.bret_payoff = C.BRET_ENDOWMENT
    elif player.bomb_position not in selected_cards:
        player.bomb_found = False
        player.bret_payoff = C.BRET_ENDOWMENT + C.BRET_CARD_VALUE * player.cards_flipped
    else:
        player.bomb_found = True
        player.bret_payoff = C.BRET_ENDOWMENT
    update_total_payoff(player)


def get_selected_bret_cards(player: Player):
    """Return the submitted BRET card positions, with a legacy-session fallback."""
    raw_cards = player.field_maybe_none('selected_bret_cards')
    try:
        selected_cards = sorted({int(card) for card in json.loads(raw_cards or '[]')})
    except (TypeError, ValueError, json.JSONDecodeError):
        selected_cards = []
    if selected_cards and all(1 <= card <= C.BRET_NUM_CARDS for card in selected_cards):
        return selected_cards
    # Sessions created before individual-card selection used the first N cards.
    return list(range(1, (player.field_maybe_none('cards_flipped') or 0) + 1))


def set_investment_payoff(player: Player):
    player.investment_draw = random.randint(1, 3)
    player.investment_high_return = player.investment_draw == 1
    amount = player.investment_amount
    player.investment_payoff = (
        C.INVESTMENT_ENDOWMENT + C.INVESTMENT_HIGH_RETURN_MULTIPLIER * amount
        if player.investment_high_return
        else C.INVESTMENT_ENDOWMENT - amount
    )
    update_total_payoff(player)


class TaskMPL(Page):
    template_name = 'RISK_PREFS/TaskMPL.html'

    @staticmethod
    def vars_for_template(player: Player):
        return common_template_vars(player)


class RiskTutorial(Page):
    """Guided practice that precedes the randomized risk tasks."""
    template_name = 'RISK_PREFS/RiskTutorial.html'

    @staticmethod
    def vars_for_template(player: Player):
        return common_template_vars(player)


class InstructionsMPL(Page):
    template_name = 'RISK_PREFS/InstructionsMPL.html'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **common_template_vars(player),
            mpl_example_text=format_text(
                player,
                'mpl_example_text',
                a_h=C.MPL_A_H,
                a_l=C.MPL_A_L,
            ),
            mpl_example_text_b=format_text(
                player,
                'mpl_example_text_b',
                b_h=C.MPL_B_H,
                b_l=C.MPL_B_L,
            ),
        )


class PageMPL(Page):
    template_name = 'RISK_PREFS/PageMPL.html'
    form_model = 'player'
    form_fields = [f'HL_{i}' for i in range(1, 11)]

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **common_template_vars(player),
            A_h=C.MPL_A_H,
            A_l=C.MPL_A_L,
            B_h=C.MPL_B_H,
            B_l=C.MPL_B_L,
        )

    @staticmethod
    def error_message(player: Player, values):
        missing = [
            i for i in range(1, 11)
            if values.get(f'HL_{i}') in (None, '')
        ]
        if missing:
            return (
                'Please choose A or B in every row.'
                if get_language(player) == 'en'
                else 'Scegli A oppure B in ogni riga.'
            )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        set_mpl_payoff(player)


class TaskBRET(Page):
    template_name = 'RISK_PREFS/TaskBRET.html'

    @staticmethod
    def vars_for_template(player: Player):
        return common_template_vars(player)


class WelcomeBRET(Page):
    template_name = 'RISK_PREFS/WelcomeBRET.html'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **common_template_vars(player),
            bret_fixed_amount=format_text(
                player,
                'bret_fixed_amount',
                amount=C.BRET_ENDOWMENT,
            ),
            bret_rule_zero=format_text(
                player,
                'bret_rule_zero',
                amount=C.BRET_ENDOWMENT,
            ),
            bret_rule_bomb=format_text(
                player,
                'bret_rule_bomb',
                amount=C.BRET_ENDOWMENT,
            ),
            bret_rule_safe=format_text(
                player,
                'bret_rule_safe',
                amount=C.BRET_ENDOWMENT,
                value=C.BRET_CARD_VALUE,
            ),
        )


class CardsBRET(Page):
    template_name = 'RISK_PREFS/CardsBRET.html'
    form_model = 'player'
    form_fields = ['cards_flipped', 'selected_bret_cards']

    @staticmethod
    def vars_for_template(player: Player):
        cards = list(range(1, C.BRET_NUM_CARDS + 1))
        return dict(
            **common_template_vars(player),
            card_rows=[
                cards[i:i + 8]
                for i in range(0, C.BRET_NUM_CARDS, 8)
            ]
        )

    @staticmethod
    def error_message(player: Player, values):
        try:
            selected_cards = json.loads(values.get('selected_bret_cards') or '[]')
            normalized_cards = sorted({int(card) for card in selected_cards})
        except (TypeError, ValueError, json.JSONDecodeError):
            normalized_cards = []
        valid_selection = (
            isinstance(selected_cards, list)
            and normalized_cards == sorted(selected_cards)
            and all(1 <= card <= C.BRET_NUM_CARDS for card in normalized_cards)
            and values.get('cards_flipped') == len(normalized_cards)
        )
        if not valid_selection:
            return (
                'Please select the cards on screen again before confirming.'
                if get_language(player) == 'en'
                else 'Seleziona nuovamente le carte sullo schermo prima di confermare.'
            )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        set_bret_payoff(player)


class TaskInvestment(Page):
    template_name = 'RISK_PREFS/TaskInvestment.html'

    @staticmethod
    def vars_for_template(player: Player):
        return common_template_vars(player)


class InstructionsInvestment(Page):
    template_name = 'RISK_PREFS/InstructionsInvestment.html'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **common_template_vars(player),
            investment_intro=format_text(
                player, 'investment_intro', endowment=C.INVESTMENT_ENDOWMENT,
            ),
            investment_low_rule=format_text(
                player, 'investment_low_rule', endowment=C.INVESTMENT_ENDOWMENT,
            ),
            investment_high_rule=format_text(
                player, 'investment_high_rule', endowment=C.INVESTMENT_ENDOWMENT,
            ),
        )


class InvestmentDecision(Page):
    template_name = 'RISK_PREFS/InvestmentDecision.html'
    form_model = 'player'
    form_fields = ['investment_amount']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **common_template_vars(player),
            investment_endowment=C.INVESTMENT_ENDOWMENT,
            investment_high_return_multiplier=C.INVESTMENT_HIGH_RETURN_MULTIPLIER,
            investment_choice_hint=format_text(
                player, 'investment_choice_hint', endowment=C.INVESTMENT_ENDOWMENT,
            ),
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        set_investment_payoff(player)


class TaskMPLFirst(TaskMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.MPL_TASK


class InstructionsMPLFirst(InstructionsMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.MPL_TASK


class PageMPLFirst(PageMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.MPL_TASK


class TaskBRETFirst(TaskBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.BRET_TASK


class WelcomeBRETFirst(WelcomeBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.BRET_TASK


class CardsBRETFirst(CardsBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.BRET_TASK


class TaskInvestmentFirst(TaskInvestment):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.INVESTMENT_TASK


class InstructionsInvestmentFirst(InstructionsInvestment):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.INVESTMENT_TASK


class InvestmentDecisionFirst(InvestmentDecision):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 1) == C.INVESTMENT_TASK


class TaskMPLSecond(TaskMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.MPL_TASK


class InstructionsMPLSecond(InstructionsMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.MPL_TASK


class PageMPLSecond(PageMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.MPL_TASK


class TaskBRETSecond(TaskBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.BRET_TASK


class WelcomeBRETSecond(WelcomeBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.BRET_TASK


class CardsBRETSecond(CardsBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.BRET_TASK


class TaskInvestmentSecond(TaskInvestment):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.INVESTMENT_TASK


class InstructionsInvestmentSecond(InstructionsInvestment):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.INVESTMENT_TASK


class InvestmentDecisionSecond(InvestmentDecision):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 2) == C.INVESTMENT_TASK


class TaskMPLThird(TaskMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.MPL_TASK


class InstructionsMPLThird(InstructionsMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.MPL_TASK


class PageMPLThird(PageMPL):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.MPL_TASK


class TaskBRETThird(TaskBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.BRET_TASK


class WelcomeBRETThird(WelcomeBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.BRET_TASK


class CardsBRETThird(CardsBRET):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.BRET_TASK


class TaskInvestmentThird(TaskInvestment):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.INVESTMENT_TASK


class InstructionsInvestmentThird(InstructionsInvestment):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.INVESTMENT_TASK


class InvestmentDecisionThird(InvestmentDecision):
    @staticmethod
    def is_displayed(player: Player):
        return task_at(player, 3) == C.INVESTMENT_TASK


class Summary(Page):
    template_name = 'RISK_PREFS/Summary.html'

    @staticmethod
    def vars_for_template(player: Player):
        set_bret_crra(player)
        update_total_payoff(player)
        mpl_high_payoff = C.MPL_A_H if player.mpl_choice == 'A' else C.MPL_B_H
        mpl_low_payoff = C.MPL_A_L if player.mpl_choice == 'A' else C.MPL_B_L
        profile_key, profile_task_count = overall_choice_profile(
            mpl_risk_type(player),
            bret_risk_type(player),
            investment_risk_type(player),
        )
        return dict(
            **common_template_vars(player),
            overall_profile=get_text(player)[profile_key] if profile_key else None,
            overall_profile_partial=(
                format_text(player, 'overall_profile_partial', count=profile_task_count)
                if profile_key and profile_task_count < 3 else None
            ),
            readable_order=', then '.join(task_at(player, i) for i in range(1, 4)),
            mpl_row=player.mpl_row,
            mpl_choice=player.mpl_choice,
            mpl_drawn=player.mpl_drawn,
            mpl_ball_numbers=range(1, 11),
            mpl_reveal_setup=format_text(
                player, 'mpl_reveal_setup', row=player.mpl_row, choice=player.mpl_choice,
            ),
            mpl_reveal_urn=format_text(
                player, 'mpl_reveal_urn', high=player.mpl_row, low=10 - player.mpl_row,
            ),
            mpl_reveal_high=format_text(player, 'mpl_reveal_high', payoff=mpl_high_payoff),
            mpl_reveal_low=format_text(player, 'mpl_reveal_low', payoff=mpl_low_payoff),
            mpl_reveal_drawn=format_text(player, 'mpl_reveal_drawn', draw=player.mpl_drawn),
            bret_cards=range(1, C.BRET_NUM_CARDS + 1),
            cards_flipped=player.cards_flipped,
            selected_bret_cards_json=json.dumps(get_selected_bret_cards(player)),
            bomb_position=player.bomb_position,
            bomb_found=player.bomb_found,
            bret_decided_cards=format_text(player, 'bret_decided_cards', cards=player.cards_flipped),
            bret_result_text=(
                format_text(player, 'bret_found_bomb') + ' '
                + format_text(player, 'bret_bomb_payoff', payoff=player.bret_payoff)
                if player.bomb_found else
                format_text(player, 'bret_no_bomb') + ' '
                + format_text(player, 'bret_safe_payoff', payoff=player.bret_payoff)
            ),
            investment_draw=player.investment_draw,
            investment_high_return=player.investment_high_return,
            investment_chosen=format_text(
                player, 'investment_chosen',
                amount=player.investment_amount, endowment=C.INVESTMENT_ENDOWMENT,
            ),
            investment_result_text=format_text(
                player,
                'investment_result_high' if player.investment_high_return else 'investment_result_low',
            ),
            mpl_payoff=player.mpl_payoff,
            bret_payoff=player.bret_payoff,
            investment_payoff=player.investment_payoff,
            total_payoff=player.total_payoff,
            mpl_risk_type=get_text(player)[mpl_risk_type(player)],
            bret_risk_type=get_text(player)[bret_risk_type(player)],
            investment_risk_type=get_text(player)[investment_risk_type(player)],
            mpl_behavior_feedback=mpl_behavior_feedback(player),
            bret_behavior_feedback=bret_behavior_feedback(player),
            investment_behavior_feedback=investment_behavior_feedback(player),
            mpl_payoff_text=format_text(player, 'mpl_payoff_text', payoff=player.mpl_payoff),
            bret_payoff_text=format_text(player, 'bret_payoff_text', payoff=player.bret_payoff),
            investment_payoff_text=format_text(player, 'investment_payoff_text', payoff=player.investment_payoff),
            total_payoff_text=format_text(player, 'total_payoff_text', payoff=player.total_payoff),
            ai_individual_feedback_html=(
                _risk_prefs_individual_ai_feedback(player)
                if _ai_feedback_enabled(player.session)
                else ""
            ),
        )


class GeneralRiskQuestion(Page):
    template_name = 'RISK_PREFS/GeneralRiskQuestion.html'
    form_model = 'player'
    form_fields = ['general_risk_willingness']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(**common_template_vars(player), scale_values=range(11))


class FinalWaitPage(WaitPage):
    wait_for_all_groups = True
    title_text = 'Waiting for the other participants'
    body_text = 'Please wait until everyone has completed the risk tasks.'


page_sequence = [
    RiskTutorial,
    TaskMPLFirst,
    InstructionsMPLFirst,
    PageMPLFirst,
    TaskBRETFirst,
    WelcomeBRETFirst,
    CardsBRETFirst,
    TaskInvestmentFirst,
    InstructionsInvestmentFirst,
    InvestmentDecisionFirst,
    TaskMPLSecond,
    InstructionsMPLSecond,
    PageMPLSecond,
    TaskBRETSecond,
    WelcomeBRETSecond,
    CardsBRETSecond,
    TaskInvestmentSecond,
    InstructionsInvestmentSecond,
    InvestmentDecisionSecond,
    TaskMPLThird,
    InstructionsMPLThird,
    PageMPLThird,
    TaskBRETThird,
    WelcomeBRETThird,
    CardsBRETThird,
    TaskInvestmentThird,
    InstructionsInvestmentThird,
    InvestmentDecisionThird,
    GeneralRiskQuestion,
    Summary,
    FinalWaitPage,
]
