import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analysis_tools import MODEL_SPECS, TARGET_COLUMN
from src.constants import COLUMN_NAMES, PLOT_COLORS, SHORT_COLUMN_NAMES
from src.report_tables import (
    build_conclusion_lines,
    build_growth_table,
    build_method_overview,
    build_source_table,
)
from src.ui.components import (
    format_indicator_name,
    make_excel_file,
    rename_for_display,
    render_dataframe,
    render_info_card,
    render_metric_card,
    render_plot,
    render_section_gap,
    table_height,
)
from src.ui.figures import (
    apply_plot_style,
    build_factor_importance_figure,
    build_heatmap_figure,
    build_influence_figure,
)


def render_overview_tab(context):
    analysis_df = context["analysis_df"]
    comparison_df = context["comparison_df"]
    forecast_backtest = context["forecast_backtest"]
    pca_result = context["pca_result"]
    cluster_result = context["cluster_result"]

    top_left, top_right = st.columns([1.45, 1])

    with top_left:
        unemployment_fig = px.line(
            analysis_df,
            x="year",
            y=TARGET_COLUMN,
            markers=True,
            labels=COLUMN_NAMES,
            color_discrete_sequence=[PLOT_COLORS["navy"]],
        )
        unemployment_fig.update_traces(
            line=dict(width=4),
            marker=dict(size=9),
            hovertemplate="Год: %{x}<br>Безработица: %{y:.2f}%<extra></extra>",
        )
        apply_plot_style(unemployment_fig, "Динамика уровня безработицы", "Уровень безработицы, %")
        render_plot(unemployment_fig, key="overview_unemployment")

    with top_right:
        best_model_row = comparison_df.iloc[0]
        forecast_winner = forecast_backtest.iloc[0]

        render_info_card(
            "Что делает приложение",
            (
                "<b>1.</b> Формирует единый набор официальных макроданных.<br>"
                "<b>2.</b> Проверяет качество структуры и прозрачность источника.<br>"
                "<b>3.</b> Оценивает связь безработицы с ключевыми факторами.<br>"
                "<b>4.</b> Усиливает выводы регрессией, PCA, кластеризацией и прогнозом."
            ),
        )
        render_info_card(
            "Короткий итог по текущему расчету",
            (
                f"Наиболее устойчивой по leave-one-out выглядит <b>{best_model_row['Модель']}</b>.<br>"
                f"Ее LOO RMSE составляет <b>{best_model_row['LOO RMSE']}</b>.<br>"
                f"Для краткосрочного прогноза по бэктесту лучше всего себя показывает <b>{forecast_winner['Метод']}</b>."
            ),
        )

    method_cols = st.columns(3)
    with method_cols[0]:
        render_metric_card(
            "Лучшая модель",
            comparison_df.iloc[0]["Модель"].split(".")[0],
            "Основная спецификация выбирается по минимальной ошибке LOO RMSE.",
        )
    with method_cols[1]:
        render_metric_card(
            "Главные компоненты",
            f"{pca_result['summary']['pc12_share']:.1f}%",
            "Доля вариации факторов, объясняемая двумя первыми компонентами.",
        )
    with method_cols[2]:
        render_metric_card(
            "Кластеры годов",
            cluster_result["best_cluster_count"],
            "Оптимальное число кластеров выбрано по silhouette score.",
        )

    render_section_gap()
    render_info_card(
        "Методы исследования",
        "Ниже перечислены методы, которые используются в приложении и напрямую поддерживают практическую часть ВКР.",
    )
    render_section_gap()
    method_overview_df = build_method_overview()
    render_dataframe(
        method_overview_df,
        height=table_height(len(method_overview_df), min_height=300, max_height=360),
        hide_index=True,
    )


def render_data_tab(context):
    analysis_df = context["analysis_df"]
    display_df = context["display_df"]
    quality_df = context["quality_df"]
    metadata = context["metadata"]
    revision_log = context["revision_log"]
    source_catalog = context["source_catalog"]
    corr_summary = context["corr_summary"]
    comparison_df = context["comparison_df"]
    pca_result = context["pca_result"]
    cluster_result = context["cluster_result"]
    forecast_result = context["forecast_result"]

    st.subheader("Текущий набор данных")
    render_dataframe(display_df, height=420, hide_index=True)

    quality_col, stats_col = st.columns([1, 1.2])
    stats_df = rename_for_display(analysis_df).describe().T
    stats_df["Медиана"] = rename_for_display(analysis_df).median(numeric_only=True)
    quality_stats_height = max(
        table_height(len(quality_df), min_height=340, max_height=460),
        table_height(len(stats_df), min_height=340, max_height=460),
    )

    with quality_col:
        st.subheader("Проверка качества набора")
        render_dataframe(quality_df, height=quality_stats_height, hide_index=True)

    with stats_col:
        st.subheader("Описательная статистика")
        render_dataframe(stats_df.round(3), height=quality_stats_height)

    growth_df = build_growth_table(analysis_df)
    st.subheader("Годовые изменения ключевых показателей")
    render_dataframe(
        growth_df,
        height=table_height(len(growth_df), min_height=260, max_height=340),
        hide_index=True,
    )

    if revision_log is not None and not revision_log.empty:
        st.subheader("Изменения после последнего онлайн-обновления")
        revision_display = revision_log.copy()
        revision_display["Показатель"] = revision_display["Показатель"].map(format_indicator_name)
        render_dataframe(
            revision_display,
            height=table_height(len(revision_display), min_height=250, max_height=320),
            hide_index=True,
        )

    st.subheader("Каталог источников")
    render_dataframe(
        source_catalog,
        height=table_height(len(source_catalog), min_height=310, max_height=420),
        hide_index=True,
        column_config={"URL": st.column_config.LinkColumn("URL")},
    )

    if metadata.get("notes"):
        notes_html = "<br>".join(f"• {note}" for note in metadata["notes"])
        render_info_card("Методологические примечания", notes_html)

    st.subheader("Текущий источник данных")
    render_dataframe(
        build_source_table(metadata),
        height=table_height(4, min_height=210, max_height=240),
        hide_index=True,
    )

    export_excel = make_excel_file(
        {
            "Данные": display_df,
            "Качество": quality_df,
            "Источники": source_catalog,
            "Корреляции": corr_summary.assign(
                Показатель=lambda frame: frame["Показатель"].map(format_indicator_name)
            ),
            "Регрессии": comparison_df.assign(
                Факторы=lambda frame: frame["Ключ"].map(
                    lambda key: ", ".join(
                        format_indicator_name(feature)
                        for feature in MODEL_SPECS[key]["features"]
                    )
                )
            ).drop(columns=["Ключ"]),
            "PCA": pca_result["explained_variance"],
            "Кластеры": cluster_result["summary"],
            "Прогноз": forecast_result["forecast"],
        }
    )

    download_cols = st.columns(2)
    with download_cols[0]:
        st.download_button(
            label="Скачать проверенный CSV",
            data=context["full_df"].to_csv(index=False).encode("utf-8"),
            file_name="unemployment_dataset_checked.csv",
            mime="text/csv",
            width="stretch",
        )
    with download_cols[1]:
        st.download_button(
            label="Скачать аналитическую книгу Excel",
            data=export_excel,
            file_name="unemployment_analysis_bundle.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )


def render_regression_tab(context):
    analysis_df = context["analysis_df"]
    corr_summary = context["corr_summary"]
    pearson_matrix = context["pearson_matrix"]
    spearman_matrix = context["spearman_matrix"]
    comparison_df = context["comparison_df"]
    model_results = context["model_results"]
    best_model_key = context["best_model_key"]

    render_info_card(
        "Как читать этот раздел",
        (
            "Сначала оценивается теснота связи безработицы с факторами через Pearson и Spearman, затем сравниваются несколько "
            "регрессионных спецификаций. После этого добавлена диагностика вклада факторов и влияния отдельных лет, "
            "чтобы выводы для ВКР выглядели устойчивее и аккуратнее."
        ),
    )

    corr_display = corr_summary.copy()
    corr_display["Показатель"] = corr_display["Показатель"].map(format_indicator_name)
    st.subheader("Сводная таблица корреляций")
    render_dataframe(
        corr_display.round(4),
        height=table_height(len(corr_display), min_height=300, max_height=360),
        hide_index=True,
    )

    strongest_factor = corr_summary.iloc[0]["Показатель"]
    scatter_fig = px.scatter(
        analysis_df,
        x=strongest_factor,
        y=TARGET_COLUMN,
        text="year",
        trendline="ols",
        color_discrete_sequence=[PLOT_COLORS["blue"]],
        labels=COLUMN_NAMES,
    )
    scatter_fig.update_traces(
        marker=dict(size=11, line=dict(color="#ffffff", width=1.5)),
        textposition="top center",
        hovertemplate=(
            "Год: %{text}<br>"
            + f"{format_indicator_name(strongest_factor)}: "
            + "%{x:.2f}<br>Безработица: %{y:.2f}%<extra></extra>"
        ),
    )
    apply_plot_style(
        scatter_fig,
        f"Связь безработицы с фактором: {format_indicator_name(strongest_factor)}",
        "Уровень безработицы, %",
    )

    corr_col1, corr_col2 = st.columns(2)
    with corr_col1:
        render_plot(build_heatmap_figure(pearson_matrix, "Матрица Pearson"), key="pearson_heatmap")
    with corr_col2:
        render_plot(build_heatmap_figure(spearman_matrix, "Матрица Spearman"), key="spearman_heatmap")

    render_plot(scatter_fig, key="factor_scatter")

    st.subheader("Сравнение регрессионных моделей")
    comparison_display = comparison_df.copy()
    comparison_display["Факторы"] = comparison_display["Ключ"].map(
        lambda key: ", ".join(format_indicator_name(feature) for feature in MODEL_SPECS[key]["features"])
    )
    render_dataframe(
        comparison_display.drop(columns=["Ключ"]),
        height=table_height(len(comparison_display), min_height=220, max_height=280),
        hide_index=True,
    )

    model_labels = [MODEL_SPECS[key]["label"] for key in comparison_df["Ключ"]]
    label_to_key = {MODEL_SPECS[key]["label"]: key for key in comparison_df["Ключ"]}
    selected_model_label = st.selectbox(
        "Модель для детального разбора",
        model_labels,
        index=model_labels.index(MODEL_SPECS[best_model_key]["label"]),
    )
    selected_model_key = label_to_key[selected_model_label]
    selected_model = model_results[selected_model_key]

    active_spec = selected_model["spec"]
    render_info_card(
        active_spec["label"],
        (
            f"<b>Состав факторов:</b> {', '.join(format_indicator_name(feature) for feature in active_spec['features'])}.<br>"
            f"<b>Описание:</b> {active_spec['description']}<br>"
            f"<b>Практический смысл:</b> {active_spec['purpose']}"
        ),
    )

    model_metrics = st.columns(5)
    with model_metrics[0]:
        st.metric("R²", f"{selected_model['metrics']['r2']:.3f}")
    with model_metrics[1]:
        st.metric("Adj. R²", f"{selected_model['metrics']['adj_r2']:.3f}")
    with model_metrics[2]:
        st.metric("RMSE", f"{selected_model['metrics']['rmse']:.3f}")
    with model_metrics[3]:
        st.metric("LOO RMSE", f"{selected_model['metrics']['loo_rmse']:.3f}")
    with model_metrics[4]:
        st.metric("Макс. VIF", f"{selected_model['metrics']['max_vif']:.2f}")

    coeff_col, diag_col = st.columns([1.15, 1])
    with coeff_col:
        st.subheader("Коэффициенты модели")
        coeff_df = selected_model["coefficients"].copy()
        coeff_df["Показатель"] = coeff_df["Показатель"].map(format_indicator_name)
        render_dataframe(
            coeff_df.round(4),
            height=table_height(len(coeff_df), min_height=360, max_height=460),
            hide_index=True,
        )

    with diag_col:
        st.subheader("Диагностика")
        render_dataframe(
            selected_model["diagnostics"].round(4),
            height=table_height(len(selected_model["diagnostics"]), min_height=180, max_height=240),
            hide_index=True,
        )
        render_dataframe(
            selected_model["vif"].assign(
                Показатель=lambda frame: frame["Показатель"].map(format_indicator_name)
            ).round(3),
            height=table_height(len(selected_model["vif"]), min_height=220, max_height=280),
            hide_index=True,
        )

    importance_df = selected_model["factor_importance"].copy()
    importance_df["Показатель"] = importance_df["Показатель"].map(format_indicator_name)
    influence_df = selected_model["influence"].copy()

    importance_col, influence_col = st.columns([1.05, 0.95])
    with importance_col:
        render_plot(build_factor_importance_figure(importance_df), key=f"importance_{selected_model_key}")

        top_factor = importance_df.iloc[0]
        render_info_card(
            "Интерпретация вклада факторов",
            (
                f"Наибольший стандартизированный вклад в выбранной модели показывает фактор "
                f"<b>{top_factor['Показатель']}</b> (beta = <b>{top_factor['Стандартизированный beta']:.3f}</b>). "
                f"{top_factor['Интерпретация']}"
            ),
        )

    with influence_col:
        render_plot(build_influence_figure(influence_df), key=f"influence_{selected_model_key}")

        influence_threshold = influence_df["Порог Cook's distance"].iloc[0]
        flagged_years = influence_df.loc[
            influence_df["Cook's distance"] >= influence_threshold,
            "Год",
        ].astype(int).tolist()
        flagged_text = ", ".join(map(str, flagged_years)) if flagged_years else "выраженно влияющих лет не обнаружено"
        render_info_card(
            "Устойчивость результата по годам",
            (
                f"Эвристический порог Cook's distance для данной модели: <b>{influence_threshold:.3f}</b>.<br>"
                f"Потенциально влияющие годы: <b>{flagged_text}</b>."
            ),
        )

    st.subheader("Таблица влияния наблюдений")
    render_dataframe(
        influence_df.round(4),
        height=table_height(len(influence_df), min_height=260, max_height=360),
        hide_index=True,
    )

    fit_col, residual_col = st.columns(2)
    fit_df = selected_model["actual_vs_fitted"]
    with fit_col:
        fit_fig = px.line(
            fit_df,
            x="Год",
            y=["Фактическое значение", "Расчетное значение"],
            markers=True,
            color_discrete_sequence=[PLOT_COLORS["navy"], PLOT_COLORS["gold"]],
        )
        fit_fig.update_traces(
            line=dict(width=3),
            hovertemplate="Год: %{x}<br>Значение: %{y:.2f}%<extra></extra>",
        )
        apply_plot_style(fit_fig, "Фактические и расчетные значения", "Уровень безработицы, %")
        render_plot(fit_fig, key="fit_chart")

    with residual_col:
        residual_fig = px.bar(
            fit_df,
            x="Год",
            y="Остаток",
            color="Остаток",
            color_continuous_scale=["#fca5a5", "#fef3c7", "#1d4ed8"],
        )
        residual_fig.update_traces(hovertemplate="Год: %{x}<br>Остаток: %{y:.3f}<extra></extra>")
        apply_plot_style(residual_fig, "Остатки модели", "Остаток")
        render_plot(residual_fig, key="residual_chart")


def render_pca_tab(context):
    pca_result = context["pca_result"]
    cluster_result = context["cluster_result"]

    render_info_card(
        "Зачем здесь PCA и кластеризация",
        (
            "PCA помогает увидеть скрытые сочетания факторов, которые формируют основную вариацию макроэкономической среды, "
            "а кластерный анализ группирует годы по схожему профилю безработицы, доходов, инфляции, ВВП и ставки. "
            "Для ВКР это хорошая независимая проверка структуры данных."
        ),
    )

    pca_cols = st.columns([1, 1.1])
    pca_table_height = max(
        table_height(len(pca_result["explained_variance"]), min_height=280, max_height=340),
        table_height(len(pca_result["loadings"]), min_height=280, max_height=340),
    )
    with pca_cols[0]:
        st.subheader("Дисперсия компонент PCA")
        render_dataframe(pca_result["explained_variance"], height=pca_table_height, hide_index=True)

    with pca_cols[1]:
        st.subheader("Нагрузки факторов PCA")
        loadings_display = pca_result["loadings"].copy()
        loadings_display["Показатель"] = loadings_display["Показатель"].map(
            lambda column: SHORT_COLUMN_NAMES.get(column, format_indicator_name(column))
        )
        render_dataframe(loadings_display, height=pca_table_height, hide_index=True)

    pca_scores = pca_result["scores"].merge(
        cluster_result["assignments"][["Год", "Кластер"]],
        on="Год",
        how="left",
    )
    pca_fig = px.scatter(
        pca_scores,
        x="PC1",
        y="PC2",
        color="Кластер",
        text="Год",
        color_discrete_sequence=[
            PLOT_COLORS["navy"],
            PLOT_COLORS["gold"],
            PLOT_COLORS["teal"],
            PLOT_COLORS["blue"],
        ],
    )
    pca_fig.update_traces(
        marker=dict(size=14, line=dict(color="#ffffff", width=1.5)),
        textposition="top center",
        hovertemplate="Год: %{text}<br>PC1: %{x:.3f}<br>PC2: %{y:.3f}<extra></extra>",
    )
    apply_plot_style(pca_fig, "Годы в пространстве первых двух компонент", "PC2")
    pca_fig.update_xaxes(title="PC1")
    render_plot(pca_fig, key="pca_scatter")

    cluster_eval_col, cluster_summary_col = st.columns([0.95, 1.25])
    cluster_table_height = max(
        table_height(len(cluster_result["evaluation"]), min_height=230, max_height=300),
        table_height(len(cluster_result["summary"]), min_height=230, max_height=300),
    )
    with cluster_eval_col:
        st.subheader("Подбор числа кластеров")
        render_dataframe(cluster_result["evaluation"], height=cluster_table_height, hide_index=True)
        render_info_card(
            "Итог кластеризации",
            (
                f"Оптимальное число кластеров: <b>{cluster_result['best_cluster_count']}</b>.<br>"
                f"Лучшее значение silhouette score: <b>{cluster_result['best_silhouette']:.3f}</b>."
            ),
        )

    with cluster_summary_col:
        st.subheader("Профили кластеров")
        render_dataframe(cluster_result["summary"], height=cluster_table_height, hide_index=True)

    st.subheader("Распределение лет по кластерам")
    render_dataframe(
        cluster_result["assignments"],
        height=table_height(len(cluster_result["assignments"]), min_height=220, max_height=280),
        hide_index=True,
    )


def render_forecast_tab(context):
    forecast_backtest = context["forecast_backtest"]
    forecast_method = context["forecast_method"]
    forecast_horizon = context["forecast_horizon"]
    forecast_result = context["forecast_result"]
    corr_summary = context["corr_summary"]
    comparison_df = context["comparison_df"]
    pca_result = context["pca_result"]
    cluster_result = context["cluster_result"]

    st.subheader("Мини-бэктест методов прогноза")
    render_dataframe(
        forecast_backtest,
        height=table_height(len(forecast_backtest), min_height=180, max_height=240),
        hide_index=True,
    )

    forecast_info_cols = st.columns(2)
    with forecast_info_cols[0]:
        render_info_card("Выбранный метод прогноза", forecast_method)
    with forecast_info_cols[1]:
        render_info_card("Горизонт прогноза", f"{forecast_horizon} года(лет)")

    history_df = forecast_result["history"]
    forecast_df = forecast_result["forecast"]
    last_history_year = int(history_df["Год"].iloc[-1])
    last_history_value = float(history_df["Историческое значение"].iloc[-1])
    forecast_plot_years = [last_history_year, *forecast_df["Год"].astype(int).tolist()]
    forecast_plot_values = [last_history_value, *forecast_df["Прогноз"].astype(float).tolist()]
    forecast_upper_values = [last_history_value, *forecast_df["Верхняя граница"].astype(float).tolist()]
    forecast_lower_values = [last_history_value, *forecast_df["Нижняя граница"].astype(float).tolist()]
    forecast_hover_labels = ["Старт прогноза", *["Прогноз"] * len(forecast_df)]
    forecast_fig = go.Figure()
    forecast_fig.add_trace(
        go.Scatter(
            x=history_df["Год"],
            y=history_df["Историческое значение"],
            mode="lines+markers",
            name="Исторические данные",
            line=dict(color=PLOT_COLORS["navy"], width=4),
        )
    )
    forecast_fig.add_trace(
        go.Scatter(
            x=forecast_plot_years,
            y=forecast_plot_values,
            mode="lines+markers",
            name="Прогноз",
            customdata=forecast_hover_labels,
            line=dict(color=PLOT_COLORS["gold"], width=4, dash="dash"),
            hovertemplate="Год: %{x}<br>%{customdata}: %{y:.2f}%<extra></extra>",
        )
    )
    forecast_fig.add_trace(
        go.Scatter(
            x=forecast_plot_years,
            y=forecast_upper_values,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    forecast_fig.add_trace(
        go.Scatter(
            x=forecast_plot_years,
            y=forecast_lower_values,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(245, 158, 11, 0.14)",
            name="95% интервал",
            hoverinfo="skip",
        )
    )
    forecast_fig.add_vline(
        x=last_history_year,
        line_width=2,
        line_dash="dot",
        line_color="rgba(148, 163, 184, 0.72)",
    )
    apply_plot_style(forecast_fig, "Прогноз уровня безработицы", "Уровень безработицы, %")
    render_plot(forecast_fig, key="forecast_chart")

    st.subheader("Таблица прогноза")
    render_dataframe(
        forecast_df,
        height=table_height(len(forecast_df), min_height=220, max_height=300),
        hide_index=True,
    )

    render_info_card(
        "Итоговые выводы для практической части",
        "<br><br>".join(
            f"<b>{title}.</b> {body}"
            for title, body in build_conclusion_lines(
                corr_summary,
                comparison_df,
                pca_result,
                cluster_result,
                forecast_backtest,
                analysis_df=context["analysis_df"],
                model_results=context["model_results"],
                forecast_result=forecast_result,
            )
        ),
    )
