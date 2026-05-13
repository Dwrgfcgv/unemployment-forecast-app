import plotly.express as px
import plotly.graph_objects as go

from src.constants import PLOT_COLORS, SHORT_COLUMN_NAMES


def apply_plot_style(fig, title, y_title):
    grid_color = "rgba(148, 163, 184, 0.18)"
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        title_font=dict(size=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=16, r=16, t=76, b=44),
        font=dict(family="Manrope, Segoe UI, sans-serif", size=13),
        legend_title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
        xaxis=dict(
            title="Год",
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            automargin=True,
        ),
        yaxis=dict(
            title=y_title,
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            automargin=True,
        ),
    )
    return fig


def build_heatmap_figure(matrix, title):
    display_matrix = matrix.rename(index=SHORT_COLUMN_NAMES, columns=SHORT_COLUMN_NAMES)
    x_labels = list(display_matrix.columns)
    y_labels = list(display_matrix.index)
    x_tick_labels = [
        {
            "Безработица": "Безработица",
            "Зарплата": "Зарплата",
            "Инфляция": "Инфляция",
            "Платежеспособность": "Платежесп.",
            "Рост ВВП": "Рост ВВП",
            "Ключевая ставка": "Ключ. ставка",
        }.get(label, label)
        for label in x_labels
    ]
    text_values = [[f"{value:.2f}" for value in row] for row in display_matrix.values]

    fig = go.Figure(
        data=go.Heatmap(
            z=display_matrix.values,
            x=x_labels,
            y=y_labels,
            zmin=-1,
            zmax=1,
            xgap=1,
            ygap=1,
            text=text_values,
            texttemplate="%{text}",
            textfont={"size": 12},
            colorscale="RdBu_r",
            colorbar=dict(title="", thickness=14, len=0.82),
            hovertemplate="%{y} / %{x}: %{z:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        title_font=dict(size=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, Segoe UI, sans-serif", size=13),
        height=680,
        margin=dict(l=16, r=16, t=78, b=120),
    )
    fig.update_xaxes(
        title="",
        side="bottom",
        tickmode="array",
        tickvals=x_labels,
        ticktext=x_tick_labels,
        tickangle=-32,
        tickfont=dict(size=11),
        automargin=True,
    )
    fig.update_yaxes(title="", tickfont=dict(size=12), autorange="reversed", automargin=True)
    return fig


def build_factor_importance_figure(beta_df):
    figure_df = beta_df.copy()
    figure_df["Цвет"] = figure_df["Стандартизированный beta"].apply(
        lambda value: PLOT_COLORS["gold"] if value >= 0 else PLOT_COLORS["blue"]
    )

    fig = px.bar(
        figure_df,
        x="Стандартизированный beta",
        y="Показатель",
        orientation="h",
        color="Цвет",
        color_discrete_map="identity",
        text="Стандартизированный beta",
    )
    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        hovertemplate="%{y}: %{x:.3f}<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    fig.update_yaxes(categoryorder="array", categoryarray=figure_df["Показатель"][::-1])
    apply_plot_style(fig, "Стандартизированное влияние факторов", "Фактор")
    fig.update_xaxes(title="Стандартизированный beta")
    return fig


def build_influence_figure(influence_df):
    plot_df = influence_df.copy()
    plot_df["Цвет"] = plot_df["Статус"].map(
        {
            "Повышенное влияние": PLOT_COLORS["danger"],
            "Умеренное влияние": PLOT_COLORS["gold"],
            "Обычное влияние": PLOT_COLORS["teal"],
        }
    )
    plot_df["Год"] = plot_df["Год"].astype(str)

    fig = px.bar(
        plot_df,
        x="Год",
        y="Cook's distance",
        color="Статус",
        color_discrete_map={
            "Повышенное влияние": PLOT_COLORS["danger"],
            "Умеренное влияние": PLOT_COLORS["gold"],
            "Обычное влияние": PLOT_COLORS["teal"],
        },
        text="Cook's distance",
    )
    fig.update_traces(
        texttemplate="%{text:.3f}",
        textposition="outside",
        hovertemplate="Год: %{x}<br>Cook's distance: %{y:.3f}<extra></extra>",
    )
    apply_plot_style(fig, "Влияние отдельных лет на регрессию", "Cook's distance")
    fig.update_xaxes(title="Год")
    return fig
