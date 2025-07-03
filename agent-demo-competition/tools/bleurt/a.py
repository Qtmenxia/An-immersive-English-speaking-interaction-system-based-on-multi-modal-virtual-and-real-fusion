from bleurt import score
# this is a test case to try bleurt dependencies

checkpoint = "bleurt/test_checkpoint"
references = ["This is a test."]
candidates = ["This is a test."]

scorer = score.BleurtScorer(checkpoint)
scores = scorer.score(references=references, candidates=candidates)
assert isinstance(scores, list) and len(scores) == 1
print(scores)