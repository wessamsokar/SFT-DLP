from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sft_dlp.core.audit_service import AuditService
from sft_dlp.db.repositories import (
    DlpEventRepository,
    DlpRuleRecord,
    DlpRuleRepository,
    RecipientRecord,
)


@dataclass
class DlpDecision:
    """DLP evaluation decision payload.

    Attributes:
        is_blocked: Whether transfer must be blocked.
        decision: Decision verb (`allow`, `warn`, `block`).
        matched_rule_name: Name of first matched blocking/warning rule.
        matched_excerpt: Snippet or detail that triggered the rule.
    """

    is_blocked: bool
    decision: str
    matched_rule_name: str | None
    matched_excerpt: str | None


class DlpPolicyEngine:
    """Applies local DLP rules based on patterns, file types, and recipient trust."""

    def __init__(
        self,
        rule_repository: DlpRuleRepository,
        event_repository: DlpEventRepository,
        audit_service: AuditService,
    ) -> None:
        """Initialize DLP policy evaluator.

        Args:
            rule_repository: Repository for active DLP rules.
            event_repository: Repository for rule hit events.
            audit_service: Audit writer for DLP outcomes.

        Returns:
            None.
        """
        self._rule_repository = rule_repository
        self._event_repository = event_repository
        self._audit_service = audit_service

    def evaluate_file_transfer(
        self,
        *,
        file_path: Path,
        recipient: RecipientRecord,
        actor: str,
        file_id: int | None = None,
    ) -> DlpDecision:
        """Evaluate a transfer candidate against enabled DLP policies.

        Args:
            file_path: File path to inspect.
            recipient: Recipient metadata for trust checks.
            actor: User identifier used for audit logging.
            file_id: Optional related file id.

        Returns:
            DLP decision containing block/allow outcome and match context.
        """
        file_path = file_path.resolve()
        rules = self._rule_repository.get_enabled_rules()

        for rule in rules:
            matched_excerpt = self._evaluate_rule(rule=rule, file_path=file_path, recipient=recipient)
            if matched_excerpt is None:
                continue

            self._event_repository.record_event(
                file_id=file_id,
                recipient_id=recipient.recipient_id,
                rule_id=rule.rule_id,
                matched_text=matched_excerpt,
                decision=rule.action,
            )

            status = "blocked" if rule.action == "block" else "warning"
            self._audit_service.log(
                event_type="dlp_rule_triggered",
                actor=actor,
                status=status,
                message=f"DLP rule triggered: {rule.rule_name}",
                file_id=file_id,
                recipient_id=recipient.recipient_id,
                metadata={
                    "rule_id": rule.rule_id,
                    "rule_type": rule.rule_type,
                    "decision": rule.action,
                    "file_path": str(file_path),
                },
            )

            if rule.action == "block":
                return DlpDecision(
                    is_blocked=True,
                    decision="block",
                    matched_rule_name=rule.rule_name,
                    matched_excerpt=matched_excerpt,
                )

        self._audit_service.log(
            event_type="dlp_check_passed",
            actor=actor,
            status="success",
            message="DLP checks passed for transfer.",
            file_id=file_id,
            recipient_id=recipient.recipient_id,
            metadata={"file_path": str(file_path)},
        )
        return DlpDecision(
            is_blocked=False,
            decision="allow",
            matched_rule_name=None,
            matched_excerpt=None,
        )

    def _evaluate_rule(
        self,
        *,
        rule: DlpRuleRecord,
        file_path: Path,
        recipient: RecipientRecord,
    ) -> str | None:
        """Run a single DLP rule against a transfer candidate.

        Args:
            rule: Rule definition.
            file_path: Candidate file path.
            recipient: Recipient metadata used by recipient rules.

        Returns:
            Matched excerpt/details when rule hits; otherwise None.
        """
        if rule.rule_type == "recipient":
            if "is_authorized=0" in rule.match_expression and not recipient.is_authorized:
                return f"recipient={recipient.email}"
            return None

        if rule.rule_type == "file_type":
            blocked_extensions = [item.strip().lower() for item in rule.match_expression.split(",") if item.strip()]
            if file_path.suffix.lower() in blocked_extensions:
                return file_path.suffix.lower()
            return None

        if rule.rule_type == "pattern":
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return None
            match = re.search(rule.match_expression, content)
            if match:
                snippet = match.group(0)
                return snippet[:120]
            return None

        return None
