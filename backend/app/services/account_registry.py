from __future__ import annotations

import math
import uuid
from typing import Iterable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.account import Account
from app.models.execution_group import ExecutionGroup, ExecutionMode
from app.models.execution_group_account import ExecutionGroupAccount, LotAllocationPolicy
from app.models.execution_run import ExecutionRun
from app.models.execution_run_event import ExecutionRunEvent
from app.schemas.account_registry import (
    ExecutionAllocationPreview,
    ExecutionGroupAccountCreate,
    ExecutionGroupAccountRead,
    ExecutionGroupAccountUpdate,
    ExecutionGroupCreate,
    ExecutionGroupRead,
    ExecutionGroupUpdate,
    LotAllocationPolicyEnum,
    ExecutionRunRead,
    ExecutionRunEventRead,
)


class AccountRegistryService:
    """Manages execution groups and account fan-out configuration."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _group_stmt(self, user_id: uuid.UUID) -> Select[tuple[ExecutionGroup]]:
        return (
            select(ExecutionGroup)
            .options(joinedload(ExecutionGroup.accounts).joinedload(ExecutionGroupAccount.account))
            .where(ExecutionGroup.user_id == user_id)
            .order_by(ExecutionGroup.created_at.asc())
        )

    def _get_group(self, user_id: uuid.UUID, group_id: uuid.UUID | str) -> ExecutionGroup | None:
        stmt = (
            self._group_stmt(user_id)
            .where(ExecutionGroup.id == uuid.UUID(str(group_id)))
            .limit(1)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def _ensure_group(self, user_id: uuid.UUID, group_id: uuid.UUID | str) -> ExecutionGroup:
        group = self._get_group(user_id, group_id)
        if group is None:
            raise ValueError("Execution group not found")
        return group

    def _account_to_schema(self, account: ExecutionGroupAccount) -> ExecutionGroupAccountRead:
        return ExecutionGroupAccountRead.model_validate(account)

    def _group_to_schema(self, group: ExecutionGroup) -> ExecutionGroupRead:
        return ExecutionGroupRead.model_validate(group)

    def _event_to_schema(self, event: ExecutionRunEvent) -> ExecutionRunEventRead:
        return ExecutionRunEventRead.model_validate(event)

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------
    def create_group(self, user_id: uuid.UUID, payload: ExecutionGroupCreate) -> ExecutionGroupRead:
        group = ExecutionGroup(
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            mode=ExecutionMode(payload.mode.value),
        )
        self.session.add(group)
        self.session.commit()
        self.session.refresh(group)
        return self._group_to_schema(group)

    def list_groups(self, user_id: uuid.UUID) -> list[ExecutionGroupRead]:
        stmt = self._group_stmt(user_id)
        groups: Iterable[ExecutionGroup] = self.session.execute(stmt).unique().scalars()
        return [self._group_to_schema(group) for group in groups]

    def update_group(
        self, user_id: uuid.UUID, group_id: uuid.UUID | str, payload: ExecutionGroupUpdate
    ) -> ExecutionGroupRead:
        group = self._ensure_group(user_id, group_id)
        if payload.name is not None:
            group.name = payload.name
        if payload.description is not None:
            group.description = payload.description
        if payload.mode is not None:
            group.mode = ExecutionMode(payload.mode.value)
        self.session.add(group)
        self.session.commit()
        self.session.refresh(group)
        return self._group_to_schema(group)

    def delete_group(self, user_id: uuid.UUID, group_id: uuid.UUID | str) -> bool:
        group = self._ensure_group(user_id, group_id)
        self.session.delete(group)
        self.session.commit()
        return True

    # ------------------------------------------------------------------
    # Accounts within group
    # ------------------------------------------------------------------
    def add_account(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID | str,
        payload: ExecutionGroupAccountCreate,
    ) -> ExecutionGroupAccountRead:
        group = self._ensure_group(user_id, group_id)
        account = self.session.get(Account, uuid.UUID(str(payload.account_id)))
        if account is None or account.broker.user_id != user_id:
            raise ValueError("Account not found for user")
        mapping = ExecutionGroupAccount(
            group_id=group.id,
            account_id=account.id,
            allocation_policy=LotAllocationPolicy(payload.allocation_policy.value),
            weight=payload.weight,
            fixed_lots=payload.fixed_lots,
        )
        self.session.add(mapping)
        self.session.commit()
        self.session.refresh(mapping)
        return self._account_to_schema(mapping)

    def update_account(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID | str,
        account_mapping_id: uuid.UUID | str,
        payload: ExecutionGroupAccountUpdate,
    ) -> ExecutionGroupAccountRead:
        group = self._ensure_group(user_id, group_id)
        mapping = self.session.get(ExecutionGroupAccount, uuid.UUID(str(account_mapping_id)))
        if mapping is None or mapping.group_id != group.id:
            raise ValueError("Account mapping not found")
        if payload.allocation_policy is not None:
            mapping.allocation_policy = LotAllocationPolicy(payload.allocation_policy.value)
        if payload.weight is not None:
            mapping.weight = payload.weight
        if payload.fixed_lots is not None:
            mapping.fixed_lots = payload.fixed_lots
        self.session.add(mapping)
        self.session.commit()
        self.session.refresh(mapping)
        return self._account_to_schema(mapping)

    def remove_account(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID | str,
        account_mapping_id: uuid.UUID | str,
    ) -> bool:
        group = self._ensure_group(user_id, group_id)
        mapping = self.session.get(ExecutionGroupAccount, uuid.UUID(str(account_mapping_id)))
        if mapping is None or mapping.group_id != group.id:
            raise ValueError("Account mapping not found")
        self.session.delete(mapping)
        self.session.commit()
        return True

    # ------------------------------------------------------------------
    # Allocation preview
    # ------------------------------------------------------------------
    def preview_allocation(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID | str,
        total_lots: int,
    ) -> list[ExecutionAllocationPreview]:
        if total_lots <= 0:
            raise ValueError("Total lots must be greater than zero")
        group = self._ensure_group(user_id, group_id)
        mappings = list(group.accounts)
        if not mappings:
            raise ValueError("Execution group has no accounts")

        fixed_allocations: list[tuple[ExecutionGroupAccount, int]] = []
        variable_entries: list[tuple[ExecutionGroupAccount, float]] = []
        remaining = total_lots

        for mapping in mappings:
            if mapping.allocation_policy == LotAllocationPolicy.fixed:
                lots = int(mapping.fixed_lots or 0)
                fixed_allocations.append((mapping, lots))
                remaining -= lots
            else:
                weight = float(mapping.weight or 1)
                variable_entries.append((mapping, weight))

        if remaining < 0:
            raise ValueError("Fixed allocations exceed requested lots")

        variable_allocations: list[tuple[ExecutionGroupAccount, int]] = []
        if variable_entries:
            total_weight = sum(weight for _, weight in variable_entries)
            if total_weight <= 0:
                raise ValueError("Allocation weights must be positive")
            provisional: list[tuple[ExecutionGroupAccount, int]] = []
            remainders: list[tuple[float, ExecutionGroupAccount]] = []
            for mapping, weight in variable_entries:
                share = (weight / total_weight) * remaining
                base = int(math.floor(share))
                provisional.append((mapping, base))
                remainders.append((share - base, mapping))
            assigned = sum(base for _, base in provisional)
            leftover = remaining - assigned
            remainders.sort(key=lambda item: item[0], reverse=True)
            index = 0
            provisional_dict = {mapping.id: base for mapping, base in provisional}
            while leftover > 0 and index < len(remainders):
                mapping = remainders[index][1]
                provisional_dict[mapping.id] += 1
                leftover -= 1
                index += 1
            variable_allocations = [
                (mapping, provisional_dict[mapping.id])
                for mapping, _ in provisional
            ]
        else:
            if remaining > 0:
                raise ValueError("No variable accounts available to allocate remaining lots")

        allocations = fixed_allocations + variable_allocations
        allocations = [(mapping, lots) for mapping, lots in allocations if lots > 0]
        if not allocations:
            raise ValueError("Allocation resulted in zero lots")

        total_assigned = sum(lots for _, lots in allocations)
        if total_assigned != total_lots:
            # adjust first allocation to account for rounding noise
            mapping, lots = allocations[0]
            allocations[0] = (mapping, lots + (total_lots - total_assigned))

        previews: list[ExecutionAllocationPreview] = []
        for mapping, lots in allocations:
            previews.append(
                ExecutionAllocationPreview(
                    account_id=mapping.account_id,
                    broker_id=mapping.account.broker_id,
                    lots=lots,
                    allocation_policy=LotAllocationPolicyEnum(mapping.allocation_policy.value),
                    weight=float(mapping.weight) if mapping.weight is not None else None,
                    fixed_lots=mapping.fixed_lots,
                )
            )
        return previews

    def get_group_runs(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID | str,
    ) -> list[ExecutionRunRead]:
        group = self._ensure_group(user_id, group_id)
        stmt = (
            select(ExecutionRun)
            .where(ExecutionRun.group_id == group.id)
            .order_by(ExecutionRun.requested_at.desc())
        )
        runs = self.session.execute(stmt).scalars().all()
        return [ExecutionRunRead.model_validate(run) for run in runs]


    def get_run_events(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID | str,
        run_id: uuid.UUID | str,
    ) -> list[ExecutionRunEventRead]:
        group = self._ensure_group(user_id, group_id)
        run = self.session.get(ExecutionRun, uuid.UUID(str(run_id)))
        if run is None or run.group_id != group.id:
            raise ValueError("Execution run not found")
        stmt = (
            select(ExecutionRunEvent)
            .where(ExecutionRunEvent.run_id == run.id)
            .order_by(ExecutionRunEvent.requested_at.asc())
        )
        events = self.session.execute(stmt).scalars().all()
        return [self._event_to_schema(event) for event in events]

__all__ = ["AccountRegistryService"]
