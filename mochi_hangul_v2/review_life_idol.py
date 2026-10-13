import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf-8'))
translations={
'Life goes on':[
'One day, the world came to a halt.','Without any warning at all.','Spring knows nothing of waiting.','It came without a hint of consideration.','A street where footprints have been erased.','Here I am, fallen down.','Time goes on alone.','Without even saying sorry.','It looks like rain again today.','I have become completely soaked.','It still will not stop.','I run faster than those dark clouds.','I thought that would do it.','I guess I am only human after all.','It hurts terribly.','A cold given to me by this thing called the world.','Thanks to it, I press rewind, now covered in dust.','Dancing offbeat while still lying where I fell.','When winter comes, let us breathe out.','A breath warmer still.','I cannot see the end.','Is there even an exit?','I cannot lift my feet.','Close your eyes for a moment.','Take my hand here.','Let us run away toward that future.','Another day will come around.','As though nothing had happened.','Another day will fly by.','I will borrow this music to tell you something.','People say the world has completely changed.','Fortunately, what lies between us','still has not changed, even now.','With the familiar word “hello” that marked our beginnings and endings,','let us connect today and tomorrow once more.','Though we have come to a stop, do not hide in the darkness.','Because the light will rise again.','I cannot see the end.','Is there even an exit?','I cannot lift my feet.','Close your eyes for a moment.','Take my hand here.','Let us run away toward that future.','Another day will come around.','As though nothing had happened.','Another day will fly by.'],
'IDOL':[
'Or whatever else you might call me.','Whatever you say, I do not care.','I am free.','Because I have always been myself.','They point fingers at me.','I do not care about it at all.','You, who insult me—','whatever your reason may be.','What on earth are you rambling on about?','I do what I do, so mind your own business.','How wonderful!','What a joyous occasion!','Traditional rhythmic chant (non-lexical syllables).','Traditional rhythmic chant (non-lexical syllables).','Face off, like an idol statue.','Sometimes I become a superhero.','I keep turning your Anpanman around.','Twenty-four hours are not enough.','Confusion is a luxury I cannot afford.','Inside me,','there are dozens, even hundreds, of versions of myself.','Today I greet another new day.','Because all of them are me anyway.','Rather than worrying, I just keep running.','What on earth are you rambling on about?','I do what I do, so mind your own business.','How wonderful!','What a joyous occasion!','Traditional rhythmic chant (non-lexical syllables).','Traditional rhythmic chant (non-lexical syllables).']}
words={
'Life goes on':[
('멈추다','to stop','verb',0,'멈췄','버스가 정류장에서 멈췄어요.','The bus stopped at the bus stop.'),
('예고','advance notice; warning','noun',1,'예고','예고 없이 일정이 바뀌었어요.','The schedule changed without warning.'),
('발자국','footprint','noun',4,'발자국','눈 위에 발자국이 남았어요.','Footprints were left in the snow.'),
('흠뻑','thoroughly; completely (soaked)','adverb',9,'흠뻑','소나기에 옷이 흠뻑 젖었어요.','My clothes got completely soaked in the sudden rain.'),
('먹구름','dark rain cloud','noun',11,'먹구름','하늘에 먹구름이 몰려왔어요.','Dark rain clouds gathered in the sky.'),
('겨우','barely; only (just)','adverb',13,'겨우','기차를 겨우 탔어요.','I barely caught the train.'),
('출구','exit','noun',21,'출구','출구가 어디에 있어요?','Where is the exit?'),
('미래','future','noun',25,'미래','미래를 위해 저축하고 있어요.','I am saving for the future.'),
('전하다','to convey; to tell','verb',29,'전할','그 소식을 가족에게 전했어요.','I told my family the news.'),
('어둠','darkness','noun',35,'어둠','어둠 속에서 불빛이 보였어요.','I saw a light in the darkness.')],
'IDOL':[
('자유롭다','to be free','adjective',2,'자유롭','주말에는 시간이 자유로워요.','My time is flexible on weekends.'),
('손가락질하다','to point fingers at; to condemn','verb',4,'손가락질','남을 손가락질하지 마세요.','Do not point fingers at others.'),
('신경 쓰다','to care about; to pay attention to','verb',5,'신경 쓰','그런 말에 신경 쓰지 마세요.','Do not pay attention to such remarks.'),
('이유','reason','noun',7,'이유','늦은 이유를 설명했어요.','I explained why I was late.'),
('떠들어대다','to chatter noisily; to rant','verb',8,'떠들어대','아이들이 복도에서 떠들어댔어요.','The children chattered noisily in the hallway.'),
('헷갈리다','to get confused','verb',18,'헷갈','두 이름이 자꾸 헷갈려요.','I keep mixing up the two names.'),
('사치','luxury; extravagance','noun',18,'사치','지금은 휴식조차 사치처럼 느껴져요.','Even resting feels like a luxury right now.'),
('맞이하다','to welcome; to greet','verb',21,'맞이해','가족과 함께 새해를 맞이했어요.','I welcomed the new year with my family.'),
('고민','worry; concern','noun',23,'고민','친구에게 고민을 털어놓았어요.','I confided my worries to a friend.'),
('달리다','to run','verb',23,'달리','매일 아침 공원에서 달려요.','I run in the park every morning.')]
}
for song in d:
 title=song['title']
 if title not in translations:continue
 assert len(song['lines'])==len(translations[title]),(title,len(song['lines']),len(translations[title]))
 for line,en in zip(song['lines'],translations[title]):line['en']=en
 song['words']=[dict(lemma=a,gloss=b,pos=c,line=i,surface=s,example=e,example_en=f) for a,b,c,i,s,e,f in words[title]]
 for w in song['words']:assert w['surface'] in song['lines'][w['line']]['ko'],(title,w)
with open(p,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print('Completed Life goes on and IDOL')
