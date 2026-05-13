import io
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from requests.exceptions import RequestException, SSLError
from urllib3.exceptions import InsecureRequestWarning

from src.constants import DISPLAY_NAME_TO_COLUMN


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


DATASET_COLUMNS = [
    "year",
    "unemployment_rate",
    "average_salary",
    "inflation",
    "real_income_index",
    "gdp_growth",
    "key_rate",
]

DEFAULT_DATA_PATH = Path("data/unemployment_data.csv")
PUBLIC_DATA_PATH = Path("data/unemployment_official_2015_2024.csv")

SOURCE_URLS = {
    "salary": "https://rosstat.gov.ru/storage/mediabank/tab1-zpl_02-2026.xlsx",
    "inflation": "https://www.rosstat.gov.ru/storage/mediabank/ipc_mes_03-2026.xlsx",
    "unemployment": "https://rosstat.gov.ru/storage/mediabank/Trud_3_15-s.xlsx",
    "real_income": "https://rosstat.gov.ru/storage/mediabank/urov_12kv_1kv-2026.xlsx",
    "gdp": "https://rosstat.gov.ru/storage/mediabank/VVP_god_s1995-2025.xlsx",
    "key_rate": (
        "https://www.cbr.ru/hd_base/KeyRate/"
        "?UniDbQuery.From={date_from}"
        "&UniDbQuery.To={date_to}"
        "&UniDbQuery.Posted=True"
    ),
}

LEGACY_UNEMPLOYMENT_VALUES = {
    2015: 5.6,
    2016: 5.5,
}

LEGACY_UNEMPLOYMENT_SOURCE = (
    "https://26.rosstat.gov.ru/storage/mediabank/"
    "%D0%9A%D0%B0%D0%B1%D0%B0%D1%80%D0%B4%D0%B8%D0%BD%D0%BE-"
    "%D0%91%D0%B0%D0%BB%D0%BA%D0%B0%D1%80%D0%B8%D1%8F%2B%D0%B2%2B"
    "%D1%86%D0%B8%D1%84%D1%80%D0%B0%D1%85%2B2018%281%29.pdf"
)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )
}


def _parse_year(value):
    if pd.isna(value):
        return None

    match = re.search(r"(19|20)\d{2}", str(value))
    return int(match.group(0)) if match else None


def _parse_float(value):
    if pd.isna(value):
        return None

    text = str(value).replace(",", ".").replace("\xa0", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def _get_session():
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    return session


def _fetch_bytes(session, url, timeout=60):
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content, True
    except SSLError:
        response = session.get(url, timeout=timeout, verify=False)
        response.raise_for_status()
        return response.content, False
    except RequestException as exc:
        raise RuntimeError(f"Не удалось загрузить источник: {url}") from exc


def _read_excel_from_url(session, url, sheet_name=0):
    content, verified = _fetch_bytes(session, url)
    dataframe = pd.read_excel(io.BytesIO(content), sheet_name=sheet_name, header=None)
    return dataframe, verified


def _read_html_tables_from_url(session, url):
    content, verified = _fetch_bytes(session, url)
    html_text = content.decode("utf-8", errors="ignore")
    tables = pd.read_html(io.StringIO(html_text))
    return tables, verified


def _build_salary_series(session):
    raw_df, verified = _read_excel_from_url(session, SOURCE_URLS["salary"], "Лист1")

    rows = []

    for _, row in raw_df.iloc[7:].iterrows():
        year = _parse_year(row[0])
        value = _parse_float(row[1])

        if year and value is not None:
            rows.append((year, value))

    salary_df = pd.DataFrame(rows, columns=["year", "average_salary"]).drop_duplicates("year")

    return salary_df, verified


def _build_inflation_series(session):
    raw_df, verified = _read_excel_from_url(session, SOURCE_URLS["inflation"], "01")

    years = [_parse_year(value) for value in raw_df.iloc[3, 1:36]]
    cpi_values = [_parse_float(value) for value in raw_df.iloc[18, 1:36]]

    inflation_df = pd.DataFrame(
        {
            "year": years,
            "inflation": [
                value - 100 if value is not None else None
                for value in cpi_values
            ],
        }
    ).dropna()

    inflation_df["year"] = inflation_df["year"].astype(int)

    return inflation_df, verified


def _build_unemployment_series(session, include_legacy=True):
    raw_df, verified = _read_excel_from_url(session, SOURCE_URLS["unemployment"], "2")

    years = [_parse_year(value) for value in raw_df.iloc[4, 1:10]]
    values = [_parse_float(value) for value in raw_df.iloc[5, 1:10]]

    unemployment_df = pd.DataFrame(
        {
            "year": years,
            "unemployment_rate": values,
        }
    ).dropna()

    unemployment_df["year"] = unemployment_df["year"].astype(int)

    if include_legacy:
        legacy_df = pd.DataFrame(
            {
                "year": list(LEGACY_UNEMPLOYMENT_VALUES.keys()),
                "unemployment_rate": list(LEGACY_UNEMPLOYMENT_VALUES.values()),
            }
        )
        unemployment_df = pd.concat([legacy_df, unemployment_df], ignore_index=True)

    unemployment_df = unemployment_df.drop_duplicates("year").sort_values("year").reset_index(drop=True)

    return unemployment_df, verified


def _build_real_income_series(session):
    raw_df, verified = _read_excel_from_url(session, SOURCE_URLS["real_income"], "РРДД_РДД")

    rows = []
    current_year = None

    for _, row in raw_df.iterrows():
        first_cell = str(row[0]) if not pd.isna(row[0]) else ""

        if "год" in first_cell.lower() and _parse_year(first_cell):
            current_year = _parse_year(first_cell)
            continue

        if first_cell.strip().lower() == "год" and current_year:
            rows.append((current_year, _parse_float(row[3])))

    real_income_df = pd.DataFrame(rows, columns=["year", "real_income_index"])
    real_income_df["year"] = real_income_df["year"].astype(int)

    return real_income_df, verified


def _build_gdp_series(session):
    raw_df, verified = _read_excel_from_url(session, SOURCE_URLS["gdp"], "8")

    years = [_parse_year(value) for value in raw_df.iloc[2, :14]]
    indices = [_parse_float(value) for value in raw_df.iloc[3, :14]]

    gdp_df = pd.DataFrame(
        {
            "year": years,
            "gdp_growth": [
                value - 100 if value is not None else None
                for value in indices
            ],
        }
    ).dropna()

    gdp_df["year"] = gdp_df["year"].astype(int)

    return gdp_df, verified


def load_cbr_key_rate(start_year=2015, end_year=2024):
    session = _get_session()

    date_from = f"01.01.{start_year}"
    date_to = f"31.12.{end_year}"
    url = SOURCE_URLS["key_rate"].format(date_from=date_from, date_to=date_to)

    tables, verified = _read_html_tables_from_url(session, url)

    if not tables:
        raise RuntimeError("Банк России не вернул таблицу с ключевой ставкой.")

    df = tables[0].copy()
    df.columns = ["Дата", "Ключевая ставка"]

    df["Дата"] = pd.to_datetime(df["Дата"], format="%d.%m.%Y", errors="coerce")
    df["Ключевая ставка"] = (
        df["Ключевая ставка"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    if df["Ключевая ставка"].max() > 100:
        df["Ключевая ставка"] = df["Ключевая ставка"] / 100

    df = df.dropna(subset=["Дата", "Ключевая ставка"])
    df["Год"] = df["Дата"].dt.year

    annual_df = (
        df.groupby("Год", as_index=False)
        .agg(
            **{
                "Среднегодовая ключевая ставка, %": ("Ключевая ставка", "mean"),
                "Минимальная ставка за год, %": ("Ключевая ставка", "min"),
                "Максимальная ставка за год, %": ("Ключевая ставка", "max"),
                "Количество наблюдений": ("Ключевая ставка", "count"),
            }
        )
        .round(2)
    )

    annual_df.attrs["ssl_verified"] = verified
    annual_df.attrs["source_url"] = url

    return annual_df


def _prepare_dataset(dataframe):
    dataframe = dataframe.copy()

    for column in DATASET_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    dataframe = dataframe.dropna(subset=DATASET_COLUMNS)
    dataframe = dataframe.sort_values("year").reset_index(drop=True)
    dataframe["year"] = dataframe["year"].astype(int)
    dataframe["average_salary"] = dataframe["average_salary"].round(0).astype(int)

    for column in DATASET_COLUMNS:
        if column not in {"year", "average_salary"}:
            dataframe[column] = dataframe[column].round(2)

    return dataframe


def _normalize_uploaded_columns(dataframe):
    rename_map = {
        column: DISPLAY_NAME_TO_COLUMN.get(column, column)
        for column in dataframe.columns
    }
    normalized_df = dataframe.rename(columns=rename_map)

    missing_columns = [column for column in DATASET_COLUMNS if column not in normalized_df.columns]
    if missing_columns:
        raise ValueError(
            "В CSV отсутствуют обязательные столбцы: "
            + ", ".join(missing_columns)
        )

    return normalized_df[DATASET_COLUMNS]


def build_source_catalog(verification_flags=None):
    verification_flags = verification_flags or {}

    catalog = [
        {
            "Показатель": "Уровень безработицы, %",
            "Источник": "Росстат",
            "Формат": "XLSX + legacy PDF для 2015-2016",
            "Определение": "Среднегодовой уровень безработицы; для 2017-2024 — 15 лет и старше",
            "URL": SOURCE_URLS["unemployment"],
            "Статус SSL": "Проверен" if verification_flags.get("unemployment", True) else "Повтор без проверки SSL",
        },
        {
            "Показатель": "Средняя заработная плата, руб.",
            "Источник": "Росстат",
            "Формат": "XLSX",
            "Определение": "Среднемесячная номинальная начисленная заработная плата работников",
            "URL": SOURCE_URLS["salary"],
            "Статус SSL": "Проверен" if verification_flags.get("salary", True) else "Повтор без проверки SSL",
        },
        {
            "Показатель": "Инфляция, %",
            "Источник": "Росстат",
            "Формат": "XLSX",
            "Определение": "ИПЦ в декабре к декабрю предыдущего года минус 100",
            "URL": SOURCE_URLS["inflation"],
            "Статус SSL": "Проверен" if verification_flags.get("inflation", True) else "Повтор без проверки SSL",
        },
        {
            "Показатель": "Платежеспособность населения (реальные располагаемые доходы), %",
            "Источник": "Росстат",
            "Формат": "XLSX",
            "Определение": "Реальные располагаемые денежные доходы населения, % к предыдущему году",
            "URL": SOURCE_URLS["real_income"],
            "Статус SSL": "Проверен" if verification_flags.get("real_income", True) else "Повтор без проверки SSL",
        },
        {
            "Показатель": "Темп роста ВВП, %",
            "Источник": "Росстат",
            "Формат": "XLSX",
            "Определение": "Индекс физического объема ВВП к предыдущему году минус 100",
            "URL": SOURCE_URLS["gdp"],
            "Статус SSL": "Проверен" if verification_flags.get("gdp", True) else "Повтор без проверки SSL",
        },
        {
            "Показатель": "Ключевая ставка, %",
            "Источник": "Банк России",
            "Формат": "HTML таблица",
            "Определение": "Среднегодовая ключевая ставка по ежедневным наблюдениям",
            "URL": "https://www.cbr.ru/hd_base/KeyRate/",
            "Статус SSL": "Проверен" if verification_flags.get("key_rate", True) else "Повтор без проверки SSL",
        },
        {
            "Показатель": "Безработица 2015-2016, %",
            "Источник": "Росстат, региональный статистический сборник",
            "Формат": "PDF",
            "Определение": "Добавлено в архивный хвост ряда для расширения ретроспективы",
            "URL": LEGACY_UNEMPLOYMENT_SOURCE,
            "Статус SSL": "Архивный источник",
        },
    ]

    return pd.DataFrame(catalog)


def build_revision_log(previous_df, new_df):
    if previous_df is None:
        return pd.DataFrame(columns=["Год", "Показатель", "Было", "Стало", "Изменение"])

    comparable_columns = [
        column for column in DATASET_COLUMNS
        if column in previous_df.columns and column in new_df.columns and column != "year"
    ]

    if not comparable_columns:
        return pd.DataFrame(columns=["Год", "Показатель", "Было", "Стало", "Изменение"])

    merged = previous_df.merge(new_df, on="year", suffixes=("_old", "_new"))
    rows = []

    for column in comparable_columns:
        old_col = f"{column}_old"
        new_col = f"{column}_new"

        for _, row in merged.iterrows():
            old_value = pd.to_numeric(row[old_col], errors="coerce")
            new_value = pd.to_numeric(row[new_col], errors="coerce")

            if pd.isna(old_value) or pd.isna(new_value):
                continue

            if round(float(old_value), 4) == round(float(new_value), 4):
                continue

            rows.append(
                {
                    "Год": int(row["year"]),
                    "Показатель": column,
                    "Было": round(float(old_value), 4),
                    "Стало": round(float(new_value), 4),
                    "Изменение": round(float(new_value - old_value), 4),
                }
            )

    return pd.DataFrame(rows)


def build_official_dataset(start_year=2015, end_year=2024, include_legacy_unemployment=True):
    session = _get_session()

    salary_df, salary_verified = _build_salary_series(session)
    inflation_df, inflation_verified = _build_inflation_series(session)
    unemployment_df, unemployment_verified = _build_unemployment_series(
        session,
        include_legacy=include_legacy_unemployment,
    )
    income_df, income_verified = _build_real_income_series(session)
    gdp_df, gdp_verified = _build_gdp_series(session)
    key_rate_df = load_cbr_key_rate(start_year=start_year, end_year=end_year)

    dataset = unemployment_df.merge(salary_df, on="year", how="left")
    dataset = dataset.merge(inflation_df, on="year", how="left")
    dataset = dataset.merge(income_df, on="year", how="left")
    dataset = dataset.merge(gdp_df, on="year", how="left")
    dataset = dataset.merge(
        key_rate_df[["Год", "Среднегодовая ключевая ставка, %"]].rename(
            columns={
                "Год": "year",
                "Среднегодовая ключевая ставка, %": "key_rate",
            }
        ),
        on="year",
        how="left",
    )

    dataset = dataset[(dataset["year"] >= start_year) & (dataset["year"] <= end_year)]
    dataset = _prepare_dataset(dataset)

    verification_flags = {
        "salary": salary_verified,
        "inflation": inflation_verified,
        "unemployment": unemployment_verified,
        "real_income": income_verified,
        "gdp": gdp_verified,
        "key_rate": key_rate_df.attrs.get("ssl_verified", True),
    }

    metadata = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "used_fallback": False,
        "online_source_count": 6,
        "legacy_unemployment_years": [2015, 2016] if include_legacy_unemployment else [],
        "source_mode": "online",
        "source_mode_label": "Онлайн-источники Росстата и Банка России",
        "notes": [
            "Значения по безработице за 2015-2016 годы оставлены как архивное продолжение ряда.",
            "Начиная с 2017 года используется актуальная федеральная таблица Росстата.",
            "Инфляция трактуется как ИПЦ в декабре к декабрю предыдущего года минус 100.",
        ],
    }

    return dataset, build_source_catalog(verification_flags), metadata


def load_local_dataset(csv_path=DEFAULT_DATA_PATH):
    csv_path = Path(csv_path)
    dataframe = pd.read_csv(csv_path)
    dataframe = _prepare_dataset(dataframe)

    file_updated_at = None
    if csv_path.exists():
        file_updated_at = datetime.fromtimestamp(
            csv_path.stat().st_mtime,
            tz=timezone.utc,
        ).isoformat()

    metadata = {
        "built_at_utc": None,
        "used_fallback": False,
        "online_source_count": 0,
        "legacy_unemployment_years": [2015, 2016],
        "source_mode": "local",
        "source_mode_label": "Локальный официальный CSV проекта",
        "local_file_path": str(csv_path),
        "public_file_path": str(PUBLIC_DATA_PATH),
        "local_file_updated_at_utc": file_updated_at,
        "notes": [
            "Используется локальный CSV проекта, сформированный по тем же официальным источникам.",
        ],
    }

    return dataframe, build_source_catalog(), metadata


def load_uploaded_dataset(uploaded_file):
    dataframe = pd.read_csv(uploaded_file, sep=None, engine="python")
    dataframe = _normalize_uploaded_columns(dataframe)
    dataframe = _prepare_dataset(dataframe)

    metadata = {
        "built_at_utc": None,
        "used_fallback": False,
        "online_source_count": 0,
        "legacy_unemployment_years": [2015, 2016],
        "source_mode": "upload",
        "source_mode_label": "CSV, загруженный пользователем",
        "uploaded_file_name": getattr(uploaded_file, "name", "uploaded.csv"),
        "local_file_updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "notes": [
            "Используется CSV, который пользователь загрузил вручную в интерфейс приложения.",
        ],
    }

    return dataframe, build_source_catalog(), metadata


def save_dataset(dataframe, csv_path=DEFAULT_DATA_PATH):
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(csv_path, index=False)


def refresh_local_dataset(csv_path=DEFAULT_DATA_PATH, start_year=2015, end_year=2024):
    previous_df = None
    csv_path = Path(csv_path)

    try:
        previous_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        previous_df = None

    dataset, source_catalog, metadata = build_official_dataset(
        start_year=start_year,
        end_year=end_year,
        include_legacy_unemployment=True,
    )

    revision_log = build_revision_log(previous_df, dataset)
    save_dataset(dataset, csv_path)
    save_dataset(dataset, PUBLIC_DATA_PATH)

    metadata["revision_log"] = revision_log
    metadata["saved_to"] = str(csv_path)
    metadata["public_file_path"] = str(PUBLIC_DATA_PATH)
    metadata["local_file_updated_at_utc"] = metadata["built_at_utc"]

    return dataset, source_catalog, metadata


def load_official_dataset(csv_path=DEFAULT_DATA_PATH, start_year=2015, end_year=2024):
    return refresh_local_dataset(
        csv_path=csv_path,
        start_year=start_year,
        end_year=end_year,
    )


def load_dataset_with_fallback(csv_path=DEFAULT_DATA_PATH, start_year=2015, end_year=2024):
    try:
        return refresh_local_dataset(
            csv_path=csv_path,
            start_year=start_year,
            end_year=end_year,
        )
    except Exception as exc:
        dataset, source_catalog, metadata = load_local_dataset(csv_path)
        metadata["used_fallback"] = True
        metadata["fallback_reason"] = str(exc)
        metadata["revision_log"] = pd.DataFrame(
            columns=["Год", "Показатель", "Было", "Стало", "Изменение"]
        )
        return dataset, source_catalog, metadata
