import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import date, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="글로벌 주요 주식 대시보드", page_icon="📈", layout="wide")

st.title("📈 글로벌 주요 주식 대시보드")
st.write("주요 글로벌 종목의 주가 흐름을 확인해보세요.")

# 글로벌 주요 종목 리스트 (티커: 표시 이름)
stock_list = {
    "AAPL": "애플 (Apple)",
    "MSFT": "마이크로소프트 (Microsoft)",
    "GOOGL": "알파벳 (Google)",
    "AMZN": "아마존 (Amazon)",
    "NVDA": "엔비디아 (NVIDIA)",
    "TSLA": "테슬라 (Tesla)",
    "META": "메타 (Meta)",
    "005930.KS": "삼성전자 (Samsung Electronics)",
    "000660.KS": "SK하이닉스 (SK Hynix)",
    "7203.T": "도요타 (Toyota)",
    "9984.T": "소프트뱅크그룹 (SoftBank Group)",
    "0700.HK": "텐센트 (Tencent)",
    "BABA": "알리바바 (Alibaba)",
}

# 사이드바 설정
st.sidebar.header("설정")

selected_names = st.sidebar.multiselect(
    "종목 선택 (여러 개 선택 가능)",
    options=list(stock_list.values()),
    default=["애플 (Apple)", "엔비디아 (NVIDIA)", "삼성전자 (Samsung Electronics)"]
)

period_options = {
    "1개월": 30,
    "3개월": 90,
    "6개월": 180,
    "1년": 365,
    "2년": 730,
}
selected_period = st.sidebar.selectbox("조회 기간", list(period_options.keys()), index=2)

end_date = date.today()
start_date = end_date - timedelta(days=period_options[selected_period])

# 이름 -> 티커 역매핑
name_to_ticker = {v: k for k, v in stock_list.items()}
selected_tickers = [name_to_ticker[name] for name in selected_names]

if not selected_tickers:
    st.info("왼쪽 사이드바에서 종목을 하나 이상 선택해주세요.")
else:
    # 데이터 가져오기
    with st.spinner("주가 데이터를 불러오는 중..."):
        data = yf.download(selected_tickers, start=start_date, end=end_date, group_by="ticker", auto_adjust=True)

    # 현재가 요약 카드
    st.subheader("현재 주가 요약")
    cols = st.columns(len(selected_tickers))

    for i, ticker in enumerate(selected_tickers):
        try:
            if len(selected_tickers) == 1:
                close_series = data["Close"].dropna()
            else:
                close_series = data[ticker]["Close"].dropna()

            last_price = close_series.iloc[-1]
            prev_price = close_series.iloc[-2] if len(close_series) > 1 else last_price
            change = last_price - prev_price
            change_pct = (change / prev_price) * 100 if prev_price != 0 else 0

            with cols[i]:
                st.metric(
                    label=stock_list[ticker],
                    value=f"{last_price:,.2f}",
                    delta=f"{change:,.2f} ({change_pct:,.2f}%)"
                )
        except Exception:
            with cols[i]:
                st.write(f"{stock_list[ticker]}: 데이터 없음")

    # 정규화 비교 차트 (시작점 100 기준)
    st.subheader("주가 추이 비교 (시작 시점 = 100 기준)")

    fig = go.Figure()

    for ticker in selected_tickers:
        try:
            if len(selected_tickers) == 1:
                close_series = data["Close"].dropna()
            else:
                close_series = data[ticker]["Close"].dropna()

            normalized = (close_series / close_series.iloc[0]) * 100

            fig.add_trace(go.Scatter(
                x=normalized.index,
                y=normalized.values,
                mode="lines",
                name=stock_list[ticker]
            ))
        except Exception:
            continue

    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="상대 지수 (시작=100)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # 개별 종목 상세 차트
    st.subheader("개별 종목 상세 차트")
    detail_name = st.selectbox("상세히 볼 종목 선택", selected_names)
    detail_ticker = name_to_ticker[detail_name]

    try:
        if len(selected_tickers) == 1:
            detail_df = data.dropna()
        else:
            detail_df = data[detail_ticker].dropna()

        candle_fig = go.Figure(data=[go.Candlestick(
            x=detail_df.index,
            open=detail_df["Open"],
            high=detail_df["High"],
            low=detail_df["Low"],
            close=detail_df["Close"],
            name=detail_name
        )])

        candle_fig.update_layout(
            xaxis_title="날짜",
            yaxis_title="가격",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(candle_fig, use_container_width=True)
    except Exception:
        st.write("상세 차트를 불러올 수 없습니다.")

st.caption("데이터 출처: Yahoo Finance (yfinance)")
