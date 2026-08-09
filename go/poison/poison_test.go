package poison

import "testing"

func TestIDOverlap(t *testing.T) {
	r := Analyze(
		[]Example{{"a", "h1"}, {"b", "h2"}},
		[]Example{{"a", "h9"}},
		0, 0.01,
	)
	if !r.Contaminated || r.IDOverlap != 1 {
		t.Fatalf("%+v", r)
	}
}
