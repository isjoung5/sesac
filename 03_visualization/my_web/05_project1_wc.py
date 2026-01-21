from bs4 import BeautifulSoup
import requests
import json

import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from wordcloud import WordCloud, STOPWORDS
from PIL import Image 

import streamlit as st 

from dotenv import load_dotenv
import os 

# stopwords 설정 -------------------------------------------------------------------------
# 1. 파일에서 스톱워드 읽어오기
# with open('../data/stopwords.txt', 'r', encoding='utf-8') as f:
with open('data/stopwords.txt', 'r', encoding='utf-8') as f:
    # 줄바꿈 문자(\n) 제거 및 set으로 변환
    custom_stopwords = set(line.strip() for line in f)

# 2. 기본 STOPWORDS와 결합 (필요시)
final_stopwords = set(STOPWORDS)
final_stopwords.update(custom_stopwords)

# load_dotenv()
# client_id = os.getenv("NAVER_CLIENT_ID")
# client_secret = os.getenv("NAVER_CLIENT_SECRET")
# NAVER_CLIENT_ID=rM06oSKgxOg3ZP9Dtf8Z
# NAVER_CLIENT_SECRET=RE2JjUXd3_
client_id = "rM06oSKgxOg3ZP9Dtf8Z"
client_secret = "RE2JjUXd3_"

# 함수 설정 -------------------------------------------------------------------------
# 네이버 검색 API를 활용한 뉴스 검색 결과를 반환해주는 함수
def get_requests(query, display, start):
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret":client_secret}
    params = {"query": query, "display": display, "start": start}
    url = "https://openapi.naver.com/v1/search/news.json"

    response = requests.get(url, params=params, headers=headers)
    news_json = json.loads(response.text)

    return news_json["items"]

# 워드 클라우드 시각화 함수
# 문자열 텍스트, 배경 이미지, 최대 출력 단어수, empty 공간
def wc_chart(corpus, back_mask, max_words, emp):
    if back_mask == "타원":
        img = Image.open("data/background_1.png")
    elif back_mask == "말풍선":
        img = Image.open("data/background_2.png")
    elif back_mask == "하트":
        img = Image.open("data/background_3.png")
    else:
        img = Image.open("data/background_0.png")

    # 워드클라우드에 적용하기 위해 이미지를 배열로 변환
    my_mask = np.array(img)

    wc = WordCloud(
        # font_path="C:/Windows/Fonts/malgun.ttf",
        font_path="data/malgun.ttf",
        background_color="white",
        max_words=max_words,
        random_state=99,
        stopwords=final_stopwords,
        mask=my_mask
    )

    wc.generate(corpus) # corpus: 말주머니

    fig = plt.figure(figsize=(10, 10))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(fig) # streamlit으로 그림을 화면에 출력
    emp.success(":orange[**워드클라우드 이미지 생성 완료**]")

# 센션 설정 -------------------------------------------------------------------------
if "client_id" not in st.session_state:
    st.session_state["client_id"] = client_id

if "client_secret" not in st.session_state:
    st.session_state["client_secret"] = client_secret

# # 사이드바 설정 -------------------------------------------------------------------------
# with st.sidebar.form(key="form1", clear_on_submit=False):
#     st.header("네이버 API 설정")
#     client_id = st.text_input("Client ID:", value=st.session_state["client_id"])
#     client_secret = st.text_input("client Secret:", value=st.session_state["client_secret"], type="password")

#     if st.form_submit_button(label="OK"):
#         st.session_state["client_id"] = client_id
#         st.session_state["client_secret"] = client_secret
#         st.write("설정 완료")

# 메인화면 설정 -------------------------------------------------------------------------
chart_emp = st.empty()

try:
    with st.form(key="Search", clear_on_submit=False):
        # search_keyword = st.selectbox("키워드:", ["정치", "사회", "국제", "연애", "IT", "문화"]) # 키워드 선택
        search_keyword = st.text_input("키워드:", value="노인 노령 고령 요양 돌봄 케어") # 키워드 입력
        data_amount = st.slider("분량(1당 100개):", min_value=1, max_value=10, value=1, step=1) # 수집분량
        back_mask = st.radio("워드클라우드 출력 형태:", ["기본", "타원", "말풍선", "하트"], horizontal=True) # 워드클라우드 배경 마스크

        if st.form_submit_button("출력"):
            chart_emp.info(":red[데이터 가져오는 중 ...]")

            # 데이터 수집 -----------------------------------------------------
            corpus = "" # 수집된 문자열이 담길 변수 선언
            items = [] # 뉴스 항목이 담길 리스트 선언

            # 입력 받은 수집 분량(data_amount) 만큼 반복해서 뉴스 기사 정보 가져오기
            for i in range(data_amount):
                items.extend(get_requests(search_keyword, 100, 100*i+1))

            for item in items:
                if "n.news.naver" in item["link"]:
                    news_url = item["link"]
                    response = requests.get(news_url)
                    soup = BeautifulSoup(response.text, "lxml")
                    body_area = soup.select_one("#dic_area")
                    if body_area: # 본문이 있는지 여부, 없는 경우도 있을 수 있음
                        news_text_list = body_area.find_all(string=True, recursive=False)
                        news_text = "".join(text.strip() for text in news_text_list) # 기사 붙이기
                        corpus += news_text + " " # 본문의 텍스트를 corpus에 계속 추가하기

            st.write(f"수집된 corpus 확인: {len(corpus)}")

            # 워드 클라우드 생성 -----------------------------------------------------
            if len(corpus) >= 100:
                chart_emp.info(":red[이미지 생성중 ...]")
                wc_chart(corpus, back_mask, 70, chart_emp)
            else:
                chart_emp.error(":red[워드클라우드를 생성하기에 데이터가 충분하지 않습니다.]")

except Exception as err:
    st.write(err)
    chart_emp.error("ID와 Secret를 입력해주세요.")
