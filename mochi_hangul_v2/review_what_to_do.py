import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json';d=json.load(open(p,encoding='utf-8'))
t=[
'My nights are deep, deep, with the TV left on.','Noisy, just like my heart.','For what reason, exactly, do you','switch my heart off and on however you like?','It is not that I dislike it.','I am just worried that you might be','too tired.','That is how I feel.','If I have you, I need nobody else.','You are like summer without the sweltering heat.','You are the full stop to the loneliness I have felt until now.','When I cannot sleep because I am thinking of you, suddenly it is morning.','What am I going to do about you?','Even when I see you, I miss you more.','You are my one and only dilemma.','What should I do?','What am I going to do about you, my love?','What should I do now because of you?','Every day is filled to the brim, every day.','What can I do when I like you so much?','How about you?','Is it hard for you to fall asleep because of me?','If I keep making your heart flutter without a moment to rest,','what should I do?','What should I do, what should I do?','Every passing day I like you more.','I am clumsy by nature and tend to back away a little.','But for you, I will never back down.','Let us hum a tune together.','We each put in one earbud and feel close to each other.','I draw you every day on the sketchpad in my mind.','Anyway, I simply like you.','I have been repeating the same thing for a while.','Sorry, but that is all there is to it.','Even if I try every complicated word,','this is how I truly feel.','What am I going to do about you?','Even when I see you, I miss you more.','If all of this is a dream, then I really...','What should I do?','What am I going to do about you, my love?','What should I do now because of you?','Every day is filled to the brim, every day.','What can I do when I like you so much?','How about you?','Is it hard for you to fall asleep because of me?','If I keep making your heart flutter without a moment to rest,','what should I do?','You shine so brightly, all the way to the edge of the universe,','bright enough to reach it.','What would I do without you, baby?','What am I going to do about you, my love?','What should I do now because of you?','Every day is filled to the brim, every day.','What can I do when I like you so much?','How about you?','Do you know how I feel?','I cannot live without you.','What should I do?','What should I do?'
]
s=d[16];s['lines'].pop(24)
for w in s['words']:
 if w['line']>24:w['line']-=1
assert len(s['lines'])==len(t),(len(s['lines']),len(t))
for l,en in zip(s['lines'],t):l['en']=en
for w in s['words']:
 if w['lemma']=='별':w.update(lemma='진심',surface='진심',line=35,gloss='sincere feelings; true feelings',pos='noun',example='그의 진심을 믿어요.',example_en='I believe in his sincerity.')
 if w['lemma']=='노래':w.update(lemma='콧노래',surface='콧노래',line=28,gloss='humming; a hummed tune',pos='noun',example='그녀는 콧노래를 부르며 걸었어요.',example_en='She walked along humming a tune.')
 assert w['surface'] in s['lines'][w['line']]['ko'],w
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('translated',sum(l['en'] is not None for song in d for l in song['lines']))
