import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf8'))
s=d[19]
t='''I used to need a morning wake-up call.
But today my eyes spring wide open!
Maybe it's because today is our date.
Even last night's dream was a good one.
I put on my new shoes,
and when I open the front door and head out,
today's weather looks so much like you.
The road to you becomes a flower-lined path.
If I can glimpse what is in your heart,
my whole body tingles and my heart pounds.
What is this feeling? What do I do?
So nice!
So nice!
This feeling is so nice!
So nice!
Can I ask you something?
Do you think I even dream of you floating around?
Do you think I joined a gym to become a cool guy?
Do you think I'm nervous because this is my first relationship?
You seem to be the answer to every question I have.
Ah, there's something I'm curious about: how are you so pretty?
There's a great restaurant just across the traffic lights.
Today's weather looks so much like you.
The road to you becomes a flower-lined path.
If I can glimpse what is in your heart,
my whole body tingles and my heart pounds.
What is this feeling? What do I do?
What is it? What do I do?
So nice!
So nice!
This feeling is so nice!
So nice!
Some people say
that dating is just dating, and that's the end of it.
If that's so, let the beginning become the end,
let it begin with you and end with me,
like a circle formed by our two clasped hands.
(There is no end to us.)
Right now, the two of us are together forever.
Let's choose not to believe that first love never works out.
I hope we don't lose each other by taking familiarity for granted.
So that this thing called 'us' can be protected.
I'm serious, though this may sound out of the blue.
Today, you see...
So nice!
So nice!
This feeling is so nice!
So nice!
I had such a wonderful day today.
I hope we can have another date soon.
The walk taking you home feels far too short.
Let's meet again tomorrow at this time.'''.splitlines()
assert len(t)==len(s['lines']),(len(t),len(s['lines']))
for l,en in zip(s['lines'],t):l['en']=en
s['words']=[
 dict(lemma='필수',gloss='necessity; essential',pos='noun',line=0,surface='필수',example='이 수업에서는 출석이 필수예요.',example_en='Attendance is mandatory in this class.'),
 dict(lemma='현관문',gloss='front door; entrance door',pos='noun',line=5,surface='현관문',example='나가기 전에 현관문을 잠갔어요.',example_en='I locked the front door before going out.'),
 dict(lemma='닮다',gloss='to resemble; to look like',pos='verb',line=6,surface='닮아',example='그 아이는 아버지를 많이 닮았어요.',example_en='That child looks a lot like their father.'),
 dict(lemma='간질간질하다',gloss='to tingle; to feel ticklish',pos='adjective',line=9,surface='간질간질',example='새 스웨터를 입으니 목이 간질간질해요.',example_en='My neck feels ticklish when I wear the new sweater.'),
 dict(lemma='긴장하다',gloss='to feel nervous; to be tense',pos='verb',line=18,surface='긴장',example='면접 전에 너무 긴장했어요.',example_en='I was very nervous before the interview.'),
 dict(lemma='의문점',gloss='question; point of doubt',pos='noun',line=19,surface='의문점',example='설명을 듣고도 의문점이 남았어요.',example_en='I still had questions after hearing the explanation.'),
 dict(lemma='신호등',gloss='traffic light',pos='noun',line=21,surface='신호등',example='신호등이 초록색으로 바뀌면 건너세요.',example_en='Cross when the traffic light turns green.'),
 dict(lemma='익숙함',gloss='familiarity; being accustomed to something',pos='noun',line=40,surface='익숙함',example='익숙함 때문에 소중한 것을 잊기도 해요.',example_en='Familiarity sometimes makes us forget what is precious.'),
 dict(lemma='뜬금없다',gloss='to be sudden; out of the blue',pos='adjective',line=42,surface='뜬금없',example='갑자기 뜬금없는 질문을 했어요.',example_en='They suddenly asked an out-of-the-blue question.'),
 dict(lemma='데려다주다',gloss='to take someone home; escort someone somewhere',pos='verb',line=50,surface='데려다 주',example='친구를 집까지 데려다줬어요.',example_en='I took my friend home.'),
]
for w in s['words']:
 assert w['surface'] in s['lines'][w['line']]['ko'],w
 assert w['example'] and w['example_en']
json.dump(d,open(p,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print('Saved',s['title'],len(s['lines']),'lines',len(s['words']),'words')
