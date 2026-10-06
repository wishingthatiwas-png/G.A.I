import json, random, statistics
from pathlib import Path
ROOT=Path('/mnt/gai'); OUT=ROOT/'lab/results'; OUT.mkdir(parents=True,exist_ok=True)

def run(name, learn=True, shift=True, seed=7, n=4000):
    rng=random.Random(seed); Q={}; visits={}; errors=[]; rewards=[]; actions=[]; context=0
    def key(a,c): return (a,c)
    for t in range(n):
        if shift and t==n//2: context=1
        candidates=['rest','maintain','interact','explore']
        scores=[]
        for a in candidates:
            q=Q.get(key(a,context),0.0) if learn else 0.0
            novelty=0.12 if a!='explore' else (0.55 if context==0 else 0.75)
            scores.append(q + novelty*0.10*rng.random())
        # small exploration floor prevents an unvisited action from disappearing forever
        if rng.random()<0.08:
            a=rng.choice(candidates)
        else: a=candidates[max(range(4),key=lambda i:scores[i])]
        if context==0:
            base={'rest':0.18,'maintain':0.28,'interact':0.36,'explore':0.52}[a]
        else:
            base={'rest':0.12,'maintain':0.20,'interact':0.18,'explore':0.62}[a]
        reward=max(-1,min(1,base+rng.gauss(0,0.10)))
        # delayed/contextual consequence: exploration reveals the new regime more reliably
        if a=='explore' and context==1: reward += 0.12
        old=Q.get(key(a,context),0.0); err=reward-old
        if learn: Q[key(a,context)]=old+0.08*err
        visits[(a,context)]=visits.get((a,context),0)+1
        errors.append(abs(err)); rewards.append(reward); actions.append(a)
    def avg(xs): return statistics.mean(xs) if xs else 0
    mid=n//2
    result={'run':name,'learn':learn,'shift':shift,'seed':seed,'ticks':n,
      'early_reward':avg(rewards[:mid//2]),'late_reward':avg(rewards[-mid//2:]),
      'early_prediction_error':avg(errors[:mid//2]),'late_prediction_error':avg(errors[-mid//2:]),
      'post_shift_reward':avg(rewards[mid:mid+500]),'post_shift_error':avg(errors[mid:mid+500]),
      'action_counts':{a:actions.count(a) for a in ['rest','maintain','interact','explore']},
      'context_models':len(Q),'visits':{f'{a}|{c}':v for (a,c),v in visits.items()},
      'final_q':{f'{a}|{c}':round(v,4) for (a,c),v in Q.items()}}
    (OUT/f'{name}.json').write_text(json.dumps(result,indent=2)); return result

results=[run('A_learning_stationary',True,False,7),run('B_learning_shift',True,True,7),run('C_no_learning_shift',False,True,7)]
summary={'experiments':results,'hypothesis':'learning should reduce late prediction error and improve adaptation after a context shift'}
(OUT/'learning_lab_summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
