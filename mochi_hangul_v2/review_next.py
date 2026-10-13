import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf-8'))
translations={
'Fake love':[
'As long as it was for you, I','I could pretend to be happy even when sad.','As long as it was for you, I','I could pretend to be strong even when in pain.','I wished love could be perfect through love alone.','I wished all my weaknesses could be hidden.','In a dream that could never come true,','I grew a flower that could never bloom.','I gave you the world, just for you.','I changed everything, just for you.','Hey, in the forest that was ours, you were not there.','I forgot the route I had taken.','I ended up not even knowing who I had been.','Try babbling to the mirror: who on earth are you?','As long as it was for you, I','I could pretend to be happy even when sad.','As long as it was for you, I','I could pretend to be strong even when in pain.','I wished love could be perfect through love alone.','I wished all my weaknesses could be hidden.','In a dream that could never come true,','I grew a flower that could never bloom.','I fashion a beautiful lie for you.','I try to erase myself and become your doll.','I fashion a beautiful lie for you.','I try to erase myself and become your doll.',"Why are you sad? I don't know; I don't know.",'Try smiling; try saying you love me.','Look at me, who has even abandoned myself.','Me, whom even you cannot understand.','They say I seem unfamiliar, now that I have become the person you liked.','They say I am not the person you once knew so well.','What do you mean I am not? I was blinded.','What kind of love is this? It is all fake love.','Oh, I do not even understand myself.','I fashion a beautiful lie for you.','I try to erase myself and become your doll.','I fashion a beautiful lie for you.','I try to erase myself and become your doll.','As long as it was for you, I','I could pretend to be happy even when sad.','As long as it was for you, I','I could pretend to be strong even when in pain.','I wished love could be perfect through love alone.','I wished all my weaknesses could be hidden.','In a dream that could never come true,','I grew a flower that could never bloom.'],
'Fire':[
"It's blazing up.","I've got nothing at all.",'After the sun sets, I stagger as I walk.','Completely battered, I am drunk, drunk.','I curse recklessly out on the street.','I have lost it; I seem like a madman.','Everything is a complete mess, living like [bleep].','Live however you like; it is yours anyway.','Do not try so hard; it is okay even if you lose.','Raise your hands and shout; burn it up.',"It's blazing up.",'Burn it all down, every last bit.','Burn it all down, every last bit.','As though we were going to burn everything.','Until dawn has passed.','We can just live, because we are young.','What kind of silver-spoon status do you have to talk like that?','You keep talking about spoons, but I am a person.','Live however you like; it is yours anyway.','Do not try so hard; it is okay even if you lose.','Raise your hands and shout; burn it up.',"It's blazing up.",'Burn it all down, every last bit.','Burn it all down, every last bit.','You who are full of fear, come here.','You who are suffering, come here.','With bare fists raised, all night long.','With the footsteps of a marching advance.','Jump; go wild, all of you.','Burn it all down, every last bit.','Burn it all down, every last bit.','Burn it all down, every last bit.','Burn it all down, every last bit.',"I'll forgive you."]}
words={
'Fake love':[
('척하다','to pretend','verb',1,'척','아픈 척하지 마세요.','Please do not pretend to be sick.'),
('완벽하다','to be perfect','adjective',4,'완벽하','모든 것이 완벽할 필요는 없어요.','Not everything has to be perfect.'),
('약점','weakness','noun',5,'약점','누구나 약점이 있어요.','Everyone has weaknesses.'),
('숨기다','to hide','verb',5,'숨겨','그는 사실을 숨겼어요.','He hid the truth.'),
('이루어지다','to come true; to be achieved','verb',6,'이뤄지','오랜 꿈이 이루어졌어요.','A long-held dream came true.'),
('키우다','to grow; to raise','verb',7,'키웠','베란다에서 꽃을 키워요.','I grow flowers on the balcony.'),
('잊어버리다','to forget completely','verb',11,'잊어버렸','약속을 잊어버렸어요.','I forgot the appointment.'),
('거울','mirror','noun',13,'거울','거울을 보고 머리를 빗었어요.','I looked in the mirror and brushed my hair.'),
('지우다','to erase; to delete','verb',23,'지워','사진을 실수로 지웠어요.','I accidentally deleted the photo.'),
('낯설다','to feel unfamiliar','adjective',30,'낯설','처음에는 이 도시가 낯설었어요.','At first, this city felt unfamiliar.')],
'Fire':[
('비틀대다','to stagger','verb',2,'비틀대','술에 취한 사람이 비틀대며 걸었어요.','A drunk person walked unsteadily.'),
('만신창이','a battered or wrecked state','noun',3,'만신창이','경기가 끝난 뒤 선수들은 만신창이가 됐어요.','After the match, the players were completely battered.'),
('엉망진창','a complete mess','noun',6,'엉망진창','방이 엉망진창이 됐어요.','The room became a complete mess.'),
('멋대로','as one pleases','adverb',7,'멋대로','남의 물건을 멋대로 쓰지 마세요.','Do not use other people’s things without permission.'),
('애쓰다','to make an effort','verb',8,'애쓰','혼자 해결하려고 너무 애쓰지 마세요.','Do not try too hard to solve it alone.'),
('불태우다','to burn up','verb',11,'불태워','마른 나뭇가지를 불태웠어요.','We burned the dry branches.'),
('새벽','dawn; early morning','noun',14,'새벽','새벽에 일어나서 공부했어요.','I woke up at dawn and studied.'),
('젊다','to be young','adjective',15,'젊','우리 부모님은 아직 젊으세요.','My parents are still young.'),
('괴롭다','to be distressed; to suffer','adjective',25,'괴로운','그 기억을 떠올리면 괴로워요.','Remembering that makes me suffer.'),
('용서하다','to forgive','verb',33,'용서해','친구의 실수를 용서했어요.','I forgave my friend’s mistake.')]
}
for song in d:
 title=song['title']
 if title not in translations:continue
 assert len(song['lines'])==len(translations[title]),title
 for line,en in zip(song['lines'],translations[title]):line['en']=en
 song['words']=[dict(lemma=lemma,gloss=gloss,pos=pos,line=i,surface=surface,example=ex,example_en=ex_en) for lemma,gloss,pos,i,surface,ex,ex_en in words[title]]
 for w in song['words']:
  assert w['surface'] in song['lines'][w['line']]['ko'],(title,w)
with open(p,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print('Updated',[(x['title'],len(x['lines']),len(x['words'])) for x in d if x['title'] in translations])
