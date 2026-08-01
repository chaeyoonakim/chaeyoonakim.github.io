---
layout: post
type: reflection
title: "Survey data analysis for free-text responses"
date: 2026-07-03
categories: [자연어, 데이터과학]
tags: [python, nltk, text-preprocessing, contractions, stopwords, stemming, lemmatization]
---
24년 초반으로 기억하고 있다. 커밋 히스토리는 그 해 가을이더라. 

지난 플젝 톺아보기 시작은 한달 전 동기에게 받은 짧은 메세지로부터였다. 그 당시 우리가 같은 팀이었을 때 내가 스탭 서베이 결과를 가지고 감정 분석을 했던 내용을 동기가 기억하고 있었다. 새로 통합한지 얼마 안된 조직에서 팀 어웨이데이를 앞두고 일종의 온도 체크 방식으로 진행한 사전 설문조사가 있었다. 동기가 내게 묻고자 하는 내용이 언제적 무엇을 가리키는지 정확히 알았다. 그런데 정작 분석 내용이 기억나지 않았다. 

원본 리포지토리를 불러와 들여다봤다.
> https://github.com/chaeyoonakim/survey-sent-analysis

어렵지 않게 다음날 통화에서 설명할 수 있었다.

코드베이스는 크게 세 가지 메인 스크립트로 구성되어 있다: (1) 텍스트 데이터 전처리, (2) wordcloud 만들기, (3) 감정 분석. 주요 코드는 NLTK 라이브러리를 기반으로 하고 시각화를 위한 기본 패키지 코드가 추가되었다.

쉽게 썼고 쉽게 기억해내어 쉽게 전달한 코드가 90% 틀렸다는 사실을 한달 뒤에서야 알게된다. 크게 4가지 지점이다.

1. 감정 분석 대상 지정오류

지난 플젝에서 감정 분석은 `TextBlob`의 polarity를 사용하여 긍정(+)과 부정(-) 점수화를 하는 것을 메인 로직으로 하고 있다. 그런데 polarity를 측정하기 위해 넘겨준 단어들이 normalisation을 거친 상태여서 particle들이 사라진 단어 형태가 감정 스코어링에 적합하지 않았다는 것을 알게된다. 본 플젝에서는 stop-words 제외와 stemming, lemmatization 세 가지를 활용하여 텍스트 데이터를 표준화하는 작업을 거쳤다. NLTK의 PorterStemmer와 WordNet lemmatization을 사용한 부분을 오류로 판단할 수 있었다. 예를 들어, "terrible"이라는 강한 부정 감정의 단어는 stemming을 거치며 "terribl"이 되었을 때 감정을 가진 원단어와 매칭되지 않아 중성화 처리가 될 수 있다.

2. Stop-words 제거 검토부족

지난 플젝은 NLTK의 표준 English stop-words 패키지를 다운 받아 사용했었다. 그에 더해서 설문 대상들이 공통적으로 공유하고 있는 축약어들 (예를 들어, 팀 이름 등) 혹은 설문 특성으로 인해 반복되는 단어들 (예를 들어, 리더쉽 등)을 stop-words로 추가하는 노력이 있었다. 하지만 기존 세트 안에 포함된 내용을 제외하는 작업을 진행하지 않은 오류가 있었다. 예를 들어, "not", "no"와 같은 negations을 제거해주어야 했다. 감정 분석에서 부정적으로 분류될 단어들이 stop-words에 들어가 제외되면 부정어가 사용된 부분들이 최종 통계로 잡히지 않고 반대 의미인 긍정어만 점수에 집계되었다. 이것은 한번의 텍스트 처리를 두 개의 다른 목적으로 공통되게 사용하면서 발생한 문제였다. Wordcloud를 만드는 과정에서는 전치사를 포함해 중요하지 않은 stop-words를 모두 제거하는 것이 옳았기 때문이다. 하지만 감정 분석을 할 때는 다르게 텍스트 표준 작업을 거쳤어야 한다. 다행히 지난 코드가 이미 모듈화된 상태여서 각각의 분석에 서로 다른 params 적용을 하도록 쉽게 분리할 수 있었다.

3. 감정 분석 결과 통계오류

polarity scoring을 마친 후 mean값을 구하는데 0으로 매겨진 점수들을 제거하는 오류가 있었다. 해당 필터를 제외하는 것으로 해결하였다.

4. 축약어 처리 검토부족

위 세가지 오류들을 수정하면서 한 가지 개선도 함께 이뤄졌다. contractions 패키지를 사용해 축약어를 처리하는 단계를 추가하였다. NLTK의 Tokenizer가 동작할 때 예를 들어 "didn't"와 같은 축약어를 "did"와 "n't"로 분류한다. a-z regex필터를 거치면서 "n't"가 사라지면 "not"에 대한 언급이 제거된다. 이를 "did"와 "not"으로 수정할 수 있었다.

다시 동기를 만나 내용을 전달하고 각자 생각할 부분을 숙제로 가져왔다.

동기가 처음부터 지난 플젝을 떠올린 이유도 현재 진행해야 할 본인의 플젝이 있기 때문이었다.

그 당시 리뷰어들이 결과를 받아보고 왜 그럴듯하다고 받아들였을까?

지금도 리뷰어들이 (가채점)결과를 받아보고 특별한 비판 없이 받아들인 이유는 무엇일까?

2년 전 로직 오류를 이제 파악하고 고쳤는데도 왜 결과 수치가 크게 변하지 않을까?

그 당시와 다르게 이번에 사용하는 새로운 데이터가 가지고 있는 한계점 때문인가?

polarity scoring 결과 텍스트 처리를 다르게 주어도 0.12에서 0.18까지 변화 폭이 크지 않았다. 

| Category | Lemmatization | Stemming True | Stemming False |
| :--- | :--- | :---: | :---: |
| **Defining Insights** | True | 0.18 | 0.17 |
| | False | 0.19 | 0.18 |
| **Mechanisms to create insights** | True | 0.14 | 0.13 |
| | False | 0.14 | 0.14 |
| **Tools to create insights** | True | 0.14 | 0.12 |
| | False | 0.14 | 0.13 |
| **Insight Dissemination** | True | 0.14 | 0.14 |
| | False | 0.15 | 0.15 |


특별한 시기였다. 답변 내용이 민감할 수 있었다.

데이터가 손에 있어서 간단하게 돌려본 텍스트 분석 결과가 중립적인 (혹은 미세한 수치로 긍정적) 사실이 새로운 리더쉽에게 도움되는 방향이었다. 기대 이상으로 호평을 받아서 얼떨떨한 기분이 기억난다. 뜻밖의 칭찬들에 상기된 내가 서 있던 회의장의 온도를 아직 기억한다. 그리고 나서 2년 후, 결국 당시 오류가 있던 부분을 고쳐내고 오늘의 회고까지 작성한다. 아직 질문에 대한 모든 답을 찾지 못했다. 일차적인 회고를 발행하면서 추가 피드백을 구할 수 있게 현재까지 상황을 정리하는 것을 목표로 하였다.

관련된 포스트:
- ["What I Got Wrong Building a Sentiment Analysis Pipeline for Survey Data"]({% post_url 2026-07-01-what-i-got-wrong-sentiment-analysis %})
- ["Fixing a Sentiment Analysis Pipeline: A Checklist for Next Time"]({% post_url 2026-07-01-fixing-sentiment-analysis-pipeline-next-time %})
- ["Four Knobs in My Text Preprocessing Pipeline (and What Each One Actually Does)"]({% post_url 2026-07-02-four-parameters-text-preprocessing %})
