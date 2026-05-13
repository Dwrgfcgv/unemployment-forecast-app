ANALYSIS_START_YEAR = 2015
ANALYSIS_END_YEAR = 2024
ANALYSIS_PERIOD_LABEL = f"{ANALYSIS_START_YEAR}-{ANALYSIS_END_YEAR}"

COLUMN_NAMES = {
    "year": "Год",
    "unemployment_rate": "Уровень безработицы, %",
    "average_salary": "Средняя заработная плата, руб.",
    "inflation": "Инфляция, %",
    "real_income_index": "Платежеспособность населения (реальные доходы), %",
    "gdp_growth": "Темп роста ВВП, %",
    "key_rate": "Ключевая ставка, %",
}

DISPLAY_NAME_TO_COLUMN = {value: key for key, value in COLUMN_NAMES.items()}

SHORT_COLUMN_NAMES = {
    "unemployment_rate": "Безработица",
    "average_salary": "Зарплата",
    "inflation": "Инфляция",
    "real_income_index": "Платежеспособность",
    "gdp_growth": "Рост ВВП",
    "key_rate": "Ключевая ставка",
}

DISPLAY_ORDER = [
    "year",
    "unemployment_rate",
    "average_salary",
    "inflation",
    "real_income_index",
    "gdp_growth",
    "key_rate",
]

SOURCE_OPTIONS = {
    "Онлайн-источники Росстата и Банка России": "online",
    "Загрузить CSV файл": "upload",
}

PLOT_COLORS = {
    "navy": "#5b8cff",
    "blue": "#3f83f8",
    "teal": "#0ea5a3",
    "gold": "#f59e0b",
    "ink": "#dce8ff",
    "muted": "#9fb2cf",
    "surface": "#111b2d",
    "surface_soft": "#182338",
    "danger": "#ef4444",
    "success": "#22c55e",
}

PLOTLY_CONFIG = {
    "displaylogo": False,
    "displayModeBar": "hover",
    "responsive": True,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
        "autoScale2d",
        "toggleSpikelines",
    ],
}

CSV_TEMPLATE_COLUMNS = DISPLAY_ORDER.copy()
