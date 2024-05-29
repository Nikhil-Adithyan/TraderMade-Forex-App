import pandas as pd
import streamlit as st
import requests
import numpy as np
from lightweight_charts.widgets import StreamlitChart

if "currency_list" not in st.session_state:
    st.session_state.currency_list = None

st.set_page_config(
    page_title = 'Currency Converter',
    layout = 'wide'
)

st.markdown(
    """
    <style>
        footer {display: none}
        [data-testid="stHeader"] {display: none}
    </style>
    """, unsafe_allow_html = True
)

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

api_key = 'Jm8O3tsF_UWhvzPcp1ZO'

with st.container():
    from_col, amount_col, emp_col, text_col, emp_col, to_col = st.columns([0.5,0.5,0.05,0.08,0.05,0.5])
    
    with from_col:
        
        if st.session_state.currency_list == None:
            currency_json = requests.get(f'https://marketdata.tradermade.com/api/v1/live_currencies_list?api_key={api_key}').json()
            currencies = []
            for key in currency_json['available_currencies'].keys():
                currency = f'{key}' + ' ' + f'({currency_json["available_currencies"].get(key)})'
                currencies.append(currency)
            st.session_state.currency_list = currencies
            
        from_currency = st.selectbox('From', st.session_state.currency_list, index = 0, key = 'fromcurrency_selectbox')
        
    with amount_col:
        
        amount = st.number_input(f'Amount (in {from_currency[:3]})', min_value = 1, key = 'amount_numberinput')
        
    with text_col:
        
        st.image('to_icon.png')
        #st.markdown(f'<p class="to_text">TO</p>', unsafe_allow_html = True)
        
    with to_col:
        
        to_currency = st.selectbox('To', st.session_state.currency_list, index = 1, key = 'tocurrency_selectbox')
    
    st.markdown('')
    
    currency_col, conversion_col, details_col, emp_col, button_col = st.columns([0.06, 0.16, 0.26, 0.6, 0.1])
    
    with button_col:
        convert = st.button('Convert')
        
if convert:
    converted_details = requests.get(f'https://marketdata.tradermade.com/api/v1/convert?api_key={api_key}&from={from_currency[:3]}&to={to_currency[:3]}&amount={amount}').json()
    
    with currency_col:
        st.markdown(f'<p class="converted_currency">{to_currency[:3]}</p>', unsafe_allow_html = True)
        
    with conversion_col:
        converted_total = round(converted_details['total'],4)
        st.markdown(f'<p class="converted_total">{converted_total}</p>', unsafe_allow_html = True)
        
    with details_col:
        st.markdown(f'<p class="details_text">( 1 {from_currency[:3]}  =  {converted_total} {to_currency[:3]} )</p>', unsafe_allow_html = True)
    
    st.markdown('')
    
    last10_col, chart_col = st.columns([0.3,0.7])

    with last10_col:
        
        #st.markdown(f'<p class="converted_currency">1 {from_currency[:3]} to {to_currency[:3]} exchange rate last 10 days</p>', unsafe_allow_html = True)
        st.markdown(f'<p><b>1 {from_currency[:3]} to {to_currency[:3]} exchange rate last 10 days</b></p>', unsafe_allow_html = True)
        st.markdown('')
        
        api_currency = from_currency[:3] + to_currency[:3]
        historical_json = requests.get(f'https://marketdata.tradermade.com/api/v1/timeseries?currency={api_currency}&api_key={api_key}&start_date=2023-06-01&format=records').json()
        historical_df = pd.DataFrame(historical_json['quotes']).dropna().reset_index().drop('index', axis = 1)
        historical_df.date = pd.to_datetime(historical_df.date)
        historical_df = historical_df.set_index('date')
        st.dataframe(historical_df.tail(10), use_container_width = True)
    
    with chart_col:

        chart = StreamlitChart(height = 450, width = 950, volume_enabled = False)
        chart.grid(vert_enabled = True, horz_enabled = True)

        chart.layout(background_color='#131722', font_family='Trebuchet MS', font_size = 16)

        chart.candle_style(up_color='#2962ff', down_color='#e91e63',
                           border_up_color='#2962ffcb', border_down_color='#e91e63cb',
                           wick_up_color='#2962ffcb', wick_down_color='#e91e63cb')
        
        chart.watermark(f'{from_currency[:3]}/{to_currency[:3]} 1D')
                   
        #chart.volume_config(up_color='#2962ffcb', down_color='#e91e63cb')
        chart.legend(visible = True, font_family = 'Trebuchet MS', ohlc = True, percent = True)
        
        chart_df = historical_df.reset_index()
        chart.set(chart_df)
        chart.load()
        
    with st.container():
        
        st.markdown('')
        
        st.markdown(f'<p class="section_title"><b>{from_currency[:3]}/{to_currency[:3]} Historical Volatility</b> (length = 20)</p>', unsafe_allow_html = True)
        st.markdown('')
        
        hv_data_col, hv_chart_col = st.columns([0.4,0.6])
        
        with hv_data_col:
            historical_df['log_ret'] = np.log(historical_df['close'] / historical_df['close'].shift(1))
            window_size = 20
            rolling_volatility = historical_df['log_ret'].rolling(window=window_size).std()
            historical_df['hv'] = rolling_volatility * np.sqrt(365) * 100
            historical_df = historical_df.dropna()
            st.dataframe(historical_df[['close','log_ret','hv']], use_container_width = True)
        with hv_chart_col:
            st.line_chart(historical_df.hv, height = 450)
        
        st.markdown('')
        
        st.markdown(f'<p class="section_title"><b>{from_currency[:3]}/{to_currency[:3]} Pivot Points</b></p>', unsafe_allow_html = True)
        st.markdown('')
        
        pivot_data_col, pivot_chart_col = st.columns([0.4,0.6])
        
        with pivot_data_col:
            historical_df['pivot'] = (historical_df['high'].shift(1) + historical_df['low'].shift(1) + historical_df['close'].shift(1)) / 3

            historical_df['r1'] = 2 * historical_df['pivot'] - historical_df['low'].shift(1)
            historical_df['s1'] = 2 * historical_df['pivot'] - historical_df['high'].shift(1)

            historical_df['r2'] = historical_df['pivot'] + (historical_df['high'].shift(1) - historical_df['low'].shift(1))
            historical_df['s2'] = historical_df['pivot'] - (historical_df['high'].shift(1) - historical_df['low'].shift(1))

            historical_df['r3'] = historical_df['high'].shift(1) + 2 * (historical_df['pivot'] - historical_df['low'].shift(1))
            historical_df['s3'] = historical_df['low'].shift(1) - 2 * (historical_df['high'].shift(1) - historical_df['pivot'])
            
            historical_df = historical_df.dropna()
            st.dataframe(historical_df.iloc[:,-6:], use_container_width = True)

            r1,r2,r3 = historical_df.r1[-1], historical_df.r2[-1], historical_df.r3[-1]
            s1,s2,s3 = historical_df.s1[-1], historical_df.s2[-1], historical_df.s3[-1]
            
        with pivot_chart_col:     
            
            chart = StreamlitChart(height = 450, width = 800, volume_enabled = False)
            chart.grid(vert_enabled = True, horz_enabled = True)

            chart.layout(background_color='#131722', font_family='Trebuchet MS', font_size = 16)

            chart.candle_style(up_color='#2962ff', down_color='#e91e63',
                               border_up_color='#2962ffcb', border_down_color='#e91e63cb',
                               wick_up_color='#2962ffcb', wick_down_color='#e91e63cb')
            
            chart.horizontal_line(price = r1, color = 'darkorange', text = f'R1', style = 'dotted')
            chart.horizontal_line(price = r2, color = 'darkorange', text = f'R2', style = 'dotted')
            chart.horizontal_line(price = r3, color = 'darkorange', text = f'R3', style = 'dotted')
            chart.horizontal_line(price = s1, color = 'darkorange', text = f'S1', style = 'dotted')
            chart.horizontal_line(price = s2, color = 'darkorange', text = f'S2', style = 'dotted')
            chart.horizontal_line(price = s3, color = 'darkorange', text = f'S3', style = 'dotted')

            #chart.volume_config(up_color='#2962ffcb', down_color='#e91e63cb')
            chart.legend(visible = True, font_family = 'Trebuchet MS', ohlc = True, percent = True)
                        
            chart_df = historical_df.reset_index()
            chart.set(chart_df)
            chart.load()
        