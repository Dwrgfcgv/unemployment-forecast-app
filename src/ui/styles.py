import streamlit as st


def inject_global_styles():
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap');

        :root {
            --brand: var(--primary-color, #2563eb);
            --brand-strong: color-mix(in srgb, var(--brand) 82%, #0f172a 18%);
            --surface-faint: color-mix(in srgb, currentColor 6%, transparent);
            --text-soft: color-mix(in srgb, currentColor 68%, transparent);
            --card-bg: linear-gradient(
                150deg,
                color-mix(in srgb, currentColor 6%, transparent) 0%,
                color-mix(in srgb, currentColor 3.5%, transparent) 100%
            );
            --card-bg-strong: linear-gradient(
                145deg,
                color-mix(in srgb, currentColor 7.5%, transparent) 0%,
                color-mix(in srgb, currentColor 4.5%, transparent) 100%
            );
            --card-glow: 0 22px 48px rgba(15, 23, 42, 0.14), 0 0 34px color-mix(in srgb, var(--brand) 10%, transparent);
            --card-glow-strong: 0 28px 58px rgba(15, 23, 42, 0.18), 0 0 44px color-mix(in srgb, var(--brand) 16%, transparent);
            --success: color-mix(in srgb, #22c55e 18%, transparent);
            --warning: color-mix(in srgb, #f59e0b 18%, transparent);
            --danger: color-mix(in srgb, #ef4444 18%, transparent);
            --radius-xl: 30px;
            --radius-lg: 24px;
            --radius-md: 18px;
        }

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main {
            font-family: "Manrope", "Segoe UI", sans-serif;
        }

        [data-testid="stAppViewContainer"] > .main {
            background:
                radial-gradient(circle at 0% 0%, color-mix(in srgb, var(--brand) 9%, transparent) 0%, transparent 24%),
                radial-gradient(circle at 100% 0%, color-mix(in srgb, #0ea5a3 8%, transparent) 0%, transparent 20%);
        }

        [data-testid="stSidebar"] {
            background: color-mix(in srgb, currentColor 4%, transparent);
            backdrop-filter: blur(18px);
            border-right: none;
        }

        .block-container {
            padding-top: 3.7rem;
            padding-bottom: 4.2rem;
            max-width: 1360px;
        }

        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            min-height: 3.2rem;
            border: none;
            border-radius: 16px;
            background: linear-gradient(135deg, var(--brand) 0%, var(--brand-strong) 100%);
            color: #ffffff !important;
            font-weight: 800;
            box-shadow: none;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            color: #ffffff !important;
            filter: brightness(1.05);
        }

        .stButton > button p,
        .stButton > button span,
        .stButton > button div,
        .stDownloadButton > button p,
        .stDownloadButton > button span,
        .stDownloadButton > button div {
            color: #ffffff !important;
        }

        input[type="radio"],
        input[type="checkbox"] {
            accent-color: var(--brand-strong);
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div {
            background: var(--surface-faint);
            border: none;
            border-radius: 16px;
            backdrop-filter: blur(12px);
        }

        .hero-shell {
            background: var(--card-bg-strong);
            border-radius: var(--radius-xl);
            padding: 34px 36px 30px;
            margin-bottom: 1.4rem;
            position: relative;
            overflow: hidden;
            box-shadow: var(--card-glow-strong);
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            width: 320px;
            height: 320px;
            right: -90px;
            top: -90px;
            background: radial-gradient(circle, color-mix(in srgb, var(--brand) 22%, transparent) 0%, transparent 68%);
            pointer-events: none;
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border-radius: 999px;
            background: color-mix(in srgb, var(--brand) 16%, transparent);
            font-size: 0.86rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: clamp(2.5rem, 4.8vw, 5rem);
            line-height: 1.04;
            font-weight: 800;
            margin: 0;
            max-width: 1120px;
        }

        .hero-text {
            font-size: 1.03rem;
            line-height: 1.72;
            color: var(--text-soft);
            max-width: 980px;
            margin-top: 1rem;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            margin-top: 1.35rem;
        }

        .chip {
            padding: 0.62rem 0.92rem;
            border-radius: 999px;
            background: color-mix(in srgb, var(--brand) 10%, transparent);
            font-size: 0.9rem;
            font-weight: 700;
        }

        .metric-card,
        .section-card {
            display: flex;
            flex-direction: column;
            background: var(--card-bg);
            border-radius: var(--radius-lg);
            position: relative;
            overflow: hidden;
            box-shadow: var(--card-glow);
            isolation: isolate;
        }

        .metric-card::before,
        .section-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(135deg, color-mix(in srgb, #ffffff 12%, transparent) 0%, transparent 28%),
                radial-gradient(circle at 88% 10%, color-mix(in srgb, var(--brand) 16%, transparent) 0%, transparent 36%);
            pointer-events: none;
            z-index: -1;
        }

        .metric-card::after,
        .section-card::after {
            content: "";
            position: absolute;
            left: 18px;
            right: 18px;
            top: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, color-mix(in srgb, var(--brand) 35%, transparent) 50%, transparent 100%);
            pointer-events: none;
        }

        .metric-card {
            justify-content: space-between;
            min-height: 14.2rem;
            padding: 1.4rem 1.45rem 1.25rem;
        }

        .metric-label {
            min-height: 3.5rem;
            display: flex;
            align-items: flex-start;
            color: var(--text-soft);
            font-size: 0.92rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            margin-bottom: 0.35rem;
        }

        .metric-value {
            font-size: clamp(2rem, 3vw, 3.2rem);
            font-weight: 800;
            line-height: 1.02;
            margin-bottom: 0.55rem;
        }

        .metric-caption {
            min-height: 4.4rem;
            color: var(--text-soft);
            font-size: 0.95rem;
            line-height: 1.46;
        }

        .section-card {
            padding: 1.45rem 1.55rem;
            margin-bottom: 1.2rem;
            height: 100%;
        }

        .section-card h3 {
            margin: 0 0 0.6rem;
            font-size: 1.1rem;
        }

        .section-copy {
            color: var(--text-soft);
            line-height: 1.68;
        }

        .status-box {
            border-radius: 20px;
            padding: 1rem 1.15rem;
            margin-bottom: 1rem;
            line-height: 1.6;
            box-shadow: 0 18px 34px rgba(0, 0, 0, 0.2);
        }

        .status-good {
            background: var(--success);
        }

        .status-warn {
            background: var(--warning);
        }

        .status-error {
            background: var(--danger);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.6rem;
            padding: 0.8rem;
            background: var(--card-bg);
            border-radius: 26px;
            margin-top: 1.1rem;
            margin-bottom: 1.9rem;
            box-shadow: var(--card-glow);
        }

        .stTabs [data-baseweb="tab-highlight"] {
            display: none !important;
        }

        .stTabs [data-baseweb="tab"] {
            min-height: 3.35rem;
            padding: 0.62rem 1.12rem;
            border-radius: 999px;
            font-weight: 800;
            color: inherit;
            opacity: 0.72;
            background: transparent;
            border: none;
        }

        .stTabs [data-baseweb="tab"]:hover {
            opacity: 1;
            background: var(--surface-faint);
        }

        .stTabs [aria-selected="true"] {
            opacity: 1;
            color: #ffffff !important;
            background: linear-gradient(135deg, var(--brand) 0%, var(--brand-strong) 100%) !important;
        }

        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span,
        .stTabs [aria-selected="true"] div {
            color: #ffffff !important;
        }

        [data-testid="stMetric"] {
            background: var(--card-bg);
            border: none;
            border-radius: 20px;
            box-shadow: var(--card-glow);
            padding: 0.95rem 1rem;
            min-height: 8rem;
        }

        [data-testid="stMetricLabel"] {
            font-weight: 800;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        [data-testid="stDataFrameResizable"],
        [data-testid="stDataFrameGlideDataEditor"] {
            border: none !important;
            border-radius: 20px !important;
            box-shadow: 0 18px 38px rgba(0, 0, 0, 0.26), 0 0 26px rgba(63, 131, 248, 0.08) !important;
            overflow: hidden !important;
        }

        [data-testid="stElementToolbar"] {
            border-radius: 999px !important;
            background: transparent !important;
            box-shadow: none !important;
            backdrop-filter: none;
        }

        button[kind="elementToolbar"],
        button[data-testid="stBaseButton-elementToolbar"] {
            color: inherit !important;
            background: transparent !important;
            border: none !important;
            min-height: unset !important;
            padding: 0.34rem !important;
        }

        button[kind="elementToolbar"]:hover,
        button[kind="elementToolbar"]:focus-visible,
        button[data-testid="stBaseButton-elementToolbar"]:hover,
        button[data-testid="stBaseButton-elementToolbar"]:focus-visible {
            background: color-mix(in srgb, currentColor 10%, transparent) !important;
            color: inherit !important;
            box-shadow: none !important;
        }

        .js-plotly-plot .modebar {
            background: transparent !important;
            border-radius: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
            backdrop-filter: none;
        }

        .js-plotly-plot .modebar-btn {
            color: inherit !important;
            background: transparent !important;
            border-radius: 9px !important;
        }

        .js-plotly-plot .modebar-btn:hover,
        .js-plotly-plot .modebar-btn:focus-visible {
            background: color-mix(in srgb, currentColor 10%, transparent) !important;
        }

        [data-testid="stStatusWidget"] {
            border-radius: 20px;
            border: none;
            background: var(--card-bg);
            box-shadow: var(--card-glow);
        }

        :not(pre) > code {
            padding: 0.15rem 0.45rem;
            border-radius: 9px;
            background: var(--surface-faint);
        }

        .section-divider {
            margin: 2rem 0 1.35rem;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, color-mix(in srgb, currentColor 18%, transparent) 12%, color-mix(in srgb, currentColor 18%, transparent) 88%, transparent 100%);
        }

        .section-gap {
            height: 1.7rem;
        }

        @media (max-width: 1100px) {
            .block-container {
                padding-top: 2.8rem;
            }

            .hero-shell {
                padding: 28px 24px 24px;
            }

            .hero-title {
                max-width: 100%;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
