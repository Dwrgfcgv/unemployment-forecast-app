import pandas as pd
import streamlit as st

from src.analysis_tools import (
    TARGET_COLUMN,
    backtest_forecast_methods,
    build_cluster_analysis,
    build_correlation_outputs,
    build_forecast,
    build_model_comparison,
    build_pca_analysis,
)
from src.constants import (
    ANALYSIS_END_YEAR,
    ANALYSIS_START_YEAR,
    DISPLAY_ORDER,
    SOURCE_OPTIONS,
)
from src.data_pipeline import load_official_dataset, load_uploaded_dataset
from src.report_tables import dataset_quality_table
from src.ui.components import (
    build_csv_template,
    rename_for_display,
    render_hero,
    render_metric_card,
    render_section_divider,
    render_status_box,
)
from src.ui.sections import (
    render_data_tab,
    render_forecast_tab,
    render_overview_tab,
    render_pca_tab,
    render_regression_tab,
)
from src.ui.styles import inject_global_styles


st.set_page_config(
    page_title="Прогнозирование безработицы",
    page_icon="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><path fill=%22%233f83f8%22 d=%22M4 24h4V12H4zm10 0h4V8h-4zm10 0h4V4h-4zM4 28h24v-2H4z%22/></svg>",
    layout="wide",
)

inject_global_styles()


@st.cache_data(show_spinner=False)
def get_online_dataset(refresh_token):
    return load_official_dataset(
        start_year=ANALYSIS_START_YEAR,
        end_year=ANALYSIS_END_YEAR,
    )


if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = 0

if "source_selector" not in st.session_state:
    st.session_state.source_selector = "Онлайн-источники Росстата и Банка России"


st.sidebar.title("Параметры исследования")

selected_source_label = st.sidebar.radio(
    "Источник данных",
    list(SOURCE_OPTIONS.keys()),
    key="source_selector",
)
source_mode = SOURCE_OPTIONS[selected_source_label]

uploaded_file = None
if source_mode == "online":
    if st.sidebar.button("Обновить онлайн-данные", width="stretch"):
        get_online_dataset.clear()
        st.session_state.refresh_token += 1
else:
    st.sidebar.download_button(
        "Скачать шаблон CSV",
        data=build_csv_template(),
        file_name="unemployment_template.csv",
        mime="text/csv",
        width="stretch",
    )
    uploaded_file = st.sidebar.file_uploader(
        "Загрузите CSV для анализа",
        type=["csv"],
        help="Ожидаются столбцы year, unemployment_rate, average_salary, inflation, real_income_index, gdp_growth, key_rate.",
    )

forecast_method = st.sidebar.selectbox(
    "Метод прогноза",
    ["Экспоненциальное сглаживание", "ARIMA (1,1,1)"],
)

forecast_horizon = st.sidebar.slider(
    "Горизонт прогноза, лет",
    min_value=1,
    max_value=5,
    value=3,
)

st.sidebar.markdown("---")
st.sidebar.write("**Структура анализа**")
st.sidebar.write("1. Паспорт исследования и динамика")
st.sidebar.write("2. Проверка данных и источников")
st.sidebar.write("3. Корреляции, регрессия и устойчивость модели")
st.sidebar.write("4. PCA, кластеры и прогноз")


full_df = None
source_catalog = None
metadata = {}
load_error = None
loading_placeholder = st.empty()

if source_mode == "online":
    loading_status = loading_placeholder.status(
        "Подгружаю официальные онлайн-данные для исследования",
        expanded=True,
    )
    loading_status.write("Подключаюсь к источникам Росстата и Банка России.")
    try:
        full_df, source_catalog, metadata = get_online_dataset(st.session_state.refresh_token)
        loading_status.write("Официальный набор данных успешно получен.")
        loading_status.update(
            label="Онлайн-данные успешно загружены",
            state="complete",
            expanded=False,
        )
    except Exception as exc:
        load_error = str(exc)
        loading_status.update(
            label="Онлайн-обновление не выполнено",
            state="error",
            expanded=True,
        )
else:
    loading_placeholder.empty()
    if uploaded_file is not None:
        try:
            full_df, source_catalog, metadata = load_uploaded_dataset(uploaded_file)
        except Exception as exc:
            load_error = str(exc)


if full_df is None:
    render_hero(
        {
            "source_mode_label": (
                "Ожидается загрузка CSV"
                if source_mode == "upload"
                else "Онлайн-источники Росстата и Банка России"
            ),
            "uploaded_file_name": getattr(uploaded_file, "name", "файл не выбран"),
            "built_at_utc": None,
            "analysis_period_label": "после загрузки данных",
        }
    )

    if source_mode == "upload" and not load_error:
        render_status_box(
            "Загрузите CSV-файл через левую панель, и приложение сразу построит полный аналитический контур для ВКР.",
            "warn",
        )
    elif source_mode == "upload":
        render_status_box(
            (
                "CSV-файл не удалось обработать.<br><br>"
                f"<b>Причина:</b> {load_error}<br><br>"
                "Проверьте структуру столбцов или скачайте шаблон CSV в боковой панели."
            ),
            "error",
        )
    else:
        render_status_box(
            (
                "Онлайн-обновление не выполнено. Приложение не будет скрытно брать локальный файл проекта.<br><br>"
                f"<b>Причина:</b> {load_error}"
            ),
            "error",
        )
        if st.button("Перейти к ручной загрузке CSV", width="stretch"):
            st.session_state.source_selector = "Загрузить CSV файл"
            st.rerun()

    st.stop()


loading_placeholder.empty()

analysis_df = full_df.copy()
metadata = {
    **metadata,
    "analysis_period_label": f"{int(full_df['year'].min())}-{int(full_df['year'].max())}",
}
display_df = rename_for_display(full_df[DISPLAY_ORDER])
quality_df = dataset_quality_table(full_df[DISPLAY_ORDER], metadata)
revision_log = metadata.get("revision_log", pd.DataFrame())

correlation_outputs = build_correlation_outputs(analysis_df)
corr_summary = correlation_outputs["summary_table"]
pearson_matrix = correlation_outputs["pearson_matrix"]
spearman_matrix = correlation_outputs["spearman_matrix"]

comparison_df, model_results = build_model_comparison(analysis_df)
best_model_key = comparison_df.iloc[0]["Ключ"]

pca_result = build_pca_analysis(analysis_df)
cluster_result = build_cluster_analysis(analysis_df)
forecast_backtest = backtest_forecast_methods(analysis_df.set_index("year")[TARGET_COLUMN])
forecast_result = build_forecast(
    series=analysis_df.set_index("year")[TARGET_COLUMN],
    steps=forecast_horizon,
    method=forecast_method,
)

latest_row = full_df.iloc[-1]
min_row = analysis_df.loc[analysis_df[TARGET_COLUMN].idxmin()]
max_row = analysis_df.loc[analysis_df[TARGET_COLUMN].idxmax()]

render_hero(metadata)

if source_mode == "online":
    render_status_box(
        "Официальные данные загружены напрямую из онлайн-источников Росстата и Банка России.",
        "good",
    )
else:
    render_status_box(
        (
            f"Сейчас используется пользовательский CSV: <b>{metadata.get('uploaded_file_name', 'uploaded.csv')}</b>. "
            "Файл читается напрямую из интерфейса и не подменяется данными из проекта."
        ),
        "warn",
    )

metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric_card(
        "Наблюдений",
        len(analysis_df),
        "Количество годовых наблюдений, включенных в анализ.",
    )
with metric_cols[1]:
    render_metric_card(
        "Минимум безработицы",
        f"{min_row[TARGET_COLUMN]:.2f}%",
        f"{int(min_row['year'])} год",
    )
with metric_cols[2]:
    render_metric_card(
        "Максимум безработицы",
        f"{max_row[TARGET_COLUMN]:.2f}%",
        f"{int(max_row['year'])} год",
    )
with metric_cols[3]:
    render_metric_card(
        "Последнее значение",
        f"{latest_row[TARGET_COLUMN]:.2f}%",
        f"{int(latest_row['year'])} год",
    )

render_section_divider()
tabs = st.tabs(
    [
        "Паспорт исследования",
        "Данные и источники",
        "Связь факторов и регрессия",
        "PCA и кластеры",
        "Прогноз и выводы",
    ]
)
render_section_divider()

context = {
    "full_df": full_df,
    "analysis_df": analysis_df,
    "display_df": display_df,
    "quality_df": quality_df,
    "source_catalog": source_catalog,
    "metadata": metadata,
    "revision_log": revision_log,
    "corr_summary": corr_summary,
    "pearson_matrix": pearson_matrix,
    "spearman_matrix": spearman_matrix,
    "comparison_df": comparison_df,
    "model_results": model_results,
    "best_model_key": best_model_key,
    "pca_result": pca_result,
    "cluster_result": cluster_result,
    "forecast_backtest": forecast_backtest,
    "forecast_result": forecast_result,
    "forecast_method": forecast_method,
    "forecast_horizon": forecast_horizon,
}

with tabs[0]:
    render_overview_tab(context)

with tabs[1]:
    render_data_tab(context)

with tabs[2]:
    render_regression_tab(context)

with tabs[3]:
    render_pca_tab(context)

with tabs[4]:
    render_forecast_tab(context)
