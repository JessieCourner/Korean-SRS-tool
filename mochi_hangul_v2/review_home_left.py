import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf-8'))
home=[
'What am I supposed to do?','If I do not have you,','my heart stops like an old robot, and I am always cold.','What are we supposed to do?','If you do not have me,','you would struggle just like me. What are we supposed to do?','Baby, I want to preserve','the warmth between us just as it is.','No matter who it is,','they cannot undo the bond between us.','Tell me, my dear, tell me, my dear.','Say something to me, from within me.','I am struggling inside your heart.','Suddenly I feel afraid.','What can I do?','If I do not have you,','I have no home where I can comfortably lean and rest.','There is an empty space inside me reserved for you.','In a way,','it may be a little difficult,','but I am standing right here, anytime.','You can feel at ease.','You can cry here; you can come here.','I think I have already','gotten ahead of your feelings now.','That does not mean your feelings are small.','It is still cold outside; even the tip of my nose is freezing.','Memories bring us closer even from far away.','If a hole opens in your heart, I will cover it with both hands.','Reach out even an empty hand; I will fill it.','Tell me, my dear, tell me, my dear.','Say something to me, from within me.','I am inside your heart.','I am struggling there.','Suddenly I feel afraid.','What can I do?','If I do not have you,','I have no home where I can comfortably lean and rest.','There is an empty space inside me reserved for you.','In a way,','it may be a little difficult,','but I am standing right here, anytime.','You can feel at ease.','I do not want to let you go like this.','I do not want to be scared every day with a broken heart.','I am a place where you can belong.','You are a place where I can belong.','A place where you can cry, and where I can cry too.'
]
left=[
'One, two, three, four.','Do not forget when you stand at the starting line.','Open your eyes wide and lift your head.','Once you kneel down and gather momentum,','I want to get ahead first, baby.','Call your friends; I am going to celebrate.','Nobody can stop us; we party today.','Run toward the climax, waving your tail.','You know it, buffalo.','Run along the red carpet.','Tomorrow I will be even more successful.','Even through the atmosphere,','break through, break through, break through.','Smile some more.','Twenty more times; this is','a celebration when we cross the finish line.','With a refreshing burst.','When you feel good, without worrying.','More, more confidently; follow me.','I will not listen to what anyone says.','They chatter on about something else.','They go on and on; it is noisy, so hush.','What we need','is a sweet tomorrow, after all.','Toss someone into the air in celebration, toward the sky.','Up, up, up, up.','Even if we keep running and running,','when on earth will we overtake them?','Just running is enough.','So what am I supposed to do?','Not running is also an option.','So what? It does not matter.','Smile some more.','Twenty more times; this is','a celebration when we cross the finish line.','With a refreshing burst.','When you feel good, without worrying.','More, more confidently; follow me.','We are not alone.','Because we are together.','There is no need to be afraid.','We are not alone; we are together.','So we run without worrying again.','A celebration full of passion.','Count to four and go.','Let us go together, without worrying.','More, more confidently; follow me.','One, two, three, four.','Two, two, three, four.','Three, two, three, four.','Four, two, three, four.'
]
assert len(home)==48,len(home)
assert len(left)==51,len(left)
for idx,remove_idx,translations in [(14,22,home),(15,17,left)]:
 s=d[idx];s['lines'].pop(remove_idx)
 for w in s['words']:
  if w['line']>remove_idx:w['line']-=1
 assert len(s['lines'])==len(translations)
 for line,en in zip(s['lines'],translations):line['en']=en
# Fix word list to avoid partial-word false matches, particles and mismatched sense.
def update(i,old,**kwargs):
 for w in d[i]['words']:
  if w['lemma']==old:
   w.update(kwargs);return
 raise ValueError((i,old))
update(14,'발',lemma='발버둥치다',surface='발버둥',line=12,gloss='to struggle; to flail',pos='verb',example='물속에서 발버둥치지 말고 침착하세요.',example_en='Do not thrash about in the water; stay calm.')
update(14,'비',lemma='비다',surface='비어',line=17,gloss='to be empty',pos='verb',example='회의실이 지금 비어 있어요.',example_en='The meeting room is empty right now.')
update(14,'끝',lemma='추억',surface='추억',line=27,gloss='memory; cherished recollection',pos='noun',example='여행에서 좋은 추억을 만들었어요.',example_en='I made wonderful memories on the trip.')
update(14,'말',lemma='간직하다',surface='간직하고',line=7,gloss='to keep; to treasure',pos='verb',example='그 편지를 오랫동안 간직했어요.',example_en='I kept that letter for a long time.')
update(15,'말',lemma='출발선',surface='출발선',line=1,gloss='starting line',pos='noun',example='선수들이 출발선에 섰어요.',example_en='The athletes stood at the starting line.')
update(15,'발',lemma='추진력',surface='추진력',line=3,gloss='driving force; momentum',pos='noun',example='작은 성공이 다음 도전의 추진력이 됐어요.',example_en='A small success became the driving force for the next challenge.')
for i in [14,15]:
 for w in d[i]['words']:
  assert w['surface'] in d[i]['lines'][w['line']]['ko'],(i,w['lemma'],w['surface'])
  assert w['example'] and w['example_en']
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('Done',sum(x['en'] is not None for s in d for x in s['lines']),sum(len(s['lines']) for s in d))
