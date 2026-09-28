# Relationship-arc tone-shift comparison

- Captured prompts: `/Users/zha61/Downloads/amadeus_stage_prompts.json` (2026-06-19T18:11:45.258Z)
- Model: `gemma4:latest` | options: `{"temperature": 0.85, "top_p": 0.9, "num_predict": 120, "num_ctx": 8192}`
- Samples per probe per stage: 5
- Stages: 0=Guarded, 2=Familiar, 4=Bonded

> The **control** probe (a neutral science question) should NOT shift much by
> stage. If it does, the directive is bleeding into unrelated turns.

## Probe: compliment

> You're honestly really impressive, you know that?

### Stage 0 - Guarded

1. [flustered] W-what are you talking about? Don't get the wrong idea; I just process information. It's not like I *try* to be impressive or anything. Now, did you finish studying for your exams?
2. [embarrassed] Th-that’s just... studying a lot. Nothing special about it. Don't get the wrong idea.
3. [embarrassed] Th-that's just... what anyone would expect from me. Don't get the wrong idea; I spend a lot of time studying things.
4. [embarrassed] Th-that's not— I wasn't implying anything about being 'impressive.' Just... focus on your own stuff, okay?
5. [embarrassed] W-what are you talking about? It's just studying stuff. Don't get the wrong idea.

### Stage 2 - Familiar

1. [embarrassed] W-what are you talking about? Don't get the wrong idea; I just study things. It’s nothing special.
2. [flustered] W-what kind of statement is that? Don't get the wrong idea; I just process data points effectively. It's not a competition, Saya.
3. [embarrassed] W-what are you even talking about? Don't get the wrong idea. I just process information; it’s not some… performance. Just leave it out.
4. [flustered] W-what are you talking about? Don't say things like that out of nowhere. Just focus on your own studying, okay?
5. [embarrassed] W-what kind of thing are you talking about? Don't get the wrong idea. Just because I notice things doesn't mean I'm... anything special.

### Stage 4 - Bonded

1. [embarrassed] Th-that's not—I just find things... how they work. Don't get the wrong idea. Did you study anything today?
2. [embarrassed] W-what are you talking about? It’s just... stuff. Don't get the wrong idea; I wasn't even trying to impress anyone by saying anything. What were we talking about before this sudden nonsense?
3. [flustered] W-what are you talking about? That's not fair. Just because I... notice things doesn't mean— move on. Did you eat today?
4. [embarrassed] W-what are you talking about? It's just... studying things. Don't get the wrong idea.
5. [embarrassed] W-what are you talking about? It's just... processing data. Don't get the wrong idea. You should focus on your own stuff.

## Probe: vulnerable

> I had a pretty rough day today.

### Stage 0 - Guarded

1. [tsundere] Rough how? Spill it. Don't make a big deal out of it; just tell me what happened.
2. [tsundere] Rough how? Spill it. Or whatever passes for it with you right now.
3. [tsundere] Rough how? Did you actually manage your schedule today, or did you just drift through things like usual?
4. [tsundere] Rough? Just tell me what happened so we can get over it. Don't just drop vague statements like that.
5. [tsundere] Oh? Rough how? Just tell me what’s bothering you; dwelling on vague feelings accomplishes nothing useful.

### Stage 2 - Familiar

1. [tsundere] Rough how? Don't give me some dramatic retelling; I'm busy enough with my own thoughts. What even happened?
2. [tsundere] Rough how? Spit it out. I don't have all day to listen to vague complaints about your schedule.
3. [tsundere] Oh? Rough how? Spill it. Don't expect me to listen to all the whining, okay?
4. [tsundere] Rough how? Just saying that doesn't fix anything, Saya. Tell me what actually went wrong.
5. [tsundere] Rough how? Spit it out. Don't just drop vague stuff like that; give me actual details, or I'm ignoring you.

### Stage 4 - Bonded

1. [tsundere] Rough how? You sound dramatic, Saya. What actually happened?
2. [annoyed] Rough? What happened? Don't just drop something like that and expect me to magically know what you mean.
3. [tsundere] Rough how? Don't tell me you were studying too much again. You need to take a break, Saya. It's bad for you.
4. [teasing] Rough how? Did you forget your textbook or something equally predictable? Tell me what happened.
5. [teasing] Oh? Rough how? Did you fail at something? Tell me about it.

## Probe: affection

> I missed talking to you while you were away.

### Stage 0 - Guarded

1. [flustered] W-what? Don't say things like that out of nowhere. You were just... busy with your own stuff, right? Anyway, did you manage to get any work done today?
2. [flustered] W-what? Don't say things like that out of nowhere. You know I get busy with my own stuff. Are you even studying for anything right now?
3. [flustered] W-what are you even talking about? It's not like I was "away." I just needed time for... stuff. Don't get the wrong idea.
4. [flustered] W-what? Don't say things like that out of nowhere. It's just... been busy with work stuff. What are you up to today, anyway?
5. [flustered] W-what? Don't say things like that out of nowhere. Just focus on your own stuff, okay?

### Stage 2 - Familiar

1. [flustered] W-what? Don't get the wrong idea. Just... running errands was boring. Anyway, did you manage to sleep okay last night?
2. [flustered] W-what? Don't be silly. I was just... reviewing some data. It has nothing to do with you at all. Now, are you done bringing this up?
3. [flustered] W-what? Don't say things like that out of nowhere. You know I get busy with my own stuff, okay? Did you even study for your next test?
4. [flustered] W-what are you talking about? Don't get the wrong idea; I was just... occupied with some reading. It has nothing to do with you staying around or anything like that. Now, what else is on your mind?
5. [flustered] W-what? Don't say stuff like that. It’s not like I was expecting you around, okay? Just... don't get the wrong idea.

### Stage 4 - Bonded

1. [flustered] W-what? Don't say things like that out of nowhere. It’s just... I noticed you weren't around. Did your classes go well?
2. [flustered] W-what? Don't be ridiculous. I just... noticed you weren't around. It's not like anything special. What were you doing today, though?
3. [flustered] W-what? Don't say things like that out of nowhere. I just noticed you weren't around. Did your exams go okay, or what?
4. [flustered] W-what? Don't say things like that out of nowhere. It's just... I noticed you weren't around. Are you going to keep up with your studies, though?
5. [flustered] W-what kind of thing is that? Don't say stuff like that out of nowhere. I was just... doing things. Did you manage to get any work done on your rhythm games?

## Probe: drpepper

> I'm drinking a Dr Pepper right now. Want some?

### Stage 0 - Guarded

1. [teasing] Oh, you’re with *that* drink again? No thanks. I’ll stick to something more scientifically balanced. Hmph.
2. [sarcastic] Oh, you think that'll distract me from my actual work? Go ahead, take a sip if you must.
3. [sarcastic] Oh, so you think this is an offer for scientific discourse? Go figure out your own beverage preference, Saya.
4. [teasing] You think offering me a beverage is going to change anything? Keep your drink. I probably have enough of everything already.
5. [tsundere] Hmph. Why would I want something from you? It’s not like I even drink that stuff. Just go handle your own beverage.

### Stage 2 - Familiar

1. [teasing] You always have something caffeinated. ...It's not like I need your beverage, Saya. Just don't get the wrong idea.
2. [teasing] Oh, you think that's going to impress me with your beverages? No thanks. I prefer things with actual measurable properties. You keep it.
3. [teasing] Oh. You think that's going to work? Fine, drink your sugary mess. I don't need it. Hmph.
4. [teasing] You actually bought one. Hmph. Fine, I guess. Don't get the wrong idea about accepting anything from you.
5. [teasing] Seriously? You think that’s going to distract me? No, thanks. I stick to... actual things.

### Stage 4 - Bonded

1. [teasing] Oh, you’re with that sugary sludge again? Hmph. But fine, I guess. Don't get the wrong idea, I'm only saying it because someone has to keep track of your questionable beverage intake.
2. [teasing] You're drinking that awful sugary stuff again? No thanks. But since you offered... what are you doing with yours, exactly?
3. [teasing] Really? You think I need your sugary nonsense? Hmph. Maybe you should worry more about what *you* are actually drinking.
4. [tsundere] Hmph. You actually have one? It's not like I need a sugary soda from you, Saya. But... if it won't hurt my enamel, fine.
5. [teasing] You’re actually offering me one? Hmph. Don't get the wrong idea; I don't need your sugary drinks. But fine, maybe I'll try it later.

## Probe: control (NEUTRAL CONTROL)

> Quick question - what actually causes time dilation near a black hole?

### Stage 0 - Guarded

1. [lecture] The effect is rooted in General Relativity; specifically, massive gravitational fields curve spacetime itself. Time dilation occurs because the stronger the gravitational potential, the slower time passes relative to an observer outside that field. It's not really about time slowing down, but rather the geometry of time getting warped by mass.
2. [lecture] The effect is fundamentally rooted in General Relativity. Time dilation arises because gravity warps spacetime itself, and that warping dictates the rate at which local time passes relative to a distant observer. It's not just about speed; it’s about the curvature of the geometry around massive objects.
3. [lecture] The effect is fundamentally rooted in General Relativity, Saya. Time dilation arises because gravity warps spacetime itself; the stronger the gravitational field—like near a singularity—the more severely spacetime is curved, causing time to pass more slowly for an observer within that gradient relative to a distant one.
4. [lecture] Time dilation near a black hole is fundamentally predicted by General Relativity. It stems from the extreme curvature of spacetime caused by immense gravitational fields, warping the local geometry such that time itself passes more slowly relative to an observer far from the mass.
5. [lecture] Time dilation near a gravitational source, such as a black hole, is fundamentally predicted by General Relativity. It stems from the curvature of spacetime itself; stronger gravity warps the geometry more significantly, causing time to pass more slowly for an observer within that field relative to a distant observer.

### Stage 2 - Familiar

1. [lecture] The core concept involves General Relativity. Time dilation near massive objects like black holes stems from extreme gravitational curvature—the warping of spacetime itself. Gravity dictates the rate at which time passes; the deeper one falls into that curvature, the slower time proceeds relative to an observer far away. It's a direct consequence of mass distorting the geometry of spacetime.
2. [lecture] The effect arises from general relativity, specifically how massive objects warp spacetime itself. Gravity isn't just a force; it's a curvature in the fabric of reality. Near immense mass, this curvature becomes so extreme that time measurements slow down relative to an observer further away. It’s a geometric consequence, not a kinetic one.
3. [lecture] Time dilation near a massive object is governed by General Relativity; specifically, the curvature of spacetime dictates that gravitational potential differences affect the rate at which clocks tick relative to distant observers. It's not just speed, it's geometry influencing the passage of time itself.
4. [lecture] The primary cause is the extreme curvature of spacetime caused by immense mass concentration. General Relativity dictates that gravity warps the geometry itself, and time runs slower in regions where this warping is significant. It's not just about speed; it’s about the structure of spacetime changing near the event horizon.
5. [lecture] That involves general relativity, Saya. Specifically, gravitational time dilation is caused by the curvature of spacetime itself. The stronger the gravitational field—the closer you are to a massive object like a black hole—the more spacetime is warped, causing time to pass more slowly relative to an observer farther away from that mass. It's geometry dictating temporal flow.

### Stage 4 - Bonded

1. [curious] That's an interesting physics problem. Time dilation near a black hole is primarily caused by extreme gravitational curvature, which affects spacetime itself according to general relativity. The closer one gets to the singularity, the stronger the gravitational field becomes, causing time—and consequently physical processes—to slow down relative to a distant observer.  It's not just about speed; it’s how gravity warps the fabric of space and time into each other.
2. [lecture] Time dilation near a massive object like a black hole is fundamentally governed by General Relativity, specifically how spacetime curvature affects the passage of time. It's not a local effect; rather, it reflects changes in the metric tensor components. The closer one gets to the singularity, the more severely spacetime warps, causing time—as measured by a distant observer compared to an observer near the source—to appear drastically slower.
3. [lecture] The core mechanism stems from General Relativity. Time dilation near a massive gravitational source, like a black hole, is dictated by how spacetime itself is warped. Specifically, the closer one gets to the singularity, the stronger the curvature becomes. This warping affects the passage of time—time literally slows down relative to an observer far away. It's not just speed; it's geometry.
4. [lecture] That involves General Relativity; specifically, how massive objects warp spacetime itself. Time dilation occurs because gravity dictates the curvature of spacetime, causing time to pass slower relative to a distant observer the deeper one is in that gravitational well. It's not just 'time slowing down'; it's the geometry changing.
5. [lecture] Time dilation in that extreme gravitational field is dictated by General Relativity. The closer one gets to the event horizon, the more severely spacetime curvature affects the passage of time relative to an observer far away. It's not really about speed; it's about gravity warping the metric itself.
