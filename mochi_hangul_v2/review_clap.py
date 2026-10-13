import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf-8'))
s=next(s for s in d if s['title']=='박수' and s['artist']=='SEVENTEEN')
translations=[
'Applause.','It’s okay, it’s okay; things like this happen all the time.','Things get so tangled up, like earphones in your pocket.','When you get something on your white T-shirt (and then...)','When there’s no balance left on your transit card (at times like that).','Yeah, it always seems to happen on days like these.','You get caught in the rain before you make it home.','You wonder, “Why does this only happen to me?”','You blink, and the weekend is already over.','If you think, “That sounds just like me,”','Come on over, everybody, gather around.','Starting now,','Clap until your hands feel like they’re on fire.','When the moment feels right, clap your hands.','Hey, over there, come this way.','We get excited when we’re together.','Keep clapping until this song is over.','Ooh, clap, clap, clap, clap.','Ooh, clap, clap, clap, clap.','No matter how hard you try, nothing works out—not for you or for anyone else.','If nothing works, even a spell that does nothing will do.','Kim Su-han-mu, a turtle and a crane—','Three thousand years and Dongbangsak—words from a traditional tongue-twister.','You know, there are times like that.','I mean, times when I feel so small.','I did everything I was told to do, but','I’m still just watching how everyone else reacts.','You wonder, “Why does this only happen to me?”','You blink, and the weekend is already over.','If you think, “That sounds just like me,”','Come on over, everybody, gather around.','Starting now,','Clap until your hands feel like they’re on fire.','When the moment feels right, clap your hands.','Hey, over there, come this way.','We get excited when we’re together.','Keep clapping until this song is over.','Ooh, clap, clap, clap, clap.','Ooh, clap, clap, clap, clap.','Ooh, clap, clap, clap, clap.','Just for today, summon up your courage.','Pull the blanket over yourself and shout (one more time).','Let’s clap until our hands burn.','This song is coming to an end—clap!','Hey, over there, come this way.','We get excited when we’re together.','Everyone together, stand up and give a round of applause.','Ooh, clap, clap, clap, clap.','Ooh, clap, clap, clap, clap.'
]
assert len(translations)==len(s['lines'])
for l,t in zip(s['lines'],translations):l['en']=t
entries=[
('꼬이다','to get tangled; to go wrong','verb',2,'꼬인','일이 자꾸 꼬여서 계획을 바꿨어요.','Things kept going wrong, so I changed my plans.'),
('묻다','to get on; to stain (a surface)','verb',3,'묻을','셔츠에 커피가 묻었어요.','I got coffee on my shirt.'),
('잔고','balance (of an account or card)','noun',4,'잔고','교통카드 잔고를 확인했어요.','I checked the balance on my transit card.'),
('깜빡하다','to blink; to forget briefly','verb',8,'깜빡','눈을 깜빡하는 사이에 버스가 지나갔어요.','The bus passed by in the blink of an eye.'),
('모이다','to gather','verb',10,'모여','친구들이 공원에 모였어요.','My friends gathered at the park.'),
('박수','applause; clapping','noun',12,'박수','공연이 끝나자 관객들이 박수를 쳤어요.','The audience applauded when the performance ended.'),
('어차피','anyway; in any case','adverb',19,'어차피','어차피 늦었으니 천천히 가요.','We are late anyway, so let’s take our time.'),
('눈치','social awareness; reading the situation','noun',26,'눈치','그는 눈치가 빨라서 분위기를 금방 알아챘어요.','He reads the room well and quickly sensed the mood.'),
('용기','courage','noun',40,'용기','용기를 내서 먼저 말을 걸었어요.','I gathered my courage and spoke first.'),
('기립','standing up; rising to one’s feet','noun',46,'기립','관객들이 기립 박수를 보냈어요.','The audience gave a standing ovation.')]
s['words']=[dict(lemma=a,gloss=b,pos=c,line=i,surface=surf,example=ex,example_en=en) for a,b,c,i,surf,ex,en in entries]
for w in s['words']:assert w['surface'] in s['lines'][w['line']]['ko'],w
with open(p,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print('Reviewed',s['title'],len(s['lines']),'lines',len(s['words']),'words')
