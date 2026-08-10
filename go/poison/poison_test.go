package poison

import (
	"math"
	"testing"
)

func TestIDOverlap(t *testing.T) {
	report, err := AnalyzeChecked(
		[]Example{{"a", "h1"}, {"b", "h2"}},
		[]Example{{"a", "h9"}},
		0, 0.01,
	)
	if err != nil {
		t.Fatal(err)
	}
	if !report.Contaminated || report.IDOverlap != 1 {
		t.Fatalf("%+v", report)
	}
}

func TestFeatureOverlapRatio(t *testing.T) {
	report, err := AnalyzeChecked(
		[]Example{{"a", "h1"}, {"b", "h2"}},
		[]Example{{"c", "h1"}, {"d", "h3"}},
		0, 0.4,
	)
	if err != nil {
		t.Fatal(err)
	}
	if report.FeatureOverlap != 1 || report.FeatureOverlapRatio != 0.5 || !report.Contaminated {
		t.Fatalf("%+v", report)
	}
}

func TestPolicyAndInputsBindFingerprint(t *testing.T) {
	train := []Example{{"a", "h1"}}
	eval := []Example{{"b", "h1"}}
	strict, err := AnalyzeChecked(train, eval, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	permissive, err := AnalyzeChecked(train, eval, 0, 1)
	if err != nil {
		t.Fatal(err)
	}
	if strict.PolicyFingerprint == permissive.PolicyFingerprint || strict.Fingerprint == permissive.Fingerprint {
		t.Fatalf("policy change did not affect fingerprints")
	}
	if !strict.Contaminated || permissive.Contaminated {
		t.Fatalf("unexpected policy outcomes: strict=%+v permissive=%+v", strict, permissive)
	}

	other, err := AnalyzeChecked([]Example{{"x", "h1"}}, []Example{{"y", "h1"}}, 0, 1)
	if err != nil {
		t.Fatal(err)
	}
	if permissive.InputFingerprint == other.InputFingerprint {
		t.Fatalf("distinct datasets share input fingerprint")
	}
}

func TestInvalidInputsFailClosed(t *testing.T) {
	cases := []struct {
		train, eval []Example
		maxID       int
		maxRatio    float64
	}{
		{[]Example{{"a", "h1"}, {"a", "h2"}}, []Example{{"b", "h3"}}, 0, 0.1},
		{[]Example{{"", "h1"}}, nil, 0, 0.1},
		{[]Example{{"a", ""}}, nil, 0, 0.1},
		{nil, nil, -1, 0.1},
		{nil, nil, 0, -0.1},
		{nil, nil, 0, 1.1},
		{nil, nil, 0, math.NaN()},
	}
	for _, tc := range cases {
		if report, err := AnalyzeChecked(tc.train, tc.eval, tc.maxID, tc.maxRatio); err == nil || report != (Report{}) {
			t.Fatalf("expected checked refusal, report=%+v err=%v", report, err)
		}
		if report := Analyze(tc.train, tc.eval, tc.maxID, tc.maxRatio); !report.Contaminated || report.RefuseReason == "" {
			t.Fatalf("compatibility API did not fail closed: %+v", report)
		}
	}
}
