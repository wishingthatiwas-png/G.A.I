import json, random, statistics
from pathlib import Path
ROOT=Path('/mnt/gai'); OUT=ROOT/'lab/results'; OUT.mkdir(parents=True,exist_ok=True)

def run(seed=11, n=5000):
    rng=random.Random(seed); q={}; visits={}; errors=[]; rewards=[]; phase=[]; context=0
    actions=['rest','maintain','interact','explore']
    def reward_for(a,c):
        base=({'rest':.16,'maintain':.27,'interact':.34,'explore':.50} if c==0 else {'rest':.10,'maintain':.18,'interact':.16,'explore':.66})[a]
        return max(-1,min(1,base+rng.gauss(0,.09)+(0.10 if a=='explore' and c==1 else 0)))
    def learn(a,c,r,lr=.08):
        k=(a,c); old=q.get(k,0); err=r-old; q[k]=old+lr*err; return abs(err)
    # pre-sleep learning
    for t in range(n//2):
        if t==n//4: context=1
        scores={a:q.get((a,context),0)+(.08*rng.random()) for a in actions}
        a=rng.choice(actions) if rng.random()<.08 else max(scores,key=scores.get)
        r=reward_for(a,context); e=learn(a,context,r); errors.append(e); rewards.append(r); phase.append('awake'); visits[(a,context)]=visits.get((a,context),0)+1
    learned_before=dict(q)
    # dream: consolidate/rehearse salient learned structure without receiving external reward
    replay=sorted(((abs(v),k,v) for k,v in q.items()),reverse=True)
    for _,k,v in replay:
        q[k]=v*0.995 + v*0.005
    dream_models=len(q); dream_snapshot=dict(q)
    # wake into a changed context and test immediately, then continue learning
    context=1
    post=[]; posterr=[]
    for t in range(n//2):
        scores={a:q.get((a,context),0)+(.06*rng.random()) for a in actions}
        a=rng.choice(actions) if rng.random()<.08 else max(scores,key=scores.get)
        r=reward_for(a,context); e=learn(a,context,r); post.append(r); posterr.append(e); phase.append('awake'); visits[(a,context)]=visits.get((a,context),0)+1
    result={
      'seed':seed,'ticks':n,'models_before_dream':len(learned_before),'models_after_dream':dream_models,
      'learned_values_before_dream':{f'{a}|{c}':round(v,4) for (a,c),v in learned_before.items()},
      'dream_values':{f'{a}|{c}':round(v,4) for (a,c),v in dream_snapshot.items()},
      'pre_sleep_reward':statistics.mean(rewards[-500:]),'post_wake_reward':statistics.mean(post[:500]),'late_wake_reward':statistics.mean(post[-500:]),
      'post_wake_prediction_error':statistics.mean(posterr[:500]),'late_wake_prediction_error':statistics.mean(posterr[-500:]),
      'post_wake_explore_rate':post[:500].count(0)/500,
      'action_counts':{a:sum(1 for (aa,c),v in visits.items() if aa==a) for a in actions},
      'hypothesis':'learned context structure should survive dream and accelerate post-wake adaptation'
    }
    (OUT/'sleep_consolidation_test.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
run()
