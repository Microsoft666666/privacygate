"""Re-run the frozen v2 detector and current detector on identical annotations."""
from benchmarks import detector_v2
from evaluation import ADVERSARIAL, DATASET, evaluate


def previous_detector(text: str, sensitive_phrases: tuple = ()) -> list:
    rules = tuple(detector_v2.SensitivePhrase(r.phrase, r.category) for r in sensitive_phrases)
    return detector_v2.detect(text, rules)


def comparison_reports() -> dict:
    return {name: {"v2": evaluate(cases, previous_detector), "current": evaluate(cases)}
            for name, cases in (("Original 37", DATASET), ("Adversarial 52", ADVERSARIAL))}


if __name__ == "__main__":
    import json
    print(json.dumps(comparison_reports(), indent=2))
