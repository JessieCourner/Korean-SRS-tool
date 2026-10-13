import json
from pathlib import Path

OUT = Path(__file__).with_name("vocabulary_packs_v2.json")
TOPIK_SOURCE = "https://www.topikguide.com/topik-beginner-level-vocabulary-list-with-meanings/"
TOPIK2_SOURCE = "https://www.topikguide.com/6000-most-common-korean-words-1/"

# Each row: lemma, POS, English target, answer in context, Korean before/after,
# English before/after, required answer form.
PACKS = [
    ("topik1_daily", "Everyday routines", "TOPIK I · beginner", "Daily life", [
        ("아침", "noun", "morning", "아침", "저는 ", "마다 물을 한 잔 마셔요.", "Every ", ", I drink a glass of water.", "Noun"),
        ("일어나다", "verb", "get up", "일어나요", "저는 평일에 여섯 시에 ", ".", "I ", " at six on weekdays.", "Polite present (-아요/어요)"),
        ("씻다", "verb", "wash up", "씻어요", "운동한 다음에 먼저 ", ".", "After exercising, I ", " first.", "Polite present (-아요/어요)"),
        ("준비하다", "verb", "get ready", "준비해요", "출근하기 전에 가방을 ", ".", "Before work, I ", " my bag.", "Polite present (-해요)"),
        ("바쁘다", "adjective", "busy", "바빠요", "월요일에는 일이 많아서 ", ".", "I am ", " because I have a lot of work on Mondays.", "Polite present (-아요/어요)"),
        ("천천히", "adverb", "slowly", "천천히", "시간이 있을 때는 아침을 ", " 먹어요.", "When I have time, I eat breakfast ", ".", "Adverb (unchanged)"),
        ("일찍", "adverb", "early", "일찍", "내일은 회의가 있어서 평소보다 ", " 출발해요.", "I have a meeting tomorrow, so I will leave ", " than usual.", "Adverb (unchanged)"),
        ("청소하다", "verb", "clean", "청소해요", "저는 토요일마다 방을 ", ".", "I ", " my room every Saturday.", "Polite present (-해요)"),
        ("쉬다", "verb", "rest", "쉬어요", "점심을 먹고 십 분 동안 ", ".", "After lunch, I ", " for ten minutes.", "Polite present (-어요)"),
        ("항상", "adverb", "always", "항상", "저는 자기 전에 ", " 일기를 써요.", "I ", " write in my journal before bed.", "Adverb (unchanged)"),
    ]),
    ("topik1_food", "Food and cafés", "TOPIK I · beginner", "Food & dining", [
        ("밥", "noun", "rice", "밥을", "저는 점심에 ", " 먹어요.", "I eat ", " for lunch.", "Noun + object marker -을"),
        ("먹다", "verb", "eat", "먹어요", "배가 고파서 지금 ", ".", "I am hungry, so I am going to ", " now.", "Polite present (-어요)"),
        ("마시다", "verb", "drink", "마셔요", "아침마다 따뜻한 차를 ", ".", "I ", " warm tea every morning.", "Polite present (-어요)"),
        ("맛있다", "adjective", "delicious", "맛있어요", "이 식당의 국수는 정말 ", ".", "The noodles at this restaurant are really ", ".", "Polite present (-어요)"),
        ("맵다", "adjective", "spicy", "매워요", "이 김치는 조금 ", ".", "This kimchi is a little ", ".", "Polite present (ㅂ-irregular)"),
        ("달다", "adjective", "sweet", "달아요", "딸기가 아주 ", ".", "The strawberries are very ", ".", "Polite present (-아요)"),
        ("주문하다", "verb", "order", "주문해요", "카페에서 커피와 케이크를 ", ".", "At the café, I ", " coffee and cake.", "Polite present (-해요)"),
        ("계산하다", "verb", "pay", "계산해요", "식사를 다 한 뒤에 여기서 ", ".", "After finishing the meal, I ", " here.", "Polite present (-해요)"),
        ("조금", "adverb", "a little", "조금", "배가 불러서 음식을 ", " 남겼어요.", "I was full, so I left ", " food.", "Adverb (unchanged)"),
        ("배부르다", "adjective", "full", "배불러요", "점심을 많이 먹어서 지금 ", ".", "I ate a lot for lunch, so I am ", " now.", "Polite present (르-irregular)"),
    ]),
    ("topik1_people", "People and relationships", "TOPIK I · beginner", "People", [
        ("가족", "noun", "family", "가족과", "이번 주말에는 ", " 바다에 가요.", "This weekend I am going to the sea with my ", ".", "Noun + companion marker -과"),
        ("부모님", "noun", "parents", "부모님께", "명절에 저는 ", " 전화를 드려요.", "On holidays I call my ", ".", "Honorific noun + recipient marker -께"),
        ("친구", "noun", "friend", "친구를", "오늘 저녁에 ", " 만나요.", "I am meeting a ", " this evening.", "Noun + object marker -를"),
        ("만나다", "verb", "meet", "만나요", "우리는 역 앞에서 ", ".", "We ", " in front of the station.", "Polite present (-아요)"),
        ("연락하다", "verb", "contact", "연락해요", "도착하면 가족에게 바로 ", ".", "When I arrive, I ", " my family right away.", "Polite present (-해요)"),
        ("친절하다", "adjective", "kind", "친절해요", "새 선생님은 학생들에게 늘 ", ".", "The new teacher is always ", " to the students.", "Polite present (-해요)"),
        ("같이", "adverb", "together", "같이", "오늘은 동생과 ", " 저녁을 만들어요.", "Today I am making dinner ", " with my younger sibling.", "Adverb (unchanged)"),
        ("약속", "noun", "appointment", "약속이", "내일 오후에 중요한 ", " 있어요.", "I have an important ", " tomorrow afternoon.", "Noun + subject marker -이"),
        ("기다리다", "verb", "wait", "기다려요", "친구가 올 때까지 카페에서 ", ".", "I ", " at the café until my friend arrives.", "Polite present (-려요)"),
        ("웃다", "verb", "smile", "웃어요", "그 사진을 보면 저도 모르게 ", ".", "When I see that photo, I ", " without realizing it.", "Polite present (-어요)"),
    ]),
    ("topik1_school", "School and work", "TOPIK I · beginner", "Study & work", [
        ("학교", "noun", "school", "학교에", "저는 버스를 타고 ", " 가요.", "I take the bus ", ".", "Noun + destination marker -에"),
        ("공부하다", "verb", "study", "공부해요", "시험 전에 도서관에서 매일 ", ".", "Before an exam, I ", " at the library every day.", "Polite present (-해요)"),
        ("배우다", "verb", "learn", "배워요", "요즘 저는 한국어를 ", ".", "These days, I am ", " Korean.", "Polite present (-워요)"),
        ("질문", "noun", "question", "질문을", "모르는 단어가 있으면 선생님께 ", " 해요.", "If I do not know a word, I ask the teacher a ", ".", "Noun + object marker -을"),
        ("대답하다", "verb", "answer", "대답해요", "학생이 선생님의 질문에 ", ".", "The student ", " the teacher's question.", "Polite present (-해요)"),
        ("설명하다", "verb", "explain", "설명해요", "선생님은 새 문법을 천천히 ", ".", "The teacher ", " the new grammar slowly.", "Polite present (-해요)"),
        ("어렵다", "adjective", "difficult", "어려워요", "이 책은 단어가 많아서 조금 ", ".", "This book is a little ", " because it has many words.", "Polite present (ㅂ-irregular)"),
        ("쉽다", "adjective", "easy", "쉬워요", "이 앱으로 복습하면 문법이 더 ", ".", "Grammar becomes ", " when I review with this app.", "Polite present (ㅂ-irregular)"),
        ("열심히", "adverb", "diligently", "열심히", "제 친구는 매일 도서관에서 ", " 공부해요.", "My friend studies ", " at the library every day.", "Adverb (unchanged)"),
        ("시험", "noun", "exam", "시험이", "다음 주에 한국어 ", " 있어요.", "I have a Korean ", " next week.", "Noun + subject marker -이"),
    ]),
    ("topik1_transport", "Places and transport", "TOPIK I · beginner", "Getting around", [
        ("버스", "noun", "bus", "버스를", "저는 매일 아침 ", " 타고 회사에 가요.", "Every morning I take the ", " to work.", "Noun + object marker -를"),
        ("지하철", "noun", "subway", "지하철로", "비가 와서 오늘은 ", " 출근해요.", "It is raining, so today I commute by ", ".", "Noun + means marker -로"),
        ("타다", "verb", "ride", "타요", "우리는 공항에서 택시를 ", ".", "We ", " a taxi at the airport.", "Polite present (-아요)"),
        ("내리다", "verb", "get off", "내려요", "두 정거장 뒤에 버스에서 ", ".", "I ", " the bus two stops later.", "Polite present (-려요)"),
        ("갈아타다", "verb", "transfer", "갈아타요", "시청역에서 2호선으로 ", ".", "I ", " to Line 2 at City Hall Station.", "Polite present (-아요)"),
        ("걷다", "verb", "walk", "걸어요", "날씨가 좋아서 집까지 ", ".", "The weather is nice, so I ", " home.", "Polite present (ㄷ-irregular)"),
        ("가깝다", "adjective", "close", "가까워요", "우리 집은 지하철역에서 아주 ", ".", "My home is very ", " to the subway station.", "Polite present (ㅂ-irregular)"),
        ("멀다", "adjective", "far", "멀어요", "회사까지 거리가 조금 ", ".", "The distance to work is a little ", ".", "Polite present (-어요)"),
        ("출발하다", "verb", "depart", "출발해요", "기차는 오전 아홉 시에 ", ".", "The train ", " at nine in the morning.", "Polite present (-해요)"),
        ("도착하다", "verb", "arrive", "도착해요", "비행기는 밤 열 시에 인천에 ", ".", "The plane ", " in Incheon at ten at night.", "Polite present (-해요)"),
    ]),
    ("topik1_shopping", "Shopping and services", "TOPIK I · beginner", "Shopping", [
        ("가격", "noun", "price", "가격이", "이 가방은 디자인도 좋고 ", " 괜찮아요.", "This bag has a nice design, and the ", " is reasonable.", "Noun + subject marker -이"),
        ("사다", "verb", "buy", "사요", "저는 시장에서 신선한 과일을 ", ".", "I ", " fresh fruit at the market.", "Polite present (-아요)"),
        ("팔다", "verb", "sell", "팔아요", "이 가게에서는 직접 만든 빵을 ", ".", "This shop ", " bread made in-house.", "Polite present (-아요)"),
        ("고르다", "verb", "choose", "골라요", "선물로 줄 책을 천천히 ", ".", "I am taking my time to ", " a book as a gift.", "Polite present (르-irregular)"),
        ("싸다", "adjective", "inexpensive", "싸요", "오늘은 시장 채소가 아주 ", ".", "The vegetables at the market are very ", " today.", "Polite present (-아요)"),
        ("비싸다", "adjective", "expensive", "비싸요", "백화점의 가죽 가방은 조금 ", ".", "The leather bags at the department store are a little ", ".", "Polite present (-아요)"),
        ("필요하다", "adjective", "need", "필요해요", "새 노트와 펜이 ", ".", "I ", " a new notebook and pen.", "Polite present (-해요)"),
        ("카드", "noun", "card", "카드로", "현금이 없어서 ", " 결제했어요.", "I did not have cash, so I paid by ", ".", "Noun + means marker -로"),
        ("현금", "noun", "cash", "현금으로", "작은 가게에서는 ", " 계산했어요.", "At the small shop, I paid with ", ".", "Noun + means marker -으로"),
        ("환불하다", "verb", "get a refund", "환불해요", "영수증을 가지고 가면 이 물건을 ", ".", "If I bring the receipt, I can ", " this item.", "Polite present (-해요)"),
    ]),
    ("topik1_health", "Health and the body", "TOPIK I · beginner", "Health", [
        ("머리", "noun", "head", "머리가", "아침부터 ", " 아파요.", "My ", " has hurt since this morning.", "Noun + subject marker -가"),
        ("배", "noun", "stomach", "배가", "찬 음식을 먹어서 ", " 아파요.", "My ", " hurts because I ate cold food.", "Noun + subject marker -가"),
        ("아프다", "adjective", "hurt", "아파요", "계단에서 넘어져서 무릎이 ", ".", "I fell on the stairs, so my knee ", ".", "Polite present (-아요)"),
        ("병원", "noun", "hospital", "병원에", "열이 계속 나서 아침에 ", " 갔어요.", "I kept having a fever, so I went to the ", " in the morning.", "Noun + destination marker -에"),
        ("약", "noun", "medicine", "약을", "감기에 걸려서 식사 후에 ", " 먹었어요.", "I caught a cold, so I took the ", " after eating.", "Noun + object marker -을"),
        ("건강", "noun", "health", "건강을", "매일 조금씩 운동하며 ", " 지켜요.", "I protect my ", " by exercising a little every day.", "Noun + object marker -을"),
        ("피곤하다", "adjective", "tired", "피곤해요", "어제 잠을 늦게 자서 오늘 ", ".", "I am ", " today because I went to bed late yesterday.", "Polite present (-해요)"),
        ("운동하다", "verb", "exercise", "운동해요", "저는 건강을 위해 주 세 번 ", ".", "I ", " three times a week for my health.", "Polite present (-해요)"),
        ("괜찮다", "adjective", "be okay", "괜찮아요", "조금 쉬고 나니까 이제 ", ".", "After resting a little, I am ", " now.", "Polite present (-아요)"),
        ("기침", "noun", "cough", "기침이", "감기에 걸린 뒤로 ", " 계속 나요.", "I have had a ", " ever since I caught a cold.", "Noun + subject marker -이"),
    ]),
    ("topik1_time", "Time and plans", "TOPIK I · beginner", "Time", [
        ("오늘", "adverb", "today", "오늘", "저는 ", " 도서관에서 공부해요.", "I am studying at the library ", ".", "Time adverb (unchanged)"),
        ("내일", "adverb", "tomorrow", "내일", "회의가 있어서 ", " 일찍 회사에 가요.", "I have a meeting, so ", " I am going to work early.", "Time adverb (unchanged)"),
        ("어제", "adverb", "yesterday", "어제", "저는 ", " 친구와 영화를 봤어요.", "I watched a movie with a friend ", ".", "Time adverb (unchanged)"),
        ("주말", "noun", "weekend", "주말에는", "저는 보통 ", " 집에서 쉬어요.", "On the ", " I usually rest at home.", "Noun + topic marker -에는"),
        ("늦다", "adjective", "late", "늦어요", "버스가 오지 않아서 수업에 ", ".", "The bus did not come, so I am ", " for class.", "Polite present (-어요)"),
        ("빠르다", "adjective", "fast", "빨라요", "이 기차는 다른 기차보다 ", ".", "This train is ", " than the others.", "Polite present (르-irregular)"),
        ("시작하다", "verb", "start", "시작해요", "영화는 저녁 일곱 시에 ", ".", "The movie ", " at seven in the evening.", "Polite present (-해요)"),
        ("끝나다", "verb", "end", "끝나요", "수업은 오후 네 시에 ", ".", "Class ", " at four in the afternoon.", "Polite present (-나요)"),
        ("가끔", "adverb", "sometimes", "가끔", "저는 바쁜 날에도 ", " 산책해요.", "Even on busy days, I ", " go for a walk.", "Adverb (unchanged)"),
        ("미리", "adverb", "in advance", "미리", "여행 날짜가 정해지면 표를 ", " 예매해요.", "Once the travel dates are set, I book tickets ", ".", "Adverb (unchanged)"),
    ]),
    ("topik1_weather", "Weather and nature", "TOPIK I · beginner", "Nature", [
        ("날씨", "noun", "weather", "날씨가", "오늘은 ", " 좋아서 창문을 열었어요.", "The ", " is nice today, so I opened the window.", "Noun + subject marker -가"),
        ("비", "noun", "rain", "비가", "오후부터 ", " 와서 우산을 썼어요.", "It started to ", " this afternoon, so I used an umbrella.", "Noun + subject marker -가"),
        ("눈", "noun", "snow", "눈이", "밤새 ", " 내려서 길이 하얘졌어요.", "It ", " fell all night, so the road turned white.", "Noun + subject marker -이"),
        ("바람", "noun", "wind", "바람이", "밖에 ", " 많이 불어서 모자를 썼어요.", "The ", " was strong outside, so I wore a hat.", "Noun + subject marker -이"),
        ("춥다", "adjective", "cold", "추워요", "겨울 아침에는 밖이 정말 ", ".", "It is really ", " outside on winter mornings.", "Polite present (ㅂ-irregular)"),
        ("덥다", "adjective", "hot", "더워요", "오늘은 날씨가 너무 ", ".", "The weather is very ", " today.", "Polite present (ㅂ-irregular)"),
        ("맑다", "adjective", "clear", "맑아요", "비가 그친 뒤 하늘이 ", ".", "After the rain stopped, the sky was ", ".", "Polite present (-아요)"),
        ("흐리다", "adjective", "cloudy", "흐려요", "오후에는 하늘이 조금 ", ".", "The sky is a little ", " this afternoon.", "Polite present (ㅡ deletion)"),
        ("따뜻하다", "adjective", "warm", "따뜻해요", "봄에는 햇볕이 ", ".", "The sunshine is ", " in spring.", "Polite present (-해요)"),
        ("산책하다", "verb", "take a walk", "산책해요", "저녁을 먹은 후에 공원에서 ", ".", "After dinner, I ", " in the park.", "Polite present (-해요)"),
    ]),
    ("topik1_hobbies", "Hobbies and media", "TOPIK I · beginner", "Hobbies", [
        ("음악", "noun", "music", "음악을", "저는 집에서 조용한 ", " 들어요.", "At home, I listen to quiet ", ".", "Noun + object marker -을"),
        ("노래하다", "verb", "sing", "노래해요", "기분이 좋을 때 혼자 ", ".", "When I am in a good mood, I ", " by myself.", "Polite present (-해요)"),
        ("춤추다", "verb", "dance", "춤춰요", "친구들은 축제에서 함께 ", ".", "My friends ", " together at the festival.", "Polite present (-춰요)"),
        ("읽다", "verb", "read", "읽어요", "잠자기 전에 소설을 조금 ", ".", "I ", " a little of a novel before bed.", "Polite present (ㄺ cluster)"),
        ("보다", "verb", "watch", "봐요", "주말에는 가족과 영화를 ", ".", "On weekends, I ", " a movie with my family.", "Polite present (ㅗ contraction)"),
        ("사진", "noun", "photo", "사진을", "여행에서 찍은 ", " 친구에게 보여 줬어요.", "I showed my friend the ", " I took on the trip.", "Noun + object marker -을"),
        ("찍다", "verb", "take (a photo)", "찍어요", "벚꽃이 피면 사진을 많이 ", ".", "When the cherry blossoms bloom, I ", " lots of photos.", "Polite present (-어요)"),
        ("재미있다", "adjective", "fun", "재미있어요", "이 드라마는 이야기가 정말 ", ".", "The story in this drama is really ", ".", "Polite present (-어요)"),
        ("자주", "adverb", "often", "자주", "저는 출퇴근길에 팟캐스트를 ", " 들어요.", "I ", " listen to podcasts on my commute.", "Adverb (unchanged)"),
        ("취미", "noun", "hobby", "취미는", "제 ", " 요리예요.", "My ", " is cooking.", "Noun + topic marker -는"),
    ]),
    ("topik2_emotions", "Feelings and communication", "TOPIK II-oriented · intermediate", "People & feelings", [
        ("걱정", "noun", "worry", "걱정이", "시험 결과가 아직 안 나와서 ", " 많아요.", "I have a lot of ", " because the exam results are not out yet.", "Noun + subject marker -이"),
        ("행복하다", "adjective", "happy", "행복해요", "가족과 저녁을 먹을 때 가장 ", ".", "I feel ", " when I have dinner with my family.", "Polite present (-해요)"),
        ("기쁘다", "adjective", "glad", "기뻐요", "친구가 다시 건강해져서 정말 ", ".", "I am really ", " that my friend is healthy again.", "Polite present (ㅡ deletion)"),
        ("슬프다", "adjective", "sad", "슬퍼요", "좋아하는 드라마가 끝나서 조금 ", ".", "I am a little ", " because my favorite drama ended.", "Polite present (ㅡ deletion)"),
        ("외롭다", "adjective", "lonely", "외로워요", "새 도시에서 아는 사람이 없어서 가끔 ", ".", "I sometimes feel ", " because I do not know anyone in the new city.", "Polite present (ㅂ-irregular)"),
        ("안심하다", "verb", "feel relieved", "안심해요", "검사 결과가 괜찮다는 말을 듣고 ", ".", "I ", " after hearing the test results are fine.", "Polite present (-해요)"),
        ("화나다", "verb", "get angry", "화나요", "약속 시간을 지키지 않으면 친구가 ", ".", "If someone does not keep an appointment, my friend ", ".", "Polite present (-나요)"),
        ("솔직하다", "adjective", "honest", "솔직해요", "그 친구는 자기 감정에 늘 ", ".", "That friend is always ", " about their feelings.", "Polite present (-해요)"),
        ("의견", "noun", "opinion", "의견을", "회의에서 제 ", " 차분하게 말했어요.", "I calmly shared my ", " at the meeting.", "Noun + object marker -을"),
        ("이해하다", "verb", "understand", "이해해요", "상대방의 입장에서 생각하면 그 마음을 ", ".", "If I think from the other person's perspective, I ", " their feelings.", "Polite present (-해요)"),
    ]),
    ("topik2_travel", "Travel and culture", "TOPIK II-oriented · intermediate", "Travel & culture", [
        ("여행", "noun", "trip", "여행을", "가을에 친구와 제주도 ", " 계획하고 있어요.", "I am planning a ", " to Jeju with a friend in fall.", "Noun + object marker -을"),
        ("예약하다", "verb", "reserve", "예약해요", "표가 매진되기 전에 숙소를 ", ".", "I ", " accommodation before tickets sell out.", "Polite present (-해요)"),
        ("여권", "noun", "passport", "여권을", "출국 전에 ", " 꼭 확인하세요.", "Be sure to check your ", " before departure.", "Noun + object marker -을"),
        ("공항", "noun", "airport", "공항에", "비행기 출발 두 시간 전에 ", " 도착했어요.", "I arrived at the ", " two hours before the flight.", "Noun + destination marker -에"),
        ("표", "noun", "ticket", "표를", "온라인으로 기차 ", " 미리 샀어요.", "I bought a train ", " online in advance.", "Noun + object marker -를"),
        ("관광하다", "verb", "sightsee", "관광해요", "오전에는 박물관 주변을 ", ".", "In the morning, we ", " around the museum.", "Polite present (-해요)"),
        ("유명하다", "adjective", "famous", "유명해요", "이 마을은 오래된 시장으로 ", ".", "This town is ", " for its old market.", "Polite present (-해요)"),
        ("전통", "noun", "tradition", "전통을", "박물관에서 한국의 ", " 배웠어요.", "At the museum, I learned about Korean ", ".", "Noun + object marker -을"),
        ("문화", "noun", "culture", "문화를", "여행을 하며 다른 나라의 ", " 직접 경험했어요.", "By traveling, I experienced another country's ", " firsthand.", "Noun + object marker -를"),
        ("경험하다", "verb", "experience", "경험해요", "새로운 음식을 먹으며 그 지역의 맛을 ", ".", "By trying new food, I ", " the local flavors.", "Polite present (-해요)"),
    ]),
]

# Second batch for each topic. These are selected from the same public
# beginner/intermediate vocabulary references as the first batch, then placed
# in original short sentences written for this app. Keeping the added words
# next to their first batch makes each topic pack a useful 20-card set.
TOPIC_EXTENSIONS = {
    "topik1_daily": [
        ("자다", "verb", "sleep", "자요", "저는 보통 자정 전에 ", ".", "I usually ", " before midnight.", "Polite present (-아요)"),
        ("출근하다", "verb", "goes to work", "출근해요", "제 언니는 매일 아침 지하철로 ", ".", "My older sister ", " by subway every morning.", "Polite present (-해요)"),
        ("퇴근하다", "verb", "leaves work", "퇴근해요", "아버지는 보통 여섯 시에 ", ".", "My father usually ", " at six.", "Polite present (-해요)"),
        ("샤워하다", "verb", "take a shower", "샤워해요", "저는 운동한 뒤에 ", ".", "I ", " after exercising.", "Polite present (-해요)"),
        ("방", "noun", "room", "방을", "저는 토요일마다 ", " 청소해요.", "I clean my ", " every Saturday.", "Noun + object marker -을"),
        ("집", "noun", "home", "집에", "주말에는 친구들이 우리 ", " 자주 와요.", "On weekends, my friends often come to our ", ".", "Noun + location marker -에"),
        ("일기", "noun", "diary", "일기를", "저는 자기 전에 ", " 써요.", "I write in my ", " before bed.", "Noun + object marker -를"),
        ("보통", "adverb", "usually", "보통", "저는 ", " 아침에 커피를 마셔요.", "I ", " drink coffee in the morning.", "Adverb (unchanged)"),
        ("매일", "adverb", "every day", "매일", "저는 ", " 저녁에 한국어를 공부해요.", "I study Korean ", " in the evening.", "Adverb (unchanged)"),
        ("저녁", "noun", "evening", "저녁에는", "저는 ", " 가족과 함께 식사해요.", "In the ", ", I eat with my family.", "Noun + topic marker -에는"),
    ],
    "topik1_food": [
        ("국수", "noun", "noodles", "국수를", "비 오는 날에는 따뜻한 ", " 먹고 싶어요.", "On rainy days, I want to eat warm ", ".", "Noun + object marker -를"),
        ("과일", "noun", "fruit", "과일을", "저는 아침마다 ", " 조금 먹어요.", "I eat some ", " every morning.", "Noun + object marker -을"),
        ("빵", "noun", "bread", "빵으로", "아침에 바빠서 ", " 간단히 먹었어요.", "I was busy, so I had ", " for a quick breakfast.", "Noun + means marker -으로"),
        ("사과", "noun", "apple", "사과를", "저는 후식으로 ", " 하나 먹었어요.", "I ate an ", " for dessert.", "Noun + object marker -를"),
        ("우유", "noun", "milk", "우유를", "잠자기 전에 따뜻한 ", " 마셔요.", "I drink warm ", " before bed.", "Noun + object marker -를"),
        ("물", "noun", "water", "물을", "운동할 때는 ", " 자주 마셔요.", "I drink ", " often when I exercise.", "Noun + object marker -을"),
        ("음식", "noun", "food", "한국 음식을", "저는 ", " 좋아해요. 특히 비빔밥을 자주 먹어요.", "I like Korean ", ", especially bibimbap.", "Noun + object marker -을"),
        ("식당", "noun", "restaurant", "식당은", "이 ", " 점심시간에 손님이 많아요.", "This ", " is busy at lunchtime.", "Noun + topic marker -은"),
        ("배고프다", "adjective", "hungry", "배고파요", "저녁을 늦게 먹어서 지금 ", ".", "I ate dinner late, so I am ", " now.", "Polite present (-아요)"),
        ("달걀", "noun", "egg", "달걀을", "김치볶음밥에 ", " 하나 넣어요.", "I add one ", " to kimchi fried rice.", "Noun + object marker -을"),
    ],
    "topik1_people": [
        ("동생", "noun", "younger sibling", "동생을", "어제 역에서 ", " 만났어요.", "I met my ", " at the station yesterday.", "Noun + object marker -을"),
        ("아버지", "noun", "father", "아버지께", "생신에 저는 ", " 선물을 드렸어요.", "I gave my ", " a gift for his birthday.", "Honorific recipient marker -께"),
        ("어머니", "noun", "mother", "어머니와", "주말에 ", " 시장에 다녀왔어요.", "I went to the market with my ", " on the weekend.", "Noun + companion marker -와"),
        ("할머니", "noun", "grandmother", "할머니께서", "", " 만드신 김치가 정말 맛있어요.", "The kimchi my ", " made is delicious.", "Honorific subject marker -께서"),
        ("할아버지", "noun", "grandfather", "할아버지께", "저는 명절에 ", " 안부 전화를 드려요.", "I call my ", " to send my regards on holidays.", "Honorific recipient marker -께"),
        ("선생님", "noun", "teacher", "선생님께", "모르는 단어가 있어서 ", " 여쭤봤어요.", "I asked the ", " because I had a question about a word.", "Honorific recipient marker -께"),
        ("이름", "noun", "name", "이름을", "새로 만난 친구의 ", " 금방 외웠어요.", "I quickly learned my new friend's ", ".", "Noun + object marker -을"),
        ("이야기하다", "verb", "talked", "이야기했어요", "친구와 카페에서 오래 ", ".", "I ", " with my friend at a café for a long time.", "Polite past (-했어요)"),
        ("초대하다", "verb", "invited", "초대했어요", "이번 주말에 친구를 집에 ", ".", "I ", " a friend to my home this weekend.", "Polite past (-했어요)"),
        ("소개하다", "verb", "introduced", "소개했어요", "저는 동료에게 새 친구를 ", ".", "I ", " my new friend to a coworker.", "Polite past (-했어요)"),
    ],
    "topik1_school": [
        ("학생", "noun", "student", "학생이", "그 ", " 수업 시간에 질문을 했어요.", "The ", " asked a question in class.", "Noun + subject marker -이"),
        ("교실", "noun", "classroom", "교실에서", "우리는 ", " 한국어를 공부해요.", "We study Korean in the ", ".", "Noun + location marker -에서"),
        ("공책", "noun", "notebook", "공책에", "새 단어를 ", " 적어 두세요.", "Write new words in your ", ".", "Noun + location marker -에"),
        ("연필", "noun", "pencil", "연필로", "저는 ", " 이름을 썼어요.", "I wrote my name with a ", ".", "Noun + means marker -로"),
        ("사전", "noun", "dictionary", "사전에서", "모르는 단어를 ", " 찾아봤어요.", "I looked up the unfamiliar word in a ", ".", "Noun + location marker -에서"),
        ("수업", "noun", "class", "수업은", "오늘 ", " 아홉 시에 시작해요.", "Today's ", " starts at nine.", "Noun + topic marker -은"),
        ("숙제", "noun", "homework", "숙제를", "저는 저녁을 먹고 ", " 했어요.", "I did my ", " after dinner.", "Noun + object marker -를"),
        ("가르치다", "verb", "teaches", "가르쳐요", "이 선생님은 학생들에게 발음을 ", ".", "This teacher ", " pronunciation to students.", "Polite present (-쳐요)"),
        ("일하다", "verb", "works", "일해요", "제 언니는 병원에서 ", ".", "My older sister ", " at a hospital.", "Polite present (-해요)"),
        ("학원", "noun", "academy", "학원에", "저는 퇴근한 뒤 한국어 ", " 가요.", "I go to a Korean ", " after work.", "Noun + destination marker -에"),
    ],
    "topik1_transport": [
        ("택시", "noun", "taxi", "택시를", "공항에서 ", " 타고 호텔에 갔어요.", "I took a ", " from the airport to the hotel.", "Noun + object marker -를"),
        ("비행기", "noun", "plane", "비행기로", "저는 ", " 부다페스트에서 서울까지 갔어요.", "I went from Budapest to Seoul by ", ".", "Noun + means marker -로"),
        ("기차", "noun", "train", "기차는", "이 ", " 보통 제시간에 도착해요.", "This ", " usually arrives on time.", "Noun + topic marker -는"),
        ("자전거", "noun", "bicycle", "자전거를", "날씨가 좋으면 ", " 타고 공원에 가요.", "When the weather is nice, I ride a ", " to the park.", "Noun + object marker -를"),
        ("자동차", "noun", "car", "자동차는", "이 ", " 연료를 많이 사용해요.", "This ", " uses a lot of fuel.", "Noun + topic marker -는"),
        ("역", "noun", "station", "역에", "저는 약속 시간보다 십 분 일찍 ", " 도착했어요.", "I arrived at the ", " ten minutes before our meeting.", "Noun + location marker -에"),
        ("길", "noun", "road", "길이", "눈이 와서 ", " 미끄러워요.", "The ", " is slippery because it snowed.", "Noun + subject marker -이"),
        ("운전하다", "verb", "drives", "운전해요", "아버지는 장거리도 안전하게 ", ".", "My father ", " safely, even on long trips.", "Polite present (-해요)"),
        ("편리하다", "adjective", "convenient", "편리해요", "새 버스 노선은 출근할 때 정말 ", ".", "The new bus route is really ", " for commuting.", "Polite present (-해요)"),
        ("복잡하다", "adjective", "crowded", "복잡해요", "출근 시간에는 시내 도로가 ", ".", "The city roads are ", " during rush hour.", "Polite present (-해요)"),
    ],
    "topik1_shopping": [
        ("가게", "noun", "shop", "가게에서", "집 앞 ", " 우유를 샀어요.", "I bought milk at the ", " in front of my home.", "Noun + location marker -에서"),
        ("백화점", "noun", "department store", "백화점에", "저는 코트를 보러 ", " 갔어요.", "I went to the ", " to look at coats.", "Noun + destination marker -에"),
        ("옷", "noun", "clothes", "옷을", "새 재킷을 사기 전에 ", " 입어 봤어요.", "I tried on the ", " before buying the new jacket.", "Noun + object marker -을"),
        ("신발", "noun", "shoes", "신발을", "가게에서 편한 ", " 찾아봤어요.", "I looked for comfortable ", " at the shop.", "Noun + object marker -을"),
        ("지갑", "noun", "wallet", "지갑을", "저는 아침에 ", " 집에 두고 왔어요.", "I left my ", " at home this morning.", "Noun + object marker -을"),
        ("영수증", "noun", "receipt", "영수증을", "물건을 산 뒤에 ", " 꼭 확인해요.", "I always check the ", " after buying something.", "Noun + object marker -을"),
        ("할인", "noun", "discount", "할인", "오늘은 ", " 행사가 있어서 가방이 저렴해요.", "There is a ", " today, so the bag costs less.", "Noun (unchanged)"),
        ("선물", "noun", "gift", "선물로", "친구 생일에 책을 ", " 골랐어요.", "I chose a book as a ", " for my friend's birthday.", "Noun + purpose marker -로"),
        ("입다", "verb", "wear", "입어요", "겨울에는 따뜻한 코트를 ", ".", "I ", " a warm coat in winter.", "Polite present (-어요)"),
        ("신다", "verb", "wear", "신어요", "비가 오면 장화를 ", ".", "When it rains, I ", " boots.", "Polite present (-어요)"),
    ],
    "topik1_health": [
        ("의사", "noun", "doctor", "의사에게", "저는 증상을 ", " 자세히 설명했어요.", "I explained my symptoms to the ", ".", "Noun + recipient marker -에게"),
        ("약국", "noun", "pharmacy", "약국에서", "감기약을 사려고 ", " 기다렸어요.", "I waited at the ", " to buy cold medicine.", "Noun + location marker -에서"),
        ("감기에 걸리다", "verb phrase", "caught a cold", "감기에 걸렸어요", "여행 중에 ", ".", "I ", " during the trip.", "Polite past (-렸어요)"),
        ("열이 나다", "verb phrase", "had a fever", "열이 나서", "어젯밤에 ", " 일찍 잤어요.", "I ", " last night, so I went to bed early.", "Causal connective (-아서/어서)"),
        ("몸", "noun", "body", "몸을", "운동하기 전에 ", " 충분히 풀어요.", "I warm up my ", " before exercising.", "Noun + object marker -을"),
        ("얼굴", "noun", "face", "얼굴을", "저는 아침마다 ", " 찬물로 씻어요.", "I wash my ", " with cold water every morning.", "Noun + object marker -을"),
        ("손", "noun", "hands", "손을", "음식을 먹기 전에 ", " 씻으세요.", "Wash your ", " before eating.", "Noun + object marker -을"),
        ("마스크", "noun", "mask", "마스크를", "사람이 많은 곳에서는 ", " 써요.", "I wear a ", " in crowded places.", "Noun + object marker -를"),
        ("체온", "noun", "body temperature", "체온을", "열이 있는 것 같아서 ", " 쟀어요.", "I thought I had a fever, so I took my ", ".", "Noun + object marker -을"),
        ("건강하다", "adjective", "healthy", "건강해요", "요즘은 매일 걸어서 몸이 ", ".", "I walk every day these days, so I am ", ".", "Polite present (-해요)"),
    ],
    "topik1_time": [
        ("시간", "noun", "time", "시간이", "오늘은 ", " 없어서 점심을 빨리 먹었어요.", "I did not have much ", " today, so I ate lunch quickly.", "Noun + subject marker -이"),
        ("분", "noun", "minutes", "분 동안", "저는 매일 십 ", " 한국어를 들어요.", "I listen to Korean for ten ", " every day.", "Counter + duration particle -동안"),
        ("시", "noun", "o'clock", "시부터", "저녁 여섯 ", " 아홉 시까지 공부했어요.", "I studied from six ", " until nine in the evening.", "Time marker -부터"),
        ("날", "noun", "day", "날에는", "비가 오는 ", " 집에서 책을 읽어요.", "On a rainy ", ", I read at home.", "Noun + topic marker -에는"),
        ("달", "noun", "month", "달마다", "저는 한 ", " 책을 한 권 읽어요.", "I read one book every ", ".", "Noun + frequency marker -마다"),
        ("다음달", "noun", "next month", "다음달에", " ", " 한국어 시험이 있어요.", "I have a Korean exam ", ".", "Time noun + location marker -에"),
        ("지난주", "noun", "last week", "지난주에", " ", " 친구를 만나서 영화를 봤어요.", "I met a friend and watched a movie ", ".", "Time noun + location marker -에"),
        ("올해", "noun", "this year", "올해는", " ", " 한국어 공부를 시작했어요.", "I started studying Korean ", ".", "Time noun + topic marker -는"),
        ("내년", "noun", "next year", "내년에는", " ", " 한국에 가고 싶어요.", "I want to go to Korea ", ".", "Time noun + topic marker -에는"),
        ("이번", "determiner", "This", "이번 주말에는", "", " 집에서 푹 쉴 거예요.", "", " weekend, I am going to rest at home.", "Determiner + time noun"),
    ],
    "topik1_weather": [
        ("봄", "noun", "spring", "봄에는", " ", " 공원에 꽃이 많이 피어요.", "In ", ", many flowers bloom in the park.", "Noun + topic marker -에는"),
        ("여름", "noun", "summer", "여름에는", " ", " 해가 늦게 져요.", "In ", ", the sun sets late.", "Noun + topic marker -에는"),
        ("가을", "noun", "autumn", "가을에는", " ", " 나무 잎이 빨갛게 변해요.", "In ", ", the leaves on the trees turn red.", "Noun + topic marker -에는"),
        ("겨울", "noun", "winter", "겨울에는", " ", " 따뜻한 차를 자주 마셔요.", "In ", ", I often drink warm tea.", "Noun + topic marker -에는"),
        ("계절", "noun", "seasons", "계절이", "한국에는 네 ", " 있어요.", "There are four ", " in Korea.", "Noun + subject marker -이"),
        ("꽃", "noun", "flower", "꽃이", "정원에 빨간 ", " 피었어요.", "A red ", " bloomed in the garden.", "Noun + subject marker -이"),
        ("나무", "noun", "tree", "나무 아래에서", "더운 날에는 ", " 쉬고 싶어요.", "On hot days, I want to rest under a ", ".", "Noun + location marker -아래에서"),
        ("강", "noun", "river", "강가에서", "저녁에 ", " 산책했어요.", "I took a walk by the ", " in the evening.", "Noun + location marker -가에서"),
        ("산", "noun", "mountain", "산에", "날씨가 맑아서 ", " 올랐어요.", "The weather was clear, so I climbed the ", ".", "Noun + destination marker -에"),
        ("구름", "noun", "clouds", "구름이", "오늘은 하늘에 ", " 많아요.", "There are a lot of ", " in the sky today.", "Noun + subject marker -이"),
    ],
    "topik1_hobbies": [
        ("축구하다", "verb", "play soccer", "축구를 해요", "주말마다 친구들과 ", ".", "I ", " with friends every weekend.", "Polite present (-해요)"),
        ("야구", "noun", "baseball", "야구를", "아버지는 저녁에 ", " 봐요.", "My father watches ", " in the evening.", "Noun + object marker -를"),
        ("농구하다", "verb", "play basketball", "농구를 해요", "학생들은 방과 후에 ", ".", "The students ", " after class.", "Polite present (-해요)"),
        ("수영하다", "verb", "swim", "수영해요", "저는 여름마다 수영장에서 ", ".", "I ", " at the pool every summer.", "Polite present (-해요)"),
        ("등산하다", "verb", "go hiking", "등산해요", "가을에는 친구들과 자주 ", ".", "In autumn, I often ", " with friends.", "Polite present (-해요)"),
        ("피아노를 치다", "verb phrase", "plays the piano", "피아노를 쳐요", "제 동생은 매일 저녁 ", ".", "My younger sibling ", " every evening.", "Polite present (-어요)"),
        ("테니스 치다", "verb phrase", "plays tennis", "테니스를 쳐요", "민수 씨는 주말마다 ", ".", "Minsu ", " every weekend.", "Polite present (-어요)"),
        ("그림을 그리다", "verb phrase", "draw a picture", "그림을 그려요", "아이들이 교실에서 ", ".", "The children ", " in the classroom.", "Polite present (-려요)"),
        ("영화", "noun", "movie", "영화를", "새 ", " 보러 주말에 극장에 갈 거예요.", "I am going to the theater this weekend to see a new ", ".", "Noun + object marker -를"),
        ("드라마", "noun", "drama", "드라마를", "저는 저녁에 한국 ", " 한 편 봐요.", "I watch one Korean ", " in the evening.", "Noun + object marker -를"),
    ],
    "topik2_emotions": [
        ("기분", "noun", "mood", "기분이", "오늘은 ", " 좋아요.", "I am in a good ", " today.", "Noun + subject marker -이"),
        ("마음", "noun", "heart", "마음을", "그 따뜻한 말이 제 ", " 편하게 해 줬어요.", "Those kind words put my ", " at ease.", "Noun + object marker -을"),
        ("긴장하다", "verb", "felt nervous", "긴장했어요", "많은 사람 앞에서 발표해서 ", ".", "I ", " because I presented in front of a lot of people.", "Polite past (-했어요)"),
        ("놀라다", "verb", "was surprised", "놀랐어요", "갑자기 문이 열려서 ", ".", "I ", " when the door suddenly opened.", "Polite past (-랐어요)"),
        ("실망하다", "verb", "disappointed", "실망했어요", "기대가 컸지만 결과를 보고 조금 ", ".", "My expectations were high, but the result left me ", ".", "Polite past (-했어요)"),
        ("부럽다", "adjective", "envious", "부러워요", "친구의 여행 사진을 보니 ", ".", "Seeing my friend's travel photos makes me ", ".", "Polite present (르-irregular)"),
        ("친하다", "adjective", "close", "친해요", "우리는 오래전부터 ", ".", "We have been ", " for a long time.", "Polite present (-해요)"),
        ("관심", "noun", "interest", "관심이", "저는 한국 역사에 ", " 많아요.", "I have a lot of ", " in Korean history.", "Noun + subject marker -이"),
        ("생각하다", "verb", "think", "생각해 볼게요", "그 문제에 대해 더 ", ".", "I will ", " about that issue more.", "Polite intention (-아/어 볼게요)"),
        ("믿다", "verb", "believe", "믿어요", "저는 친구의 말을 ", ".", "I ", " what my friend says.", "Polite present (-어요)"),
    ],
    "topik2_travel": [
        ("지도", "noun", "map", "지도를", "우리는 ", " 보고 길을 찾았어요.", "We looked at a ", " to find our way.", "Noun + object marker -를"),
        ("박물관", "noun", "museum", "박물관에서", "저는 ", " 한국의 역사를 배웠어요.", "I learned about Korean history at the ", ".", "Noun + location marker -에서"),
        ("역사", "noun", "history", "역사를", "그 ", " 잘 알면 여행이 더 재미있어요.", "Knowing the ", " makes the trip more interesting.", "Noun + object marker -를"),
        ("관광객", "noun", "tourists", "관광객이", "여름에는 이 도시에 ", " 많이 와요.", "Many ", " visit this city in summer.", "Noun + subject marker -이"),
        ("구경하다", "verb", "looked around", "구경했어요", "저는 시장을 천천히 ", ".", "I slowly ", " the market.", "Polite past (-했어요)"),
        ("떠나다", "verb", "left", "떠났어요", "우리는 아침 일찍 서울을 ", ".", "We ", " Seoul early in the morning.", "Polite past (-났어요)"),
        ("돌아오다", "verb", "came back", "돌아왔어요", "저는 밤늦게 숙소로 ", ".", "I ", " to my lodging late at night.", "Polite past (-왔어요)"),
        ("거리", "noun", "street", "거리는", "서울의 이 ", " 밤에도 사람이 많아요.", "This ", " in Seoul is busy even at night.", "Noun + topic marker -는"),
        ("기념품", "noun", "souvenir", "기념품을", "저는 여행지에서 작은 ", " 샀어요.", "I bought a small ", " at the destination.", "Noun + object marker -을"),
        ("지역", "noun", "region", "지역의", "이 ", " 음식은 다른 곳과 조금 달라요.", "The food in this ", " is a little different from elsewhere.", "Noun + possessive marker -의"),
    ],
}

packs = []
cards = []
for pack_id, title, level, topic, entries in PACKS:
    entries = entries + TOPIC_EXTENSIONS.get(pack_id, [])
    packs.append({"id": pack_id, "title": title, "level": level, "topic": topic,
                  "pack_type": "topik", "source_label": ("TOPIK Guide beginner vocabulary list; original sentences" if level.startswith("TOPIK I") else "Common Korean vocabulary reference; TOPIK II-oriented selection, original sentences"),
                  "source_url": TOPIK_SOURCE if level.startswith("TOPIK I") else TOPIK2_SOURCE,
                  "description": ("Topic-based beginner word selection. This is a curated study list, not an official exhaustive TOPIK list." if level.startswith("TOPIK I") else "Intermediate topic selection for TOPIK II practice, cross-referenced with common Korean vocabulary. It is not an official TOPIK II word list.")})
    for idx, (lemma, pos, target_en, answer, ko_pre, ko_post, en_pre, en_post, answer_form) in enumerate(entries, 1):
        source = ko_pre + answer + ko_post
        translation = en_pre + target_en + en_post
        cards.append({"id": f"{pack_id}_{idx:02d}", "pack_id": pack_id, "card_type": "context",
                      "target": lemma, "part_of_speech": pos, "target_translation": target_en,
                      "prompt": ko_pre + "___" + ko_post, "source_sentence": source,
                      "translation": translation, "answer": answer,
                      "base_form": f"{lemma} ({pos})", "answer_form": answer_form,
                      "explanation": "",
                      "source_label": "Original contextual sentence", "source_url": next(p["source_url"] for p in packs if p["id"] == pack_id)})

THEMES = [
    ("theme_kpop", "K-pop fandom words", "K-pop & fandom",
     "Kfluent K-pop vocabulary list; original sentences", "https://kfluent.com/korean-kpop-words/",
     "Fan vocabulary in original sentences. Register and fandom-specific meanings are shown on the source page.", [
        ("최애", "noun", "bias", "최애는", "제 ", " BTS의 지민이에요.", "My ", " is Jimin from BTS.", "Noun + topic marker -는"),
        ("입덕하다", "verb", "became a fan", "입덕했어요", "친구는 이 무대를 보고 그 그룹에 ", ".", "My friend ", " of the group after seeing this performance.", "Polite past (-했어요)"),
        ("덕질", "noun", "fandom activities", "덕질을", "저는 주말마다 좋아하는 그룹의 ", " 해요.", "I do ", " for my favorite group on weekends.", "Noun + object marker -을"),
        ("직캠", "noun", "fancam", "직캠을", "콘서트가 끝난 뒤에 지민의 ", " 다시 봤어요.", "I watched Jimin's ", " again after the concert.", "Noun + object marker -을"),
        ("컴백", "noun", "comeback", "컴백이", "그룹의 ", " 다음 달로 정해졌어요.", "The group's ", " is scheduled for next month.", "Noun + subject marker -이"),
        ("응원봉", "noun", "lightstick", "응원봉을", "공연이 시작되자 관객들이 ", " 켰어요.", "When the concert began, the audience turned on their ", ".", "Noun + object marker -을"),
        ("팬덤", "noun", "fandom", "팬덤이", "이 그룹은 여러 나라에 큰 ", " 있어요.", "This group has a large ", " in many countries.", "Noun + subject marker -이"),
        ("데뷔", "noun", "debut", "데뷔", "그 그룹의 ", " 무대가 큰 화제가 됐어요.", "The group's ", " stage became a big topic.", "Noun (unchanged)"),
        ("막내", "noun", "youngest member", "막내는", "우리 그룹의 ", " 춤을 잘 춰요.", "The ", " in our group is a good dancer.", "Noun + topic marker -는"),
        ("앨범", "noun", "album", "앨범에", "새 ", " 열두 곡이 들어 있어요.", "The new ", " has twelve songs on it.", "Noun + location marker -에"),
    ]),
    ("theme_kdrama", "K-drama vocabulary", "K-drama & screen", 
     "Just Study Korean drama vocabulary guide; original sentences", "https://juststudykorean.com/%F0%9F%8E%AC-k-drama-in-korean-100-must-know-korean-drama-vocabulary-phrases-for-every-fan/",
     "Production and story vocabulary for talking about Korean dramas; example sentences are original.", [
        ("에피소드", "noun", "episode", "에피소드의", "이번 ", " 결말이 정말 놀라웠어요.", "The ending of this ", " really surprised me.", "Noun + possessive marker -의"),
        ("시즌", "noun", "season", "시즌은", "새 ", " 다음 달에 공개돼요.", "The new ", " will be released next month.", "Noun + topic marker -은"),
        ("장면", "noun", "scene", "장면에서", "마지막 ", " 눈물이 났어요.", "I cried during the final ", ".", "Noun + location marker -에서"),
        ("대본", "noun", "script", "대본을", "배우들은 촬영 전에 ", " 함께 읽어요.", "The actors read the ", " together before filming.", "Noun + object marker -을"),
        ("배우", "noun", "actor", "배우는", "그 ", " 새 드라마에서 의사 역할을 맡았어요.", "The ", " plays a doctor in the new drama.", "Noun + topic marker -는"),
        ("감독", "noun", "director", "감독은", " ", " 촬영 전에 배우들과 장면을 연습해요.", "The ", " rehearses scenes with the actors before filming.", "Noun + topic marker -은"),
        ("작가", "noun", "writer", "작가가", "드라마 ", " 다음 회에 새로운 인물을 소개했어요.", "The drama's ", " introduced a new character in the next episode.", "Noun + subject marker -가"),
        ("예고편", "noun", "trailer", "예고편이", "새 드라마 ", " 어제 공개됐어요.", "The new drama's ", " was released yesterday.", "Noun + subject marker -이"),
        ("결말", "noun", "ending", "결말을", "저는 예상하지 못한 ", " 보고 놀랐어요.", "I was surprised by the unexpected ", ".", "Noun + object marker -을"),
        ("주인공", "noun", "main character", "주인공이", "이 드라마에서는 ", " 친구를 찾으러 서울로 떠나요.", "In this drama, the ", " leaves for Seoul to find a friend.", "Noun + subject marker -이"),
    ]),
    ("theme_slang", "Everyday Korean slang", "Slang & chat", 
     "90 Day Korean 2026 slang guide; register labels retained; original sentences", "https://www.90daykorean.com/korean-slang/",
     "Informal language only. Several items are internet slang; 존맛 is vulgar slang and should be avoided at work or with elders.", [
        ("대박", "interjection", "incredible", "대박이었어요", "콘서트 마지막 무대가 정말 ", ".", "The final stage at the concert was ", ".", "Informal spoken slang"),
        ("헐", "interjection", "Whoa", "헐", "", ", 이 카페는 새벽까지 열어요?", "", ", is this café open until dawn?", "Informal reaction; casual conversation"),
        ("꿀잼", "noun/slang", "so much fun", "꿀잼이었어요", "친구가 추천한 예능 프로그램이 정말 ", ".", "The variety show my friend recommended was ", ".", "Informal slang; casual conversation"),
        ("존맛", "noun/slang", "insanely good", "존맛이야", "이 떡볶이 진짜 ", ".", "This tteokbokki tastes ", ".", "Vulgar slang; avoid formal settings and elders"),
        ("갑분싸", "noun/slang", "suddenly became awkward", "갑분싸가", "그 농담 뒤에 단체 채팅방 분위기가 ", " 됐어요.", "After that joke, the group chat ", ".", "Informal internet slang"),
        ("혼밥하다", "verb/slang", "ate alone", "혼밥했어요", "오늘은 점심에 ", ".", "I ", " at lunch today.", "Informal slang; polite past ending in this sentence"),
        ("인싸", "noun/slang", "social butterfly", "인싸는", "우리 반 ", " 친구 이름을 다 알아요.", "The ", " in our class knows everyone's name.", "Informal slang; casual conversation"),
        ("아싸", "noun/slang", "outsider", "아싸라고", "그는 모임에서 말이 적어서 스스로 ", " 농담했어요.", "He joked that he was an ", " because he was quiet at the gathering.", "Informal slang; casual conversation"),
        ("ㅋㅋㅋ", "texting expression", "lol", "ㅋㅋㅋ", "친구가 보낸 짤이 너무 웃겨서 ", "라고 답했어요.", "The meme was so funny that I replied with ", ".", "Texting only; informal"),
        ("ㄱㅅ", "texting abbreviation", "thx", "ㄱㅅ", "도와줘서 고맙다고 메시지에 ‘", "’라고 썼어요.", "I sent '", "' in a message to thank them for the help.", "Texting abbreviation; informal"),
    ]),
    ("theme_onomatopoeia", "Korean sound & motion words", "Onomatopoeia & mimetics",
     "TOPIK GUIDE onomatopoeia and mimetic-word list; original sentences", "https://www.topikguide.com/ultimate-list-of-korean-onomatopoeia-and-mimetic-words/",
     "Sound-symbolic and mimetic words practiced in short everyday contexts; meanings are context dependent.", [
        ("두근두근", "mimetic adverb", "pounding", "두근두근", "발표 결과를 기다리며 가슴이 ", " 뛰었어요.", "My heart was ", " as I waited for the presentation result.", "Mimetic adverb (unchanged)"),
        ("멍멍", "onomatopoeia", "woof, woof", "멍멍", "강아지가 문 앞에서 ", " 짖었어요.", "The puppy barked at the door: ", ".", "Animal sound (unchanged)"),
        ("야옹", "onomatopoeia", "meowed", "야옹", "고양이가 배고픈지 ", " 울었어요.", "The cat ", " as if it were hungry.", "Animal sound (unchanged)"),
        ("딩동", "onomatopoeia", "ding-dong", "딩동", "초인종이 ", " 울려서 문을 열었어요.", "The doorbell went ", ", so I opened the door.", "Sound word (unchanged)"),
        ("똑똑", "onomatopoeia", "tap-tap", "똑똑", "누군가 문을 ", " 두드렸어요.", "I heard a ", " at the door.", "Sound word (unchanged)"),
        ("반짝반짝", "mimetic adverb", "sparkle", "반짝반짝", "별이 밤하늘에서 ", " 빛나요.", "Stars ", " in the night sky.", "Mimetic adverb (unchanged)"),
        ("솔솔", "mimetic adverb", "gently", "솔솔", "창문으로 시원한 바람이 ", " 불어요.", "A cool breeze is blowing ", " through the window.", "Mimetic adverb (unchanged)"),
        ("주룩주룩", "mimetic adverb", "steadily", "주룩주룩", "비가 ", " 내려서 길이 젖었어요.", "The rain fell ", ", leaving the road wet.", "Mimetic adverb (unchanged)"),
        ("따끈따끈하다", "adjective", "piping hot", "따끈따끈해요", "갓 구운 빵이 아직 ", ".", "Freshly baked bread is still ", ".", "Polite present (-해요)"),
        ("깔깔", "mimetic adverb", "laughed heartily", "깔깔", "아이들은 그 이야기를 듣고 ", " 웃었어요.", "The children ", " when they heard the story.", "Mimetic adverb (unchanged)"),
    ]),
]

for pack_id, title, topic, source_label, source_url, description, entries in THEMES:
    packs.append({"id": pack_id, "title": title, "level": "Themed · intermediate", "topic": topic,
                  "pack_type": "theme", "source_label": source_label, "source_url": source_url,
                  "description": description})
    for idx, (lemma, pos, target_en, answer, ko_pre, ko_post, en_pre, en_post, answer_form) in enumerate(entries, 1):
        source = ko_pre + answer + ko_post
        translation = en_pre + target_en + en_post
        cards.append({"id": f"{pack_id}_{idx:02d}", "pack_id": pack_id, "card_type": "context",
                      "target": lemma, "part_of_speech": pos, "target_translation": target_en,
                      "prompt": ko_pre + "___" + ko_post, "source_sentence": source,
                      "translation": translation, "answer": answer,
                      "base_form": f"{lemma} ({pos})", "answer_form": answer_form,
                      "explanation": "", "source_label": "Original contextual sentence", "source_url": source_url})

MUSIC = {
    "BTS": {
        "catalog": "https://bts.ibighit.com/eng/discography/",
        "songs": [
            ("Spring Day", "보고 싶다", "miss", "보고 싶다", "", " 이렇게 말하니까 더 보고 싶다.", "I ", " you; saying it makes me miss you even more.", "보고 싶어요", "요즘은 고향 친구들을 자주 ", ".", "These days I often ", " my friends from home.", "Polite desire expression (-고 싶어요)"),
            ("Fake Love", "완벽하다", "perfect", "완벽하길", "사랑이 사랑만으로 ", ".", "I hope love can be ", " simply by being love.", "완벽해요", "이 계획은 준비가 잘되어서 거의 ", ".", "The plan is nearly ", " because it is well prepared.", "Polite present (-해요)"),
            ("Boy With Luv", "삶", "life", "삶은", "널 알게 된 이후 내 ", " 온통 너야.", "Since I met you, my ", " has been all about you.", "삶이", "저는 가족과 함께하는 ", " 가장 소중해요.", "The ", " I share with my family is most precious.", "Noun + subject marker -이"),
            ("Life Goes On", "하루", "day", "하루가", " ", " 돌아오겠지 또 아무 일도 없단 듯이.", "A new ", " will come around again, as if nothing happened.", "하루가", "바쁜 ", " 끝나면 책을 읽어요.", "When a busy ", " ends, I read a book.", "Noun + subject marker -가"),
            ("DNA", "우연", "coincidence", "우연이", "이 모든 건 ", " 아니니까.", "None of this is a ", ".", "우연은", "우리는 이 만남이 ", " 아니라고 생각해요.", "We do not think this meeting is a ", ".", "Noun + topic marker -은"),
            ("IDOL", "좋다", "good", "좋다", "얼쑤 ", ".", "Eolssu, that's ", ".", "좋아요", "새로 연 카페의 분위기가 참 ", ".", "The atmosphere at the new café is really ", ".", "Polite present (-아요)"),
            ("Black Swan", "뛰다", "beat", "뛰지 않는대", "심장이 ", ".", "They say the heart no longer ", "s.", "뛰어요", "운동을 시작하면 심장이 더 빨리 ", ".", "When I start exercising, my heart ", "s faster.", "Polite present (-어요)"),
            ("Run BTS", "달리다", "run", "달려라", "끝까지 ", " 방탄.", " ", " to the end, Bangtan.", "달려요", "아침마다 공원에서 삼십 분씩 ", ".", "I ", " for thirty minutes in the park every morning.", "Polite present (-어요)"),
            ("Fire", "불타오르다", "burn", "불타오르네", "불타오르네 불타오르네 ", ".", "It burns, it burns; it will ", " again.", "불타올라요", "조명 아래에서 축제 분위기가 ", ".", "Under the lights, the festival mood starts to ", " with excitement.", "Polite present (-아요)"),
            ("No More Dream", "꿈", "dream", "꿈이", "니 ", " 뭐니.", "What is your ", "?", "꿈은", "요즘 제 ", " 한국에서 일하는 거예요.", "These days my ", " is to work in Korea.", "Noun + topic marker -은"),
        ],
    },
    "Stray Kids": {
        "catalog": "https://straykids.jype.com/discography",
        "songs": [
            ("God's Menu", "비비다", "mix", "비벼", "", " 비벼 네 손님!", "", "Mix it, mix it, customer!", "비벼요", "그릇에 담은 채소와 양념을 잘 ", ".", "I ", " the vegetables and seasoning together in a bowl.", "Polite present (-어요)"),
            ("Back Door", "암호", "password", "암호는", "", " 열려라 참깨!", "The ", " is ‘open sesame.’", "암호는", "공연장에 들어갈 때 필요한 ", " 세 글자예요.", "The ", " you need to enter the venue has three characters.", "Noun + topic marker -는"),
            ("Thunderous", "소리꾼", "performer", "소리꾼", "우린 ", "!", "We are ", "s!", "소리꾼은", "무대 위에서 ", " 관객을 즐겁게 해요.", "On stage, a ", " entertains the audience.", "Noun + topic marker -은"),
            ("MANIAC", "힘", "energy", "힘", "정상인 척 다들 ", " 좀 빼.", "Everyone, save some ", ".", "힘을", "계단을 오르느라 ", " 다 썼어요.", "I used all my ", " climbing the stairs.", "Noun + object marker -을"),
            ("CASE 143", "사건", "case", "사건", "잊지 못할 ", "!", "An unforgettable ", "!", "사건이", "그 ", " 아직도 뉴스에 나와요.", "That ", " is still in the news.", "Noun + subject marker -이"),
            ("Hellevator", "삶", "life", "삶은", "내 ", " 밑바닥 낭떠러지.", "My ", " is at rock bottom.", "삶을", "건강한 ", " 위해 매일 운동해요.", "I exercise every day for a healthy ", ".", "Noun + object marker -을"),
            ("MIROH", "미로", "maze", "미로", "Run through the ", " like a beast.", "Run through the ", " like a beast.", "미로를", "우리는 복잡한 ", " 지나 출구를 찾았어요.", "We found the exit after passing through a complicated ", ".", "Noun + object marker -를"),
            ("Levanter", "의심하다", "doubt", "의심", "", " 따윈 해본 적도 없었어.", "I had never had any ", ".", "의심하지 않아요", "그는 제 계획을 ", ".", "He does not ", " my plan.", "Polite negative present (-지 않아요)"),
            ("S-Class", "빛나다", "shine", "빛나는", "", " 쪽이 되는 게 훨씬 폼 잡기 편해.", "It is much cooler to be the one who ", ".", "빛나요", "밤하늘에서 별이 아주 밝게 ", ".", "Stars in the night sky ", " very brightly.", "Polite present (해요체)"),
            ("Chk Chk Boom", "과식하다", "overindulged", "과식했지", "승리를 너무 ", " 배불러.", "I ", " in victories and got full.", "과식했어요", "어제 저녁에 ", ".", "I ", " at dinner last night.", "Polite past (-았어요/었어요)"),
        ],
    },
    "TXT": {
        "catalog": "https://txt.ibighit.com/eng/discography/",
        "songs": [
            ("CROWN", "뿔", "horn", "뿔이", "머리에 ", " 자라났어.", "A ", " grew on my head.", "뿔이", "사슴의 ", " 크고 멋있어요.", "The deer's ", " are large and beautiful.", "Noun + subject marker -이"),
            ("Run Away", "승강장", "platform", "승강장에서", "9와 4분의 3 ", " 너를 기다려.", "I am waiting for you at the nine-and-three-quarters ", ".", "승강장에서", "기차를 타려고 ", " 친구를 만났어요.", "I met my friend at the ", " to take the train.", "Noun + location marker -에서"),
            ("Blue Hour", "하늘", "sky", "하늘에서", "5시 53분의 ", " 발견한 너와 나.", "You and I found in the ", " at 5:53.", "하늘이", "오늘 ", " 맑아서 산책하기 좋아요.", "The ", " is clear today, so it is nice for a walk.", "Noun + subject marker -이"),
            ("0X1=LOVESONG", "문제", "problem", "문제투성이", "난 ", " Love sick.", "I'm full of ", ", lovesick.", "문제가", "이 수학 ", " 생각보다 어려워요.", "This math ", " is harder than I expected.", "Noun compound + context subject marker -가"),
            ("Anti-Romantic", "미안하다", "sorry", "미안해", " ", " 난 안 될 것 같아.", "I'm ", "; I don't think I can do it.", "미안해요", "약속에 늦어서 정말 ", ".", "I am really ", " for being late to our appointment.", "Polite apology (-해요)"),
            ("Can't You See Me?", "세계", "world", "세계가", " ", " 불타버린 밤.", "The night the ", " burned down.", "세계는", "우리가 사는 ", " 조금씩 달라지고 있어요.", "The ", " we live in is gradually changing.", "Noun + topic marker -는"),
            ("LO$ER=LO♡ER", "웃다", "laugh", "웃어", "미친 듯 크게 ", ".", "Laugh loudly as if you have gone crazy.", "", "웃어요", "친구의 농담을 듣고 모두 크게 ", ".", "Everyone ", " loudly after hearing my friend's joke.", "Polite present (-어요)"),
            ("Sugar Rush Ride", "달콤하다", "sweet", "달콤한", " ", " 그 맛.", "That ", " taste.", "달콤해요", "이 케이크는 크림이 부드럽고 ", ".", "This cake has soft cream and tastes ", ".", "Polite present (-해요)"),
            ("Deja Vu", "약속", "promise", "약속의", "You and I ", " 별빛 아래서.", "You and I, under the starlight of our ", ".", "약속을", "우리는 지난주에 한 ", " 꼭 지켰어요.", "We kept the ", " we made last week.", "Noun + possessive marker -의"),
            ("Chasing That Feeling", "시간", "time", "시간", "길을 잃었던 나의 ", ".", "The ", " when I was lost.", "시간이", "시험을 준비할 ", " 부족해요.", "There isn't enough ", " to prepare for the exam.", "Noun + subject marker -이"),
        ],
    },
    "SEVENTEEN": {
        "catalog": "https://www.pledis.co.kr/artist/detail/seventeen/",
        "songs": [
            ("Pretty U", "예쁘다", "pretty", "예쁘다", "너 ", ".", "You're so ", ".", "예뻐요", "오늘 피어난 꽃이 정말 ", ".", "The flowers that bloomed today are really ", ".", "Polite present (ㅡ deletion)"),
            ("Very NICE", "아주", "very", "아주", " ", " NICE.", " ", " nice.", "아주", "이 빵은 ", " 부드러워요.", "This bread is ", " soft.", "Adverb (unchanged)"),
            ("Don't Wanna Cry", "울다", "cry", "울고 싶지 않아", "난 ", ".", "I don't want to ", ".", "울고 싶지 않아요", "영화를 보고도 오늘은 ", ".", "Even after the movie, I do not want to ", " today.", "Polite negative desire (-고 싶지 않아요)"),
            ("CLAP", "박수", "applause", "박수", "이때다 싶으면 쳐 ", ".", "When the moment feels right, give a round of ", ".", "박수를", "공연이 끝나자 관객들이 큰 ", " 보냈어요.", "When the show ended, the audience gave loud ", ".", "Noun + object marker -를"),
            ("Thanks", "고맙다", "thankful", "고맙다", "고맙다 또 ", " 뿐이지만.", "I'm thankful; that's all I can say.", "", "고마워요", "도와줘서 정말 ", ".", "I am really ", " for your help.", "Polite thanks (-워요)"),
            ("Oh My!", "어찌하다", "what can I do", "어쩌나", "네가 좋은 걸 ", ".", "I like you, but what can I do?", "", "어쩌죠", "버스를 놓쳤는데 이제 ", "?", "I missed the bus—what can I do now?", "", "Fixed wondering expression; polite question in context"),
            ("Home", "집", "home", "집이", "내 마음 편히 기댈 ", " 없어.", "There is no ", " where I can rest my heart.", "집이", "긴 여행 뒤에 돌아갈 ", " 가장 편해요.", "The ", " I return to after a long trip is the most comfortable.", "Noun + subject marker -이"),
            ("Fear", "독", "poison", "독이", " ", " 번져 가기 전에.", "Before the ", " spreads.", "독이", "뱀에 물린 뒤 몸에 ", " 퍼지기 전에 병원에 갔어요.", "After a snakebite, I went to the hospital before the ", " spread through my body.", "Noun + subject marker -이"),
            ("Left & Right", "위", "up", "위로", "하늘 향해 ", " 위로 위로 위로.", "Toward the sky, ", " up, up, up.", "위로", "계단을 따라 ", " 올라가면 출구가 있어요.", "If you go ", " the stairs, there is an exit.", "Direction adverb (unchanged)"),
            ("God of Music", "음악", "music", "음악의", "우리는 ", " 신.", "We are the gods of ", ".", "음악을", "저녁에는 조용한 ", " 들으며 책을 읽어요.", "In the evening, I read while listening to quiet ", ".", "Noun + object marker -을"),
        ],
    },
}

GROUPS = {
    "BTS": ["Spring Day", "Fake Love", "Boy With Luv", "Life Goes On", "DNA", "IDOL", "Black Swan", "Run BTS", "Fire", "No More Dream"],
    "Stray Kids": ["God's Menu", "Back Door", "Thunderous", "MANIAC", "CASE 143", "Hellevator", "MIROH", "Levanter", "S-Class", "Chk Chk Boom"],
    "TXT": ["CROWN", "Run Away", "Blue Hour", "0X1=LOVESONG", "Anti-Romantic", "Can't You See Me?", "LO$ER=LO♡ER", "Sugar Rush Ride", "Deja Vu", "Chasing That Feeling"],
    "SEVENTEEN": ["Pretty U", "Very NICE", "Don't Wanna Cry", "CLAP", "Thanks", "Oh My!", "Home", "Fear", "Left & Right", "God of Music"],
}

def lyric_url(artist, title):
    from urllib.parse import quote_plus
    return "https://music.bugs.co.kr/search/integrated?q=" + quote_plus(f"{artist} {title}")

MUSIC_POS = {
    "보고 싶다": "fixed expression", "완벽하다": "adjective", "삶": "noun", "하루": "noun", "우연": "noun",
    "좋다": "adjective", "뛰다": "verb", "달리다": "verb", "불타오르다": "verb", "꿈": "noun",
    "비비다": "verb", "문": "noun", "암호": "noun", "소리꾼": "noun", "힘": "noun", "사건": "noun", "괴롭히다": "verb",
    "승리": "noun", "찾다": "verb", "특별하다": "adjective", "빛나다": "verb", "뿔": "noun",
    "승강장": "noun", "하늘": "noun", "문제": "noun", "미안하다": "adjective", "세상": "noun", "세계": "noun",
    "웃다": "verb", "달콤하다": "adjective", "약속": "noun", "불꽃": "noun", "예쁘다": "adjective",
    "아주": "adverb", "울다": "verb", "박수": "noun", "고맙다": "adjective", "어찌하다": "fixed expression",
    "집": "noun", "숨": "noun", "왼쪽": "noun", "음악": "noun", "오래전": "noun",
    "미로": "noun", "시간": "noun", "독": "noun", "위": "adverb",
    "의심하다": "verb", "과식하다": "verb",
}

for artist, info in MUSIC.items():
    for song in info["songs"]:
        (title, lemma, target_en, lyric_answer, lyric_pre, lyric_post, lyric_en_pre, lyric_en_post,
         context_answer, context_pre, context_post, context_en_pre, context_en_post, context_form) = song
        # A few rows use a non-space-leading or non-space-trailing fragment; normalize only joins,
        # never Korean spelling inside the excerpt.
        pack_id = "music_" + artist.lower().replace(" ", "_") + "_" + "".join(ch.lower() if ch.isalnum() else "_" for ch in title).strip("_")
        source_url = lyric_url(artist, title)
        packs.append({"id": pack_id, "title": f"{artist} · {title}", "level": "Music · Korean lyrics",
                      "topic": artist, "pack_type": "music", "artist": artist, "song": title,
        "source_label": "Lyric lookup; brief excerpt for study",
                      "source_url": source_url, "catalog_url": info["catalog"],
                      "description": "One short lyric cloze plus one original context sentence for the same target word."})
        lyric_sentence = lyric_pre + lyric_answer + lyric_post
        lyric_translation = lyric_en_pre + target_en + lyric_en_post
        context_sentence = context_pre + context_answer + context_post
        context_translation = context_en_pre + target_en + context_en_post
        pos = MUSIC_POS[lemma]
        base_form = f"{lemma} ({pos})"
        for card_type, sentence, translation, answer, answer_form, source_label in [
            ("lyric", lyric_sentence, lyric_translation, lyric_answer, "Original lyric wording", f"{artist} · {title} · brief lyric excerpt"),
            ("context", context_sentence, context_translation, context_answer, context_form, "Original contextual sentence"),
        ]:
            if answer not in sentence:
                raise ValueError(f"Answer missing from source sentence: {pack_id} {card_type}")
            cards.append({"id": f"{pack_id}_{card_type}", "pack_id": pack_id, "card_type": card_type,
                          "target": lemma, "part_of_speech": pos, "target_translation": target_en,
                          "prompt": sentence.replace(answer, "___", 1), "source_sentence": sentence,
                          "translation": translation, "answer": answer, "base_form": base_form,
                          "answer_form": answer_form, "explanation": "",
                          "source_label": source_label, "source_url": source_url, "artist": artist, "song": title,
                          "catalog_url": info["catalog"]})

for song_group, names in GROUPS.items():
    actual = [p["song"] for p in packs if p.get("artist") == song_group]
    if actual != names:
        raise ValueError(f"Song list mismatch for {song_group}: {actual}")

for card in cards:
    if card["prompt"].count("___") != 1:
        raise ValueError(f"Expected exactly one blank in {card['id']}")
    if card["prompt"].replace("___", card["answer"], 1) != card["source_sentence"]:
        raise ValueError(f"Answer does not reconstruct source in {card['id']}")
    if card["target_translation"].casefold() not in card["translation"].casefold():
        raise ValueError(f"Target translation absent from translation in {card['id']}: {card['target_translation']}")
    if card["card_type"] == "lyric" and len(card["source_sentence"].split()) > 10:
        raise ValueError(f"Lyric fragment over 10 word tokens: {card['id']}")

if OUT.exists():
    existing = json.loads(OUT.read_text(encoding="utf-8"))
    existing_count = len(existing.get("cards", []))
    if existing_count > len(cards):
        raise RuntimeError(
            f"Refusing to overwrite the expanded vocabulary seed ({existing_count} cards) "
            f"with the legacy generator output ({len(cards)} cards)."
        )
OUT.write_text(json.dumps({"schema_version": 1, "source_note": "TOPIK word selection based on public study lists; original sentences are written for Mochi Hangul. Music snippets are kept under 10 whitespace-separated tokens per track.", "packs": packs, "cards": cards}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(packs)} packs and {len(cards)} cards to {OUT}")
