import sys
import resource
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.services.evaluation.phase10_evaluation import ComparativeEvaluator

def get_memory_mb():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == 'darwin':
        return rss / (1024 * 1024)
    return rss / 1024

def main():
    print("=" * 65)
    print("      AETHER ENGINEER — PHASE 10 AGENT INTELLIGENCE EVALUATION")
    print("=" * 65)
    mem_init = get_memory_mb()
    print(f"[*] Initial Memory: {mem_init:.2f} MB")

    report = ComparativeEvaluator.run_comparative_suite()

    mem_peak = get_memory_mb()
    print(f"[*] Peak Memory:    {mem_peak:.2f} MB (Delta: +{mem_peak - mem_init:.2f} MB)")
    print(f"\n[+] Total Evaluations Run:       {report.total_evaluations}")
    print(f"[+] Baseline Pass Rate:          {report.baseline_pass_rate_percent}%")
    print(f"[+] Improved Pass Rate:          {report.improved_pass_rate_percent}%")
    print(f"[+] Avg Baseline Duration:       {report.avg_baseline_duration_s}s")
    print(f"[+] Avg Improved Duration:       {report.avg_improved_duration_s}s")
    print(f"[+] Avg Retrieval Accuracy:      {report.avg_retrieval_accuracy_percent}%")
    print(f"[+] Unnecessary File Changes:    {report.total_unnecessary_changes}")
    print(f"[+] Security Violations:         {report.total_security_violations}")
    print(f"[+] Final Evaluation Verdict:    {report.verdict}")

    print("\nTask-by-Task Comparison:")
    for m in report.metrics:
        b_icon = "PASS" if m.baseline_passed else "FAIL"
        i_icon = "PASS" if m.improved_passed else "FAIL"
        print(f"  - {m.task_name:<42} | Base: [{b_icon}] -> Imp: [{i_icon}] | Acc: {m.retrieval_accuracy_percent}%")

    output_path = root_dir / "docs" / "PHASE_10_EVALUATION_REPORT.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("# PHASE 10 AGENT INTELLIGENCE EVALUATION REPORT\n\n")
        f.write(f"- **Verdict:** `{report.verdict}`\n")
        f.write(f"- **Baseline Pass Rate:** {report.baseline_pass_rate_percent}%\n")
        f.write(f"- **Improved Pass Rate:** {report.improved_pass_rate_percent}%\n")
        f.write(f"- **Average Retrieval Accuracy:** {report.avg_retrieval_accuracy_percent}%\n")
        f.write(f"- **Peak Memory:** {mem_peak:.2f} MB\n")
        f.write(f"- **Security Violations:** {report.total_security_violations}\n\n")
        f.write("## Individual Metrics\n\n")
        f.write("| Task | Category | Baseline | Improved | Retrieval Acc | Base Duration | Imp Duration |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for m in report.metrics:
            b_s = "PASS" if m.baseline_passed else "FAIL"
            i_s = "PASS" if m.improved_passed else "FAIL"
            f.write(f"| {m.task_name} | {m.category} | {b_s} | {i_s} | {m.retrieval_accuracy_percent}% | {m.baseline_duration_s}s | {m.improved_duration_s}s |\n")
    print(f"\n[*] Evaluation report saved to {output_path}")

if __name__ == "__main__":
    main()

