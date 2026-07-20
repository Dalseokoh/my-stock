import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="글로벌 주식 대시보드", page_icon="📈", layout="wide")

# ------------------------------
# 종목 리스트 정의
# ------------------------------
INDEX_TICKERS = {
    "S&P 500": "^GSPC",
    "다우존스": "^DJI",
    "나스닥": "^IXIC",
    "코스피": "^KS11",
    "코스닥": "^KQ11",
    "닛케이225": "^N225",
    "항셍지수": "^HSI",
    "상해종합": "000001.SS",
    "DAX(독일)": "^GDAXI",
    "FTSE100(영국)": "^FTSE",
}

STOCK_TICKERS = {
    "애플": "AAPL",
    "마이크로소프트": "MSFT",
    "엔비디아": "NVDA",
    "아마존": "AMZN",
    "구글(알파벳)": "GOOGL",
    "메타": "META",
    "테슬라": "TSLA",
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "TSMC": "TSM",
}

ALL_TICKERS = {**INDEX_TICKERS, **STOCK_TICKERS}

# ------------------------------
# 사이드바 - 옵션 선택
# ------------------------------
st.sidebar.title("⚙️ 옵션 설정")

category = st.sidebar.radio("카테고리 선택", ["주요 지수", "글로벌 대형주", "전체"])

if category == "주요 지수":
    ticker_pool = INDEX_TICKERS
elif category == "글로벌 대형주":
    ticker_pool = STOCK_TICKERS
else:
    ticker_pool = ALL_TICKERS

selected_names = st.sidebar.multiselect(
    "종목 선택",
    options=list(ticker_pool.keys()),
    default=list(ticker_pool.keys())[:5]
)

period_options = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
    "YTD": "ytd",
}
period_label = st.sidebar.selectbox("조회 기간", list(period_options.keys()), index=2)
period = period_options[period_label]

interval_options = {
    "1일": "1d",
    "1주": "1wk",
    "1개월": "1mo",
}
interval_label = st.sidebar.selectbox("데이터 간격", list(interval_options.keys()), index=0)
interval = interval_options[interval_label]

normalize = st.sidebar.checkbox("수익률(%) 기준으로 비교", value=True)

st.sidebar.markdown("---")
st.sidebar.caption("데이터 출처: Yahoo Finance (yfinance)")

# ------------------------------
# 메인 타이틀
# ------------------------------
st.title("📈 글로벌 주요 주식 대시보드")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if not selected_names:
    st.warning("사이드바에서 종목을 하나 이상 선택해주세요.")
    st.stop()

selected_tickers = {name: ticker_pool[name] for name in selected_names}

# ------------------------------
# 데이터 로딩 함수
# ------------------------------
@st.cache_data(ttl=600)
def load_data(tickers_dict, period, interval):
    data = {}
    for name, ticker in tickers_dict.items():
        try:
            df = yf.Ticker(ticker).history(period=period, interval=interval)
            if not df.empty:
                data[name] = df
        except Exception as e:
            st.error(f"{name} 데이터를 불러오는 중 오류 발생: {e}")
    return data

with st.spinner("데이터를 불러오는 중입니다..."):
    stock_data = load_data(selected_tickers, period, interval)

if not stock_data:
    st.error("선택한 종목의 데이터를 불러오지 못했습니다.")
    st.stop()

# ------------------------------
# 요약 지표 카드
# ------------------------------
st.subheader("📊 요약 지표")
cols = st.columns(len(stock_data))

for idx, (name, df) in enumerate(stock_data.items()):
    last_price = df["Close"].iloc[-1]
    prev_price = df["Close"].iloc[-2] if len(df) > 1 else last_price
    change = last_price - prev_price
    pct_change = (change / prev_price) * 100 if prev_price != 0 else 0

    with cols[idx]:
        st.metric(
            label=name,
            value=f"{last_price:,.2f}",
            delta=f"{change:,.2f} ({pct_change:.2f}%)"
        )

st.markdown("---")

# ------------------------------
# 가격 비교 차트 (Plotly)
# ------------------------------
st.subheader("💹 가격 추이 비교")

fig = go.Figure()

for name, df in stock_data.items():
    if normalize:
        base = df["Close"].iloc[0]
        y_values = (df["Close"] / base - 1) * 100
        y_title = "수익률 (%)"
    else:
        y_values = df["Close"]
        y_title = "가격"

    fig.add_trace(go.Scatter(
        x=df.index,
        y=y_values,
        mode="lines",
        name=name,
        hovertemplate="%{y:.2f}<extra>" + name + "</extra>"
    ))

fig.update_layout(
    height=550,
    hovermode="x unified",
    yaxis_title=y_title,
    xaxis_title="날짜",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=30, b=10),
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ------------------------------
# 개별 종목 캔들스틱 차트
# ------------------------------
st.subheader("🕯️ 개별 종목 캔들스틱 차트")

selected_candle = st.selectbox("종목 선택 (캔들스틱)", list(stock_data.keys()))
candle_df = stock_data[selected_candle]

fig_candle = go.Figure(data=[go.Candlestick(
    x=candle_df.index,
    open=candle_df["Open"],
    high=candle_df["High"],
    low=candle_df["Low"],
    close=candle_df["Close"],
    name=selected_candle
)])

# 거래량 서브플롯을 위한 간단한 바 차트 추가 (보조축)
fig_candle.add_trace(go.Bar(
    x=candle_df.index,
    y=candle_df["Volume"],
    name="거래량",
    yaxis="y2",
    opacity=0.3,
    marker_color="gray"
))

fig_candle.update_layout(
    height=600,
    xaxis_rangeslider_visible=False,
    yaxis=dict(title="가격"),
    yaxis2=dict(title="거래량", overlaying="y", side="right", showgrid=False),
    margin=dict(l=10, r=10, t=30, b=10),
)

st.plotly_chart(fig_candle, use_container_width=True)

st.markdown("---")

# ------------------------------
# 상세 데이터 테이블
# ------------------------------
st.subheader("📋 상세 데이터")

table_rows = []
for name, df in stock_data.items():
    last_price = df["Close"].iloc[-1]
    prev_price = df["Close"].iloc[-2] if len(df) > 1 else last_price
    change = last_price - prev_price
    pct_change = (change / prev_price) * 100 if prev_price != 0 else 0
    period_return = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100

    table_rows.append({
        "종목": name,
        "티커": selected_tickers[name],
        "현재가": round(last_price, 2),
        "전일대비": round(change, 2),
        "등락률(%)": round(pct_change, 2),
        "기간수익률(%)": round(period_return, 2),
        "최고가": round(df["High"].max(), 2),
        "최저가": round(df["Low"].min(), 2),
    })

summary_df = pd.DataFrame(table_rows)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("⚠️ 본 대시보드는 정보 제공 목적이며, 투자 판단의 근거로 사용될 수 없습니다.")
