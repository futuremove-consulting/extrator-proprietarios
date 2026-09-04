"""Process Learning Logger — NDJSON structured logging for extraction pipeline analysis."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import contextmanager
import time


class ProcessLearningLogger:
    """
    Logger estruturado para análise de processo e aprendizado contínuo.
    
    Gera arquivo NDJSON append-only com eventos atômicos da extração.
    Permite reconstruir funil completo, calcular custos reais, identificar gargalos.
    """

    def __init__(self, log_dir: str = ".", prefix: str = "extraction"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.run_id = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.log_path = self.log_dir / f"process_log_{self.run_id}.ndjson"
        
        self._stage_stack = []
        self._action_start_times = {}
        
        # Log inicial do run
        self._write_event({
            "event_type": "run_start",
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": {"log_version": "1.0"}
        })

    def _write_event(self, event: Dict[str, Any]) -> None:
        """Escreve evento no arquivo NDJSON (append-only, crash-safe)."""
        event["run_id"] = self.run_id
        event["timestamp"] = event.get("timestamp", datetime.now().isoformat())
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    @contextmanager
    def stage(self, stage_name: str, system: str = None, metadata: Dict = None):
        """Context manager para marcar início/fim de um estágio."""
        stage_start = time.perf_counter()
        stage_id = f"{stage_name}_{len(self._stage_stack)}"
        
        self._stage_stack.append(stage_name)
        
        self._write_event({
            "event_type": "stage_start",
            "stage": stage_name,
            "system": system,
            "stage_id": stage_id,
            "metadata": metadata or {}
        })
        
        try:
            yield stage_id
        except Exception as e:
            self._write_event({
                "event_type": "stage_error",
                "stage": stage_name,
                "system": system,
                "stage_id": stage_id,
                "duration_ms": int((time.perf_counter() - stage_start) * 1000),
                "error": {"type": type(e).__name__, "message": str(e)},
                "metadata": metadata or {}
            })
            raise
        finally:
            duration_ms = int((time.perf_counter() - stage_start) * 1000)
            self._write_event({
                "event_type": "stage_end",
                "stage": stage_name,
                "system": system,
                "stage_id": stage_id,
                "duration_ms": duration_ms,
                "metadata": metadata or {}
            })
            self._stage_stack.pop()

    @contextmanager
    def action(self, action_name: str, system: str, stage: str, input_data: Dict = None):
        """Context manager para logar ação atômica (query, parse, persist, etc)."""
        action_start = time.perf_counter()
        action_id = f"{stage}_{action_name}_{int(action_start * 1000)}"
        
        self._write_event({
            "event_type": "action_start",
            "action": action_name,
            "system": system,
            "stage": stage,
            "action_id": action_id,
            "input": input_data or {}
        })
        
        success = True
        error = None
        output = {}
        cost = {"queries_used": 0, "capcoins_spent": 0, "credits_spent": 0}
        
        try:
            # Yield um objeto para coletar output/cost durante a ação
            collector = ActionCollector()
            yield collector
            output = collector.output
            cost = collector.cost
        except Exception as e:
            success = False
            error = {"type": type(e).__name__, "message": str(e)}
            raise
        finally:
            duration_ms = int((time.perf_counter() - action_start) * 1000)
            self._write_event({
                "event_type": "action_end",
                "action": action_name,
                "system": system,
                "stage": stage,
                "action_id": action_id,
                "duration_ms": duration_ms,
                "success": success,
                "error": error,
                "output": output,
                "cost": cost
            })

    def log_extraction_result(self, system: str, stage: str, result: Dict[str, Any]) -> None:
        """Log resultado agregado de extração (contagens, custos totais)."""
        self._write_event({
            "event_type": "extraction_summary",
            "system": system,
            "stage": stage,
            "result": result
        })

    def log_cost_snapshot(self, system: str, snapshot: Dict[str, Any]) -> None:
        """Log snapshot de custos/limites do sistema."""
        self._write_event({
            "event_type": "cost_snapshot",
            "system": system,
            "snapshot": snapshot
        })

    def log_decision(self, stage: str, decision: str, rationale: str, data: Dict = None) -> None:
        """Log decisão de fluxo (ex: pular sistema, abortar, retry)."""
        self._write_event({
            "event_type": "decision",
            "stage": stage,
            "decision": decision,
            "rationale": rationale,
            "data": data or {}
        })

    def finalize(self, status: str = "completed", summary: Dict = None) -> str:
        """Finaliza o log e retorna caminho do arquivo."""
        self._write_event({
            "event_type": "run_end",
            "status": status,
            "duration_ms": None,  # seria calculado se guardássemos start time global
            "summary": summary or {},
            "log_path": str(self.log_path)
        })
        return str(self.log_path)

    @property
    def current_stage(self) -> Optional[str]:
        return self._stage_stack[-1] if self._stage_stack else None


class ActionCollector:
    """Coletor de output/cost durante uma ação."""
    
    def __init__(self):
        self.output = {}
        self.cost = {"queries_used": 0, "capcoins_spent": 0, "credits_spent": 0}
    
    def add_output(self, key: str, value: Any) -> None:
        self.output[key] = value
    
    def add_cost(self, queries: int = 0, capcoins: int = 0, credits: int = 0) -> None:
        self.cost["queries_used"] += queries
        self.cost["capcoins_spent"] += capcoins
        self.cost["credits_spent"] += credits


def analyze_process_log(log_path: str) -> Dict[str, Any]:
    """
    Analisa log NDJSON e gera relatório de aprendizado.
    
    Uso:
        report = analyze_process_log("process_log_extraction_20260904_103000_abc123.ndjson")
    """
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    if not events:
        return {"error": "Log vazio"}
    
    run_start = next((e for e in events if e.get("event_type") == "run_start"), {})
    run_end = next((e for e in events if e.get("event_type") == "run_end"), {})
    
    # Filtrar ações
    actions = [e for e in events if e.get("event_type") == "action_end"]
    stages = [e for e in events if e.get("event_type") in ("stage_start", "stage_end")]
    decisions = [e for e in events if e.get("event_type") == "decision"]
    cost_snapshots = [e for e in events if e.get("event_type") == "cost_snapshot"]
    extractions = [e for e in events if e.get("event_type") == "extraction_summary"]
    
    # Análise por sistema
    by_system = {}
    for action in actions:
        sys = action.get("system", "unknown")
        if sys not in by_system:
            by_system[sys] = {"actions": 0, "total_ms": 0, "queries": 0, "capcoins": 0, "credits": 0, "errors": 0}
        by_system[sys]["actions"] += 1
        by_system[sys]["total_ms"] += action.get("duration_ms", 0)
        by_system[sys]["queries"] += action.get("cost", {}).get("queries_used", 0)
        by_system[sys]["capcoins"] += action.get("cost", {}).get("capcoins_spent", 0)
        by_system[sys]["credits"] += action.get("cost", {}).get("credits_spent", 0)
        if not action.get("success", True):
            by_system[sys]["errors"] += 1
    
    # Funil de estágios
    stage_funnel = {}
    for stage_evt in stages:
        if stage_evt.get("event_type") == "stage_end":
            st = stage_evt.get("stage")
            if st not in stage_funnel:
                stage_funnel[st] = {"count": 0, "total_ms": 0}
            stage_funnel[st]["count"] += 1
            stage_funnel[st]["total_ms"] += stage_evt.get("duration_ms", 0)
    
    return {
        "run_id": run_start.get("run_id"),
        "start_time": run_start.get("timestamp"),
        "end_time": run_end.get("timestamp"),
        "status": run_end.get("status"),
        "total_actions": len(actions),
        "total_errors": sum(1 for a in actions if not a.get("success", True)),
        "by_system": by_system,
        "stage_funnel": stage_funnel,
        "decisions": decisions,
        "cost_snapshots": cost_snapshots,
        "extraction_summaries": extractions,
        "log_file": log_path
    }


def generate_learning_report(log_path: str, output_path: str = None) -> str:
    """Gera relatório Markdown legível do log de processo."""
    analysis = analyze_process_log(log_path)
    
    if "error" in analysis:
        return f"# Erro\n{analysis['error']}"
    
    lines = []
    lines.append(f"# Process Learning Report")
    lines.append(f"**Run ID:** {analysis['run_id']}")
    lines.append(f"**Início:** {analysis['start_time']}")
    lines.append(f"**Fim:** {analysis['end_time']}")
    lines.append(f"**Status:** {analysis['status']}")
    lines.append(f"**Total Ações:** {analysis['total_actions']}")
    lines.append(f"**Total Erros:** {analysis['total_errors']}\n")
    
    lines.append("## Por Sistema")
    lines.append("| Sistema | Ações | Tempo Total (ms) | Queries | Capcoins | Créditos | Erros |")
    lines.append("|---------|-------|------------------|---------|----------|----------|-------|")
    for sys, data in analysis["by_system"].items():
        lines.append(f"| {sys} | {data['actions']} | {data['total_ms']} | {data['queries']} | {data['capcoins']} | {data['credits']} | {data['errors']} |")
    lines.append("")
    
    lines.append("## Funil de Estágios")
    lines.append("| Estágio | Execuções | Tempo Total (ms) | Tempo Médio (ms) |")
    lines.append("|---------|-----------|------------------|------------------|")
    for stage, data in analysis["stage_funnel"].items():
        avg = data["total_ms"] // data["count"] if data["count"] > 0 else 0
        lines.append(f"| {stage} | {data['count']} | {data['total_ms']} | {avg} |")
    lines.append("")
    
    if analysis["decisions"]:
        lines.append("## Decisões de Fluxo")
        for d in analysis["decisions"]:
            lines.append(f"- **{d['stage']}**: {d['decision']} — *{d['rationale']}*")
        lines.append("")
    
    if analysis["extraction_summaries"]:
        lines.append("## Resumos de Extração")
        for ext in analysis["extraction_summaries"]:
            lines.append(f"- **{ext['system']}** ({ext['stage']}): {ext['result']}")
        lines.append("")
    
    report = "\n".join(lines)
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
    
    return report