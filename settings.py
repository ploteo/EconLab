from os import environ

SESSION_CONFIGS = [

    dict(
        name='beauty_contest_ita',
         display_name = 'Beauty Contest (ITA)',
        app_sequence=['BEAUTY_CONTEST'],
        num_demo_participants=6,
        openai_api_key=environ.get('OPENAI_API_KEY'),
        openai_beauty_model='gpt-5.4-mini',
        language='it', #'it' for italian, 'en' for english
    ),
    dict(
        name='public_goods_ita',
        display_name='Public Goods Game (ITA)',
        app_sequence=['PGG'],
        num_demo_participants=3,
        openai_api_key=environ.get('OPENAI_API_KEY'),
        openai_pgg_model='gpt-5.4-mini', #gpt-5.5, 'gpt-5.4'
        language='it', #'it' for italian, 'en' for english
    ),
    dict(
        name='public_goods_eng',
        display_name='Public Goods Game (ENG)',
        app_sequence=['PGG'],
        num_demo_participants=3,
        openai_api_key=environ.get('OPENAI_API_KEY'),
        openai_pgg_model='gpt-5.4-mini', #gpt-5.5, 'gpt-5.4'
        language='en',
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
SECRET_KEY = environ.get(
    'OTREE_SECRET_KEY',
    'otree-dev-secret-key-change-me-for-production',
)

DEMO_PAGE_INTRO_HTML = """ """
