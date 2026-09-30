import json
from bioagent_deeprare import DeepRareAgent

CASE={"schema":"rare-disease-diagnosis-case/v1","case_id":"case-1","dataset":"fixture","phenotype_hpo_ids":["HP:0001250"],"phenotype_terms":["Seizure"],"private_label":"must not leak"}
EV="ev_0123456789abcdef01234567"

def config(reject=False):
    candidate={"diagnosis_id":"ORPHA:123","diagnosis_name":"Fixture syndrome","rationale":"fits","evidence_ids":[EV,"ev_bad"]}
    roles={
      "zero-shot diagnostician":[json.dumps({"diagnoses":[candidate]})],
      "similar-patient checking agent":[json.dumps({"similar":True,"reasoning":"phenotypes overlap"})],
      "central host candidate-fusion agent":[json.dumps({"diagnoses":[candidate]})],
      "candidate-specific disease checking agent":[json.dumps({"assessment":"incorrect" if reject else "plausible","reasoning":"checked","evidence_ids":[EV]})],
      "central host final reflection agent":[json.dumps({"diagnoses":[candidate]})],
    }
    if reject:
      expanded={"diagnosis_id":"OMIM:456","diagnosis_name":"Retry syndrome","rationale":"retry","evidence_ids":[]}
      roles["expanded differential agent"]=[json.dumps({"diagnoses":[expanded]})]
      roles["candidate-specific disease checking agent"].append(json.dumps({"assessment":"plausible","reasoning":"retry checked","evidence_ids":[]}))
      roles["central host final reflection agent"]=[json.dumps({"diagnoses":[expanded]})]
    return {"provider":"fixture","model_responses":roles,"source_responses":{
      "fit_case_search":[{"title":"similar","evidence_id":EV,"identifiers":{"orpha":"ORPHA:123"}}],
      "phenobrain_predict":[{"title":"Fixture syndrome","evidence_id":EV,"identifiers":{"orpha":"ORPHA:123"}}],
      "orphanet_lookup":[{"title":"Fixture syndrome","evidence_id":EV,"identifiers":{"orpha":"ORPHA:123"}}]}}

def test_full_workflow_and_public_projection():
    result=DeepRareAgent(config()).run(CASE)
    assert result["diagnoses"][0]["diagnosis_id"]=="ORPHA:123"
    assert result["diagnoses"][0]["evidence_ids"]==[EV]
    prompts="\n".join(x.get("content","") for x in result["trace"])
    assert "private_label" not in prompts
    roles=[x.get("role") for x in result["trace"] if x["event"]=="model_result"]
    assert roles==["zero-shot diagnostician","similar-patient checking agent","central host candidate-fusion agent","candidate-specific disease checking agent","central host final reflection agent"]

def test_all_rejected_retries_once():
    result=DeepRareAgent(config(True)).run(CASE)
    assert result["diagnoses"][0]["diagnosis_id"]=="OMIM:456"
    roles=[x.get("role") for x in result["trace"]]
    assert roles.count("expanded differential agent")==1
    assert roles.count("candidate-specific disease checking agent")==2
