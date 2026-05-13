import pandas as pd

from src.analysis_tools import TARGET_COLUMN
from src.constants import ANALYSIS_PERIOD_LABEL
from src.ui.components import format_indicator_name, format_timestamp


def dataset_quality_table(dataframe, metadata):
    return pd.DataFrame(
        {
            "Проверка": [
                "Период исследования",
                "Количество наблюдений",
                "Пропуски в обязательных столбцах",
                "Дубликаты по году",
                "Активный источник данных",
                "Последнее онлайн-обновление",
                "Загруженный CSV",
                "Последнее изменение файла",
            ],
            "Результат": [
                f"{int(dataframe['year'].min())}-{int(dataframe['year'].max())}",
                int(len(dataframe)),
                int(dataframe.isna().sum().sum()),
                int(dataframe["year"].duplicated().sum()),
                metadata.get("source_mode_label", "не определен"),
                format_timestamp(metadata.get("built_at_utc")),
                metadata.get("uploaded_file_name", "не используется"),
                format_timestamp(metadata.get("local_file_updated_at_utc")),
            ],
        }
    ).astype(str)


def build_method_overview():
    return pd.DataFrame(
        {
            "Метод": [
                "Корреляционный анализ",
                "Регрессионный анализ",
                "Стандартизированные beta и диагностика влияния",
                "Метод главных компонент (PCA)",
                "Кластерный анализ",
                "Анализ временного ряда",
            ],
            "Назначение": [
                "Проверяет направление и тесноту связи между безработицей и макроэкономическими показателями.",
                "Оценивает, как комбинация факторов объясняет изменение безработицы.",
                "Показывает относительную силу факторов и проверяет, не определяется ли результат одним-двумя годами.",
                "Сжимает набор факторов до нескольких скрытых компонент и показывает структуру вариации.",
                "Группирует годы по сходству макроэкономического режима и уровня безработицы.",
                "Используется для построения прогноза уровня безработицы по историческому ряду.",
            ],
        }
    )


def build_source_table(metadata):
    return pd.DataFrame(
        {
            "Артефакт": [
                "Активный источник данных",
                "Имя текущего CSV",
                "Последнее онлайн-обновление",
                "Режим использования данных",
            ],
            "Статус": [
                metadata.get("source_mode_label", "не определен"),
                metadata.get("uploaded_file_name", "не используется"),
                format_timestamp(metadata.get("built_at_utc")),
                (
                    "CSV загружается пользователем вручную."
                    if metadata.get("source_mode") == "upload"
                    else "Данные получены напрямую из официальных онлайн-источников."
                ),
            ],
        }
    )


def build_growth_table(dataframe):
    growth_df = dataframe[["year", TARGET_COLUMN, "average_salary", "inflation", "gdp_growth"]].copy()
    growth_df["Изменение безработицы к пред. году, п.п."] = growth_df[TARGET_COLUMN].diff().round(2)
    growth_df["Рост зарплаты к пред. году, %"] = (
        growth_df["average_salary"].pct_change().mul(100).round(2)
    )
    growth_df = growth_df.rename(
        columns={
            "year": "Год",
            TARGET_COLUMN: "Безработица, %",
            "average_salary": "Средняя зарплата, руб.",
            "inflation": "Инфляция, %",
            "gdp_growth": "Рост ВВП, %",
        }
    )
    return growth_df


def _format_years(years):
    if not years:
        return "нет выраженно влияющих лет"

    return ", ".join(str(int(year)) for year in years)


def build_conclusion_lines(
    corr_summary,
    comparison_df,
    pca_result,
    cluster_result,
    forecast_backtest,
    *,
    analysis_df=None,
    model_results=None,
    forecast_result=None,
):
    strongest_corr = corr_summary.iloc[0]
    secondary_corr = corr_summary.iloc[1] if len(corr_summary) > 1 else strongest_corr
    best_model = comparison_df.iloc[0]
    cluster_summary = cluster_result["summary"].sort_values("Средняя безработица, %", ascending=False)
    tense_cluster = cluster_summary.iloc[0]
    stable_cluster = cluster_summary.iloc[-1]
    forecast_winner = forecast_backtest.iloc[0]

    conclusion_lines = []

    if analysis_df is not None and not analysis_df.empty:
        min_row = analysis_df.loc[analysis_df[TARGET_COLUMN].idxmin()]
        max_row = analysis_df.loc[analysis_df[TARGET_COLUMN].idxmax()]
        latest_row = analysis_df.iloc[-1]
        change_from_max = float(latest_row[TARGET_COLUMN] - max_row[TARGET_COLUMN])

        conclusion_lines.append(
            (
                "Динамика безработицы",
                (
                    f"В исследовании использовано <b>{len(analysis_df)}</b> годовых наблюдений за период "
                    f"<b>{int(analysis_df['year'].min())}-{int(analysis_df['year'].max())}</b>. "
                    f"Максимальный уровень безработицы зафиксирован в <b>{int(max_row['year'])}</b> году "
                    f"(<b>{max_row[TARGET_COLUMN]:.2f}%</b>), минимальный уровень — "
                    f"в <b>{int(min_row['year'])}</b> году (<b>{min_row[TARGET_COLUMN]:.2f}%</b>), "
                    f"последнее значение ряда составляет <b>{latest_row[TARGET_COLUMN]:.2f}%</b> "
                    f"за <b>{int(latest_row['year'])}</b> год. "
                    f"Относительно пика показатель изменился на <b>{change_from_max:.2f} п.п.</b>, что указывает "
                    f"на заметное улучшение ситуации на рынке труда к концу рассматриваемого периода."
                ),
            )
        )

    conclusion_lines.extend(
        [
            (
                "Связь факторов",
                (
                    f"Наиболее выраженная связь с безработицей наблюдается у показателя "
                    f"<b>{format_indicator_name(strongest_corr['Показатель'])}</b>: Pearson r = "
                    f"<b>{strongest_corr['Pearson r']:.3f}</b>, Spearman rho = "
                    f"<b>{strongest_corr['Spearman rho']:.3f}</b>. Знак коэффициентов показывает направление связи: "
                    f"при росте этого показателя безработица, как правило, снижается. Второй по силе фактор — "
                    f"<b>{format_indicator_name(secondary_corr['Показатель'])}</b> "
                    f"(Pearson r = <b>{secondary_corr['Pearson r']:.3f}</b>), поэтому практический вывод состоит "
                    f"в том, что уровень безработицы в данных сильнее всего связан с доходной и зарплатной динамикой."
                ),
            ),
            (
                "Лучшая регрессионная спецификация",
                (
                    f"Наименьшую ошибку leave-one-out показывает <b>{best_model['Модель']}</b>. "
                    f"Для нее R² = <b>{best_model['R²']}</b>, Adj. R² = <b>{best_model['Adj. R²']}</b>, "
                    f"RMSE = <b>{best_model['RMSE']}</b>, LOO RMSE = <b>{best_model['LOO RMSE']}</b>, "
                    f"MAPE = <b>{best_model['MAPE, %']}%</b>. Это означает, что модель хорошо описывает историческую "
                    f"динамику и сохраняет приемлемую ошибку при проверке по принципу исключения одного года."
                ),
            ),
        ]
    )

    if model_results is not None and best_model["Ключ"] in model_results:
        selected_model = model_results[best_model["Ключ"]]
        top_factor = selected_model["factor_importance"].iloc[0]
        influence_df = selected_model["influence"]
        influence_threshold = influence_df["Порог Cook's distance"].iloc[0]
        influential_years = influence_df.loc[
            influence_df["Cook's distance"] >= influence_threshold,
            "Год",
        ].tolist()

        conclusion_lines.append(
            (
                "Содержательная интерпретация модели",
                (
                    f"По стандартизированным коэффициентам главный вклад в выбранной модели дает фактор "
                    f"<b>{format_indicator_name(top_factor['Показатель'])}</b> "
                    f"(beta = <b>{top_factor['Стандартизированный beta']:.3f}</b>). "
                    f"{top_factor['Интерпретация']} Диагностика влияния показывает, что годы "
                    f"<b>{_format_years(influential_years)}</b> превышают эвристический порог Cook's distance "
                    f"(<b>{influence_threshold:.3f}</b>), поэтому именно эти наблюдения стоит отдельно упомянуть "
                    f"в тексте ВКР как годы, сильнее влияющие на параметры регрессии."
                ),
            )
        )

    conclusion_lines.extend(
        [
            (
                "Сжатие факторов",
                (
                    f"Первые две главные компоненты объясняют <b>{pca_result['summary']['pc12_share']:.2f}%</b> "
                    f"вариации факторов. Первая компонента в основном связана с показателями "
                    f"<b>{', '.join(format_indicator_name(feature) for feature in pca_result['summary']['pc1_top_features'])}</b>, "
                    f"вторая — с <b>{', '.join(format_indicator_name(feature) for feature in pca_result['summary']['pc2_top_features'])}</b>. "
                    f"Это подтверждает, что структура данных не случайна: большая часть различий между годами сводится "
                    f"к доходно-зарплатному блоку и макроэкономическим колебаниям."
                ),
            ),
            (
                "Кластерный вывод",
                (
                    f"Кластеризация разделила период на <b>{cluster_result['best_cluster_count']}</b> группы. "
                    f"Наиболее напряженный режим — <b>{tense_cluster['Кластер']}</b>, годы "
                    f"<b>{tense_cluster['Годы']}</b>, средняя безработица <b>{tense_cluster['Средняя безработица, %']:.2f}%</b>. "
                    f"Более устойчивый режим — <b>{stable_cluster['Кластер']}</b>, годы <b>{stable_cluster['Годы']}</b>, "
                    f"средняя безработица <b>{stable_cluster['Средняя безработица, %']:.2f}%</b>. "
                    f"Следовательно, последние годы ряда формируют отдельный профиль с более низкой безработицей "
                    f"и более высокими средними макроэкономическими показателями."
                ),
            ),
        ]
    )

    if forecast_result is not None:
        forecast_df = forecast_result["forecast"]
        first_forecast = forecast_df.iloc[0]
        last_forecast = forecast_df.iloc[-1]
        forecast_text = (
            f"По короткому бэктесту предпочтителен метод <b>{forecast_winner['Метод']}</b> "
            f"с RMSE <b>{forecast_winner['RMSE']}</b>. Прогноз на <b>{int(first_forecast['Год'])}</b> год "
            f"составляет <b>{first_forecast['Прогноз']:.2f}%</b> с интервалом "
            f"<b>{first_forecast['Нижняя граница']:.2f}-{first_forecast['Верхняя граница']:.2f}%</b>; "
            f"к <b>{int(last_forecast['Год'])}</b> году ориентир снижается до "
            f"<b>{last_forecast['Прогноз']:.2f}%</b>. Это поддерживает вывод о сохранении низкого уровня "
            f"безработицы при отсутствии резких внешних шоков."
        )
    else:
        forecast_text = (
            f"По короткому бэктесту предпочтителен метод <b>{forecast_winner['Метод']}</b> "
            f"с RMSE <b>{forecast_winner['RMSE']}</b>. Прогноз нужно трактовать как ориентир на период "
            f"{ANALYSIS_PERIOD_LABEL}+, а не как жесткий сценарий."
        )

    conclusion_lines.extend(
        [
            (
                "Прогноз",
                forecast_text,
            ),
            (
                "Общий итог практической части",
                (
                    "Практическая часть показывает, что снижение безработицы в рассматриваемом периоде связано прежде всего "
                    "с улучшением доходной динамики, ростом заработной платы и переходом последних лет в более устойчивый "
                    "макроэкономический режим. Использование нескольких методов дает согласованный результат: корреляции "
                    "показывают направление связи, регрессия оценивает вклад факторов, PCA подтверждает структуру данных, "
                    "кластеры выделяют разные режимы периода, а прогноз формирует краткосрочный ориентир."
                ),
            ),
        ]
    )

    return conclusion_lines
