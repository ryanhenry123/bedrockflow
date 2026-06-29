from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from src.registry import WorkflowSpec
from utils.log import get_logger

LOGGER = get_logger(__file__)

EXAMPLES_ROOT = Path(__file__).resolve().parents[2] / "examples"


@dataclass
class WorkflowDefinition:
    name: str
    path: Path
    spec: WorkflowSpec
    task_module: str
    default_context: dict[str, object] = field(default_factory=dict)
    report_key: str | None = None
    max_workers: int | None = None


def _path_to_module(path: Path, repo_root: Path) -> str:
    rel = path.relative_to(repo_root)
    return str(rel.with_suffix("")).replace("/", ".")


def _task_module_candidates(examples_root: Path) -> list[tuple[str, Path]]:
    repo_root = examples_root.parent
    candidates: list[tuple[str, Path]] = []
    for path in sorted(examples_root.rglob("*.py")):
        if path.name == "tasks.py" or path.name.endswith("_tasks.py"):
            if path.name.startswith("_") or path.name.startswith("run_"):
                continue
            candidates.append((_path_to_module(path, repo_root), path))
    return candidates


def _register_names_in_source(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "register":
            if node.args and isinstance(node.args[0], ast.Constant):
                if isinstance(node.args[0].value, str):
                    names.add(node.args[0].value)
    return names


def _infer_report_key(spec: WorkflowSpec) -> str | None:
    depended_on = {dep for step in spec.steps for dep in step.depends_on}
    sinks = [step.step_name for step in spec.steps if step.step_name not in depended_on]
    if len(sinks) == 1:
        return sinks[0]
    return spec.report_key


def _infer_max_workers(spec: WorkflowSpec) -> int | None:
    if spec.max_workers is not None:
        return spec.max_workers
    depth_groups: dict[int, int] = {}
    depth: dict[str, int] = {}

    def step_depth(name: str, visiting: set[str] | None = None) -> int:
        if name in depth:
            return depth[name]
        visiting = visiting or set()
        if name in visiting:
            return 0
        visiting.add(name)
        step = next(s for s in spec.steps if s.step_name == name)
        if not step.depends_on:
            value = 0
        else:
            value = max(step_depth(dep, visiting) for dep in step.depends_on) + 1
        depth[name] = value
        return value

    for step in spec.steps:
        level = step_depth(step.step_name)
        depth_groups[level] = depth_groups.get(level, 0) + 1

    if not depth_groups:
        return None
    peak = max(depth_groups.values())
    return peak if peak > 1 else None


def _resolve_task_module(
    spec: WorkflowSpec,
    workflow_path: Path,
    candidates: list[tuple[str, Path]],
) -> str:
    if spec.task_module:
        return spec.task_module

    required = spec.referenced_function_names()
    local_tasks = workflow_path.parent.parent / "tasks.py"
    ordered: list[tuple[str, Path]] = []
    if local_tasks.exists():
        repo_root = EXAMPLES_ROOT.parent
        ordered.append((_path_to_module(local_tasks, repo_root), local_tasks))
    ordered.extend((mod, path) for mod, path in candidates if path != local_tasks)

    matches: list[tuple[int, str]] = []
    for module_name, source_path in ordered:
        registered = _register_names_in_source(source_path)
        if required <= registered:
            extras = len(registered - required)
            matches.append((extras, module_name))

    if not matches:
        raise ValueError(
            f"No task module provides all functions for workflow {spec.name!r}: "
            f"{sorted(required)}"
        )

    matches.sort(key=lambda item: (item[0], item[1]))
    return matches[0][1]


def _load_spec(path: Path) -> WorkflowSpec:
    if path.suffix == ".yaml":
        return WorkflowSpec.load(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return WorkflowSpec.model_validate(payload)


def discover_workflows(
    examples_root: Path = EXAMPLES_ROOT,
) -> dict[str, WorkflowDefinition]:
    candidates = _task_module_candidates(examples_root)
    discovered: dict[str, WorkflowDefinition] = {}

    yaml_paths = sorted(examples_root.glob("**/workflows/*.yaml"))
    json_paths = [
        path
        for path in sorted(examples_root.glob("**/workflows/*.json"))
        if not path.with_suffix(".yaml").exists()
    ]
    all_paths = [*yaml_paths, *json_paths]

    seen_paths: dict[str, Path] = {}
    for path in all_paths:
        preview = _load_spec(path)
        if preview.name in seen_paths:
            existing = seen_paths[preview.name]
            raise ValueError(
                f"Duplicate workflow name {preview.name!r} at {path} and {existing}"
            )
        seen_paths[preview.name] = path

    for path in all_paths:
        spec = _load_spec(path)
        task_module = _resolve_task_module(spec, path, candidates)
        definition = WorkflowDefinition(
            name=spec.name,
            path=path,
            spec=spec,
            task_module=task_module,
            default_context=dict(spec.default_context),
            report_key=spec.report_key or _infer_report_key(spec),
            max_workers=_infer_max_workers(spec),
        )
        discovered[spec.name] = definition
        LOGGER.debug(
            "discovered workflow=%s path=%s task_module=%s report_key=%s",
            spec.name,
            path,
            task_module,
            definition.report_key,
        )

    return discovered


@lru_cache(maxsize=1)
def workflow_catalog() -> dict[str, WorkflowDefinition]:
    return discover_workflows()


def reload_workflow_catalog() -> dict[str, WorkflowDefinition]:
    workflow_catalog.cache_clear()
    return workflow_catalog()


def list_workflow_names() -> list[str]:
    return sorted(workflow_catalog())


def get_workflow(name: str) -> WorkflowDefinition:
    try:
        return workflow_catalog()[name]
    except KeyError as exc:
        raise FileNotFoundError(f"Workflow not found: {name}") from exc


def load_workflow_spec(name: str) -> WorkflowSpec:
    return get_workflow(name).spec
