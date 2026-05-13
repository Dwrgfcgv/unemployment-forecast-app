import io

import pandas as pd
import streamlit as st

from src.constants import (
    ANALYSIS_PERIOD_LABEL,
    CSV_TEMPLATE_COLUMNS,
    COLUMN_NAMES,
    PLOTLY_CONFIG,
)


def rename_for_display(dataframe):
    return dataframe.rename(columns=COLUMN_NAMES)


def format_indicator_name(column_name):
    return COLUMN_NAMES.get(column_name, column_name)


def format_timestamp(timestamp):
    if not timestamp:
        return "нет отметки времени"

    return str(timestamp).replace("T", " ").replace("+00:00", " UTC")


def make_excel_file(sheets):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet_name, sheet_df in sheets.items():
            sheet_df.to_excel(writer, index=False, sheet_name=sheet_name[:31])

    output.seek(0)
    return output


def render_plot(fig, key=None):
    st.plotly_chart(
        fig,
        width="stretch",
        theme="streamlit",
        config=PLOTLY_CONFIG,
        key=key,
    )


def render_metric_card(title, value, caption):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(title, body, box_class="section-card"):
    st.markdown(
        f"""
        <div class="{box_class}">
            <h3>{title}</h3>
            <div class="section-copy">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_box(body, kind):
    st.markdown(
        f"""
        <div class="status-box status-{kind}">
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_divider():
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


def render_section_gap():
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)


def render_dataframe(dataframe, *, height=None, hide_index=False, column_config=None):
    dataframe_kwargs = {
        "width": "stretch",
        "hide_index": hide_index,
    }

    if height is not None:
        dataframe_kwargs["height"] = height

    if column_config is not None:
        dataframe_kwargs["column_config"] = column_config

    st.dataframe(dataframe, **dataframe_kwargs)


def table_height(row_count, min_height=200, max_height=520, row_height=42, padding=68):
    return int(max(min_height, min(max_height, padding + row_count * row_height)))


def render_hero(metadata):
    source_label = metadata.get("source_mode_label", "не определен")
    update_label = format_timestamp(metadata.get("built_at_utc"))
    file_label = metadata.get("uploaded_file_name", "онлайн-источники")
    period_label = metadata.get("analysis_period_label", ANALYSIS_PERIOD_LABEL)

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">Практическая часть ВКР · период {period_label} · макроэкономические данные</div>
            <h1 class="hero-title">Анализ и прогнозирование безработицы на основе макроэкономических факторов</h1>
            <div class="hero-text">
                Приложение помогает оформить практическую часть ВКР на одном чистом аналитическом контуре:
                динамика показателей, связь факторов, регрессионные спецификации, PCA, кластеры и прогноз временного ряда.
            </div>
            <div class="chip-row">
                <div class="chip">Источник: {source_label}</div>
                <div class="chip">Период: {period_label}</div>
                <div class="chip">Последнее онлайн-обновление: {update_label}</div>
                <div class="chip">Текущий CSV: {file_label}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_csv_template():
    return pd.DataFrame(columns=CSV_TEMPLATE_COLUMNS).to_csv(index=False).encode("utf-8")
