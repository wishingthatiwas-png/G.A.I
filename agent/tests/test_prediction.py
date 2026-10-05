from core.prediction import PredictiveModel

def test_prediction_learns_and_errors():
    p=PredictiveModel()
    p.models={}
    state={"curiosity":0.5,"satisfaction":0.5,"safety":0.1,"energy":0.2,"social":0.0}
    p.choose("explore",["red","circle"],state)
    after=dict(state); after["curiosity"]=0.7; after["satisfaction"]=0.6
    err=p.observe(after)
    assert err > 0
    pred=p.predict("explore",["red","circle"])
    assert pred["curiosity"] > 0
    assert pred["satisfaction"] > 0

def test_novel_context_falls_back_to_action_model():
    p=PredictiveModel()
    p.models={}
    s={"curiosity":.5,"satisfaction":.5,"safety":.1,"energy":.2,"social":0}
    p.choose("rest",["red"],s)
    a=dict(s); a["energy"]=.3
    p.observe(a)
    assert p.predict("rest",["blue"]) != {}
