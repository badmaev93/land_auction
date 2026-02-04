from os import environ

# ============================================================================
# КОНФИГУРАЦИИ СЕССИЙ - ДАШБОРД ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================
# Здесь можно выбрать тип аукциона и настроить параметры
# Администратор выбирает нужную конфигурацию при создании сессии

SESSION_CONFIGS = [
    # -------------------------------------------------------------------------
    # АУКЦИОН ЕДИНОЙ ЦЕНЫ (Uniform Price) - РЕКОМЕНДУЕТСЯ
    # Все победители платят одинаковую цену отсечения
    # -------------------------------------------------------------------------
    dict(
        name='uniform_price_auction',
        display_name='Аукцион единой цены (Uniform Price) - Рекомендуется',
        app_sequence=['auction_app'],
        num_demo_participants=6,
        auction_type='uniform',
        items_available=10,
        min_valuation=5000,
        max_valuation=15000,
    ),

    # -------------------------------------------------------------------------
    # АУКЦИОН ПЕРВОЙ ЦЕНЫ (GFP - Generalized First Price)
    # Каждый победитель платит свою собственную ставку
    # -------------------------------------------------------------------------
    dict(
        name='first_price_auction',
        display_name='Аукцион первой цены (GFP)',
        app_sequence=['auction_app'],
        num_demo_participants=6,
        auction_type='first_price',
        items_available=10,
        min_valuation=5000,
        max_valuation=15000,
    ),

    # -------------------------------------------------------------------------
    # МЕХАНИЗМ ВИКРИ-КЛАРКА-ГРОВСА (VCG)
    # Победители платят внешние эффекты на других участников
    # -------------------------------------------------------------------------
    dict(
        name='vcg_auction',
        display_name='Механизм VCG (Викри-Кларка-Гровса)',
        app_sequence=['auction_app'],
        num_demo_participants=6,
        auction_type='vcg',
        items_available=10,
        min_valuation=5000,
        max_valuation=15000,
    ),

    # -------------------------------------------------------------------------
    # СРАВНЕНИЕ АУКЦИОНОВ - Малое количество путёвок (высокая конкуренция)
    # -------------------------------------------------------------------------
    dict(
        name='uniform_high_competition',
        display_name='Единая цена - Высокая конкуренция (5 путёвок)',
        app_sequence=['auction_app'],
        num_demo_participants=9,
        auction_type='uniform',
        items_available=5,
        min_valuation=5000,
        max_valuation=15000,
    ),

    dict(
        name='first_price_high_competition',
        display_name='Первая цена - Высокая конкуренция (5 путёвок)',
        app_sequence=['auction_app'],
        num_demo_participants=9,
        auction_type='first_price',
        items_available=5,
        min_valuation=5000,
        max_valuation=15000,
    ),

    # -------------------------------------------------------------------------
    # ТЕСТ С БОЛЬШИМ КОЛИЧЕСТВОМ УЧАСТНИКОВ
    # -------------------------------------------------------------------------
    dict(
        name='uniform_large_group',
        display_name='Единая цена - Большая группа (12 участников)',
        app_sequence=['auction_app'],
        num_demo_participants=12,
        auction_type='uniform',
        items_available=20,
        min_valuation=5000,
        max_valuation=15000,
    ),
]

# ============================================================================
# НАСТРОЙКИ ПО УМОЛЧАНИЮ
# ============================================================================
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc="Эксперимент по распределению путёвок в заповедник через аукцион"
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# Язык интерфейса
LANGUAGE_CODE = 'ru'

# Валюта
REAL_WORLD_CURRENCY_CODE = 'RUB'
USE_POINTS = True

# Администратор
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin123')

# Описание демо-страницы
DEMO_PAGE_INTRO_HTML = """
<h2>Аукцион путёвок в заповедник "Земля леопарда"</h2>
<p>
    Этот эксперимент исследует различные механизмы распределения
    дефицитного ресурса (путёвок в заповедник) через аукционы.
</p>
<h4>Доступные типы аукционов:</h4>
<ul>
    <li><strong>Uniform Price (Единой цены)</strong> - все платят цену отсечения</li>
    <li><strong>First Price (Первой цены)</strong> - каждый платит свою ставку</li>
    <li><strong>VCG (Викри-Кларка-Гровса)</strong> - платят внешние эффекты</li>
</ul>
<p>
    Выберите конфигурацию ниже для запуска эксперимента.
</p>
"""

SECRET_KEY = '1108820876562'

# Отладка
DEBUG = environ.get('OTREE_DEBUG', 'True').lower() == 'true'
