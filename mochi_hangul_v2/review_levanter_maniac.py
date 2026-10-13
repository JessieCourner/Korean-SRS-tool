import json
p='/mnt/data/mochi_final_work/music_lyrics_library.json'
d=json.load(open(p,encoding='utf-8'))
translations={24:[
'I thought that if I kept chasing, I might finally reach you.',
'I had never even doubted it.',
'I embraced the you I had imagined,',
'and held you tightly in both hands,',
'but there was only emptiness in my arms.',
'I wandered on, with nothing but that left.',
'In the end, I came to realize',
'that I had to let you go.',
'Oh, deceiving myself,',
'the moment I woke from the dream I had endured for so long,',
'I could feel the light pouring down.',
'Even if it still feels unfamiliar,',
'the moment I broke free from you, I could see myself.',
'Everything, all of it, came into view.',
'Now I understand.',
'What I needed was myself.',
'I walk wherever my own two feet take me.',
'As I ran unwaveringly toward you, I realized',
'everything about me had been directed toward you.',
'The closer I got to you,',
'the more I lost myself.',
'Like fallen leaves beneath that tree,',
'even if I end up buried in snow and trampled,',
'now I move beyond you and set off in search of spring.',
'The feelings left behind scatter in the blowing wind.',
'Oh, the dream that kept me imprisoned,',
'the moment I escaped its tunnel,',
'I could feel the light pouring down.',
'Even if it still feels unfamiliar,',
'the moment I broke free from you, I could see myself.',
'Everything, all of it, came into view.',
'Now I understand.',
'What I needed was myself.',
'I walk wherever my own two feet take me.',
'Although I was afraid of letting you go,',
'I have no choice but to let you go.',
'Even if it still feels unfamiliar,',
'Only after breaking free from you can I see it.',
'Everything, all of it, comes into view.'
],25:[
'Everyone, stop pretending to be normal and loosen up.',
'The smiles you are wearing feel unsettling.',
'Once the lock comes off, everyone is the same.',
'Your eyes cannot fool me.',
'The real self has been unleashed.',
'I barely manage to keep my wits about me.',
'Blink once, and then it is back again.',
'Back to playing the normal person the world has defined.',
'My mind is scrambled; I have to back it up.',
'Inside, I have always been a freaky monster.',
'That trendy kindness is already past its prime.',
'Even if you insult me behind my back, I ignore it all.',
'Acting innocent only gets you badly hurt.',
'When kindness keeps coming, people mistake it for a right.',
'No wonder it drives me crazy.',
'[Unrelated song recommendation: remove.]',
'[Unrelated song recommendation: remove.]',
'I go crazy as though a screw has come loose.',
'I will probably end up spinning wildly.',
'I walk like Frankenstein.',
'I laugh as though a screw has come loose.',
'I will probably end up spinning wildly.',
'A whole group of people who are anything but normal.',
'Like loose threads from a torn doll,',
'our true colors eventually show.',
'This life is anything but comfortable.',
'Everyone, stop pretending to be normal.',
'The smiles you are wearing are not genuine.',
'Once the locket opens, everyone is the same.',
'Your eyes cannot fool me.',
'This street I walk on is a minefield.',
'No one knows when it will explode.',
'Even the once-gentle wind might change at any moment.',
'Everyone lives with something hidden away.',
'Acting innocent only gets you badly hurt.',
'When kindness keeps coming, people mistake it for a right.',
'No wonder it drives me crazy.',
'I go crazy as though a screw has come loose.',
'I will probably end up spinning wildly.',
'I walk like Frankenstein.',
'I laugh as though a screw has come loose.',
'I will probably end up spinning wildly.',
'A whole group of people who are anything but normal.',
'Both eyes are full of madness.',
'Every sense is on edge.',
'You keep locking me up in pretty packaging.',
'As time passes, the truth will eventually emerge.',
'That hidden part of my inner self.'
]}
for idx,ens in translations.items():
 assert len(ens)==len(d[idx]['lines']),(idx,len(ens),len(d[idx]['lines']))
 for line,en in zip(d[idx]['lines'],ens):line['en']=en
# The source contains unrelated song recommendations inserted between the lyrics.
s=d[25]
for ix in sorted([15,16],reverse=True):
 s['lines'].pop(ix)
 for w in s['words']:
  if w['line']>ix:w['line']-=1
for idx in translations:
 for w in d[idx]['words']:
  assert w['surface'] in d[idx]['lines'][w['line']]['ko'],(idx,w)
with open(p,'w',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print('Reviewed',[(d[i]['title'],len(d[i]['lines'])) for i in translations])
