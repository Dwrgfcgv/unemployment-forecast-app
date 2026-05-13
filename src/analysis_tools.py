import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing


TARGET_COLUMN = "unemployment_rate"
FACTOR_COLUMNS = [
    "average_salary",
    "inflation",
    "real_income_index",
    "gdp_growth",
    "key_rate",
]
CLUSTER_COLUMNS = [TARGET_COLUMN, *FACTOR_COLUMNS]

MODEL_SPECS = {
    "social": {
        "label": "Модель 1. Социально-ценовые факторы",
        "description": (
            "Показывает связь безработицы со средней заработной платой, "
            "инфляцией и платежеспособностью населения."
        ),
        "features": ["average_salary", "inflation", "real_income_index"],
        "purpose": "Базовая регрессионная спецификация для основной части исследования.",
    },
    "monetary": {
        "label": "Модель 2. Социально-ценовые факторы и денежно-кредитная среда",
        "description": (
            "Дополняет базовую модель ключевой ставкой Банка России "
            "как индикатором жесткости денежно-кредитной политики."
        ),
        "features": ["average_salary", "inflation", "real_income_index", "key_rate"],
        "purpose": "Подходит для проверки, усиливает ли объясняющую способность учет кредитной среды.",
    },
    "cycle": {
        "label": "Модель 3. Макроэкономический цикл",
        "description": (
            "Сопоставляет безработицу с инфляцией, реальными доходами, "
            "темпом роста ВВП и ключевой ставкой."
        ),
        "features": ["inflation", "real_income_index", "gdp_growth", "key_rate"],
        "purpose": "Используется как альтернативная спецификация для проверки устойчивости выводов.",
    },
}


def safe_mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mask = y_true != 0

    if mask.sum() == 0:
        return np.nan

    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def normality_test(residuals):
    residuals = pd.Series(residuals).dropna()

    if len(residuals) < 3:
        return np.nan, np.nan

    statistic, p_value = stats.shapiro(residuals)
    return float(statistic), float(p_value)


def interpret_vif(value):
    if value < 5:
        return "Низкая"
    if value < 10:
        return "Умеренная"
    return "Высокая"


def correlation_strength(value):
    abs_value = abs(value)

    if abs_value >= 0.7:
        return "Сильная"
    if abs_value >= 0.4:
        return "Умеренная"
    if abs_value >= 0.2:
        return "Слабая"
    return "Очень слабая"


def diagnostic_conclusion(metric_name, value):
    if pd.isna(value):
        return "Недостаточно данных для вывода."

    if metric_name == "shapiro_p":
        return (
            "Остатки не противоречат нормальности."
            if value >= 0.05
            else "Есть риск отклонения остатков от нормального распределения."
        )
    if metric_name == "durbin_watson":
        return (
            "Автокорреляция остатков не выглядит выраженной."
            if 1.5 <= value <= 2.5
            else "Нужна осторожность: возможна автокорреляция остатков."
        )
    if metric_name == "condition_number":
        return (
            "Численная устойчивость выглядит приемлемой."
            if value < 30
            else "Есть риск неустойчивости из-за масштаба факторов или мультиколлинеарности."
        )
    if metric_name == "f_pvalue":
        return (
            "Модель в целом статистически значима."
            if value < 0.05
            else "Модель в целом не подтверждена на уровне 5%."
        )

    return "Интерпретация не задана."


def _pairwise_correlation(x_series, y_series, method):
    x_clean = pd.to_numeric(x_series, errors="coerce")
    y_clean = pd.to_numeric(y_series, errors="coerce")
    valid = pd.concat([x_clean, y_clean], axis=1).dropna()

    if len(valid) < 3:
        return np.nan, np.nan

    if method == "pearson":
        statistic, p_value = stats.pearsonr(valid.iloc[:, 0], valid.iloc[:, 1])
    else:
        statistic, p_value = stats.spearmanr(valid.iloc[:, 0], valid.iloc[:, 1])

    return float(statistic), float(p_value)


def build_correlation_outputs(dataframe, feature_columns=None):
    feature_columns = feature_columns or FACTOR_COLUMNS
    analysis_columns = [TARGET_COLUMN, *feature_columns]
    correlation_df = dataframe[analysis_columns].astype(float)

    pearson_matrix = correlation_df.corr(method="pearson")
    spearman_matrix = correlation_df.corr(method="spearman")

    rows = []

    for feature in feature_columns:
        pearson_r, pearson_p = _pairwise_correlation(
            correlation_df[feature],
            correlation_df[TARGET_COLUMN],
            method="pearson",
        )
        spearman_rho, spearman_p = _pairwise_correlation(
            correlation_df[feature],
            correlation_df[TARGET_COLUMN],
            method="spearman",
        )

        rows.append(
            {
                "Показатель": feature,
                "Pearson r": pearson_r,
                "Pearson p-value": pearson_p,
                "Spearman rho": spearman_rho,
                "Spearman p-value": spearman_p,
                "Сила линейной связи": correlation_strength(pearson_r) if not pd.isna(pearson_r) else "Нет данных",
                "Направление": (
                    "Положительная"
                    if pd.notna(pearson_r) and pearson_r > 0
                    else "Отрицательная"
                    if pd.notna(pearson_r) and pearson_r < 0
                    else "Нет данных"
                ),
            }
        )

    summary_df = pd.DataFrame(rows).sort_values(
        by="Pearson r",
        key=lambda series: series.abs(),
        ascending=False,
    ).reset_index(drop=True)

    return {
        "pearson_matrix": pearson_matrix,
        "spearman_matrix": spearman_matrix,
        "summary_table": summary_df,
    }


def _calculate_vif(dataframe, features):
    X = sm.add_constant(dataframe[features], has_constant="add")
    rows = []

    for index, column in enumerate(X.columns):
        vif_value = variance_inflation_factor(X.values, index)
        rows.append(
            {
                "Показатель": "Константа" if column == "const" else column,
                "VIF": float(vif_value),
                "Оценка": interpret_vif(float(vif_value)),
            }
        )

    return pd.DataFrame(rows)


def _standardized_betas(dataframe, features):
    X = dataframe[features].astype(float)
    y = dataframe[TARGET_COLUMN].astype(float)

    X_std = (X - X.mean()) / X.std(ddof=0)
    y_std = (y - y.mean()) / y.std(ddof=0)

    model = sm.OLS(y_std, sm.add_constant(X_std, has_constant="add")).fit()

    return {
        feature: float(model.params.get(feature, np.nan))
        for feature in features
    }


def _build_factor_importance(standardized_betas):
    importance_df = pd.DataFrame(
        [
            {
                "Показатель": feature,
                "Стандартизированный beta": value,
                "Абсолютный вклад": abs(value),
                "Интерпретация": (
                    "Рост фактора связан с повышением безработицы."
                    if value > 0
                    else "Рост фактора связан со снижением безработицы."
                ),
            }
            for feature, value in standardized_betas.items()
        ]
    )

    return importance_df.sort_values("Абсолютный вклад", ascending=False).reset_index(drop=True)


def _build_influence_table(model, years):
    influence = OLSInfluence(model)
    cooks_distance = influence.cooks_distance[0]
    leverage = influence.hat_matrix_diag
    studentized = influence.resid_studentized_external
    threshold = 4 / len(years)

    influence_df = pd.DataFrame(
        {
            "Год": years.astype(int).values,
            "Cook's distance": cooks_distance,
            "Leverage": leverage,
            "Studentized residual": studentized,
        }
    )
    influence_df["Порог Cook's distance"] = threshold
    influence_df["Статус"] = influence_df["Cook's distance"].apply(
        lambda value: "Повышенное влияние"
        if value >= threshold
        else "Умеренное влияние"
        if value >= threshold * 0.6
        else "Обычное влияние"
    )

    return influence_df.sort_values("Cook's distance", ascending=False).reset_index(drop=True)


def _leave_one_out_metrics(dataframe, features):
    X = dataframe[features].astype(float).reset_index(drop=True)
    y = dataframe[TARGET_COLUMN].astype(float).reset_index(drop=True)

    predictions = []
    observations = []

    loo = LeaveOneOut()

    for train_index, test_index in loo.split(X):
        X_train = sm.add_constant(X.iloc[train_index], has_constant="add")
        X_test = sm.add_constant(X.iloc[test_index], has_constant="add")
        y_train = y.iloc[train_index]
        y_test = y.iloc[test_index]

        model = sm.OLS(y_train, X_train).fit()
        prediction = model.predict(X_test).iloc[0]

        predictions.append(float(prediction))
        observations.append(float(y_test.iloc[0]))

    return {
        "loo_mae": float(mean_absolute_error(observations, predictions)),
        "loo_rmse": float(mean_squared_error(observations, predictions) ** 0.5),
    }


def fit_regression_model(dataframe, spec_key):
    spec = MODEL_SPECS[spec_key]
    features = spec["features"]

    X = dataframe[features].astype(float)
    y = dataframe[TARGET_COLUMN].astype(float)
    X_const = sm.add_constant(X, has_constant="add")

    model = sm.OLS(y, X_const).fit()
    predictions = model.predict(X_const)
    residuals = y - predictions

    shapiro_stat, shapiro_p = normality_test(residuals)
    loo_metrics = _leave_one_out_metrics(dataframe, features)
    standardized = _standardized_betas(dataframe, features)
    importance_df = _build_factor_importance(standardized)
    vif_df = _calculate_vif(dataframe, features)
    confidence_intervals = model.conf_int(alpha=0.05)
    influence_df = _build_influence_table(model, dataframe["year"])

    coef_rows = []

    for name in model.params.index:
        p_value = float(model.pvalues[name])
        coef_rows.append(
            {
                "Показатель": "Константа" if name == "const" else name,
                "Коэффициент": float(model.params[name]),
                "Стандартизированный beta": np.nan if name == "const" else standardized.get(name, np.nan),
                "p-value": p_value,
                "Нижняя граница 95%": float(confidence_intervals.loc[name, 0]),
                "Верхняя граница 95%": float(confidence_intervals.loc[name, 1]),
                "Значимость на 5%": "Да" if p_value < 0.05 else "Нет",
            }
        )

    actual_vs_fitted = pd.DataFrame(
        {
            "Год": dataframe["year"].astype(int),
            "Фактическое значение": y,
            "Расчетное значение": predictions,
            "Остаток": residuals,
            "Абсолютная ошибка": np.abs(residuals),
        }
    )

    metrics = {
        "r2": float(r2_score(y, predictions)),
        "adj_r2": float(model.rsquared_adj),
        "mae": float(mean_absolute_error(y, predictions)),
        "rmse": float(mean_squared_error(y, predictions) ** 0.5),
        "mape": float(safe_mape(y, predictions)),
        "loo_mae": loo_metrics["loo_mae"],
        "loo_rmse": loo_metrics["loo_rmse"],
        "f_pvalue": float(model.f_pvalue),
        "condition_number": float(model.condition_number),
        "shapiro_stat": shapiro_stat,
        "shapiro_p": shapiro_p,
        "durbin_watson": float(durbin_watson(residuals)),
        "n_obs": int(len(dataframe)),
        "features_count": int(len(features)),
        "max_vif": float(vif_df["VIF"].iloc[1:].max()),
    }

    diagnostics = pd.DataFrame(
        {
            "Показатель": [
                "F-тест p-value",
                "Shapiro-Wilk p-value",
                "Durbin-Watson",
                "Condition number",
            ],
            "Значение": [
                metrics["f_pvalue"],
                metrics["shapiro_p"],
                metrics["durbin_watson"],
                metrics["condition_number"],
            ],
            "Вывод": [
                diagnostic_conclusion("f_pvalue", metrics["f_pvalue"]),
                diagnostic_conclusion("shapiro_p", metrics["shapiro_p"]),
                diagnostic_conclusion("durbin_watson", metrics["durbin_watson"]),
                diagnostic_conclusion("condition_number", metrics["condition_number"]),
            ],
        }
    )

    return {
        "spec": spec,
        "features": features,
        "model": model,
        "metrics": metrics,
        "coefficients": pd.DataFrame(coef_rows),
        "factor_importance": importance_df,
        "vif": vif_df,
        "diagnostics": diagnostics,
        "influence": influence_df,
        "actual_vs_fitted": actual_vs_fitted,
    }


def build_model_comparison(dataframe):
    rows = []
    results = {}

    for spec_key, spec in MODEL_SPECS.items():
        result = fit_regression_model(dataframe, spec_key)
        results[spec_key] = result
        metrics = result["metrics"]

        rows.append(
            {
                "Ключ": spec_key,
                "Модель": spec["label"],
                "Назначение": spec["purpose"],
                "Факторы": ", ".join(spec["features"]),
                "R²": round(metrics["r2"], 3),
                "Adj. R²": round(metrics["adj_r2"], 3),
                "RMSE": round(metrics["rmse"], 3),
                "LOO RMSE": round(metrics["loo_rmse"], 3),
                "MAPE, %": round(metrics["mape"], 2),
                "F p-value": round(metrics["f_pvalue"], 4),
                "Макс. VIF": round(metrics["max_vif"], 2),
            }
        )

    comparison_df = pd.DataFrame(rows).sort_values(
        by=["LOO RMSE", "Adj. R²"],
        ascending=[True, False],
    ).reset_index(drop=True)

    best_key = comparison_df.iloc[0]["Ключ"]
    comparison_df["Статус"] = comparison_df["Ключ"].apply(
        lambda key: "Оптимальна по LOO RMSE" if key == best_key else "Альтернативная"
    )

    return comparison_df, results


def build_pca_analysis(dataframe, feature_columns=None):
    feature_columns = feature_columns or FACTOR_COLUMNS
    features_df = dataframe[feature_columns].astype(float)

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(features_df)

    pca = PCA()
    scores = pca.fit_transform(scaled_values)
    component_names = [f"PC{i + 1}" for i in range(scores.shape[1])]

    explained_df = pd.DataFrame(
        {
            "Компонента": component_names,
            "Собственное значение": pca.explained_variance_,
            "Доля дисперсии, %": pca.explained_variance_ratio_ * 100,
            "Накопленная доля, %": np.cumsum(pca.explained_variance_ratio_) * 100,
        }
    ).round(3)

    loadings_df = pd.DataFrame(
        pca.components_.T,
        index=feature_columns,
        columns=component_names,
    ).reset_index().rename(columns={"index": "Показатель"})

    scores_df = pd.DataFrame(scores, columns=component_names)
    scores_df.insert(0, "Год", dataframe["year"].astype(int).values)

    top_pc1 = (
        loadings_df[["Показатель", "PC1"]]
        .assign(Абсолютная_нагрузка=lambda frame: frame["PC1"].abs())
        .sort_values("Абсолютная_нагрузка", ascending=False)
        .head(2)
    )
    top_pc2 = (
        loadings_df[["Показатель", "PC2"]]
        .assign(Абсолютная_нагрузка=lambda frame: frame["PC2"].abs())
        .sort_values("Абсолютная_нагрузка", ascending=False)
        .head(2)
    )

    summary = {
        "pc1_share": float(explained_df.loc[0, "Доля дисперсии, %"]),
        "pc2_share": float(explained_df.loc[1, "Доля дисперсии, %"]) if len(explained_df) > 1 else np.nan,
        "pc12_share": float(explained_df.loc[:1, "Доля дисперсии, %"].sum()),
        "pc1_top_features": top_pc1["Показатель"].tolist(),
        "pc2_top_features": top_pc2["Показатель"].tolist(),
    }

    return {
        "explained_variance": explained_df,
        "loadings": loadings_df.round(4),
        "scores": scores_df.round(4),
        "summary": summary,
    }


def _cluster_profile(row, unemployment_mean, salary_mean):
    if row["Средняя безработица, %"] > unemployment_mean and row["Средняя зарплата, руб."] < salary_mean:
        return "Периоды более напряженного рынка труда."
    if row["Средняя безработица, %"] < unemployment_mean and row["Средняя зарплата, руб."] > salary_mean:
        return "Периоды более устойчивого рынка труда."
    return "Промежуточный макроэкономический режим."


def build_cluster_analysis(dataframe, feature_columns=None):
    feature_columns = feature_columns or CLUSTER_COLUMNS
    cluster_df = dataframe[["year", *feature_columns]].copy()

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(cluster_df[feature_columns].astype(float))

    evaluation_rows = []
    best_score = None
    best_model = None
    best_labels = None

    max_clusters = min(4, len(cluster_df) - 1)

    for clusters_count in range(2, max_clusters + 1):
        model = KMeans(n_clusters=clusters_count, random_state=42, n_init=30)
        labels = model.fit_predict(scaled_values)
        score = silhouette_score(scaled_values, labels)

        evaluation_rows.append(
            {
                "Количество кластеров": clusters_count,
                "Silhouette": round(float(score), 3),
                "Inertia": round(float(model.inertia_), 3),
            }
        )

        if best_score is None or score > best_score:
            best_score = score
            best_model = model
            best_labels = labels

    evaluation_df = pd.DataFrame(evaluation_rows).sort_values(
        by="Silhouette",
        ascending=False,
    ).reset_index(drop=True)

    assignments = cluster_df.copy()
    assignments["cluster_raw"] = best_labels

    cluster_order = (
        assignments.groupby("cluster_raw", as_index=False)[TARGET_COLUMN]
        .mean()
        .sort_values(TARGET_COLUMN, ascending=False)
        .reset_index(drop=True)
    )
    cluster_mapping = {
        raw_id: f"Кластер {index + 1}"
        for index, raw_id in enumerate(cluster_order["cluster_raw"])
    }
    assignments["Кластер"] = assignments["cluster_raw"].map(cluster_mapping)

    summary_df = (
        assignments.groupby("Кластер", as_index=False)
        .agg(
            **{
                "Размер кластера": ("year", "count"),
                "Годы": ("year", lambda years: ", ".join(str(int(year)) for year in sorted(years))),
                "Средняя безработица, %": (TARGET_COLUMN, "mean"),
                "Средняя зарплата, руб.": ("average_salary", "mean"),
                "Инфляция, %": ("inflation", "mean"),
                "Платежеспособность, %": ("real_income_index", "mean"),
                "Темп роста ВВП, %": ("gdp_growth", "mean"),
                "Ключевая ставка, %": ("key_rate", "mean"),
            }
        )
        .sort_values("Кластер")
        .reset_index(drop=True)
    )

    unemployment_mean = float(summary_df["Средняя безработица, %"].mean())
    salary_mean = float(summary_df["Средняя зарплата, руб."].mean())
    summary_df["Профиль"] = summary_df.apply(
        lambda row: _cluster_profile(row, unemployment_mean, salary_mean),
        axis=1,
    )

    assignments_display = assignments.rename(
        columns={
            "year": "Год",
            TARGET_COLUMN: "Уровень безработицы, %",
            "average_salary": "Средняя зарплата, руб.",
            "inflation": "Инфляция, %",
            "real_income_index": "Платежеспособность, %",
            "gdp_growth": "Темп роста ВВП, %",
            "key_rate": "Ключевая ставка, %",
        }
    ).drop(columns=["cluster_raw"])

    centroids = pd.DataFrame(
        scaler.inverse_transform(best_model.cluster_centers_),
        columns=feature_columns,
    )
    centroids["cluster_raw"] = range(len(centroids))
    centroids["Кластер"] = centroids["cluster_raw"].map(cluster_mapping)
    centroid_df = centroids.drop(columns=["cluster_raw"]).sort_values("Кластер").reset_index(drop=True)

    return {
        "evaluation": evaluation_df,
        "assignments": assignments_display.round(3),
        "summary": summary_df.round(3),
        "centroids": centroid_df.round(3),
        "best_cluster_count": int(len(summary_df)),
        "best_silhouette": float(best_score),
    }


def backtest_forecast_methods(series, holdout=2):
    series = pd.Series(series).astype(float)

    if len(series) <= holdout + 2:
        return pd.DataFrame(
            [
                {
                    "Метод": "Недостаточно наблюдений",
                    "MAE": np.nan,
                    "RMSE": np.nan,
                    "Комментарий": "Для бэктеста требуется более длинный ряд.",
                }
            ]
        )

    train = series.iloc[:-holdout]
    test = series.iloc[-holdout:]
    rows = []

    methods = [
        "Экспоненциальное сглаживание",
        "ARIMA (1,1,1)",
    ]

    for method in methods:
        try:
            forecast_result = build_forecast(series=train, steps=holdout, method=method)
            prediction = forecast_result["forecast"]["Прогноз"].astype(float)

            rows.append(
                {
                    "Метод": method,
                    "MAE": round(float(mean_absolute_error(test, prediction)), 3),
                    "RMSE": round(float(mean_squared_error(test, prediction) ** 0.5), 3),
                    "Комментарий": "Оценка по двум последним наблюдениям годового ряда.",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "Метод": method,
                    "MAE": np.nan,
                    "RMSE": np.nan,
                    "Комментарий": f"Не удалось построить бэктест: {exc}",
                }
            )

    return pd.DataFrame(rows).sort_values(by="RMSE", na_position="last").reset_index(drop=True)


def build_forecast(series, steps, method):
    series = pd.Series(series).astype(float)
    series.index = pd.Index(series.index.astype(int), name="Год")

    if method == "Экспоненциальное сглаживание":
        fitted_model = ExponentialSmoothing(series, trend="add", seasonal=None).fit()
        forecast_values = fitted_model.forecast(steps)
        fitted_values = fitted_model.fittedvalues
        residual_std = float(pd.Series(fitted_model.resid).std(ddof=1))
        horizon = np.arange(1, steps + 1, dtype=float)
        interval = 1.96 * residual_std * np.sqrt(horizon)

        lower = forecast_values.values - interval
        upper = forecast_values.values + interval

    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fitted_model = ARIMA(series, order=(1, 1, 1)).fit()
        forecast_object = fitted_model.get_forecast(steps=steps)
        forecast_values = forecast_object.predicted_mean
        conf_int = forecast_object.conf_int(alpha=0.05)
        conf_int.columns = ["Нижняя граница", "Верхняя граница"]
        fitted_values = fitted_model.get_prediction(
            start=series.index.min(),
            end=series.index.max(),
        ).predicted_mean
        lower = conf_int["Нижняя граница"].values
        upper = conf_int["Верхняя граница"].values

    future_years = np.arange(series.index.max() + 1, series.index.max() + steps + 1)

    forecast_df = pd.DataFrame(
        {
            "Год": future_years,
            "Прогноз": np.round(forecast_values.values, 3),
            "Нижняя граница": np.round(lower, 3),
            "Верхняя граница": np.round(upper, 3),
        }
    )

    history_df = pd.DataFrame(
        {
            "Год": series.index.astype(int),
            "Историческое значение": series.values,
            "Сглаженное значение": pd.Series(fitted_values, index=series.index).reindex(series.index).values,
        }
    )

    return {
        "history": history_df,
        "forecast": forecast_df,
    }
