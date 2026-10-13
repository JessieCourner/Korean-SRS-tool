import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf-8'))
s=next(x for x in d if x['title']=='Spring day')
en=[
'I miss you.','Saying it like this makes me miss you even more.','Even when I look at photos of you all,','I miss you.','Time is so cruel; I hate what we have become.','Even seeing each other’s faces once has become difficult for us.','It is nothing but winter here; winter comes even in August.','My heart races through time, a snow-country train left alone.','I want to hold your hand and go to the other side of the Earth, to end this winter.','How much longing must fall like snow before that spring day comes, my friend?',
'Small things drifting through the empty air,','like dust, like tiny specks of dust.','If I were the snowflakes blowing in the wind,','I could reach you','a little sooner.','Snowflakes are falling.','We are drifting farther apart, little by little.','I miss you.','I miss you.','How long must I wait?','How many more nights must I stay awake?','Will I get to see you?','Will I get to meet you?','After passing through the end of the cold winter,','until spring comes again,','until the flowers bloom,','please stay there a little longer.','Is it you who have changed?','Or is it me who has changed?','I even hate the time passing in this moment.','We have changed, I guess; everyone does.','Yes, I resent you, though you have left.','Not a single day has passed when I forgot you.','Honestly, I miss you, but I will let you go now.','Because that hurts less than blaming you.','I try to blow away the memory of you, cold as it is.','Like smoke, like white smoke.','Even if I say I am erasing you,','the truth is I still cannot let you go.','Snowflakes are falling.','We are drifting farther apart, little by little.','I miss you.','I miss you.','How long must I wait?','How many more nights must I stay awake?','Will I get to see you?','Will I get to meet you?','Morning will come again.','Because no darkness and no season','can last forever.','It looks like the cherry blossoms are blooming.','This winter, too, is coming to an end.','I miss you.','I miss you.','If I wait just a little longer,','if I stay awake just a few more nights,','I will come to see you.','I will come to pick you up.','After passing through the end of the cold winter,','until spring comes again,','until the flowers bloom,','please stay there a little longer.']
assert len(en)==len(s['lines'])
for line,translation in zip(s['lines'],en):line['en']=translation
items=[
('야속하다','to be cruel or heartless','adjective',4,'야속한','그의 차가운 대답이 야속했어요.','His cold reply felt heartless.'),
('그리움','longing; yearning','noun',9,'그리움','오랜 친구에 대한 그리움이 커졌어요.','My longing for an old friend grew.'),
('허공','empty air; midair','noun',10,'허공','그는 허공을 바라봤어요.','He stared into empty space.'),
('떠돌다','to drift; to wander','verb',10,'떠도는','구름이 하늘을 떠돌고 있어요.','Clouds are drifting across the sky.'),
('닿다','to reach; to touch','verb',14,'닿을','손이 선반에 닿지 않아요.','My hand cannot reach the shelf.'),
('머무르다','to stay; to remain','verb',26,'머물러','이곳에 며칠 더 머물 거예요.','I will stay here a few more days.'),
('원망하다','to resent; to blame','verb',34,'원망하','그는 누구도 원망하지 않았어요.','He did not blame anyone.'),
('연기','smoke','noun',36,'연기','창문 밖으로 연기가 보여요.','I can see smoke outside the window.'),
('어둠','darkness','noun',48,'어둠','어둠 속에서 길을 찾았어요.','I found my way in the darkness.'),
('데리러 가다','to go to pick someone up','verb',57,'데리러 갈','퇴근 후에 동생을 데리러 갈게요.','I will go pick up my younger sibling after work.')]
s['words']=[dict(lemma=a,gloss=b,pos=c,line=i,surface=surf,example=ex,example_en=exen) for a,b,c,i,surf,ex,exen in items]
for w in s['words']:assert w['surface'] in s['lines'][w['line']]['ko'],w
with open(p,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print('Spring day complete:',len(en),'lines',len(items),'words')
