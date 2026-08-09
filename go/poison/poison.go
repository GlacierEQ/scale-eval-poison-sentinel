package poison

type Example struct {
	ID, FeatureHash string
}

type Report struct {
	IDOverlap, FeatureOverlap int
	Contaminated              bool
}

func Analyze(train, eval []Example, maxID int, maxFeatRatio float64) Report {
	tID, eID := map[string]struct{}{}, map[string]struct{}{}
	tF, eF := map[string]struct{}{}, map[string]struct{}{}
	for _, x := range train {
		tID[x.ID] = struct{}{}
		tF[x.FeatureHash] = struct{}{}
	}
	for _, x := range eval {
		eID[x.ID] = struct{}{}
		eF[x.FeatureHash] = struct{}{}
	}
	idOv, fOv := 0, 0
	for id := range eID {
		if _, ok := tID[id]; ok {
			idOv++
		}
	}
	for f := range eF {
		if _, ok := tF[f]; ok {
			fOv++
		}
	}
	ratio := 0.0
	if len(eF) > 0 {
		ratio = float64(fOv) / float64(len(eF))
	}
	return Report{idOv, fOv, idOv > maxID || ratio > maxFeatRatio}
}
