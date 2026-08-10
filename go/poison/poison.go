package poison

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"sort"
)

type Example struct {
	ID, FeatureHash string
}

type Report struct {
	IDOverlap          int
	FeatureOverlap     int
	FeatureOverlapRatio float64
	TrainN             int
	EvalN              int
	Contaminated       bool
	InputFingerprint   string
	PolicyFingerprint  string
	Fingerprint        string
	RefuseReason       string
}

func digest(value any) string {
	raw, _ := json.Marshal(value)
	hash := sha256.Sum256(raw)
	return hex.EncodeToString(hash[:])
}

func validateDataset(name string, examples []Example) error {
	seen := map[string]struct{}{}
	for _, example := range examples {
		if example.ID == "" {
			return fmt.Errorf("%s example ID must be non-empty", name)
		}
		if example.FeatureHash == "" {
			return fmt.Errorf("%s feature hash must be non-empty", name)
		}
		if _, exists := seen[example.ID]; exists {
			return fmt.Errorf("duplicate %s example ID: %s", name, example.ID)
		}
		seen[example.ID] = struct{}{}
	}
	return nil
}

func datasetFingerprint(examples []Example) [][2]string {
	pairs := make([][2]string, len(examples))
	for i, example := range examples {
		pairs[i] = [2]string{example.ID, example.FeatureHash}
	}
	sort.Slice(pairs, func(i, j int) bool {
		if pairs[i][0] == pairs[j][0] {
			return pairs[i][1] < pairs[j][1]
		}
		return pairs[i][0] < pairs[j][0]
	})
	return pairs
}

// AnalyzeChecked detects exact example-ID and exact feature-hash overlap under
// an explicit bounded policy. It does not itself compute semantic similarity.
func AnalyzeChecked(train, eval []Example, maxID int, maxFeatRatio float64) (Report, error) {
	if maxID < 0 {
		return Report{}, fmt.Errorf("maxID must be non-negative")
	}
	if math.IsNaN(maxFeatRatio) || math.IsInf(maxFeatRatio, 0) || maxFeatRatio < 0 || maxFeatRatio > 1 {
		return Report{}, fmt.Errorf("maxFeatRatio must be finite and in [0,1]")
	}
	if err := validateDataset("train", train); err != nil {
		return Report{}, err
	}
	if err := validateDataset("eval", eval); err != nil {
		return Report{}, err
	}

	trainIDs, evalIDs := map[string]struct{}{}, map[string]struct{}{}
	trainFeatures, evalFeatures := map[string]struct{}{}, map[string]struct{}{}
	for _, example := range train {
		trainIDs[example.ID] = struct{}{}
		trainFeatures[example.FeatureHash] = struct{}{}
	}
	for _, example := range eval {
		evalIDs[example.ID] = struct{}{}
		evalFeatures[example.FeatureHash] = struct{}{}
	}

	idOverlap, featureOverlap := 0, 0
	for id := range evalIDs {
		if _, exists := trainIDs[id]; exists {
			idOverlap++
		}
	}
	for feature := range evalFeatures {
		if _, exists := trainFeatures[feature]; exists {
			featureOverlap++
		}
	}
	featureRatio := 0.0
	if len(evalFeatures) > 0 {
		featureRatio = float64(featureOverlap) / float64(len(evalFeatures))
	}
	contaminated := idOverlap > maxID || featureRatio > maxFeatRatio

	inputFingerprint := digest(struct {
		Train [][2]string `json:"train"`
		Eval  [][2]string `json:"eval"`
	}{datasetFingerprint(train), datasetFingerprint(eval)})
	policyFingerprint := digest(struct {
		MaxID        int     `json:"max_id_overlap"`
		MaxFeatRatio float64 `json:"max_feature_overlap_ratio"`
	}{maxID, maxFeatRatio})
	reportFingerprint := digest(struct {
		InputFingerprint  string  `json:"input_fingerprint"`
		PolicyFingerprint string  `json:"policy_fingerprint"`
		IDOverlap         int     `json:"id_overlap"`
		FeatureOverlap    int     `json:"feature_overlap"`
		FeatureRatio      float64 `json:"feature_overlap_ratio"`
		TrainN            int     `json:"train_n"`
		EvalN             int     `json:"eval_n"`
		Contaminated      bool    `json:"contaminated"`
	}{inputFingerprint, policyFingerprint, idOverlap, featureOverlap, featureRatio, len(train), len(eval), contaminated})

	return Report{
		IDOverlap: idOverlap,
		FeatureOverlap: featureOverlap,
		FeatureOverlapRatio: featureRatio,
		TrainN: len(train),
		EvalN: len(eval),
		Contaminated: contaminated,
		InputFingerprint: inputFingerprint,
		PolicyFingerprint: policyFingerprint,
		Fingerprint: reportFingerprint,
	}, nil
}

// Analyze preserves the original API. Invalid requests fail closed as a
// contaminated report; callers needing the refusal reason should use AnalyzeChecked.
func Analyze(train, eval []Example, maxID int, maxFeatRatio float64) Report {
	report, err := AnalyzeChecked(train, eval, maxID, maxFeatRatio)
	if err != nil {
		return Report{Contaminated: true, RefuseReason: err.Error()}
	}
	return report
}
