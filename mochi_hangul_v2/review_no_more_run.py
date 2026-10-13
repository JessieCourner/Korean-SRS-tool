import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf-8'))
translations={
'No more dream':[
'Hey, what is your dream?','Hey, what is your dream?','Hey, what is your dream?','Is that really all your dream amounts to?',
'But the truth is, I do not have any big dreams.','Ha, I live quite comfortably.','Nobody complains even if I do not dream of anything.','Everyone thinks just like me.','My childhood, full of dreams I have completely forgotten.','Do not worry about college; I will go, even if it is far away.','I told you, Mom, I am going to the study room now.','What is the person you have dreamed of becoming like?','Who do you see in your mirror now?','Follow your own path, even if you live for only one day.','Do something, anything; put your weakness aside.','Why can you not say it? You say you hate studying.','Too scared to quit school? Look, you are already getting ready to go.','Grow up, please; you are all talk, with a fragile mentality.','Stop and ask yourself when you last truly worked hard.','Hey, what is your dream?','Hey, what is your dream?','Hey, what is your dream?','Is that really all your dream amounts to?','It is a lie; you are such a liar.','Look at me; you are a hypocrite.','Why do you keep telling me to take a different path? Mind your own business.','Please stop forcing me.','What is your dream? What is your dream?','Is that all? Is that really all?',
'Another tiresome day, the same thing every day.','Adults and parents force cookie-cutter dreams into us.','The number-one career aspiration: a civil servant?','No more forced dreams; a relief pitcher in the bottom of the ninth.','Throw a fastball at the waste of time that is evening self-study.','Rebel against this hellish society; pardon your dreams.','Ask yourself what the profile of your dream looks like.','You have lived under oppression; become the subject of your own life.','What is the person you have dreamed of becoming like?','Who do you see in your mirror now?','Follow your own path, even if you live for only one day.','Do something, anything; put your weakness aside.','Hey, what is your dream?','Hey, what is your dream?','Hey, what is your dream?','Is that really all your dream amounts to?','It is a lie; you are such a liar.','Look at me; you are a hypocrite.','Why do you keep telling me to take a different path? Mind your own business.','Please stop forcing me.','What is your dream? What is your dream?','Is that all? Is that really all?',
'I do not know how to live.','I do not know how to fly.','I do not know how to make decisions.','Now I do not even know how to dream.','Open your eyes, all of you, now.','Come on, dance again.','Come on, dream again.','Do not dawdle or hesitate. What is up?','It is a lie; you are such a liar.','Look at me; you are a hypocrite.','Why do you keep telling me to take a different path? Mind your own business.','Please stop forcing me.','What is your dream? What is your dream?','Is that all? Is that really all?'],
'RUN BTS':[
'Our spot, 100 meters in Nonhyeon.','When school ended, the company would call.','Oh, I will be right there.','Please do not send me home.','Sometimes I dream of those days.','I shudder and wake up.','Ten years of waiting.','We are pretty fast.','Look closely; we have each other.','We knock the breath right out of you.','No matter who it is.','Our two bare feet are our gasoline.','Now let us go; are you ready?','I was right there in the studio in Nonhyeon-dong where rain leaked in.','Drinking cheap soju and complaining about our lot in life.','We swore that once we succeeded, everyone would be finished.','The reason for BTS’s success? I do not know either; there is no secret like that.','We just all ran ourselves ragged.','Whatever anyone said, we kept running.','The answer is right here.','Upward, we have got that.','Principles, we have got those.','Above those who run are those who fly.','And above them is BTS, running; let us go.','Ten years of waiting.','We are pretty fast.','Look closely; we have each other.','We knock the breath right out of you.','No matter who it is.','Our two bare feet are our gasoline.','Now let us go; are you ready?','With reckless faith.','Just run, on our own two legs.','That is how we proved it.','The seven little ones.','Worth a million dollars.','Jimin and V, you worked hard.','Namjoon and Hobi, you worked hard.','Yoongi and Jin, you worked hard.','Jungkook, everyone: thank you.','Get ready; further ahead.','Go get it; let us run.','We knock the breath right out of you.','No matter who it is.','Our two bare feet are our gasoline.','Now let us go; are you ready?']}
words={
'No more dream':[
('겨우','only; merely','adverb',3,'겨우','그는 겨우 열 살이에요.','He is only ten years old.'),
('까먹다','to forget (colloquial)','verb',8,'까먹','약속을 까먹어서 미안해요.','I am sorry I forgot our appointment.'),
('나약함','weakness; frailty','noun',14,'나약함','그는 자신의 나약함을 인정했어요.','He acknowledged his own weakness.'),
('노력하다','to make an effort','verb',18,'노력했','매일 한국어를 배우려고 노력해요.','I make an effort to learn Korean every day.'),
('위선자','hypocrite','noun',24,'위선자','그는 남을 비판하면서 같은 일을 하는 위선자예요.','He is a hypocrite who criticizes others while doing the same thing.'),
('강요하다','to force; to impose','verb',26,'강요하','자신의 의견을 남에게 강요하지 마세요.','Do not force your opinion on others.'),
('반복되다','to be repeated','verb',29,'반복되는','같은 실수가 반복되고 있어요.','The same mistake keeps happening.'),
('장래희망','future career aspiration','noun',31,'장래희망','어릴 때 제 장래희망은 의사였어요.','When I was little, I wanted to become a doctor.'),
('억압','oppression','noun',36,'억압','사람들은 억압에 맞서 싸웠어요.','People fought against oppression.'),
('결정하다','to decide','verb',53,'결정하는','어디로 갈지 아직 결정하지 못했어요.','I have not decided where to go yet.')],
'RUN BTS':[
('가끔','sometimes','adverb',4,'가끔','저는 가끔 혼자 영화를 봐요.','Sometimes I watch movies alone.'),
('몸서리치다','to shudder','verb',5,'몸서리치','그 기억을 떠올리면 몸서리쳐요.','I shudder when I remember it.'),
('맨발','bare foot','noun',11,'맨발','모래사장을 맨발로 걸었어요.','I walked barefoot on the beach.'),
('작업실','studio; workspace','noun',13,'작업실','그 화가는 작업실에서 그림을 그려요.','The artist paints in a studio.'),
('다짐하다','to resolve; to make a promise to oneself','verb',15,'다짐했','올해는 더 열심히 공부하겠다고 다짐했어요.','I resolved to study harder this year.'),
('성공','success','noun',16,'성공','성공을 위해 꾸준히 노력했어요.','I worked steadily toward success.'),
('이유','reason','noun',16,'이유','늦은 이유를 말해 주세요.','Please tell me why you are late.'),
('지조','integrity; steadfast principles','noun',21,'지조','그는 어려운 상황에서도 지조를 지켰어요.','He held to his principles even in difficult circumstances.'),
('증명하다','to prove','verb',33,'증명했','그는 자신의 실력을 결과로 증명했어요.','He proved his ability through his results.'),
('앞으로','from now on; ahead','adverb',40,'앞으로','앞으로 더 자주 연락할게요.','I will contact you more often from now on.')]
}
for s in d:
 if s['title'] not in translations:continue
 name=s['title']; assert len(s['lines'])==len(translations[name]),name
 for line,translation in zip(s['lines'],translations[name]):line['en']=translation
 s['words']=[dict(lemma=a,gloss=b,pos=c,line=i,surface=surf,example=ex,example_en=en) for a,b,c,i,surf,ex,en in words[name]]
 for w in s['words']:assert w['surface'] in s['lines'][w['line']]['ko'],(name,w)
with open(p,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print('Reviewed:',list(translations))
